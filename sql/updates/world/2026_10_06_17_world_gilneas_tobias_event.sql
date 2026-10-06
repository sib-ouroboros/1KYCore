-- Existing objective-free 24902 must wait for the actual escort/dialogue event.
-- Preserve real objectives, custom quest scripts and alternate creature handlers.
UPDATE quest_template_addon AS qa
JOIN quest_template AS qt ON qt.ID=qa.ID
JOIN creature_template AS tobias ON tobias.entry=38507
JOIN creature_template AS sylvanas ON sylvanas.entry=38530
SET qa.SpecialFlags=qa.SpecialFlags | 2
WHERE qa.ID=24902 AND qt.QuestType=2 AND qa.SpecialFlags IN (0,2) AND qa.ScriptName=''
  AND tobias.AIName='' AND tobias.ScriptName='npc_tobias_mistmantle_38507'
  AND sylvanas.AIName='' AND sylvanas.ScriptName='npc_lady_sylvanas_windrunner_38530'
  AND NOT EXISTS (SELECT 1 FROM quest_objectives AS qo WHERE qo.QuestID=qa.ID);
