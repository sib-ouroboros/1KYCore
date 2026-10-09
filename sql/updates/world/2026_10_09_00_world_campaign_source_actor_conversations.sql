-- Restore4304 and4576 with rebuilt conversation_campaign_source_actors.
-- Source actor-template branch only; never merge ignored world player sentinels.
-- Global actor-template51642 must remain unchanged; C++ assigns exact local payload.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_source_actor_guard`, `_1kycore_source_lines`, `_1kycore_source_conversations`;
CREATE TEMPORARY TABLE `_1kycore_source_actor_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_source_actor_guard` VALUES(1);
-- Exact opaque high-word schema is mandatory before importing any lines.
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding' AND DATA_TYPE='smallint' AND COLUMN_TYPE LIKE '%unsigned%' AND IS_NULLABLE='NO' AND COLUMN_DEFAULT='0');
CREATE TEMPORARY TABLE `_1kycore_source_lines` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_source_lines` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) VALUES
(9822,0,0,0,0,0,0),
(10101,4000,593,1,0,0,0),
(9796,17213,98,2,0,0,0),
(10223,0,99,0,0,0,0),
(10224,10549,99,0,0,8214,0),
(10225,20645,99,0,0,0,0);
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_source_lines` n ON n.Id=a.Id WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags` AND a.`Padding` <=> n.`Padding`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_source_conversations` LIKE `conversation_template`;
INSERT INTO `_1kycore_source_conversations` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(4304,9822,54554,'conversation_campaign_source_actors',0),
(4576,10223,39764,'conversation_campaign_source_actors',0);
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_source_conversations` n ON n.Id=a.Id WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 FROM conversation_actors WHERE ConversationId IN(4304,4576) LIMIT 1;
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM creature_template WHERE entry=117443);
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM creature_template WHERE entry=118793);
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM creature_template WHERE entry=118975);
-- A published template with lost line dependencies is not an interrupted prefix.
INSERT INTO `_1kycore_source_actor_guard` SELECT 1 FROM conversation_template WHERE (Id=4304 AND (SELECT COUNT(*) FROM conversation_line_template WHERE Id IN(9822,10101,9796))<>3) OR (Id=4576 AND (SELECT COUNT(*) FROM conversation_line_template WHERE Id IN(10223,10224,10225))<>3) LIMIT 1;
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`Padding`,n.`VerifiedBuild` FROM `_1kycore_source_lines` n LEFT JOIN `conversation_line_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_source_conversations` n LEFT JOIN `conversation_template` a ON a.Id=n.Id WHERE a.Id IS NULL;
DROP TEMPORARY TABLE `_1kycore_source_actor_guard`, `_1kycore_source_lines`, `_1kycore_source_conversations`;
