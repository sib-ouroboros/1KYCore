-- Read-only snapshot. Run against world, not characters. Save full output.
SELECT * FROM updates WHERE name LIKE '%gilneas%' ORDER BY name;
SELECT entry,minlevel,maxlevel,faction,AIName,ScriptName,VehicleId,spell1,spell2,flags_extra,HealthModifier,DamageModifier FROM creature_template WHERE entry IN(35905,35907,35914,36332,36488,36540,36741,37067,37078,37685,37686,37692,37716,37718,37733,37735,38022,38210,38420,38507,38540);
SELECT * FROM creature_template_scaling WHERE Entry IN(36488,37685,37686,37692,37716,37718,37733,37735,38022,38210,38420);
SELECT id,map,phaseUseFlags,PhaseId,PhaseGroup,COUNT(*) FROM creature WHERE map=654 AND id IN(35905,35907,35914,36332,37067,37078,37733,38507,38540) GROUP BY id,map,phaseUseFlags,PhaseId,PhaseGroup;
SELECT guid,id,map,phaseUseFlags,PhaseId,PhaseGroup,position_x,position_y,position_z FROM creature WHERE id=37733;
SELECT * FROM gameobject WHERE id=196472;
SELECT id,COUNT(*) points,MIN(point),MAX(point) FROM waypoint_data WHERE id IN(3850701,3850702,3850703,3850704,3850705,3854001,3854002) GROUP BY id;
SELECT CreatureID,GroupID,ID,BroadcastTextID,Text FROM creature_text WHERE CreatureID=36332 ORDER BY GroupID,ID;
