"""Current Gilneas scene/localization updates; isolated database only."""
from pathlib import Path

def test_gilneas_current_database(sql,checksum):
 root=Path(__file__).resolve().parents[2]
 names=['2026_10_11_01_world_gilneas_quest_ruru_missing.sql','2026_10_11_02_world_gilneas_scene_spawns_balance.sql','2026_10_11_03_world_gilneas_dialogue_ruru.sql','2026_10_11_04_world_gilneas_fox_roaming.sql','2026_10_11_05_world_gilneas_gwen_mount.sql','2026_10_11_06_world_gilneas_koroth_scene_visibility.sql','2026_10_11_07_world_gilneas_survivor_talk_credit.sql','2026_10_11_08_world_gilneas_battle_actor_scaling.sql']
 texts=[(root/'sql/updates/world'/n).read_text('utf8') for n in names]
 tables=sql('SHOW TABLES;').stdout.splitlines()
 modified={'quest_objectives','quest_template_locale','quest_objectives_locale','quest_offer_reward_locale','quest_request_items_locale','creature','creature_addon','creature_template_scaling','creature_text_locale'}
 untouched=checksum([t for t in tables if t not in modified])
 for text in texts:sql(text)
 assert sql('SELECT mount FROM creature_addon WHERE guid=801805;').stdout.strip()=='229'
 assert sql("SELECT COUNT(*) FROM creature_addon a JOIN creature c ON c.guid=a.guid WHERE c.map=654 AND c.id IN (37805,37806,37807,37808) AND a.auras='80852';").stdout.strip()=='28'
 assert sql('SELECT ObjectID,Amount FROM quest_objectives WHERE ID=255768 AND QuestID=24468;').stdout.strip()=='37067\t5'
 assert sql('SELECT COUNT(*) FROM creature_template_scaling WHERE Entry IN (38210,38218,38221,38331,38415,38420,38426,38464,38465,38466) AND LevelScalingMin=5 AND LevelScalingMax=20 AND LevelScalingDeltaMin=0 AND LevelScalingDeltaMax=0;').stdout.strip()=='10'
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
