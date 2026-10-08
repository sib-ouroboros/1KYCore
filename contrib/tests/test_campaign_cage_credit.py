#!/usr/bin/env python3
"""Compile actual personal/group credit handlers for the three cage spells."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from test_gameobject_visuals import block


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[2];source=(root/'src/server/game/Spells/SpellEffects.cpp').read_text('utf8')
    reg=json.loads((root/'docs/audit-data/campaign-cage-state-restoration.json').read_text('utf8'))
    handlers={90:'EffectKillCreditPersonal',134:'EffectKillCredit'};cases=[]
    for spell,effects in reg['spell_effects']['effects'].items():
        assert len(effects)==1;effect=effects[0];handler=handlers[effect['Effect']]
        assert re.search(r'&Spell::'+handler+r',\s*//\s*'+str(effect['Effect'])+r'\s',source)
        assert effect['ImplicitTarget1']==1 and effect['TriggerSpell']==0
        target='personal' if effect['Effect']==90 else 'group'
        cases.append(f'''{{Player player;Effect effect{{{effect['MiscValue1']}}};Spell spell;spell.unitTarget=&player;spell.effectInfo=&effect;spell.{handler}(0);check(player.{target}.size()==1 && player.{target}[0]=={effect['MiscValue1']},"spell{spell} native credit");
        auto original=player.{target};spell.effectHandleMode=0;spell.{handler}(0);check(player.{target}==original,"other effect mode ignored");spell.effectHandleMode=1;spell.unitTarget=nullptr;spell.{handler}(0);Unit npc;spell.unitTarget=&npc;spell.{handler}(0);check(player.{target}==original,"null/NPC target ignored");}}''')
    header=r'''
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using SpellEffIndex=int;
constexpr int SPELL_EFFECT_HANDLE_HIT_TARGET=1,TYPEID_PLAYER=4;
struct Player;
struct Unit{virtual ~Unit()=default;virtual int GetTypeId(){return 3;}virtual Player* ToPlayer(){return nullptr;}};
struct Player:Unit{std::vector<uint32> personal,group;int GetTypeId()override{return 4;}Player* ToPlayer()override{return this;}void KilledMonsterCredit(uint32 entry){personal.push_back(entry);}void RewardPlayerAndGroupAtEvent(uint32 entry,Unit*){group.push_back(entry);}};
struct Effect{int32 MiscValue;};
struct Spell{int effectHandleMode=1;Unit* unitTarget=nullptr;Effect* effectInfo=nullptr;int32 damage=0;void EffectKillCreditPersonal(SpellEffIndex);void EffectKillCredit(SpellEffIndex);};
void check(bool x,char const* m){if(!x)throw std::runtime_error(m);}
'''
    functions='\n'.join(block(source,'void Spell::'+name+'(') for name in handlers.values())
    harness=header+functions+'\nint main(){try{'+''.join(cases)+r'''std::cout<<"PASS: three cage spells, actual personal/group credit dispatch, NPC credit entries, HIT_TARGET and player-only guards\n";}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);cpp=d/'credit.cpp';exe=d/'credit.exe';cpp.write_text(harness,'utf8')
        flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
