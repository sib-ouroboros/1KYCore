#!/usr/bin/env python3
"""Exercise the actual periodic mastery hit handler, with a stubbed damage helper."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/Spells/spell_monk.cpp').read_text('utf8')
    block=source[source.index('class spell_monk_mastery_combo_strikes_periodic_triggers :'):]
    start=block.index('        void HandleHit(');end=block.index('\n        void Register()',start)
    method=block[start:end]
    constants='\n'.join('constexpr int32 '+name+'='+value+';' for name,value in
        re.findall(r'^\s*(SPELL_MONK_(?:FISTS_OF_FURY|SPINNING_CRANE_KICK|WHIRLING_DRAGON_PUNCH)(?:_DAMAGE)?)\s*=\s*(\d+)',source,re.M))
    assert constants.count('constexpr')==6
    harness=r'''
#include <cstdint>
#include <iostream>
#include <stdexcept>
using int32=std::int32_t;using SpellEffIndex=int;
CONSTANTS
struct PlayerStorage{};
struct Player;
struct Unit{Player* player=nullptr;Player* ToPlayer(){return player;}};
struct Player:Unit{PlayerStorage* storage=nullptr;PlayerStorage* GetStorage(){return storage;}};
struct Info{int32 Id;};
struct spell_monk_mastery_combo_strikes{
    static int calls,id;static bool repeat;
    static void TryToHandleDamage(Player*,int32 spell,int32& damage,bool repeated){++calls;id=spell;repeat=repeated;damage+=7;}
};
int spell_monk_mastery_combo_strikes::calls=0,spell_monk_mastery_combo_strikes::id=0;
bool spell_monk_mastery_combo_strikes::repeat=false;
struct Handler{
    Unit* caster=nullptr;Info info{0};int32 damage=100;unsigned writes=0;
    Unit* GetCaster(){return caster;}Info* GetSpellInfo(){return &info;}
    int32 GetHitDamage(){return damage;}void SetHitDamage(int32 value){damage=value;++writes;}
METHOD
};
void check(bool ok){if(!ok)throw std::runtime_error("monk mastery guard failed");}
int main(){
    PlayerStorage storage;Player player;player.player=&player;player.storage=&storage;
    int32 inputs[]={117418,107270,158221},outputs[]={113656,101546,152175};
    for(unsigned i=0;i<3;++i){
        Handler h;h.caster=&player;h.info.Id=inputs[i];h.HandleHit(0);
        check(h.damage==107&&h.writes==1);
        check(spell_monk_mastery_combo_strikes::id==outputs[i]&&spell_monk_mastery_combo_strikes::repeat);
    }
    check(spell_monk_mastery_combo_strikes::calls==3);
    for(int32 id:{0,100780,2147483647}){
        Handler h;h.caster=&player;h.info.Id=id;h.HandleHit(0);check(h.damage==100&&h.writes==0);
    }
    Handler h;h.info.Id=117418;h.HandleHit(0);check(h.writes==0);
    player.storage=nullptr;h.caster=&player;h.HandleHit(0);check(h.writes==0);
    check(spell_monk_mastery_combo_strikes::calls==3);
    std::cout<<"PASS: actual monk hit handler, three native mappings, unknown spell leaves damage unchanged, null caster/storage\n";
}
'''.replace('CONSTANTS',constants).replace('METHOD',method)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'monk.cpp';exe=Path(tmp)/'monk';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=undefined',
            '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
