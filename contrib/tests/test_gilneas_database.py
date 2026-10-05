#!/usr/bin/env python3
"""Gilneas migrations on a disposable DB735.02/release schema copy.

Caller must provide an isolated database; never pass the deployed world database.
"""
from pathlib import Path
import json
from audit_gilneas_bindings import registered_scripts, audit

def test_gilneas_database(sql, checksum):
 root=Path(__file__).resolve().parents[2]
 files=['2026_10_06_00_world_gilneas_early_mechanics.sql','2026_10_06_01_world_gilneas_quest_object_spawns.sql','2026_10_06_02_world_gilneas_rescue_bindings.sql','2026_10_06_03_world_gilneas_duskhaven_phase_handoff.sql','2026_10_06_04_world_gilneas_walden_genn.sql','2026_10_06_05_world_gilneas_half_burnt_torch.sql','2026_10_06_06_world_gilneas_liberation_day.sql','2026_10_06_07_world_gilneas_horn_of_taldoren.sql','2026_10_06_08_world_gilneas_chance_lucius.sql','2026_10_06_09_world_gilneas_manor_ride.sql','2026_10_06_10_world_gilneas_late_phase_handoffs.sql','2026_10_06_11_world_gilneas_leader_of_the_pack.sql','2026_10_06_12_world_gilneas_bat_flight.sql']
 texts=[(root/'sql/updates/world'/name).read_text('utf8') for name in files]
 manifest=json.loads((root/'docs/audit-data/gilneas-static-restoration.json').read_text('utf8'))
 tables=sql('SHOW TABLES;').stdout.splitlines()
 modified={'creature_template','creature','creature_addon','game_event_creature','pool_creature','creature_formations','smart_scripts','gameobject','npc_spellclick_spells','spell_script_names','spell_area','waypoint_data'}
 foreign_phases=sql('SELECT * FROM spell_area WHERE area BETWEEN 7037 AND 7129 ORDER BY spell,area,quest_start,quest_end;').stdout
 untouched=checksum([t for t in tables if t not in modified])
 # Exercise the actual legacy assignments present in the published release.
 sql("UPDATE creature_template SET ScriptName='npc_james_36268' WHERE entry=36288 AND ScriptName IN ('','npc_ashley_36269');")
 sql("UPDATE creature_template SET ScriptName='npc_ashley_36269' WHERE entry=36289 AND ScriptName IN ('','npc_james_36268');")
 sql('UPDATE creature_template SET KillCredit1=14386 WHERE entry=36312 AND KillCredit1=0;')
 scripts=registered_scripts();registered={s['script'] for s in scripts if s['registered']}
 # Unrelated existing spell hooks survive.
 sql("INSERT INTO spell_script_names (spell_id,ScriptName) VALUES (68735,'gilneas_test_custom_hook');")
 for text in texts:sql(text)
 snapshot={}
 names=','.join("'"+name+"'" for name in sorted(registered))
 for table,key in [('creature_template','entry'),('creature','guid'),('gameobject_template','entry'),('gameobject','guid'),('spell_script_names','spell_id')]:
  columns=f"'{key}',`{key}`,'ScriptName',ScriptName"+(" ,'AIName',AIName" if table=='creature_template' else '')
  snapshot[table]=[json.loads(line) for line in sql(f"SELECT JSON_OBJECT({columns}) FROM `{table}` WHERE ScriptName IN ({names});").stdout.splitlines()]
 binding_report=audit(snapshot)
 once=checksum(tables)
 for text in texts:sql(text)
 assert checksum(tables)==once,'Repeat changed persistent data'
 assert checksum([t for t in tables if t not in modified])==untouched,'Unrelated tables changed'
 assert sql('SELECT COUNT(*) FROM creature WHERE id=36140 AND map=654 AND PhaseId=182;').stdout.strip()=='1'
 assert sql('SELECT COUNT(*) FROM gameobject WHERE id=196403 AND map=654 AND PhaseId=182;').stdout.strip()=='10'
 assert sql('SELECT * FROM spell_area WHERE area BETWEEN 7037 AND 7129 ORDER BY spell,area,quest_start,quest_end;').stdout==foreign_phases,'Draenor phases changed'
 assert sql('SELECT COUNT(*) FROM spell_area WHERE spell=68483 AND area=4714 AND quest_start=14396 AND quest_start_status=74;').stdout.strip()=='1'
 for entry,script in [(36409,'npc_mastiff_36409'),(36405,'npc_mastiff_36405'),(37783,'npc_lorna_crowley_37783'),(36741,'npc_swift_mountain_horse_36741'),(36452,'npc_gwen_armstead_36452'),(36606,'npc_queen_mia_greymane_36606'),(36459,'npc_chance_36459'),(36461,'npc_gilneas_lucius_the_cruel'),(38027,'npc_gilneas_taldoren_tracker'),(37694,'npc_enslaved_villager_37694'),(37876,'npc_king_genn_greymane_37876'),(36290,'npc_lord_godfrey_36290'),(36287,'npc_cynthia_36267'),(36288,'npc_ashley_36269'),(36289,'npc_james_36268'),(36231,'npc_horrid_abomination_36231'),(36440,'npc_drowning_watchman_36440'),(36540,'npc_mountain_horse_36540'),(36555,'npc_mountain_horse_36555'),(37067,'npc_crash_survivor_37067'),(37078,'npc_swamp_crocolisk_37078'),(36488,'npc_forsaken_castaway_36488')]:
  assert script in registered,(entry,script,'unregistered C++')
  assert sql(f"SELECT COUNT(*) FROM creature_template WHERE entry={entry} AND ScriptName='{script}' AND AIName='';").stdout.strip()=='1',(entry,script)
 for spell,script in [(72472,'spell_gilneas_captured_bat_summon'),(68682,'spell_gilneas_leader_of_the_pack'),(71061,'spell_gilneas_horn_of_taldoren'),(68735,'spell_rescue_drowning_watchman_68735'),(68903,'spell_round_up_horse_68903'),(75359,'spell_gilneas_walden_brandy'),(70631,'spell_gilneas_half_burnt_torch')]:
  assert script in registered
  assert sql(f"SELECT COUNT(*) FROM spell_script_names WHERE spell_id={spell} AND ScriptName='{script}';").stdout.strip()=='1'
 assert sql('SELECT COUNT(*) FROM creature_loot_template WHERE Entry=36461 AND Item=49281 AND Chance=100 AND QuestRequired=1;').stdout.strip()=='1','Native cat loot dependency'
 assert sql('SELECT cast_flags FROM npc_spellclick_spells WHERE npc_entry=36440 AND spell_id=68735;').stdout.strip()=='1'
 assert sql("SELECT COUNT(*) FROM spell_script_names WHERE spell_id=68735 AND ScriptName='gilneas_test_custom_hook';").stdout.strip()=='1'
 for row in manifest['rows']:
  spawn=row['spawn']
  assert sql(f"SELECT COUNT(*) FROM gameobject WHERE guid={spawn['guid']} AND id={spawn['id']} AND map=654 AND PhaseId={spawn['PhaseId']};").stdout.strip()=='1',spawn['guid']
 assert sql('SELECT KillCredit1 FROM creature_template WHERE entry=36312;').stdout.strip()=='0'
 route=json.loads((root/'docs/audit-data/gilneas-horse-route-source.json').read_text('utf8'))
 assert sql('SELECT COUNT(*) FROM waypoint_data WHERE id=3674101;').stdout.strip()=='28'
 for point in route['points']:
  assert sql(f"SELECT COUNT(*) FROM waypoint_data WHERE id=3674101 AND point={point['point']} AND ABS(position_x-({point['x']}))<0.01 AND ABS(position_y-({point['y']}))<0.01 AND ABS(position_z-({point['z']}))<0.01 AND move_type=1;").stdout.strip()=='1'
 assert sql('SELECT COUNT(*) FROM spell_area WHERE spell=69077 AND area IN (4714,4817) AND quest_start=14465 AND quest_end=24438 AND quest_start_status=66 AND quest_end_status=64;').stdout.strip()=='2'
 sql('UPDATE waypoint_data SET position_x=position_x+100 WHERE id=3674101 AND point=1;')
 before=checksum(tables);sql(texts[9],ok=False)
 assert checksum(tables)==before,'Conflicting route wrote permanent data'
 sql('UPDATE waypoint_data SET position_x=position_x-100 WHERE id=3674101 AND point=1;')
 assert sql('SELECT COUNT(*) FROM spell_area WHERE spell=69484 AND area IN (4714,4730,4731,4732,4734,4787,4788,4794,4817,4842) AND quest_start=14467 AND quest_end=24676 AND quest_end_status=64;').stdout.strip()=='10'
 for spell,start,end,mask in [(69485,24676,24903,64),(70696,24903,24678,74),(69486,24678,24680,74),(70695,24680,14434,74)]:
  assert sql(f'SELECT COUNT(*) FROM spell_area WHERE spell={spell} AND area IN (4714,4755) AND quest_start={start} AND quest_end={end} AND quest_start_status={mask};').stdout.strip()=='2'
 assert sql('SELECT COUNT(*) FROM creature WHERE map=654 AND PhaseId=0 AND PhaseGroup=440 AND ((guid=802508 AND id=37783) OR (guid=802514 AND id=38553));').stdout.strip()=='2'
 bat=json.loads((root/'docs/audit-data/gilneas-bat-source.json').read_text('utf8'))
 for path_id,route in bat['routes'].items():
  assert sql(f'SELECT COUNT(*) FROM waypoint_data WHERE id={path_id};').stdout.strip()==str(len(route['points']))
  for point in route['points']:
   assert sql(f"SELECT COUNT(*) FROM waypoint_data WHERE id={path_id} AND point={point['point']} AND ABS(position_x-({point['x']}))<0.01 AND ABS(position_y-({point['y']}))<0.01 AND ABS(position_z-({point['z']}))<0.01 AND move_type=1;").stdout.strip()=='1'
 for actor in bat['actors']:
  assert sql(f"SELECT COUNT(*) FROM creature WHERE guid={actor['guid']} AND id={actor['id']} AND map=654 AND PhaseId=190 AND PhaseGroup=0;").stdout.strip()=='1'
 assert sql('SELECT cast_flags FROM npc_spellclick_spells WHERE npc_entry=38615 AND spell_id=72472;').stdout.strip()=='1'
 assert sql('SELECT COUNT(*) FROM creature_template WHERE entry=38615 AND npcflag & 16777216;').stdout.strip()=='1'
 sql('UPDATE waypoint_data SET position_x=position_x+100 WHERE id=3854003 AND point=1;')
 before=checksum(tables);sql(texts[12],ok=False);assert checksum(tables)==before,'Foreign bat route changed'
 sql('UPDATE waypoint_data SET position_x=position_x-100 WHERE id=3854003 AND point=1;')
 # A foreign GUID cannot be overwritten, nor can an earlier part of this migration write.
 first=manifest['rows'][0]['spawn'];guid=first['guid']
 sql(f'UPDATE gameobject SET id=9999999 WHERE guid={guid};')
 before=checksum(tables);failure=sql(texts[1],ok=False)
 assert '_1kycore_gilneas_spawn_guard' in failure.stderr and 'Duplicate entry' in failure.stderr
 assert checksum(tables)==before,'Conflict wrote permanent data'
 sql(f"UPDATE gameobject SET id={first['id']} WHERE guid={guid};")
 # Preserve a compatible existing spawn with a different GUID; don't duplicate it.
 sql(f'UPDATE gameobject SET guid=310066999 WHERE guid={guid};')
 sql(texts[1]);assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid={guid};').stdout.strip()=='0'
 assert sql('SELECT COUNT(*) FROM gameobject WHERE guid=310066999;').stdout.strip()=='1'
 # Protect administrator scripts instead of replacing them with blanket bindings.
 sql("UPDATE creature_template SET ScriptName='custom_child',AIName='' WHERE entry=36288;")
 for text in (texts[0],texts[2]):sql(text)
 assert sql("SELECT ScriptName FROM creature_template WHERE entry=36288;").stdout.strip()=='custom_child'
 print('PASS: Gilneas first/repeat migration, actor bindings, 95 spawns, conflict rejection and unrelated preservation')
 return binding_report
