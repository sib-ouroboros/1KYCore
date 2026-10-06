-- Missing scaling made Creature::SelectLevel choose a random level5..20.
-- Restore the existing bounds with a neutral level delta; no claimed sniff build.
INSERT INTO creature_template_scaling (Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT ct.entry,ct.minlevel,ct.maxlevel,0,0,0 FROM creature_template ct
WHERE ct.entry=37757 AND ct.minlevel=5 AND ct.maxlevel=20
 AND ct.AIName='SmartAI' AND ct.ScriptName=''
 AND EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map=654)
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654)
 AND EXISTS (SELECT 1 FROM quest_objectives qo WHERE qo.QuestID=24627 AND qo.Type=0 AND qo.ObjectID=ct.entry AND qo.Amount=6)
 AND NOT EXISTS (SELECT 1 FROM creature_template_scaling existing WHERE existing.Entry=ct.entry);
