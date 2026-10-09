#!/usr/bin/env python3
"""Prepare a review-only SmartAI draft; never import it into a world database."""
import argparse
import copy
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def translate(candidate):
    if candidate['entry']!=245102 or candidate['connected_source_rows']!=31:
        raise ValueError('Unexpected pinned lever chain')
    allowed={(98771,9,5),(98836,0,5),(98836,0,9)}
    for mismatch in candidate['enum_mismatches']:
        if tuple(mismatch['key']) not in allowed or mismatch['value']!=205 or mismatch['field']!='action_type' or mismatch['source']!='SMART_ACTION_UPDATE_ACHIEVEMENT_CRITERIA':
            raise ValueError('Unreviewed enum mismatch')
    result=copy.deepcopy(candidate['source_rows']);changed=[]
    for row in result:
        key=tuple(int(row[name]) for name in ('entryorguid','source_type','id'))
        if int(row['action_type'])!=205:continue
        if key not in allowed or int(row['action_param1'])!=92 or any(int(row['action_param'+str(i)]) for i in range(3,7)) or int(row['action_param2'])<=0:
            raise ValueError('Only SEND_EVENT_SCENARIO criteria can be translated')
        event=int(row['action_param2']);row['action_type']='250';row['action_param1']=str(event);row['action_param2']='0'
        changed.append({'key':list(key),'source_action':205,'source_criteria_type':92,'native_action':250,'event':event})
    if {tuple(r['key']) for r in changed}!=allowed:raise ValueError('Incomplete translated event chain')
    return {'status':'REVIEW_ONLY_NOT_INSTALLABLE','entry':245102,'native_rows':result,'translations':changed,
            'blocked_on':['source-and-native-route-activation-semantics','waypoints-and-creature-text','spell-targets-and-effects','scenario-step-and-owner-lifecycle','guarded-SQL-and-client-playthrough']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    data=json.loads((ROOT/'docs/audit-data/campaign-script-chain-inventory-2026-10-08.json').read_text('utf8'))
    candidate=next(r for r in data['rows'] if r['entry']==245102);result=translate(candidate)
    result['source_core_commit']=data['source_core_commit'];result['source_world_sha256']=data['source_world_sha256']
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('PASS:31 review-only rows,3 scenario event translations; no DB access or activation')
if __name__=='__main__':main()
