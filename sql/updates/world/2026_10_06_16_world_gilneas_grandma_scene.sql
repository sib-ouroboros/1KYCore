-- Bind only the personal helper factory; persistent Grandma retains default questgiver AI.
-- No template flags, questgiver/gossip fields, shared spawns, texts or loot changes.
UPDATE creature_template SET ScriptName='npc_gilneas_grandma_scene'
WHERE entry=36458 AND AIName='' AND ScriptName IN ('','npc_gilneas_grandma_scene');
