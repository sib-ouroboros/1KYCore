-- Quest 24679: spell 72853 (item 51956) requires spell focus 1643.
-- Restore the invisible focus at the tomb measured in the client. No NPC AI changes.
-- Always-visible phasing keeps the inert focus accessible across the player's Gilneas story phases.
INSERT INTO gameobject
(guid,id,map,zoneId,areaId,spawnDifficulties,phaseUseFlags,PhaseId,PhaseGroup,terrainSwapMap,
 position_x,position_y,position_z,orientation,rotation0,rotation1,rotation2,rotation3,
 spawntimesecs,animprogress,state,isActive,ScriptName,VerifiedBuild)
SELECT (SELECT COALESCE(MAX(guid),0)+1 FROM gameobject),201964,654,4714,0,'0',1,0,0,-1,
 -1621.367188,1897.508057,20.0,0,0,0,0,1,300,0,1,0,'',0
WHERE EXISTS (SELECT 1 FROM gameobject_template WHERE entry=201964 AND type=8 AND Data0=1643 AND Data1>=10)
 AND NOT EXISTS (SELECT 1 FROM gameobject g JOIN gameobject_template t ON t.entry=g.id
 WHERE g.map=654 AND t.type=8 AND t.Data0=1643
 AND ABS(g.position_x+1621.367188)<1 AND ABS(g.position_y-1897.508057)<1
 AND ABS(g.position_z-20.0)<1 AND g.PhaseId=0 AND g.PhaseGroup=0 AND (g.phaseUseFlags & 1)=1);

