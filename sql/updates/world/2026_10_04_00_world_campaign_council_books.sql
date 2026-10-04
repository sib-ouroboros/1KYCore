-- 1KYCore: restore Council Notice and Logbook of Urdan with exact terminal pages.
-- Source world SHA256 cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Native spell218330: effect90, credit109693, target22/7; no new spell script or conditions.
-- Forgotten Letter251697 remains deferred: separate conversation2851 SmartAI chain.
-- Preserve every existing spawn/phase and reject customized dependencies before writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`, `_1kycore_book_pages`;
CREATE TEMPORARY TABLE `_1kycore_model_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_model_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_model_baseline` LIKE gameobject_template;
INSERT INTO `_1kycore_model_baseline` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(251696,0,0,'Council Notice','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0),
(251698,0,0,'Logbook of Ur\'dan','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'','',0);
CREATE TEMPORARY TABLE `_1kycore_model_source` LIKE gameobject_template;
INSERT INTO `_1kycore_model_source` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`RequiredLevel`,`AIName`,`ScriptName`,`VerifiedBuild`) VALUES
(251696,10,15139,'Council Notice','questinteract','','',1,0,0,0,4,0,0,0,5313,0,1,218330,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,'','',21491),
(251698,10,25779,'Logbook of Urdan','questinteract','','',1,0,0,0,4,0,0,0,5315,0,1,218330,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,'','',21491);

CREATE TEMPORARY TABLE `_1kycore_model_addons` LIKE gameobject_template_addon;
INSERT INTO `_1kycore_model_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(251696,0,262144,0,0,0),
(251698,0,262144,0,0,0);

CREATE TEMPORARY TABLE `_1kycore_book_pages` LIKE page_text;
INSERT INTO `_1kycore_book_pages` (`ID`,`Text`,`NextPageID`,`PlayerConditionID`,`Flags`,`VerifiedBuild`) VALUES
(5313,'Gul\'dan has returned! A better Gul\'dan! \n\nHe is extending his hand out to all those that have fled or gone into hiding due to failures of the past. The Legion is here and now is our chance to prove we belong with the victors.\n\nGul\'dan plans a powerful ritual that will bring all opposition to their knees. I am gathering forces at Caer Darrow to retrieve something that he requires. If you would rejoin a stronger Shadow Council, join me there. Once we\'ve \"convinced\" the necromancers to aid us, we will move to another task.\n\nOur time has come, don\'t be left behind.\n\n- Jergosh',0,0,36,21491),
(5315,'Caer Darrow Assets:\n- 7 warlocks, middling ability\n- 9 warriors, well equipped\n- 4 months supplies\n\nUnknown how long this will take. Jergosh getting very angry.\n\nTol Barad Expedition Assets:\n- unknown number of forces\n- Nagaz, bringing Argus Wake?\n- possible Dark Strand presence, at least Athrikus\n- unsure how long they will wait for success here\n\nTol Barad Obstacles:\n- completely broken prison, inmates running around crazy\n- uncontrolled demons, beasts, criminals\n- exact location of Eye of Dalaran unknown, heavy scouting required',0,0,34,21491);

