-- Client feedback: lower the known tree spawn by0.3m; retain pose, phase and custom placements.
UPDATE creature SET position_z=20.496
WHERE id=35753 AND map=654 AND PhaseId=171
 AND ABS(position_x+1672.8)<0.001 AND ABS(position_y-1345.26)<0.001
 AND ABS(position_z-20.796)<0.001;
-- Vehicle charm is retained for68219. Native SmartScript requires WHILE_CHARMED(512).
-- Only the release rescue handlers and timed route start; keep all existing flag bits.
UPDATE smart_scripts s JOIN creature_template c ON c.entry=35905
SET s.event_flags=s.event_flags|512
WHERE c.ScriptName='npc_gilneas_rescue_horse_runtime'
 AND ((s.entryorguid=35905 AND s.source_type=0 AND
 ((s.id=0 AND s.event_type=27 AND s.action_type=80 AND s.action_param1=3590500)
 OR (s.id=1 AND s.event_type=61 AND s.action_type=8 AND s.action_param1=0)
 OR (s.id=2 AND s.event_type=40 AND s.event_param1=6 AND s.action_type=97)
 OR (s.id=3 AND s.event_type=40 AND s.event_param1=16 AND s.action_type=45 AND s.action_param1=1 AND s.action_param2=1 AND s.target_type=29 AND s.target_param1=1)
 OR (s.id=4 AND s.event_type=61 AND s.action_type=41 AND s.action_param1=5000)))
 OR (s.entryorguid=3590500 AND s.source_type=9 AND s.id=0 AND s.action_type=53 AND s.action_param1=1 AND s.action_param2=35905));
