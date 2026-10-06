-- Restore only the missing native group, without replacing administrator texts.
-- Pinned JadeCore 380bfface3da0198e5c29004b1d9d2a3ab7b133d, 2016_09_01_02.
-- Sound19631 from the Cataclysm source is not imported without Legion validation.
INSERT INTO creature_text (CreatureID,GroupID,ID,Text,Type,Language,Probability,Emote,Duration,Sound,BroadcastTextId,TextRange,comment)
SELECT 37875,0,0,'No...i''d sooner die than have one of your kind for a king!',12,0,100,0,0,0,0,0,'Gilneas: Godfrey answer to Genn'
FROM creature_template godfrey JOIN creature_template genn ON genn.entry=37876
WHERE godfrey.entry=37875 AND godfrey.AIName='' AND godfrey.ScriptName='npc_gilneas_godfrey_departure'
 AND genn.AIName='' AND genn.ScriptName='npc_king_genn_greymane_37876'
 AND NOT EXISTS (SELECT 1 FROM creature_text existing WHERE existing.CreatureID=37875 AND existing.GroupID=0);
