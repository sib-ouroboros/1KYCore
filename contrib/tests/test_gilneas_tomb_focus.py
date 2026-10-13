"""Exercise the tomb migration with missing, repeated and unrelated spawns."""
import sqlite3
from pathlib import Path
sql=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_12_02_world_gilneas_aderic_tomb_focus.sql').read_text('utf-8-sig')
c=sqlite3.connect(':memory:')
c.executescript('CREATE TABLE gameobject_template(entry INTEGER PRIMARY KEY,type INTEGER,Data0 INTEGER,Data1 INTEGER); CREATE TABLE gameobject(guid INTEGER PRIMARY KEY,id INTEGER,map INTEGER,zoneId INTEGER,areaId INTEGER,spawnDifficulties TEXT,phaseUseFlags INTEGER,PhaseId INTEGER,PhaseGroup INTEGER,terrainSwapMap INTEGER,position_x REAL,position_y REAL,position_z REAL,orientation REAL,rotation0 REAL,rotation1 REAL,rotation2 REAL,rotation3 REAL,spawntimesecs INTEGER,animprogress INTEGER,state INTEGER,isActive INTEGER,ScriptName TEXT,VerifiedBuild INTEGER);')
c.executescript(sql);assert not c.execute('SELECT * FROM gameobject').fetchall()
c.execute('INSERT INTO gameobject_template VALUES(201964,8,1643,10)')
c.execute("INSERT INTO gameobject(guid,id,map,position_x,position_y,position_z,PhaseId,PhaseGroup,phaseUseFlags) VALUES(42,201964,1,0,0,0,0,0,0)")
prior=c.execute('SELECT * FROM gameobject WHERE guid=42').fetchone()
c.executescript(sql)
r=c.execute('SELECT id,map,position_x,position_y,position_z,phaseUseFlags,PhaseId,PhaseGroup FROM gameobject WHERE guid=43').fetchone()
assert r==(201964,654,-1621.367188,1897.508057,20.0,1,0,0),r
assert c.execute('SELECT * FROM gameobject WHERE guid=42').fetchone()==prior
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
print('PASS: tomb focus SQL, prerequisite guard, measured coordinates, phase flags, repeat and unrelated preservation (SQLite semantics)')

from math import dist
fix=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_13_00_world_gilneas_aderic_tomb_position.sql').read_text('utf-8-sig')
c.executescript(fix)
assert c.execute('SELECT position_x,position_y,position_z,areaId FROM gameobject WHERE guid=43').fetchone()==(-1643,1904,30,4727)
assert c.execute('SELECT * FROM gameobject WHERE guid=42').fetchone()==prior
before=list(c.iterdump());c.executescript(fix);assert list(c.iterdump())==before
for p in [(-1642.311035,1905.172363,29.951511),(-1644.763428,1904.045532,29.959845),(-1639.253418,1906.638672,29.952402),(-1646.357300,1902.511353,30.029156)]:
 assert dist(p,(-1643,1904,30))<5
c.execute('DELETE FROM gameobject WHERE guid=43');c.executescript(fix)
assert c.execute('SELECT COUNT(*) FROM gameobject WHERE map=654').fetchone()[0]==1
c.execute("INSERT INTO gameobject(guid,id,map,position_x,position_y,position_z,PhaseId,PhaseGroup,phaseUseFlags,ScriptName) VALUES(44,201964,654,-1621.367188,1897.508057,20,0,0,1,'custom')")
before=list(c.iterdump());c.executescript(fix);assert list(c.iterdump())==before
print('PASS: corrected tomb position, four client samples within native radius, repeat/missing/custom guards')
