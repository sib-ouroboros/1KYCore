-- 1KYCore: restore thirteen source conversations with one terminal client line.
-- Exact source actor/line packet fields and source LastLineEndTime are retained.
-- Source SQL SHA256 0265cc795b6507f8918162293e7c905143cdb2ef227ee72179bb43bcf889f68c.
-- No NPC scripts, quests, spawns, actor GUIDs or native duration behavior changed.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`, `_1kycore_conversation_line_template`, `_1kycore_conversation_actors`, `_1kycore_conversation_template`;
CREATE TEMPORARY TABLE `_1kycore_conversation_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_conversation_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_conversation_actor_template` LIKE `conversation_actor_template`;
INSERT INTO `_1kycore_conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`) VALUES
(48432,99456,64011,0),
(52359,105112,38227,0),
(52939,106693,69686,0),
(54543,110749,62788,0),
(54324,107987,67773,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_line_template` LIKE `conversation_line_template`;
INSERT INTO `_1kycore_conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`) VALUES
(1768,0,270,0,0,0),
(1769,0,270,0,0,0),
(1770,0,270,0,0,0),
(1771,0,270,0,0,0),
(3801,0,807,0,0,0),
(4538,0,800,0,0,0),
(6485,0,129,0,0,0),
(6486,0,129,0,0,0),
(6487,0,129,0,0,0),
(6488,0,129,0,0,0),
(6489,0,129,0,0,0),
(6490,0,129,0,0,0),
(6675,0,977,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_actors` LIKE `conversation_actors`;
INSERT INTO `_1kycore_conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`) VALUES
(740,48432,0,0,0),
(741,48432,0,0,0),
(742,48432,0,0,0),
(743,48432,0,0,0),
(1785,52359,0,0,0),
(2138,52939,0,0,0),
(3047,54543,0,0,0),
(3048,54543,0,0,0),
(3049,54543,0,0,0),
(3050,54543,0,0,0),
(3051,54543,0,0,0),
(3052,54543,0,0,0),
(3159,54324,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_conversation_template` LIKE `conversation_template`;
INSERT INTO `_1kycore_conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`) VALUES
(740,1768,14700,'',0),
(741,1769,15250,'',0),
(742,1770,15900,'',0),
(743,1771,15050,'',0),
(1785,3801,14039,'',0),
(2138,4538,8800,'',0),
(3047,6485,19685,'',0),
(3048,6486,17792,'',0),
(3049,6487,15600,'',0),
(3050,6488,20013,'',0),
(3051,6489,20090,'',0),
(3052,6490,17573,'',0),
(3159,6675,14637,'',0);
-- Validate all dependencies and ownership before any permanent write.
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_actor_template` a JOIN `_1kycore_conversation_actor_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`CreatureId` <=> n.`CreatureId` AND a.`CreatureModelId` <=> n.`CreatureModelId`) LIMIT 1;
INSERT INTO `_1kycore_conversation_guard` SELECT 1 FROM `conversation_line_template` a JOIN `_1kycore_conversation_line_template` n ON a.`Id`=n.`Id` WHERE NOT (a.`StartTime` <=> n.`StartTime` AND a.`UiCameraID` <=> n.`UiCameraID` AND a.`ActorIdx` <=> n.`ActorIdx` AND a.`Flags` <=> n.`Flags`) LIMIT 1;
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
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=99456);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=105112);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=106693);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=107987);
INSERT INTO `_1kycore_conversation_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=110749);

-- Install conversation_actor_template; matching administrator provenance survives.
INSERT INTO `conversation_actor_template` (`Id`,`CreatureId`,`CreatureModelId`,`VerifiedBuild`)
SELECT n.`Id`,n.`CreatureId`,n.`CreatureModelId`,n.`VerifiedBuild` FROM `_1kycore_conversation_actor_template` n LEFT JOIN `conversation_actor_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_line_template; matching administrator provenance survives.
INSERT INTO `conversation_line_template` (`Id`,`StartTime`,`UiCameraID`,`ActorIdx`,`Flags`,`VerifiedBuild`)
SELECT n.`Id`,n.`StartTime`,n.`UiCameraID`,n.`ActorIdx`,n.`Flags`,n.`VerifiedBuild` FROM `_1kycore_conversation_line_template` n LEFT JOIN `conversation_line_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;

-- Install conversation_actors; matching administrator provenance survives.
INSERT INTO `conversation_actors` (`ConversationId`,`ConversationActorId`,`ConversationActorGuid`,`Idx`,`VerifiedBuild`)
SELECT n.`ConversationId`,n.`ConversationActorId`,n.`ConversationActorGuid`,n.`Idx`,n.`VerifiedBuild` FROM `_1kycore_conversation_actors` n LEFT JOIN `conversation_actors` a ON a.`ConversationId`=n.`ConversationId` AND a.`Idx`=n.`Idx` WHERE a.`ConversationId` IS NULL;

-- Install conversation_template; matching administrator provenance survives.
INSERT INTO `conversation_template` (`Id`,`FirstLineId`,`LastLineEndTime`,`ScriptName`,`VerifiedBuild`)
SELECT n.`Id`,n.`FirstLineId`,n.`LastLineEndTime`,n.`ScriptName`,n.`VerifiedBuild` FROM `_1kycore_conversation_template` n LEFT JOIN `conversation_template` a ON a.`Id`=n.`Id` WHERE a.`Id` IS NULL;
DROP TEMPORARY TABLE `_1kycore_conversation_guard`, `_1kycore_conversation_actor_template`,`_1kycore_conversation_line_template`,`_1kycore_conversation_actors`,`_1kycore_conversation_template`;
