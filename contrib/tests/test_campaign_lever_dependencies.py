"""Keep all discovered lever dependencies explicit; reject incomplete review data."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[2];folder=root/'docs/audit-data'
proof=json.loads((folder/'campaign-lever-dependencies-2026-10-09.json').read_text('utf8'));draft=json.loads((folder/'campaign-lever-smartai-draft-2026-10-09.json').read_text('utf8'))
assert proof['source_world_sha256']==draft['source_world_sha256']
assert len(proof['source_condition_files_sha256'])==4 and all(len(x)==64 for x in proof['source_condition_files_sha256'].values())
routes=proof['rows']['waypoints'];assert {(int(r['entry']),int(r['pointid'])) for r in routes}=={(98836,1),(9883600,1)}
texts=proof['rows']['creature_text'];assert len(texts)==1 and texts[0]['Entry']=='98771' and texts[0]['GroupID']=='0'
conditions=proof['rows']['conditions'];gate=next(r for r in conditions if r['SourceTypeOrReferenceId']=='22');assert (gate['ConditionTypeOrReference'],gate['ConditionValue1'],gate['ConditionValue2'])==('44','962','0')
target=next(r for r in conditions if r['SourceTypeOrReferenceId']=='13');assert (target['SourceEntry'],target['ConditionValue2'])==('199336','98836')
steps=proof['client_scenario_steps']['rows'];assert len(steps)==6 and sorted(r['OrderIndex'] for r in steps)==list(range(6)) and all(r['ScenarioID']==962 and r['Flags']==0 for r in steps)
effects=proof['client_spell_effects']['effects'];assert set(map(int,effects))==set(proof['spells']) and all(effects.values())
conversations=sorted({e['MiscValue1'] for rows in effects.values() for e in rows if e['Effect']==219});assert conversations==proof['spell_conversation_ids']==[586,587,591,592,593,595,597,598,599,652]
assert not proof['spell_conversations_present_in_clean_release']
assert proof['additional_conversation_dependencies_not_in_original_98']==conversations
assert effects['199338'][0]['EffectAura']==293 and effects['199338'][0]['MiscValue1']==643
assert proof['client_override_spells']['rows'][0]['Spells']==[199336]+[0]*9
assert effects['199336'][0]['Effect']==3 and effects['199336'][0]['ImplicitTarget1']==38
assert proof['condition_translation_status'].startswith('REVIEW_ONLY')
print('PASS: both routes, source dialogue, both conditions,16 spells,10 extra conversations,6 scenario steps and override-button chain remain explicit and unactivated')
