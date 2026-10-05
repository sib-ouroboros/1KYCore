-- Native item49240/spell68682 summons36409; no alternate summon/linked-spell path.
UPDATE creature_template SET AIName='',ScriptName='npc_mastiff_36409'
WHERE entry=36409 AND ScriptName IN ('','npc_mastiff_36409');
UPDATE creature_template SET AIName='',ScriptName='npc_mastiff_36405'
WHERE entry=36405 AND ScriptName IN ('','npc_mastiff_36405');
-- A historical workaround used a quest ID as a creature kill credit. Fix only that value.
UPDATE creature_template SET KillCredit1=0 WHERE entry=36312 AND KillCredit1=14386;
INSERT INTO spell_script_names (spell_id,ScriptName)
SELECT 68682,'spell_gilneas_leader_of_the_pack' WHERE NOT EXISTS
(SELECT 1 FROM spell_script_names WHERE spell_id=68682 AND ScriptName='spell_gilneas_leader_of_the_pack');
