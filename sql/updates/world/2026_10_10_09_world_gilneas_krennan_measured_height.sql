-- Quest14293: client calibration supplied by the server administrator.
-- Use measured Z only; keep source X/Y/orientation and user-customized placements.
UPDATE creature SET position_z=19.456224
WHERE guid=20556808 AND id=35753 AND map=654 AND PhaseId=171
 AND ABS(position_x+1672.8)<0.001 AND ABS(position_y-1345.26)<0.001
 AND (ABS(position_z-20.496)<0.001 OR ABS(position_z-20.796)<0.001);
