-- Quest14401 objective is item49281, supplied by existing100% quest loot36461.
-- Click starts a private ambush; the shared Chance spawn is not removed.
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_chance_36459', `npcflag`=`npcflag` | 1
WHERE `entry`=36459 AND `ScriptName` IN ('','npc_chance_36459');
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_gilneas_lucius_the_cruel'
WHERE `entry`=36461 AND `ScriptName` IN ('','npc_gilneas_lucius_the_cruel');
