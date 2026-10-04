-- Preserve original creator-relative nearest-creature actors, not unused source GUIDs.
-- Requires rebuilt World script conversation_campaign_nearest_actors.
-- Source core22bfd97d0e0e30d215e408eb4da2b0419d8f00e7; no NPC AI/spawns modified.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_nearest_guard`, `_1kycore_nearest_lines`, `_1kycore_nearest_templates`;
CREATE TEMPORARY TABLE `_1kycore_nearest_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_nearest_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_nearest_lines` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_nearest_lines` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`) VALUES
(3875,0,0,0,0,0),
(3882,0,0,0,0,0),
(3893,0,0,0,0,0),
(4261,0,0,0,0,0),
(4268,0,0,0,0,0),
(4659,0,0,0,0,0),
(4853,0,0,0,0,0),
(5051,0,102,0,0,0),
(6177,0,0,0,0,0),
(6178,0,0,0,0,0),
(6179,0,0,0,0,0),
(6180,0,0,0,0,0),
(6181,0,0,0,0,0),
(6182,0,0,0,0,0),
(6183,0,0,0,0,0),
(6184,0,0,0,0,0),
(6721,0,0,0,0,0),
(7987,0,138,0,0,0),
(7990,0,0,0,0,0),
(8056,0,0,0,0,0),
(8057,1958,0,1,0,0),
(8207,0,0,0,0,0),
(8394,0,0,0,0,0),
(8395,0,0,0,0,0),
(8438,0,0,0,0,0),
(8439,0,0,0,0,0),
(8440,0,0,0,0,0),
(8460,0,0,0,0,0),
(8451,0,0,0,0,0),
(8449,0,0,0,0,0),
(8458,0,0,0,0,0),
(8459,0,0,0,0,0),
(8450,0,0,0,0,0),
(9423,0,0,0,0,0),
(9424,4430,0,1,0,0),
(9425,15653,0,0,0,0),
(9761,19006,0,1,0,0),
(10249,0,0,0,0,0),
(10250,3008,0,0,0,0),
(10259,0,0,0,0,0);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_nearest_lines` n ON a.Id=n.Id WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_nearest_templates` LIKE `conversation_template`;
INSERT INTO `_1kycore_nearest_templates` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(1821,3875,12750,'conversation_campaign_nearest_actors',0),
(1823,3882,9600,'conversation_campaign_nearest_actors',0),
(1832,3893,8500,'conversation_campaign_nearest_actors',0),
(2017,4261,8263,'conversation_campaign_nearest_actors',0),
(2023,4268,11892,'conversation_campaign_nearest_actors',0),
(2211,4659,13420,'conversation_campaign_nearest_actors',0),
(2300,4853,11650,'conversation_campaign_nearest_actors',0),
(2381,5051,7250,'conversation_campaign_nearest_actors',0),
(2937,6177,11009,'conversation_campaign_nearest_actors',0),
(2938,6178,13016,'conversation_campaign_nearest_actors',0),
(2939,6179,10804,'conversation_campaign_nearest_actors',0),
(2940,6180,10813,'conversation_campaign_nearest_actors',0),
(2941,6181,10306,'conversation_campaign_nearest_actors',0),
(2942,6182,12038,'conversation_campaign_nearest_actors',0),
(2943,6183,10723,'conversation_campaign_nearest_actors',0),
(2944,6184,12734,'conversation_campaign_nearest_actors',0),
(3187,6721,11466,'conversation_campaign_nearest_actors',0),
(3572,7987,7500,'conversation_campaign_nearest_actors',0),
(3575,7990,8400,'conversation_campaign_nearest_actors',0),
(3597,8056,8916,'conversation_campaign_nearest_actors',0),
(3642,8207,10654,'conversation_campaign_nearest_actors',0),
(3771,8394,8074,'conversation_campaign_nearest_actors',0),
(3772,8395,8469,'conversation_campaign_nearest_actors',0),
(3786,8438,8337,'conversation_campaign_nearest_actors',0),
(3787,8439,8965,'conversation_campaign_nearest_actors',0),
(3788,8440,10092,'conversation_campaign_nearest_actors',0),
(3791,8460,9652,'conversation_campaign_nearest_actors',0),
(3792,8451,8866,'conversation_campaign_nearest_actors',0),
(3793,8449,11970,'conversation_campaign_nearest_actors',0),
(3794,8458,8847,'conversation_campaign_nearest_actors',0),
(3795,8459,12677,'conversation_campaign_nearest_actors',0),
(3796,8450,9210,'conversation_campaign_nearest_actors',0),
(4110,9423,59246,'conversation_campaign_nearest_actors',0),
(4593,10249,19023,'conversation_campaign_nearest_actors',0),
(4597,10259,9693,'conversation_campaign_nearest_actors',0);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_nearest_templates` n ON a.Id=n.Id WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_nearest_guard` SELECT 1 FROM conversation_actors a JOIN `_1kycore_nearest_templates` t ON a.ConversationId=t.Id LIMIT 1;
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=42465);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=93453);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=93555);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=94138);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=98008);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=98013);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=98102);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=99997);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=102594);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=103778);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=103832);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=104329);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=105333);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106001);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106091);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106093);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106517);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106518);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106519);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106521);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106524);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106649);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=107025);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=107806);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=107979);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=108975);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=109102);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=112959);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=113299);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=113419);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=113481);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=115883);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=116414);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=116448);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=116880);
INSERT INTO `_1kycore_nearest_guard` SELECT 1 FROM conversation_template t JOIN (SELECT 1821 AS ConversationId,3875 AS LineId
UNION ALL
SELECT 1823 AS ConversationId,3882 AS LineId
UNION ALL
SELECT 1832 AS ConversationId,3893 AS LineId
UNION ALL
SELECT 2017 AS ConversationId,4261 AS LineId
UNION ALL
SELECT 2023 AS ConversationId,4268 AS LineId
UNION ALL
SELECT 2211 AS ConversationId,4659 AS LineId
UNION ALL
SELECT 2300 AS ConversationId,4853 AS LineId
UNION ALL
SELECT 2381 AS ConversationId,5051 AS LineId
UNION ALL
SELECT 2937 AS ConversationId,6177 AS LineId
UNION ALL
SELECT 2938 AS ConversationId,6178 AS LineId
UNION ALL
SELECT 2939 AS ConversationId,6179 AS LineId
UNION ALL
SELECT 2940 AS ConversationId,6180 AS LineId
UNION ALL
SELECT 2941 AS ConversationId,6181 AS LineId
UNION ALL
SELECT 2942 AS ConversationId,6182 AS LineId
UNION ALL
SELECT 2943 AS ConversationId,6183 AS LineId
UNION ALL
SELECT 2944 AS ConversationId,6184 AS LineId
UNION ALL
SELECT 3187 AS ConversationId,6721 AS LineId
UNION ALL
SELECT 3572 AS ConversationId,7987 AS LineId
UNION ALL
SELECT 3575 AS ConversationId,7990 AS LineId
UNION ALL
SELECT 3597 AS ConversationId,8056 AS LineId
UNION ALL
SELECT 3597 AS ConversationId,8057 AS LineId
UNION ALL
SELECT 3642 AS ConversationId,8207 AS LineId
UNION ALL
SELECT 3771 AS ConversationId,8394 AS LineId
UNION ALL
SELECT 3772 AS ConversationId,8395 AS LineId
UNION ALL
SELECT 3786 AS ConversationId,8438 AS LineId
UNION ALL
SELECT 3787 AS ConversationId,8439 AS LineId
UNION ALL
SELECT 3788 AS ConversationId,8440 AS LineId
UNION ALL
SELECT 3791 AS ConversationId,8460 AS LineId
UNION ALL
SELECT 3792 AS ConversationId,8451 AS LineId
UNION ALL
SELECT 3793 AS ConversationId,8449 AS LineId
UNION ALL
SELECT 3794 AS ConversationId,8458 AS LineId
UNION ALL
SELECT 3795 AS ConversationId,8459 AS LineId
UNION ALL
SELECT 3796 AS ConversationId,8450 AS LineId
UNION ALL
SELECT 4110 AS ConversationId,9423 AS LineId
UNION ALL
SELECT 4110 AS ConversationId,9424 AS LineId
UNION ALL
SELECT 4110 AS ConversationId,9425 AS LineId
UNION ALL
SELECT 4110 AS ConversationId,9761 AS LineId
UNION ALL
SELECT 4593 AS ConversationId,10249 AS LineId
UNION ALL
SELECT 4593 AS ConversationId,10250 AS LineId
UNION ALL
SELECT 4597 AS ConversationId,10259 AS LineId) expected ON t.Id=expected.ConversationId LEFT JOIN conversation_line_template l ON l.Id=expected.LineId WHERE l.Id IS NULL LIMIT 1;
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`) SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`VerifiedBuild` FROM `_1kycore_nearest_lines` n LEFT JOIN `conversation_line_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_nearest_templates` n LEFT JOIN `conversation_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
DROP TEMPORARY TABLE `_1kycore_nearest_guard`, `_1kycore_nearest_lines`, `_1kycore_nearest_templates`;
