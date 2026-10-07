-- Requires rebuilt conversation loader and world update2026_10_07_02.
-- Restore source3914/4204 without dropping the opaque high word or changing timing.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_packed_guard`, `_1kycore_packed_lines`, `_1kycore_packed_templates`;
CREATE TEMPORARY TABLE `_1kycore_packed_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_packed_guard` VALUES (1);
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding' AND DATA_TYPE='smallint' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
CREATE TEMPORARY TABLE `_1kycore_packed_lines` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_packed_lines` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) VALUES
(8926,0,0,0,0,0,0),
(8928,4095,0,0,0,100,0),
(8931,12480,0,1,0,0,0),
(9883,0,0,0,0,0,0),
(9570,8129,0,0,0,2078,0);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_packed_lines` n ON a.Id=n.Id WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags` AND a.`Padding` <=> n.`Padding`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_packed_templates` LIKE `conversation_template`;
INSERT INTO `_1kycore_packed_templates` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(3914,8926,42948,'conversation_campaign_nearest_actors',0),
(4204,9883,18792,'conversation_campaign_nearest_actors',0);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_packed_templates` n ON a.Id=n.Id WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM conversation_actors WHERE ConversationId IN (3914,4204) LIMIT 1;
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=110489);
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=116880);
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=118242);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM conversation_template t JOIN (SELECT 3914 AS ConversationId,8926 AS LineId UNION ALL SELECT 3914 AS ConversationId,8928 AS LineId UNION ALL SELECT 3914 AS ConversationId,8931 AS LineId UNION ALL SELECT 4204 AS ConversationId,9883 AS LineId UNION ALL SELECT 4204 AS ConversationId,9570 AS LineId) expected ON t.Id=expected.ConversationId LEFT JOIN conversation_line_template l ON l.Id=expected.LineId WHERE l.Id IS NULL LIMIT 1;
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`Padding`,n.`VerifiedBuild` FROM `_1kycore_packed_lines` n LEFT JOIN `conversation_line_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_packed_templates` n LEFT JOIN `conversation_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
DROP TEMPORARY TABLE `_1kycore_packed_guard`, `_1kycore_packed_lines`, `_1kycore_packed_templates`;
