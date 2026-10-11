#!/usr/bin/env python3
"""Actual controller arrival cases and wave readiness predicate."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    guards=[]
    for name in ['npc_krennan_aranas_38553','npc_sister_almyra_38466','npc_prince_liam_greymane_38218','npc_myriam_spellwaker_38465','npc_lorna_crowley_38426','npc_lord_darius_crowley_38415','npc_king_genn_greymane_38470']:
        body=s[s.index('class '+name+' :'):]
        guards.append('struct '+name+'{'+method(body,'        void DamageTaken(').replace(' override','')+'};')
    guard_checks=''.join('{'+name+' ai;uint32 damage=100000;ai.DamageTaken(nullptr,damage);check(damage==0,"critical allied actor survives combat damage");}' for name in ['npc_krennan_aranas_38553','npc_sister_almyra_38466','npc_prince_liam_greymane_38218','npc_myriam_spellwaker_38465','npc_lorna_crowley_38426','npc_lord_darius_crowley_38415','npc_king_genn_greymane_38470'])
    s=s[s.index('class npc_sister_almyra_38466 :'):s.index('class npc_prince_liam_greymane_38218 :')]
    actions=s[s.index('                case ACTION_LIAM_ARRIVED:'):s.index('\n            }\n        }\n\n        void SetGUID')]
    assert 'if (AreWaveLeadersReady(IsPlayerNear(25.0f)))' in s
    selection=method((root/'src/server/game/Entities/Object/Object.cpp').read_text('utf8'),'std::list<Player*> WorldObject::SelectNearestPlayers(')
    code=r'''
#include <cstdint>
#include <list>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
enum{ACTION_LIAM_ARRIVED=1,ACTION_MYRIAM_ARRIVED,ACTION_LORNA_ARRIVED,ACTION_DARIUS_ARRIVED,ACTION_GENN_ARRIVED,ACTION_SYLVANAS_ARRIVED};
struct Player{bool alive;float distance;};
struct WorldObject{std::list<Player*> SelectNearestPlayers(float,bool);};
namespace Trinity{
struct AnyPlayerInObjectRangeCheck{float range;bool alive;AnyPlayerInObjectRangeCheck(WorldObject*,float r,bool a):range(r),alive(a){}bool operator()(Player*p){return p->distance<=range&&p->alive==alive;}};
template<class Check>struct PlayerListSearcher{std::list<Player*>&out;Check&check;PlayerListSearcher(WorldObject*,std::list<Player*>&o,Check&c):out(o),check(c){}};
}
Player nearbyPlayer{true,5},deadPlayer{false,5},distantPlayer{true,50};
namespace Cell{
template<class T>void VisitGridObjects(WorldObject*,T&,float){} // No Player in AllGridObjectTypes.
template<class T>void VisitWorldObjects(WorldObject*,T&v,float){for(Player*p:{&nearbyPlayer,&deadPlayer,&distantPlayer})if(v.check(p))v.out.push_back(p);}
}
struct Unit{};
GUARDS
SELECTION
struct Controller{uint32 m_wave=0,m_arrivedMask=0;
PREDICATE
void Arrived(int action){switch(action){ACTIONS}}
};
void check(bool ok,char const*message){if(!ok)throw std::runtime_error(message);}
int main(){try{
 GUARD_CHECKS
 WorldObject world;auto players=world.SelectNearestPlayers(25,true);check(players.size()==1&&players.front()==&nearbyPlayer,"real player selector visits world container and preserves alive/radius checks");
 Controller c;c.m_wave=7;c.Arrived(ACTION_DARIUS_ARRIVED);check(c.m_arrivedMask==16,"Darius arrival never marks Genn");c.Arrived(ACTION_DARIUS_ARRIVED);check(c.m_arrivedMask==16,"duplicate arrival idempotent");c.Arrived(ACTION_GENN_ARRIVED);check(c.m_arrivedMask==48,"independent Genn arrival");
 for(uint32 wave=1;wave<=7;++wave){c.m_wave=wave;uint32 leaders=wave<=2?7:wave==3?15:wave<=6?31:63;c.m_arrivedMask=leaders;check(c.AreWaveLeadersReady(true),"all native leaders and player allow transition");for(uint32 bit=1;bit<=32;bit*=2)if(leaders&bit){c.m_arrivedMask=leaders&~bit;check(!c.AreWaveLeadersReady(true),"each required leader independently blocks transition");}c.m_arrivedMask=leaders;check(c.AreWaveLeadersReady(true),"presence initially recorded");check(c.AreWaveLeadersReady(false)==(wave<=2),"leaving player blocks only original presence-gated waves");check(!(c.m_arrivedMask&128),"stale player bit removed");check(c.AreWaveLeadersReady(true),"returning player resumes eligibility");}
 c.m_arrivedMask=255;for(uint32 wave:{0u,8u,0xffffffffu}){c.m_wave=wave;check(!c.AreWaveLeadersReady(true),"invalid wave never uses undefined mask");}
 std::cout<<"Gilneas battle synchronization: production arrival cases and readiness PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''.replace('PREDICATE',method(s,'        bool AreWaveLeadersReady(')).replace('ACTIONS',actions)
    code=code.replace('SELECTION',selection).replace('GUARDS','\n'.join(guards)).replace('GUARD_CHECKS',guard_checks)
    with tempfile.TemporaryDirectory() as folder:
        cpp=Path(folder)/'sync.cpp';exe=Path(folder)/'sync.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
        if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
        subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
