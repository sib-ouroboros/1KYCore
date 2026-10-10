"""Native Tobias route migration against an isolated release database."""
from pathlib import Path
import json

def test_gilneas_tobias_native_database(sql,checksum):
    root=Path(__file__).resolve().parents[2]
    text=(root/'sql/updates/world/2026_10_10_04_world_gilneas_tobias_native_routes.sql').read_text('utf8')
    source=json.loads((root/'docs/audit-data/gilneas-tobias-native-route-source.json').read_text('utf8'))
    ids=','.join(source['route_counts'])
    sql('DELETE FROM waypoint_data WHERE id IN('+ids+');')
    sql("UPDATE creature_template SET AIName='',ScriptName='npc_tobias_mistmantle_38507' WHERE entry=38507;")
    tables=sql('SHOW TABLES;').stdout.splitlines()
    other=checksum([t for t in tables if t!='waypoint_data'])
    sql(text)
    counts=sql('SELECT id,COUNT(*) FROM waypoint_data WHERE id IN('+ids+') GROUP BY id ORDER BY id;').stdout.splitlines()
    assert counts==[f'{i}\t{n}' for i,n in source['route_counts'].items()],counts
    actual=sql('SELECT id,point,CAST(position_x AS DECIMAL(12,5)),CAST(position_y AS DECIMAL(12,5)),CAST(position_z AS DECIMAL(12,5)) FROM waypoint_data WHERE id IN('+ids+') ORDER BY id,point;').stdout.splitlines()
    for line,row in zip(actual,source['records']):
        values=line.split('\t')
        assert values[:2]==row[:2]
        assert all(abs(float(a)-float(b))<0.001 for a,b in zip(values[2:],row[2:5]))
    assert other==checksum([t for t in tables if t!='waypoint_data'])
    before=checksum(tables);sql(text);assert before==checksum(tables)
    sql('DELETE FROM waypoint_data WHERE id=3850705 AND point>0; UPDATE waypoint_data SET position_z=999 WHERE id=3850705;')
    before=checksum(tables);sql(text);assert before==checksum(tables),'custom partial route overwritten'
    sql("DELETE FROM waypoint_data WHERE id IN("+ids+"); UPDATE creature_template SET ScriptName='custom_tobias' WHERE entry=38507;")
    before=checksum(tables);sql(text);assert before==checksum(tables),'custom script ignored'
    print('PASS: 38 native Tobias points, first/repeat, custom partial route and script preservation')
