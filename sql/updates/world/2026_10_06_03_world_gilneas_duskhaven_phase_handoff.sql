-- 14396 accepts phase183 before it is rewarded. The phase182 end mask is74.
-- Restore only the Gilneas rows; the same spell is used by Draenor quest chains.
UPDATE `spell_area` SET `quest_start_status`=74
WHERE `spell`=68483 AND `area` IN (4714,4786,4792,4793,4806,4807,4808,4817,4818,5720)
    AND `quest_start`=14396 AND `quest_end` IN (14465,24438)
    AND `quest_start_status`=64 AND `quest_end_status`=64
    AND `aura_spell`=0 AND `teamId`=-1 AND `racemask`=0 AND `gender`=2 AND `flags`=3;
UPDATE `creature_template` SET `AIName`='', `ScriptName`='npc_lord_godfrey_36290'
WHERE `entry`=36290 AND `ScriptName` IN ('','npc_lord_godfrey_36290');
