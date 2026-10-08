-- Requires rebuilt conversation loader and world update2026_10_07_02.
-- Restore source1841/2778 without dropping the opaque high word or changing timing.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_packed_guard`, `_1kycore_packed_lines`, `_1kycore_packed_templates`;
CREATE TEMPORARY TABLE `_1kycore_packed_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_packed_guard` VALUES (1);
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding' AND DATA_TYPE='smallint' AND COLUMN_TYPE LIKE '%unsigned' AND IS_NULLABLE='NO' AND (COLUMN_DEFAULT <=> '0') AND EXTRA='');
CREATE TEMPORARY TABLE `_1kycore_packed_lines` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_packed_lines` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) VALUES
(3906,0,0,0,0,0,0),
(3907,6950,0,0,0,8224,0),
(5781,0,0,0,0,0,0),
(5782,5810,0,0,0,8252,0);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_packed_lines` n ON a.Id=n.Id WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags` AND a.`Padding` <=> n.`Padding`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_packed_templates` LIKE `conversation_template`;
INSERT INTO `_1kycore_packed_templates` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(1841,3906,8450,'conversation_campaign_nearest_actors',0),
(2778,5781,10276,'conversation_campaign_nearest_actors',0);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_packed_templates` n ON a.Id=n.Id WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM conversation_actors WHERE ConversationId IN (1841,2778) LIMIT 1;
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=105464);
INSERT INTO `_1kycore_packed_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=109000);
INSERT INTO `_1kycore_packed_guard` SELECT 1 FROM conversation_template t JOIN (SELECT 1841 AS ConversationId,3906 AS LineId UNION ALL SELECT 1841 AS ConversationId,3907 AS LineId UNION ALL SELECT 2778 AS ConversationId,5781 AS LineId UNION ALL SELECT 2778 AS ConversationId,5782 AS LineId) expected ON t.Id=expected.ConversationId LEFT JOIN conversation_line_template l ON l.Id=expected.LineId WHERE l.Id IS NULL LIMIT 1;
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`Padding`,n.`VerifiedBuild` FROM `_1kycore_packed_lines` n LEFT JOIN `conversation_line_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_packed_templates` n LEFT JOIN `conversation_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
DROP TEMPORARY TABLE `_1kycore_packed_guard`, `_1kycore_packed_lines`, `_1kycore_packed_templates`;
