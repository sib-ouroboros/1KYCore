from pathlib import Path
import importlib.util,json,copy
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('draft',root/'contrib/tools/campaign_lever_smartai_draft.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
data=json.loads((root/'docs/audit-data/campaign-script-chain-inventory-2026-10-08.json').read_text('utf8'));candidate=next(r for r in data['rows'] if r['entry']==245102)
result=module.translate(candidate)
published=dict(result,source_core_commit=data['source_core_commit'],source_world_sha256=data['source_world_sha256'])
assert published==json.loads((root/'docs/audit-data/campaign-lever-smartai-draft-2026-10-09.json').read_text('utf8'))
assert len(result['native_rows'])==31 and result['status']=='REVIEW_ONLY_NOT_INSTALLABLE'
assert sorted(r['event'] for r in result['translations'])==[47152,47179,47333]
for source,native in zip(candidate['source_rows'],result['native_rows']):
 changed={k for k in source if source[k]!=native[k]}
 assert changed==({'action_type','action_param1','action_param2'} if int(source['action_type'])==205 else set())
assert all(int(r['action_type'])!=205 for r in result['native_rows'])
for field,value in [('action_param1','91'),('action_param2','0'),('action_param3','1')]:
 changed=copy.deepcopy(candidate);row=next(r for r in changed['source_rows'] if int(r['action_type'])==205);row[field]=value
 try:module.translate(changed)
 except ValueError:pass
 else:raise AssertionError('Unsupported criteria configuration accepted')
print('PASS: exact31-row preservation;3 explicit translations; non-scenario, empty and extra-parameter criteria rejected')
