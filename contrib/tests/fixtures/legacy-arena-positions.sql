CREATE TABLE `aiwaypoints`  (
  `entry` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `map` int(10) NOT NULL DEFAULT 0,
  `x` float NOT NULL DEFAULT 0,
  `y` float NOT NULL DEFAULT 0,
  `z` float NOT NULL DEFAULT 0,
  `link` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `helpText` varchar(128) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`entry`) USING BTREE,
  UNIQUE INDEX `entry_UNIQUE`(`entry`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 74 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of aiwaypoints
-- ----------------------------
INSERT INTO `aiwaypoints` VALUES (7, 489, 1539.39, 1481.34, 352.487, '', '战歌LM旗点');
INSERT INTO `aiwaypoints` VALUES (8, 489, 1449.07, 1491, 350.279, '', '战歌LM出口1');
INSERT INTO `aiwaypoints` VALUES (9, 489, 1355.67, 1461.9, 324.513, '', '战歌LM出口2');
INSERT INTO `aiwaypoints` VALUES (10, 489, 1356.13, 1396.79, 325.811, '', '战歌LM出口3');
INSERT INTO `aiwaypoints` VALUES (11, 489, 916.729, 1434.61, 346.283, '', '战歌BL旗点');
INSERT INTO `aiwaypoints` VALUES (12, 489, 1003.91, 1425.61, 344.184, '', '战歌BL出口1');
INSERT INTO `aiwaypoints` VALUES (13, 489, 1120.45, 1462.24, 316.268, '', '战歌BL出口2');
INSERT INTO `aiwaypoints` VALUES (14, 489, 1094.43, 1532.12, 315.771, '', '战歌BL出口3');
INSERT INTO `aiwaypoints` VALUES (17, 529, 1166.28, 1202.05, -56.4207, '', '');
INSERT INTO `aiwaypoints` VALUES (18, 529, 855.425, 1150.35, 11.539, '', '');
INSERT INTO `aiwaypoints` VALUES (19, 529, 978.243, 1045.1, -44.5344, '', '');
INSERT INTO `aiwaypoints` VALUES (20, 529, 1145.71, 849.484, -110.513, '', '');
INSERT INTO `aiwaypoints` VALUES (21, 529, 804.227, 874.871, -55.2496, '', '');
INSERT INTO `aiwaypoints` VALUES (22, 529, 1154.43, 999.954, -63.9715, '', '阿拉希联盟桥口');
INSERT INTO `aiwaypoints` VALUES (23, 529, 850.353, 986.463, -60.0914, '', '阿拉希部落桥口');
INSERT INTO `aiwaypoints` VALUES (24, 529, 1291.84, 1289.03, -13.6839, '', '阿拉希联盟开始点');
INSERT INTO `aiwaypoints` VALUES (25, 529, 701.937, 703.624, -15.9786, '', '阿拉希部落开始点');
INSERT INTO `aiwaypoints` VALUES (26, 566, 2456.89, 1602.02, 1206.45, '', '暴风之眼联盟开始点');
INSERT INTO `aiwaypoints` VALUES (27, 566, 1875.77, 1530.65, 1206.87, '', '暴风之眼部落开始点');
INSERT INTO `aiwaypoints` VALUES (28, 566, 2284.83, 1730.77, 1189.91, '', '暴风之眼联盟1塔');
INSERT INTO `aiwaypoints` VALUES (29, 566, 2286.77, 1402.8, 1197.18, '', '暴风之眼联盟2塔');
INSERT INTO `aiwaypoints` VALUES (30, 566, 2048.39, 1393.9, 1194.39, '', '暴风之眼部落1塔');
INSERT INTO `aiwaypoints` VALUES (31, 566, 2044, 1729.95, 1189.86, '', '暴风之眼部落2塔');
INSERT INTO `aiwaypoints` VALUES (32, 566, 2174.32, 1569.64, 1159.96, '', '暴风之眼旗点');
INSERT INTO `aiwaypoints` VALUES (37, 30, 705.506, -15.6266, 50.1454, '', '奥山LM将军点');
INSERT INTO `aiwaypoints` VALUES (38, 30, 638.783, -33.4612, 45.9414, '', '奥山LM将军墓地点');
INSERT INTO `aiwaypoints` VALUES (39, 30, 673.537, -143.997, 63.6631, '', '奥山LM北塔');
INSERT INTO `aiwaypoints` VALUES (40, 30, 553.358, -77.6423, 51.9391, '', '奥山LM南塔');
INSERT INTO `aiwaypoints` VALUES (41, 30, 667.742, -293.749, 30.301, '', '奥山LM雷矛墓地点');
INSERT INTO `aiwaypoints` VALUES (42, 30, 202.546, -359.454, 56.387, '', '奥山LM冰翼塔');
INSERT INTO `aiwaypoints` VALUES (43, 30, -152.278, -440.811, 40.3996, '', '奥山LM石炉塔');
INSERT INTO `aiwaypoints` VALUES (44, 30, 77.2176, -402.11, 46.407, '', '奥山LM石炉墓地点');
INSERT INTO `aiwaypoints` VALUES (45, 30, -41.3935, -289.563, 15.0886, '', '奥山LM女人点');
INSERT INTO `aiwaypoints` VALUES (46, 30, -203.972, -114.35, 79.7015, '', '奥山落雪墓地点');
INSERT INTO `aiwaypoints` VALUES (47, 30, -534.268, -169.448, 57.011, '', '奥山BL男人点');
INSERT INTO `aiwaypoints` VALUES (48, 30, -613.005, -397.793, 60.8684, '', '奥山BL冰血墓地点');
INSERT INTO `aiwaypoints` VALUES (49, 30, -571.105, -263.464, 75.0179, '', '奥山BL冰血塔');
INSERT INTO `aiwaypoints` VALUES (50, 30, -768.377, -362.685, 90.906, '', '奥山BL高塔');
INSERT INTO `aiwaypoints` VALUES (51, 30, -1080.68, -345.853, 55.1093, '', '奥山BL霜狼墓地点');
INSERT INTO `aiwaypoints` VALUES (52, 30, -1303.43, -316.12, 113.877, '', '奥山BL东塔');
INSERT INTO `aiwaypoints` VALUES (53, 30, -1298.56, -266.924, 114.16, '', '奥山BL西塔');
INSERT INTO `aiwaypoints` VALUES (54, 30, -1402.5, -309.193, 89.3977, '', '奥山BL将军墓地点');
INSERT INTO `aiwaypoints` VALUES (55, 30, -1366.28, -231.521, 98.4241, '', '奥山BL将军点');
INSERT INTO `aiwaypoints` VALUES (56, 30, -252.194, -291.924, 6.67758, '', '奥山中心点');
INSERT INTO `aiwaypoints` VALUES (57, 30, 795.509, -493.479, 99.7655, '', '奥山LM开始点');
INSERT INTO `aiwaypoints` VALUES (58, 30, -1387.45, -550.928, 54.9859, '', '奥山BL开始点');
INSERT INTO `aiwaypoints` VALUES (59, 628, 299.652, -785.527, 49.5924, '', '征服之岛LM城堡墓地');
INSERT INTO `aiwaypoints` VALUES (60, 628, 397.03, -859.237, 49.3704, '', '征服之岛LM城堡传送1');
INSERT INTO `aiwaypoints` VALUES (61, 628, 425.63, -856.905, 48.9807, '', '征服之岛LM城堡外传送1');
INSERT INTO `aiwaypoints` VALUES (62, 628, 776.382, -803.496, 6.4213, '', '征服之岛车间墓地');
INSERT INTO `aiwaypoints` VALUES (63, 628, 726.47, -360.966, 17.8253, '', '征服之岛码头墓地');
INSERT INTO `aiwaypoints` VALUES (64, 628, 807.491, -1000.85, 132.391, '', '征服之岛飞艇墓地');
INSERT INTO `aiwaypoints` VALUES (65, 628, 1142.98, -779.294, 49.1, '', '征服之岛BL城堡外传送1');
INSERT INTO `aiwaypoints` VALUES (66, 628, 1159.08, -746.338, 49.0988, '', '征服之岛BL城堡传送1');
INSERT INTO `aiwaypoints` VALUES (67, 628, 1283.86, -705.834, 48.9248, '', '征服之岛BL城堡墓地');
INSERT INTO `aiwaypoints` VALUES (68, 628, 393.072, -833.883, 48.6395, '', '征服之岛LM开始点');
INSERT INTO `aiwaypoints` VALUES (69, 628, 1166.72, -763.092, 48.6384, '', '征服之岛BL开始点');
INSERT INTO `aiwaypoints` VALUES (70, 628, 443.388, -832.336, 44.0983, '', '征服之岛LM阵地战开始点');
INSERT INTO `aiwaypoints` VALUES (71, 628, 1119.95, -761.947, 47.8879, '', '征服之岛BL阵地战开始点');
INSERT INTO `aiwaypoints` VALUES (72, 617, 1255.58, 766.713, 3.15722, '', '达拉然竞技场联盟点');
INSERT INTO `aiwaypoints` VALUES (73, 617, 1328.29, 814.895, 3.16107, '', '达拉然竞技场部落点');

SET FOREIGN_KEY_CHECKS = 1;
