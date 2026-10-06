#!/usr/bin/env python3
"""Compile production actor-spawn event and cleanup; inject each summon failure."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8');s=source[source.index('class npc_tobias_mistmantle_38507 :'):source.index('// 38530')]
 code=r"""
#include <cstdint>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr int TEMPSUMMON_TIMED_DESPAWN=1;
ENUM
EVENTS
struct ObjectGuid{int id=0;};
struct Motion{int clears=0;void Clear(){++clears;}};
struct Creature{Motion motion;int despawns=0;Motion*GetMotionMaster(){return &motion;}void DespawnOrUnsummon(){++despawns;}Creature*SummonCreature(int,float,float,float,float,int,int);};
std::map<int,Creature*>actors;namespace ObjectAccessor{Creature*GetCreature(Creature&,ObjectGuid g){auto i=actors.find(g.id);return i==actors.end()?nullptr:i->second;}}
struct Events{int resets=0;void Reset(){++resets;}};
struct Tobias{Creature*me;Events m_events;ObjectGuid m_sylvanasGUID,m_warhowlGUID,m_crenshawGUID;bool m_stopped=false,m_sceneActorsSpawned=false;
CLEANUP
void Spawn(){switch(int(EVENT_MOVEMENT_START_SYLVANAS_AI)){SPAWN_CASE}}
};
Tobias*current;Creature warhowl,sylvanas,crenshaw;int attempts=0,fail=0;
Creature*Creature::SummonCreature(int entry,float,float,float,float,int,int){++attempts;if(attempts==fail)return nullptr;Creature*child=nullptr;int id=0;if(entry==NPC_GENERAL_WARHOWL){child=&warhowl;id=3;current->m_warhowlGUID={id};}if(entry==NPC_LADY_SYLVANAS_WINDRUNNER_38530){child=&sylvanas;id=4;current->m_sylvanasGUID={id};}if(entry==NPC_HIGH_EXECUTOR_CRENSHAW){child=&crenshaw;id=5;current->m_crenshawGUID={id};}actors[id]=child;return child;}
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
int main(){try{for(int failure=0;failure<=3;++failure){Creature guide,foreign;warhowl={};sylvanas={};crenshaw={};actors={{99,&foreign}};Tobias t;t.me=&guide;current=&t;attempts=0;fail=failure;t.Spawn();if(!failure){check(!t.m_stopped&&attempts==3&&!guide.despawns,"all three successful summons retain native scene");t.Spawn();check(attempts==3,"spawn event latches once");}else{check(t.m_stopped&&attempts==failure&&guide.despawns==1&&t.m_events.resets==1,"failed summon stops immediately and cancels events");check(warhowl.despawns==(failure>1)&&sylvanas.despawns==(failure>2)&&!crenshaw.despawns,"only successfully tracked actors cleaned");t.Spawn();t.StopScene();check(attempts==failure&&guide.despawns==1,"failure cannot restart or clean twice");}check(!foreign.despawns,"unrelated actor untouched");}std::cout<<"Native Tobias partial summon cleanup and unrelated preservation: PASS\n";}catch(std::exception const&e){std::cerr<<e.what();return 1;}}
"""
 code=code.replace('ENUM',method(source,'enum eBattleForGilneas')+';').replace('EVENTS',method(s,'    enum eNpc')+';').replace('CLEANUP',method(s,'        void StopScene(')).replace('SPAWN_CASE',method(s,'                    case EVENT_MOVEMENT_START_SYLVANAS_AI:'))
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
