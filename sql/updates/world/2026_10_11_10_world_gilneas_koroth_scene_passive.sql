-- Invisibility alone does not prevent these cinematic actors from attacking.
-- The native script applies only to audited persistent Gilneas spawn GUIDs.
-- Other spawns and summons retain default AI; custom scripts are preserved.
UPDATE creature_template
SET ScriptName='npc_gilneas_koroth_scene_actor'
WHERE entry IN (37805,37806,37807,37808) AND AIName=''
 AND ScriptName IN ('','npc_gilneas_koroth_scene_actor');
