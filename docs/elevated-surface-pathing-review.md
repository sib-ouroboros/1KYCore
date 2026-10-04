# Elevated NPC surface pathing: review

Branch: `fix/npc-elevated-surface-pathing`, based on local
`feature/ruRU-localization` at `b733ecf`. No merge/rebase with main, no deployment,
no push. Investigated against this source tree, not another branch.

## Root cause

For an elevated source, BuildPolyPath can project its Detour start onto the
underlying polygon. BuildPointPath then converts Detour Y/Z/X coordinates to
world X/Y/Z. Old NormalizePath passes that lower Z to UpdateAllowedPositionZ.
DynamicMapTree casts downward from query Z+0.5; a GO floor above that origin
cannot be seen. GetStaticHeight similarly starts its VMAP query at Z+2.
Map::GetHeight combines static and dynamic results using their maximum, but
neither can recover a floor above both query origins.

MoveSplineInit replaces ONLY path[0] with the real unit position. Lower later
vertices remain. In addition, ValidatePathAgainstCollision previously saw the
lower path[0], so it could miss a floor between the real start and path[1].
The code establishes this failure mechanism; the live NPC incident has NOT been
reproduced. No NPC GUID/spawn coordinates were provided, so no actual SQL spawn
has been declared valid or invalid.

## Lifecycle

1. UnitAI::AttackStart calls Attack then MotionMaster::MoveChase.
2. TargetedMovementGenerator::_setTargetLocation computes its contact/near point
   and calls PathGenerator::CalculatePath; NOPATH sets CannotReachTarget.
3. CalculatePath records the supplied start (also supports explicit start overload)
   and destination, then BuildPolyPath selects a corridor. The existing far-poly
   projection is kept.
4. BuildPointPath produces point vertices. The lower navmesh Z appears here,
   before NormalizePath. NormalizePath is where the collision floor was lost.
5. Corrected native point paths are validated from the supplied real start before
   forceDestination can replace the endpoint with a point under the floor.
6. TargetedMovementGenerator supplies the path to MoveSplineInit::MovebyPath.
   Launch anchors path[0] to the current spline/unit position and emits MonsterMove;
   server movement continues using those spline vertices.
7. HomeMovementGenerator uses MoveSplineInit::MoveTo and the same PathGenerator.
   Its existing no-path fallback is unchanged; live evade is a required follow-up.

## Algorithm and scope

- Surface preservation is enabled only by successful native BuildPointPath, not
  BuildShortcut. Flying, swimming/submerged sources, transports and players bypass
  the new logic. No gravity/movement flags, teleport, AI, combat reach or SQL changed.
- Require the supplied start above the raw first navmesh vertex by more than
  SMOOTH_PATH_SLOP, and a real height result within that tolerance of the start.
  This is evidence of support, not permission to invent a surface for a bad spawn.
- Preserve actual start vertex for collision validation. For lower later points,
  query from the previous normalized floor with a downward search range based on
  the gap. Accept only a real higher-than-baseline surface no higher than previous
  floor+SMOOTH_PATH_SLOP. Never assign a query altitude without a surface result.
- There is no sourceZ+5 or permanent source-altitude clamp. Descending floors feed
  the next query, so the anchor descends. Existing SMOOTH_PATH_STEP_SIZE provides
  search slack; Map's existing ray biases suffice to find level support.
- Preserve collision truncation/NOPATH and mark a displaced destination INCOMPLETE.
  Do not force a destination through the detected elevated floor.
- Queries occur during path construction, not every world tick. No nearby GO scan
  or DynamicTree locking change. Extra height queries occur only for an eligible
  source and subsequent lower vertices. A timing benchmark is still pending.

## Evidence

Compiled ACTUAL BuildPointPath, NormalizePath, ValidatePathAgainstCollision and
BuildShortcut bodies with controlled floor/ray geometry:

| Source Z | Raw MMAP Z | Legacy normalized Z | New normalized Z |
|---:|---:|---:|---:|
| 45 | 38 | 38 | 45 |

The numerical example is an analytical regression, not a captured live NPC trace.
The stair fixture yields `45,44,43,42,41,40,39,38,38`; the same-platform fixture
stays at 45; a wall truncates the path; a target at 38 below an intact floor at 45
remains unreachable at its actual endpoint despite forceDestination.

User assets at `F:/Projects` were read without modifying them. A scratch executable
compiled this repository's six Detour sources and loaded 12 real map-530 tiles
(grids x=11..13, y=42..45), format MMAP=9 / Detour=7, with a 2048-node query.
Near Sunstrider Island it found `(10349,-6357,33.4295)` and a 10-polygon corridor.
An explicitly synthetic elevated probe Z=40.9295 projected to Z=33.4295.
This confirms native mesh loading/projection; it does NOT prove a collision floor
exists at 40.9295. VMAP/dynamic GO integration was not run against a server instance.

## Historical comparison

