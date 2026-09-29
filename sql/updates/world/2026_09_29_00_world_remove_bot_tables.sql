-- Retired module tables only; accounts, characters and arena positions are retained.
DROP TABLE IF EXISTS `ai_playerbot_names`;
DROP TABLE IF EXISTS `ai_playerbot_locks`;

-- Match the retired route in full. Preserve any custom coordinates or descriptions.
CREATE TEMPORARY TABLE `tmp_1kycore_retired_siege_route` (
  `entry` int unsigned NOT NULL PRIMARY KEY,
  `map` int NOT NULL,
  `x` float NOT NULL, `y` float NOT NULL, `z` float NOT NULL,
  `link` varchar(128), `helpText` varchar(128)
) DEFAULT CHARACTER SET utf8;
INSERT INTO `tmp_1kycore_retired_siege_route` (`entry`, `map`, `x`, `y`, `z`, `link`, `helpText`) VALUES
(1000, 0, -9204.4, 466.6, 97.9, '', 'Hurlevent 01/30 - Route d Elwynn'),
(1001, 0, -9183.4, 416.5, 90.0, '', 'Hurlevent 02/30 - Route d Elwynn'),
(1002, 0, -9133.8, 387.3, 90.8, '', 'Hurlevent 03/30 - Route d Elwynn'),
(1003, 0, -9086.7, 420.5, 92.3, '', 'Hurlevent 04/30 - Route d Elwynn'),
(1004, 0, -9041.4, 452.0, 93.1, '', 'Hurlevent 05/30 - Route d Elwynn'),
(1005, 0, -8996.5, 487.4, 96.6, '', 'Hurlevent 06/30 - Route d Elwynn'),
(1006, 0, -8959.8, 529.1, 96.4, '', 'Hurlevent 07/30 - Route d Elwynn'),
(1007, 0, -8970.3, 555.1, 94.0, '', 'Hurlevent 08/30 - Route d Elwynn'),
(1008, 0, -8946.9, 560.4, 93.8, '', 'Hurlevent 09/30 - Route d Elwynn'),
(1009, 0, -8926.9, 541.9, 94.7, '', 'Hurlevent 10/30 - Route d Elwynn'),
(1010, 0, -8882.1, 580.2, 93.2, '', 'Hurlevent 11/30 - Route d Elwynn'),
(1011, 0, -8839.1, 614.8, 93.0, '', 'Hurlevent 12/30 - Porte de Hurlevent'),
(1012, 0, -8796.9, 647.5, 94.8, '', 'Hurlevent 13/30 - Porte de Hurlevent'),
(1013, 0, -8793.2, 676.0, 102.0, '', 'Hurlevent 14/30 - Porte de Hurlevent'),
(1014, 0, -8749.7, 690.6, 100.1, '', 'Hurlevent 15/30 - Place du Commerce'),
(1015, 0, -8711.7, 655.5, 99.4, '', 'Hurlevent 16/30 - Place du Commerce'),
(1016, 0, -8710.0, 598.6, 99.1, '', 'Hurlevent 17/30 - Place du Commerce'),
(1017, 0, -8745.6, 556.2, 97.7, '', 'Hurlevent 18/30 - Place du Commerce'),
(1018, 0, -8704.9, 527.9, 97.7, '', 'Hurlevent 19/30 - Place du Commerce'),
(1019, 0, -8656.6, 552.9, 97.1, '', 'Hurlevent 20/30 - Place du Commerce'),
(1020, 0, -8613.4, 514.2, 103.5, '', 'Hurlevent 21/30 - Place du Commerce'),
(1021, 0, -8571.8, 475.7, 104.8, '', 'Hurlevent 22/30 - Place du Commerce'),
(1022, 0, -8525.9, 440.9, 105.7, '', 'Hurlevent 23/30 - Quartier du Donjon'),
(1023, 0, -8484.3, 411.9, 115.7, '', 'Hurlevent 24/30 - Donjon, grand hall'),
(1024, 0, -8454.9, 419.4, 125.6, '', 'Hurlevent 25/30 - Donjon, grand hall'),
(1025, 0, -8436.1, 403.3, 132.3, '', 'Hurlevent 26/30 - Donjon, escalier'),
(1026, 0, -8439.5, 348.9, 136.0, '', 'Hurlevent 27/30 - Donjon, escalier'),
(1027, 0, -8435.1, 321.6, 145.1, '', 'Hurlevent 28/30 - Donjon, escalier'),
(1028, 0, -8397.9, 276.4, 152.2, '', 'Hurlevent 29/30 - Donjon, appartements royaux'),
(1029, 0, -8364.3, 234.1, 157.0, '', 'Hurlevent 30/30 - Donjon, appartements royaux');

DELETE actual FROM `aiwaypoints` actual
INNER JOIN `tmp_1kycore_retired_siege_route` retired
  ON actual.entry = retired.entry AND actual.map = retired.map
  AND actual.x = retired.x AND actual.y = retired.y AND actual.z = retired.z
  AND BINARY actual.link = BINARY retired.link
  AND BINARY actual.helpText = BINARY retired.helpText;
DROP TEMPORARY TABLE `tmp_1kycore_retired_siege_route`;
