-- Rescue68219 is cast by the charmer, forces68228, which summons35907.
-- IsSummonedBy forwards that player as the JUST_SUMMONED action invoker.
-- Select that invoker's vehicle, never the nearest other player's horse.
-- 84275 requests passenger seat2; retain the existing SmartAI horse route.
UPDATE smart_scripts s
SET s.event_type=54,s.action_param1=84275,s.target_type=22,
    s.target_param1=0,s.target_param2=0,
    s.comment='Krennan Aranas - On Summoned - Board summoner vehicle passenger seat2'
WHERE s.entryorguid=35907 AND s.source_type=0 AND s.id=0 AND s.link=0
 AND s.event_type=11 AND s.event_phase_mask=0 AND s.event_chance=100 AND s.event_flags=1
 AND s.action_type=11 AND s.action_param1=46598 AND s.action_param2=0
 AND s.target_type=11 AND s.target_param1=35905 AND s.target_param2=10 AND s.target_param3=0
 AND EXISTS (SELECT 1 FROM creature_template ct WHERE ct.entry=35907 AND ct.AIName='SmartAI' AND ct.ScriptName='')
 AND EXISTS (SELECT 1 FROM creature_template horse WHERE horse.entry=35905 AND horse.AIName='SmartAI' AND horse.ScriptName='' AND horse.VehicleId=494 AND horse.spell1=68219);
