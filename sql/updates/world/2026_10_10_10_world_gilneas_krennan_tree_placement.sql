-- Quest14293: administrator's client-calibrated tree position.
-- Only the original tree spawn or previous package placements; retain orientation/phase.
UPDATE creature SET position_x=-1673.4,position_y=1344.18,position_z=19.65
WHERE guid=20556808 AND id=35753 AND map=654 AND PhaseId=171
 AND ((ABS(position_x+1673.24)<0.001 AND ABS(position_y-1344.8)<0.001 AND ABS(position_z-18.9827)<0.001)
 OR (ABS(position_x+1672.8)<0.001 AND ABS(position_y-1345.26)<0.001
 AND (ABS(position_z-20.796)<0.001 OR ABS(position_z-20.496)<0.001 OR ABS(position_z-19.456224)<0.001)));
-- Air-only allows native UpdateMovementFlags to disable gravity above the floor.
-- Rescued passenger35907 and its boarding script are separate and unchanged.
UPDATE creature_template SET InhabitType=4 WHERE entry=35753 AND InhabitType=3;