Reference: https://github.com/Titans-Project/LegionCore-Reforged/commit/814091a88444167966222910b0821e6ac4cf6b1a
Compared actual GitHub commit patches (read-only API) with `git show b4b14b591c`.

| Status | Relevant change |
|---|---|
| ported | Start closestPointOnPoly projection in farFromPoly; 2048 query nodes |
| not ported; adapted here | NormalizePath upward-query idea, with support/previous-floor checks instead of sourceZ+5 |
| not ported; separate risk | prefixPolyLength<=1 guard before decrement/index: current source still has possible unsigned underflow; outside this fix |
| not ported; outside scope | Partial-path point-limit behavior, FindSmoothPath return, total-length calculation |
| not applicable as direct port | Foreign phasing/GO callback signatures differ from current PhaseShift API |
| dangerous to copy blindly | Unconditional sourceZ+5 for every lower point, including shortcut/flying/transport paths |
| outside scope | DynamicTree concurrency, time-sync handler, specific map preload, follow offsets and raid chase exceptions |

## Changed files

- `src/server/game/Movement/PathGenerator.cpp`: bounded height normalization,
  real-start collision validation, protection from forced endpoints under floors.
- `src/server/game/Movement/PathGenerator.h`: private NormalizePath opt-in/result.
- `contrib/tests/test_elevated_surface_pathing.py`: compiles actual C++ functions;
  tests paths and statuses with controlled geometry rather than checking a string.
- `.github/workflows/reliability-regression.yml`: test path filter and sanitizer run.
- `docs/elevated-surface-pathing-review.md`: evidence, limits and acceptance checklist.

## Tests

Passed locally: portable GCC 16.2 C++17, -Wall -Wextra -Werror; analytical platform,
stairs/descent, upper storey, wall, lower target with forceDestination, lost support,
bad spawn guard, terrain/cave lower layer, flying/swimming/transport/player bypass,
empty/no-height paths, unchanged shortcuts, NOPATH, SHORT and INCOMPLETE control flow.
Real map-530 Detour loading/query probe passed. Legacy-normalization mutation
failed the platform regression as expected; corrected actual functions passed.
git diff --check passed.

During test development, the first stair fixture failed collision validation:
its 2m drop over 2m crossed a solid tread with the existing 1m torso ray. Replaced
with a walkable 1m-over-2m fixture; collision validation was not relaxed. Initial
uncaught test assertion termination on Windows was replaced by explicit reporting.

Not tested: complete server build, CI GCC11/Clang/Windows jobs, ASan/UBSan in this
Windows portable compiler, live NPC combat/evade, actual dynamic GO and VMAP floors,
real offmesh connections and CPU load. CMake/MSVC/server dependency stack and WSL
Linux distribution are unavailable here; CI was not dispatched or claimed passed.

Reproduce available regression:

```sh
python3 contrib/tests/test_elevated_surface_pathing.py
# On a compiler without ASan/UBSan:
python3 contrib/tests/test_elevated_surface_pathing.py --compiler /path/to/g++ --no-sanitizers
```

## Remaining risks and acceptance

This is a reviewable candidate, not complete runtime acceptance. Height rays do not
reconstruct missing navmesh connectivity: stairs/ramps must overlap the chosen
corridor. A low ceiling inside existing height-query bias can prevent support
recognition; dynamic rising ramps steeper than the tolerance may not be recovered.
Existing torso LOS is not a full walkability/foot-support check. Ordinary offmesh
movement is untouched, but an elevated source using offmesh needs a real test.
Home movement's existing shortcut on NOPATH also requires a live check. A spawn
standing exactly on the wrong-but-real floor cannot be diagnosed from Z alone.

AC1/2/4/5/6: analytical coverage passed; corresponding live geometry checks pending.
AC3/8: bypass/terrain control-flow tests passed; live terrain/water/flying pending.
AC7: home lifecycle inspected; live evade pending.
AC9: bounded additional work documented; actual CPU benchmark pending.
AC10: actual changed function bodies compiled; full project compilation pending.

Live checklist on an isolated server using the supplied matching assets:

1. Select a supported NPC, record `.gps` plus DB spawn/home Z; enable GM mode.
2. Use `.mmap path` with player on the same platform; compare StartPosition,
   EndPosition, ActualEndPosition and visible vertices before/after the fix.
3. Repeat with `.mmap path true` and `.mmap path line`; test aggro, chase, stop,
   moving target, loss of aggro and return to home.
4. Repeat platform/downstairs/no-stairs, bridge/exit, storeys, cave, ascending and
   descending ramps, normal terrain, water, flying, transport and offmesh cases.
5. No direct drop/shortcut through floor; unreachable target should stay unreachable.
   Save NPC GUID/Entry, map, phase, source/path heights and matching asset versions.
6. Run full existing GCC, Clang and Windows build configurations and sanitizer
   regression before merging; benchmark path-heavy encounters before deployment.
