#!/usr/bin/env python3
"""Read-only Legion Gossip audit. No repair SQL or credentials in output.

Use MYSQL_PWD / an existing client login file for authentication. Audit a frozen
JSON snapshot, or SELECT known columns through a mysql client. Live MyISAM reads
are not a transactionally consistent snapshot: preferably use a local DB copy.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess

TABLES={
 'gossip_menu':['MenuId','TextId'],
 'gossip_menu_option':['MenuId','OptionIndex','OptionType','OptionNpcFlag','OptionText'],
 'gossip_menu_option_action':['MenuId','OptionIndex','ActionMenuId','ActionPoiId'],
 'gossip_menu_option_box':['MenuId','OptionIndex','BoxCoded','BoxMoney'],
 'gossip_menu_option_trainer':['MenuId','OptionIndex','TrainerId'],
 'gossip_menu_option_locale':['MenuId','OptionIndex','Locale'],
 'conditions':['SourceTypeOrReferenceId','SourceGroup','SourceEntry','SourceId','ElseGroup','ConditionTypeOrReference','ConditionTarget','ConditionValue1','ConditionValue2','ConditionValue3','NegativeCondition'],
 'creature_template':['entry','name','AIName','ScriptName','gossip_menu_id','npcflag'],
 'gameobject_template':['entry','AIName','ScriptName','type','Data3','Data19'],
 'smart_scripts':['entryorguid','source_type','id','link','event_type','event_param1','event_param2','event_phase_mask','event_chance','event_flags','action_type','action_param1','action_param2','target_type','target_param1','target_param2','comment'],
 'points_of_interest':['ID'], 'trainer':['Id'], 'npc_trainer':['ID','SpellID'],
 'creature_default_trainer':['CreatureId','TrainerId']}


def enums(root):
    text=(root/'src/server/game/Entities/Creature/GossipDef.h').read_text('utf8')
    body=re.search(r'enum Gossip_Option\s*\{(.*?)\};',text,re.S)[1];result={};value=-1
    for name,explicit in re.findall(r'^\s*(GOSSIP_OPTION_\w+)\s*(?:=\s*(\d+))?\s*[,\n]',body,re.M):
        value=int(explicit) if explicit else value+1;result[name]=value
    assert 'GOSSIP_OPTION_MAX' in result
    smart=(root/'src/server/game/AI/SmartScripts/SmartScriptMgr.h').read_text('utf8')
    events={name:int(number) for name,number in re.findall(r'(SMART_(?:EVENT|ACTION)_\w+)\s*=\s*(\d+)\s*,',smart)}
    flags={name:int(number,0) for name,number in re.findall(r'(UNIT_NPC_FLAG_\w+)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,',(root/'src/server/game/Entities/Unit/UnitDefines.h').read_text('utf8'))}
    return result,events,flags


def export_database(args):
    command=[args.mysql,'--default-character-set=utf8mb4','--batch','--raw','--skip-column-names','--host='+args.host,'--port='+str(args.port),'--user='+args.user,args.database]
    def query(text):
        p=subprocess.run(command,input=text,text=True,encoding='utf8',capture_output=True)
        if p.returncode:raise RuntimeError('Read-only MySQL audit query failed: '+p.stderr)
        return p.stdout.splitlines()
    result={'tables':{},'schema':{},'unavailable':{},'basis':'Read-only SELECT from '+args.database+'; MyISAM consistency requires a quiescent copy'}
    existing=set(query('SHOW TABLES;'))
    for table,columns in TABLES.items():
        if table not in existing:result['unavailable'][table]='Missing table';continue
        schema=query('SHOW COLUMNS FROM `'+table+'`;');result['schema'][table]=schema
        present={line.split('\t')[0] for line in schema};missing=set(columns)-present
        if missing:result['unavailable'][table]='Missing columns: '+','.join(sorted(missing));continue
        pairs=','.join("'"+column+"',`"+column+'`' for column in columns)
        result['tables'][table]=[json.loads(line) for line in query('SELECT JSON_OBJECT('+pairs+') FROM `'+table+'`;')]
    return result


def cpp_inventory(root):
    rows=[];locations=defaultdict(list)
    for path in sorted(p for p in (root/'src/server/scripts').rglob('*') if p.suffix in ('.cpp','.h')):
        raw=path.read_bytes();encoding='utf8'
        try:text=raw.decode('utf8')
        except UnicodeDecodeError:text=raw.decode('latin1');encoding='latin1 byte-preserving fallback'
        relative=path.relative_to(root).as_posix()
        for name in re.findall(r'(?:CreatureScript|GameObjectScript)\s*\(\s*"([^"]+)"',text):locations[name].append(relative)
        for match in re.finditer(r'\b(OnGossipHello|OnGossipSelectCode|OnGossipSelect|sGossipHello|sGossipSelectCode|sGossipSelect|GossipSelectCode|GossipSelect)\s*\([^;{}]*\)\s*(?:override\s*)?\{',text):
            opening=match.end()-1;depth=1;end=opening+1
            while depth and end<len(text):depth+=(text[end]=='{')-(text[end]=='}');end+=1
            body=text[opening:end];actions=re.findall(r'(GOSSIP_ACTION_INFO_DEF\s*\+\s*\d+)',body)
            rows.append({'path':relative,'encoding':encoding,'line':text.count('\n',0,match.start())+1,'hook':match[1],
                         'clears_menu':bool(re.search(r'ClearGossipMenuFor|ClearMenus',body)),
                         'adds_menu':bool(re.search(r'AddGossipItemFor|ADD_GOSSIP_ITEM|AddMenuItem',body)),
                         'sends_menu':bool(re.search(r'SendGossipMenuFor|SEND_GOSSIP_MENU|SendGossipMenu',body)),
                         'closes_menu':bool(re.search(r'CloseGossipMenuFor|SendCloseGossip',body)),
                         'returns':sorted(set(re.findall(r'\breturn\s+(true|false)\s*;',body))),
                         'repeated_action_expressions':sorted(k for k,v in Counter(re.sub(r'\s+','',a) for a in actions).items() if v>1),
                         'status':'REVIEW_REQUIRED','note':'Lexical inventory; conditional branches, helpers and dynamic menus need manual review. Missing direct ClearMenus is not proof of a bug.'})
    return rows,dict(locations)


def audit(snapshot,root):
    option_types,events,flags=enums(root);tables=snapshot['tables'];findings=[]
    def emit(category,status,**evidence):findings.append(dict(category=category,status=status,**evidence))
    missing=set(TABLES)-set(tables)
    if missing:
        for table in sorted(missing):emit('SCHEMA_UNAVAILABLE','REVIEW_REQUIRED',table=table,reason=snapshot.get('unavailable',{}).get(table,'Absent in snapshot'))
        return {'basis':snapshot.get('basis'),'complete':False,'counts':dict(Counter(x['category'] for x in findings)),'findings':findings}
    def key(row):return int(row['MenuId']),int(row['OptionIndex'])
    options={key(row):row for row in tables['gossip_menu_option']};menus={int(row['MenuId']) for row in tables['gossip_menu']}
    option_menus={m for m,i in options};poi={int(row['ID']) for row in tables['points_of_interest']};trainers={int(row['Id']) for row in tables['trainer']}
    actions={key(row):row for row in tables['gossip_menu_option_action']};bindings={key(row):row for row in tables['gossip_menu_option_trainer']}
    positive={int(row['ID']) for row in tables['npc_trainer'] if int(row['SpellID'])>0}
    legacy=positive|{int(row['ID']) for row in tables['npc_trainer'] if int(row['SpellID'])<0 and -int(row['SpellID']) in positive}
    valid_types=set(option_types.values())-{option_types['GOSSIP_OPTION_MAX']};smart=defaultdict(list)
    for row in tables['smart_scripts']:smart[int(row['entryorguid']),int(row['source_type'])].append(row)
    npc_menus=defaultdict(list)
    for npc in tables['creature_template']:npc_menus[int(npc['gossip_menu_id'])].append(npc)
    cpp,locations=cpp_inventory(root)
    for table in ['gossip_menu_option_action','gossip_menu_option_box','gossip_menu_option_trainer','gossip_menu_option_locale']:
        for row in tables[table]:
            if key(row) not in options:emit('ORPHAN_OPTION','CONFIRMED_DATA_ERROR',table=table,**row)
    for pair,option in options.items():
        m,index=pair;type_=int(option['OptionType']);action=actions.get(pair,{})
        if type_ not in valid_types:emit('INVALID_OPTION_TYPE','CONFIRMED_DATA_ERROR',**option,core_max=option_types['GOSSIP_OPTION_MAX'])
        if m not in menus:emit('ORPHAN_MENU','REVIEW_REQUIRED',**option,reason='Menu text missing; default title or scripted menu may be intentional')
        destination=int(action.get('ActionMenuId',0))
        if destination and destination not in menus:
            emit('BROKEN_ACTION_MENU',('FALSE_POSITIVE' if type_!=option_types['GOSSIP_OPTION_GOSSIP'] else 'CONFIRMED_DATA_ERROR' if destination not in option_menus else 'REVIEW_REQUIRED'),**option,ActionMenuId=destination,
                 reason='Native dispatch does not use ActionMenuId for this OptionType' if type_!=option_types['GOSSIP_OPTION_GOSSIP'] else 'Missing destination text and option rows; verify quest/default-menu fallback before repair' if destination not in option_menus else 'Destination options exist; default text may be intentional')
        point=int(action.get('ActionPoiId',0))
        if point and point not in poi:emit('MISSING_POI','CONFIRMED_DATA_ERROR',**option,ActionPoiId=point,ActionMenuId=destination,reason='Loader discards this POI; other action or script may still work')
        trainer=int(bindings.get(pair,{}).get('TrainerId',0))
        if trainer and trainer not in trainers:emit('MISSING_TRAINER','CONFIRMED_DATA_ERROR',**option,TrainerId=trainer)
        elif type_==option_types['GOSSIP_OPTION_TRAINER'] and not trainer:
            # Gossip trainer0 falls back to legacy npc_trainer, not creature_default_trainer.
            owners=npc_menus.get(m,[])
            unresolved=[int(n['entry']) for n in owners if int(n['entry']) not in legacy]
            emit('MISSING_TRAINER','REVIEW_REQUIRED' if unresolved or not owners else 'VALID',**option,TrainerId=0,unresolved_creature_count=len(unresolved),unresolved_creature_examples=unresolved[:20],reason='Zero uses legacy npc_trainer (including one-level reference join); default trainer applies to HandleTrainerListOpcode, not this Gossip path. Runtime spell validation and dynamic owners still matter')
        if m==0:
            owners=npc_menus.get(0,[])
            hidden=[int(n['entry']) for n in owners if not int(n['npcflag'])&int(option['OptionNpcFlag'])]
            emit('DEFAULT_MENU_REVIEW','REVIEW_REQUIRED',MenuId=0,OptionIndex=index,hidden_template_count=len(hidden),creature_examples=hidden[:20],reason='Shared fallback menu0 is filtered per NPC at runtime; do not expand a Cartesian product into supposed broken buttons')
        for npc in ([] if m==0 else npc_menus.get(m,[])):
            entry=int(npc['entry']);mask=int(npc['npcflag']);option_mask=int(option['OptionNpcFlag'])
            if not mask&option_mask:emit('SUSPICIOUS_NPCFLAG','REVIEW_REQUIRED',MenuId=m,OptionIndex=index,entry=entry,npcflag=mask,OptionNpcFlag=option_mask,reason='Native PrepareGossipMenu hides this option; runtime flags or C++ menus can differ')
            expected={'GOSSIP_OPTION_VENDOR':'UNIT_NPC_FLAG_VENDOR','GOSSIP_OPTION_TAXIVENDOR':'UNIT_NPC_FLAG_FLIGHTMASTER','GOSSIP_OPTION_TRAINER':'UNIT_NPC_FLAG_TRAINER'}
            for option_name,flag_name in expected.items():
                if type_==option_types[option_name] and flag_name in flags and not mask&flags[flag_name]:emit('SUSPICIOUS_NPCFLAG','REVIEW_REQUIRED',MenuId=m,OptionIndex=index,entry=entry,expected_flag=flag_name,reason='Service-specific flag is absent in template; runtime/script ownership needs review')
            if npc['AIName']=='SmartAI' and type_==option_types['GOSSIP_OPTION_GOSSIP'] and not destination and not point:
                matching=[s for s in smart[entry,0] if int(s['event_type'])==events['SMART_EVENT_GOSSIP_SELECT'] and int(s['event_param1'])==m and int(s['event_param2'])==index]
                if not matching:emit('MISSING_SMART_EVENT','REVIEW_REQUIRED',entry=entry,MenuId=m,OptionIndex=index,reason='No entry-level binding; GUID scripts, timed/dynamic menus or C++ may own selection')
    for npc in tables['creature_template']:
        entry=int(npc['entry']);select=[s for s in smart[entry,0] if int(s['event_type']) in (events['SMART_EVENT_GOSSIP_SELECT'],events['SMART_EVENT_GOSSIP_HELLO'])]
        if npc['AIName']=='SmartAI' and npc['ScriptName']:
            emit('SMARTAI_CPP_CONFLICT','REVIEW_REQUIRED',**npc,smart_gossip_events=select,cpp_files=locations.get(npc['ScriptName'],[]),reason='AI selection prefers GetAI from ScriptName when non-null; overlap is not proof of double processing')
    for go in tables['gameobject_template']:
        entry=int(go['entry']);kind=int(go['type']);menu=int(go['Data3'] if kind==2 else go['Data19'] if kind==10 else 0)
        if go['AIName']=='SmartGameObjectAI' and go['ScriptName']:
            emit('SMARTAI_CPP_CONFLICT','REVIEW_REQUIRED',**go,target_kind='gameobject',gossip_menu_id=menu,cpp_files=locations.get(go['ScriptName'],[]),smart_gossip_events=[x for x in smart[entry,1] if int(x['event_type']) in (events['SMART_EVENT_GOSSIP_SELECT'],events['SMART_EVENT_GOSSIP_HELLO'])],reason='GO AI/ScriptName overlap needs GetAI and bool handled-contract review')
        if menu and menu not in menus:
            emit('ORPHAN_MENU','REVIEW_REQUIRED',entry=entry,target_kind='gameobject',MenuId=menu,reason='GO points to missing menu title; options and default text need review')
        if menu and go['AIName']=='SmartGameObjectAI':
            for (m,index),option in options.items():
                if m!=menu or int(option['OptionType'])!=option_types['GOSSIP_OPTION_GOSSIP']:continue
                action=actions.get((m,index),{})
                if int(action.get('ActionMenuId',0)) or int(action.get('ActionPoiId',0)):continue
                matching=[x for x in smart[entry,1] if int(x['event_type'])==events['SMART_EVENT_GOSSIP_SELECT'] and int(x['event_param1'])==menu and int(x['event_param2'])==index]
                if not matching:emit('MISSING_SMART_EVENT','REVIEW_REQUIRED',entry=entry,target_kind='gameobject',MenuId=menu,OptionIndex=index,reason='No entry-level binding; GUID script or C++ may own selection')
    for (entry,source_type),rows in smart.items():
        groups=defaultdict(list)
        for row in rows:
            if int(row['event_type'])!=events['SMART_EVENT_GOSSIP_SELECT']:continue
            pair=int(row['event_param1']),int(row['event_param2']);groups[pair].append(row)
            if source_type not in (0,1):emit('SMART_BINDING_MISMATCH','REVIEW_REQUIRED',**row,reason='Gossip select is only allowed for creature/gameobject source types')
            if pair not in options:emit('SMART_BINDING_MISMATCH','REVIEW_REQUIRED',**row,reason='No DB option for menu/index; scripted/dynamic menu or default menu0 remapping may be intentional')
            if int(row['target_type']) in (19,20,22,23) and int(row['target_param1'])==0:emit('SMART_TARGET_REVIEW','REVIEW_REQUIRED',**row,reason='Entry-based target0; inspect native target semantics and event chain')
        for pair,events_ in groups.items():
            if len(events_)>1:emit('DUPLICATE_SMART_EVENT','REVIEW_REQUIRED',entryorguid=entry,source_type=source_type,MenuId=pair[0],OptionIndex=pair[1],rows=events_,reason='Multiple actions, chance and phase-gated branches can be intentional')
    gossip_events={(int(x['entryorguid']),int(x['source_type']),int(x['id'])) for x in tables['smart_scripts'] if int(x['event_type']) in (events['SMART_EVENT_GOSSIP_SELECT'],events['SMART_EVENT_GOSSIP_HELLO'])}
    for condition in tables['conditions']:
        source_type=int(condition['SourceTypeOrReferenceId'])
        if source_type==15 and (int(condition['SourceGroup']),int(condition['SourceEntry'])) not in options:emit('ORPHAN_CONDITION','CONFIRMED_DATA_ERROR',**condition)
        elif source_type==14 and int(condition['SourceGroup']) not in menus:emit('ORPHAN_CONDITION','REVIEW_REQUIRED',**condition)
        elif source_type==22 and (int(condition['SourceEntry']),int(condition['SourceId']),int(condition['SourceGroup'])-1) in gossip_events:emit('SMART_CONDITION_REVIEW','REVIEW_REQUIRED',**condition,reason='Static snapshot cannot evaluate player quest/race/class/map/phase/aura/level/objective state')
    return {'basis':snapshot.get('basis'),'complete':True,'core_option_max':option_types['GOSSIP_OPTION_MAX'],
            'enum_header_sha256':hashlib.sha256((root/'src/server/game/Entities/Creature/GossipDef.h').read_text('utf8').encode('utf8')).hexdigest(),
            'table_counts':{k:len(v) for k,v in tables.items()},'counts':dict(Counter(x['category'] for x in findings)),
            'status_counts':dict(Counter(x['status'] for x in findings)),
            'category_status_counts':{category:dict(Counter(x['status'] for x in findings if x['category']==category)) for category in sorted({x['category'] for x in findings})},
            'findings':findings,'cpp_inventory':cpp,'cpp_hook_counts':dict(Counter(x['hook'] for x in cpp)),
            'limits':['Read-only audit; no repair SQL. Counts refer to selected database snapshot, not production.', 'Missing menu text is not proof that options are unusable.', 'C++ inventory is lexical, not a control-flow proof.', 'Current conditions and player-specific states require client/server reproduction.', 'SmartAI GUID scripts and dynamic/default menus prevent inferring missing handlers as confirmed bugs.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--snapshot',type=Path);p.add_argument('--mysql',default='mysql');p.add_argument('--database');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=3306);p.add_argument('--user',default='root');p.add_argument('--export-snapshot',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if bool(args.snapshot)==bool(args.database):p.error('Choose one of --snapshot or --database')
    snapshot=json.loads(args.snapshot.read_text('utf8')) if args.snapshot else export_database(args)
    if args.export_snapshot:args.export_snapshot.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    report=audit(snapshot,args.root);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('complete','counts')},ensure_ascii=False))


if __name__=='__main__':main()
