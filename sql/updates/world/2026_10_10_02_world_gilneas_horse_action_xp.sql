-- 14416: VehicleSpellInitialize reads creature spell slots. The native horse
-- has Vehicle527 but an empty action slot; binding a SpellScript alone is insufficient.
UPDATE creature_template SET spell1=68903
WHERE entry=36540 AND VehicleId=527 AND spell1=0 AND AIName=''
 AND ScriptName='npc_mountain_horse_36540';

-- 14154: bit0x40 explicitly suppresses the engine's standard kill XP.
-- Remove only that bit for the four audited rooftop attackers; no scripted XP.
-- Preserve other flags, loot tagging and player damage contribution requirements.
UPDATE creature_template ct SET ct.flags_extra=ct.flags_extra & ~64
WHERE ct.minlevel=3 AND ct.maxlevel=4 AND ct.faction=2179 AND (
 (ct.entry=35188 AND ct.ScriptName='npc_worgen_runt_35188')
 OR (ct.entry=35456 AND ct.ScriptName='npc_worgen_runt_35456')
 OR (ct.entry=35170 AND ct.ScriptName='npc_worgen_alpha_35170')
 OR (ct.entry=35167 AND ct.ScriptName='npc_worgen_alpha_35167'))
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654);
