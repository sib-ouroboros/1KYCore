#!/usr/bin/env python3
"""Audit the entire pinned monk delivery group without changing game data."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def audit(evidence, inventory):
    source = evidence['source']
    effects = evidence['aura_and_goober_effects']['effects']
    summons = evidence['summon_effects']['effects']
    properties = {r['ID']: r for r in evidence['summon_properties']['rows']}
    if set(properties) != {4031, 4032, 4033}:
        raise ValueError('Incomplete summon properties, including copied records')
    for ident, record in properties.items():
        if record['Control'] != 1 or record['Title'] != 0 or not record['Flags'] & 16:
            raise ValueError(f'Unexpected summon ownership/visibility for {ident}')
    aura_by_creature = {}
    for aura in (237611, 237613, 237615):
        rows = effects[str(aura)]
        if len(rows) != 1 or rows[0]['Effect'] != 6 or rows[0]['EffectAura'] != 428:
            raise ValueError(f'Unexpected linked summon aura {aura}')
        spawn = summons[str(rows[0]['TriggerSpell'])]
        if len(spawn) != 1 or spawn[0]['Effect'] != 28 or spawn[0]['MiscValue2'] not in properties:
            raise ValueError(f'Unexpected summon chain for {aura}')
        creature = spawn[0]['MiscValue1']
        if creature in aura_by_creature:
            raise ValueError('Ambiguous aura ownership')
        aura_by_creature[creature] = aura
    candidates = {r['entry']: r for r in inventory['rows']}
    rows = []
    for entry in (268377, 268378, 268379):
        candidate = candidates[entry]
        own = [r for r in candidate['source_rows'] if int(r['entryorguid']) == entry and int(r['source_type']) == 1]
        def action(kind):
            found = [r for r in own if int(r['action_type']) == kind]
            if len(found) != 1:
                raise ValueError(f'Unexpected action chain {entry}/{kind}')
            return found[0]
        select, credit, remove = action(45), action(33), action(28)
        if int(select['target_type']) != 19 or int(select['action_param1']) != 1 or int(select['action_param2']) != 1:
            raise ValueError('Unexpected delivery receiver protocol')
        receiver = int(select['target_param1'])
        aura = aura_by_creature[receiver]
        waypoints = sorted((r for r in source['waypoints'] if int(r['entry']) == receiver), key=lambda r: int(r['pointid']))
        if [int(r['pointid']) for r in waypoints] != [1, 2]:
            raise ValueError('Incomplete source return route')
        if not any(m['value'] == 207 and m['source'] == 'SMART_ACTION_SUMMON_ADD_PLR_PERSONNAL_VISIBILE' and m['native'] == 'SMART_ACTION_MODIFY_THREAT' for m in candidate['enum_mismatches']):
            raise ValueError('Personal visibility action collision no longer matches inventory')
        source_aura = int(remove['action_param1'])
        rows.append(dict(entry=entry, receiver=receiver, credit=int(credit['action_param1']),
                         source_removed_aura=source_aura, client_receiver_aura=aura,
                         source_aura_matches_client_receiver=source_aura == aura,
                         route=waypoints, status='blocked-not-restored',
                         blockers=['linked-aura-removal-despawns-returning-summon',
                                   'source-action-207-is-native-modify-threat',
                                   'owner-scoped-receiver-selection-required',
                                   'target-client-and-source-hotfix-validation-required']))
    return dict(source_core_commit=inventory['source_core_commit'],
                source_world_sha256=inventory['source_world_sha256'],
                candidate_count=len(rows), rows=rows,
                assurance='Decoded client evidence identifies discrepancies; no SQL, AI, spawn or restoration change.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    folder = ROOT / 'docs/audit-data'
    def read(name):
        return json.loads((folder / name).read_text(encoding='utf8'))
    result = audit(read('campaign-brew-client-evidence-2026-10-09.json'),
                   read('campaign-script-chain-inventory-2026-10-08.json'))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
    print(f"PASS: {result['candidate_count']} complete delivery chains; two source/client aura discrepancies")


if __name__ == '__main__':
    main()
