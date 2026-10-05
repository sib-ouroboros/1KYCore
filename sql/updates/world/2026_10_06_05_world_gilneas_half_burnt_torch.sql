-- Spell70631 is the native item50220 spell; existing vermin/end-NPC spawns are retained.
INSERT INTO `spell_script_names` (`spell_id`,`ScriptName`)
SELECT 70631,'spell_gilneas_half_burnt_torch'
WHERE NOT EXISTS (SELECT 1 FROM `spell_script_names` WHERE `spell_id`=70631 AND `ScriptName`='spell_gilneas_half_burnt_torch');
