# Quest 38727: Stop the Bombardment

The old banner handler awarded both credits immediately, hid the shared spawn
for its owner, and killed a personal copy after two seconds. Destruction was a TODO.

Each flag now creates a personal helper and a matching devastator copy: Ashtongue
at Doom Fortress, Shivarra at Forge of Corruption, Coilskar at Soul Engine. This
assignment is supported by the [Wowhead quest description](https://www.wowhead.com/quest=38727/stop-the-bombardment).
The helper says its existing localized line, attacks at two seconds, and the
copy receives the native fire visual and dies at six seconds. Coilskar additionally
freezes the copy. Credits follow destruction; temporary actors leave at fourteen
seconds, with a twenty-second hard lifetime. These timings and the combined
visual sequence are an approximation, not a verified retail replay.

Packets for dialogue, sound and attack/fire visuals go directly to the owner.
Only cosmetic dummy aura 191568 is actually cast. Damage spells 191669/191667 are
excluded. Shared spawns are never moved, killed or despawned. Interrupted scenes
restore the shared object to a nearby owner's client with an explicit create
update; they award no credit. Quest/map/class, per-target completion and repeat
click guards protect the handler. Partially completed objective pairs can retry.

SQL `2026_10_05_07_world_mardum_bombardment.sql` clears only the obsolete Data10
spells on these three flags with this script binding. It preserves custom scripts,
custom spells and other objects, and is repeatable. The existing binding and
helper creature_text rows were present in the audited release; no shared AI,
spawns, objective definitions or phases are modified.

The previous owner's `DestroyForPlayer` replacement is retained. It is packet
visibility, not durable per-object phasing: revisiting after leaving visibility
range/relogging may show a credited shared machine again. This change does not
introduce persistent wrecks or claim to fix that pre-existing limitation.

## Validation

- Native fixture tests compile the actual banner and scene handlers; cover all
  three crews, owner isolation, delayed/once-only credit, partial progress,
  repeat clicks, failed summons/AI, logout, abandonment and leaving the scene.
- The departure test also passes after fixing `UNIT_FIELD_NPC_FLAGS` to the real
  `UNIT_NPC_FLAGS` field, the cause of both preceding full build failures.
- MySQL 8 on a disposable release-copy schema: repeat import, unrelated rows and
  custom scripts/spells preserved. No working server was accessed.
- Spell/SpellEffect/SpellXSpellVisual data decoded from local 7.3.5 build 26654
  with core layout checks. The core expects 26972; client appearance is untested.

Run `python contrib/tests/test_mardum_bombardment.py` (ASan/UBSan by default).
`--no-sanitizers` is available for local Windows toolchains. This is an isolated
handler test, not a full server build or gameplay test. CI also performs full
Windows/GCC builds separately.

## Client acceptance

On a test server with updated code and SQL, verify all three flags using quest
38727: helper appearance, dialogue, visible attack, Coilskar freeze, destruction
animation/fire, and both corresponding credits after six seconds. Test two
players simultaneously, repeated clicks, abandoning during the scene, and a
partial objective pair. Nearby players must keep their original shared machine
and receive no scene chat/visuals. Confirm that the normal quest turn-in works.
Tune visual packet behavior/timing only after observing this in the client.
