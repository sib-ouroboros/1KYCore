-- Own movement completion belongs to Godfrey, not Genn.
-- No invented route, text, phase, immunity or spawn changes.
UPDATE creature_template SET ScriptName='npc_gilneas_godfrey_departure'
WHERE entry=37875 AND AIName='' AND ScriptName IN ('','npc_gilneas_godfrey_departure');
