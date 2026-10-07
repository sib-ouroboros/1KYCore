-- Native Godfrey24592 departure, remapped source spawn252545 -> release spawn802361.
-- Source: pinned ArkCORE-NG July2016 archive/2016_07_07_00_world.sql.
-- All source positions/IDs0..4 are retained; map654 mmaps connectivity checked separately.
-- No gravity, teleport, quest credit, faction or objective changes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_godfrey_route`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_godfrey_route` (`point` INT UNSIGNED,`x` DOUBLE,`y` DOUBLE,`z` DOUBLE,`o` DOUBLE,`move_type` TINYINT UNSIGNED);
INSERT INTO `_1kycore_gilneas_godfrey_route` VALUES
(0,-2039.679,983.3817,70.06663,4.322849,1),
(1,-2043.107,977.2275,70.06663,4.684133,1),
(2,-2043.373,967.8233,70.07954,4.511345,1),
(3,-2051.509,960.2091,70.09149,3.890882,1),
(4,-2077.494,952.7342,70.49577,3.301833,1);
INSERT INTO `waypoint_data` (`id`,`point`,`position_x`,`position_y`,`position_z`,`orientation`,`delay`,`move_type`,`action`,`action_chance`,`wpguid`)
SELECT c.`guid`,p.`point`,p.`x`,p.`y`,p.`z`,p.`o`,0,p.`move_type`,0,100,0
FROM `_1kycore_gilneas_godfrey_route` p
JOIN `creature` c ON c.`guid`=802361 AND c.`id`=37875 AND c.`map`=654 AND c.`PhaseId`=186 AND c.`PhaseGroup`=0
JOIN `creature_template` godfrey ON godfrey.`entry`=c.`id` AND godfrey.`AIName`='' AND godfrey.`ScriptName`='npc_gilneas_godfrey_departure'
JOIN `creature_template` genn ON genn.`entry`=37876 AND genn.`AIName`='' AND genn.`ScriptName`='npc_king_genn_greymane_37876'
WHERE c.`ScriptName` IN ('','npc_gilneas_godfrey_departure') AND c.`MovementType`=0 AND c.`spawndist`=0
 AND ABS(c.`position_x`-(-2041.35))<0.01 AND ABS(c.`position_y`-979.016)<0.01 AND ABS(c.`position_z`-70.1487)<0.01
 AND NOT EXISTS (SELECT 1 FROM `waypoint_data` w WHERE w.`id`=c.`guid`)
 AND NOT EXISTS (SELECT 1 FROM `creature_addon` a WHERE a.`guid`=c.`guid` AND a.`path_id`<>0)
 AND NOT EXISTS (SELECT 1 FROM `smart_scripts` a WHERE a.`entryorguid`=-CAST(c.`guid` AS SIGNED));
DROP TEMPORARY TABLE `_1kycore_gilneas_godfrey_route`;
