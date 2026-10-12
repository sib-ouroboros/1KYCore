#!/usr/bin/env python3
"""Execute scoped vehicle SQL and verify repeat/custom preservation."""
import sqlite3
from pathlib import Path

def main():
 r=Path(__file__).resolve().parents[2];sql=(r/'sql/updates/world/2026_10_12_01_world_gilneas_bat_vehicle.sql').read_text('utf8')
 c=sqlite3.connect(':memory:');c.executescript("CREATE TABLE creature_template(entry INTEGER PRIMARY KEY,AIName TEXT,ScriptName TEXT,VehicleId INTEGER,npcflag INTEGER,spell1 INTEGER,spell5 INTEGER);CREATE TABLE npc_spellclick_spells(npc_entry INTEGER,spell_id INTEGER,cast_flags INTEGER);CREATE TABLE spell_script_names(spell_id INTEGER,ScriptName TEXT);INSERT INTO creature_template VALUES(38615,'','',641,0,0,0),(38540,'','npc_captured_riding_bat_38540',641,0,0,0),(999,'','',641,0,0,0);INSERT INTO npc_spellclick_spells VALUES(38615,72472,0),(999,72472,0);")
 c.executescript(sql)
 assert c.execute('SELECT VehicleId,spell1,spell5 FROM creature_template WHERE entry=38540').fetchone()==(641,72246,72849)
 assert c.execute('SELECT VehicleId,npcflag FROM creature_template WHERE entry=38615').fetchone()==(0,16777216)
 assert c.execute('SELECT cast_flags FROM npc_spellclick_spells WHERE npc_entry=38615').fetchone()[0]==1
 assert c.execute('SELECT COUNT(*) FROM spell_script_names').fetchone()[0]==2
 before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
 c.execute("UPDATE creature_template SET ScriptName='custom' WHERE entry=38615")
 c.execute('UPDATE creature_template SET spell1=999,spell5=888 WHERE entry=38540')
 c.execute('UPDATE npc_spellclick_spells SET cast_flags=0 WHERE npc_entry=38615')
 before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
 print('PASS: actual vehicle SQL abilities/clicker/flags, repeat and custom/unrelated preservation (SQLite semantics)')
if __name__=='__main__':main()
