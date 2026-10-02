-- 1KYCore: client-validated campaign object restoration.
-- Original templates: The-Legion-Preservation-Project/LegionCore-7.3.5
-- release LegionCore735.24101, LegionCore_world_735.26972_2024_10_23.sql.
-- Archive SHA256: cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Spawn coordinates/phases: pinned Sylvania a6145c22e9ad6ac69690d4a2f7794bae4e1caf95.
-- Five DOOR, two SPELL_FOCUS, one PHASEABLE_MO and four SPELLCASTER.
-- References/models/maps/phases verified against user-supplied WDC1 DB2 with
-- matching current-core layout hashes. No missing PlayerCondition substituted.
-- Teleport233947 uses effect1; facing is already supplied by native DB2 data.
-- Preserve existing templates/spawns. Reject foreign GUID ownership before world writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_campaign_destinations`;
CREATE TEMPORARY TABLE `_1kycore_generic_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_generic_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_generic_templates` LIKE `gameobject_template`;
INSERT INTO `_1kycore_generic_templates` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`) VALUES
(243784,8,8109,'Alchemical Lab','','','',1,663,10,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21287),
(246428,43,7552,'\"Кровавая завеса\"','','','',1,1547,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246473,0,30592,'Door','','','',1,0,5,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246487,0,30592,'Door','','','',1,0,0,0,0,0,0,0,5703,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(251596,0,6391,'Wall','','','',1.5,0,0,0,0,0,0,0,5703,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(251597,0,14501,'Wall','','','',1.5,0,0,0,0,0,0,0,5703,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(251679,0,14501,'Wall','','','',0.5,0,0,0,0,0,0,0,5703,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(266668,22,8111,'Portal on the Broken Shore','questinteract','','',1,231762,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24015),
(267198,22,26702,'Portal to One Thousand Eagles.','','','',1.3,233947,-1,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24015),
(267595,22,8111,'Portal to Crimson Thicket','','','',1,234742,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24015),
(267957,22,34876,'Portal to the Whirlpool','','','',1,236635,-1,0,1,0,40074,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24015),
(301343,8,299,'Blood Offering Spellfocus','','','',1,1905,8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1);
CREATE TEMPORARY TABLE `_1kycore_generic_addons` LIKE `gameobject_template_addon`;
INSERT INTO `_1kycore_generic_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(243784,0,32,0,0,0),
(246428,0,1048608,0,0,0),
(246473,0,34,0,0,0),
(246487,0,32,0,0,0),
(251596,0,32,0,0,0),
(251597,0,32,0,0,0),
(251679,0,32,0,0,0),
(266668,0,0,0,0,0),
(267198,0,0,0,0,0),
(267595,0,0,0,0,0),
(267957,0,0,0,0,0),
(301343,0,0,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_generic_spawns` LIKE `gameobject`;
INSERT INTO `_1kycore_generic_spawns` (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
(210302377,246473,1545,7334,8003,'12',0,6199,0,-1,-1214.0,6139.76,47.0843,5.86452,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302381,246487,1545,7334,8003,'12',0,6199,0,-1,-1086.08,6025.58,42.6096,1.34551,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302387,246428,1545,7334,8001,'12',0,6199,0,-1,-1521.67,5806.28,5.37278,5.20624,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210306779,267595,1513,7879,7879,'0',0,7781,0,-1,-851.873,4658.19,939.992,1.11612,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210306832,266668,1513,7879,7879,'0',0,7783,0,-1,-845.075,4655.5,939.992,1.92564,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309267,243784,1480,7695,7743,'12',0,5425,0,-1,-702.447,2147.5,588.975,4.95056,7200,0.0,0.0,0.999762,-0.0218145,255,1,0,'',0),
(210310326,301343,1519,8022,8023,'0',0,7606,0,-1,1561.6,1413.02,217.864,4.72984,7200,0.0,0.0,-0.70091,0.71325,255,0,0,'',0),
(210311559,267198,1469,7745,7752,'0',0,5368,0,-1,831.33,1061.48,49.8033,2.28732,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210311597,267957,1,400,2097,'0',0,6468,0,-1,-4908.47,-2078.15,84.574,2.3244,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210313684,251597,1625,8262,8262,'12',0,6905,0,-1,867.292,-2479.34,189.419,5.97973,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210313687,251596,1625,8262,8262,'12',0,6905,0,-1,871.667,-2466.37,176.344,2.82164,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210313698,251679,1625,8262,8262,'12',0,6905,0,-1,891.538,-2463.13,183.142,4.45059,7200,0.0,0.0,0.0,1.0,255,1,0,'',0);
CREATE TEMPORARY TABLE `_1kycore_campaign_destinations` LIKE spell_target_position;
INSERT INTO `_1kycore_campaign_destinations` (`ID`,`EffectIndex`,`MapID`,`PositionX`,`PositionY`,`PositionZ`,`VerifiedBuild`) VALUES
(231762,0,1220,-493.42,3017.62,96.83,0),
(233947,1,1,-5312.15,-2289.93,84.2,0),
(234742,0,1220,1886.64,3541.64,265.97,0),
(236635,0,1469,961.55,1087.81,17.15,0);
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

-- Preserve any matching existing route/build marker; reject altered destinations.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM spell_target_position p JOIN `_1kycore_campaign_destinations` expected
ON p.ID=expected.ID AND p.EffectIndex=expected.EffectIndex
WHERE p.MapID<>expected.MapID OR p.PositionX<>expected.PositionX
OR p.PositionY<>expected.PositionY OR p.PositionZ<>expected.PositionZ LIMIT 1;

-- Complete missing native destinations before adding the corresponding portals.
INSERT INTO spell_target_position (`ID`,`EffectIndex`,`MapID`,`PositionX`,`PositionY`,`PositionZ`,`VerifiedBuild`)
SELECT expected.`ID`,expected.`EffectIndex`,expected.`MapID`,expected.`PositionX`,expected.`PositionY`,expected.`PositionZ`,expected.`VerifiedBuild` FROM `_1kycore_campaign_destinations` expected
LEFT JOIN spell_target_position p ON p.ID=expected.ID AND p.EffectIndex=expected.EffectIndex
WHERE p.ID IS NULL;

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
DROP TEMPORARY TABLE `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_campaign_destinations`;
