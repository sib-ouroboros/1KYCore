-- Quest14400: source sql/test/world/magic_storm/_revision_/need test/2018_10_11_00_world_duskhaven_part2.sql.
-- Restore only the known release chest, preserving custom phases/positions/templates.
UPDATE gameobject g JOIN gameobject_template t ON t.entry=g.id
SET g.PhaseId=183
WHERE g.id=196472 AND g.map=654 AND g.PhaseId=0 AND g.PhaseGroup=0 AND g.phaseUseFlags=0
 AND ABS(g.position_x+2116.14)<0.001 AND ABS(g.position_y-2431.93)<0.001 AND ABS(g.position_z-13.0241)<0.001
 AND t.type=3 AND t.Data0=1691 AND t.Data1=27591 AND t.ScriptName=''
 AND EXISTS (SELECT 1 FROM quest_objectives WHERE QuestID=14400 AND Type=1 AND ObjectID=49279 AND Amount=1)
 AND EXISTS (SELECT 1 FROM gameobject_loot_template WHERE Entry=27591 AND Item=49279 AND Chance=100 AND QuestRequired=1)
 AND EXISTS (SELECT 1 FROM creature WHERE id=36458 AND map=654 AND PhaseId=183);
-- Same source uses5s, instead of the release7200s; retain any custom respawn delay.
UPDATE gameobject g JOIN gameobject_template t ON t.entry=g.id
SET g.spawntimesecs=5
WHERE g.id=196472 AND g.map=654 AND g.PhaseId=183 AND g.PhaseGroup=0 AND g.phaseUseFlags=0 AND g.spawntimesecs=7200
 AND ABS(g.position_x+2116.14)<0.001 AND ABS(g.position_y-2431.93)<0.001 AND ABS(g.position_z-13.0241)<0.001
 AND t.type=3 AND t.Data0=1691 AND t.Data1=27591 AND t.ScriptName=''
 AND EXISTS (SELECT 1 FROM quest_objectives WHERE QuestID=14400 AND Type=1 AND ObjectID=49279 AND Amount=1)
 AND EXISTS (SELECT 1 FROM gameobject_loot_template WHERE Entry=27591 AND Item=49279 AND Chance=100 AND QuestRequired=1);
