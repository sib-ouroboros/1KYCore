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

