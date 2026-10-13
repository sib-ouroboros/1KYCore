-- Quest26706: the physical gunship must share its passengers' Endgame phase.
UPDATE transports SET phaseid=191
WHERE guid=28 AND entry=203428 AND phaseUseFlags=0 AND phaseid=0 AND phasegroup=0
 AND ScriptName=''
 AND EXISTS(SELECT 1 FROM gameobject_template WHERE entry=203428 AND type=15
 AND Data6=749 AND ScriptName='go_worgen_gunship_203428');
