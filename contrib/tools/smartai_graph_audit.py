#!/usr/bin/env python3
"""Read-only SmartAI LINK validator on an explicitly supplied DB row snapshot.

Raw-DB topology is not the loader's post-validation graph: resource rejection
can remove nodes. Never report runtime validity based on this report alone.
"""
import argparse
from collections import defaultdict,Counter
import json
from pathlib import Path


def validate(rows):
    grouped=defaultdict(list);findings=[]
    for row in rows:grouped[(int(row['entryorguid']),int(row['source_type']))].append(row)
    for (entry,source),data in sorted(grouped.items()):
        ids=Counter(int(r['id']) for r in data);by_id={int(r['id']):r for r in data}
        def add(kind,event):findings.append({'entryorguid':entry,'source_type':source,'event_id':event,'category':kind,'severity':'P1','status':'NEEDS_SOURCE_DATA'})
        for event,count in ids.items():
            if count>1:add('DUPLICATE_EVENT_ID',event)
        edges={};incoming=Counter()
        for r in data:
            event,link=int(r['id']),int(r['link'])
            if link:
                if event==link:add('SELF_LINK',event)
                if link not in by_id:add('MISSING_DESTINATION',event)
                elif int(by_id[link]['event_type'])!=61:add('DESTINATION_NOT_LINK_EVENT',event)
                else:edges[event]=link;incoming[link]+=1
        for r in data:
            event=int(r['id'])
            if int(r['event_type'])==61 and not incoming[event]:add('ORPHAN_LINK_EVENT',event)
        # Iterative walks avoid recursion limits on corrupted long chains.
        completed=set();cycles=set()
        for start in sorted(by_id):
            trail=[];positions={};event=start
            while event in edges and event not in completed:
                if event in positions:
                    cycle=tuple(sorted(trail[positions[event]:]));cycles.add(cycle);break
                positions[event]=len(trail);trail.append(event);event=edges[event]
            completed.update(trail)
        for cycle in sorted(cycles):
            if len(cycle)>1:add('MULTI_NODE_CYCLE',list(cycle))
        # Timed action lists (source9) execute in sequence, not by LINK dispatch.
        if source!=9:
            reachable=set();todo=[int(r['id']) for r in data if int(r['event_type'])!=61]
            while todo:
                event=todo.pop()
                if event in reachable:continue
                reachable.add(event)
                if event in edges:todo.append(edges[event])
            for r in data:
                event=int(r['id'])
                if int(r['event_type'])==61 and event not in reachable:add('UNREACHABLE_LINK_EVENT',event)
    return {'graph_count':len(grouped),'row_count':len(rows),'scope':'raw snapshot only; resource-rejected runtime graph requires startup log','findings':findings,'category_counts':dict(Counter(x['category'] for x in findings))}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--fail-on-integrity',action='store_true');a=p.parse_args()
    snapshot=json.loads(a.snapshot.read_text('utf8'));report=validate(snapshot['smart_scripts']);report['provenance']=snapshot['provenance'];a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report['category_counts']))
    return int(a.fail_on_integrity and bool(report['findings']))


if __name__=='__main__':raise SystemExit(main())
