-- Remove only identified overlapping Gilneas abominations; keep the original nine quest targets.
-- Custom movement, formations, events, pools and linked respawns prevent removal.
DROP TEMPORARY TABLE IF EXISTS gilneas_duplicate_spawns;
CREATE TEMPORARY TABLE gilneas_duplicate_spawns (guid BIGINT UNSIGNED PRIMARY KEY);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801360
WHERE c.guid=801400 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801368
WHERE c.guid=801401 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801361
WHERE c.guid=801403 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801357
WHERE c.guid=801404 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801362
WHERE c.guid=801425 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801359
WHERE c.guid=801477 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801356
WHERE c.guid=801528 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801362
WHERE c.guid=801548 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801362
WHERE c.guid=801596 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801368
WHERE c.guid=801601 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801356
WHERE c.guid=801603 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801389
WHERE c.guid=801604 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801361
WHERE c.guid=801606 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801360
WHERE c.guid=801608 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801359
WHERE c.guid=801609 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801384
WHERE c.guid=801610 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c JOIN creature k ON k.guid=801357
WHERE c.guid=801620 AND c.id=36231 AND k.id=c.id AND c.map=654 AND k.map=c.map
 AND c.PhaseId=182 AND k.PhaseId=c.PhaseId AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND POW(c.position_x-k.position_x,2)+POW(c.position_y-k.position_y,2)+POW(c.position_z-k.position_z,2)<16
 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid);
-- Lucius is summoned personally by Chance, never a persistent quest-area spawn.
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c WHERE c.guid=801836
 AND c.id=36461 AND c.map=654 AND c.PhaseId=183 AND c.PhaseGroup=0
 AND ABS(c.position_x-(-2106.37))<0.05 AND ABS(c.position_y-(2331.11))<0.05
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0);
INSERT INTO gilneas_duplicate_spawns SELECT c.guid FROM creature c WHERE c.guid=801901
 AND c.id=36461 AND c.map=654 AND c.PhaseId=183 AND c.PhaseGroup=0
 AND ABS(c.position_x-(-2111.52))<0.05 AND ABS(c.position_y-(2329.95))<0.05
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0);
DELETE a FROM creature_addon a JOIN gilneas_duplicate_spawns d ON d.guid=a.guid;
DELETE c FROM creature c JOIN gilneas_duplicate_spawns d ON d.guid=c.guid;
DROP TEMPORARY TABLE gilneas_duplicate_spawns;
-- Preserve existing scaling; missing rows otherwise choose random levels 5..20.
INSERT INTO creature_template_scaling
 (Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT ct.entry,ct.minlevel,ct.maxlevel,0,0,0 FROM creature_template ct
WHERE ct.entry=36671 AND ct.minlevel=5 AND ct.maxlevel=20 AND ct.faction=2201
 AND ct.HealthModifier=1 AND ct.DamageModifier=1 AND ct.ScriptName=''
 AND EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map=654)
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654)
ON DUPLICATE KEY UPDATE Entry=creature_template_scaling.Entry;
