-- Requested simplified completion: talk to a crash survivor for quest 24468.
UPDATE `creature_template`
SET `npcflag`=`npcflag`|1, `AIName`='', `ScriptName`='npc_crash_survivor_37067'
WHERE `entry`=37067 AND `ScriptName` IN ('','npc_crash_survivor_37067');
