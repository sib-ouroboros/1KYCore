#!/usr/bin/env python3
"""Exercise actual Blackhand blaze action and periodic caster lifetime with sanitizers."""
import os
from pathlib import Path
import re
import subprocess
import tempfile

def method(source, marker):
    start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/Draenor/BlackrockFoundry/boss_blackhand.cpp').read_text('latin1')
    header=(root/'src/server/scripts/Draenor/BlackrockFoundry/boss_blackhand.h').read_text('latin1')
    action=method(source[source.index('struct npc_foundry_blaze_controllerAI'):],'            void DoAction(int32 p_Action)')
    tick=method(source[source.index('class spell_foundry_blaze_growth'):],'            void OnTick(AuraEffect const* /*p_AurEff*/)')
    actions=re.search(r'enum eBlackhandActions\s*\{.*?\};',header,re.S)[0]
    count=int(re.search(r'\bMaxBlazeSpreadCount\s*=\s*(\d+)',header)[1])
    blaze=int(re.search(r'\bBlaze\s*=\s*(\d+)',header)[1])
    harness=r"""
#include <cstdint>
#include <cmath>
#include <list>
#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint8=std::uint8_t;using int32=std::int32_t;
ACTIONS
namespace eBlackhandDatas{constexpr uint8 MaxBlazeSpreadCount=COUNT;}
namespace eBlackhandCreatures{constexpr uint32 Blaze=BLAZE;}
namespace TimeConstants{constexpr uint32 IN_MILLISECONDS=1000;}
enum class TempSummonType {TEMPSUMMON_TIMED_DESPAWN};
struct ObjectGuid{uint32 value=0;operator bool()const{return value!=0;}};
struct Position {
    float x,y,z,o;
    static void NormalizeOrientation(float& angle){angle=std::fmod(angle,float(2*M_PI));if(angle<0)angle+=float(2*M_PI);}
};
struct FakeAI {
    uint32 calls=0,assigned=0;ObjectGuid owner;
    virtual ~FakeAI()=default;
    virtual void DoAction(int32 action){if(action!=eBlackhandActions::BlackhandSpreadBlaze)throw std::runtime_error("unexpected action");++calls;}
    void SetGUID(ObjectGuid guid){owner=guid;++assigned;}
};
struct Creature;
struct Unit{virtual ~Unit()=default;virtual Creature* ToCreature(){return nullptr;}};
struct AreaTrigger {};
struct Creature : Unit {
    float m_positionX=0,m_positionY=0,m_positionZ=5;
    bool IsAIEnabled=true,failSummon=false;
    ObjectGuid guid{100};FakeAI basic;FakeAI* brain=&basic;
    Creature* output=nullptr;
    std::vector<Position> summons;
    Creature* ToCreature()override{return this;}
    FakeAI* AI(){return brain;}
    ObjectGuid GetGUID()const{return guid;}
    Creature* SummonCreature(uint32 entry,Position pos,TempSummonType,uint32 duration){
        if(entry!=eBlackhandCreatures::Blaze||duration!=60000)throw std::runtime_error("spawn contract changed");
        summons.push_back(pos);return failSummon?nullptr:output+summons.size()-1;
    }
};
namespace ObjectAccessor {
    Creature* owner=nullptr;uint32 lookups=0,available=99;
    Creature* GetCreature(Creature&,ObjectGuid guid){++lookups;if(!guid)throw std::runtime_error("empty GUID lookup");return lookups<=available?owner:nullptr;}
}
struct Controller : FakeAI {
    Creature* me;ObjectGuid m_Controller;float m_Orientation=0;
    explicit Controller(Creature* creature):me(creature){}
ACTION
};
struct AuraEffect {};
struct Growth {
    Unit* caster=nullptr;
    Unit* GetCaster(){return caster;}
TICK
};
void check(bool ok){if(!ok)throw std::runtime_error("Blackhand blaze controller regression");}
int main(){
    for(bool hasOwner:{false,true})for(bool ownerPresent:{false,true})for(bool enabled:{false,true})for(bool failed:{false,true}){
        Creature me,parent;Creature children[COUNT];Controller ai(&me);me.output=children;
        ai.m_Controller=ObjectGuid{hasOwner?900u:0u};me.failSummon=failed;
        for(auto& child:children)child.IsAIEnabled=enabled;
        ObjectAccessor::owner=ownerPresent?&parent:nullptr;ObjectAccessor::lookups=0;ObjectAccessor::available=99;
        ai.DoAction(eBlackhandActions::BlackhandSpreadBlaze);
        uint32 expected=(!hasOwner||ownerPresent)?COUNT:0;
        check(me.summons.size()==expected);
        check(ObjectAccessor::lookups==(hasOwner?COUNT:0));
        for(uint32 i=0;i<expected;++i){
            check(children[i].basic.assigned==static_cast<uint32>(enabled&&!failed));
            if(enabled&&!failed)check(children[i].basic.owner.value==(hasOwner?900u:100u));
            auto const& p=me.summons[i];check(std::abs(p.x-10*std::cos(float(i*M_PI/2)))<0.001f);
            check(std::abs(p.y-10*std::sin(float(i*M_PI/2)))<0.001f&&p.z==5);
        }
        check(std::abs(ai.m_Orientation-float(COUNT*M_PI/2))<0.001f);
    }
    Creature me,parent;Creature children[COUNT];Controller ai(&me);me.output=children;ai.m_Controller={900};
    ObjectAccessor::owner=&parent;ObjectAccessor::lookups=0;ObjectAccessor::available=1;
    ai.DoAction(eBlackhandActions::BlackhandSpreadBlaze);check(me.summons.size()==1);
    me.summons.clear();ai.DoAction(-1);check(me.summons.empty());
    Growth aura;Unit player;
    aura.OnTick(nullptr);aura.caster=&player;aura.OnTick(nullptr);
    Creature fire;aura.caster=&fire;fire.IsAIEnabled=false;aura.OnTick(nullptr);check(fire.basic.calls==0);
    fire.IsAIEnabled=true;aura.OnTick(nullptr);check(fire.basic.calls==1);
    std::cout<<"PASS: actual Blackhand blaze action, root/linked/missing/disappearing controller, owner inheritance, original geometry/count/lifetime, summon failure, disabled AI and null/noncreature aura caster\n";
}
""".replace('ACTIONS',actions).replace('ACTION',action).replace('TICK',tick).replace('COUNT',str(count)).replace('BLAZE',str(blaze))
    with tempfile.TemporaryDirectory() as tmp:
        cpp,exe=Path(tmp)/'blaze.cpp',Path(tmp)/'blaze'
        cpp.write_text(harness,encoding='utf8')
        # The unchanged action contains an unused variable in a commented geometry filter.
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
                        '-Wno-unused-variable','-Wno-misleading-indentation',
                        '-fsanitize=address,undefined','-fno-sanitize-recover=all','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)

if __name__=='__main__':
    main()
