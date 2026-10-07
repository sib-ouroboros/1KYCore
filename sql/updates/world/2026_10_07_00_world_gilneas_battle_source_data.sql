-- Restore the native Gilneas battle start/join positions and 90-second regrouping.
-- Pinned ArkCORE-NG a7304c3075bf8ee7eb5bdf45f31cda01c8626b52, July2016 archive.
-- Only the exact release spawns in phase187 with native scripts are eligible.
-- Custom positions, timers, movement, per-spawn scripts/addons and external owners survive.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_battle_spawns`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_battle_spawns` (
 `guid` BIGINT UNSIGNED PRIMARY KEY, `entry` INT UNSIGNED, `script` VARCHAR(64),
 `old_x` DOUBLE, `old_y` DOUBLE, `old_z` DOUBLE, `old_o` DOUBLE,
 `old_movement` TINYINT UNSIGNED, `old_distance` DOUBLE,
 `x` DOUBLE, `y` DOUBLE, `z` DOUBLE, `o` DOUBLE
);
INSERT INTO `_1kycore_gilneas_battle_spawns` VALUES
(802761,38218,'npc_prince_liam_greymane_38218',-1770.8,1381.13,19.8033,3.36518,1,10.0,-1408.661,1260.017,36.51123,1.79),
(802707,38415,'npc_lord_darius_crowley_38415',-1752.55,1362.04,19.8818,0.785867,1,10.0,-1773.54,1341.46,19.786,0.94),
(802754,38426,'npc_lorna_crowley_38426',-1804.81,1470.29,19.3146,1.70597,1,10.0,-1549.21,1285.97,11.7804,3.47383),
(802671,38465,'npc_myriam_spellwaker_38465',-1412.95,1248.7,36.5112,1.76278,0,0.0,-1412.95,1248.7,36.5112,1.76278),
(802670,38466,'npc_sister_almyra_38466',-1401.31,1251.91,36.5112,2.02458,0,0.0,-1401.31,1251.91,36.5112,2.02458),
(802781,38469,'npc_lady_sylvanas_windrunner_38469',-1678.06,1611.81,20.5728,2.44346,0,0.0,-1678.06,1611.81,20.5728,2.44346),
(802822,38470,'npc_king_genn_greymane_38470',-1779.95,1694.7,22.158,5.58193,0,0.0,-1750.84,1670.42,22.158,5.6022);
UPDATE `creature` c
JOIN `_1kycore_gilneas_battle_spawns` s ON s.`guid`=c.`guid` AND s.`entry`=c.`id`
JOIN `creature_template` t ON t.`entry`=c.`id` AND t.`ScriptName`=s.`script` AND t.`AIName`=''
SET c.`VerifiedBuild`=0,
 c.`position_x`=s.`x`,c.`position_y`=s.`y`,c.`position_z`=s.`z`,c.`orientation`=s.`o`,
 c.`MovementType`=0,c.`spawndist`=0,c.`spawntimesecs`=90
WHERE c.`map`=654 AND c.`PhaseId`=187 AND c.`PhaseGroup`=0
 AND c.`ScriptName` IN ('',s.`script`) AND c.`spawntimesecs`=7200
 AND c.`MovementType`=s.`old_movement` AND ABS(c.`spawndist`-s.`old_distance`)<0.01
 AND ABS(c.`position_x`-s.`old_x`)<0.01 AND ABS(c.`position_y`-s.`old_y`)<0.01
 AND ABS(c.`position_z`-s.`old_z`)<0.01 AND ABS(c.`orientation`-s.`old_o`)<0.01
 AND NOT EXISTS (SELECT 1 FROM `creature_addon` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `smart_scripts` a WHERE a.`entryorguid`=-CAST(c.`guid` AS SIGNED))
 AND NOT EXISTS (SELECT 1 FROM `game_event_creature` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `pool_creature` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `creature_formations` a WHERE a.`leaderGUID`=c.`guid` OR a.`memberGUID`=c.`guid`);
