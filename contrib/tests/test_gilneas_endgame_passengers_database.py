"""Verify the audited transport migration and source-click semantics with actual SQL."""
import json,sqlite3
from pathlib import Path
r=Path(__file__).resolve().parents[2]
data=json.loads((r/'docs/audit-data/gilneas-endgame-transport-passengers.json').read_text('utf8'))
sql=(r/'sql/updates/world/2026_10_13_03_world_gilneas_endgame_transport_passengers.sql').read_text('utf8')
c=sqlite3.connect(':memory:');c.executescript('''CREATE TABLE gameobject_template(entry INTEGER,type INTEGER,Data6 INTEGER,ScriptName TEXT);
CREATE TABLE creature_template(entry INTEGER,AIName TEXT,ScriptName TEXT,VehicleId INTEGER);
CREATE TABLE creature(guid INTEGER PRIMARY KEY,id INTEGER,map INTEGER,zoneId INTEGER,areaId INTEGER,PhaseId INTEGER,PhaseGroup INTEGER,ScriptName TEXT,position_x REAL,position_y REAL,position_z REAL);
CREATE TABLE gameobject(guid INTEGER PRIMARY KEY,id INTEGER,map INTEGER,zoneId INTEGER,areaId INTEGER,spawnDifficulties TEXT,phaseUseFlags INTEGER,PhaseId INTEGER,PhaseGroup INTEGER,terrainSwapMap INTEGER,position_x REAL,position_y REAL,position_z REAL,orientation REAL,rotation0 REAL,rotation1 REAL,rotation2 REAL,rotation3 REAL,spawntimesecs INTEGER,animprogress INTEGER,state INTEGER,isActive INTEGER,ScriptName TEXT,VerifiedBuild INTEGER);
CREATE TABLE npc_spellclick_spells(npc_entry INTEGER,spell_id INTEGER,cast_flags INTEGER,user_type INTEGER);
INSERT INTO gameobject_template VALUES(203428,15,749,'go_worgen_gunship_203428'),(204428,10,0,'go_rope_204428');
INSERT INTO creature_template VALUES(43747,'','',0);INSERT INTO npc_spellclick_spells VALUES(43747,81877,0,0),(999,81877,0,0);
''')
for row in data['passengers']:
 c.execute('INSERT INTO creature VALUES(?,?,0,267,279,191,0,?,?,?,?)',(row['guid'],row['entry'],'',*row['offset']))
c.execute("INSERT INTO creature VALUES(1,43566,0,267,279,191,0,'',6,0,84)")
c.executescript(sql)
assert c.execute('SELECT COUNT(*) FROM creature WHERE map=749').fetchone()==(94,)
assert c.execute('SELECT map FROM creature WHERE guid=1').fetchone()==(0,)
assert c.execute('SELECT COUNT(*) FROM gameobject WHERE id=204428 AND map=749').fetchone()==(2,)
assert c.execute('SELECT cast_flags FROM npc_spellclick_spells WHERE npc_entry=43747').fetchone()==(1,)
assert c.execute('SELECT cast_flags FROM npc_spellclick_spells WHERE npc_entry=999').fetchone()==(0,)
for row in data['passengers']:
 assert c.execute('SELECT position_x,position_y,position_z FROM creature WHERE guid=?',(row['guid'],)).fetchone()==tuple(row['offset'])
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
c.execute("UPDATE creature SET map=0,ScriptName='custom' WHERE guid=804788")
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
print('PASS:94 audited passenger maps/offsets,2 ropes, native source spell, repeat/custom/unrelated guards (SQLite semantics)')

phase_sql=(r/'sql/updates/world/2026_10_13_04_world_gilneas_endgame_ship_phase.sql').read_text('utf-8-sig')
c.executescript("CREATE TABLE transports(guid INTEGER PRIMARY KEY,entry INTEGER,phaseUseFlags INTEGER,phaseid INTEGER,phasegroup INTEGER,ScriptName TEXT);INSERT INTO transports VALUES(28,203428,0,0,0,''),(29,203428,0,0,0,'');")
c.executescript(phase_sql)
assert c.execute('SELECT phaseid FROM transports WHERE guid=28').fetchone()==(191,)
assert c.execute('SELECT phaseid FROM transports WHERE guid=29').fetchone()==(0,)
before=list(c.iterdump());c.executescript(phase_sql);assert list(c.iterdump())==before
c.execute("UPDATE transports SET phaseid=0,ScriptName='custom' WHERE guid=28")
before=list(c.iterdump());c.executescript(phase_sql);assert list(c.iterdump())==before
print('PASS: physical gunship phase191; repeat, custom and unrelated transport preservation')
