#!/usr/bin/env python3
"""Compile all six production battle target scans; exercise disappearing grid units."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
from test_gilneas_quests import method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    native = (root / 'src/server/game/Entities/Unit/Unit.cpp').read_text('utf8')
    search = method(native, 'void Unit::GetAttackableUnitListInRange(')
    assert '.clear()' not in search, 'fixture must model the actual append-only native API'
    sections = re.split(r'    struct (npc_\w+AI) : public ScriptedAI', source)
    classes = []
    for i in range(1, len(sections), 2):
        name, body = sections[i:i + 2]
        if '        void FindTargets()' not in body:
            continue
        members = '\n'.join(re.findall(r'^        (?:uint32\s+m_(?:wave|waveSize|point)\b.*|Unit\*\s+m_nearestTarget\b.*|float\s+m_(?:nearestDistance|checkDistance)\b.*|bool\s+m_doneA\b.*);$', body, re.M))
        classes.append('struct ' + name + '{ Creature* me; std::list<Unit*> m_targetList;\n' + members + '\n' + method(body, '        void FindTargets()') + '\n};')
    assert len(classes) == 6
    code = r'''
#include <cstdint>
#include <list>
#include <memory>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr uint32 NPC_GOREROT=38331,NPC_LADY_SYLVANAS_WINDRUNNER=38469;
struct Unit { float distance; uint32 entry; float GetDistance2d(Unit*)const{return distance;} uint32 GetEntry()const{return entry;} };
struct Creature:Unit { std::vector<Unit*> grid; void GetAttackableUnitListInRange(std::list<Unit*>& out,float range){ for(auto* u:grid) if(u->distance<=range)out.push_back(u); } };
void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
PRODUCTION
template<class AI>void exercise(bool hasSpacing){
 Creature owner{}; AI ai; ai.me=&owner;
 check(ai.m_wave==0&&ai.m_waveSize==0&&ai.m_point==0&&!ai.m_nearestTarget&&ai.m_nearestDistance==0&&ai.m_checkDistance==0&&!ai.m_doneA&&!ai.m_doneB,"idle state initialized before watchdog");
 auto old=std::make_unique<Unit>(Unit{2,1}); Unit far{12,2},near{3,3};
 owner.grid={old.get(),&far};ai.FindTargets();check(ai.m_nearestTarget==old.get(),"initial nearest target");
 ai.FindTargets();check(ai.m_targetList.size()==2,"repeated scan does not accumulate duplicates");
 owner.grid={&far,&near};old.reset();
 ai.FindTargets();check(ai.m_nearestTarget==&near&&ai.m_targetList.size()==2,"destroyed grid unit discarded before any dereference");
 owner.grid.clear();ai.FindTargets();check(!ai.m_nearestTarget&&ai.m_nearestDistance==0&&ai.m_targetList.empty(),"empty grid clears previous combat target");
 Unit gorerot{4,NPC_GOREROT},sylvanas{4,NPC_LADY_SYLVANAS_WINDRUNNER};
 owner.grid={&gorerot};ai.FindTargets();if(hasSpacing)check(ai.m_checkDistance==16,"native Gorerot spacing retained");
 owner.grid={&sylvanas};ai.FindTargets();if(hasSpacing)check(ai.m_checkDistance==25,"native Sylvanas spacing retained");
 owner.grid={&near};ai.FindTargets();if(hasSpacing)check(ai.m_checkDistance==15,"ordinary spacing restored");
}
int main(){try{ EXERCISES std::cout<<"Gilneas battle: six production scans and idle states PASS\n"; }catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;} }
'''
    names = [c.split('{')[0].split()[1] for c in classes]
    code = code.replace('PRODUCTION', '\n'.join(classes)).replace('EXERCISES', ''.join('exercise<' + n + '>(' + ('true' if 'm_checkDistance = 15.0f' in c else 'false') + ');' for n, c in zip(names, classes)))
    with tempfile.TemporaryDirectory(prefix='gilneas-battle-') as folder:
        cpp = Path(folder) / 'battle.cpp'
        binary = Path(folder) / ('battle.exe' if os.name == 'nt' else 'battle')
        cpp.write_text(code, 'utf8')
        command = [os.environ.get('CXX', 'g++'), '-std=c++17', '-Wall', '-Wextra', '-Werror', '-g', str(cpp), '-o', str(binary)]
        if not args.no_sanitizers:
            command += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-fno-pie', '-no-pie']
        subprocess.run(command, check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
