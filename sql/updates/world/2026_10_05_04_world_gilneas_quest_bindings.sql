-- Keep the spell hook active even when the mastiff is a Pet and uses PetAI.
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`)
SELECT 67805, 'spell_gilneas_attack_lurker'
WHERE NOT EXISTS (
    SELECT 1 FROM `spell_script_names`
    WHERE `spell_id` = 67805 AND `ScriptName` = 'spell_gilneas_attack_lurker'
);

-- Scope AI bindings to these quest actors. Other NPC and spell scripts are untouched.
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_josiah_avery_35369' WHERE `entry` = 35369;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_lorna_crowley_35378' WHERE `entry` = 35378;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bloodfang_lurker_35463' WHERE `entry` = 35463;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_gilnean_mastiff_35631' WHERE `entry` = 35631;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_krennan_aranas_36331' WHERE `entry` = 36331;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_king_genn_greymane_36332' WHERE `entry` = 36332;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_josiah_avery_trigger_50415' WHERE `entry` = 50415;
