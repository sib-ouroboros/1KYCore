-- Quest 14204: handle the command for either the quest AI or native PetAI.
-- Keep other scripts bound to this spell intact.
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`)
SELECT 67805, 'spell_gilneas_attack_lurker'
WHERE NOT EXISTS (
    SELECT 1 FROM `spell_script_names`
    WHERE `spell_id` = 67805 AND `ScriptName` = 'spell_gilneas_attack_lurker'
);
