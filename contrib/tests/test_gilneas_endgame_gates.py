#!/usr/bin/env python3
"""Native Lorna participant and ship-floor gates, controlled world boundaries."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
    source=source[source.index('    struct npc_lorna_crowley_43566AI'):]
    code=r'''
#include <list>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;
enum{QUEST_ENDGAME=26706,QUEST_STATUS_INCOMPLETE=3,NPC_GUNSHIP_GRUNT=42141};
struct Transport{}ship,otherShip;
struct Position{float z=86;float GetPositionZ(){return z;}};
struct Unit{int entry=42141,map=654,phase=188;bool alive=true;Transport*transport=&ship;Position pos;int GetEntry(){return entry;}Transport*GetTransport(){return transport;}Position GetTransOffset(){return pos;}int GetMapId(){return map;}bool IsAlive(){return alive;}};
struct Player:Unit{int status=QUEST_STATUS_INCOMPLETE;bool combat=false;int GetQuestStatus(int){return status;}bool IsInCombat(){return combat;}};
struct Creature:Unit{std::list<Player*>players;std::list<Unit*>targets;bool IsInPhase(Unit*u){return phase==u->phase;}std::list<Player*>SelectNearestPlayers(float){return players;}void GetAttackableUnitListInRange(std::list<Unit*>&out,float){out=targets;}};
void check(bool b,char const*m){if(!b)throw std::runtime_error(m);}
struct Gates{Creature*me;
'''
    for signature in ['        bool IsSceneParticipant(', '        bool IsPlayerInCombat()', '        bool IsPlayerInRange(', '        uint32 CountGruntOnThisFloorZ(']:
        code+=method(source,signature)
    code+=r'''
};
int main(){Creature lorna;Gates g{&lorna};Player valid,outsider;outsider.status=0;outsider.combat=true;lorna.players={&outsider,&valid};
check(g.IsPlayerInRange(15)&&!g.IsPlayerInCombat(),"nearby outsider cannot mask participant or stall scene with combat");valid.combat=true;check(g.IsPlayerInCombat(),"participant combat still blocks progression");
for(int reason=0;reason<6;++reason){Player p;p.combat=true;if(reason==0)p.alive=false;if(reason==1)p.status=0;if(reason==2)p.map=1;if(reason==3)p.phase=1;if(reason==4)p.transport=nullptr;if(reason==5)p.transport=&otherShip;lorna.players={&p};check(!g.IsSceneParticipant(&p)&&!g.IsPlayerInRange(50)&&!g.IsPlayerInCombat(),"dead/abandoned/map/phase/off-ship/other-ship player excluded");}
lorna.players={&valid};lorna.transport=nullptr;check(!g.IsPlayerInRange(50)&&!g.IsPlayerInCombat(),"scene without ship cannot advance");lorna.transport=&ship;check(!g.IsSceneParticipant(nullptr),"null participant rejected");
Unit grunt,otherEnemy,otherFloor,otherPhase,offShip,otherBoat;otherEnemy.entry=43567;otherFloor.pos.z=34;otherPhase.phase=1;offShip.transport=nullptr;otherBoat.transport=&otherShip;lorna.targets={&grunt,&otherEnemy,&otherFloor,&otherPhase,&offShip,&otherBoat};
check(g.CountGruntOnThisFloorZ(86,15)==1,"only same-ship same-phase grunt on requested floor counts");check(g.CountGruntOnThisFloorZ(34,3)==1,"lower floor still counts native grunt");lorna.targets={&otherEnemy,&otherPhase,&offShip,&otherBoat};check(g.CountGruntOnThisFloorZ(86,15)==0,"unrelated attackable targets cannot prevent clearing deck");lorna.targets={&grunt};lorna.transport=nullptr;check(g.CountGruntOnThisFloorZ(86,15)==0,"no transport excludes targets");
std::cout<<"PASS: native Endgame participant combat/range and same-ship grunt floor gates\n";}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
