-- These persistent phase186 actors belong to the Introductions Are in Order scene (24472).
-- Liam already grants detection84481 during the scene and removes it afterwards.
-- Client SpellEffect confirms 80852 is invisibility18 and 84481 detects that same type.
-- Preserve the actual actors, phases, faction, combat flags, paths and existing addon data.
INSERT INTO creature_addon (guid,auras)
SELECT c.guid,'80852' FROM creature c
WHERE c.map=654 AND c.PhaseId=186 AND c.PhaseGroup=0
 AND ((c.guid BETWEEN 802085 AND 802112 AND c.id=37805)
   OR (c.guid=802086 AND c.id=37807) OR (c.guid=802087 AND c.id=37806)
   OR (c.guid=802103 AND c.id=37808))
 AND c.position_x BETWEEN -2190 AND -2170 AND c.position_y BETWEEN 1800 AND 1825
 AND NOT EXISTS (SELECT 1 FROM creature_template_addon a WHERE a.entry=c.id)
ON DUPLICATE KEY UPDATE auras=IF(CONCAT(' ',COALESCE(creature_addon.auras,''),' ') LIKE '% 80852 %',
 creature_addon.auras,TRIM(CONCAT(COALESCE(creature_addon.auras,''),' 80852')));
