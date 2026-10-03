#!/usr/bin/env python3
"""Execute actual Stormstout creation block/event with native EventProcessor."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/Pandaria/StormstoutBrewery/instance_stormstout_brewery.cpp').read_text('utf8')
    event=source[source.index('    class StormstoutGushingBrewEvent final'):source.index('\n}\n\nclass instance_stormstout_brewery')]
    block=source[source.index('            case NPC_PURPOSE_BUNNY_GROUND:'):source.index('            case NPC_DRUNKEN_HOZEN_BRAWLER:')]
    header=(root/'src/server/scripts/Pandaria/StormstoutBrewery/stormstout_brewery.h').read_text('utf8')
    ids={name:re.search(r'\b'+name+r'\s*=\s*(\d+)',header)[1] for name in ('NPC_PURPOSE_BUNNY_GROUND','NPC_PURPOSE_BUNNY_FLYING','SPELL_GUSHING_BREW')}
    harness=r'''
#include "EventProcessor.h"
#include <iostream>
#include <stdexcept>
void check(bool value){if(!value)throw std::runtime_error("Stormstout brew event regression");}
CONSTANTS
unsigned totalCasts=0;
struct Creature {
    EventProcessor m_Events;
    Creature* nearby=nullptr;
    unsigned casts=0,removed=0,searches=0;
    void RemoveAurasDueToSpell(uint32 spell){check(spell==128571);++removed;}
    Creature* FindNearestCreature(uint32 entry,float range,bool alive){check(entry==NPC_PURPOSE_BUNNY_FLYING&&range==30.0f&&alive);++searches;return nearby;}
    void CastSpell(Creature* target,uint32 spell,bool triggered){check(target&&target==nearby&&spell==SPELL_GUSHING_BREW&&triggered);++casts;++totalCasts;}
};
EVENT
void created(Creature* creature,uint32 entry){switch(entry){BLOCK default:break;}}
int main(){
    Creature first,target;first.nearby=&target;first.m_Events.Update(1000);
    created(&first,NPC_PURPOSE_BUNNY_GROUND);check(first.removed==1&&first.casts==0);
    first.m_Events.Update(1499);check(first.searches==0);
    first.m_Events.Update(1);check(first.searches==1&&first.casts==1);
    first.m_Events.Update(5000);check(first.casts==1);
    Creature missing;created(&missing,NPC_PURPOSE_BUNNY_GROUND);missing.m_Events.Update(1500);check(missing.searches==1&&missing.casts==0);
    Creature gone;gone.nearby=&target;created(&gone,NPC_PURPOSE_BUNNY_GROUND);gone.nearby=nullptr;gone.m_Events.Update(1500);check(gone.casts==0);
    Creature cancelled;created(&cancelled,NPC_PURPOSE_BUNNY_GROUND);cancelled.m_Events.KillAllEvents(false);cancelled.m_Events.Update(1500);check(cancelled.searches==0);
    {Creature destroyed;created(&destroyed,NPC_PURPOSE_BUNNY_GROUND);}
    Creature unrelated;created(&unrelated,0);unrelated.m_Events.Update(2000);check(unrelated.removed==0&&unrelated.searches==0);
    check(totalCasts==1);
    std::cout<<"PASS: actual Stormstout creation block/event and native queue, 1500ms boundary, target lookup, missing target, cancellation/destruction\n";
}
'''.replace('CONSTANTS','\n'.join('constexpr uint32 '+name+'='+value+';' for name,value in ids.items())).replace('EVENT',event).replace('BLOCK',block)
    processor=root/'src/common/Utilities/EventProcessor.cpp'
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp)
        (directory/'Define.h').write_text('#pragma once\n#include <cstdint>\n#include <mutex>\nusing uint8=std::uint8_t;using uint32=std::uint32_t;using uint64=std::uint64_t;\n#define TC_COMMON_API\n',encoding='utf8')
        (directory/'Errors.h').write_text('#pragma once\n#include <cassert>\n#define ASSERT(value) assert(value)\n',encoding='utf8')
        cpp=directory/'brew.cpp';exe=directory/'brew';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g','-pthread',
            '-I',tmp,'-I',str(processor.parent),str(cpp),str(processor),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
