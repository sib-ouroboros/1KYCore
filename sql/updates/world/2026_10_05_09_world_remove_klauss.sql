-- Remove the custom XP-rate selector Klauss. Do not change player XP rates.
-- Clean GUID-owned data before deleting spawns; do not rely on fixed spawn GUIDs.
DELETE a FROM `creature_addon` a INNER JOIN `creature` c ON c.`guid` = a.`guid` WHERE c.`id` = 1000000;
DELETE e FROM `game_event_creature` e INNER JOIN `creature` c ON c.`guid` = e.`guid` WHERE c.`id` = 1000000;
DELETE p FROM `pool_creature` p INNER JOIN `creature` c ON c.`guid` = p.`guid` WHERE c.`id` = 1000000;
DELETE FROM `creature_formations` WHERE `leaderGUID` IN (SELECT `guid` FROM `creature` WHERE `id` = 1000000)
    OR `memberGUID` IN (SELECT `guid` FROM `creature` WHERE `id` = 1000000);
DELETE s FROM `smart_scripts` s INNER JOIN `creature` c ON s.`entryorguid` = -CAST(c.`guid` AS SIGNED)
    WHERE s.`source_type` = 0 AND c.`id` = 1000000;
DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` = 1000000;
DELETE FROM `creature` WHERE `id` = 1000000;

DELETE FROM `creature_template_locale` WHERE `entry` = 1000000;
DELETE FROM `creature_template_addon` WHERE `entry` = 1000000;
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 1000000;
DELETE FROM `creature_template_scaling` WHERE `Entry` = 1000000;
DELETE FROM `creature_text_locale` WHERE `CreatureID` = 1000000;
DELETE FROM `creature_text` WHERE `CreatureID` = 1000000;
DELETE FROM `creature_queststarter` WHERE `id` = 1000000;
DELETE FROM `creature_questender` WHERE `id` = 1000000;
DELETE FROM `creature_questitem` WHERE `CreatureEntry` = 1000000;
DELETE FROM `creature_default_trainer` WHERE `CreatureId` = 1000000;
DELETE FROM `npc_trainer` WHERE `ID` = 1000000;
DELETE FROM `npc_vendor` WHERE `entry` = 1000000;
DELETE FROM `npc_spellclick_spells` WHERE `npc_entry` = 1000000;
DELETE FROM `creature_template` WHERE `entry` = 1000000;
