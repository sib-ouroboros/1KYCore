-- Quest 24679: correct the focus restored by 2026_10_12_02 using new client measurements.
-- Keep the native 5-metre focus radius; only relocate the previously restored inert spawn.
UPDATE gameobject SET position_x=-1643.0,position_y=1904.0,position_z=30.0,areaId=4727
WHERE id=201964 AND map=654 AND phaseUseFlags=1 AND PhaseId=0 AND PhaseGroup=0
 AND ScriptName='' AND ABS(position_x+1621.367188)<1
 AND ABS(position_y-1897.508057)<1 AND ABS(position_z-20.0)<1;
INSERT INTO gameobject
(guid,id,map,zoneId,areaId,spawnDifficulties,phaseUseFlags,PhaseId,PhaseGroup,terrainSwapMap,
 position_x,position_y,position_z,orientation,rotation0,rotation1,rotation2,rotation3,
 spawntimesecs,animprogress,state,isActive,ScriptName,VerifiedBuild)
SELECT (SELECT COALESCE(MAX(guid),0)+1 FROM gameobject),201964,654,4714,4727,'0',1,0,0,-1,
 -1643.0,1904.0,30.0,0,0,0,0,1,300,0,1,0,'',0
WHERE EXISTS (SELECT 1 FROM gameobject_template WHERE entry=201964 AND type=8 AND Data0=1643 AND Data1>=10)
 AND NOT EXISTS (SELECT 1 FROM gameobject g JOIN gameobject_template t ON t.entry=g.id
 WHERE g.map=654 AND t.type=8 AND t.Data0=1643
 AND ABS(g.position_x+1643.0)<1 AND ABS(g.position_y-1904.0)<1
 AND ABS(g.position_z-30.0)<1 AND g.PhaseId=0 AND g.PhaseGroup=0 AND (g.phaseUseFlags & 1)=1);
