-- Quest14293: Krennan must be summoned by Rescue68219/68228, never preinstalled.
DELETE a FROM vehicle_template_accessory a JOIN creature_template c ON c.entry=a.entry
WHERE a.entry=35905 AND a.accessory_entry=35907 AND a.seat_id=1 AND a.minion=0
 AND a.summontype=3 AND a.summontimer=300000
 AND c.ScriptName='npc_gilneas_rescue_horse_runtime';
-- Start on the first SmartAI update after boarding, preserving the native path/quest.
UPDATE smart_scripts s JOIN creature_template c ON c.entry=35905
SET s.event_param1=0,s.event_param2=0,s.event_param3=0,s.event_param4=0
WHERE c.ScriptName='npc_gilneas_rescue_horse_runtime'
 AND s.entryorguid=3590500 AND s.source_type=9 AND s.id=0
 AND s.action_type=53 AND s.action_param1=1 AND s.action_param2=35905 AND s.action_param4=14293
 AND s.event_param1=5000 AND s.event_param2=5000 AND s.event_param3=5000 AND s.event_param4=5000;
-- This legacy point6 jump overrides waypoint movement; use the contiguous route instead.
DELETE s FROM smart_scripts s JOIN creature_template c ON c.entry=35905
WHERE c.ScriptName='npc_gilneas_rescue_horse_runtime'
 AND s.entryorguid=35905 AND s.source_type=0 AND s.id=2 AND s.event_type=40 AND s.event_param1=6
 AND s.action_type=97 AND s.action_param1=25 AND s.action_param2=10 AND s.target_type=1
 AND ABS(s.target_x+1674.46)<0.001 AND ABS(s.target_y-1344.95)<0.001 AND ABS(s.target_z-15.1352)<0.001;
-- Prevent rescue before the stop or repeated summons after boarding.
INSERT INTO spell_script_names(spell_id,ScriptName)
SELECT 68219,'spell_gilneas_rescue_at_tree'
WHERE NOT EXISTS (SELECT 1 FROM spell_script_names WHERE spell_id=68219 AND ScriptName='spell_gilneas_rescue_at_tree');
