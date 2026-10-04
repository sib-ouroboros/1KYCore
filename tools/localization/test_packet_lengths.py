#!/usr/bin/env python3
"""Audit accepted UTF8 bytes against actual current-core packet length bit fields.

Read-only static test; client substitutions/printf expansion/gameplay are not simulated.
Gameobject names/captions use NUL-terminated strings in a sized payload, not these bits.
"""
import argparse,gzip,json,re
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--bundle-root',type=Path);a=p.parse_args()
    root=a.root;packets=root/'src/server/game/Server/Packets'
    text={n:(packets/(n+'Packets.cpp')).read_bytes().decode('latin1') for n in ('Quest','Query','NPC','Chat')}
    def limit(file,expression,terminator=0):
        matches=re.findall(r'WriteBits\(\s*'+re.escape(expression)+r'\s*,\s*(\d+)\s*\)',text[file])
        if not matches or len(set(matches))!=1:raise ValueError('Missing/ambiguous packet field: '+expression)
        return (1<<int(matches[0]))-1-terminator
    caps={}
    for field in ('LogTitle','LogDescription','QuestDescription','AreaDescription','PortraitGiverText','PortraitGiverName','PortraitTurnInText','PortraitTurnInName','QuestCompletionLog'):
        caps[('quests',field)]=limit('Quest','Info.'+field+'.size()')
    for cat,field,expr in (('objectives','Description','questObjective.Description.size()'),('rewards','RewardText','RewardText.size()'),('requests','CompletionText','CompletionText.size()'),('choices','Question','Question.length()')):
        caps[(cat,field)]=limit('Quest',expr)
    for field in ('Header','Answer','Description','Confirmation'):caps[('responses',field)]=limit('Quest','playerChoiceResponse.'+field+'.length()')
    caps[('pages','Text')]=limit('Query','page.Text.length()')
    for field,expr in (('Name','Stats.Name[i].length() + 1'),('NameAlt','Stats.NameAlt[i].length() + 1'),('Title','Stats.Title.length() + 1'),('TitleAlt','Stats.TitleAlt.length() + 1')):
        caps[('npcs',field)]=limit('Query',expr,1)
    for field,expr in (('OptionText','options.Text.size()'),('BoxText','options.Confirm.size()')):caps[('gossip',field)]=limit('NPC',expr)
    caps[('pointers','Name')]=limit('NPC','Name.length()')
    chat=min(limit('Chat',e) for e in ('ChatText.length()','NotifyText.size()','MessageText.length()'))
    caps[('server_strings','content_loc8')]=chat
    for f in ('Text_lang','Text1_lang'):caps[('broadcast',f)]=chat
    bundle=a.bundle_root or root/'sql/optional/ruRU/2026-10-04'
    checked=0;db_only=0
    for db in ('world','hotfix','poi'):
        with gzip.open(bundle/db/'accepted-fields.jsonl.gz','rt',encoding='utf8') as f:
            for line in f:
                r=json.loads(line);cap=caps.get((r['category'],r['field']))
                if cap is None:
                    if r['category']!='objects':raise ValueError('Unmapped accepted packet field')
                    db_only+=1;continue
                if len(r['proposal'].encode('utf8'))>cap:raise ValueError('UTF8 packet overflow: '+str((r['category'],r['key'],r['field'],cap)))
                checked+=1
    print('PASS: actual packet bit bounds for',checked,'accepted fields;',db_only,'gameobject fields use sized NUL-terminated payload; SQL/schema lengths separately tested')
if __name__=='__main__':main()
