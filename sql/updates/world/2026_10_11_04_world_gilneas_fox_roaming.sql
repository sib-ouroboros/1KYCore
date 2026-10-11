-- Give idle Gilneas foxes short walks using the native random movement generator.
-- Preserve custom scripts, existing movement, waypoint paths and other maps/phases.
UPDATE creature c
JOIN creature_template ct ON ct.entry=c.id
SET c.MovementType=1,c.spawndist=8
WHERE c.id=36512 AND c.map=654 AND c.PhaseId=183 AND c.PhaseGroup=0
 AND c.MovementType=0 AND c.spawndist=0
 AND ct.AIName='' AND ct.ScriptName=''
 AND NOT EXISTS (SELECT 1 FROM creature_addon ca WHERE ca.guid=c.guid AND ca.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_template_addon ca WHERE ca.entry=c.id AND ca.path_id<>0)
 AND NOT EXISTS (SELECT 1 FROM creature_formations f WHERE f.leaderGUID=c.guid OR f.memberGUID=c.guid);
