"""Slavedriver scaling import and custom-data guards; disposable schema only."""
from pathlib import Path

def test_gilneas_slavedriver_database(sql,checksum):
 text=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_09_00_world_gilneas_slavedriver_scaling.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines()
 sql('DELETE FROM creature_template_scaling WHERE Entry=37701;')
 foreign=sql('SELECT * FROM creature_template_scaling WHERE Entry<>37701 ORDER BY Entry;').stdout
 other=checksum([t for t in tables if t!='creature_template_scaling'])
 sql(text)
 assert sql('SELECT LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild FROM creature_template_scaling WHERE Entry=37701;').stdout.strip()=='5\t20\t0\t0\t0'
 assert other==checksum([t for t in tables if t!='creature_template_scaling'])
 assert foreign==sql('SELECT * FROM creature_template_scaling WHERE Entry<>37701 ORDER BY Entry;').stdout
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Non-idempotent import'
 sql('UPDATE creature_template_scaling SET LevelScalingMax=12,LevelScalingDeltaMin=1 WHERE Entry=37701;')
 before=checksum(tables);sql(text);assert checksum(tables)==before,'Custom scaling overwritten'
 sql('DELETE FROM creature_template_scaling WHERE Entry=37701;')
 for change,restore in [
  ("UPDATE creature_template SET ScriptName='custom_slavedriver' WHERE entry=37701;","UPDATE creature_template SET ScriptName='' WHERE entry=37701;"),
  ("UPDATE creature_template SET AIName='' WHERE entry=37701;","UPDATE creature_template SET AIName='SmartAI' WHERE entry=37701;"),
  ('UPDATE creature_template SET maxlevel=10 WHERE entry=37701;','UPDATE creature_template SET maxlevel=20 WHERE entry=37701;'),
  ('UPDATE creature_template SET faction=35 WHERE entry=37701;','UPDATE creature_template SET faction=21 WHERE entry=37701;'),
  ('UPDATE creature SET map=0 WHERE id=37701 AND map=654;','UPDATE creature SET map=654 WHERE id=37701 AND map=0;')]:
  sql(change);before=checksum(tables);sql(text);assert checksum(tables)==before,'Custom template/map guard failed';sql(restore)
 # A shared template must be preserved even when it still has Gilneas spawns.
 guid=sql('SELECT MIN(guid) FROM creature WHERE id=37701;').stdout.strip()
 sql('UPDATE creature SET map=0 WHERE guid='+guid+';');before=checksum(tables);sql(text);assert checksum(tables)==before,'Mixed-map template changed';sql('UPDATE creature SET map=654 WHERE guid='+guid+';')
 sql(text)
 # Exercise the real duplicate-key branch with both release MyISAM and InnoDB.
 engine=sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='creature_template_scaling';").stdout.strip()
 try:
  for target_engine in ('MyISAM','InnoDB'):
   sql('ALTER TABLE creature_template_scaling ENGINE='+target_engine+';')
   sql('DELETE FROM creature_template_scaling WHERE Entry=37701;')
   sql(text);before=checksum(tables);sql(text);assert checksum(tables)==before,'Repeated insert changed '+target_engine
   sql('UPDATE creature_template_scaling SET LevelScalingMin=7,LevelScalingMax=12,LevelScalingDeltaMin=-1,LevelScalingDeltaMax=2,VerifiedBuild=26972 WHERE Entry=37701;')
   before=checksum(tables);sql(text);assert checksum(tables)==before,'Duplicate-key branch overwrote custom '+target_engine
 finally:
  sql('ALTER TABLE creature_template_scaling ENGINE='+engine+';')
 print('PASS: Slavedriver first/repeat/custom scaling/AI/bounds/faction/no Gilneas/mixed-map/unrelated preservation')
