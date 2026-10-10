-- Scoped runtime extends SmartAI; retain the release16-point route and rescue spells.
UPDATE creature_template SET ScriptName='npc_gilneas_rescue_horse_runtime'
WHERE entry=35905 AND AIName='SmartAI' AND ScriptName='' AND VehicleId=494 AND spell1=68219
 AND EXISTS (SELECT 1 FROM waypoints WHERE entry=35905 AND pointid=7 AND ABS(position_x+1674.46)<0.01 AND ABS(position_y-1344.95)<0.01 AND ABS(position_z-15.1352)<0.01)
 AND (SELECT COUNT(*) FROM waypoints WHERE entry=35905)=16;
-- Source: WoWCircle434 e0950ef1,2014_05_19_world_kezan_gilneas_4.sql: emote472.
-- Keep actual spawn coordinates and quest visibility aura; restore the hanging pose.
UPDATE creature_addon a JOIN creature c ON c.guid=a.guid
SET a.emote=472
WHERE c.id=35753 AND c.map=654 AND a.emote=0 AND a.bytes1=50397184 AND a.bytes2=1 AND a.auras='49414';
-- Final waypoint must address this horse passenger, not every nearby player's Krennan.
UPDATE smart_scripts SET target_type=29,target_param1=1,target_param2=0
WHERE entryorguid=35905 AND source_type=0 AND id=3 AND event_type=40 AND event_param1=16
 AND action_type=45 AND action_param1=1 AND action_param2=1
 AND target_type=11 AND target_param1=35907 AND target_param2=10
 AND EXISTS (SELECT 1 FROM creature_template WHERE entry=35905 AND ScriptName='npc_gilneas_rescue_horse_runtime');
-- Pinned LegionCore world735.26972 snapshot2024_10_23: original tree placement.
-- Preserve live phases and custom placements; update only the known low release spawn.
UPDATE creature SET position_x=-1672.8,position_y=1345.26,position_z=20.796,orientation=0.415266
WHERE id=35753 AND map=654 AND PhaseId=171
 AND ABS(position_x+1673.24)<0.01 AND ABS(position_y-1344.8)<0.01
 AND ABS(position_z-18.9827)<0.01;
