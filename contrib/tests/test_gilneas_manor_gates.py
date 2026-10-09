#!/usr/bin/env python3
"""Execute both native Manor gate AIs with controlled world/event boundaries."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r'''
#include <chrono>
#include <cstdint>
#include <list>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using namespace std::chrono_literals;
enum{QUEST_STATUS_NONE,QUEST_STATUS_COMPLETE,QUEST_STATUS_INCOMPLETE,QUEST_STATUS_REWARDED};
enum{QUEST_TO_GREYMANE_MANOR=14465,QUEST_EXODUS=24438,NPC_SWIFT_MOUNTAIN_HORSE=36741,NPC_HARNESS_43336=43336,EVENT_CHECK_PLAYER_NEAR=1,EVENT_COOLDOWN_00,PLAYER_GUID=1};
struct ObjectGuid{int id=0;};struct Player;struct AI;
struct Unit{virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}virtual Unit*GetCharmerOrOwner(){return nullptr;}virtual ObjectGuid GetGUID(){return {};}virtual AI*GetAI(){return nullptr;}};
struct Player:Unit{int manor=QUEST_STATUS_COMPLETE,exodus=QUEST_STATUS_NONE;Player*ToPlayer()override{return this;}int GetQuestStatus(int q){return q==QUEST_TO_GREYMANE_MANOR?manor:exodus;}};
struct AI{ObjectGuid GetGUID(int){return {};}};
struct Creature:Unit{ObjectGuid guid{1};Player*owner=nullptr;int entry=NPC_SWIFT_MOUNTAIN_HORSE;float distance=5;AI ai;ObjectGuid GetGUID()override{return guid;}Unit*GetOwner(){return owner;}Unit*GetCharmerOrOwner()override{return owner;}float GetDistance(void*){return distance;}AI*GetAI(){return &ai;}};
std::list<Creature*> horses;
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Update(uint32 d){now+=d;}
 template<class R,class P>void ScheduleEvent(uint32 e,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),e);}
 template<class R,class P>void RescheduleEvent(uint32 e,std::chrono::duration<R,P>d){for(auto i=events.begin();i!=events.end();)if(i->second==e)i=events.erase(i);else++i;ScheduleEvent(e,d);}
 uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto e=events.begin()->second;events.erase(events.begin());return e;}};
struct GameObject{int openings=0,resets=0;void GetCreatureListWithEntryInGrid(std::list<Creature*>&out,int entry,float){for(auto*h:horses)if(h->entry==entry)out.push_back(h);}void UseDoorOrButton(int){++openings;}void ResetDoorOrButton(){++resets;}};
void GetCreatureListWithEntryInGrid(std::list<Creature*>&out,GameObject*go,int entry,float radius){go->GetCreatureListWithEntryInGrid(out,entry,radius);}
namespace ObjectAccessor{Creature*GetCreature(GameObject&,ObjectGuid g){for(auto*h:horses)if(h->guid.id==g.id)return h;return nullptr;}Player*GetPlayer(GameObject&,ObjectGuid){return nullptr;}}
struct GameObjectAI{GameObject*go;GameObjectAI(GameObject*g):go(g){}virtual~GameObjectAI()=default;};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
'''
 for name in ['go_gate_196399AI','go_gate_196401AI']:
  code+=method(source,'    struct '+name+' :')+';\n'
 code+=r'''
template<class Gate>void test(){
 Player player;Creature horse;horse.owner=&player;horses={&horse};
 for(int status:{QUEST_STATUS_INCOMPLETE,QUEST_STATUS_COMPLETE}){
  player.manor=status;GameObject go;Gate ai(&go);ai.Reset();ai.UpdateAI(1000);check(go.openings==1,"active Manor quest must open gate");
  ai.UpdateAI(1000);check(go.openings==1,"no duplicate opening during cooldown");
  horse.distance=100;ai.UpdateAI(6000);check(go.resets==1&&go.openings==1,"gate closes and distant horse cannot reopen");horse.distance=5;
 }
 for(int status:{QUEST_STATUS_NONE,QUEST_STATUS_REWARDED}){player.manor=status;GameObject go;Gate ai(&go);ai.Reset();ai.UpdateAI(1000);check(!go.openings,"inactive Manor quest must not open gate");}
 player.manor=QUEST_STATUS_COMPLETE;horse.owner=nullptr;{GameObject go;Gate ai(&go);ai.Reset();ai.UpdateAI(1000);check(!go.openings,"ownerless horse denied");}horse.owner=&player;
}
int main(){test<go_gate_196399AI>();test<go_gate_196401AI>();Player player;player.manor=QUEST_STATUS_NONE;player.exodus=QUEST_STATUS_COMPLETE;Creature harness;harness.owner=&player;harness.entry=NPC_HARNESS_43336;horses={&harness};GameObject go;go_gate_196401AI ai(&go);ai.Reset();ai.UpdateAI(1000);check(go.openings==1,"existing Exodus gate behavior preserved");std::cout<<"PASS: both native Manor gate AIs; completed/incomplete quests, cooldown, no quest, rewarded, missing owner and Exodus\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8')
  flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
