#!/usr/bin/env python3
"""Execute native Endgame passenger readiness and late ship registration methods."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <vector>
#include <list>
#include <stdexcept>
#include <iostream>
#define TC_LOG_INFO(...) ((void)0)
using uint32=std::uint32_t;using int32=std::int32_t;
enum{QUEST_ENDGAME=26706,NPC_LORNA_CRAWLEY_43566=43566,NPC_WORGEN_WARRIOR=43651,NPC_GILNEAN_SHARPSHOOTER=43703,NPC_GUNSHIP_GRUNT=42141,NPC_GILNEAS_VEHICLE_ROPE=43793,GO_ROPE=204428,NPC_TOBIAS_MISTMANTLE_43749=43749,ACTION_EVENT_ID_25663=25663,ACTION_EVENT_ID_25664=25664,ACTION_EVENT_ID_25670=25670,ACTION_EVENT_ID_25727=25727};
struct ObjectGuid{int id=0;};bool operator!=(ObjectGuid a,ObjectGuid b){return a.id!=b.id;}
struct WorldLocation{WorldLocation(int,float,float,float,float){}};
struct Player{void TeleportTo(WorldLocation){}};
struct Creature;struct GameObject;struct Transport;
struct WorldObject{virtual~WorldObject()=default;virtual Creature*ToCreature(){return nullptr;}virtual GameObject*ToGameObject(){return nullptr;}Transport*transport=nullptr;Transport*GetTransport(){return transport;}};
struct ActorAI{int calls=0,last=0;void DoAction(int action){++calls;last=action;}};
struct Creature:WorldObject{int entry=0;bool alive=true,IsAIEnabled=true;ActorAI ai;Creature*ToCreature()override{return this;}bool IsAlive(){return alive;}int GetEntry(){return entry;}ActorAI*AI(){return &ai;}};
struct Map{int loads=0;void LoadGrid(float,float){++loads;}};
struct ShipAI{bool m_boardingWindow=false;ObjectGuid m_tobiasGUID,m_triggerGUID;GameObject*go=nullptr;uint32 GetData(uint32)const;void EventInform(uint32);void SetGUID(ObjectGuid,int32);};
struct GameObject:WorldObject{int entry=GO_ROPE,map=654;ShipAI*ai=nullptr;GameObject*ToGameObject()override{return this;}int GetEntry(){return entry;}virtual Transport*ToTransport(){return nullptr;}ShipAI*AI(){return ai;}std::list<Player*>SelectNearestPlayers(float){return {};}};
struct TaxiNode{uint32 ArrivalEventID=ACTION_EVENT_ID_25670;};
struct KeyFrame{TaxiNode const*Node;uint32 ArriveTime=1000,DepartureTime=181000;};
struct Transport:GameObject{TaxiNode node;uint32 timer=1000;std::vector<KeyFrame>frames{{&node,1000,181000}};uint32 GetTimer(){return timer;}uint32 GetTransportPeriod(){return 600000;}std::vector<KeyFrame>const&GetKeyFrames(){return frames;}Map grid;int reloads=0;std::vector<WorldObject*>passengers;Transport*ToTransport()override{return this;}int GetMapId(){return map;}Map*GetMap(){return &grid;}float GetPositionX(){return 1;}float GetPositionY(){return 2;}std::vector<WorldObject*>const&GetStaticPassengers(){return passengers;}void LoadStaticPassengers(){++reloads;}};
Creature harbor;namespace ObjectAccessor{GameObject*ship=nullptr;GameObject*GetGameObject(Creature&,ObjectGuid){return ship;}Creature*GetCreature(GameObject&,ObjectGuid guid){return guid.id==1?&harbor:nullptr;}}
struct Harbor{uint32 m_readinessReportCooldown=0;Creature*me=&harbor;ObjectGuid m_gunshipGUID{2};bool CheckIsGunshipReady();};
void check(bool ok,char const*msg){if(!ok)throw std::runtime_error(msg);}
'''
 part=source[source.index('    struct go_worgen_gunship_203428AI'):]
 for signature in ['        uint32 GetData(', '        void EventInform(', '        void SetGUID(']:
  body=method(part,signature)
  name={'        uint32 GetData(':'uint32 ShipAI::GetData(', '        void EventInform(':'void ShipAI::EventInform(', '        void SetGUID(':'void ShipAI::SetGUID('}[signature]
  code+=body.replace(signature.strip(),name,1)+'\n'
 part=source[source.index('class npc_tobias_mistmantle_43749 :'):]
 code+=method(part,'        bool CheckIsGunshipReady()').replace('bool CheckIsGunshipReady()', 'bool Harbor::CheckIsGunshipReady()',1)
 code+=r'''
int main(){Transport ship;ShipAI ai;ai.go=&ship;ship.ai=&ai;ObjectAccessor::ship=&ship;Harbor npc;
 ai.EventInform(ACTION_EVENT_ID_25670);check(ai.GetData(QUEST_ENDGAME)==1&&harbor.ai.calls==0,"arrival retained before harbor registration");ai.SetGUID({1},NPC_TOBIAS_MISTMANTLE_43749);check(harbor.ai.last==ACTION_EVENT_ID_25670&&harbor.ai.calls==1,"late registration replays current window");ai.SetGUID({1},NPC_TOBIAS_MISTMANTLE_43749);check(harbor.ai.calls==1,"registration is idempotent");
 check(!npc.CheckIsGunshipReady()&&ship.reloads==1,"empty grid requests load but never opens boarding");
 std::vector<Creature>actors(46);int index=0;for(auto pair:std::vector<std::pair<int,int>>{{43566,1},{43651,4},{43703,4},{42141,22},{43793,15}})for(int n=0;n<pair.second;++n){actors[index].entry=pair.first;actors[index].transport=&ship;ship.passengers.push_back(&actors[index++]);}
 GameObject rope1,rope2;rope1.transport=&ship;rope2.transport=&ship;ship.passengers.push_back(&rope1);ship.passengers.push_back(&rope2);
 check(npc.CheckIsGunshipReady(),"all required participants and ropes open boarding");ai.m_boardingWindow=false;check(npc.CheckIsGunshipReady(),"actual dock timer recovers missed arrival callback");
 for(int n: {0,1,5,31}){actors[n].alive=false;check(!npc.CheckIsGunshipReady(),"dead required passenger blocks incomplete scene");actors[n].alive=true;}
 actors[9].alive=false;check(npc.CheckIsGunshipReady(),"defeated guard does not invalidate loaded scene");actors[9].alive=true;
 ship.passengers.pop_back();check(!npc.CheckIsGunshipReady(),"missing ropes block entry");ship.passengers.push_back(&rope2);
 actors[0].IsAIEnabled=false;check(!npc.CheckIsGunshipReady(),"disabled Lorna blocks entry");actors[0].IsAIEnabled=true;
 ship.timer=181000;ai.EventInform(ACTION_EVENT_ID_25664);check(!npc.CheckIsGunshipReady(),"departure closes boarding even with full crew");ai.EventInform(ACTION_EVENT_ID_25663);check(!npc.CheckIsGunshipReady(),"leaving-ship event never opens new boarding");ai.EventInform(ACTION_EVENT_ID_25727);check(!npc.CheckIsGunshipReady(),"destruction never opens boarding");ship.timer=1000;ai.EventInform(ACTION_EVENT_ID_25670);check(npc.CheckIsGunshipReady(),"arrival opens real docking window");ship.timer=61000;check(npc.CheckIsGunshipReady(),"120 seconds remaining allows safe flight");ship.timer=61001;check(!npc.CheckIsGunshipReady(),"insufficient docking time blocks late launch");ship.timer=181000;check(!npc.CheckIsGunshipReady(),"departed dock rejected even if event not yet processed");ship.timer=1000;
 ship.map=1;check(!npc.CheckIsGunshipReady(),"other map rejected");ObjectAccessor::ship=nullptr;check(!npc.CheckIsGunshipReady(),"missing ship rejected");
 std::cout<<"PASS: native ship readiness, grid activation, required crew/ropes, late registration and cycle window\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
