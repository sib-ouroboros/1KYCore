-- Quest 24681: restore a directly boardable glaive thrower in Keel Harbor.
-- Vehicle 447 is the existing single-driver glaive configuration (seat 4806).
UPDATE creature_template SET VehicleId=447,npcflag=npcflag | 16777216,minlevel=5,maxlevel=20
WHERE entry=37927 AND AIName='' AND ScriptName='' AND VehicleId IN (0,447)
 AND spell1=70735 AND spell2=70732 AND spell4=59737 AND minlevel IN (1,5) AND maxlevel IN (1,20);
-- The old click spell summons another unconfigured copy; use native vehicle boarding instead.
DELETE FROM npc_spellclick_spells
WHERE npc_entry=37927 AND spell_id=71238 AND cast_flags=1 AND user_type=0
 AND EXISTS (SELECT 1 FROM creature_template WHERE entry=37927 AND VehicleId=447 AND ScriptName='' AND AIName='');
INSERT INTO npc_spellclick_spells(npc_entry,spell_id,cast_flags,user_type)
SELECT 37927,46598,1,0 WHERE NOT EXISTS(SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=37927)
 AND EXISTS(SELECT 1 FROM creature_template WHERE entry=37927 AND VehicleId=447 AND ScriptName='' AND AIName='');
INSERT INTO creature
(guid,id,map,zoneId,areaId,spawnDifficulties,phaseUseFlags,PhaseId,PhaseGroup,terrainSwapMap,
 position_x,position_y,position_z,orientation,spawntimesecs,spawndist,MovementType,ScriptName)
SELECT (SELECT COALESCE(MAX(guid),0)+1 FROM creature),37927,654,4714,4726,'0',0,189,0,-1,
 -1322.3,2117.34,5.71432,3.15905,90,0,0,''
WHERE EXISTS(SELECT 1 FROM creature WHERE guid=804189 AND id=38149 AND map=654 AND PhaseId=189
 AND ABS(position_x+1322.3)<1 AND ABS(position_y-2120.34)<1)
 AND EXISTS(SELECT 1 FROM creature_template WHERE entry=37927 AND VehicleId=447 AND ScriptName='' AND AIName='')
 AND NOT EXISTS(SELECT 1 FROM creature WHERE id=37927 AND map=654 AND PhaseId=189 AND PhaseGroup=0);
-- Accessories are rejected by ObjectMgr without a spellclick row, even for NPC-only mounts.
INSERT INTO npc_spellclick_spells(npc_entry,spell_id,cast_flags,user_type)
SELECT 37939,46598,1,0 WHERE NOT EXISTS(SELECT 1 FROM npc_spellclick_spells WHERE npc_entry=37939)
 AND EXISTS(SELECT 1 FROM creature_template WHERE entry=37939 AND VehicleId=429 AND AIName='' AND ScriptName='');
-- Summon type 0 is invalid and immediately despawns. Preserve the native rider-after-wolf-death behavior.
UPDATE vehicle_template_accessory SET summontype=7
WHERE entry=37939 AND accessory_entry=37938 AND seat_id=0 AND minion=0 AND summontype=0 AND summontimer=0;
-- Missing Legion scaling currently randomizes each spawn to a level between 5 and 20.
INSERT INTO creature_template_scaling
(Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT entry,5,20,0,0,0 FROM creature_template ct
WHERE entry IN (37884,37885,37916,37921,37938,37939,37927) AND minlevel=5 AND maxlevel=20
 AND ScriptName='' AND AIName IN ('','SmartAI')
 AND NOT EXISTS(SELECT 1 FROM creature_template_scaling s WHERE s.Entry=ct.entry);

