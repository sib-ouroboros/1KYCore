-- 1KYCore: fifth conservative campaign object restoration.
-- Original templates: The-Legion-Preservation-Project/LegionCore-7.3.5
-- release LegionCore735.24101, LegionCore_world_735.26972_2024_10_23.sql.
-- Archive SHA256: cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Spawn coordinates/phases: pinned Sylvania a6145c22e9ad6ac69690d4a2f7794bae4e1caf95.
-- Original wall251657 with its own native SmartGameObjectAI script.
-- UPDATE60 -> ACTIVATE_GOBJECT9 SELF1, NOT_REPEATABLE1; no external producer.
-- Native enums, GO event mask, model, condition, maps and phases reviewed.
-- Preserve existing templates/spawns. Reject foreign GUID ownership before world writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_wall_scripts`;
CREATE TEMPORARY TABLE `_1kycore_generic_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_generic_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_generic_templates` LIKE `gameobject_template`;
INSERT INTO `_1kycore_generic_templates` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`,`AIName`,`ScriptName`) VALUES
(251657,0,11420,'Wall','','','',1,0,0,0,0,0,0,0,5703,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491,'SmartGameObjectAI','');
CREATE TEMPORARY TABLE `_1kycore_generic_addons` LIKE `gameobject_template_addon`;
INSERT INTO `_1kycore_generic_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(251657,0,4,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_generic_spawns` LIKE `gameobject`;
INSERT INTO `_1kycore_generic_spawns` (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
(210313693,251657,1625,8262,8262,'12',0,6905,0,-1,879.309,-2459.46,176.303,1.26008,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210313702,251657,1625,8262,8262,'12',0,6905,0,-1,968.215,-2606.99,181.288,2.82164,7200,0.0,0.0,0.0,1.0,255,1,0,'',0);
CREATE TEMPORARY TABLE `_1kycore_wall_scripts` LIKE smart_scripts;
INSERT INTO `_1kycore_wall_scripts` (`entryorguid`,`source_type`,`id`,`link`,`event_type`,`event_phase_mask`,`event_chance`,`event_flags`,`event_param1`,`event_param2`,`event_param3`,`event_param4`,`event_param5`,`event_param_string`,`action_type`,`action_param1`,`action_param2`,`action_param3`,`action_param4`,`action_param5`,`action_param6`,`target_type`,`target_param1`,`target_param2`,`target_param3`,`target_x`,`target_y`,`target_z`,`target_o`,`comment`) VALUES (251657,1,0,0,60,0,100,1,0,0,0,0,0,'',9,0,0,0,0,0,0,1,0,0,0,0,0,0,0,'Event Update - Activate GO');
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
WHERE t.type<>expected.type OR BINARY t.AIName<>BINARY expected.AIName OR BINARY t.ScriptName<>BINARY expected.ScriptName OR t.Data0<>expected.Data0 OR t.Data1<>expected.Data1 OR t.Data2<>expected.Data2 OR t.Data3<>expected.Data3 OR t.Data4<>expected.Data4 OR t.Data5<>expected.Data5 OR t.Data6<>expected.Data6 OR t.Data7<>expected.Data7 OR t.Data8<>expected.Data8 OR t.Data9<>expected.Data9 OR t.Data10<>expected.Data10 OR t.Data11<>expected.Data11 OR t.Data12<>expected.Data12 OR t.Data13<>expected.Data13 OR t.Data14<>expected.Data14 OR t.Data15<>expected.Data15 OR t.Data16<>expected.Data16 OR t.Data17<>expected.Data17 OR t.Data18<>expected.Data18 OR t.Data19<>expected.Data19 OR t.Data20<>expected.Data20 OR t.Data21<>expected.Data21 OR t.Data22<>expected.Data22 OR t.Data23<>expected.Data23 OR t.Data24<>expected.Data24 OR t.Data25<>expected.Data25 OR t.Data26<>expected.Data26 OR t.Data27<>expected.Data27 OR t.Data28<>expected.Data28 OR t.Data29<>expected.Data29 OR t.Data30<>expected.Data30 OR t.Data31<>expected.Data31 OR t.Data32<>expected.Data32 LIMIT 1;

-- Exact native script semantics; preserve a compatible custom comment.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM smart_scripts s LEFT JOIN `_1kycore_wall_scripts` expected
ON s.entryorguid=expected.entryorguid AND s.source_type=expected.source_type
AND s.id=expected.id AND s.link=expected.link
WHERE s.entryorguid=251657 AND s.source_type=1
AND (expected.entryorguid IS NULL OR NOT ((s.`entryorguid` <=> expected.`entryorguid`) AND (s.`source_type` <=> expected.`source_type`) AND (s.`id` <=> expected.`id`) AND (s.`link` <=> expected.`link`) AND (s.`event_type` <=> expected.`event_type`) AND (s.`event_phase_mask` <=> expected.`event_phase_mask`) AND (s.`event_chance` <=> expected.`event_chance`) AND (s.`event_flags` <=> expected.`event_flags`) AND (s.`event_param1` <=> expected.`event_param1`) AND (s.`event_param2` <=> expected.`event_param2`) AND (s.`event_param3` <=> expected.`event_param3`) AND (s.`event_param4` <=> expected.`event_param4`) AND (s.`event_param5` <=> expected.`event_param5`) AND (BINARY s.`event_param_string` <=> BINARY expected.`event_param_string`) AND (s.`action_type` <=> expected.`action_type`) AND (s.`action_param1` <=> expected.`action_param1`) AND (s.`action_param2` <=> expected.`action_param2`) AND (s.`action_param3` <=> expected.`action_param3`) AND (s.`action_param4` <=> expected.`action_param4`) AND (s.`action_param5` <=> expected.`action_param5`) AND (s.`action_param6` <=> expected.`action_param6`) AND (s.`target_type` <=> expected.`target_type`) AND (s.`target_param1` <=> expected.`target_param1`) AND (s.`target_param2` <=> expected.`target_param2`) AND (s.`target_param3` <=> expected.`target_param3`) AND (s.`target_x` <=> expected.`target_x`) AND (s.`target_y` <=> expected.`target_y`) AND (s.`target_z` <=> expected.`target_z`) AND (s.`target_o` <=> expected.`target_o`))) LIMIT 1;
-- GUID-specific overrides shadow the entry script and must be reviewed separately.
INSERT INTO `_1kycore_generic_guard`
SELECT 1 FROM smart_scripts WHERE source_type=1 AND entryorguid IN (-210313693,-210313702) LIMIT 1;

-- Install the native script before enabling AI on any new wall template.
INSERT INTO smart_scripts (`entryorguid`,`source_type`,`id`,`link`,`event_type`,`event_phase_mask`,`event_chance`,`event_flags`,`event_param1`,`event_param2`,`event_param3`,`event_param4`,`event_param5`,`event_param_string`,`action_type`,`action_param1`,`action_param2`,`action_param3`,`action_param4`,`action_param5`,`action_param6`,`target_type`,`target_param1`,`target_param2`,`target_param3`,`target_x`,`target_y`,`target_z`,`target_o`,`comment`)
SELECT expected.`entryorguid`,expected.`source_type`,expected.`id`,expected.`link`,expected.`event_type`,expected.`event_phase_mask`,expected.`event_chance`,expected.`event_flags`,expected.`event_param1`,expected.`event_param2`,expected.`event_param3`,expected.`event_param4`,expected.`event_param5`,expected.`event_param_string`,expected.`action_type`,expected.`action_param1`,expected.`action_param2`,expected.`action_param3`,expected.`action_param4`,expected.`action_param5`,expected.`action_param6`,expected.`target_type`,expected.`target_param1`,expected.`target_param2`,expected.`target_param3`,expected.`target_x`,expected.`target_y`,expected.`target_z`,expected.`target_o`,expected.`comment` FROM `_1kycore_wall_scripts` expected
LEFT JOIN smart_scripts s ON s.entryorguid=expected.entryorguid AND s.source_type=expected.source_type
AND s.id=expected.id AND s.link=expected.link WHERE s.entryorguid IS NULL;

-- Restore exact source addons before templates, so an interrupted import can retry.
-- All ownership/behavior/dependency guards above run BEFORE any permanent write.
INSERT INTO gameobject_template_addon (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`)
SELECT expected.`entry`,expected.`faction`,expected.`flags`,expected.`mingold`,expected.`maxgold`,expected.`WorldEffectID`
FROM `_1kycore_generic_addons` expected LEFT JOIN gameobject_template_addon a ON a.entry=expected.entry
WHERE a.entry IS NULL;

-- Add only absent templates; retain every pre-existing compatible template.
INSERT INTO gameobject_template (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`,`AIName`,`ScriptName`)
SELECT expected.`entry`,expected.`type`,expected.`displayId`,expected.`name`,expected.`IconName`,expected.`castBarCaption`,expected.`unk1`,expected.`size`,expected.`Data0`,expected.`Data1`,expected.`Data2`,expected.`Data3`,expected.`Data4`,expected.`Data5`,expected.`Data6`,expected.`Data7`,expected.`Data8`,expected.`Data9`,expected.`Data10`,expected.`Data11`,expected.`Data12`,expected.`Data13`,expected.`Data14`,expected.`Data15`,expected.`Data16`,expected.`Data17`,expected.`Data18`,expected.`Data19`,expected.`Data20`,expected.`Data21`,expected.`Data22`,expected.`Data23`,expected.`Data24`,expected.`Data25`,expected.`Data26`,expected.`Data27`,expected.`Data28`,expected.`Data29`,expected.`Data30`,expected.`Data31`,expected.`Data32`,expected.`VerifiedBuild`,expected.`AIName`,expected.`ScriptName` FROM `_1kycore_generic_templates` expected
LEFT JOIN gameobject_template t ON t.entry=expected.entry WHERE t.entry IS NULL;

-- Restore exact imported spawns, leaving existing coordinates/phases untouched.
INSERT INTO gameobject (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`)
SELECT expected.`guid`,expected.`id`,expected.`map`,expected.`zoneId`,expected.`areaId`,expected.`spawnDifficulties`,expected.`phaseUseFlags`,expected.`PhaseId`,expected.`PhaseGroup`,expected.`terrainSwapMap`,expected.`position_x`,expected.`position_y`,expected.`position_z`,expected.`orientation`,expected.`spawntimesecs`,expected.`rotation0`,expected.`rotation1`,expected.`rotation2`,expected.`rotation3`,expected.`animprogress`,expected.`state`,expected.`isActive`,expected.`ScriptName`,expected.`VerifiedBuild`
FROM `_1kycore_generic_spawns` expected LEFT JOIN gameobject g ON g.guid=expected.guid
WHERE g.guid IS NULL;
DROP TEMPORARY TABLE `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`, `_1kycore_wall_scripts`;
