#!/usr/bin/env python3
"""Read-only source SmartScript dependency inventory for every pending campaign GO.

Requires the pinned original world dump and SmartScriptMgr.h; produces JSON only.
Matching enum names are a compatibility screen, never gameplay validation.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

SOURCE_COMMIT = '22bfd97d0e0e30d215e408eb4da2b0419d8f00e7'
SOURCE_SHA = '0265cc795b6507f8918162293e7c905143cdb2ef227ee72179bb43bcf889f68c'


def split_values(text):
    values=[];start=0;quote=None;depth=0;i=0
    while i<len(text):
        c=text[i]
        if quote:
            if c=='\\':i+=1
            elif c==quote:
                if i+1<len(text) and text[i+1]==quote:i+=1
                else:quote=None
        elif c in "'\"`":quote=c
        elif c=='(':depth+=1
        elif c==')':depth-=1
        elif c==',' and depth==0:values.append(text[start:i].strip());start=i+1
        i+=1
    if quote or depth:raise ValueError('Unbalanced SQL values')
    values.append(text[start:].strip());return values


def smart_rows(path):
    schemas={};schema=None;table=None;rows=[]
    with path.open(encoding='utf8') as stream:
        for line in stream:
            m=re.match(r'CREATE TABLE `([^`]+)`',line)
            if m:schema=m[1];schemas[schema]=[]
            elif schema:
                m=re.match(r'\s+`([^`]+)`',line)
                if m:schemas[schema].append(m[1])
                if line.startswith(')'):schema=None
            if line.startswith('INSERT INTO '):table=re.search(r'`([^`]+)`',line)[1]
            if table!='smart_scripts':continue
            if line.startswith('INSERT INTO ') and ' VALUES ' in line:values=line.split(' VALUES ',1)[1].strip().rstrip(';')
            elif line.startswith('('):values=line.strip().rstrip(',;')
            else:continue
            for raw in split_values(values):
                vals=split_values(raw[1:-1]);assert len(vals)==len(schemas[table])
                rows.append(dict(zip(schemas[table],vals)))
    assert rows,'Source SmartScript table empty'
    return rows


def enums(path,prefix):
    return {int(value):name for name,value in re.findall(r'('+prefix+r'\w+)\s*=\s*(\d+)\s*,',path.read_text('utf8'))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-world',type=Path,required=True)
    parser.add_argument('--source-header',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[2];folder=root/'docs/audit-data'
    digest=hashlib.file_digest(args.source_world.open('rb'),'sha256').hexdigest()
    assert digest==SOURCE_SHA,'Wrong original database: refusing an unpinned audit'
    assert hashlib.sha256(args.source_header.read_bytes()).hexdigest()=='2a513b1e9796f91494230a084ef939391aaf180022c36d052e03b00817096445','Wrong pinned source header'
    native=root/'src/server/game/AI/SmartScripts/SmartScriptMgr.h'
    source_actions=enums(args.source_header,'SMART_ACTION_');native_actions=enums(native,'SMART_ACTION_')
    source_events=enums(args.source_header,'SMART_EVENT_');native_events=enums(native,'SMART_EVENT_')
    rows=smart_rows(args.source_world);by_key=defaultdict(list)
    for r in rows:by_key[(int(r['entryorguid']),int(r['source_type']))].append(r)
    models=json.loads((folder/'campaign-remaining-models-2026-10-05.json').read_text())['rows']
    pending=json.loads((folder/'campaign-pending-dependencies.json').read_text())['entries']
    candidates=sorted({x['entry'] for x in models+pending});results=[]
    targets={11:0,19:0,15:1,20:1}
    for entry in candidates:
        keys={(entry,1)};queue=[(entry,1)];edges=[]
        # Include incoming object activation/SetData senders, then outgoing receivers
        # and timed lists. Do not call this a complete spell/event/waypoint graph.
        incoming=[r for r in rows if int(r['target_type']) in (15,20) and int(r['target_param1'])==entry]
        for r in incoming:
            key=(int(r['entryorguid']),int(r['source_type']))
            if key not in keys:keys.add(key);queue.append(key)
        while queue:
            key=queue.pop()
            for r in by_key[key]:
                action=int(r['action_type']);target=int(r['target_type']);dest=None
                if action==80:dest=(int(r['action_param1']),9)
                elif action==45 and target in targets and int(r['target_param1']):dest=(int(r['target_param1']),targets[target])
                if dest:
                    receivers=by_key.get(dest,[])
                    matched=[x['id'] for x in receivers if int(x['event_type'])==38 and x['event_param1']==r['action_param1'] and x['event_param2']==r['action_param2']]
                    edges.append({'from':list(key),'row':int(r['id']),'to':list(dest),'kind':'timed_list' if action==80 else 'set_data','source_rows':len(receivers),'matching_data_set_rows':matched})
                    if dest not in keys:keys.add(dest);queue.append(dest)
        selected=[r for key in sorted(keys) for r in by_key[key]];mismatches=[]
        for r in selected:
            for field,sm,nm in [('action_type',source_actions,native_actions),('event_type',source_events,native_events)]:
                value=int(r[field]);sn=sm.get(value);nn=nm.get(value)
                if sn!=nn or sn is None:
                    mismatches.append({'key':[int(r['entryorguid']),int(r['source_type']),int(r['id'])],'field':field,'value':value,'source':sn,'native':nn})
        results.append({'entry':entry,'own_source_rows':len(by_key.get((entry,1),[])),
            'incoming_rows':len(incoming),'connected_keys':[list(k) for k in sorted(keys)],
            'connected_source_rows':len(selected),'enum_mismatches':mismatches,'edges':edges,
            'conversation_dependencies':sorted({int(r['action_param1']) for r in selected if source_actions.get(int(r['action_type']))=='SMART_ACTION_SUMMON_CONVERSATION'}),
            'source_rows':selected})
    report={'source_core_commit':SOURCE_COMMIT,'source_world_sha256':digest,
        'source_header_sha256':hashlib.sha256(args.source_header.read_bytes()).hexdigest(),
        'native_header_sha256':hashlib.sha256(native.read_text('utf8').encode('utf8')).hexdigest(),
        'candidate_count':len(candidates),'source_smart_rows':len(rows),
        'candidate_enum_mismatches':dict(Counter(str(m['value']) for r in results for m in r['enum_mismatches'] if m['key'][0]==r['entry'] and m['key'][1]==1 and m['field']=='action_type')),
        'scope':'All current absent templates and placeholder models; source GO-entry rows, incoming entry-based targets, outgoing SetData targets and fixed timed lists. GUID targets, random lists, spells, conditions, event/waypoint scripts, client timing and native/release receiver behavior require separate review.',
        'assurance':'Inventory only. Equal enum names do not establish equal parameter/target/lifecycle semantics. No SQL or gameplay changes; no candidate marked restored.',
        'rows':results}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(f'PASS: inventoried {len(candidates)} pending objects from {len(rows)} pinned source SmartScript rows')
    print('Own action-number mismatches:',report['candidate_enum_mismatches'])


if __name__=='__main__':main()
