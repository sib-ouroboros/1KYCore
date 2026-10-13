# Endgame transport repair, 2026-10-13

Video evidence: `World of Warcraft 2026-10-13 20-57-29.mp4` (4m46s).
At about 1:35 the incoming bird approaches the upper hull; around 1:40-2:00
it goes below the ship and the player falls into the water. At 2:50 a Rope
tooltip is visible, so the rope problem is not solely an absent template. At
3:10 the selected hostile is gunship grunt42141 and attack attempts fail.
The later boarding involves GM flight, so it is not a successful native handoff.

Changes:
- Unit::SetFacingTo keeps world-to-transport spline transformations enabled.
  Its prior branch disabled them while passing world XYZ and yaw. Native tests
  use a moving, rotated ship and verify unchanged world movement outside ships.
- Home movement uses passenger-local home coordinates on transports and avoids
  world navmesh projection there; ordinary home/reset logic remains intact.
- Lorna's evade home is her transport offset, not the ship's world position.
- Handoff now explicitly exits the bird, attaches the player to the actual ship,
  sets the deck offset and teleports with the existing NOT_LEAVE_TRANSPORT
  semantics before beginning Lorna's scene. The old MovePosition-only block
  merely modified a temporary position and did not attach or relocate the player.
- The incoming bird caches the ship's actual Lorna GUID, requests a bounded ship
  hold, survives the spell's summon expiry, retries missing handoff, and safely
  returns on a five-minute flight timeout. No fabricated completion is added.
- Only native gunship203428 is made stoppable through Data8=1 in
  `2026_10_13_06_world_gilneas_endgame_scene_hold.sql`. First incoming boarding
  holds its actual dock; first ship handoff closes late boarding. An actually
  boarded escape wyvern releases the ship. Recovery is bounded to15minutes.
  This adjusts native route timing to scene progress; it is not an exact retail
  timing claim. The route coordinates and existing scene stages are preserved.
- Rope interaction requires an eligible player and the same ship, selects the
  next lower deck using local height and proximity, and jumps to its exact anchor
  position. It does not randomly skip floors or use contact-point adjustment.
  Friendly NPC rope jumps also use exact anchor positions and explicit speeds.
- Destruction/timeout recovery snapshots real ship participants before teleport,
  leaves unrelated players alone, and grants no automatic credit. Existing escape
  AI grants43729 only after successful arrival; its cancellation guards remain.

Validation: native-method fixtures for facing/home, handoff/rope/evacuation,
readiness/hold/release/timeout, incoming and outgoing ownership/lifecycle,
barrel/boss creation and deck combat pass locally. SQL stopping-flag checks
cover first/repeat/custom/unrelated cases with SQLite semantics. CI also runs
ASan/UBSan native checks and full Linux/Windows builds. No production server or
DB changed. Real MySQL import and complete client passage remain to verify.

Deployment requires rebuilt core and scripts, not just the scripts module,
plus the06 world update and a worldserver restart. All previous Endgame SQL
and player-phase changes remain prerequisites. Retest with GM OFF: incoming
boarding/deck attachment, NPC turning/combat on the ship, ropes to the next
floor, three charges/boss, escape, credit43729 and turn-in. Also test abandon,
logout and death; no successful quest credit should be invented by recovery.
