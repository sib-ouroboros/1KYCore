"""Measured path fidelity, idempotency and unrelated route preservation."""
from pathlib import Path
import csv

def test_gilneas_exodus_route_database(sql,checksum):
 root=Path(__file__).resolve().parents[2]
 text=(root/'sql/updates/world/2026_10_11_00_world_gilneas_exodus_measured_route.sql').read_text('utf8')
 before=sql('SELECT * FROM waypoint_data WHERE id<>4492802 ORDER BY id,point;').stdout
 sql(text)
 data=sql('SELECT point,CAST(position_x AS DECIMAL(12,6)),CAST(position_y AS DECIMAL(12,6)),CAST(position_z AS DECIMAL(12,6)) FROM waypoint_data WHERE id=4492802 ORDER BY point;').stdout.splitlines()
 assert len(data)==56
 with (root/'contrib/data/gilneas/24438-exodus-player-route.csv').open(encoding='utf8') as f: rows=list(csv.DictReader(f))
 for got,want in zip(data[:53],rows):
  vals=got.split('\t');assert int(vals[0])==int(want['point'])
  assert all(abs(float(vals[i+1])-float(want[k]))<0.001 for i,k in enumerate(['x','y','z']))
 assert before==sql('SELECT * FROM waypoint_data WHERE id<>4492802 ORDER BY id,point;').stdout
 tables=sql('SHOW TABLES;').stdout.splitlines();first=checksum(tables);sql(text);assert first==checksum(tables)
 print('PASS measured Exodus route: 53 CSV coordinates, 3 drive-away points, idempotency, old routes preserved')
