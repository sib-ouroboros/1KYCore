"""Guarded rescue binding, isolated release schema supplied by caller."""
from pathlib import Path
def test_gilneas_krennan_database(sql,checksum):
    text=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_10_05_world_gilneas_krennan_owner_vehicle.sql').read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines()
    before=checksum([t for t in tables if t!='smart_scripts'])
    other=sql('SELECT * FROM smart_scripts WHERE NOT(entryorguid=35907 AND source_type=0 AND id=0) ORDER BY entryorguid,source_type,id;').stdout
    sql(text)
    assert sql('SELECT event_type,action_param1,target_type,target_param1,target_param2 FROM smart_scripts WHERE entryorguid=35907 AND source_type=0 AND id=0;').stdout.strip()=='54\t84275\t22\t0\t0'
    assert before==checksum([t for t in tables if t!='smart_scripts'])
    assert other==sql('SELECT * FROM smart_scripts WHERE NOT(entryorguid=35907 AND source_type=0 AND id=0) ORDER BY entryorguid,source_type,id;').stdout
    before=checksum(tables);sql(text);assert before==checksum(tables)
    sql('UPDATE smart_scripts SET event_type=11,action_param1=46598,target_type=11,target_param1=35905,target_param2=10 WHERE entryorguid=35907 AND source_type=0 AND id=0;')
    sql("UPDATE creature_template SET ScriptName='custom_rescue' WHERE entry=35907;")
    before=checksum(tables);sql(text);assert before==checksum(tables),'custom handler overwritten'
    sql("UPDATE creature_template SET ScriptName='' WHERE entry=35907;")
    sql('UPDATE smart_scripts SET action_param1=172 WHERE entryorguid=35907 AND source_type=0 AND id=0;')
    before=checksum(tables);sql(text);assert before==checksum(tables),'custom action overwritten'
    print('PASS: rescue invoker vehicle binding, repeat/custom guards, route and unrelated rows preservation')
