#!/usr/bin/env python3
"""Native Endgame hippogryph callbacks; substitutes do not prove the ship scene."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using int8=std::int8_t;using namespace std::chrono_literals;
enum{QUEST_ENDGAME=26706,QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,EVENT_MOVEMENT_START=10,EVENT_MOVE_LAST_POINT=201,EVENT_EJECT_ALL_PASSENGER,EVENT_JUMP_TO_LORNA,WAYPOINT_MOTION_TYPE=2,POINT_MOTION_TYPE=8,MOVE_RUN=1,NPC_LORNA_CRAWLEY_43566=43566,PLAYER_GUID=1,EVENT_TELEPORT_01=123};
struct ObjectGuid{int id=0;static const ObjectGuid Empty;bool IsEmpty()const{return id==0;}};const ObjectGuid ObjectGuid::Empty{};bool operator==(ObjectGuid a,ObjectGuid b){return a.id==b.id;}bool operator!=(ObjectGuid a,ObjectGuid b){return !(a==b);}
struct Creature;struct Player;struct Position{float m_positionZ=0;};
struct Unit{virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}};
struct Player:Unit{ObjectGuid guid{1};bool alive=true;int map=654,status=QUEST_STATUS_INCOMPLETE,phase=1,exits=0;Creature*base=nullptr;Player*ToPlayer()override{return this;}bool IsAlive(){return alive;}int GetMapId(){return map;}int GetQuestStatus(int){return status;}ObjectGuid GetGUID(){return guid;}Creature*GetVehicleBase(){return base;}void ExitVehicle(){++exits;base=nullptr;}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){events.clear();now=0;}void Update(uint32 d){now+=d;}void ScheduleEvent(uint32 e,uint32 d){events.emplace(now+d,e);}template<class R,class P>void ScheduleEvent(uint32 e,std::chrono::duration<R,P>d){ScheduleEvent(e,std::chrono::duration_cast<std::chrono::milliseconds>(d).count());}void RescheduleEvent(uint32 e,uint32 d){for(auto i=events.begin();i!=events.end();)if(i->second==e)i=events.erase(i);else++i;ScheduleEvent(e,d);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto e=events.begin()->second;events.erase(events.begin());return e;}};
struct MotionMaster{int paths=0,points=0;void MovePath(uint32 id,bool){if(id!=4375101)throw std::runtime_error("wrong route");++paths;}void MovePoint(uint32,Position){++points;}};
struct ActorAI{void SetGUID(ObjectGuid,int){}void DoAction(int){}};
struct Creature:Unit{int map=654,phase=1,despawns=0;bool flying=false,gravity=false;MotionMaster motion;ActorAI ai;Creature*lorna=nullptr;int GetMapId(){return map;}bool IsInPhase(Player*p){return p->phase==phase;}Creature*FindNearestCreature(int entry,float){return entry==NPC_LORNA_CRAWLEY_43566?lorna:nullptr;}float GetOrientation(){return 0;}void SetOrientation(float){}void SetSpeed(int,float){}void SetCanFly(bool b){flying=b;}void SetDisableGravity(bool b){gravity=b;}MotionMaster*GetMotionMaster(){return &motion;}ActorAI*AI(){return &ai;}Position GetPosition(){return {};}ObjectGuid GetGUID(){return {5};}template<class T>void DespawnOrUnsummon(T){++despawns;}};
std::map<int,Player*>players;namespace ObjectAccessor{Player*GetPlayer(Creature&me,ObjectGuid guid){auto i=players.find(guid.id);return i!=players.end()&&i->second->map==me.map?i->second:nullptr;}Creature*GetCreature(Creature&me,ObjectGuid){return me.lorna;}}
struct ScriptedAI{Creature*me;ScriptedAI(Creature*c):me(c){}void UpdateAI(uint32){}};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
'''
 code+=method(source,'    struct npc_hippogryph_43751AI :')+';\n'
 code+=r'''
int main(){using AI=npc_hippogryph_43751AI;Player owner,other;other.guid.id=2;players={{1,&owner},{2,&other}};Creature bird;AI ai(&bird);ai.Reset();Unit accessory;
 ai.PassengerBoarded(nullptr,1,true);ai.PassengerBoarded(&accessory,1,true);ai.PassengerBoarded(&accessory,1,false);check(!bird.despawns&&ai.m_events.events.empty(),"accessories must not destroy ride");
 owner.base=&bird;ai.PassengerBoarded(&owner,0,true);ai.PassengerBoarded(&owner,0,true);check(ai.m_events.events.size()==1&&ai.m_playerGUID==owner.guid,"duplicate boarding starts once");
 other.base=&bird;ai.PassengerBoarded(&other,1,true);ai.PassengerBoarded(&other,1,false);check(other.exits==1&&!bird.despawns&&ai.m_playerGUID==owner.guid,"foreign player cannot hijack or destroy ride");
 ai.UpdateAI(999);check(!bird.motion.paths,"native takeoff delay preserved");ai.UpdateAI(1);check(bird.motion.paths==1&&bird.flying&&bird.gravity,"native flight starts");
 ai.MovementInform(WAYPOINT_MOTION_TYPE,7);check(!ai.m_events.events.empty(),"arrival schedules native handoff");owner.status=QUEST_STATUS_NONE;ai.UpdateAI(1);check(ai.m_finished&&owner.exits==1&&bird.despawns==1&&ai.m_events.events.empty(),"abandon cancels queued scene and dismounts");
 ai.MovementInform(WAYPOINT_MOTION_TYPE,7);ai.UpdateAI(10000);ai.JustDied(nullptr);check(bird.despawns==1&&ai.m_events.events.empty(),"finished ride stays idempotent");
 for(int reason=0;reason<5;++reason){Player p;p.guid.id=3;players[3]=&p;Creature c;AI x(&c);x.Reset();p.base=&c;x.PassengerBoarded(&p,0,true);if(reason==0)p.alive=false;if(reason==1)p.map=1;if(reason==2)p.phase=2;if(reason==3)players.erase(3);if(reason==4)p.base=nullptr;x.UpdateAI(1000);check(x.m_finished&&c.despawns==1&&!c.motion.paths&&x.m_events.events.empty(),"invalid owner cannot take off");}
 {Player p;p.guid.id=4;players[4]=&p;Creature c;AI x(&c);x.Reset();p.base=&c;x.PassengerBoarded(&p,0,true);x.PassengerBoarded(&p,0,false);x.UpdateAI(1000);check(x.m_finished&&!c.motion.paths,"owner dismount cancels pending takeoff");}
 std::cout<<"PASS: native Endgame hippogryph boarding/update/finish/movement; accessories, ownership, delays, abandon/death/logout/map/phase/vehicle loss\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
