#!/usr/bin/env python3
"""Check current campaign registries agree; historical snapshots remain historical."""
from collections import Counter
import json
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[2]
    folder=root/'docs/audit-data'
    def read(name):return json.loads((folder/name).read_text('utf8'))
    def unique(values,label):
        result=set(values)
        assert len(result)==len(values),f'Duplicate IDs: {label}'
        return result
    templates=read('campaign-restoration-status.json')
    pending=read('campaign-pending-dependencies.json')
    restored=unique(templates['restored_entries'],'restored templates')
    missing=unique(templates['pending_entries'],'pending templates')
    assert restored.isdisjoint(missing)
    assert len(restored|missing)==templates['source_total_templates']
    assert templates['restored_spawns']+templates['pending_spawns']==templates['source_total_spawns']
    assert unique([x['entry'] for x in pending['entries']],'pending details')==missing
    assert pending['remaining_templates']==len(missing)
    assert pending['remaining_spawns']==sum(x['source_spawns'] for x in pending['entries'])==templates['pending_spawns']
    models=read('campaign-remaining-models-2026-10-05.json')
    baseline=read('campaign-placeholder-audit.json')
    missing_models=unique([x['entry'] for x in models['rows']],'remaining models')
    restored_models=unique(baseline['restored_placeholder_entries'],'restored models')
    assert missing_models.isdisjoint(restored_models)
    assert missing_models|restored_models==unique([x['entry'] for x in baseline['source_nonzero_display_candidates']],'model source candidates')
    assert models['remaining_count']==baseline['remaining_placeholder_candidates']==baseline['current_counts']['remaining_models']==len(missing_models)
    assert models['restored_count']==baseline['current_counts']['restored_models']==len(restored_models)
    assert dict(Counter(b for x in models['rows'] for b in x['blockers']))==models['overlapping_blocker_counts']
    conversations=read('campaign-conversation-dependency-review-2026-10-04.json')
    unresolved=unique(conversations['unresolved_ids'],'unresolved conversations')
    covered=unique(conversations['covered_by_other_current_sql_inserts'],'covered conversations')
    details=read('campaign-remaining-conversations-2026-10-05.json')
    assert unresolved.isdisjoint(covered)
    assert len(unresolved|covered)==conversations['distinct_conversation_ids']
    assert unique([x['conversation'] for x in details['rows']],'conversation details')==unresolved
    assert details['count']==len(unresolved)
    assert dict(Counter(b for x in details['rows'] for b in x['blockers']))==details['overlapping_blocker_counts']
    for migration in templates['migrations']+baseline['restoration_migrations']:
        assert (root/'sql/updates/world'/migration).is_file(),f'Missing migration: {migration}'
    print(f'PASS: current campaign counters: {len(unresolved)} conversations, {len(missing)} templates/{pending["remaining_spawns"]} deferred spawns, {len(missing_models)} models')


if __name__=='__main__':main()
