#!/usr/bin/env python3
"""Conflict/retry checks for two GENERIC objects, on a disposable MySQL DB."""
import json
from pathlib import Path

def test_required_level_objects(sql, checksum):
 root=Path(__file__).resolve().parents[2]
 manifest=json.loads((root/'docs/audit-data/campaign-required-level-restoration.json').read_text('utf8'))
 content=(root/'sql/updates/world/2026_10_05_08_world_campaign_required_level_objects.sql').read_text('utf8')
 schema=(root/'sql/updates/world/2026_10_05_03_world_gameobject_visual_fields.sql').read_text('utf8')
 sql(schema)
 ids=','.join(map(str,manifest['entries']));guids=','.join(s['guid'] for s in manifest['spawns'])
 owned=['gameobject_template','gameobject_template_addon','gameobject']
 tables=sql('SHOW TABLES;').stdout.splitlines()
 protected=[t for t in tables if t not in owned]
 original=checksum(tables)
 assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN({ids});').stdout.strip()=='0'
 assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN({guids});').stdout.strip()=='0'
 def insert(table,row):
  sql('INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');')
 def clear():
  sql(f'DELETE FROM gameobject WHERE guid IN({guids});DELETE FROM gameobject_template WHERE entry IN({ids});DELETE FROM gameobject_template_addon WHERE entry IN({ids});')
 def rejected():
  before=checksum(tables);error=sql(content,ok=False)
  assert 'Duplicate entry' in error.stderr and '_1kycore_level_guard' in error.stderr,error.stderr
  assert checksum(tables)==before,'Rejection changed permanent rows'
 def exact():
  for table,key in [('gameobject_template','templates'),('gameobject_template_addon','addons'),('gameobject','spawns')]:
   for row in manifest[key]:
    filters=[]
    for k,v in row.items():
     if k=='VerifiedBuild':continue
     if k in ('size','position_x','position_y','position_z','orientation','rotation0','rotation1','rotation2','rotation3'):
      filters.append(f'ABS(`{k}`-({v}))<=0.001')
     else:filters.append('BINARY `'+k+'` <=> BINARY '+v)
    assert sql('SELECT COUNT(*) FROM '+table+' WHERE '+' AND '.join(filters)+';').stdout.strip()=='1',(table,row)
  assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN({ids}) AND RequiredLevel=100 AND type=5;').stdout.strip()=='2'
 untouched=checksum(protected)
 sql(content);exact();once=checksum(tables);sql(content);assert checksum(tables)==once
 assert checksum(protected)==untouched,'Unrelated tables changed'
 # Matching provenance is retained, not overwritten by old source build.
 sql(f'UPDATE gameobject_template SET VerifiedBuild=26972 WHERE entry IN({ids});')
 sql(content);assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN({ids}) AND VerifiedBuild=26972;').stdout.strip()=='2'
 for alteration in ("name='Custom object'",'RequiredLevel=80','displayId=12345','Data32=99',"AIName='SmartGameObjectAI'", "ScriptName='custom_scene'"):
  clear();sql(content);sql('UPDATE gameobject_template SET '+alteration+' WHERE entry=269053;');rejected()
 for field in ('flags','WorldEffectID','SpellVisualID','SpellStateVisualID','StateWorldEffectID'):
  clear();sql(content);sql('UPDATE gameobject_template_addon SET '+field+'=99 WHERE entry=269053;');rejected()
 clear();sql(content);sql('DELETE FROM gameobject_template_addon WHERE entry=269053;');rejected()
 clear();row=dict(manifest['spawns'][0]);row['id']='123456';insert('gameobject',row);rejected()
 clear();sql('INSERT INTO gameobject_questitem (GameObjectEntry,ItemId) VALUES(269053,123456);');rejected();sql('DELETE FROM gameobject_questitem WHERE GameObjectEntry=269053;')
 for entry in ('269053','-'+manifest['spawns'][0]['guid']):
  sql('INSERT INTO smart_scripts (entryorguid,source_type,id,comment) VALUES('+entry+',1,0,\'fixture\');');rejected();sql('DELETE FROM smart_scripts WHERE entryorguid='+entry+' AND source_type=1;')
 sql('INSERT INTO conditions (SourceTypeOrReferenceId,SourceGroup,SourceEntry,SourceId,ElseGroup,ConditionTypeOrReference,ConditionTarget,ConditionValue1,ConditionValue2,ConditionValue3,NegativeCondition,ErrorType,ErrorTextId,ScriptName,Comment) VALUES(31,0,269053,0,0,1,0,1,0,0,0,0,0,\'\',\'fixture\');');rejected();sql('DELETE FROM conditions WHERE SourceEntry=269053;')
 # Every statement boundary, including interrupted permanent inserts.
 statements=content.split(';')
 for i in range(1,len(statements)):
  clear();sql(';'.join(statements[:i])+';');sql(content);exact()
 clear();assert checksum(tables)==original,'Test left changed release content'
 print('PASS: RequiredLevel100 mapping; first/repeat import, custom/dependency guards, all interrupted prefixes, unrelated tables preserved',flush=True)
