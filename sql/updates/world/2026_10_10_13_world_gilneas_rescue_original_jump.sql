-- Restore the release point6 jump requested after client testing.
-- Keep all16 route points, immediate start, owned rescue and the empty initial rear seat.
INSERT INTO smart_scripts
(entryorguid,source_type,id,link,event_type,event_phase_mask,event_chance,event_flags,
 event_param1,event_param2,event_param3,event_param4,action_type,
 action_param1,action_param2,action_param3,action_param4,action_param5,action_param6,
 target_type,target_param1,target_param2,target_param3,target_x,target_y,target_z,target_o,comment)
SELECT 35905,0,2,0,40,0,100,512,6,0,0,0,97,25,10,0,0,0,0,1,0,0,0,-1674.46,1344.95,15.1352,0,
 'King Greymanes Horse - Point6 - Original rescue jump; runtime waits after landing'
WHERE EXISTS (SELECT 1 FROM creature_template WHERE entry=35905 AND ScriptName='npc_gilneas_rescue_horse_runtime')
 AND NOT EXISTS (SELECT 1 FROM smart_scripts WHERE entryorguid=35905 AND source_type=0 AND id=2);
