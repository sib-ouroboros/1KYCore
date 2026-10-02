#!/usr/bin/env python3
"""Compile the actual Aggramar spawn table and bounded spawning method."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root/'src/server/scripts/Argus/AntorusTheBurningThrone/boss_aggramar.cpp').read_text('utf8')
    table = source[source.index('struct SpawnData'):source.index('struct boss_aggramar')]
    method = source[source.index('    void LoadNPC('):source.index('    void EnterCombat(', source.index('    void LoadNPC('))]
    constants = '\n'.join('constexpr uint32 '+k+'='+re.search(r'\b'+k+r'\s*=\s*(\d+)',source)[1]+';' for k in ('EVNET_PHASE_2','EVNET_PHASE_3','NPC_EMBER_OF_TAESHALACH'))
    harness = r'''
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint32 = std::uint32_t;
CONSTANTS
constexpr uint32 TEMPSUMMON_MANUAL_DESPAWN=1, WEEK=604800;
void check(bool value) { if (!value) throw std::runtime_error("Aggramar spawn regression"); }
struct Position {
    float x,y,z,o;
    Position(float px,float py,float pz,float po):x(px),y(py),z(pz),o(po) {}
};
TABLE
struct Creature {
    std::vector<Position> summoned;
    void SummonCreature(uint32 id, Position pos, uint32 type, uint32 duration) {
        check(id == NPC_EMBER_OF_TAESHALACH && type == TEMPSUMMON_MANUAL_DESPAWN && duration == WEEK);
        summoned.push_back(pos);
    }
};
struct Boss {
    Creature* me;
METHOD
};
void checkPair(Creature const& creature) {
    check(creature.summoned.size() == 2);
    auto const& first=creature.summoned[0]; auto const& second=creature.summoned[1];
    check(first.x == -12679.456f && first.y == -2254.8264f && first.z == 2514.2646f && first.o == 0.0f);
    check(second.x == -12588.12f && second.y == -2254.8215f && second.z == 2514.6276f && second.o == 3.101369f);
}
int main() {
    Creature creature; Boss boss{&creature};
    boss.LoadNPC(EVNET_PHASE_2); checkPair(creature);
    creature.summoned.clear();
    boss.LoadNPC(EVNET_PHASE_3); checkPair(creature);
    creature.summoned.clear();
    boss.LoadNPC(0); boss.LoadNPC(99); check(creature.summoned.empty());
    for (unsigned i=0;i<20;++i) {
        boss.LoadNPC(EVNET_PHASE_2); checkPair(creature); creature.summoned.clear();
    }
    std::cout << "PASS: production Aggramar spawn table/method, exact two actors per phase, positions/orientations, unrelated events, repeated bounded traversal\n";
}
'''.replace('CONSTANTS',constants).replace('TABLE',table).replace('METHOD',method)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'aggramar.cpp';exe=Path(tmp)/'aggramar';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
