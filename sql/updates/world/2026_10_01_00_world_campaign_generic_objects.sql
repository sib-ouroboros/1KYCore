-- 1KYCore: first conservative campaign object restoration.
-- Original templates: The-Legion-Preservation-Project/LegionCore-7.3.5
-- release LegionCore735.24101, LegionCore_world_735.26972_2024_10_23.sql.
-- Archive SHA256: cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Spawn coordinates/phases: pinned Sylvania a6145c22e9ad6ac69690d4a2f7794bae4e1caf95.
-- Six generic objects: all DataN, special effects, faction, flags and quest items are zero.
-- Preserve existing templates/spawns. Reject foreign GUID ownership before world writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`;
CREATE TEMPORARY TABLE `_1kycore_generic_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_generic_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_generic_templates` LIKE `gameobject_template`;
INSERT INTO `_1kycore_generic_templates` (`entry`,`type`,`displayId`,`name`,`size`,`VerifiedBuild`) VALUES
(226941,5,35126,'Blood spatter',1,23420),
(245435,5,7736,'Armor Stand',1,20994),
(246161,5,30877,'Round Table',1,21491),
(246419,5,13400,'Boat',1,21021),
(246420,5,16847,'Bonfire',1,21021),
(246429,5,30953,'Compass',1,21021);
CREATE TEMPORARY TABLE `_1kycore_generic_spawns` LIKE `gameobject`;
INSERT INTO `_1kycore_generic_spawns` (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
(210301279,245435,1220,7502,8011,'0',0,6764,0,-1,-878.564,4491.88,706.539,2.55324,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301301,245435,1220,7502,8011,'0',0,6764,0,-1,-883.764,4500.73,706.655,5.03795,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301302,245435,1220,7502,8011,'0',0,6764,0,-1,-886.587,4488.46,706.53,2.2096,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301303,245435,1220,7502,8011,'0',0,6764,0,-1,-889.708,4501.32,706.614,4.60113,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301304,245435,1220,7502,8011,'0',0,6764,0,-1,-884.439,4490.25,706.529,1.9184,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301308,245435,1220,7502,8011,'0',0,6764,0,-1,-895.873,4493.09,706.571,0.0914358,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210301309,245435,1220,7502,8011,'0',0,6764,0,-1,-896.076,4497.71,706.602,5.65304,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302382,246420,1545,7334,8001,'12',0,6199,0,-1,-1384.37,5880.65,1.93558,6.23368,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302385,246429,1545,7334,8001,'12',0,6199,0,-1,-1381.18,5876.98,3.13861,5.49394,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302389,246419,1545,7334,8001,'12',0,6199,0,-1,-1400.62,5885.21,0.195427,0.0933501,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302517,246420,1545,7334,8001,'12',0,6199,0,-1,-1022.99,5949.32,16.119,6.0675,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302518,246420,1545,7334,8001,'12',0,6199,0,-1,-999.333,5974.26,16.4918,6.0675,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307912,246161,0,28,2298,'0',0,6936,0,-1,1082.17,-2558.84,60.7873,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307918,246161,0,28,2298,'0',0,6936,0,-1,1146.93,-2553.88,60.0527,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309074,226941,1618,8285,8285,'0',0,7557,0,-1,1036.42,591.057,0.811604,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309075,226941,1618,8285,8285,'0',0,7557,0,-1,1038.45,612.762,0.347416,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309076,226941,1618,8285,8285,'0',0,7557,0,-1,1045.2,632.637,1.00549,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309077,226941,1618,8285,8285,'0',0,7557,0,-1,1046.97,641.111,1.00548,4.30843,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309123,226941,1618,8285,8285,'0',0,7557,0,-1,1031.88,648.087,0.344259,5.1074,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309124,226941,1618,8285,8285,'0',0,7557,0,-1,1038.26,648.948,0.34426,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309125,226941,1618,8285,8285,'0',0,7557,0,-1,1030.41,624.085,0.34772,0.32051,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309126,226941,1618,8285,8285,'0',0,7557,0,-1,1028.22,616.592,0.859086,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309127,226941,1618,8285,8285,'0',0,7557,0,-1,1029.84,613.62,0.347595,1.21667,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309129,226941,1618,8285,8285,'0',0,7557,0,-1,1055.53,636.208,1.00548,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309130,226941,1618,8285,8285,'0',0,7557,0,-1,1029.57,600.116,0.345025,0.0,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309131,226941,1618,8285,8285,'0',0,7557,0,-1,1037.45,602.849,0.345323,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309132,226941,1618,8285,8285,'0',0,7557,0,-1,1030.59,591.498,0.888917,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210309133,226941,1618,8285,8285,'0',0,7557,0,-1,1038.94,622.128,0.347719,2.64463,120,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310289,245435,1220,7502,8011,'0',0,6261,0,-1,-878.564,4491.88,706.539,2.55324,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310295,245435,1220,7502,8011,'0',0,6261,0,-1,-883.764,4500.73,706.655,5.03795,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310296,245435,1220,7502,8011,'0',0,6261,0,-1,-886.587,4488.46,706.53,2.2096,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310297,245435,1220,7502,8011,'0',0,6261,0,-1,-889.708,4501.32,706.614,4.60113,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310298,245435,1220,7502,8011,'0',0,6261,0,-1,-884.439,4490.25,706.529,1.9184,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310302,245435,1220,7502,8011,'0',0,6261,0,-1,-895.873,4493.09,706.571,0.0914358,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310303,245435,1220,7502,8011,'0',0,6261,0,-1,-896.076,4497.71,706.602,5.65304,180,0.0,0.0,0.0,1.0,255,1,0,'',0);
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject g JOIN `_1kycore_generic_spawns` expected ON g.guid=expected.guid
WHERE g.id<>expected.id LIMIT 1;
-- A pre-existing addon for an absent template is not silently reinterpreted.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_template_addon a JOIN `_1kycore_generic_templates` expected ON a.entry=expected.entry
LEFT JOIN gameobject_template t ON t.entry=expected.entry
WHERE t.entry IS NULL AND (a.faction<>0 OR a.flags<>0 OR a.mingold<>0 OR a.maxgold<>0 OR a.WorldEffectID<>0) LIMIT 1;
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_questitem qi JOIN `_1kycore_generic_templates` expected ON qi.GameObjectEntry=expected.entry
LEFT JOIN gameobject_template t ON t.entry=expected.entry
WHERE t.entry IS NULL AND qi.ItemId<>0 LIMIT 1;
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM gameobject_template t JOIN `_1kycore_generic_templates` expected ON t.entry=expected.entry
WHERE t.type<>5 OR t.AIName<>'' OR t.ScriptName<>'' OR t.Data0<>0 OR t.Data1<>0 OR t.Data2<>0 OR t.Data3<>0 OR t.Data4<>0 OR t.Data5<>0 OR t.Data6<>0 OR t.Data7<>0 OR t.Data8<>0 OR t.Data9<>0 OR t.Data10<>0 OR t.Data11<>0 OR t.Data12<>0 OR t.Data13<>0 OR t.Data14<>0 OR t.Data15<>0 OR t.Data16<>0 OR t.Data17<>0 OR t.Data18<>0 OR t.Data19<>0 OR t.Data20<>0 OR t.Data21<>0 OR t.Data22<>0 OR t.Data23<>0 OR t.Data24<>0 OR t.Data25<>0 OR t.Data26<>0 OR t.Data27<>0 OR t.Data28<>0 OR t.Data29<>0 OR t.Data30<>0 OR t.Data31<>0 OR t.Data32<>0 LIMIT 1;

-- Add only absent templates; retain every pre-existing template unchanged.
INSERT INTO gameobject_template (`entry`,`type`,`displayId`,`name`,`size`,`VerifiedBuild`)
SELECT expected.entry,expected.type,expected.displayId,expected.name,expected.size,expected.VerifiedBuild
FROM `_1kycore_generic_templates` expected LEFT JOIN gameobject_template t ON t.entry=expected.entry
WHERE t.entry IS NULL;

-- Restore exact imported spawns, leaving existing coordinates/phases untouched.
INSERT INTO gameobject (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`)
SELECT expected.`guid`,expected.`id`,expected.`map`,expected.`zoneId`,expected.`areaId`,expected.`spawnDifficulties`,expected.`phaseUseFlags`,expected.`PhaseId`,expected.`PhaseGroup`,expected.`terrainSwapMap`,expected.`position_x`,expected.`position_y`,expected.`position_z`,expected.`orientation`,expected.`spawntimesecs`,expected.`rotation0`,expected.`rotation1`,expected.`rotation2`,expected.`rotation3`,expected.`animprogress`,expected.`state`,expected.`isActive`,expected.`ScriptName`,expected.`VerifiedBuild`
FROM `_1kycore_generic_spawns` expected LEFT JOIN gameobject g ON g.guid=expected.guid
WHERE g.guid IS NULL;
DROP TEMPORARY TABLE `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`;
