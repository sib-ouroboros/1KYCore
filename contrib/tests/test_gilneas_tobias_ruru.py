#!/usr/bin/env python3
"""Execute portable ruRU update semantics against empty/stock/custom locale rows."""
import json,sqlite3
from pathlib import Path

def main():
 r=Path(__file__).resolve().parents[2]
 data=json.loads((r/'docs/audit-data/gilneas-tobias-dialogue-ruru.json').read_text('utf8'))
 sql=(r/'sql/updates/world/2026_10_12_00_world_gilneas_tobias_ruru.sql').read_text('utf8').replace('SET NAMES utf8mb4;','')
 c=sqlite3.connect(':memory:')
 c.executescript("CREATE TABLE creature_template(entry INTEGER PRIMARY KEY,AIName TEXT,ScriptName TEXT); CREATE TABLE creature_template_locale(entry INTEGER,locale TEXT,Name TEXT,PRIMARY KEY(entry,locale)); CREATE TABLE creature_text(CreatureID INTEGER,GroupID INTEGER,ID INTEGER,Text TEXT,Type INTEGER,Language INTEGER,Probability INTEGER,Emote INTEGER,Duration INTEGER,Sound INTEGER,BroadcastTextId INTEGER,TextRange INTEGER,comment TEXT,PRIMARY KEY(CreatureID,GroupID,ID)); CREATE TABLE creature_text_locale(CreatureID INTEGER,GroupID INTEGER,ID INTEGER,Locale TEXT,Text TEXT,PRIMARY KEY(CreatureID,GroupID,ID));")
 for entry in data['names']:
  e=int(entry);script={38507:'npc_tobias_mistmantle_38507',38530:'npc_lady_sylvanas_windrunner_38530'}.get(e,'')
  c.execute('INSERT INTO creature_template VALUES (?,?,?)',(e,'',script))
 c.executescript(sql)
 assert c.execute('SELECT COUNT(*) FROM creature_text').fetchone()[0]==15
 assert c.execute('SELECT COUNT(*) FROM creature_text_locale').fetchone()[0]==15
 assert c.execute('SELECT COUNT(*) FROM creature_template_locale').fetchone()[0]==5
 for row in data['lines']:
  key=(row['entry'],row['group'],row['id'])
  assert c.execute('SELECT BroadcastTextId,Sound FROM creature_text WHERE CreatureID=? AND GroupID=? AND ID=?',key).fetchone()==(row['broadcast'],0)
  assert c.execute('SELECT Text FROM creature_text_locale WHERE CreatureID=? AND GroupID=? AND ID=?',key).fetchone()[0]==row['ru']
 snapshot=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==snapshot
 c.execute("UPDATE creature_text_locale SET Locale='frFR',Text='Texte existant' WHERE CreatureID=38507 AND GroupID=0")
 c.execute("UPDATE creature_text_locale SET Text='Свой перевод' WHERE CreatureID=38507 AND GroupID=1")
 c.execute("UPDATE creature_text SET Text='Custom dialogue',BroadcastTextId=999,Sound=123 WHERE CreatureID=38530 AND GroupID=0")
 c.execute("UPDATE creature_template_locale SET Name='Своё имя' WHERE entry=38507")
 snapshot=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==snapshot
 c.execute('DELETE FROM creature_text_locale WHERE CreatureID=38507 AND GroupID=2')
 c.execute('UPDATE creature_text SET BroadcastTextId=0,Sound=19606 WHERE CreatureID=38507 AND GroupID=2')
 c.executescript(sql)
 assert c.execute('SELECT BroadcastTextId,Sound FROM creature_text WHERE CreatureID=38507 AND GroupID=2').fetchone()==(38401,0)
 c.execute('DELETE FROM creature_text WHERE CreatureID=38507 AND GroupID=4')
 c.execute("UPDATE creature_template SET ScriptName='custom_script' WHERE entry=38507")
 snapshot=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==snapshot
 print('PASS: 15 dialogue groups, five names, repeat import, stock repair and custom/foreign locale preservation (SQLite semantics)')
if __name__=='__main__':main()
