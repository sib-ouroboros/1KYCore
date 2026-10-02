#!/usr/bin/env python3
"""Exercise production Magni handler and EventProcessor, with actual teleport ABI."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/scripts/Argus/AntorusTheBurningThrone/boss_aggramar.cpp').read_text('utf8')
    event = source[source.index('class MagniTeleportEvent final'):source.index('void AddSC_boss_aggramar()')]
    spell = re.search(r'SPELL_TITANS_ASSEMBLE_MOVIE\s*=\s*(\d+)', source)[1]
    player_header = (root / 'src/server/game/Entities/Player/Player.h').read_text('utf8')
    declaration = re.search(r'bool TeleportTo\(uint32 mapid, float x, float y, float z, float orientation[^;]+;', player_header)[0]
    # Compile the actual scheduler, including its event destruction/cancellation.
    processor = root / 'src/common/Utilities/EventProcessor.cpp'
    unit = (root / 'src/server/game/Entities/Unit/Unit.cpp').read_text('utf8')
    assert 'm_Events.Update(p_time);' in unit and 'm_Events.KillAllEvents(true);' in unit
    harness = r'''
#include "EventProcessor.h"
#include <iostream>
#include <stdexcept>
void check(bool value) { if (!value) throw std::runtime_error("Magni teleport regression"); }
constexpr uint32 SPELL_TITANS_ASSEMBLE_MOVIE = MOVIE_VALUE;
unsigned totalTeleports = 0;
struct Player {
    EventProcessor m_Events;
    unsigned movies = 0, teleports = 0, gossipClosed = 0;
    bool alive = true;
    ~Player() { alive = false; }
    void CastSpell(Player* target, uint32 spell, bool triggered) {
        check(alive && target == this && spell == SPELL_TITANS_ASSEMBLE_MOVIE && triggered);
        ++movies;
    }
    DECLARATION
};
bool Player::TeleportTo(uint32 mapid, float x, float y, float z, float orientation,
                       uint32 options, uint32 optionParam) {
    check(alive && movies == 1 && gossipClosed == 1);
    check(mapid == 1712 && x == 2826.39f && y == -4567.94f && z == 291.95f);
    check(orientation == 0.02513274f && options == 0 && optionParam == 0);
    ++teleports;
    ++totalTeleports;
    return true;
}
void CloseGossipMenuFor(Player* player) { ++player->gossipClosed; }
struct Creature {};
struct ScriptedAI {
    explicit ScriptedAI(Creature*) {}
    virtual ~ScriptedAI() = default;
    virtual void sGossipSelect(Player*, uint32, uint32) {}
};
PRODUCTION
int main() {
    Creature magni;
    npc_magni_bronzebeard_128169 handler(&magni);
    Player first, second;
    first.m_Events.Update(1234);
    handler.sGossipSelect(&first, 0, 0);
    handler.sGossipSelect(&second, 0, 0);
    check(first.movies == 1 && second.movies == 1 && totalTeleports == 0);
    first.m_Events.Update(3999);
    second.m_Events.Update(1000);
    check(totalTeleports == 0);
    first.m_Events.Update(1);
    check(first.teleports == 1 && second.teleports == 0);
    second.m_Events.Update(2999);
    check(second.teleports == 0);
    second.m_Events.Update(1);
    check(second.teleports == 1 && totalTeleports == 2);
    first.m_Events.Update(10000);
    check(first.teleports == 1);
    Player cancelled;
    handler.sGossipSelect(&cancelled, 0, 0);
    cancelled.m_Events.KillAllEvents(false);
    cancelled.m_Events.Update(5000);
    check(cancelled.teleports == 0 && totalTeleports == 2);
    {
        Player disconnected;
        handler.sGossipSelect(&disconnected, 0, 0);
        disconnected.m_Events.Update(3999);
    }
    check(totalTeleports == 2);
    std::cout << "PASS: production Magni handler, actual EventProcessor, 4s delay, correct map/XYZ/facing/options, independent players, cancellation and destruction\n";
}
'''.replace('MOVIE_VALUE', spell).replace('DECLARATION', declaration).replace('PRODUCTION', event)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        (directory / 'Define.h').write_text('#pragma once\n#include <cstdint>\n#include <mutex>\nusing uint8=std::uint8_t; using uint32=std::uint32_t; using uint64=std::uint64_t;\n#define TC_COMMON_API\n', encoding='utf8')
        (directory / 'Errors.h').write_text('#pragma once\n#include <cassert>\n#define ASSERT(value) assert(value)\n', encoding='utf8')
        cpp = directory / 'magni.cpp'
        exe = directory / 'magni'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Wconversion', '-Werror',
                        '-fsanitize=address,undefined,float-cast-overflow', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', '-pthread', '-I', str(directory),
                        '-I', str(processor.parent), str(cpp), str(processor), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
