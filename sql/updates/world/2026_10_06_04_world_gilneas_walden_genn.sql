-- Existing Genn scene plus scoped protection against ambient NPC damage.
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_king_genn_greymane_37876'
WHERE `entry`=37876 AND `ScriptName` IN ('','npc_king_genn_greymane_37876');
INSERT INTO `spell_script_names` (`spell_id`,`ScriptName`)
SELECT 75359,'spell_gilneas_walden_brandy'
WHERE NOT EXISTS (SELECT 1 FROM `spell_script_names` WHERE `spell_id`=75359 AND `ScriptName`='spell_gilneas_walden_brandy');
