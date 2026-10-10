-- Administrator's corrected height; retain calibrated X/Y and orientation.
UPDATE creature SET position_z=19.05
WHERE guid=20556808 AND id=35753 AND map=654 AND PhaseId=171
 AND ABS(position_x+1673.4)<0.001 AND ABS(position_y-1344.18)<0.001
 AND ABS(position_z-19.65)<0.001;
