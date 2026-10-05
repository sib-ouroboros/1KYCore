-- Item50134 -> spell71061 -> event23338. Eight temporary allies, no permanent spawns.
-- Keep native faction2207 (Gilnean, friendly Alliance and hostile to ranger faction2213).
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_gilneas_taldoren_tracker'
WHERE `entry`=38027 AND `faction`=2207 AND `ScriptName` IN ('','npc_gilneas_taldoren_tracker');
INSERT INTO `spell_script_names` (`spell_id`,`ScriptName`)
SELECT 71061,'spell_gilneas_horn_of_taldoren'
WHERE NOT EXISTS (SELECT 1 FROM `spell_script_names` WHERE `spell_id`=71061 AND `ScriptName`='spell_gilneas_horn_of_taldoren');
