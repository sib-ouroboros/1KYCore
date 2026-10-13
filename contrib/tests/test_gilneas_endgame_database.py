"""Native Endgame routes: disposable schema, whole-group/custom-data preservation."""
import json
from pathlib import Path
def test_gilneas_endgame_database(sql,checksum):
 root=Path(__file__).resolve().parents[2];manifest=json.loads((root/'docs/audit-data/gilneas-endgame-source-routes.json').read_text('utf8'));text=(root/'sql/updates/world/2026_10_10_00_world_gilneas_endgame_routes.sql').read_text('utf8')
 ids=','.join(str(x['id']) for x in manifest['routes']);tables=sql('SHOW TABLES;').stdout.splitlines()
 sql('DELETE FROM waypoint_data WHERE id IN('+ids+');')
 foreign=sql('SELECT * FROM waypoint_data WHERE id NOT IN('+ids+') ORDER BY id,point;').stdout
 other=checksum([t for t in tables if t!='waypoint_data']);sql(text)
 assert sql('SELECT COUNT(*) FROM waypoint_data WHERE id IN('+ids+');').stdout.strip()=='48'
 for route in manifest['routes']:
  for row in route['points']:
   key,point,x,y,z,o,delay,mode,action,chance,guid=row
   assert sql(f'SELECT COUNT(*) FROM waypoint_data WHERE id={key} AND point={point} AND ABS(position_x-({x}))<0.001 AND ABS(position_y-({y}))<0.001 AND ABS(position_z-({z}))<0.001 AND ABS(orientation-({o}))<0.0001 AND delay={delay} AND move_type={mode} AND action={action} AND action_chance={chance} AND wpguid={guid};').stdout.strip()=='1'
 before=checksum(['waypoint_data','creature_template']);sql(text);assert checksum(['waypoint_data','creature_template'])==before,'Non-idempotent route import'
 assert checksum([t for t in tables if t!='waypoint_data'])==other
 assert foreign==sql('SELECT * FROM waypoint_data WHERE id NOT IN('+ids+') ORDER BY id,point;').stdout
 for route in manifest['routes']:
  sql('DELETE FROM waypoint_data WHERE id IN('+ids+');')
  key=route['id'];sql(f'INSERT INTO waypoint_data (id,point,position_x,position_y,position_z) VALUES({key},0,1,2,3);')
  before=sql(f'SELECT * FROM waypoint_data WHERE id={key};').stdout;sql(text)
  assert sql(f'SELECT * FROM waypoint_data WHERE id={key};').stdout==before,'Existing custom/partial group extended or overwritten'
 for entry,field,value,restore,blocked in [(43751,'VehicleId','0','641',[4375101]),(43713,'VehicleId','0','983',[4371301]),(43566,'ScriptName',"'custom_lorna'","'npc_lorna_crowley_43566'",[4356601,4356602,4356603,4356604,4356605,4356606,4356607,4356701]),(43567,'AIName',"'custom_orc'","''",[4356701])]:
  sql('DELETE FROM waypoint_data WHERE id IN('+ids+');');sql(f'UPDATE creature_template SET {field}={value} WHERE entry={entry};');sql(text)
  assert sql('SELECT COUNT(*) FROM waypoint_data WHERE id IN('+','.join(map(str,blocked))+');').stdout.strip()=='0','Custom template/vehicle guard failed'
  sql(f'UPDATE creature_template SET {field}={restore} WHERE entry={entry};')
 sql('DELETE FROM waypoint_data WHERE id IN('+ids+');');sql(text)
 print('PASS: Endgame10 routes/48 source points, idempotence,10 partial/custom groups, vehicle/binding guards, unrelated preservation')
