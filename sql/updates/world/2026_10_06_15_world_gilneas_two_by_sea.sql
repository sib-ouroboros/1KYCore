-- Two By Sea14382: player control seat0, machinist accessory seat2 (Vehicle516).
-- Fail before permanent writes if an administrator installed different handlers.
DROP TEMPORARY TABLE IF EXISTS `_1kycore_gilneas_catapult_guard`;
CREATE TEMPORARY TABLE `_1kycore_gilneas_catapult_guard` (`ok` INT NOT NULL);
INSERT INTO `_1kycore_gilneas_catapult_guard` SELECT NULL
WHERE NOT EXISTS (SELECT 1 FROM creature_template WHERE entry=36283 AND VehicleId=516
 AND spell1=68659 AND AIName='' AND ScriptName IN ('','npc_forsaken_catapult_36283'));
INSERT INTO `_1kycore_gilneas_catapult_guard` SELECT NULL FROM vehicle_template_accessory
WHERE entry=36283 AND (accessory_entry<>36292 OR seat_id<>2 OR minion<>0
 OR summontype NOT IN (0,7) OR summontimer<>0);
INSERT INTO `_1kycore_gilneas_catapult_guard` SELECT NULL FROM npc_spellclick_spells
WHERE npc_entry=36283 AND (spell_id<>69434 OR cast_flags NOT IN (0,1) OR user_type<>0);
UPDATE creature_template SET ScriptName='npc_forsaken_catapult_36283' WHERE entry=36283;
INSERT INTO vehicle_template_accessory (entry,accessory_entry,seat_id,minion,description,summontype,summontimer)
SELECT 36283,36292,2,0,'Gilneas catapult machinist',7,0
WHERE NOT EXISTS (SELECT 1 FROM vehicle_template_accessory WHERE entry=36283);
UPDATE vehicle_template_accessory SET summontype=7 WHERE entry=36283 AND accessory_entry=36292 AND seat_id=2;
INSERT INTO npc_spellclick_spells (npc_entry,spell_id,cast_flags,user_type)
SELECT 36283,69434,1,0 WHERE NOT EXISTS (SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=36283);
UPDATE npc_spellclick_spells SET cast_flags=1 WHERE npc_entry=36283 AND spell_id=69434;
INSERT INTO spell_script_names (spell_id,ScriptName)
SELECT 68659,'spell_launch_68659' WHERE NOT EXISTS
 (SELECT 1 FROM spell_script_names WHERE spell_id=68659 AND ScriptName='spell_launch_68659');
DROP TEMPORARY TABLE `_1kycore_gilneas_catapult_guard`;
