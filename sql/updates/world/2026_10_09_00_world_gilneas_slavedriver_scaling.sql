-- 37701 has release bounds 5..20 but no scaling row, allowing random level20.
-- Retain those Legion bounds with neutral delta; VerifiedBuild0 is not a sniff.
-- Do not modify shared templates outside Gilneas or existing custom scaling.
INSERT INTO creature_template_scaling
 (Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT ct.entry,ct.minlevel,ct.maxlevel,0,0,0
FROM creature_template ct
WHERE ct.entry=37701 AND ct.minlevel=5 AND ct.maxlevel=20 AND ct.faction=21
 AND ct.AIName='SmartAI' AND ct.ScriptName=''
 AND EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map=654)
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654)
 AND NOT EXISTS (SELECT 1 FROM creature_template_scaling s WHERE s.Entry=ct.entry);
