-- Exodus24438: coordinate-only captured route, native nested vehicles.
-- Reject foreign routes, bindings, seats and click handlers before any permanent write.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_coach_route`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_coach_route` LIKE `waypoint_data`;
INSERT INTO `_1kycore_gilneas_coach_route`
(`id`,`point`,`position_x`,`position_y`,`position_z`,`orientation`,`delay`,`move_type`,`action`,`action_chance`,`wpguid`) VALUES
(4492801,1,-1681.45,2508.27,97.84,0,0,1,0,100,0),
(4492801,2,-1695.46,2486.82,92.64,0,0,1,0,100,0),
(4492801,3,-1704.99,2468.26,84.84,0,0,1,0,100,0),
(4492801,4,-1698.38,2447.65,80.77,0,0,1,0,100,0),
(4492801,5,-1698.42,2432.73,76.52,0,0,1,0,100,0),
(4492801,6,-1725.88,2390.5,60.8,0,0,1,0,100,0),
(4492801,7,-1735.64,2362.27,63.15,0,0,1,0,100,0),
(4492801,8,-1745.18,2343.69,67.34,0,0,1,0,100,0),
(4492801,9,-1746.53,2329.92,69.6,0,0,1,0,100,0),
(4492801,10,-1757.21,2300.38,75.77,0,0,1,0,100,0),
(4492801,11,-1776.38,2271.8,82.11,0,0,1,0,100,0),
(4492801,12,-1799.38,2251.48,87.64,0,0,1,0,100,0),
(4492801,13,-1826.19,2238.05,89.31,0,0,1,0,100,0),
(4492801,14,-1868.5,2174.6,89.31,0,0,1,0,100,0),
(4492801,15,-1872.45,2135.71,89.31,0,0,1,0,100,0),
(4492801,16,-1872.96,2075.18,89.31,0,0,1,0,100,0),
(4492801,17,-1881.14,2046.58,89.31,0,0,1,0,100,0),
(4492801,18,-1885.72,2019.56,89.31,0,0,1,0,100,0),
(4492801,19,-1876.85,1970.16,89.17,0,0,1,0,100,0),
(4492801,20,-1878.35,1921.33,89.13,0,0,1,0,100,0),
(4492801,21,-1890.52,1904.26,89.15,0,0,1,0,100,0),
(4492801,22,-1990.23,1901.42,89.28,0,0,1,0,100,0),
(4492801,23,-2036.81,1914.56,83.23,0,0,1,0,100,0),
(4492801,24,-2061.07,1905.41,73.95,0,0,1,0,100,0),
(4492801,25,-2093.23,1881.99,53.77,0,0,1,0,100,0),
(4492801,26,-2103.06,1870.42,46.52,0,0,1,0,100,0),
(4492801,27,-2122.61,1831.95,29.18,0,0,1,0,100,0),
(4492801,28,-2146.32,1814.97,19.03,0,0,1,0,100,0),
(4492801,29,-2186.33,1808.11,12.11,0,0,1,0,100,0),
(4492801,30,-2217.77,1809.6,11.78,0,0,1,0,100,0),
(4492801,31,-2239.38,1805.1,11.94,0,0,1,0,100,0),
(4492801,32,-2310.3,1774.33,11.05,0,0,1,0,100,0),
(4492801,33,-2376.5,1704.52,11.15,0,0,1,0,100,0);
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_coach_guard`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_coach_guard` (`ok` INT NOT NULL);
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM waypoint_data d
LEFT JOIN `_1kycore_gilneas_coach_route` s ON s.id=d.id AND s.point=d.point
WHERE d.id=4492801 AND (s.point IS NULL OR ABS(d.position_x-s.position_x)>0.01
OR ABS(d.position_y-s.position_y)>0.01 OR ABS(d.position_z-s.position_z)>0.01
OR d.orientation<>0 OR d.delay<>0 OR d.move_type<>1 OR d.action<>0 OR d.action_chance<>100 OR d.wpguid<>0) LIMIT 1;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM creature_template
WHERE (entry=43336 AND (VehicleId<>958 OR AIName<>'' OR ScriptName NOT IN ('','npc_harness_43336')))
OR (entry=43337 AND (VehicleId<>959 OR AIName<>'' OR ScriptName NOT IN ('','npc_stagecoach_carriage_43337')))
OR (entry=44928 AND (VehicleId<>959 OR AIName<>'' OR ScriptName NOT IN ('','npc_stagecoach_carriage_44928')))
OR (entry=38755 AND VehicleId<>970) LIMIT 1;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM npc_spellclick_spells
WHERE npc_entry IN (38755,43336,43337,44928)
AND NOT ((spell_id=46598 AND cast_flags=1 AND user_type=0)
OR (npc_entry IN (38755,44928) AND spell_id=72767 AND cast_flags=0 AND user_type=0)) LIMIT 1;
-- The only accepted legacy passenger-seat occupant is the release's Marie.
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM vehicle_template_accessory
WHERE entry IN (43337,44928) AND ((seat_id IN (0,1) AND accessory_entry<>38853)
OR (seat_id=0 AND EXISTS (SELECT 1 FROM vehicle_template_accessory legacy WHERE legacy.entry=vehicle_template_accessory.entry AND legacy.seat_id=1))) LIMIT 1;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM vehicle_template_accessory
WHERE (entry=38755 AND seat_id=2 AND accessory_entry<>44928)
OR (entry=43336 AND seat_id=2 AND accessory_entry<>43337) LIMIT 1;
-- Existing horse and family passengers must match the captured composition.
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM vehicle_template_accessory
WHERE (entry IN (38755,43336) AND seat_id IN (0,1) AND accessory_entry<>43338)
OR (entry IN (43337,44928) AND ((seat_id=2 AND accessory_entry<>44460)
OR (seat_id=3 AND accessory_entry<>36138) OR (seat_id=4 AND accessory_entry<>43907)
OR (seat_id=5 AND accessory_entry NOT IN (37946,43907)) OR (seat_id=6 AND accessory_entry<>51409))) LIMIT 1;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM DUAL
WHERE (SELECT COUNT(*) FROM creature_template WHERE entry IN (38755,43336,43337,44928,43338,38853,44460,36138,43907,37946,51409))<>11;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM creature_template
WHERE entry=38755 AND (AIName<>'' OR ScriptName<>'') LIMIT 1;
INSERT INTO `_1kycore_gilneas_coach_guard` SELECT NULL FROM vehicle_template_accessory
WHERE (entry IN (38755,43336) AND seat_id NOT IN (0,1,2))
OR (entry IN (43337,44928) AND seat_id NOT IN (0,1,2,3,4,5,6)) LIMIT 1;
-- All guards above run before the first permanent mutation.
INSERT INTO waypoint_data SELECT s.* FROM `_1kycore_gilneas_coach_route` s
LEFT JOIN waypoint_data d ON d.id=s.id AND d.point=s.point WHERE d.id IS NULL;
UPDATE vehicle_template_accessory SET seat_id=0
WHERE entry IN (43337,44928) AND seat_id=1 AND accessory_entry=38853;
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 38755,43338,0,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=38755 AND seat_id=0);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 38755,43338,1,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=38755 AND seat_id=1);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 38755,44928,2,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=38755 AND seat_id=2);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43336,43338,0,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43336 AND seat_id=0);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43336,43338,1,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43336 AND seat_id=1);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43336,43337,2,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43336 AND seat_id=2);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,38853,0,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=0);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,44460,2,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=2);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,36138,3,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=3);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,43907,4,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=4);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,37946,5,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=5);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 43337,51409,6,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=43337 AND seat_id=6);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,38853,0,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=0);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,44460,2,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=2);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,36138,3,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=3);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,43907,4,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=4);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,37946,5,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=5);
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer) SELECT 44928,51409,6,1,'Gilneas Exodus native accessory',8,0 WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=44928 AND seat_id=6);
-- Convert only the known legacy zero-type accessories to native manual lifetime.
UPDATE vehicle_template_accessory SET minion=1,summontype=8
WHERE entry IN (38755,43336,43337,44928) AND minion=0 AND summontype=0 AND summontimer=0;
-- Old72767 summoned another harness during accessory installation. Gossip now
-- creates exactly one private harness; accessory clicks must only mount.
DELETE FROM npc_spellclick_spells WHERE npc_entry IN (38755,44928) AND spell_id=72767 AND cast_flags=0 AND user_type=0;
INSERT INTO npc_spellclick_spells (npc_entry,spell_id,cast_flags,user_type) SELECT 38755,46598,1,0 WHERE NOT EXISTS (SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=38755 AND spell_id=46598);
INSERT INTO npc_spellclick_spells (npc_entry,spell_id,cast_flags,user_type) SELECT 43336,46598,1,0 WHERE NOT EXISTS (SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=43336 AND spell_id=46598);
INSERT INTO npc_spellclick_spells (npc_entry,spell_id,cast_flags,user_type) SELECT 43337,46598,1,0 WHERE NOT EXISTS (SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=43337 AND spell_id=46598);
INSERT INTO npc_spellclick_spells (npc_entry,spell_id,cast_flags,user_type) SELECT 44928,46598,1,0 WHERE NOT EXISTS (SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=44928 AND spell_id=46598);
UPDATE creature_template SET ScriptName='npc_harness_43336' WHERE entry=43336 AND AIName='' AND ScriptName IN ('','npc_harness_43336');
UPDATE creature_template SET ScriptName='npc_stagecoach_carriage_43337' WHERE entry=43337 AND AIName='' AND ScriptName IN ('','npc_stagecoach_carriage_43337');
UPDATE creature_template SET ScriptName='npc_stagecoach_carriage_44928' WHERE entry=44928 AND AIName='' AND ScriptName IN ('','npc_stagecoach_carriage_44928');
UPDATE creature_template SET npcflag=npcflag|1 WHERE entry=44928 AND ScriptName='npc_stagecoach_carriage_44928';
DROP TEMPORARY TABLE `_1kycore_gilneas_coach_guard`;
DROP TEMPORARY TABLE `_1kycore_gilneas_coach_route`;
