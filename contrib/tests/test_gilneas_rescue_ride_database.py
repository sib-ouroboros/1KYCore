"""Release route/control, hanging pose and scoped passenger target SQL."""
from pathlib import Path
def test_gilneas_rescue_ride_database(sql,checksum):
 root=Path(__file__).resolve().parents[2];text=(root/'sql/updates/world/2026_10_10_06_world_gilneas_rescue_ride.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines();route=sql('SELECT * FROM waypoints WHERE entry=35905 ORDER BY pointid;').stdout
 before=checksum([t for t in tables if t not in('creature_template','creature_addon','creature','smart_scripts')])
 pose=sql('SELECT a.guid,c.PhaseId,a.bytes1,a.bytes2,a.auras FROM creature_addon a JOIN creature c ON c.guid=a.guid WHERE c.id=35753 AND c.map=654 ORDER BY a.guid;').stdout
 sql(text)
 assert sql('SELECT AIName,ScriptName,VehicleId,spell1 FROM creature_template WHERE entry=35905;').stdout.strip()=='SmartAI\tnpc_gilneas_rescue_horse_runtime\t494\t68219'
 assert sql('SELECT emote FROM creature_addon WHERE guid=20556808;').stdout.strip()=='472'
 assert pose==sql('SELECT a.guid,c.PhaseId,a.bytes1,a.bytes2,a.auras FROM creature_addon a JOIN creature c ON c.guid=a.guid WHERE c.id=35753 AND c.map=654 ORDER BY a.guid;').stdout
 assert sql('SELECT target_type,target_param1,target_param2 FROM smart_scripts WHERE entryorguid=35905 AND source_type=0 AND id=3;').stdout.strip()=='29\t1\t0'
 assert sql('SELECT COUNT(*) FROM creature WHERE id=35753 AND map=654 AND PhaseId=171 AND ABS(position_z-20.796)<0.001;').stdout.strip()=='1'
 assert route==sql('SELECT * FROM waypoints WHERE entry=35905 ORDER BY pointid;').stdout
 assert before==checksum([t for t in tables if t not in('creature_template','creature_addon','creature','smart_scripts')])
 before=checksum(tables);sql(text);assert before==checksum(tables)
 calibration=(root/'sql/updates/world/2026_10_10_08_world_gilneas_rescue_calibration.sql').read_text('utf8')
 original_flags=sql("SELECT entryorguid,source_type,id,event_flags FROM smart_scripts WHERE (entryorguid=35905 AND source_type=0) OR (entryorguid=3590500 AND source_type=9) ORDER BY entryorguid,id;").stdout
 other_scripts=sql("SELECT * FROM smart_scripts WHERE entryorguid NOT IN(35905,3590500) ORDER BY entryorguid,source_type,id;").stdout
 sql(calibration)
 assert sql("SELECT position_z FROM creature WHERE guid=20556808;").stdout.strip()=='20.496'
 changed_flags=sql("SELECT entryorguid,source_type,id,event_flags FROM smart_scripts WHERE (entryorguid=35905 AND source_type=0) OR (entryorguid=3590500 AND source_type=9) ORDER BY entryorguid,id;").stdout
 assert len(changed_flags.splitlines())==6
 for old,new in zip(original_flags.splitlines(),changed_flags.splitlines()):
  a=old.split('\t');b=new.split('\t');assert a[:3]==b[:3] and int(b[3])==(int(a[3])|512)
 assert other_scripts==sql("SELECT * FROM smart_scripts WHERE entryorguid NOT IN(35905,3590500) ORDER BY entryorguid,source_type,id;").stdout
 before=checksum(tables);sql(calibration);assert before==checksum(tables)
 measured=(root/'sql/updates/world/2026_10_10_09_world_gilneas_krennan_measured_height.sql').read_text('utf8')
 placement=sql("SELECT position_x,position_y,orientation,PhaseId FROM creature WHERE guid=20556808;").stdout
 sql(measured)
 assert abs(float(sql("SELECT position_z FROM creature WHERE guid=20556808;").stdout.strip())-19.456224)<0.0001
 assert placement==sql("SELECT position_x,position_y,orientation,PhaseId FROM creature WHERE guid=20556808;").stdout
 before=checksum(tables);sql(measured);assert before==checksum(tables)
 tree=(root/'sql/updates/world/2026_10_10_10_world_gilneas_krennan_tree_placement.sql').read_text('utf8')
 passenger=sql("SELECT * FROM creature_template WHERE entry=35907;").stdout
 sql(tree)
 xyz=list(map(float,sql("SELECT position_x,position_y,position_z FROM creature WHERE guid=20556808;").stdout.split()))
 assert all(abs(a-b)<0.0002 for a,b in zip(xyz,[-1673.4,1344.18,19.65]))
 assert sql("SELECT InhabitType FROM creature_template WHERE entry=35753;").stdout.strip()=='4'
 assert passenger==sql("SELECT * FROM creature_template WHERE entry=35907;").stdout
 before=checksum(tables);sql(tree);assert before==checksum(tables)
 sql((root/'sql/updates/world/2026_10_10_11_world_gilneas_krennan_height.sql').read_text('utf8'))
 assert abs(float(sql("SELECT position_z FROM creature WHERE guid=20556808;").stdout.strip())-19.05)<0.0001
 start=(root/'sql/updates/world/2026_10_10_12_world_gilneas_rescue_start.sql').read_text('utf8')
 other_accessories=sql("SELECT * FROM vehicle_template_accessory WHERE NOT(entry=35905 AND accessory_entry=35907) ORDER BY entry,accessory_entry,seat_id;").stdout
 sql(start)
 assert sql("SELECT COUNT(*) FROM spell_script_names WHERE spell_id=68219 AND ScriptName='spell_gilneas_rescue_at_tree';").stdout.strip()=='1'
 assert sql("SELECT COUNT(*) FROM vehicle_template_accessory WHERE entry=35905 AND accessory_entry=35907 AND seat_id=1;").stdout.strip()=='0'
 assert sql("SELECT event_param1,event_param2,event_param3,event_param4,action_param2,action_param4 FROM smart_scripts WHERE entryorguid=3590500 AND source_type=9 AND id=0;").stdout.strip()=='0\t0\t0\t0\t35905\t14293'
 assert sql("SELECT COUNT(*) FROM smart_scripts WHERE entryorguid=35905 AND source_type=0 AND id=2;").stdout.strip()=='0'
 assert other_accessories==sql("SELECT * FROM vehicle_template_accessory WHERE NOT(entry=35905 AND accessory_entry=35907) ORDER BY entry,accessory_entry,seat_id;").stdout
 assert route==sql('SELECT * FROM waypoints WHERE entry=35905 ORDER BY pointid;').stdout
 before=checksum(tables);sql(start);assert before==checksum(tables)
 sql("UPDATE creature_template SET ScriptName='custom_horse' WHERE entry=35905; UPDATE creature_addon SET emote=1 WHERE guid=20556808; UPDATE creature SET position_z=30 WHERE guid=20556808;")
 sql("INSERT INTO vehicle_template_accessory(entry,accessory_entry,seat_id,minion,description,summontype,summontimer) VALUES(35905,35907,1,0,'custom horse passenger',3,300000);")
 before=checksum(tables);sql(text);sql(calibration);sql(measured);sql(tree);sql(start);assert before==checksum(tables),'custom horse, pose or placement changed'
 binding=(root/'sql/updates/world/2026_10_10_07_world_gilneas_cannon_two_shots.sql').read_text('utf8')
 existing=sql("SELECT spell_id,ScriptName FROM spell_script_names WHERE spell_id=68235 ORDER BY ScriptName;").stdout
 sql(binding)
 assert sql("SELECT COUNT(*) FROM spell_script_names WHERE spell_id=68235 AND ScriptName='spell_gilneas_cannon_scene_target';").stdout.strip()=='1'
 assert existing==sql("SELECT spell_id,ScriptName FROM spell_script_names WHERE spell_id=68235 AND ScriptName<>'spell_gilneas_cannon_scene_target' ORDER BY ScriptName;").stdout
 before=checksum(tables);sql(binding);assert before==checksum(tables)
 print('PASS: rescue script/route, hanging pose/source placement, own passenger, repeat/custom guards')
