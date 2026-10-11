-- Mount only the stationary Duskhaven Gwen spawn on the local mountain horse (display 229).
-- Preserve coordinates, quest behavior and any existing custom mount/addon fields.
INSERT INTO creature_addon (guid,mount)
SELECT c.guid,229 FROM creature c
WHERE c.guid=801805 AND c.id=36452 AND c.map=654 AND c.PhaseId=183 AND c.PhaseGroup=0
 AND ABS(c.position_x-(-1901.85))<0.05 AND ABS(c.position_y-2255.92)<0.05
 AND NOT EXISTS (SELECT 1 FROM creature_template_addon a WHERE a.entry=c.id)
 AND EXISTS (SELECT 1 FROM creature_template ct WHERE ct.entry=36540 AND ct.modelid1=229)
ON DUPLICATE KEY UPDATE mount=IF(creature_addon.mount=0,229,creature_addon.mount);
