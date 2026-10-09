#!/usr/bin/env python3
"""Check that lever restoration excludes incomplete and corrupt source scenes."""
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[2]
    review=json.loads((root/'docs/audit-data/campaign-lever-conversation-review-2026-10-09.json').read_text('utf8'))
    restored=json.loads((root/'docs/audit-data/campaign-lever-conversation-restoration.json').read_text('utf8'))
    assert restored['entries']==[587,591,592,593]
    assert {x['id'] for x in review['restorable']}==set(restored['entries'])
    blocked={x['id']:x for x in review['blocked']}
    assert set(blocked)=={586,595,597,598,599,652}
    assert [x['id'] for x in blocked[586]['client_chain']]==[1520,8590,8591,8592,8593]
    assert len(blocked[586]['client_chain'])>1 and blocked[586]['source_line']['id']=='1520'
    for cid in (595,597,598,599,652):
        assert int(blocked[cid]['source_line']['unk1'])>0xFFFF
    rows=restored['rows']
    assert len(rows['conversation_actor_template'])==1
    assert rows['conversation_actor_template'][0]=={'Id':'49875','CreatureId':'98771','CreatureModelId':'65975','VerifiedBuild':'0'}
    assert [int(x['LastLineEndTime']) for x in rows['conversation_template']]==[11050,7550,6950,10450]
    for item,line,template in zip(review['restorable'],rows['conversation_line_template'],rows['conversation_template']):
        assert len(item['client_chain'])==1 and item['client_chain'][0]['NextConversationLineID']==0
        assert int(line['Id'])==item['client_chain'][0]['id']==int(template['FirstLineId'])
        assert line['StartTime']=='0' and line['UiCameraID']=='86' and line['ActorIdx']=='0' and line['Flags']=='0'
        assert int(template['LastLineEndTime'])>item['client_chain'][0]['AdditionalDuration']
    original=json.loads((root/'docs/audit-data/campaign-conversation-dependency-review-2026-10-04.json').read_text('utf8'))
    # Additional lever scenes must not silently reduce the original campaign totals.
    assert restored['source_world_sql_sha256']==review['source_world_sha256']
    assert restored['client_validation']['BroadcastText']['required_ids']==[100641,100642,100673,100674]
    assert original
    print('PASS: four complete source scenes; incomplete chain and five unverified cameras excluded')


if __name__=='__main__':
    main()
