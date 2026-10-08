-- Restore complete source conversation4269 before enabling its gunpowder object.
-- Source world SQL SHA256 0265cc795b6507f8918162293e7c905143cdb2ef227ee72179bb43bcf889f68c.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`,`_1kycore_conversation_line_template`,`_1kycore_conversation_actors`,`_1kycore_conversation_template`;
CREATE TEMPORARY TABLE `_1kycore_conversation_guard` (ok INT PRIMARY KEY);
INSERT INTO `_1kycore_conversation_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_conversation_actor_template` LIKE `conversation_actor_template`;
INSERT INTO `_1kycore_conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`) VALUES
(56913,117263,67721,0);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_actor_template` a JOIN `_1kycore_conversation_actor_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`CreatureId` <=> n.`CreatureId` AND a.`CreatureModelId` <=> n.`CreatureModelId`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_conversation_line_template` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) VALUES
(9723,0,133,0,0,0,0),
(9724,9320,133,0,0,0,0);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_conversation_line_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags` AND a.`Padding` <=> n.`Padding`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_conversation_actors` LIKE `conversation_actors`;
INSERT INTO `_1kycore_conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`) VALUES
(4269,56913,0,0,0);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_actors` a JOIN `_1kycore_conversation_actors` n ON a.`ConversationId`=n.`ConversationId` AND a.`Idx`=n.`Idx` WHERE NOT (a.`ConversationActorId` <=> n.`ConversationActorId` AND a.`ConversationActorGuid` <=> n.`ConversationActorGuid`) LIMIT 1;
CREATE TEMPORARY TABLE `_1kycore_conversation_template` LIKE `conversation_template`;
INSERT INTO `_1kycore_conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(4269,9723,22302,'',0);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_conversation_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM conversation_actors WHERE ConversationId=4269 AND Idx<>0 LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=117263);
-- A published template cannot be repaired as an interrupted dependency prefix.
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM conversation_template t WHERE t.Id=4269 AND
 (NOT EXISTS (SELECT 1 FROM conversation_actor_template WHERE Id=56913) OR
  NOT EXISTS (SELECT 1 FROM conversation_actors WHERE ConversationId=4269 AND Idx=0) OR
  (SELECT COUNT(*) FROM conversation_line_template WHERE Id IN(9723,9724))<>2) LIMIT 1;

-- Install conversation_actor_template; matching administrator provenance survives.
INSERT INTO `conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`) SELECT n.`Id`,n.`CreatureId`,n.`CreatureModelId`,n.`VerifiedBuild` FROM `_1kycore_conversation_actor_template` n LEFT JOIN `conversation_actor_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_line_template; matching administrator provenance survives.
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`Padding`,`VerifiedBuild`) SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`Padding`,n.`VerifiedBuild` FROM `_1kycore_conversation_line_template` n LEFT JOIN `conversation_line_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_actors; matching administrator provenance survives.
INSERT INTO `conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`) SELECT n.`ConversationId`,n.`ConversationActorId`,n.`ConversationActorGuid`,n.`Idx`,n.`VerifiedBuild` FROM `_1kycore_conversation_actors` n LEFT JOIN `conversation_actors` a ON a.`ConversationId`=n.`ConversationId` AND a.`Idx`=n.`Idx` WHERE a.`ConversationId` IS NULL;

-- Install conversation_template; matching administrator provenance survives.
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_conversation_template` n LEFT JOIN `conversation_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;
DROP TEMPORARY TABLE `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`,`_1kycore_conversation_line_template`,`_1kycore_conversation_actors`,`_1kycore_conversation_template`;
