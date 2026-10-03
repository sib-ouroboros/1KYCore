-- 1KYCore: restore two ordinary/shared chests with explicit source wildcard loot modes.
-- Original Legion source archive SHA256 cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Original core commit 22bfd97d0e0e30d215e408eb4da2b0419d8f00e7:
-- LootTemplate::Process and explicitly-chanced LootGroup::Roll accept mode 0 as wildcard.
-- Native uint16 bit mask uses 65535 to allow every nonzero mode; retain group/quantity/quest sign.
-- Only 267353 Data1 adapts to entry-based original SendLoot. No personal loot, global loot or spawns changed.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`, `_1kycore_chest_loot`, `_1kycore_chest_items`, `_1kycore_addon_baseline`;
CREATE TEMPORARY TABLE `_1kycore_model_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_model_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_model_baseline` LIKE gameobject_template;
INSERT INTO `_1kycore_model_baseline` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(267353,0,0,'Stabilizing Crystal','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0),
(251615,0,0,'Dying Tree','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0);
CREATE TEMPORARY TABLE `_1kycore_model_source` LIKE gameobject_template;
INSERT INTO `_1kycore_model_source` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(267353,3,28634,'Stabilizing Crystal','questinteract','Gather','',1,1691,267353,1,0,0,0,0,0,0,0,0,0,0,0,24982,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',24015),
(251615,3,34137,'Dying tree','questinteract','Wood felling','',0.6,2584,251615,0,1,0,0,0,0,0,0,0,0,0,0,116437,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',23171);

CREATE TEMPORARY TABLE `_1kycore_model_addons` LIKE gameobject_template_addon;
INSERT INTO `_1kycore_model_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(267353,0,0,0,0,0),
(251615,0,0,0,0,0);

CREATE TEMPORARY TABLE `_1kycore_chest_loot` LIKE gameobject_loot_template;
INSERT INTO `_1kycore_chest_loot` (`Entry`,`Item`,`Reference`,`Chance`,`QuestRequired`,`LootMode`,`GroupId`,`MinCount`,`MaxCount`) VALUES
(267353,143918,0,100,1,65535,0,1,1),
(251615,137609,0,100,0,65535,1,1,1);
CREATE TEMPORARY TABLE `_1kycore_chest_items` LIKE gameobject_questitem;
INSERT INTO `_1kycore_chest_items` (`GameObjectEntry`,`Idx`,`ItemId`,`VerifiedBuild`) VALUES
(267353,0,143918,0);

CREATE TEMPORARY TABLE `_1kycore_addon_baseline` LIKE gameobject_template_addon;


