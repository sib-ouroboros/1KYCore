-- Handle the successful impact of Lorna's cinematic shot at summoned Avery.
-- The C++ hook leaves all other users of Shoot (6660) unchanged.
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`)
SELECT 6660, 'spell_gilneas_lorna_shot'
WHERE NOT EXISTS (
    SELECT 1 FROM `spell_script_names`
    WHERE `spell_id` = 6660 AND `ScriptName` = 'spell_gilneas_lorna_shot'
);

-- Start the personal actor in human appearance before the transformation cue.
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_josiah_avery_scene_35370' WHERE `entry` = 35370;
