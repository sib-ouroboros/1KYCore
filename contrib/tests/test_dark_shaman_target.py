#!/usr/bin/env python3
"""Exercise the production Foul Stream event and native distance/aura predicate."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root/'src/server/scripts/Pandaria/SiegeOfOrgrimmar/boss_korkron_dark_shaman.cpp').read_text('utf8')
    start = source.index('                    case EVENT_FOUL_STREAM:')
    end = source.index('                    case EVENT_ASHEN_WALL:', start)
    event = source[start:end]
    native = (root/'src/server/game/AI/CoreAI/UnitAI.cpp').read_text('utf8')
    start = native.index('bool DefaultTargetSelector::operator()')
    end = native.index('\nSpellTargetSelector::', start)
    predicate = native[start:end]
    constants = '\n'.join('constexpr int '+k+'='+re.search(r'\b'+k+r'\s*=\s*(\d+)', source)[1]+';' for k in ('SPELL_TOXIC_MIST','SPELL_FOUL_STREAM','TIMER_FOUL_STREAM'))
    harness = r'''
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint32=std::uint32_t; using int32=std::int32_t;
CONSTANTS
constexpr int EVENT_FOUL_STREAM=1, SELECT_TARGET_RANDOM=0;
struct Unit {
    float distance; bool player; bool mist;
    bool IsPlayer() const { return player; }
    bool HasAura(int32 spell) const { return spell==SPELL_TOXIC_MIST && mist; }
    bool IsWithinCombatRange(Unit const* other,float range) const { return other->distance<=range; }
};
struct DefaultTargetSelector {
    Unit const* me; float m_dist; bool m_playerOnly; int32 m_aura;
    bool operator()(Unit const* target) const;
};
PREDICATE
void check(bool ok) { if(!ok) throw std::runtime_error("dark shaman selection regression"); }
struct Events { int calls=0; void ScheduleEvent(int event,int delay) { check(event==EVENT_FOUL_STREAM && delay==TIMER_FOUL_STREAM); ++calls; } };
struct Handler {
    Unit boss{0,false,false}; std::vector<Unit*> candidates; Events events;
    Unit* cast=nullptr; unsigned attempts=0;
    Unit* SelectTarget(int mode,uint32 position=0,float distance=0,bool playerOnly=false,int32 aura=0) {
        check(mode==SELECT_TARGET_RANDOM && position==0 && playerOnly);
        check(distance==(attempts==0 ? -20.0f : 0.0f));
        check(aura==(attempts<2 ? -SPELL_TOXIC_MIST : 0));
        ++attempts;
        DefaultTargetSelector selector{&boss,distance,playerOnly,aura};
        // Deterministic candidate order replaces random sampling; filtering
        // uses the actual production predicate, not a copy of its rules.
        for(Unit* target:candidates) if(selector(target)) return target;
        return nullptr;
    }
    void DoCast(Unit* target,int spell) { check(spell==SPELL_FOUL_STREAM);cast=target; }
    void ExecuteEvent(int eventId) {
        switch(eventId) {
EVENT
        }
    }
};
int main() {
    Unit close{10,true,false},boundary{20,true,false},far{21,true,false},infected{40,true,true},pet{30,false,false};
    Handler first; first.candidates={&close,&boundary,&infected,&pet,&far}; first.ExecuteEvent(EVENT_FOUL_STREAM);
    check(first.cast==&far && first.attempts==1 && first.events.calls==1);
    Handler second;second.candidates={&infected,&pet,&boundary};second.ExecuteEvent(EVENT_FOUL_STREAM);
    check(second.cast==&boundary && second.attempts==2 && second.events.calls==1);
    Handler third;third.candidates={&pet,&infected};third.ExecuteEvent(EVENT_FOUL_STREAM);
    check(third.cast==&infected && third.attempts==3 && third.events.calls==1);
    Handler empty;empty.candidates={nullptr,&pet};empty.ExecuteEvent(EVENT_FOUL_STREAM);
    check(!empty.cast && empty.attempts==3 && empty.events.calls==1);
    std::cout<<"PASS: actual Foul Stream event / native selector, distant clean player, 20-yard boundary, both fallbacks, no player, timer\n";
}
'''.replace('CONSTANTS',constants).replace('PREDICATE',predicate).replace('EVENT\n',event+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'shaman.cpp';exe=Path(tmp)/'shaman';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined,float-cast-overflow','-fno-sanitize-recover=all',
            '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