-- All checks run before any permanent write. Missing or customized rows reject.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM `_1kycore_model_baseline` b JOIN `_1kycore_model_source` n ON n.entry=b.entry
LEFT JOIN gameobject_template t ON t.entry=b.entry
WHERE t.entry IS NULL OR (NOT ((t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`)) AND NOT ((t.`entry` <=> n.`entry`) AND (t.`type` <=> n.`type`) AND (t.`displayId` <=> n.`displayId`) AND (BINARY t.`name` <=> BINARY n.`name`) AND (BINARY t.`IconName` <=> BINARY n.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY n.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY n.`unk1`) AND (t.`size` <=> n.`size`) AND (t.`Data0` <=> n.`Data0`) AND (t.`Data1` <=> n.`Data1`) AND (t.`Data2` <=> n.`Data2`) AND (t.`Data3` <=> n.`Data3`) AND (t.`Data4` <=> n.`Data4`) AND (t.`Data5` <=> n.`Data5`) AND (t.`Data6` <=> n.`Data6`) AND (t.`Data7` <=> n.`Data7`) AND (t.`Data8` <=> n.`Data8`) AND (t.`Data9` <=> n.`Data9`) AND (t.`Data10` <=> n.`Data10`) AND (t.`Data11` <=> n.`Data11`) AND (t.`Data12` <=> n.`Data12`) AND (t.`Data13` <=> n.`Data13`) AND (t.`Data14` <=> n.`Data14`) AND (t.`Data15` <=> n.`Data15`) AND (t.`Data16` <=> n.`Data16`) AND (t.`Data17` <=> n.`Data17`) AND (t.`Data18` <=> n.`Data18`) AND (t.`Data19` <=> n.`Data19`) AND (t.`Data20` <=> n.`Data20`) AND (t.`Data21` <=> n.`Data21`) AND (t.`Data22` <=> n.`Data22`) AND (t.`Data23` <=> n.`Data23`) AND (t.`Data24` <=> n.`Data24`) AND (t.`Data25` <=> n.`Data25`) AND (t.`Data26` <=> n.`Data26`) AND (t.`Data27` <=> n.`Data27`) AND (t.`Data28` <=> n.`Data28`) AND (t.`Data29` <=> n.`Data29`) AND (t.`Data30` <=> n.`Data30`) AND (t.`Data31` <=> n.`Data31`) AND (t.`Data32` <=> n.`Data32`) AND (t.`RequiredLevel` <=> n.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY n.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY n.`ScriptName`) AND (t.`VerifiedBuild` <=> n.`VerifiedBuild`))) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template_addon a JOIN `_1kycore_model_addons` expected ON expected.entry=a.entry
WHERE a.faction<>expected.faction OR a.flags<>expected.flags OR a.mingold<>expected.mingold
OR a.maxgold<>expected.maxgold OR a.WorldEffectID<>expected.WorldEffectID LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_model_source` n ON n.entry=t.entry
LEFT JOIN gameobject_template_addon a ON a.entry=t.entry
WHERE t.type=n.type AND a.entry IS NULL LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_questitem q JOIN `_1kycore_model_source` n ON n.entry=q.GameObjectEntry
WHERE q.ItemId<>0 LIMIT 1;

-- Source page payloads and the spell-credit quest are mandatory dependencies.
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM page_text p JOIN `_1kycore_book_pages` n ON n.ID=p.ID
WHERE NOT (BINARY p.Text <=> BINARY n.Text) OR NOT (p.NextPageID <=> n.NextPageID)
OR NOT (p.PlayerConditionID <=> n.PlayerConditionID) OR NOT (p.Flags <=> n.Flags)
OR NOT (p.VerifiedBuild <=> n.VerifiedBuild) LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM page_text_locale l JOIN `_1kycore_book_pages` n ON n.ID=l.ID
LEFT JOIN page_text p ON p.ID=l.ID WHERE p.ID IS NULL LIMIT 1;
INSERT INTO `_1kycore_model_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_model_source` n ON n.entry=t.entry
LEFT JOIN page_text p ON p.ID=n.Data7 WHERE t.type=n.type AND t.displayId=n.displayId AND p.ID IS NULL LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=109693);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_template WHERE ID=43100);
INSERT INTO `_1kycore_model_guard` SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM quest_objectives WHERE `ID`=285059 AND `QuestID`=43100 AND `Type`=0 AND `ObjectID`=109693 AND `Amount`=3);
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM smart_scripts WHERE source_type=1 AND entryorguid IN (251696,251698) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM conditions WHERE (SourceTypeOrReferenceId=22 AND SourceId=1 AND SourceEntry IN (251696,251698)) OR (SourceTypeOrReferenceId=13 AND SourceEntry=218330) LIMIT 1;
INSERT INTO `_1kycore_model_guard` SELECT 1 FROM spell_script_names WHERE spell_id IN (218330,-218330) LIMIT 1;

-- Restore missing terminal pages before addons and native templates.
INSERT INTO page_text (`ID`,`Text`,`NextPageID`,`PlayerConditionID`,`Flags`,`VerifiedBuild`)
SELECT n.`ID`,n.`Text`,n.`NextPageID`,n.`PlayerConditionID`,n.`Flags`,n.`VerifiedBuild`
FROM `_1kycore_book_pages` n LEFT JOIN page_text p ON p.ID=n.ID WHERE p.ID IS NULL;

