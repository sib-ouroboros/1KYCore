-- 1KYCore: restore four source conversations with one terminal client line.
-- Exact source actor/line packet fields and source LastLineEndTime are retained.
-- Source SQL SHA256 0265cc795b6507f8918162293e7c905143cdb2ef227ee72179bb43bcf889f68c.
-- No NPC scripts, quests, spawns, actor GUIDs or native duration behavior changed.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`, `_1kycore_conversation_line_template`, `_1kycore_conversation_actors`, `_1kycore_conversation_template`;
CREATE TEMPORARY TABLE `_1kycore_conversation_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_conversation_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_conversation_actor_template` LIKE `conversation_actor_template`;
INSERT INTO `_1kycore_conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`) VALUES
(49875,98771,65975,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_line_template` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`,`Padding`) VALUES
(1521,0,86,0,0,0,0),
(1527,0,86,0,0,0,0),
(1528,0,86,0,0,0,0),
(1529,0,86,0,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_actors` LIKE `conversation_actors`;
INSERT INTO `_1kycore_conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`) VALUES
(587,49875,0,0,0),
(591,49875,0,0,0),
(592,49875,0,0,0),
(593,49875,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_template` LIKE `conversation_template`;
INSERT INTO `_1kycore_conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(587,1521,11050,'',0),
(591,1527,7550,'',0),
(592,1528,6950,'',0),
(593,1529,10450,'',0);
-- Validate all dependencies and ownership before any permanent write.
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_actor_template` a JOIN `_1kycore_conversation_actor_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`CreatureId` <=> n.`CreatureId` AND a.`CreatureModelId` <=> n.`CreatureModelId`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_conversation_line_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags` AND a.`Padding` <=> n.`Padding`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_actors` a JOIN `_1kycore_conversation_actors` n ON a.`ConversationId`=n.`ConversationId` AND a.`Idx`=n.`Idx` WHERE NOT (a.`ConversationActorId` <=> n.`ConversationActorId` AND a.`ConversationActorGuid` <=> n.`ConversationActorGuid`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_template` a JOIN `_1kycore_conversation_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`FirstLineId` <=> n.`FirstLineId` AND a.`LastLineEndTime` <=> n.`LastLineEndTime` AND BINARY a.`ScriptName` <=> BINARY n.`ScriptName`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard`
SELECT 1 FROM conversation_actors a JOIN `_1kycore_conversation_template` n ON n.Id=a.ConversationId
LEFT JOIN `_1kycore_conversation_actors` expected ON expected.ConversationId=a.ConversationId AND expected.Idx=a.Idx
WHERE expected.ConversationId IS NULL LIMIT 1;
-- A published template must have a complete chain; it cannot be an interrupted prefix.
INSERT INTO `_1kycore_conversation_guard`
SELECT 1 FROM conversation_template t JOIN `_1kycore_conversation_template` n ON n.Id=t.Id
LEFT JOIN conversation_line_template l ON l.Id=n.FirstLineId
LEFT JOIN conversation_actors b ON b.ConversationId=t.Id AND b.Idx=0
LEFT JOIN conversation_actor_template a ON a.Id=b.ConversationActorId
WHERE l.Id IS NULL OR b.ConversationId IS NULL OR a.Id IS NULL LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=98771);

-- Install conversation_actor_template; matching administrator provenance survives.
INSERT INTO `conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`)
SELECT n.`Id`,n.`CreatureId`,n.`CreatureModelId`,n.`VerifiedBuild` FROM `_1kycore_conversation_actor_template` n LEFT JOIN `conversation_actor_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_line_template; matching administrator provenance survives.
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`,`Padding`)
SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`VerifiedBuild`,n.`Padding` FROM `_1kycore_conversation_line_template` n LEFT JOIN `conversation_line_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_actors; matching administrator provenance survives.
INSERT INTO `conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`)
SELECT n.`ConversationId`,n.`ConversationActorId`,n.`ConversationActorGuid`,n.`Idx`,n.`VerifiedBuild` FROM `_1kycore_conversation_actors` n LEFT JOIN `conversation_actors` a ON a.`ConversationId`=n.`ConversationId` AND a.`Idx`=n.`Idx` WHERE a.`ConversationId` IS NULL;

-- Install conversation_template; matching administrator provenance survives.
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`)
SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_conversation_template` n LEFT JOIN `conversation_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;
DROP TEMPORARY TABLE `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`,`_1kycore_conversation_line_template`,`_1kycore_conversation_actors`,`_1kycore_conversation_template`;
