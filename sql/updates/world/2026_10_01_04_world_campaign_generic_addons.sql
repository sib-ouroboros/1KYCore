-- 1KYCore: fourth conservative campaign object restoration.
-- Original templates: The-Legion-Preservation-Project/LegionCore-7.3.5
-- release LegionCore735.24101, LegionCore_world_735.26972_2024_10_23.sql.
-- Archive SHA256: cf681e1fb2e7443daab2a5db04f4efa2fc53cc485ea8de6b6ec3d60d569c2696.
-- Spawn coordinates/phases: pinned Sylvania a6145c22e9ad6ac69690d4a2f7794bae4e1caf95.
-- 25 generic objects: 19 native NODESPAWN flags and 6 plain decorations.
-- Five corrupted source names are reversibly recovered from UTF-8 interpreted as CP1252.
-- No scripts, quest/condition IDs, loot or special effects.
-- Preserve existing templates/spawns. Reject foreign GUID ownership before world writes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`;
CREATE TEMPORARY TABLE `_1kycore_generic_guard` (`ok` INT PRIMARY KEY);
INSERT INTO `_1kycore_generic_guard` VALUES (1);
CREATE TEMPORARY TABLE `_1kycore_generic_templates` LIKE `gameobject_template`;
INSERT INTO `_1kycore_generic_templates` (`entry`,`type`,`displayId`,`name`,`IconName`,`castBarCaption`,`unk1`,`size`,`Data0`,`Data1`,`Data2`,`Data3`,`Data4`,`Data5`,`Data6`,`Data7`,`Data8`,`Data9`,`Data10`,`Data11`,`Data12`,`Data13`,`Data14`,`Data15`,`Data16`,`Data17`,`Data18`,`Data19`,`Data20`,`Data21`,`Data22`,`Data23`,`Data24`,`Data25`,`Data26`,`Data27`,`Data28`,`Data29`,`Data30`,`Data31`,`Data32`,`VerifiedBuild`) VALUES
(243629,5,6391,'Security Wall','','','',3,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20994),
(246421,5,31343,'Пиратский флаг','','','',0.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246422,5,31344,'Древко флага','','','',0.3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246423,5,24985,'Кружка','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246424,5,31345,'','','','',1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21021),
(246780,5,17800,'Ритуальный круг','','','',1.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20994),
(246782,5,31712,'Свечи','','','',0.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20994),
(249783,5,29634,'Legion Portal','','','',1.5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249784,5,27616,'Legion Wall','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249785,5,30755,'Fel Pool','','','',2,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249787,5,31146,'Pillar','','','',0.75,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249789,5,33183,'Legion Cage Tower','','','',0.8,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249790,5,29815,'Loot Platform','','','',0.8,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249791,5,33263,'Fel Chest','','','',1.5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249792,5,14901,'Loot Stack','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249793,5,33684,'Loot Stack - Weapons','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249794,5,31790,'Wall Segment','','','',1.5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249795,5,32781,'Wall Segment','','','',1.5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249798,5,31790,'Wall Segment','','','',2,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249800,5,31445,'Wall Chains','','','',1.25,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(249802,5,33689,'Wall Chains','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21232),
(251170,5,14839,'Table','','','',0.75,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(252047,5,28632,'Legion Fel Spreader','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(252048,5,31888,'Legion Ground Rune','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491),
(252050,5,27286,'Legion Brazier','','','',1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,21491);
CREATE TEMPORARY TABLE `_1kycore_generic_addons` LIKE `gameobject_template_addon`;
INSERT INTO `_1kycore_generic_addons` (`entry`,`faction`,`flags`,`mingold`,`maxgold`,`WorldEffectID`) VALUES
(243629,0,32,0,0,0),
(246421,0,0,0,0,0),
(246422,0,0,0,0,0),
(246423,0,0,0,0,0),
(246424,0,0,0,0,0),
(246780,0,0,0,0,0),
(246782,0,0,0,0,0),
(249783,0,32,0,0,0),
(249784,0,32,0,0,0),
(249785,0,32,0,0,0),
(249787,0,32,0,0,0),
(249789,0,32,0,0,0),
(249790,0,32,0,0,0),
(249791,0,32,0,0,0),
(249792,0,32,0,0,0),
(249793,0,32,0,0,0),
(249794,0,32,0,0,0),
(249795,0,32,0,0,0),
(249798,0,32,0,0,0),
(249800,0,32,0,0,0),
(249802,0,32,0,0,0),
(251170,0,32,0,0,0),
(252047,0,32,0,0,0),
(252048,0,32,0,0,0),
(252050,0,32,0,0,0);
CREATE TEMPORARY TABLE `_1kycore_generic_spawns` LIKE `gameobject`;
INSERT INTO `_1kycore_generic_spawns` (`guid`,`id`,`map`,`zoneId`,`areaId`,`spawnDifficulties`,`phaseUseFlags`,`PhaseId`,`PhaseGroup`,`terrainSwapMap`,`position_x`,`position_y`,`position_z`,`orientation`,`spawntimesecs`,`rotation0`,`rotation1`,`rotation2`,`rotation3`,`animprogress`,`state`,`isActive`,`ScriptName`,`VerifiedBuild`) VALUES
(210302378,246422,1545,7334,8001,'12',0,6199,0,-1,-1404.32,5884.04,0.822662,0.0,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302384,246424,1545,7334,8001,'12',0,6199,0,-1,-1380.98,5876.5,2.00603,0.740337,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302386,246423,1545,7334,8001,'12',0,6199,0,-1,-1385.45,5878.4,1.88538,2.05093,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210302388,246421,1545,7334,8001,'12',0,6199,0,-1,-1404.35,5883.81,3.09033,1.56223,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210306788,246780,1220,7502,7502,'0',0,6401,0,-1,-842.988,4431.27,742.536,4.78097,300,0.0,0.0,0.682449,-0.730933,0,1,0,'',0),
(210306789,246782,1220,7502,7502,'0',0,6401,0,-1,-842.964,4431.31,742.535,4.80686,300,0.0,0.0,0.672929,-0.739707,0,1,0,'',0),
(210307890,251170,0,28,2298,'0',0,6936,0,-1,1149.96,-2568.64,60.0382,0.564568,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307909,251170,0,28,2298,'0',0,6936,0,-1,1147.08,-2551.03,60.0484,6.17682,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307930,249792,1498,7637,7768,'12',0,6434,0,-1,1153.96,5213.09,71.0694,5.37724,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307931,249785,1498,7637,7768,'12',0,6434,0,-1,1090.31,5238.9,75.2302,5.9602,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307934,249802,1498,7637,7768,'12',0,6434,0,-1,1126.49,5139.75,93.6947,1.14722,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307935,249795,1498,7637,7768,'12',0,6434,0,-1,1134.24,5134.76,66.1277,4.45029,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307936,249794,1498,7637,7768,'12',0,6434,0,-1,1116.38,5144.31,60.7557,0.581167,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307942,249789,1498,7637,7768,'12',0,6434,0,-1,1134.01,5225.02,70.1337,0.0,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307944,249784,1498,7637,7768,'12',0,6434,0,-1,1175.77,5231.35,76.051,2.37016,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307945,249793,1498,7637,7768,'12',0,6434,0,-1,1147.44,5206.41,70.6657,5.80756,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307950,249787,1498,7637,7768,'12',0,6434,0,-1,1084.2,5249.18,77.5703,5.71868,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307951,249792,1498,7637,7768,'12',0,6434,0,-1,1147.29,5205.19,70.6657,1.09798,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307952,249790,1498,7637,7768,'12',0,6434,0,-1,1153.37,5213.98,69.8732,6.22403,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307958,249783,1498,7637,7768,'12',0,6434,0,-1,1263.82,5235.14,92.732,5.6493,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307959,249793,1498,7637,7768,'12',0,6434,0,-1,1154.7,5213.64,71.0345,3.02032,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307960,249802,1498,7637,7768,'12',0,6434,0,-1,1059.33,5176.26,81.5661,3.43203,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307961,249800,1498,7637,7768,'12',0,6434,0,-1,1101.71,5156.11,101.935,4.09064,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307963,249790,1498,7637,7768,'12',0,6434,0,-1,1147.5,5205.25,69.4982,1.08961,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307967,249795,1498,7637,7768,'12',0,6434,0,-1,1083.93,5168.98,58.062,1.01998,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307977,249784,1498,7637,7768,'12',0,6434,0,-1,1191.61,5243.75,78.6104,1.55658,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307979,249784,1498,7637,7768,'12',0,6434,0,-1,1107.43,5195.99,65.7785,6.11784,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307980,249792,1498,7637,7768,'12',0,6434,0,-1,1148.47,5205.56,70.6657,5.37724,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307982,249794,1498,7637,7768,'12',0,6434,0,-1,1065.23,5168.92,49.7826,0.961022,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307983,249798,1498,7637,7768,'12',0,6434,0,-1,1054.84,5186.01,53.322,3.98278,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307996,249791,1498,7637,7768,'12',0,6434,0,-1,1152.89,5215.41,70.9794,2.08113,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307997,249791,1498,7637,7768,'12',0,6434,0,-1,1146.2,5205.34,70.6657,2.69802,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307998,249791,1498,7637,7768,'12',0,6434,0,-1,1148.46,5204.39,70.6657,1.06244,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210307999,252047,1220,7543,8336,'0',0,7027,0,-1,-731.993,2564.75,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308001,252050,1220,7543,8336,'0',0,7027,0,-1,-697.401,2628.13,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308003,252050,1220,7543,8336,'0',0,7027,0,-1,-609.904,2604.11,82.3863,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308005,252047,1220,7543,8336,'0',0,7027,0,-1,-667.557,2701.74,77.6515,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308006,252050,1220,7543,8336,'0',0,7027,0,-1,-676.082,2647.27,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308009,252050,1220,7543,8336,'0',0,7027,0,-1,-681.219,2556.72,82.3863,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308012,252048,1220,7543,8336,'0',0,7027,0,-1,-647.029,2584.97,82.3863,2.40562,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308013,252047,1220,7543,8336,'0',0,7027,0,-1,-611.769,2648.15,77.4961,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308014,252047,1220,7543,8336,'0',0,7027,0,-1,-776.797,2621.75,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308015,252050,1220,7543,8336,'0',0,7027,0,-1,-726.528,2663.25,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308016,252050,1220,7543,8336,'0',0,7027,0,-1,-748.582,2690.05,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308017,252050,1220,7543,8336,'0',0,7027,0,-1,-714.366,2706.1,76.5226,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308018,252047,1220,7543,8336,'0',0,7027,0,-1,-703.981,2709.17,77.4544,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308019,252050,1220,7543,8336,'0',0,7027,0,-1,-769.68,2670.68,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308020,252050,1220,7543,8336,'0',0,7027,0,-1,-704.314,2679.75,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210308021,252047,1220,7543,8336,'0',0,7027,0,-1,-774.082,2662.38,77.4463,0.0,180,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310330,243629,1498,7637,7768,'12',0,4991,0,-1,1053.45,5072.25,59.9119,0.623185,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310331,243629,1498,7637,7768,'12',0,4991,0,-1,975.43,5082.8,72.7601,1.56229,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310332,243629,1498,7637,7768,'12',0,4991,0,-1,1087.39,4868.45,56.2895,0.988416,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310335,243629,1498,7637,7768,'12',0,4991,0,-1,1000.29,5077.86,63.5206,1.67397,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310336,243629,1498,7637,7768,'12',0,4991,0,-1,965.436,5027.07,25.1718,1.05555,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310337,243629,1498,7637,7768,'12',0,4991,0,-1,1029.41,5089.83,67.7992,1.67397,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310338,243629,1498,7637,7768,'12',0,4991,0,-1,1023.15,4994.39,24.6543,1.05555,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310339,243629,1498,7637,7768,'12',0,4991,0,-1,994.307,5010.61,25.1718,1.05555,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310346,243629,1498,7637,7768,'12',0,4991,0,-1,1171.09,4956.16,54.7784,0.0346716,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310347,243629,1498,7637,7768,'12',0,4991,0,-1,1180.14,4934.46,59.6446,0.574527,7200,0.0,0.0,0.0,1.0,255,1,0,'',0),
(210310350,243629,1498,7637,7768,'12',0,4991,0,-1,1193.18,4929.08,65.9065,0.876397,7200,0.0,0.0,0.0,1.0,255,1,0,'',0);
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
DROP TEMPORARY TABLE `_1kycore_generic_guard`, `_1kycore_generic_templates`, `_1kycore_generic_spawns`, `_1kycore_generic_addons`;
