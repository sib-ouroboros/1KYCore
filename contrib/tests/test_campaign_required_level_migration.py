#!/usr/bin/env python3
"""Conflict/retry checks for source-compatible object groups, on a disposable MySQL DB."""
import json
from pathlib import Path

def test_required_level_objects(sql, checksum, registry_name="campaign-required-level-restoration.json", migration_name="2026_10_05_08_world_campaign_required_level_objects.sql"):
 root=Path(__file__).resolve().parents[2]
 manifest=json.loads((root/'docs/audit-data'/registry_name).read_text('utf8'))
 content=(root/'sql/updates/world'/migration_name).read_text('utf8')
 schema=(root/'sql/updates/world/2026_10_05_03_world_gameobject_visual_fields.sql').read_text('utf8')
 sql(schema)
 if any('SpellStateAnimID' in row for row in manifest['addons']):
  sql((root/'sql/updates/world/2026_10_08_00_world_gameobject_state_animation.sql').read_text('utf8'))
 first=str(manifest['entries'][0])
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
 def rejected(context=""):
  before=checksum(tables);error=sql(content,ok=False)
  assert 'Duplicate entry' in error.stderr and '_1kycore_level_guard' in error.stderr,error.stderr
  after=checksum(tables)
  assert after==before,('Rejection changed permanent rows',context,before,after)
 def exact():
  for table,key in [('gameobject_template','templates'),('gameobject_template_addon','addons'),('gameobject','spawns')]:
   for row in manifest[key]:
    filters=[]
    for k,v in row.items():
     if k=='VerifiedBuild':continue
     if k in ('size','position_x','position_y','position_z','orientation','rotation0','rotation1','rotation2','rotation3'):
      filters.append(f'ABS(`{k}`-({v}))<=0.001')
     else:filters.append('BINARY `'+k+'` <=> BINARY '+v)
    count=sql('SELECT COUNT(*) FROM '+table+' WHERE '+' AND '.join(filters)+';').stdout.strip()
    if count!='1':
     identity='guid' if table=='gameobject' else 'entry'
     actual=sql(f'SELECT * FROM `{table}` WHERE `{identity}`={row[identity]};').stdout
     truth=sql('SELECT '+','.join(filters)+f' FROM `{table}` WHERE `{identity}`={row[identity]};').stdout
     raise AssertionError((table,row,count,actual,truth))

 untouched=checksum(protected)
 sql(content);exact();once=checksum(tables);sql(content);assert checksum(tables)==once
 assert checksum(protected)==untouched,'Unrelated tables changed'
 # Matching provenance is retained, not overwritten by old source build.
 sql(f'UPDATE gameobject_template SET VerifiedBuild=26972 WHERE entry IN({ids});')
 sql(content);assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN({ids}) AND VerifiedBuild=26972;').stdout.strip()==str(len(manifest['entries']))
 # All substantive fields in both templates/addons and the pinned spawns.
 for table,key,identity in [('gameobject_template','templates','entry'),('gameobject_template_addon','addons','entry'),('gameobject','spawns','guid')]:
  for row in manifest[key]:
   for field,value in row.items():
    if field in (identity,'VerifiedBuild'):continue
    altered="'custom_fixture'" if value.startswith("'") else ('0' if float(value)!=0 else '1')
    sql(f'UPDATE `{table}` SET `{field}`={altered} WHERE `{identity}`={row[identity]};')
    rejected((table,row[identity],field))
    sql(f'UPDATE `{table}` SET `{field}`={value} WHERE `{identity}`={row[identity]};')
 clear();sql(content);sql('DELETE FROM gameobject_template_addon WHERE entry='+first+';');rejected()
 clear();row=dict(manifest['spawns'][0]);row['id']='123456';insert('gameobject',row);rejected()
 clear();sql(f'INSERT INTO gameobject_questitem (GameObjectEntry,ItemId) VALUES({first},123456);');rejected();sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={first};')
 for entry in (first,'-'+manifest['spawns'][0]['guid']):
  sql('INSERT INTO smart_scripts (entryorguid,source_type,id,comment) VALUES('+entry+',1,0,\'fixture\');');rejected();sql('DELETE FROM smart_scripts WHERE entryorguid='+entry+' AND source_type=1;')
 sql(f'INSERT INTO conditions (SourceTypeOrReferenceId,SourceGroup,SourceEntry,SourceId,ElseGroup,ConditionTypeOrReference,ConditionTarget,ConditionValue1,ConditionValue2,ConditionValue3,NegativeCondition,ErrorType,ErrorTextId,ScriptName,Comment) VALUES(31,0,{first},0,0,1,0,1,0,0,0,0,0,\'\',\'fixture\');');rejected();sql(f'DELETE FROM conditions WHERE SourceEntry={first};')
 if registry_name=='campaign-scenario-object-restoration.json':
  # A user-owned spawn or unexpected loot must not be adopted by a new script.
  for published in (False,True):
   clear()
   if published:sql(content)
   extra=dict(manifest['spawns'][0]);extra['guid']='4290001234';insert('gameobject',extra)
   try:rejected('extra spawn with candidate entry')
   finally:sql('DELETE FROM gameobject WHERE guid=4290001234;')
  clear();sql(content)
  sql(f'INSERT INTO gameobject_loot_template (Entry,Item,Chance,MinCount,MaxCount) VALUES({first},146310,100,1,1);')
  try:rejected('unexpected loot dependency')
  finally:sql(f'DELETE FROM gameobject_loot_template WHERE Entry={first};')
  sql(f"INSERT INTO conditions (SourceTypeOrReferenceId,SourceGroup,SourceEntry,SourceId,ElseGroup,ConditionTypeOrReference,ConditionTarget,ConditionValue1,ConditionValue2,ConditionValue3,NegativeCondition,ErrorType,ErrorTextId,ScriptName,Comment) VALUES(31,0,7777777,0,0,31,0,5,{first},0,0,0,0,'','fixture');")
  try:rejected('indirect gameobject condition')
  finally:sql('DELETE FROM conditions WHERE SourceEntry=7777777;')
 # Every statement boundary, including interrupted permanent inserts.
 statements=content.split(';')
 for i in range(1,len(statements)):
  clear();sql(';'.join(statements[:i])+';');sql(content);exact()
 clear();assert checksum(tables)==original,'Test left changed release content'
 print('PASS: '+registry_name+'; every content field, first/repeat/provenance, custom/dependency guards, all interrupted prefixes and unrelated tables preserved',flush=True)
