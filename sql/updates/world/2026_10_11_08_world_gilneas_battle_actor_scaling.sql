-- Supply missing Legion level scaling for the native Gilneas battle actors.
-- Preserve boss health, abilities, damage modifiers, admin scaling and other-map templates.
-- Some roles (including Gorerot) are summoned only, so no persistent spawn is required.
INSERT INTO creature_template_scaling
 (Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax,VerifiedBuild)
SELECT ct.entry,ct.minlevel,ct.maxlevel,0,0,0 FROM creature_template ct
WHERE ct.minlevel=5 AND ct.maxlevel=20 AND ct.DamageModifier=1
 AND ((ct.entry=38210 AND ct.ScriptName='npc_forsaken_crossbowman_38210')
 OR (ct.entry=38218 AND ct.ScriptName='npc_prince_liam_greymane_38218')
 OR (ct.entry=38221 AND ct.ScriptName='npc_gilnean_militia_38221')
 OR (ct.entry=38331 AND ct.ScriptName='npc_gorerot_38331')
 OR (ct.entry=38415 AND ct.ScriptName='npc_lord_darius_crowley_38415')
 OR (ct.entry=38420 AND ct.ScriptName='npc_vile_abomination_38420')
 OR (ct.entry=38426 AND ct.ScriptName='npc_lorna_crowley_38426')
 OR (ct.entry=38464 AND ct.ScriptName='npc_dark_ranger_elite_38464')
 OR (ct.entry=38465 AND ct.ScriptName='npc_myriam_spellwaker_38465')
 OR (ct.entry=38466 AND ct.ScriptName='npc_sister_almyra_38466'))
 AND NOT EXISTS (SELECT 1 FROM creature c WHERE c.id=ct.entry AND c.map<>654)
ON DUPLICATE KEY UPDATE Entry=creature_template_scaling.Entry;
