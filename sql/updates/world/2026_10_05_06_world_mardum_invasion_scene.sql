-- Quest 40077: personal departure scene, shared Kayn retains other SmartAI events.
-- Requires the accompanying zone_mardum.cpp change and a worldserver restart.
UPDATE `creature_template` SET `ScriptName`='npc_kayn_sunfury_welcome' WHERE `entry`=93011;

-- Seed only missing dialogue; preserve existing text, voice and locale rows.
INSERT IGNORE INTO `creature_text`
(`CreatureID`,`GroupID`,`ID`,`Text`,`Type`,`Language`,`Probability`,`Emote`,`Duration`,`Sound`,`BroadcastTextId`,`TextRange`,`comment`)
VALUES
(93011,0,0,'You heard Lord Illidan. Let\'s find that Keystone.',12,0,100,0,0,55248,0,0,'Kayn - Mardum personal departure'),
(93011,1,0,'With it, we\'ll be able to invade any Legion world, even Argus.',12,0,100,0,0,55246,0,0,'Kayn - Mardum personal departure'),
(98292,0,0,'Kill them all!',12,0,100,0,0,55284,0,0,'Korvas - Mardum personal departure');