-- Install missing source addons first; an addon-only interruption can retry.
INSERT INTO gameobject_template_addon (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`)
SELECT expected.`entry`,expected.`faction`,expected.`flags`,expected.`mingold`,expected.`maxgold`,expected.`WorldEffectID` FROM `_1kycore_model_addons` expected
LEFT JOIN gameobject_template_addon a ON a.entry=expected.entry WHERE a.entry IS NULL;

-- Rewrite only byte-compatible release placeholders; native rows stay intact.
UPDATE gameobject_template t JOIN `_1kycore_model_baseline` b ON b.entry=t.entry
JOIN `_1kycore_model_source` n ON n.entry=t.entry
SET t.`type`=n.`type`,t.`displayId`=n.`displayId`,t.`name`=n.`name`,t.`IconName`=n.`IconName`,t.`castBarCaption`=n.`castBarCaption`,t.`unk1`=n.`unk1`,t.`size`=n.`size`,t.`Data0`=n.`Data0`,t.`Data1`=n.`Data1`,t.`Data2`=n.`Data2`,t.`Data3`=n.`Data3`,t.`Data4`=n.`Data4`,t.`Data5`=n.`Data5`,t.`Data6`=n.`Data6`,t.`Data7`=n.`Data7`,t.`Data8`=n.`Data8`,t.`Data9`=n.`Data9`,t.`Data10`=n.`Data10`,t.`Data11`=n.`Data11`,t.`Data12`=n.`Data12`,t.`Data13`=n.`Data13`,t.`Data14`=n.`Data14`,t.`Data15`=n.`Data15`,t.`Data16`=n.`Data16`,t.`Data17`=n.`Data17`,t.`Data18`=n.`Data18`,t.`Data19`=n.`Data19`,t.`Data20`=n.`Data20`,t.`Data21`=n.`Data21`,t.`Data22`=n.`Data22`,t.`Data23`=n.`Data23`,t.`Data24`=n.`Data24`,t.`Data25`=n.`Data25`,t.`Data26`=n.`Data26`,t.`Data27`=n.`Data27`,t.`Data28`=n.`Data28`,t.`Data29`=n.`Data29`,t.`Data30`=n.`Data30`,t.`Data31`=n.`Data31`,t.`Data32`=n.`Data32`,t.`RequiredLevel`=n.`RequiredLevel`,t.`AIName`=n.`AIName`,t.`ScriptName`=n.`ScriptName`,t.`VerifiedBuild`=n.`VerifiedBuild`
WHERE (t.`entry` <=> b.`entry`) AND (t.`type` <=> b.`type`) AND (t.`displayId` <=> b.`displayId`) AND (BINARY t.`name` <=> BINARY b.`name`) AND (BINARY t.`IconName` <=> BINARY b.`IconName`) AND (BINARY t.`castBarCaption` <=> BINARY b.`castBarCaption`) AND (BINARY t.`unk1` <=> BINARY b.`unk1`) AND (t.`size` <=> b.`size`) AND (t.`Data0` <=> b.`Data0`) AND (t.`Data1` <=> b.`Data1`) AND (t.`Data2` <=> b.`Data2`) AND (t.`Data3` <=> b.`Data3`) AND (t.`Data4` <=> b.`Data4`) AND (t.`Data5` <=> b.`Data5`) AND (t.`Data6` <=> b.`Data6`) AND (t.`Data7` <=> b.`Data7`) AND (t.`Data8` <=> b.`Data8`) AND (t.`Data9` <=> b.`Data9`) AND (t.`Data10` <=> b.`Data10`) AND (t.`Data11` <=> b.`Data11`) AND (t.`Data12` <=> b.`Data12`) AND (t.`Data13` <=> b.`Data13`) AND (t.`Data14` <=> b.`Data14`) AND (t.`Data15` <=> b.`Data15`) AND (t.`Data16` <=> b.`Data16`) AND (t.`Data17` <=> b.`Data17`) AND (t.`Data18` <=> b.`Data18`) AND (t.`Data19` <=> b.`Data19`) AND (t.`Data20` <=> b.`Data20`) AND (t.`Data21` <=> b.`Data21`) AND (t.`Data22` <=> b.`Data22`) AND (t.`Data23` <=> b.`Data23`) AND (t.`Data24` <=> b.`Data24`) AND (t.`Data25` <=> b.`Data25`) AND (t.`Data26` <=> b.`Data26`) AND (t.`Data27` <=> b.`Data27`) AND (t.`Data28` <=> b.`Data28`) AND (t.`Data29` <=> b.`Data29`) AND (t.`Data30` <=> b.`Data30`) AND (t.`Data31` <=> b.`Data31`) AND (t.`Data32` <=> b.`Data32`) AND (t.`RequiredLevel` <=> b.`RequiredLevel`) AND (BINARY t.`AIName` <=> BINARY b.`AIName`) AND (BINARY t.`ScriptName` <=> BINARY b.`ScriptName`) AND (t.`VerifiedBuild` <=> b.`VerifiedBuild`);
DROP TEMPORARY TABLE `_1kycore_model_guard`, `_1kycore_model_baseline`, `_1kycore_model_source`, `_1kycore_model_addons`, `_1kycore_book_pages`;