DROP TEMPORARY TABLE `_1kycore_gilneas_battle_spawns`;

-- Liam38474 is created by Sylvanas' native cinematic, not a permanent duplicate.
-- The source2016_07_14_03 removes all such spawns; here only the known release row is removed.
DELETE c FROM `creature` c JOIN `creature_template` t ON t.`entry`=c.`id`
WHERE c.`guid`=802851 AND c.`id`=38474 AND c.`map`=654 AND c.`PhaseId`=187 AND c.`PhaseGroup`=0
 AND c.`ScriptName` IN ('','npc_prince_liam_greymane_38474')
 AND t.`ScriptName`='npc_prince_liam_greymane_38474' AND t.`AIName`=''
 AND ABS(c.`position_x`-(-1634.67))<0.01 AND ABS(c.`position_y`-1631.74)<0.01
 AND ABS(c.`position_z`-21.2092)<0.01 AND ABS(c.`orientation`-4.41519)<0.01
 AND c.`MovementType`=0 AND c.`spawndist`=0 AND c.`spawntimesecs`=7200
 AND NOT EXISTS (SELECT 1 FROM `creature_addon` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `smart_scripts` a WHERE a.`entryorguid`=-CAST(c.`guid` AS SIGNED))
 AND NOT EXISTS (SELECT 1 FROM `game_event_creature` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `pool_creature` a WHERE a.`guid`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `creature_formations` a WHERE a.`leaderGUID`=c.`guid` OR a.`memberGUID`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `creature_queststarter` a WHERE a.`id`=c.`id`)
 AND NOT EXISTS (SELECT 1 FROM `creature_questender` a WHERE a.`id`=c.`id`);

-- Import missing routes as complete groups; preserve any existing/custom route.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_battle_routes`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_battle_routes` (
 `id` INT UNSIGNED,`point` INT UNSIGNED,`entry` INT UNSIGNED,`script` VARCHAR(64),
 `x` DOUBLE,`y` DOUBLE,`z` DOUBLE,`o` DOUBLE,`move_type` TINYINT UNSIGNED
);
INSERT INTO `_1kycore_gilneas_battle_routes` VALUES
(3847401,0,38474,'npc_prince_liam_greymane_38474',-1634.873,1636.791,21.12881,4.689035,1),
(3847401,1,38474,'npc_prince_liam_greymane_38474',-1635.782,1621.483,20.42826,3.177146,1),
(3847401,2,38474,'npc_prince_liam_greymane_38474',-1661.025,1620.674,20.48856,3.188927,1),
(3847401,3,38474,'npc_prince_liam_greymane_38474',-1679.49,1618.253,20.48856,3.361714,1),
(3846901,0,38469,'npc_lady_sylvanas_windrunner_38469',-1659.57,1620.006,20.48808,0.24366,0),
(3846901,1,38469,'npc_lady_sylvanas_windrunner_38469',-1631.088,1621.131,20.48824,0.039456,0),
(3846901,2,38469,'npc_lady_sylvanas_windrunner_38469',-1631.993,1651.859,20.48824,1.563129,0);
INSERT INTO `waypoint_data` (`id`,`point`,`position_x`,`position_y`,`position_z`,`orientation`,`delay`,`move_type`,`action`,`action_chance`,`wpguid`)
SELECT s.`id`,s.`point`,s.`x`,s.`y`,s.`z`,s.`o`,0,s.`move_type`,0,100,0
FROM `_1kycore_gilneas_battle_routes` s
JOIN `creature_template` t ON t.`entry`=s.`entry` AND t.`ScriptName`=s.`script` AND t.`AIName`=''
WHERE NOT EXISTS (SELECT 1 FROM `waypoint_data` w WHERE w.`id`=s.`id`);
DROP TEMPORARY TABLE `_1kycore_gilneas_battle_routes`;
