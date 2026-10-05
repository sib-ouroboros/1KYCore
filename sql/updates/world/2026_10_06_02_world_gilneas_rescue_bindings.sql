-- Bind only the actors whose existing ownership/credit handlers were audited.
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_drowning_watchman_36440', `npcflag`=`npcflag` | 16777216
WHERE `entry`=36440 AND `ScriptName` IN ('','npc_drowning_watchman_36440');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_mountain_horse_36540'
WHERE `entry`=36540 AND `ScriptName` IN ('','npc_mountain_horse_36540');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_mountain_horse_36555'
WHERE `entry`=36555 AND `ScriptName` IN ('','npc_mountain_horse_36555');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_crash_survivor_37067'
WHERE `entry`=37067 AND `ScriptName` IN ('','npc_crash_survivor_37067');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_swamp_crocolisk_37078'
WHERE `entry`=37078 AND `ScriptName` IN ('','npc_swamp_crocolisk_37078');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_forsaken_castaway_36488'
WHERE `entry`=36488 AND `ScriptName` IN ('','npc_forsaken_castaway_36488');

UPDATE `npc_spellclick_spells` SET `cast_flags`=1 WHERE `npc_entry`=36440 AND `spell_id`=68735;
INSERT INTO `npc_spellclick_spells` (`npc_entry`,`spell_id`,`cast_flags`,`user_type`)
SELECT 36440,68735,1,0 WHERE NOT EXISTS (SELECT 1 FROM `npc_spellclick_spells` WHERE `npc_entry`=36440 AND `spell_id`=68735);
INSERT INTO `spell_script_names` (`spell_id`,`ScriptName`)
SELECT 68735,'spell_rescue_drowning_watchman_68735' WHERE NOT EXISTS (SELECT 1 FROM `spell_script_names` WHERE `spell_id`=68735 AND `ScriptName`='spell_rescue_drowning_watchman_68735');
INSERT INTO `spell_script_names` (`spell_id`,`ScriptName`)
SELECT 68903,'spell_round_up_horse_68903' WHERE NOT EXISTS (SELECT 1 FROM `spell_script_names` WHERE `spell_id`=68903 AND `ScriptName`='spell_round_up_horse_68903');
-- Do not add historical linked-spell68903->68908: DB2 already triggers68908 natively.