-- All checks run before any permanent write. Missing or customized rows reject.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM `_1kycore_model_baseline` b JOIN `_1kycore_model_source` n ON n.entry=b.entry
LEFT JOIN gameobject_template t ON t.entry=b.entry
WHERE t.entry IS NULL OR (NOT ((t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`)) AND NOT ((t.`entry` <=> n.`entry`) AND (t.`type` <=> n.`type`) AND (t.`displayId` <=> n.`displayId`) AND (BINARY t.`name` <=> BINARY n.`name`) AND (BINARY t.`IconName` <=> BINARY n.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY n.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY n.`unk1`) AND (t.`size` <=> n.`size`) AND (t.`Data0` <=> n.`Data0`) AND (t.`Data1` <=> n.`Data1`) AND (t.`Data2` <=> n.`Data2`) AND (t.`Data3` <=> n.`Data3`) AND (t.`Data4` <=> n.`Data4`) AND (t.`Data5` <=> n.`Data5`) AND (t.`Data6` <=> n.`Data6`) AND (t.`Data7` <=> n.`Data7`) AND (t.`Data8` <=> n.`Data8`) AND (t.`Data9` <=> n.`Data9`) AND (t.`Data10` <=> n.`Data10`) AND (t.`Data11` <=> n.`Data11`) AND (t.`Data12` <=> n.`Data12`) AND (t.`Data13` <=> n.`Data13`) AND (t.`Data14` <=> n.`Data14`) AND (t.`Data15` <=> n.`Data15`) AND (t.`Data16` <=> n.`Data16`) AND (t.`Data17` <=> n.`Data17`) AND (t.`Data18` <=> n.`Data18`) AND (t.`Data19` <=> n.`Data19`) AND (t.`Data20` <=> n.`Data20`) AND (t.`Data21` <=> n.`Data21`) AND (t.`Data22` <=> n.`Data22`) AND (t.`Data23` <=> n.`Data23`) AND (t.`Data24` <=> n.`Data24`) AND (t.`Data25` <=> n.`Data25`) AND (t.`Data26` <=> n.`Data26`) AND (t.`Data27` <=> n.`Data27`) AND (t.`Data28` <=> n.`Data28`) AND (t.`Data29` <=> n.`Data29`) AND (t.`Data30` <=> n.`Data30`) AND (t.`Data31` <=> n.`Data31`) AND (t.`Data32` <=> n.`Data32`) AND (t.`RequiredLevel` <=> n.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY n.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY n.`ScriptName`) AND (t.`VerifiedBuild` <=> n.`VerifiedBuild`))) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template_addon a JOIN `_1kycore_model_addons` expected ON expected.entry=a.entry
LEFT JOIN `_1kycore_addon_baseline` b ON b.entry=a.entry
JOIN gameobject_template t ON t.entry=a.entry
JOIN `_1kycore_model_baseline` bt ON bt.entry=t.entry
WHERE NOT ((a.`entry` <=> expected.`entry`) AND (a.`faction` <=> expected.`faction`) AND (a.`flags` <=> expected.`flags`) AND (a.`mingold` <=> expected.`mingold`) AND (a.`maxgold` <=> expected.`maxgold`) AND (a.`WorldEffectID` <=> expected.`WorldEffectID`)) AND
(b.entry IS NULL OR NOT ((a.`entry` <=> b.`entry`) AND (a.`faction` <=> b.`faction`) AND (a.`flags` <=> b.`flags`) AND (a.`mingold` <=> b.`mingold`) AND (a.`maxgold` <=> b.`maxgold`) AND (a.`WorldEffectID` <=> b.`WorldEffectID`)) OR t.type<>bt.type OR t.displayId<>bt.displayId) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_model_source` n ON n.entry=t.entry
LEFT JOIN gameobject_template_addon a ON a.entry=t.entry
WHERE t.type=n.type AND t.displayId=n.displayId AND a.entry IS NULL LIMIT 1;
-- Reject extra/custom quest-item or loot rows; retain compatible provenance markers.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_questitem q JOIN `_1kycore_model_source` n ON n.entry=q.GameObjectEntry
LEFT JOIN `_1kycore_chest_items` e ON e.GameObjectEntry=q.GameObjectEntry AND e.Idx=q.Idx
WHERE e.GameObjectEntry IS NULL OR NOT (q.ItemId <=> e.ItemId) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_loot_template l JOIN `_1kycore_model_source` n ON n.entry=l.Entry
LEFT JOIN `_1kycore_chest_loot` e ON e.Entry=l.Entry AND e.Item=l.Item
WHERE e.Entry IS NULL OR NOT (l.`Reference` <=> e.`Reference`) OR NOT (l.`Chance` <=> e.`Chance`) OR NOT (l.`QuestRequired` <=> e.`QuestRequired`) OR NOT (l.`LootMode` <=> e.`LootMode`) OR NOT (l.`GroupId` <=> e.`GroupId`) OR NOT (l.`MinCount` <=> e.`MinCount`) OR NOT (l.`MaxCount` <=> e.`MaxCount`) LIMIT 1;
-- Full template validation above admits only baseline or native rows. Native display IDs distinguish
-- existing type-3 placeholders from restored chests before requiring native dependencies.
-- A native chest without any required dependency is inconsistent; reject rather than patch it silently.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_model_source` n ON n.entry=t.entry
LEFT JOIN `_1kycore_chest_items` e ON e.GameObjectEntry=t.entry
LEFT JOIN gameobject_questitem q ON q.GameObjectEntry=e.GameObjectEntry AND q.Idx=e.Idx
JOIN `_1kycore_chest_loot` el ON el.Entry=t.entry
LEFT JOIN gameobject_loot_template l ON l.Entry=el.Entry AND l.Item=el.Item
WHERE t.type=n.type AND t.displayId=n.displayId AND ((e.GameObjectEntry IS NOT NULL AND q.GameObjectEntry IS NULL) OR l.Entry IS NULL) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_objectives WHERE `ID`=288552 AND `QuestID`=45764 AND `Type`=1 AND `ObjectID`=143918 AND `Amount`=3);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_template WHERE ID=45764);
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM conditions c JOIN `_1kycore_model_source` n ON n.entry=c.SourceGroup WHERE c.SourceTypeOrReferenceId=4 LIMIT 1;


-- Install missing source addons first; an addon-only interruption can retry.
INSERT INTO gameobject_template_addon (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`)
SELECT expected.`entry`,expected.`faction`,expected.`flags`,expected.`mingold`,expected.`maxgold`,expected.`WorldEffectID` FROM `_1kycore_model_addons` expected
LEFT JOIN gameobject_template_addon a ON a.entry=expected.entry WHERE a.entry IS NULL;

-- Upgrade only exact imported neutral addons while their template is still baseline.
UPDATE gameobject_template_addon a JOIN `_1kycore_addon_baseline` b ON b.entry=a.entry
JOIN `_1kycore_model_addons` n ON n.entry=a.entry
JOIN gameobject_template t ON t.entry=a.entry
JOIN `_1kycore_model_baseline` bt ON bt.entry=t.entry
SET a.`faction`=n.`faction`,a.`flags`=n.`flags`,a.`mingold`=n.`mingold`,a.`maxgold`=n.`maxgold`,a.`WorldEffectID`=n.`WorldEffectID`
WHERE ((a.`entry` <=> b.`entry`) AND (a.`faction` <=> b.`faction`) AND (a.`flags` <=> b.`flags`) AND (a.`mingold` <=> b.`mingold`) AND (a.`maxgold` <=> b.`maxgold`) AND (a.`WorldEffectID` <=> b.`WorldEffectID`)) AND (t.`entry` <=> bt.`entry` AND t.`type` <=> bt.`type` AND t.`displayId` <=> bt.`displayId` AND BINARY t.`name` <=> BINARY bt.`name` AND BINARY t.`IconName` <=> BINARY bt.`IconName` AND BINARY t.`castBarCaption` <=> BINARY bt.`castBarCaption` AND BINARY t.`unk1` <=> BINARY bt.`unk1` AND t.`size` <=> bt.`size` AND t.`Data0` <=> bt.`Data0` AND t.`Data1` <=> bt.`Data1` AND t.`Data2` <=> bt.`Data2` AND t.`Data3` <=> bt.`Data3` AND t.`Data4` <=> bt.`Data4` AND t.`Data5` <=> bt.`Data5` AND t.`Data6` <=> bt.`Data6` AND t.`Data7` <=> bt.`Data7` AND t.`Data8` <=> bt.`Data8` AND t.`Data9` <=> bt.`Data9` AND t.`Data10` <=> bt.`Data10` AND t.`Data11` <=> bt.`Data11` AND t.`Data12` <=> bt.`Data12` AND t.`Data13` <=> bt.`Data13` AND t.`Data14` <=> bt.`Data14` AND t.`Data15` <=> bt.`Data15` AND t.`Data16` <=> bt.`Data16` AND t.`Data17` <=> bt.`Data17` AND t.`Data18` <=> bt.`Data18` AND t.`Data19` <=> bt.`Data19` AND t.`Data20` <=> bt.`Data20` AND t.`Data21` <=> bt.`Data21` AND t.`Data22` <=> bt.`Data22` AND t.`Data23` <=> bt.`Data23` AND t.`Data24` <=> bt.`Data24` AND t.`Data25` <=> bt.`Data25` AND t.`Data26` <=> bt.`Data26` AND t.`Data27` <=> bt.`Data27` AND t.`Data28` <=> bt.`Data28` AND t.`Data29` <=> bt.`Data29` AND t.`Data30` <=> bt.`Data30` AND t.`Data31` <=> bt.`Data31` AND t.`Data32` <=> bt.`Data32` AND t.`RequiredLevel` <=> bt.`RequiredLevel` AND BINARY t.`AIName` <=> BINARY bt.`AIName` AND BINARY t.`ScriptName` <=> BINARY bt.`ScriptName` AND t.`VerifiedBuild` <=> bt.`VerifiedBuild`);

-- Install source quest-item hints and translated quest-only loot before enabling chests.
INSERT INTO gameobject_questitem (`GameObjectEntry`,`Idx`,`ItemId`,`VerifiedBuild`)
SELECT e.GameObjectEntry,e.Idx,e.ItemId,e.VerifiedBuild FROM `_1kycore_chest_items` e
LEFT JOIN gameobject_questitem q ON q.GameObjectEntry=e.GameObjectEntry AND q.Idx=e.Idx WHERE q.GameObjectEntry IS NULL;
INSERT INTO gameobject_loot_template (`Entry`,`Item`,`Reference`,`Chance`,`QuestRequired`,`LootMode`,`GroupId`,`MinCount`,`MaxCount`)
SELECT e.`Entry`,e.`Item`,e.`Reference`,e.`Chance`,e.`QuestRequired`,e.`LootMode`,e.`GroupId`,e.`MinCount`,e.`MaxCount` FROM `_1kycore_chest_loot` e
LEFT JOIN gameobject_loot_template l ON l.Entry=e.Entry AND l.Item=e.Item WHERE l.Entry IS NULL;

-- Rewrite only byte-compatible release placeholders; native rows stay intact.
UPDATE gameobject_template t JOIN `_1kycore_model_baseline` b ON b.entry=t.entry
JOIN `_1kycore_model_source` n ON n.entry=t.entry
SET t.`type`=n.`type`,t.`displayId`=n.`displayId`,t.`name`=n.`name`,t.`IconName`=n.`IconName`,t.`castBarCaption`=n.`castBarCaption`,t.`unk1`=n.`unk1`,t.`size`=n.`size`,t.`Data0`=n.`Data0`,t.`Data1`=n.`Data1`,t.`Data2`=n.`Data2`,t.`Data3`=n.`Data3`,t.`Data4`=n.`Data4`,t.`Data5`=n.`Data5`,t.`Data6`=n.`Data6`,t.`Data7`=n.`Data7`,t.`Data8`=n.`Data8`,t.`Data9`=n.`Data9`,t.`Data10`=n.`Data10`,t.`Data11`=n.`Data11`,t.`Data12`=n.`Data12`,t.`Data13`=n.`Data13`,t.`Data14`=n.`Data14`,t.`Data15`=n.`Data15`,t.`Data16`=n.`Data16`,t.`Data17`=n.`Data17`,t.`Data18`=n.`Data18`,t.`Data19`=n.`Data19`,t.`Data20`=n.`Data20`,t.`Data21`=n.`Data21`,t.`Data22`=n.`Data22`,t.`Data23`=n.`Data23`,t.`Data24`=n.`Data24`,t.`Data25`=n.`Data25`,t.`Data26`=n.`Data26`,t.`Data27`=n.`Data27`,t.`Data28`=n.`Data28`,t.`Data29`=n.`Data29`,t.`Data30`=n.`Data30`,t.`Data31`=n.`Data31`,t.`Data32`=n.`Data32`,t.`RequiredLevel`=n.`RequiredLevel`,t.`AIName`=n.`AIName`,t.`ScriptName`=n.`ScriptName`,t.`VerifiedBuild`=n.`VerifiedBuild`
WHERE (t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`);
DROP TEMPORARY TABLE `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`, `_1kycore_chest_loot`, `_1kycore_chest_items`, `_1kycore_addon_baseline`;
