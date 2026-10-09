#!/usr/bin/env python3
"""Prevent unsafe publication of source monk delivery templates."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('brew_audit', ROOT / 'contrib/tools/campaign_brew_chain_audit.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
folder = ROOT / 'docs/audit-data'
def read(name):
    return json.loads((folder / name).read_text(encoding='utf8'))
evidence = read('campaign-brew-client-evidence-2026-10-09.json')
inventory = read('campaign-script-chain-inventory-2026-10-08.json')
result = module.audit(evidence, inventory)
assert result == read('campaign-brew-chain-review-2026-10-09.json')
assert [(r['entry'], r['receiver'], r['client_receiver_aura']) for r in result['rows']] == [(268377,119620,237613),(268378,119619,237611),(268379,119621,237615)]
assert [r['source_aura_matches_client_receiver'] for r in result['rows']] == [False,False,True]
assert all(r['status'] == 'blocked-not-restored' for r in result['rows'])
def reject(mutator):
    changed = copy.deepcopy(evidence)
    mutator(changed)
    try:
        module.audit(changed, inventory)
    except (ValueError, KeyError):
        return
    raise AssertionError('Unsafe client/source dependency accepted')
reject(lambda e: e['summon_properties']['rows'].pop())
reject(lambda e: e['summon_properties']['rows'][0].update(Control=2))
reject(lambda e: e['summon_properties']['rows'][0].update(Flags=0))
reject(lambda e: e['aura_and_goober_effects']['effects']['237611'][0].update(EffectAura=0))
reject(lambda e: e['summon_effects']['effects']['237610'][0].update(MiscValue1=119620))
reject(lambda e: e['source']['waypoints'].pop())
print('PASS: three linked chains, two mismatched removals; missing, public, pet, non-linked, ambiguous and truncated inputs rejected')
