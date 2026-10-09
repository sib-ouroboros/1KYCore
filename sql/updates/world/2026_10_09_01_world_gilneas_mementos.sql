-- Quest24602: sourced Disturbed Soil positions, native item49921 x5.
-- Source SHA2560265cc795b6507f8918162293e7c905143cdb2ef227ee72179bb43bcf889f68c.
-- 17 unique positions; source duplicates/legacy phaseMask are NOT imported.
-- Phase188 follows the existing native questgiver. Identity quaternion for o=0.
-- All-or-none missing population insert: preserve custom spawns/GUIDs/templates/loot.
INSERT INTO gameobject (guid,id,map,zoneId,areaId,spawnDifficulties,phaseUseFlags,
 PhaseId,PhaseGroup,terrainSwapMap,position_x,position_y,position_z,orientation,
 rotation0,rotation1,rotation2,rotation3,spawntimesecs,animprogress,state,isActive,ScriptName,VerifiedBuild)
SELECT p.guid,201871,654,p.zone,p.area,'0',0,188,0,-1,p.x,p.y,p.z,0,
 0,0,0,1,300,255,1,0,'',0
FROM (
SELECT 310065200 guid,4714 zone,4727 area,-1708.87 x,1970.5 y,30.077 z
UNION ALL
SELECT 310065201 guid,4714 zone,4727 area,-1649.55 x,1834.94 y,4.67572 z
UNION ALL
SELECT 310065202 guid,4714 zone,4727 area,-1671.58 x,1910.84 y,30.1048 z
UNION ALL
SELECT 310065203 guid,4714 zone,4727 area,-1715.45 x,1928.21 y,21.0419 z
UNION ALL
SELECT 310065204 guid,4714 zone,4727 area,-1668.23 x,1926.97 y,29.37 z
UNION ALL
SELECT 310065205 guid,4714 zone,4727 area,-1656.87 x,1942.22 y,28.7851 z
UNION ALL
SELECT 310065206 guid,4714 zone,4727 area,-1670.88 x,1965.61 y,23.5595 z
UNION ALL
SELECT 310065207 guid,4714 zone,4727 area,-1597.41 x,1903.84 y,13.2749 z
UNION ALL
SELECT 310065208 guid,4714 zone,4727 area,-1578.16 x,1887.74 y,6.25989 z
UNION ALL
SELECT 310065209 guid,4714 zone,4727 area,-1552.21 x,1901.93 y,4.65225 z
UNION ALL
SELECT 310065210 guid,4714 zone,4727 area,-1548.97 x,1927.64 y,4.54196 z
UNION ALL
SELECT 310065211 guid,4714 zone,4727 area,-1615.96 x,1831.83 y,5.21441 z
UNION ALL
SELECT 310065212 guid,4714 zone,4727 area,-1651.92 x,1967.34 y,23.5357 z
UNION ALL
SELECT 310065213 guid,4714 zone,4727 area,-1655.8 x,1999.02 y,27.4704 z
UNION ALL
SELECT 310065214 guid,4714 zone,4727 area,-1568.16 x,1857.54 y,4.01089 z
UNION ALL
SELECT 310065215 guid,4714 zone,4727 area,-1583.5 x,1977.01 y,7.61991 z
UNION ALL
SELECT 310065216 guid,4714 zone,4727 area,-1671.04 x,1829.54 y,6.48764 z
) p
WHERE NOT EXISTS (SELECT 1 FROM gameobject existing WHERE existing.id=201871 AND existing.map=654)
 AND NOT EXISTS (SELECT 1 FROM gameobject conflict WHERE conflict.guid BETWEEN 310065200 AND 310065216)
 AND EXISTS (SELECT 1 FROM gameobject_template gt WHERE gt.entry=201871 AND gt.type=3
  AND gt.displayId=49 AND gt.Data0=43 AND gt.Data1=201871 AND gt.Data17=0 AND gt.ScriptName='')
 AND EXISTS (SELECT 1 FROM gameobject_loot_template l WHERE l.Entry=201871 AND l.Item=49921
  AND l.Chance=100 AND l.QuestRequired=1 AND l.Reference=0)
 AND EXISTS (SELECT 1 FROM quest_objectives q WHERE q.QuestID=24602 AND q.Type=1 AND q.ObjectID=49921 AND q.Amount=5)
 AND EXISTS (SELECT 1 FROM creature c JOIN creature_queststarter qs ON qs.id=c.id
  WHERE c.guid=803966 AND c.id=38144 AND c.map=654 AND c.PhaseId=188 AND c.PhaseGroup=0 AND qs.quest=24602);
