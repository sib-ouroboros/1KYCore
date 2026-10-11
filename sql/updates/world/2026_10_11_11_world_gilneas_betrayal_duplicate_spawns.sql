-- Quest24592 requires one Walden37733 and one Ashbury37735.
-- Keep Walden802443 (native ground-floor patrol) and Ashbury802419.
-- Only exact stock duplicates in the same map/phase are removed.
DROP TEMPORARY TABLE IF EXISTS gilneas_betrayal_duplicates;
CREATE TEMPORARY TABLE gilneas_betrayal_duplicates (guid BIGINT UNSIGNED PRIMARY KEY);
INSERT INTO gilneas_betrayal_duplicates
SELECT c.guid FROM creature c JOIN creature k ON k.guid=802443
WHERE c.guid=802425 AND c.id=37733 AND k.id=c.id
 AND c.map=654 AND k.map=c.map AND c.PhaseId=186 AND k.PhaseId=c.PhaseId
 AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND ABS(c.position_x-(-1917.36))<0.05 AND ABS(c.position_y-(987.519))<0.05
 AND ABS(c.position_z-(86.8961))<0.05 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM smart_scripts a WHERE a.entryorguid=-CAST(c.guid AS SIGNED) AND a.source_type=0);
INSERT INTO gilneas_betrayal_duplicates
SELECT c.guid FROM creature c JOIN creature k ON k.guid=802443
WHERE c.guid=802426 AND c.id=37733 AND k.id=c.id
 AND c.map=654 AND k.map=c.map AND c.PhaseId=186 AND k.PhaseId=c.PhaseId
 AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND ABS(c.position_x-(-1925.5))<0.05 AND ABS(c.position_y-(982.557))<0.05
 AND ABS(c.position_z-(77.7381))<0.05 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM smart_scripts a WHERE a.entryorguid=-CAST(c.guid AS SIGNED) AND a.source_type=0);
INSERT INTO gilneas_betrayal_duplicates
SELECT c.guid FROM creature c JOIN creature k ON k.guid=802443
WHERE c.guid=802450 AND c.id=37733 AND k.id=c.id
 AND c.map=654 AND k.map=c.map AND c.PhaseId=186 AND k.PhaseId=c.PhaseId
 AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND ABS(c.position_x-(-1923.72))<0.05 AND ABS(c.position_y-(981.761))<0.05
 AND ABS(c.position_z-(77.7388))<0.05 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM smart_scripts a WHERE a.entryorguid=-CAST(c.guid AS SIGNED) AND a.source_type=0);
INSERT INTO gilneas_betrayal_duplicates
SELECT c.guid FROM creature c JOIN creature k ON k.guid=802419
WHERE c.guid=802416 AND c.id=37735 AND k.id=c.id
 AND c.map=654 AND k.map=c.map AND c.PhaseId=186 AND k.PhaseId=c.PhaseId
 AND c.PhaseGroup=0 AND k.PhaseGroup=0
 AND ABS(c.position_x-(-2096.29))<0.05 AND ABS(c.position_y-(771.818))<0.05
 AND ABS(c.position_z-(94.2449))<0.05 AND c.MovementType=0 AND c.spawndist=0
 AND NOT EXISTS (SELECT 1 FROM creature_addon a WHERE a.guid=c.guid AND a.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid)
 AND NOT EXISTS (SELECT 1 FROM game_event_creature e WHERE e.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM pool_creature p WHERE p.guid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM linked_respawn l WHERE l.guid=c.guid OR l.linkedGuid=c.guid)
 AND NOT EXISTS (SELECT 1 FROM smart_scripts a WHERE a.entryorguid=-CAST(c.guid AS SIGNED) AND a.source_type=0);
DELETE a FROM creature_addon a JOIN gilneas_betrayal_duplicates d ON d.guid=a.guid;
DELETE c FROM creature c JOIN gilneas_betrayal_duplicates d ON d.guid=c.guid;
DROP TEMPORARY TABLE gilneas_betrayal_duplicates;
