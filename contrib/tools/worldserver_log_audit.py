#!/usr/bin/env python3
"""Read-only, fail-closed audit of a worldserver startup/shutdown transcript."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

# Ordering matters: specific rejected dependencies precede generic loader errors.
RULES = [
 ('PROCESS_CRASH','P0',r'Segmentation fault|core dumped|Program received signal SIG|AddressSanitizer:|ERROR: AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer|Assertion.*failed'),
 ('SCRIPT_CPP_NO_DB','P1',r"Script named '([^']+)' does not have a script name assigned"),
 ('SCRIPT_DB_NO_CPP','P1',r"ScriptName '([^']+)' exists in database, but no core script found"),
 ('SPELL_HOOK_MISMATCH','P1',r"did not match dbc effect data.*won't be executed"),
 ('SPELL_VALIDATE_FAILURE','P1',r'ValidateSpellInfo:|did not pass Validate|Validate\(\).*fail'),
 ('LOCALE_ORPHAN','P2',r'Hotfix locale table.*references row that does not exist'),
 ('REFERENCE_LOOT_MISSING','P1',r"Table 'reference_loot_template' Entry (\d+) does not exist"),
 ('GO_LOOT_MISSING','P1',r"Table 'gameobject_loot_template' Entry (\d+) does not exist"),
 ('OTHER_LOOT_MISSING','P1',r"Table '(?:creature|item|skinning|pickpocketing)_loot_template'.*does not exist"),
 ('LOOT_INVALID','P1',r'loot.*(?:chance.*100|recursive|cycle)|group.*chance.*100'),
 ('LOOT_UNREFERENCED','P3',r'loot_template.*thus useless'),
 ('TRAINER_FLAG','P1',r'npc_trainer.*(?:TRAINER|trainer flag|trainer npc|trainerflag|flag)|trainer.*(?:UNIT_NPC_FLAG_TRAINER|trainer flag)'),
 ('SMARTAI_MISSING_SPELL','P1',r'SmartAI.*(?:non-existent|non existing|not exist).*Spell|SmartAI.*Spell.*(?:not exist|non-existent)'),
 ('SMARTAI_SELF_LINK','P1',r'SmartAI.*linking self'),
 ('SMARTAI_LINK_SOURCE','P1',r'SmartAI.*Link Source Event'),
 ('SMARTAI_LINK_DESTINATION','P1',r'SmartAI.*Link Event.*not found'),
 ('SMARTAI_MISSING_CONVERSATION','P1',r'Smart.*conversation.*(?:not exist|don.t exist|missing)'),
 ('CONVERSATION_MISSING_LINE','P1',r'conversation_line_template.*missing template'),
 ('SMARTAI_MISSING_WAYPOINT','P1',r'SmartAI.*WaypointPath.*(?:non-existent|not exist)'),
 ('SMARTAI_MISSING_TEXT','P1',r'SmartAI.*non-existent Text'),
 ('SMARTAI_MIN_MAX','P1',r'SmartAI.*min/max.*wrong'),
 ('SMARTAI_OTHER_REJECTED','P1',r'SmartAI.*(?:skipped|invalid|never trigger)'),
 ('SPAWN_UNSUPPORTED_DIFFICULTY','P1',r'creature.*has unsupported difficulty'),
 ('SPAWN_DIFFICULTY','P1',r'(?:creature|Creature).*not spawned in any.*difficulty|(?:creature|Creature).*not spawned in any.*difficulties'),
 ('SPAWN_EQUIPMENT','P2',r'creature.*equipment_id.*not found'),
 ('CREATURE_BASE_STATS','P1',r'Missing base stats'),
 ('CREATURE_MODEL','P1',r'Creature.*does not have any existing display'),
 ('CREATURE_CLASS','P1',r'Creature.*invalid unit_class'),
 ('GO_ZERO_DISPLAY','P1',r"Gameobject.*doesn't have a displayId \(0\)"),
 ('GO_COORDINATES','P1',r'gameobject.*invalid coordinates'),
 ('SPAWN_MISSING_TEMPLATE','P1',r'Table `(?:creature|gameobject)`.*non existing.*entry'),
 ('CREATURE_TEXT_BROADCAST','P1',r'CreatureTextMgr.*BroadcastTextId'),
 ('QUEST_RELATION','P1',r'(?:creature|gameobject)_quest(?:starter|ender).*'),
 ('QUEST_OBJECTIVE','P1',r'quest_objectives.*(?:not exist|invalid|missing)'),
 ('PHASE_CONDITION','P1',r'\[Condition.*(?:phase|Phase)|Phase .*phase_area.*not exist|phaseid.*does not exist'),
 ('CONDITION_REJECTED','P1',r'(?:[Cc]ondition|SourceEntry.*SourceGroup).*(?:ignoring|invalid|not handled|Not handled|not exist|needs correction)'),
 ('CONDITION_UNUSED_VALUE','P3',r'[Cc]ondition.*(?:useless|unused).*Value'),
 ('GOSSIP_DEPENDENCY','P1',r'gossip_menu.*(?:non-existing|not exist|invalid|missing)'),
 ('EVENT_ORPHAN','P2',r'game_event_creature.*not found'),
 ('FORMATION_ORPHAN','P2',r'creature_formations.*incorrect'),
 ('ADDON_ORPHAN','P2',r'does not exist but has a record in `(?:creature|gameobject)_addon`'),
 ('VMAP_MISSING','P1',r'Could not load VMAP'),
 ('VENDOR_INVALID','P1',r'npc_vendor.*(?:invalid|not exist|does not)'),
 ('PROC_REJECTED','P1',r'Proc will not be triggered|spell_proc.*(?:invalid|not exist)'),
 ('INSTANCE_SCRIPT_INVALID','P1',r'InstanceMapScript.*invalid'),
 ('WAYPOINT_NUMBERING','P1',r'(?:[Ww]aypoint|[Pp]ath).*(?:expected|not in order|invalid point)'),
 ('ARENA_OUTDOOR_OPCODE','P2',r'Opcode.*does not have a value|ArenaSeason.*must be|OutdoorPvP.*no entry|command.*arena .*skipped'),
 ('UPDATER_DIRECTORY','P3',r'Given update include directory.*does not exist'),
 ('MYSQL_CLI_PASSWORD','INFO_NOISE',r'^mysql: \[Warning\] Using a password on the command line interface can be insecure\.$'),
 ('FRESH_CHARACTER_NAMES','INFO_NOISE',r'^No character name data loaded, empty query$'),
 ('EMPTY_TABLE','P3',r'DB table .* is empty'),
 ('GO_TEMPLATE_DEPENDENCY','P1',r'Gameobject.*(?:not exist|have not|invalid|missing)'),
]
COMPILED=[(c,s,re.compile(p)) for c,s,p in RULES]
UNKNOWN=re.compile(r'\b(?:ERROR|FATAL|invalid|missing|skipped|non-existing|non-existent|unsupported)\b|does not exist|not found|won.t be executed|will never trigger',re.I)


def normalize(line):
    line=re.sub(r'\x1b\[[0-9;]*m','',line).strip()
    line=re.sub(r"(['`])[^'`]+\1",'<name>',line)
    return re.sub(r'(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?', '<n>',line)


def object_keys(category,line):
    if category in ('SCRIPT_CPP_NO_DB','SCRIPT_DB_NO_CPP'):
        return [re.search(r"'([^']+)'",line)[1]]
    if category=='LOCALE_ORPHAN':
        m=re.search(r'does not exist (\d+) locale (\w+)',line)
        return [m[1]+':'+m[2]] if m else []
    if category=='SPELL_HOOK_MISMATCH':
        m=re.search(r'Spell [`\'](\d+)[`\']',line)
        script=re.search(r'script [`\']([^`\']+)[`\']',line)
        return [(m[1] if m else '?')+':'+(script[1] if script else '?')]
    if category=='VMAP_MISSING':
        m=re.search(r'id:(\d+), x:(\d+), y:(\d+)',line)
        return [':'.join(m.groups())] if m else []
    if category in ('REFERENCE_LOOT_MISSING','GO_LOOT_MISSING'):
        return re.findall(r'Entry (\d+)',line)
    if category=='SMARTAI_MISSING_SPELL':
        return re.findall(r'Spell entry (\d+)',line)
    if category=='TRAINER_FLAG':
        m=re.search(r'(?:entry|Entry|creature)\s*\(?([0-9]+)',line)
        return [m[1]] if m else re.findall(r'\d+',line)[:1]
    names=re.findall(r"(?:script|Script|ScriptName)\s*['`]([^'`]+)['`]",line)
    values=re.findall(r'(?:GUID:|Entry:?|ID:|Id:?|id:|entry|level|mapid)\s*\(?(-?\d+)',line)
    return names+values


def audit(text,allowlist=(),exit_code=None):
    allowed={}
    for item in allowlist:
        if set(item)!={'line_sha256','reason'} or not item['reason'].strip() or not re.fullmatch(r'[0-9a-f]{64}',item['line_sha256']):
            raise ValueError('Allowlist requires exact line SHA256 and nonempty reason')
        allowed[item['line_sha256']]=item['reason']
    groups={};lines=text.splitlines()
    for number,line in enumerate(lines,1):
        match=next(((c,s) for c,s,p in COMPILED if p.search(line)),None)
        if match is None:
            if not UNKNOWN.search(line):continue
            match=('UNCLASSIFIED_LOADER_MESSAGE','P1')
        category,severity=match;signature=normalize(line)
        key=(category,signature)
        group=groups.setdefault(key,{'category':category,'severity':severity,'normalized_signature':signature,'count':0,'unique_objects':[], 'object_counts':{},'example_lines':[],'first_line':number,'last_line':number,'status':'NEEDS_SOURCE_DATA','allowlisted_count':0})
        group['count']+=1;group['last_line']=number
        for obj in object_keys(category,line):group['object_counts'][obj]=group['object_counts'].get(obj,0)+1
        if len(group['example_lines'])<3 and line not in group['example_lines']:group['example_lines'].append(line)
        digest=hashlib.sha256(line.strip().encode()).hexdigest()
        if digest in allowed:
            if severity in ('P0','P1'):raise ValueError('P0/P1 findings cannot be allowlisted')
            group['allowlisted_count']+=1
        if category=='PROCESS_CRASH':group['observed_symptom']='PROCESS_TERMINATION_CONFIRMED; root cause unverified'
        if severity=='INFO_NOISE':group['status']='FALSE_POSITIVE'
    result=sorted(groups.values(),key=lambda x:(['P0','P1','P2','P3','INFO_NOISE'].index(x['severity']),-x['count'],x['category']))
    for group in result:
        group['unique_objects']=sorted(group['object_counts'])
    revision=re.search(r'TrinityCore rev\. ([0-9a-f]+)',text)
    ready=bool(re.search(r'worldserver-daemon\) ready',text))
    totals=Counter();severity_totals=Counter()
    for group in result:totals[group['category']]+=group['count'];severity_totals[group['severity']]+=group['count']
    requested=bool(re.search(r'server shutdown 1',text));halting='Halting process...' in text
    normal=exit_code==0 and ready and requested and halting and not totals['PROCESS_CRASH']
    unexpected=any(x['severity']!='INFO_NOISE' and x['count']!=x['allowlisted_count'] for x in result)
    return {'schema_version':1,'log_sha256':hashlib.sha256(text.encode()).hexdigest(),'analyzed_log_commit':revision[1] if revision else None,'line_count':len(lines),'ready_seen':ready,'shutdown_requested':requested,'halting_seen':halting,'process_exit_code':exit_code,'normal_exit_verified':normal,'category_counts':dict(sorted(totals.items())),'severity_counts':dict(severity_totals),'findings':result,'acceptance':'FAIL' if unexpected or exit_code not in (None,0) else ('PASS' if normal else 'INCOMPLETE_EXIT_EVIDENCE')}


def markdown(report):
    out=['# Аудит чистого запуска worldserver','',f"Commit лога: `{report['analyzed_log_commit']}`. SHA256 нормализованного текста: `{report['log_sha256']}`.",'', 'Числа ниже измерены по логу; это сообщения, а не число независимых дефектов.','', '| Категория | Приоритет | До | После | Остаток | Статус |','|---|---|---:|---|---:|---|']
    for category,count in report['category_counts'].items():
        severity=next(x['severity'] for x in report['findings'] if x['category']==category)
        out.append(f'| {category} | {severity} | {count} | не измерено | {count} | исследуется |')
    out+=['','Достижение ready не доказывает исправность. Нормальный exit code и ASan/GDB пока не подтверждены. Allowlist P0/P1 запрещён. Неизвестные сообщения с признаками отказа loader остаются P1 до разбора.','']
    return '\n'.join(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('--json',type=Path,required=True);parser.add_argument('--markdown',type=Path);parser.add_argument('--allowlist',type=Path);parser.add_argument('--exit-code',type=int);parser.add_argument('--fail-on-integrity',action='store_true')
    args=parser.parse_args()
    report=audit(args.log.read_text(encoding='utf-8-sig'),json.loads(args.allowlist.read_text('utf8')) if args.allowlist else [],args.exit_code)
    report['source_bytes_sha256']=hashlib.sha256(args.log.read_bytes()).hexdigest()
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if args.markdown:args.markdown.write_text(markdown(report),encoding='utf8')
    print(json.dumps({'acceptance':report['acceptance'],'counts':report['category_counts']},ensure_ascii=False))
    return 1 if args.fail_on_integrity and report['acceptance']!='PASS' else 0


if __name__=='__main__':
    raise SystemExit(main())
