-- Two distinct Genn lines pointed to36341, so the native localized lookup
-- replaced both with "I didn't think so...". The preceding question is36340.
-- Preserve timings, C++ events, creature_text_locale and custom text bindings.
UPDATE creature_text SET BroadcastTextID=36340
WHERE CreatureID=36332 AND GroupID=0 AND ID=0 AND BroadcastTextID=36341
 AND Text='Tell me, Godfrey.  Those that stayed in Gilneas City so that we could live.  Were they following protocol?';
