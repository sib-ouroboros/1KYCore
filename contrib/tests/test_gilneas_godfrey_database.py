"""Godfrey missing dialogue migration on a disposable database only."""
from pathlib import Path

def test_gilneas_godfrey_database(sql, checksum):
 text=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_06_18_world_gilneas_godfrey_text.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines()
 sql('DELETE FROM creature_text WHERE CreatureID=37875 AND GroupID=0;')
 other=checksum([t for t in tables if t!='creature_text'])
 foreign=sql('SELECT * FROM creature_text WHERE CreatureID<>37875 OR GroupID<>0 ORDER BY CreatureID,GroupID,ID;').stdout
 sql(text)
 assert sql('SELECT COUNT(*) FROM creature_text WHERE CreatureID=37875 AND GroupID=0 AND ID=0 AND Type=12 AND Probability=100 AND Sound=0 AND BroadcastTextId=0;').stdout.strip()=='1'
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Godfrey text repeated import changed data'
 assert checksum([t for t in tables if t!='creature_text'])==other
 assert sql('SELECT * FROM creature_text WHERE CreatureID<>37875 OR GroupID<>0 ORDER BY CreatureID,GroupID,ID;').stdout==foreign
 sql("UPDATE creature_text SET ID=1,Text='administrator dialogue' WHERE CreatureID=37875 AND GroupID=0;")
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Existing custom group overwritten or mixed'
 sql('DELETE FROM creature_text WHERE CreatureID=37875 AND GroupID=0;')
 for statement,restore in [("UPDATE creature_template SET ScriptName='custom_godfrey' WHERE entry=37875;","UPDATE creature_template SET ScriptName='npc_gilneas_godfrey_departure' WHERE entry=37875;"),("UPDATE creature_template SET AIName='SmartAI' WHERE entry=37875;","UPDATE creature_template SET AIName='' WHERE entry=37875;"),("UPDATE creature_template SET ScriptName='custom_genn' WHERE entry=37876;","UPDATE creature_template SET ScriptName='npc_king_genn_greymane_37876' WHERE entry=37876;"),("UPDATE creature_template SET AIName='SmartAI' WHERE entry=37876;","UPDATE creature_template SET AIName='' WHERE entry=37876;")]:
  sql(statement);before=checksum(tables);sql(text);assert checksum(tables)==before,'Custom actor binding changed';sql(restore)
 sql(text)
 assert sql('SELECT COUNT(*) FROM creature_text WHERE CreatureID=37875 AND GroupID=0;').stdout.strip()=='1'
 print('PASS: Godfrey text SQL first/repeat/custom group/actor binding/unrelated preservation')
