"""Missing native quest-item objects; caller must use a disposable release copy."""
import json
from pathlib import Path
def test_gilneas_memento_database(sql,checksum):
 root=Path(__file__).resolve().parents[2]
 text=(root/'sql/updates/world/2026_10_09_01_world_gilneas_mementos.sql').read_text('utf8')
 manifest=json.loads((root/'docs/audit-data/gilneas-memento-restoration.json').read_text('utf8'))
 tables=sql('SHOW TABLES;').stdout.splitlines()
 sql('DELETE FROM gameobject WHERE id=201871 AND map=654;')
 other=checksum([t for t in tables if t!='gameobject'])
 sql(text)
 assert sql('SELECT COUNT(*) FROM gameobject WHERE id=201871 AND map=654 AND PhaseId=188;').stdout.strip()=='17'
 for row in manifest['rows']:
  assert sql(f"SELECT COUNT(*) FROM gameobject WHERE guid={row['guid']} AND id=201871 AND ABS(position_x-({row['x']}))<0.001 AND ABS(position_y-({row['y']}))<0.001 AND ABS(position_z-({row['z']}))<0.001 AND rotation3=1;").stdout.strip()=='1'
 assert checksum([t for t in tables if t!='gameobject'])==other,'Unrelated tables changed'
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Repeat import changed data'
 sql('DELETE FROM gameobject WHERE id=201871 AND map=654;')
 for change,restore in [
  ("UPDATE gameobject_template SET ScriptName='custom_memento' WHERE entry=201871;","UPDATE gameobject_template SET ScriptName='' WHERE entry=201871;"),
  ('UPDATE gameobject_template SET Data1=0 WHERE entry=201871;','UPDATE gameobject_template SET Data1=201871 WHERE entry=201871;'),
  ('UPDATE gameobject_loot_template SET Chance=50 WHERE Entry=201871 AND Item=49921;','UPDATE gameobject_loot_template SET Chance=100 WHERE Entry=201871 AND Item=49921;'),
  ('UPDATE quest_objectives SET Amount=1 WHERE QuestID=24602 AND ObjectID=49921;','UPDATE quest_objectives SET Amount=5 WHERE QuestID=24602 AND ObjectID=49921;'),
  ('UPDATE creature SET PhaseId=187 WHERE guid=803966;','UPDATE creature SET PhaseId=188 WHERE guid=803966;'),
  ('INSERT INTO gameobject (guid,id,map,position_x,position_y,position_z) VALUES(4290000200,201871,654,1,2,3);','DELETE FROM gameobject WHERE guid=4290000200;'),
  ('INSERT INTO gameobject (guid,id,map,position_x,position_y,position_z) VALUES(310065200,196472,1,1,2,3);','DELETE FROM gameobject WHERE guid=310065200;')]:
  sql(change);before=checksum(tables);sql(text);assert checksum(tables)==before,'Dependency/custom spawn/GUID guard failed';sql(restore)
 sql(text)
 print('PASS: Mementos17 sourced positions, first/repeat import, template/loot/objective/phase/custom spawn/GUID guards and unrelated preservation')
