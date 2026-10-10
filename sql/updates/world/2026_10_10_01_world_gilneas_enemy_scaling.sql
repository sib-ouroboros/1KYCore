-- Restore missing Legion scaling for audited native Gilneas-only enemies.
-- Bounds and all health/armor/damage/XP/ability modifiers are preserved.
-- Existing administrator scaling and templates shared with other maps are retained.
-- See docs/audit-data/gilneas-expanded-release-audit.json (release baseline).
INSERT INTO creature_template_scaling
 (Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT ct.entry,ct.minlevel,ct.maxlevel,0,0,0 FROM creature_template ct
WHERE ct.minlevel=5 AND ct.maxlevel=20 AND (
 (ct.entry=36488 AND ct.faction=83 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37685 AND ct.faction=118 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37686 AND ct.faction=118 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37692 AND ct.faction=83 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37716 AND ct.faction=1924 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37718 AND ct.faction=1924 AND ABS(ct.HealthModifier-0.5)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37733 AND ct.faction=1924 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=37735 AND ct.faction=1924 AND ABS(ct.HealthModifier-1.2)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=38022 AND ct.faction=2213 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=38210 AND ct.faction=2213 AND ABS(ct.HealthModifier-1)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 OR (ct.entry=38420 AND ct.faction=2201 AND ABS(ct.HealthModifier-5)<0.0001 AND ABS(ct.DamageModifier-1)<0.0001)
 )
 AND EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map=654)
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654)
ON DUPLICATE KEY UPDATE Entry=creature_template_scaling.Entry;
