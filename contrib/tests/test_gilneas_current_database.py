"""Current Gilneas scene/localization updates; isolated database only."""
from pathlib import Path
import json

def test_gilneas_current_database(sql,checksum):
 root=Path(__file__).resolve().parents[2]
 names=['2026_10_11_01_world_gilneas_quest_ruru_missing.sql','2026_10_11_02_world_gilneas_scene_spawns_balance.sql','2026_10_11_03_world_gilneas_dialogue_ruru.sql','2026_10_11_04_world_gilneas_fox_roaming.sql','2026_10_11_05_world_gilneas_gwen_mount.sql','2026_10_11_06_world_gilneas_koroth_scene_visibility.sql','2026_10_11_07_world_gilneas_survivor_talk_credit.sql','2026_10_11_08_world_gilneas_battle_actor_scaling.sql','2026_10_11_09_world_gilneas_battle_dialogue.sql','2026_10_11_10_world_gilneas_koroth_scene_passive.sql']
 texts=[(root/'sql/updates/world'/n).read_text('utf8') for n in names]
 tables=sql('SHOW TABLES;').stdout.splitlines()
 modified={'creature_template','waypoint_data','creature_text','quest_objectives','quest_template_locale','quest_objectives_locale','quest_offer_reward_locale','quest_request_items_locale','creature','creature_addon','creature_template_scaling','creature_text_locale'}
 battle_ids='38210,38218,38221,38331,38415,38420,38426,38464,38465,38466'
 old_scaling={line.split('	')[0]:line for line in sql('SELECT * FROM creature_template_scaling WHERE Entry IN ('+battle_ids+');').stdout.splitlines()}
 untouched=checksum([t for t in tables if t not in modified])
 for text in texts:sql(text)
 assert sql("SELECT COUNT(*) FROM creature_template WHERE entry IN (37805,37806,37807,37808) AND AIName='' AND ScriptName='npc_gilneas_koroth_scene_actor';").stdout.strip()=='4'
 assert sql('SELECT mount FROM creature_addon WHERE guid=801805;').stdout.strip()=='229'
 assert sql("SELECT COUNT(*) FROM creature_addon a JOIN creature c ON c.guid=a.guid WHERE c.map=654 AND c.id IN (37805,37806,37807,37808) AND a.auras='80852';").stdout.strip()=='28'
 assert sql('SELECT ObjectID,Amount FROM quest_objectives WHERE ID=255768 AND QuestID=24468;').stdout.strip()=='37067\t5'
 new_scaling={line.split('	')[0]:line for line in sql('SELECT * FROM creature_template_scaling WHERE Entry IN ('+battle_ids+');').stdout.splitlines()}
 assert len(new_scaling)==10
 for entry,row in old_scaling.items():assert new_scaling[entry]==row,'Existing custom battle scaling was overwritten'
 for entry in set(new_scaling)-set(old_scaling):
  assert sql('SELECT LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax FROM creature_template_scaling WHERE Entry='+entry+';').stdout.strip()=='5	20	0	0'
 proof=json.loads((root/'docs/audit-data/gilneas-battle-dialogue.json').read_text('utf8'))['lines']
 for line in proof:
  e,g,i,b=line['entry'],line['group'],line['id'],line['broadcast']
  assert sql(f'SELECT BroadcastTextId FROM creature_text WHERE CreatureID={e} AND GroupID={g} AND ID={i};').stdout.strip()==str(b),(e,g,i)
  assert sql(f'SELECT Sound FROM creature_text WHERE CreatureID={e} AND GroupID={g} AND ID={i};').stdout.strip()==str(line['sound']),(e,g,i)
 assert sql("SELECT COUNT(*) FROM creature_text_locale WHERE CreatureID=38218 AND GroupID BETWEEN 0 AND 6 AND Locale='ruRU' AND Text<>'';").stdout.strip()=='7'
 assert sql('SELECT id,COUNT(*) FROM waypoint_data WHERE id IN (3847401,3846901) GROUP BY id ORDER BY id;').stdout.strip()=='3846901\t3\n3847401\t4'
 once=checksum(tables)
 for text in texts:sql(text)
 assert once==checksum(tables),'Repeat changed data'
 assert untouched==checksum([t for t in tables if t not in modified]),'Unrelated tables changed'
 assert sql("SELECT COUNT(*) FROM quest_template_locale WHERE ID=14368 AND locale='ruRU' AND LogTitle<>'';").stdout.strip()=='1'
 assert sql('SELECT COUNT(*) FROM creature WHERE guid IN (801836,801901) AND id=36461 AND map=654;').stdout.strip()=='0'
 assert sql('SELECT COUNT(*) FROM creature WHERE id=36231 AND map=654;').stdout.strip()=='9'
 assert sql("SELECT COUNT(*) FROM creature_text_locale WHERE CreatureID IN (36287,36288,36289,36461) AND Locale='ruRU' AND Text<>'';").stdout.strip()=='7'
 assert sql('SELECT COUNT(*) FROM creature WHERE id=36512 AND map=654 AND PhaseId=183 AND MovementType=1 AND spawndist=8;').stdout.strip()=='11'
 assert sql('SELECT COUNT(*) FROM creature_template_scaling WHERE Entry=36671;').stdout.strip()=='1'
 sql("UPDATE creature_text_locale SET Text='custom dialogue' WHERE CreatureID=36461;")
 sql("UPDATE quest_template_locale SET LogTitle='custom quest' WHERE ID=14368 AND locale='ruRU';")
 sql('UPDATE creature SET MovementType=2,spawndist=15 WHERE guid=801829;')
 for text in texts:sql(text)
 assert sql('SELECT Text FROM creature_text_locale WHERE CreatureID=36461;').stdout.strip()=='custom dialogue'
 assert sql("SELECT LogTitle FROM quest_template_locale WHERE ID=14368 AND locale='ruRU';").stdout.strip()=='custom quest'
 assert sql('SELECT MovementType,spawndist FROM creature WHERE guid=801829;').stdout.strip()=='2\t15'
 sql('UPDATE creature_addon SET mount=65,emote=1 WHERE guid=801805;')
 sql(texts[4])
 assert sql('SELECT mount,emote FROM creature_addon WHERE guid=801805;').stdout.strip()=='65\t1'
 sql("UPDATE creature_addon SET auras='80852 12345',mount=65 WHERE guid=802093;")
 sql(texts[5])
 assert sql('SELECT auras,mount FROM creature_addon WHERE guid=802093;').stdout.strip()=='80852 12345\t65'
 print('PASS: current Gilneas spawns, balance, dialogue, quest locales, roaming and preservation')

 # A custom group, binding and nonempty localization must survive repeated restoration.
 sql("UPDATE creature_text SET Text='custom speech',BroadcastTextId=12345 WHERE CreatureID=38218 AND GroupID=0 AND ID=0;")
 sql("UPDATE creature_text_locale SET Text='custom ru speech' WHERE CreatureID=38218 AND GroupID=1 AND ID=0 AND Locale='ruRU';")
 sql("UPDATE creature_text_locale SET Locale='frFR',Text='custom fr speech' WHERE CreatureID=38218 AND GroupID=2 AND ID=0;")
 sql("DELETE FROM creature_text WHERE CreatureID=38218 AND GroupID=7; INSERT INTO creature_text (CreatureID,GroupID,ID,Text,Type,Probability) VALUES (38218,7,9,'custom variant',14,100);")
 sql('UPDATE creature_text SET Sound=99999 WHERE CreatureID=38218 AND GroupID=3 AND ID=0;')
 sql(texts[-1])
 assert sql('SELECT Sound FROM creature_text WHERE CreatureID=38218 AND GroupID=3 AND ID=0;').stdout.strip()=='99999'
 assert sql('SELECT Text,BroadcastTextId FROM creature_text WHERE CreatureID=38218 AND GroupID=0 AND ID=0;').stdout.strip()=='custom speech\t12345'
 assert sql('SELECT Text FROM creature_text_locale WHERE CreatureID=38218 AND GroupID=1 AND ID=0;').stdout.strip()=='custom ru speech'
 assert sql('SELECT Locale,Text FROM creature_text_locale WHERE CreatureID=38218 AND GroupID=2 AND ID=0;').stdout.strip()=='frFR\tcustom fr speech'
 assert sql('SELECT COUNT(*) FROM creature_text WHERE CreatureID=38218 AND GroupID=7;').stdout.strip()=='1'
 print('PASS: all battle text groups, repeated restoration and custom/foreign locale preservation')

 sql('DELETE FROM waypoint_data WHERE id=3847401; INSERT INTO waypoint_data(id,point,position_x,position_y,position_z) VALUES (3847401,99,1,2,3);')
 before=sql('SELECT * FROM waypoint_data WHERE id=3847401;').stdout
 sql(texts[-1])
 assert sql('SELECT * FROM waypoint_data WHERE id=3847401;').stdout==before,'Partial custom cinematic route was mixed with native points'

 sql("UPDATE creature_template SET ScriptName='custom_scene_script' WHERE entry=37806;")
 sql("UPDATE creature_template SET ScriptName='',AIName='SmartAI' WHERE entry=37807;")
 sql(texts[-1])
 assert sql("SELECT ScriptName FROM creature_template WHERE entry=37806;").stdout.strip()=='custom_scene_script'
 assert sql("SELECT AIName,ScriptName FROM creature_template WHERE entry=37807;").stdout.strip()=='SmartAI'
