"""Grandma14400 chest phase/respawn; disposable release database only."""
from pathlib import Path
def test_gilneas_chest_database(sql,checksum):
 root=Path(__file__).resolve().parents[2]
 text=(root/'sql/updates/world/2026_10_10_14_world_gilneas_grandma_chest_phase.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines();baseline=checksum(tables)
 other=checksum([t for t in tables if t!='gameobject'])
 position=sql('SELECT position_x,position_y,position_z,orientation,PhaseGroup,phaseUseFlags FROM gameobject WHERE guid=51003260;').stdout
 sql(text)
 assert sql('SELECT PhaseId,spawntimesecs FROM gameobject WHERE guid=51003260;').stdout.strip()=='183\t5'
 assert position==sql('SELECT position_x,position_y,position_z,orientation,PhaseGroup,phaseUseFlags FROM gameobject WHERE guid=51003260;').stdout
 assert other==checksum([t for t in tables if t!='gameobject'])
 before=checksum(tables);sql(text);assert before==checksum(tables)
 sql('UPDATE gameobject SET PhaseId=0,spawntimesecs=7200 WHERE guid=51003260;')
 assert baseline==checksum(tables),'changes outside intended chest fields'
 for change,restore in [
  ('UPDATE gameobject SET PhaseId=456 WHERE guid=51003260;','UPDATE gameobject SET PhaseId=0 WHERE guid=51003260;'),
  ('UPDATE gameobject SET position_z=50 WHERE guid=51003260;','UPDATE gameobject SET position_z=13.0241 WHERE guid=51003260;'),
  ("UPDATE gameobject_template SET ScriptName='custom_chest' WHERE entry=196472;","UPDATE gameobject_template SET ScriptName='' WHERE entry=196472;"),
  ('UPDATE quest_objectives SET Amount=2 WHERE QuestID=14400 AND ObjectID=49279;','UPDATE quest_objectives SET Amount=1 WHERE QuestID=14400 AND ObjectID=49279;'),
  ('UPDATE gameobject SET PhaseGroup=1 WHERE guid=51003260;','UPDATE gameobject SET PhaseGroup=0 WHERE guid=51003260;')]:
  sql(change);before=checksum(tables);sql(text);assert before==checksum(tables),'custom/dependency guard';sql(restore)
 sql('UPDATE gameobject SET PhaseId=183,spawntimesecs=60 WHERE guid=51003260;')
 before=checksum(tables);sql(text);assert before==checksum(tables),'custom respawn changed'
 print('PASS: Grandma chest sourced phase/respawn, repeat, custom/dependency guards and unrelated preservation')
