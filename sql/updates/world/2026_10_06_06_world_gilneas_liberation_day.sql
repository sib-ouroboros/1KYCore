-- Existing18 villagers match the restored chain positions (0.77-1.16m).
-- Native GO use supplies objective201775; no synthetic NPC kill credit is added.
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_enslaved_villager_37694'
WHERE `entry`=37694 AND `ScriptName` IN ('','npc_enslaved_villager_37694');
