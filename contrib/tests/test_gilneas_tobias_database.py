"""Guarded event gate for objective-free 24902; disposable database only."""
from pathlib import Path
def test_gilneas_tobias_database(sql,checksum):
 root=Path(__file__).resolve().parents[2];text=(root/'sql/updates/world/2026_10_06_17_world_gilneas_tobias_event.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines();other=checksum([t for t in tables if t!='quest_template_addon']);addons=sql('SELECT * FROM quest_template_addon WHERE ID<>24902 ORDER BY ID;').stdout
 sql(text);assert sql('SELECT SpecialFlags FROM quest_template_addon WHERE ID=24902;').stdout.strip()=='2'
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Tobias SQL not idempotent'
 assert checksum([t for t in tables if t!='quest_template_addon'])==other
 assert sql('SELECT * FROM quest_template_addon WHERE ID<>24902 ORDER BY ID;').stdout==addons
 for statement,restore in [("UPDATE quest_template_addon SET ScriptName='custom_tobias' WHERE ID=24902;","UPDATE quest_template_addon SET ScriptName='' WHERE ID=24902;"),("UPDATE creature_template SET ScriptName='custom_tobias' WHERE entry=38507;","UPDATE creature_template SET ScriptName='npc_tobias_mistmantle_38507' WHERE entry=38507;"),("UPDATE creature_template SET AIName='SmartAI' WHERE entry=38530;","UPDATE creature_template SET AIName='' WHERE entry=38530;"),("INSERT INTO quest_objectives (ID,QuestID,Type,ObjectID,Amount) VALUES (9999987,24902,0,38530,1);","DELETE FROM quest_objectives WHERE ID=9999987;")]:
  sql('UPDATE quest_template_addon SET SpecialFlags=0 WHERE ID=24902;');sql(statement);before=checksum(tables);sql(text);assert checksum(tables)==before,'Tobias custom data/real objective overwritten';sql(restore)
 sql(text);assert sql('SELECT SpecialFlags FROM quest_template_addon WHERE ID=24902;').stdout.strip()=='2'
 print('PASS: Tobias event SQL first/repeat/custom script/AI/real objective and unrelated preservation')
