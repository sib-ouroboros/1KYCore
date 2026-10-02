-- 1KYCore: sixth conservative campaign object restoration.
-- Original templates: The-Legion-Preservation-Project/LegionCore-7.3.5
-- release LegionCore735.24101, LegionCore_world_735.26972_2024_10_23.sql.
-- Archive SHA256: cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Spawn coordinates/phases: pinned Sylvania a6145c22e9ad6ac69690d4a2f7794bae4e1caf95.
-- Five native DOOR templates without locks/conditions and one TEXT template.
-- Restore original page5121; retain its Italian source text without inventing a translation.
-- Door states, flags and auto-close timers are copied without changing collision policy.
-- Preserve existing templates/spawns. Reject foreign GUID ownership before world writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_campaign_pages`;
CREATE TEMPORARY TABLE `_1kycore_generic_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_generic_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_generic_templates` LIKE `gameobject_template`;
INSERT INTO `_1kycore_generic_templates` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`) VALUES
(240351,9,23142,'Фолиант древних королей','','','',1.5,5121,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21287),
(243490,0,26055,'Wall Fel','','','',0.65,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20994),
(246287,0,26055,'Block of Fel flames','questinteract','','',1.25,0,0,300000,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(246535,0,31091,'Sea Wall','','','',1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(247329,0,29161,'Cage of demon','','','',1.5,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(248466,0,24101,'Wall of Shadow','','','',1.5,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21154);
CREATE TEMPORARY TABLE `_1kycore_generic_addons` LIKE `gameobject_template_addon`;
INSERT INTO `_1kycore_generic_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(240351,0,0,0,0,0),
(243490,0,48,0,0,0),
(246287,114,0,0,0,0),
(246535,0,49,0,0,0),
(247329,114,0,0,0,0),
(248466,0,48,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_generic_spawns` LIKE `gameobject`;
INSERT INTO `_1kycore_generic_spawns` (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
(210302539,246535,1545,7334,8003,'12',0,6199,0,-1,-1311.31,6181.93,32.0951,5.88064,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210303623,240351,0,139,2270,'0',0,4691,0,-1,2504.78,-5484.54,51.7388,5.48084,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210304676,248466,1539,85,7978,'12',0,5739,0,-1,1855.28,2292.28,45.6447,2.6742,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210307843,246287,1522,7918,7918,'12',0,5444,0,-1,3087.72,1003.35,253.264,1.85923,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210307849,247329,1522,7918,7918,'12',0,5444,0,-1,2963.78,1119.99,223.269,1.15582,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210307860,247329,1522,7918,7918,'12',0,5444,0,-1,2959.25,1126.27,220.342,6.12028,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210307863,246287,1522,7918,7918,'12',0,5444,0,-1,3079.21,1060.82,274.984,1.04029,7200,0.0,0.0,0.0,1.0,255,0,0,'',0),
(210307870,246287,1522,7918,7918,'12',0,5444,0,-1,3089.05,931.521,257.357,1.5717,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307874,246287,1522,7918,7918,'12',0,5373,0,-1,3075.43,1064.28,240.511,5.54257,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307989,243490,1498,7637,7768,'12',0,6434,0,-1,1134.25,5079.54,59.1818,2.53077,7200,0.0,0.0,0.0,1.0,255,1,0,'',0);
CREATE TEMPORARY TABLE `_1kycore_campaign_pages` LIKE page_text;
INSERT INTO `_1kycore_campaign_pages` (`ID`,`Text`,`NextPageID`,`PlayerConditionID`,`Flags`,`VerifiedBuild`) VALUES (5121,'n questo tomo verrà trascritta la storia e il potere del tuo Artefatto man mano che aumenta il tuo livello di conoscenza.',0,0,7,21287);
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject g JOIN `_1kycore_generic_spawns` expected ON g.guid=expected.guid
WHERE g.id<>expected.id LIMIT 1;
-- Never overwrite/reinterpret a conflicting addon, even on an existing template.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_template_addon a JOIN `_1kycore_generic_addons` expected ON a.entry=expected.entry
WHERE a.faction<>expected.faction OR a.flags<>expected.flags OR a.mingold<>expected.mingold
OR a.maxgold<>expected.maxgold OR a.WorldEffectID<>expected.WorldEffectID LIMIT 1;
-- An existing template without an addon is custom data, not an interrupted import:
-- this migration writes addons BEFORE templates. Reject instead of changing its flags.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_generic_templates` expected ON t.entry=expected.entry
LEFT JOIN gameobject_template_addon a ON a.entry=t.entry WHERE a.entry IS NULL LIMIT 1;
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_questitem qi JOIN `_1kycore_generic_templates` expected ON qi.GameObjectEntry=expected.entry
WHERE qi.ItemId<>0 LIMIT 1;
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_generic_templates` expected ON t.entry=expected.entry
WHERE t.type<>expected.type OR t.AIName<>'' OR t.ScriptName<>'' OR t.Data0<>expected.Data0 OR t.Data1<>expected.Data1 OR t.Data2<>expected.Data2 OR t.Data3<>expected.Data3 OR t.Data4<>expected.Data4 OR t.Data5<>expected.Data5 OR t.Data6<>expected.Data6 OR t.Data7<>expected.Data7 OR t.Data8<>expected.Data8 OR t.Data9<>expected.Data9 OR t.Data10<>expected.Data10 OR t.Data11<>expected.Data11 OR t.Data12<>expected.Data12 OR t.Data13<>expected.Data13 OR t.Data14<>expected.Data14 OR t.Data15<>expected.Data15 OR t.Data16<>expected.Data16 OR t.Data17<>expected.Data17 OR t.Data18<>expected.Data18 OR t.Data19<>expected.Data19 OR t.Data20<>expected.Data20 OR t.Data21<>expected.Data21 OR t.Data22<>expected.Data22 OR t.Data23<>expected.Data23 OR t.Data24<>expected.Data24 OR t.Data25<>expected.Data25 OR t.Data26<>expected.Data26 OR t.Data27<>expected.Data27 OR t.Data28<>expected.Data28 OR t.Data29<>expected.Data29 OR t.Data30<>expected.Data30 OR t.Data31<>expected.Data31 OR t.Data32<>expected.Data32 LIMIT 1;

INSERT INTO `_1kycore_generic_guard` SELECT 1 FROM page_text p JOIN `_1kycore_campaign_pages` expected ON p.ID=expected.ID WHERE NOT (BINARY p.`Text` <=> BINARY expected.`Text`) OR NOT (p.`NextPageID` <=> expected.`NextPageID`) OR NOT (p.`PlayerConditionID` <=> expected.`PlayerConditionID`) OR NOT (p.`Flags` <=> expected.`Flags`) OR NOT (p.`VerifiedBuild` <=> expected.`VerifiedBuild`) LIMIT 1;

-- Do not silently activate an unrelated orphan translation.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM page_text_locale l JOIN `_1kycore_campaign_pages` expected ON l.ID=expected.ID
LEFT JOIN page_text p ON p.ID=l.ID WHERE p.ID IS NULL LIMIT 1;

-- Restore the complete terminal page before its template. Existing matching pages survive.
INSERT INTO page_text (`ID`,`Text`,`NextPageID`,`PlayerConditionID`,`Flags`,`VerifiedBuild`)
SELECT expected.`ID`,expected.`Text`,expected.`NextPageID`,expected.`PlayerConditionID`,expected.`Flags`,expected.`VerifiedBuild` FROM `_1kycore_campaign_pages` expected
LEFT JOIN page_text p ON p.ID=expected.ID WHERE p.ID IS NULL;

-- Restore exact source addons before templates, so an interrupted import can retry.
-- All ownership/behavior/dependency guards above run BEFORE any permanent write.
INSERT INTO gameobject_template_addon (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`)
SELECT expected.`entry`,expected.`faction`,expected.`flags`,expected.`mingold`,expected.`maxgold`,expected.`WorldEffectID`
FROM `_1kycore_generic_addons` expected LEFT JOIN gameobject_template_addon a ON a.entry=expected.entry
WHERE a.entry IS NULL;

-- Add only absent templates; retain every pre-existing template unchanged.
INSERT INTO gameobject_template (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`)
SELECT expected.`entry`,expected.`type`,expected.`displayId`,expected.`name`,expected.`IconName`,expected.`castBarCaption`,expected.`unk1`,expected.`size`,expected.`Data0`,expected.`Data1`,expected.`Data2`,expected.`Data3`,expected.`Data4`,expected.`Data5`,expected.`Data6`,expected.`Data7`,expected.`Data8`,expected.`Data9`,expected.`Data10`,expected.`Data11`,expected.`Data12`,expected.`Data13`,expected.`Data14`,expected.`Data15`,expected.`Data16`,expected.`Data17`,expected.`Data18`,expected.`Data19`,expected.`Data20`,expected.`Data21`,expected.`Data22`,expected.`Data23`,expected.`Data24`,expected.`Data25`,expected.`Data26`,expected.`Data27`,expected.`Data28`,expected.`Data29`,expected.`Data30`,expected.`Data31`,expected.`Data32`,expected.`VerifiedBuild`
FROM `_1kycore_generic_templates` expected LEFT JOIN gameobject_template t ON t.entry=expected.entry
WHERE t.entry IS NULL;

-- Restore exact imported spawns, leaving existing coordinates/phases untouched.
INSERT INTO gameobject (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`)
SELECT expected.`guid`,expected.`id`,expected.`map`,expected.`zoneId`,expected.`areaId`,expected.`spawnDifficulties`,expected.`phaseUseFlags`,expected.`PhaseId`,expected.`PhaseGroup`,expected.`terrainSwapMap`,expected.`position_x`,expected.`position_y`,expected.`position_z`,expected.`orientation`,expected.`spawntimesecs`,expected.`rotation0`,expected.`rotation1`,expected.`rotation2`,expected.`rotation3`,expected.`animprogress`,expected.`state`,expected.`isActive`,expected.`ScriptName`,expected.`VerifiedBuild`
FROM `_1kycore_generic_spawns` expected LEFT JOIN gameobject g ON g.guid=expected.guid
WHERE g.guid IS NULL;
DROP TEMPORARY TABLE `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_campaign_pages`;
