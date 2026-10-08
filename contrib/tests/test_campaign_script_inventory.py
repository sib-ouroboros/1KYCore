#!/usr/bin/env python3
"""Keep the published source dependency inventory tied to current candidate IDs."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def main():
    root=Path(__file__).resolve().parents[2];folder=root/'docs/audit-data'
    def read(name):return json.loads((folder/name).read_text('utf8'))
    report=read('campaign-script-chain-inventory-2026-10-08.json')
    candidates={x['entry'] for x in read('campaign-remaining-models-2026-10-05.json')['rows']}|{x['entry'] for x in read('campaign-pending-dependencies.json')['entries']}
    rows=report['rows'];assert len(rows)==len({r['entry'] for r in rows})
    assert {r['entry'] for r in rows}==candidates and report['candidate_count']==len(candidates)
    header=root/'src/server/game/AI/SmartScripts/SmartScriptMgr.h'
    assert hashlib.sha256(header.read_text('utf8').encode('utf8')).hexdigest()==report['native_header_sha256'],'Native enum changed: rerun pinned source audit'
    actions={int(v):n for n,v in re.findall(r'(SMART_ACTION_\w+)\s*=\s*(\d+)\s*,',header.read_text('utf8'))}
    events={int(v):n for n,v in re.findall(r'(SMART_EVENT_\w+)\s*=\s*(\d+)\s*,',header.read_text('utf8'))}
    own=Counter()
    for r in rows:
        keys={tuple(k) for k in r['connected_keys']};assert (r['entry'],1) in keys
        selected=r['source_rows'];assert len(selected)==r['connected_source_rows']
        identities={(int(x['entryorguid']),int(x['source_type']),int(x['id'])) for x in selected}
        assert len(identities)==len(selected),'Duplicate source row'
        assert r['own_source_rows']==sum(int(x['entryorguid'])==r['entry'] and int(x['source_type'])==1 for x in selected)
        for edge in r['edges']:
            assert tuple(edge['from']) in keys and tuple(edge['to']) in keys
            assert (*edge['from'],edge['row']) in identities
            receiver=[x for x in selected if (int(x['entryorguid']),int(x['source_type']))==tuple(edge['to'])]
            assert len(receiver)==edge['source_rows']
            for identifier in edge['matching_data_set_rows']:assert any(x['id']==identifier and int(x['event_type'])==38 for x in receiver)
        for mismatch in r['enum_mismatches']:
            assert tuple(mismatch['key']) in identities
            mapping=actions if mismatch['field']=='action_type' else events
            assert mapping.get(mismatch['value'])==mismatch['native']
            assert mismatch['source']!=mismatch['native'] or mismatch['source'] is None
            if mismatch['key'][:2]==[r['entry'],1] and mismatch['field']=='action_type':own[str(mismatch['value'])]+=1
    assert dict(own)==report['candidate_enum_mismatches']
    for entry in (268377,268378,268379):
        r=next(x for x in rows if x['entry']==entry)
        assert any(m['value']==207 and m['source']=='SMART_ACTION_SUMMON_ADD_PLR_PERSONNAL_VISIBILE' and m['native']=='SMART_ACTION_MODIFY_THREAT' for m in r['enum_mismatches'])
    print(f'PASS: {len(candidates)} current campaign objects, dependency edges and source/native action collisions')


if __name__=='__main__':main()
