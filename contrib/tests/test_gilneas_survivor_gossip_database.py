"""Guarded survivor gossip flag and custom script preservation."""
from pathlib import Path

def test_gilneas_survivor_gossip_database(sql, checksum):
 text=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_10_15_world_gilneas_survivor_gossip.sql').read_text('utf8')
 tables=sql('SHOW TABLES;').stdout.splitlines()
 other=checksum([t for t in tables if t!='creature_template'])
 sql(text)
 assert sql("SELECT npcflag&1,AIName,ScriptName FROM creature_template WHERE entry=37067;").stdout.strip()=='1\t\tnpc_crash_survivor_37067'
 assert other==checksum([t for t in tables if t!='creature_template'])
 before=checksum(tables);sql(text);assert before==checksum(tables)
 sql("UPDATE creature_template SET ScriptName='custom_survivor' WHERE entry=37067;")
 before=checksum(tables);sql(text);assert before==checksum(tables)
 sql("UPDATE creature_template SET ScriptName='npc_crash_survivor_37067' WHERE entry=37067;")
 print('PASS survivor gossip SQL: native binding, gossip flag, idempotency, custom script and other tables preserved')
