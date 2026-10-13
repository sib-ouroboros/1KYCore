"""Execute the glaive/seat/scaling migration against representative world rows."""
import sqlite3
from pathlib import Path
sql=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_13_01_world_gilneas_glaive_and_scaling.sql').read_text('utf-8-sig')
c=sqlite3.connect(':memory:')
c.executescript('''CREATE TABLE creature_template(entry INTEGER PRIMARY KEY,VehicleId INTEGER,npcflag INTEGER,minlevel INTEGER,maxlevel INTEGER,spell1 INTEGER,spell2 INTEGER,spell4 INTEGER,AIName TEXT,ScriptName TEXT);
CREATE TABLE npc_spellclick_spells(npc_entry INTEGER,spell_id INTEGER,cast_flags INTEGER,user_type INTEGER,PRIMARY KEY(npc_entry,spell_id));
CREATE TABLE vehicle_template_accessory(entry INTEGER,accessory_entry INTEGER,seat_id INTEGER,minion INTEGER,summontype INTEGER,summontimer INTEGER);
CREATE TABLE creature_template_scaling(Entry INTEGER PRIMARY KEY,LevelScalingMin INTEGER,LevelScalingMax INTEGER,LevelScalingDeltaMin INTEGER,LevelScalingDeltaMax INTEGER,VerifiedBuild INTEGER);
CREATE TABLE creature(guid INTEGER PRIMARY KEY,id INTEGER,map INTEGER,zoneId INTEGER,areaId INTEGER,spawnDifficulties TEXT,phaseUseFlags INTEGER,PhaseId INTEGER,PhaseGroup INTEGER,terrainSwapMap INTEGER,position_x REAL,position_y REAL,position_z REAL,orientation REAL,spawntimesecs INTEGER,spawndist REAL,MovementType INTEGER,ScriptName TEXT);
INSERT INTO creature_template VALUES(37927,0,0,1,1,70735,70732,59737,'',''),(37939,429,0,5,20,0,0,0,'',''),(37916,0,0,5,20,0,0,0,'',''),(37884,0,0,5,20,0,0,0,'SmartAI',''),(37921,0,0,5,20,0,0,0,'','custom');
INSERT INTO npc_spellclick_spells VALUES(37927,71238,1,0),(999,71238,1,0);
INSERT INTO vehicle_template_accessory VALUES(37939,37938,0,0,0,0),(999,37938,0,0,0,0);
INSERT INTO creature(guid,id,map,PhaseId,PhaseGroup,position_x,position_y) VALUES(804189,38149,654,189,0,-1322.3,2120.34);
INSERT INTO creature_template_scaling VALUES(37916,8,15,1,1,123);
''')
c.executescript(sql)
assert c.execute('SELECT VehicleId,npcflag,minlevel,maxlevel FROM creature_template WHERE entry=37927').fetchone()==(447,16777216,5,20)
assert c.execute('SELECT spell_id,cast_flags FROM npc_spellclick_spells WHERE npc_entry=37927').fetchone()==(46598,1)
assert c.execute('SELECT spell_id FROM npc_spellclick_spells WHERE npc_entry=37939').fetchone()==(46598,)
assert c.execute('SELECT summontype FROM vehicle_template_accessory WHERE entry=37939').fetchone()==(7,)
assert c.execute('SELECT summontype FROM vehicle_template_accessory WHERE entry=999').fetchone()==(0,)
assert c.execute('SELECT COUNT(*) FROM creature WHERE id=37927 AND PhaseId=189').fetchone()==(1,)
assert c.execute('SELECT LevelScalingDeltaMin FROM creature_template_scaling WHERE Entry=37916').fetchone()==(1,)
assert c.execute('SELECT COUNT(*) FROM creature_template_scaling WHERE Entry=37921').fetchone()==(0,)
assert c.execute('SELECT LevelScalingMin,LevelScalingMax FROM creature_template_scaling WHERE Entry=37884').fetchone()==(5,20)
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
c.execute('DELETE FROM creature WHERE id=37927');c.execute('DELETE FROM creature WHERE id=38149');c.executescript(sql)
assert c.execute('SELECT COUNT(*) FROM creature WHERE id=37927').fetchone()==(0,)
print('PASS: actual glaive SQL, boarding, rider lifecycle, scaling, repeat, custom and missing-anchor guards (SQLite semantics)')
