"""Missing 37757 scaling regression, disposable database only."""
from pathlib import Path

def test_gilneas_banshee_database(sql,checksum):
 text=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_06_19_world_gilneas_banshee_scaling.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines()
 sql('DELETE FROM creature_template_scaling WHERE Entry=37757;')
 other=checksum([t for t in tables if t!='creature_template_scaling'])
 foreign=sql('SELECT * FROM creature_template_scaling WHERE Entry<>37757 ORDER BY Entry;').stdout
 sql(text)
 assert sql('SELECT LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild FROM creature_template_scaling WHERE Entry=37757;').stdout.strip()=='5\t20\t0\t0\t0'
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Repeat scaling import changed data'
 assert checksum([t for t in tables if t!='creature_template_scaling'])==other
 assert sql('SELECT * FROM creature_template_scaling WHERE Entry<>37757 ORDER BY Entry;').stdout==foreign
 sql('UPDATE creature_template_scaling SET LevelScalingMax=12,LevelScalingDeltaMin=1 WHERE Entry=37757;')
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Existing custom scaling overwritten'
 sql('DELETE FROM creature_template_scaling WHERE Entry=37757;')
 for statement,restore in [("UPDATE creature_template SET ScriptName='custom_banshee' WHERE entry=37757;","UPDATE creature_template SET ScriptName='' WHERE entry=37757;"),("UPDATE creature_template SET AIName='' WHERE entry=37757;","UPDATE creature_template SET AIName='SmartAI' WHERE entry=37757;"),("UPDATE creature_template SET maxlevel=10 WHERE entry=37757;","UPDATE creature_template SET maxlevel=20 WHERE entry=37757;"),("UPDATE quest_objectives SET Amount=1 WHERE QuestID=24627 AND ObjectID=37757;","UPDATE quest_objectives SET Amount=6 WHERE QuestID=24627 AND ObjectID=37757;"),("UPDATE creature SET map=0 WHERE id=37757 AND map=654;","UPDATE creature SET map=654 WHERE id=37757 AND map=0;")]:
  sql(statement);before=checksum(tables);sql(text);assert checksum(tables)==before,'Custom data guard failed';sql(restore)
 sql(text)
 print('PASS: Banshee scaling first/repeat/existing scaling/custom AI/bounds/objective/map/unrelated preservation')
