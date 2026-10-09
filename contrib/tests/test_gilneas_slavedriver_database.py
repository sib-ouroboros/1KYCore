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
 print('PASS: Slavedriver first/repeat/custom scaling/AI/bounds/faction/no Gilneas/mixed-map/unrelated preservation')
