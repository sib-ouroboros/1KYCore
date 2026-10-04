# NPC combat slots: implementation and review

Base: `feature/ruRU-localization`, `a9b254d08e908a6fe8c31723be74650515693c76`.
Work branch: `feature/npc-crowd-separation`. No merge or deployment.

## Root cause and Phase A investigation

`TargetedMovementGenerator::_setTargetLocation`, for a zero offset, calls
`GetContactPoint`. The latter uses `GetNearPoint` with the approach angle.
`GetNearPoint` ignores its searcher and tests surface height/LoS, without
registering other attackers. Melee arrivals consequently share a destination.
The existing early return at contact distance also leaves touching creatures
alone; it is deliberately preserved to avoid reshuffling when a player walks
into melee range of a stationary creature.

`rg` found no consumers of `ObjectPosSelector` in the base. Local file history
starts at the imported upstream baseline `f8fcb8a`, so it does not establish
the historical reason for TrinityCore removing its consumer.

Primary references inspected:

- [TrinityCore 3.3.5 Object.cpp](https://github.com/TrinityCore/TrinityCore/blob/3.3.5/src/server/game/Entities/Object/Object.cpp): current near-point selection still tests LoS rather than attacker occupancy.
- [CMaNGOS Object.cpp](https://github.com/cmangos/mangos-classic/blob/master/src/game/Entities/Object.cpp): `GetNearPointAt` retains the selector; its occupancy visitor is commented out with “unused because its not blizzlike”. This is evidence of CMaNGOS's explicit choice, not proof of why a particular TrinityCore revision changed.

This feature is therefore optional combat positioning, not a claim of a
Blizzard physical collision implementation. Global `GetNearPoint` is unchanged.

The original selector's `acos(distance / denominator)` is conservative rather
than an exact circle intersection solver. Reuse is useful for generating nearby
angles, but insufficient for validating final spacing: the helper also checks
actual disk distances. Some tight valid configurations may still fall back.
The utility now clamps acos inputs, ignores invalid occupancy values, and has
a positive minimum angle step, with native regression tests.

## Architecture and changed files

- `Movement/CombatSlot.h/.cpp`: scoped eligibility, local neighbour collection,
  slot candidate validation and fallback. No global slot ownership table.
- `MovementGenerators/TargetedMovementGenerator.h/.cpp`: chase-owned angle and
  cooldown; helper called only on zero-offset/zero-angle creature contact chase.
  Valid paths are consumed by the existing spline launch. Player and follow
  generators retain their original paths.
- `Entities/Object/ObjectPosSelector.h/.cpp`: degenerate geometry safeguards.
- `World/World.h/.cpp`, `worldserver.conf.dist`: validated, reloadable settings.
- `contrib/tests/test_npc_combat_slots.py` and two fixtures: compile the real
  helper, selector and complete chase/follow implementation, with unit, grid,
  terrain and path interfaces supplied by the test.
- `.github/workflows/reliability-regression.yml`: native regression under
  address/undefined behaviour sanitizers in the existing workflow.

No SQL, AI, threat, damage, encounter, quest, global contact point or
`PathGenerator` implementation changes are included.

## Algorithm

1. Eligible: live, uncontrolled ground creature, ordinary chase of its current
   victim, no owner/charm, pet, boss, vehicle, transport, flight, swimming,
   casting lock, movement lock, fear or confusion. Victim must share map/phase.
2. Radius retains the legacy contact radius: target size + attacker size +
   contact distance. It is checked against the actual core melee range.
3. Collect grid creatures near the victim ring and immediate neighbours near
   the approaching attacker. The second local visit catches a neighbour whose
   future endpoint is near the target but whose current position is not.
   Queries never traverse the entire map or create grids. Sort by GUID and
   deduplicate. Filter same victim, phase/map, life state, ordinary chase and
   ground eligibility. Only positions close to the combat ring with at most
   2 units of vertical difference and target LoS are registered.
4. Register current positions and active spline final destinations in the
   existing selector. Endpoint reservations are read from live neighbours,
   never stored as pointers or persistent GUID locks. Capacity overflow uses
   legacy chase rather than dropping arbitrary occupants and calling it free.
5. Try the existing world angle, otherwise the natural approach angle.
   Order selector candidates by absolute angular deviation, with GUID parity
   breaking equal left/right choices. At most 64 angles are enumerated and
   8 candidates are tried, including the preferred angle.
6. Check finite map coordinates, owner-appropriate allowed Z, vertical
   difference, disk spacing, melee range and owner/target LoS. Calculate a
   non-forced path using the existing `PathGenerator`; reject incomplete,
   shortcut, non-navmesh, no-path and truncated paths. Check the actual endpoint
   against the requested point (0.25 units), melee range, Z, LoS and occupancy.
   Existing MMAP/VMAP/platform path protections remain authoritative.
7. Reuse the validated path for the original spline launch. Otherwise retain
   the original `GetContactPoint` coordinates and calculate the legacy path
   with its original flags, including its existing incomplete-path policy.

Hysteresis uses the previous world angle. A 0.75-unit victim displacement
triggers destination refresh; turning alone does not. Neighbour collection and
alternative selection are limited by the cooldown; while moving within it,
the cached angle still undergoes path validation but occupancy is not revisited.
Initialize/reset, finalize and lost victim clear the state; map/phase,
movement-mode and config eligibility are checked before reuse. State contains
only angles/coordinates/counters, so despawns cannot leave dangling references.
No periodic reshuffling of stationary melee creatures is introduced.

## Config

```ini
Creature.CrowdSeparation.Enable = 0
Creature.CrowdSeparation.Padding = 0.2
Creature.CrowdSeparation.RecalculateInterval = 500
Creature.CrowdSeparation.MaxNeighbors = 64
```

Padding accepted range: 0..0.5; interval: 100..5000 ms; neighbours: 1..128.
Invalid values use the documented defaults. Padding 0.2 is a starting value,
not a visually calibrated value. No Strength setting exists because local
steering is not implemented. With Enable=0 there is no crowd grid visit or
path calculation; the native integration test verifies the legacy destination.
The optional `movement.crowd` debug category reports owner/entry/victim,
occupancy, candidates, selected/fallback and angle when selection runs.
It is not an unconditional per-tick log. GM markers are not included.

## Performance

One local Windows GCC run, optimized fixture build, measured:

| NPC | Selected slots | Local grid visits | Path calls | Helper microseconds |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 2 | 1 | 1 |
| 5 | 5 | 10 | 5 | 11 |
| 10 | 6 | 20 | 6 | 29 |
| 20 | 6 | 40 | 6 | 98 |
| 40 | 6 | 80 | 6 | 121 |
| 80 | 6 | 160 | 6 | 290 |

These are synthetic helper timings, not world-update, real navmesh or server
CPU measurements. The fixture supplies cheap path calls. Six slots saturate
this particular 3.5-unit ring with 1.5-unit NPC sizes and 0.2 padding; further
attackers fall back to chase. This is not a promise of 40 non-overlapping NPC.
Per-selection path attempts <=8. Local collection still scales with population
of visited cells and GUID sorting; a dense shared local pack has aggregate
quadratic neighbour work, although there is no map-wide pairwise traversal.

## Tests and acceptance status

Passed locally with GCC, `-Wall -Wextra -Werror`:

- Natural approach and same-side pair, variable small/large sizes, spacing and
  melee bounds; current position and active spline endpoint occupancy.
- Stable angle, orientation independence, cooldown, moving victim and no
  stationary-target path churn.
- Different victim, map, phase, dead/despawned, vertical, pet and transport
  filtering; boss, flight and casting exclusions.
- Blocked candidate/alternative side, invalid path flags, shifted endpoint,
  lowered surface, capacity saturation and fallback.
- Actual creature/player chase and creature/player follow specializations,
  ranged offsets, arrivals/Attack, lost target, disabled legacy path and
  preservation of existing partial-path/unreachable behaviour.
- Degenerate selector sizes/reaches and finite iteration progress.
- Existing elevated-surface native regression: platform, stairs, storeys,
  collision walls, forced endpoint, invalid spawn, terrain and special motion.

Still required before enabling by default or declaring the full task accepted:

- Full GCC/Windows builds and CI sanitizer results for this branch.
- Real client/server Phase C: same-side 2 and 5–8 attackers; stop/start, moving
  player, sharp turns; doors/corridors/stairs/bridge/elevated GO; boss plus adds,
  scripted movement, pets/casters and simultaneous independent victim groups.
- Real 1/5/10/20/40+ world-update CPU, path recalculations and stability capture.
- Visual calibration of padding and vertical tolerance.

Maps/vmaps/mmaps exist under `F:/Projects`, but no local server build/runtime
was available for these checks. Fixture terrain checks do not replace them.
The existing elevated path regression does not prove all live bridges safe.

Phase D local steering is deliberately deferred until real Phase C shows
overlap on approach remains unacceptable. Combat slots separate destinations;
they do not physically separate the shared incoming path. The full AC list
must not be marked passed based on the fixture suite alone.

## Risks and next review

Feature is off by default. Its strict surface/path conditions can reject valid
points and fall back, especially on steep stairs or elevated dynamic geometry.
Very closely spaced storeys can evade a fixed vertical filter; LoS/path checks
reduce but do not eliminate the need for live multi-level tests. During the
cooldown a newly occupied cached destination is not immediately reconsidered.
The selector is conservative, so crowded geometry can fall back earlier than
an exact circle solver. Boss classification and unusual scripted chase
patterns require encounter review even with the provided exclusions.

Review the focused diff and CI first; then enable only in an isolated test
server, capture Phase C scenarios, and decide whether bounded local steering
is necessary. No working server configuration or data was changed.
