-- Only this additional handler; preserve all other spell bindings.
INSERT INTO spell_script_names(spell_id,ScriptName)
SELECT 68235,'spell_gilneas_cannon_scene_target'
WHERE NOT EXISTS (SELECT 1 FROM spell_script_names WHERE spell_id=68235 AND ScriptName='spell_gilneas_cannon_scene_target');
