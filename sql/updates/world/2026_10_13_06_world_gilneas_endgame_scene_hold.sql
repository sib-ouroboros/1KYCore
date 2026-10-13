-- Only the audited Endgame transport may be held during boarding and its scene.
UPDATE gameobject_template SET Data8=1
WHERE entry=203428 AND type=15 AND Data0=2338 AND Data6=749 AND Data8=0
 AND ScriptName='go_worgen_gunship_203428';
