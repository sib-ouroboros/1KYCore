-- Quest26706: enforce ship readiness on the actual harbor click spell.
INSERT INTO spell_script_names(spell_id,ScriptName)
SELECT 81877,'spell_gilneas_endgame_hippogryph'
WHERE EXISTS(SELECT 1 FROM creature_template WHERE entry=43749 AND AIName='' AND ScriptName='npc_tobias_mistmantle_43749')
 AND NOT EXISTS(SELECT 1 FROM spell_script_names WHERE spell_id=81877 AND ScriptName='spell_gilneas_endgame_hippogryph');
