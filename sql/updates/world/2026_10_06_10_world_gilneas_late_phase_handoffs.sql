-- Persistent late story phases, audited against native quest graph and DB2 phase auras.
-- Scope to Gilneas, preserve unrelated/custom spell_area rules.
UPDATE spell_area SET quest_end=24676,quest_end_status=64
WHERE spell=69484 AND area IN (4714,4730,4731,4732,4734,4787,4788,4794,4817,4842)
AND quest_start=14467 AND quest_end=0 AND quest_start_status=64 AND quest_end_status=0
AND aura_spell=0 AND teamId=-1 AND racemask=0 AND gender=2 AND flags=3;
-- Reward24676 must precede187, otherwise Lorna vanishes before the turn-in.
INSERT INTO spell_area (spell,area,quest_start,quest_end,aura_spell,teamId,racemask,gender,flags,quest_start_status,quest_end_status)
SELECT s.spell,a.area,s.quest_start,s.quest_end,0,-1,0,2,3,s.start_mask,s.end_mask
FROM (SELECT 69485 spell,24676 quest_start,24903 quest_end,64 start_mask,74 end_mask
UNION ALL SELECT 70696,24903,24678,74,74
UNION ALL SELECT 69486,24678,24680,74,74
UNION ALL SELECT 70695,24680,14434,74,64) s
CROSS JOIN (SELECT 4714 area UNION ALL SELECT 4755) a
WHERE NOT EXISTS (SELECT 1 FROM spell_area d WHERE d.spell=s.spell AND d.area=a.area AND d.quest_start=s.quest_start);
-- Native PhaseGroup440 =186+187. Keep the turn-in/next-quest actors on both sides.
-- Only the two audited persistent spawns; no unphased NPC or duplicate spawn.
UPDATE creature SET PhaseId=0,PhaseGroup=440
WHERE map=654 AND PhaseId=186 AND PhaseGroup=0
AND ((guid=802508 AND id=37783) OR (guid=802514 AND id=38553));
UPDATE creature_template SET AIName='',ScriptName='npc_lorna_crowley_37783'
WHERE entry=37783 AND ScriptName IN ('','npc_lorna_crowley_37783');
