-- Quest24920: clickable source summons a personal flight vehicle, not a ground mount.
UPDATE creature_template SET VehicleId=0,npcflag=npcflag | 16777216
WHERE entry=38615 AND AIName='' AND ScriptName='' AND VehicleId IN (0,641);
UPDATE npc_spellclick_spells SET cast_flags=cast_flags | 1
WHERE npc_entry=38615 AND spell_id=72472 AND cast_flags IN (0,1)
 AND EXISTS (SELECT 1 FROM creature_template WHERE entry=38615 AND AIName='' AND ScriptName='');
UPDATE creature_template SET VehicleId=641,spell1=72246,spell5=72849
WHERE entry=38540 AND AIName='' AND ScriptName='npc_captured_riding_bat_38540'
 AND VehicleId IN (0,641) AND spell1 IN (0,72246) AND spell5 IN (0,72849);
INSERT INTO spell_script_names (spell_id,ScriptName)
SELECT 72472,'spell_gilneas_captured_bat_summon'
WHERE NOT EXISTS (SELECT 1 FROM spell_script_names WHERE spell_id=72472 AND ScriptName='spell_gilneas_captured_bat_summon');
INSERT INTO spell_script_names (spell_id,ScriptName)
SELECT 72849,'spell_fly_back_72849'
WHERE NOT EXISTS (SELECT 1 FROM spell_script_names WHERE spell_id=72849 AND ScriptName='spell_fly_back_72849');
