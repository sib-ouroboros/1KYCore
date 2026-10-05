-- Coordinate-only route from the pinned source in gilneas-horse-route-source.json.
-- No historical quest/SmartAI updates. Reject conflicting administrator routes.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_horse_route`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_horse_route` LIKE `waypoint_data`;
INSERT INTO `_1kycore_gilneas_horse_route`
(`id`,`point`,`position_x`,`position_y`,`position_z`,`orientation`,`delay`,`move_type`,`action`,`action_chance`,`wpguid`) VALUES
(3674101,1,-1897.62,2255.62,42.32,0,0,1,0,100,0),
(3674101,2,-1890.28,2263.13,42.32,0,0,1,0,100,0),
(3674101,3,-1872.94,2280.44,42.2953,0,0,1,0,100,0),
(3674101,4,-1860.56,2292.81,42.3087,0,0,1,0,100,0),
(3674101,5,-1845.66,2307.61,40.6978,0,0,1,0,100,0),
(3674101,6,-1835.79,2317.54,38.6136,0,0,1,0,100,0),
(3674101,7,-1820.01,2331.38,36.485,0,0,1,0,100,0),
(3674101,8,-1813.89,2336.01,36.1204,0,0,1,0,100,0),
(3674101,9,-1802.57,2344.22,35.7727,0,0,1,0,100,0),
(3674101,10,-1791.23,2355.17,37.0379,0,0,1,0,100,0),
(3674101,11,-1784.84,2370.95,40.3052,0,0,1,0,100,0),
(3674101,12,-1782.62,2384.77,43.7825,0,0,1,0,100,0),
(3674101,13,-1781.17,2395.17,46.8268,0,0,1,0,100,0),
(3674101,14,-1780.4,2409.14,51.0919,0,0,1,0,100,0),
(3674101,15,-1779.14,2419.56,54.3815,0,0,1,0,100,0),
(3674101,16,-1776.97,2428.53,56.9944,0,0,1,0,100,0),
(3674101,17,-1772.51,2439.71,60.1307,0,0,1,0,100,0),
(3674101,18,-1768.21,2448.99,62.882,0,0,1,0,100,0),
(3674101,19,-1760.81,2459.4,66.8709,0,0,1,0,100,0),
(3674101,20,-1751.4,2463.61,70.1644,0,0,1,0,100,0),
(3674101,21,-1737.45,2464.72,74.6456,0,0,1,0,100,0),
(3674101,22,-1726.96,2465.04,77.8381,0,0,1,0,100,0),
(3674101,23,-1716.52,2466.09,81.0769,0,0,1,0,100,0),
(3674101,24,-1706.09,2470.13,85.1433,0,0,1,0,100,0),
(3674101,25,-1699.06,2480.35,89.8907,0,0,1,0,100,0),
(3674101,26,-1692.36,2492.64,94.831,0,0,1,0,100,0),
(3674101,27,-1684.2,2504.01,97.6016,0,0,1,0,100,0),
(3674101,28,-1670.86,2517.95,97.8954,0,0,1,0,100,0);
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_horse_guard`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_horse_guard` (`ok` INT NOT NULL);
INSERT INTO `_1kycore_gilneas_horse_guard` SELECT NULL FROM `waypoint_data` d
LEFT JOIN `_1kycore_gilneas_horse_route` s ON s.id=d.id AND s.point=d.point
WHERE d.id=3674101 AND (s.point IS NULL OR ABS(d.position_x-s.position_x)>0.01
OR ABS(d.position_y-s.position_y)>0.01 OR ABS(d.position_z-s.position_z)>0.01
OR d.orientation<>0 OR d.delay<>0 OR d.move_type<>1 OR d.action<>0 OR d.action_chance<>100 OR d.wpguid<>0) LIMIT 1;
INSERT INTO `waypoint_data` SELECT s.* FROM `_1kycore_gilneas_horse_route` s
LEFT JOIN `waypoint_data` d ON d.id=s.id AND d.point=s.point WHERE d.id IS NULL;
DROP TEMPORARY TABLE `_1kycore_gilneas_horse_guard`;
DROP TEMPORARY TABLE `_1kycore_gilneas_horse_route`;
UPDATE `creature_template` SET AIName='',ScriptName='npc_swift_mountain_horse_36741'
WHERE entry=36741 AND ScriptName IN ('','npc_swift_mountain_horse_36741');
UPDATE `creature_template` SET AIName='',ScriptName='npc_gwen_armstead_36452'
WHERE entry=36452 AND ScriptName IN ('','npc_gwen_armstead_36452');
UPDATE `creature_template` SET AIName='',ScriptName='npc_queen_mia_greymane_36606'
WHERE entry=36606 AND ScriptName IN ('','npc_queen_mia_greymane_36606');
-- Known native phase184 rule from audited Duskhaven part2. Limited to Gilneas.
INSERT INTO spell_area (spell,area,quest_start,quest_end,aura_spell,teamId,racemask,gender,flags,quest_start_status,quest_end_status)
SELECT 69077,a.area,14465,24438,0,-1,0,2,3,66,64 FROM (SELECT 4714 area UNION ALL SELECT 4817) a
WHERE NOT EXISTS (SELECT 1 FROM spell_area s WHERE s.spell=69077 AND s.area=a.area AND s.quest_start=14465);
