#!/usr/bin/env python3
"""Native Endgame escape AI and Lorna boarding case; world/spline are substitutes."""
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
#include <list>
#include <vector>
#include <string>
#include <algorithm>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using int8=std::int8_t;using namespace std::chrono_literals;
enum{PLAYER_GUID=1,QUEST_ENDGAME=26706,QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,WAYPOINT_MOTION_TYPE=2,EVENT_MOVEMENT_START=10,EVENT_MOVE_PART1=11,EVENT_MOVE_PART2=12,EVENT_TALK_PART_15=15,EVENT_TALK_PART_14=14};
struct ObjectGuid{using LowType=int;int id=0;static const ObjectGuid Empty;bool IsEmpty()const{return !id;}std::string ToString()const{return std::to_string(id);}};const ObjectGuid ObjectGuid::Empty{};bool operator==(ObjectGuid a,ObjectGuid b){return a.id==b.id;}bool operator!=(ObjectGuid a,ObjectGuid b){return !(a==b);}
struct Player;struct Creature;struct ScriptedAI;
struct CreatureData{int id=0;float posX=0,posY=0,posZ=0,orientation=0;};
enum class HighGuid{GameObject};struct Map{int next=100;template<HighGuid>int GenerateLowGuid(){return next++;}}worldMap;
struct Position{float GetPositionX(){return 1;}float GetPositionY(){return 2;}float GetPositionZ(){return 3;}float GetOrientation(){return 0;}};
struct Transport{std::list<Creature*>queue;Creature*CreateNPCPassenger(int,CreatureData*);int attempts=0;}defaultTransport;
std::vector<std::string>traceStates;
template<class...T>void captureTrace(char const*,char const*,char const*state,T...args){traceStates.emplace_back(state);((void)args,...);}
#define TC_LOG_DEBUG(...) captureTrace(__VA_ARGS__)
int spawnErrors=0;
#define TC_LOG_ERROR(...) (++spawnErrors)
std::list<Player*>selectedPlayers;
struct ObjectMgr{std::map<int,CreatureData>data;int gridAdds=0;CreatureData&NewOrExistCreatureData(int g){return data[g];}void AddCreatureToGrid(int,CreatureData*){++gridAdds;}}objectMgr;auto*sObjectMgr=&objectMgr;
struct Unit{virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}};
struct WorldLocation{int map;WorldLocation(int m,float,float,float,float):map(m){}};
struct Player:Unit{ObjectGuid guid{1};int map=654,status=QUEST_STATUS_INCOMPLETE,phase=1,credits=0,teleports=0,entries=0,exits=0;bool alive=true;Creature*base=nullptr;Transport*transport=&defaultTransport;Player*ToPlayer()override{return this;}ObjectGuid GetGUID(){return guid;}bool IsAlive(){return alive;}int GetMapId(){return map;}int GetQuestStatus(int){return status;}Creature*GetVehicleBase(){return base;}Transport*GetTransport(){return transport;}Position GetTransOffset(){return {};}void EnterVehicle(Creature*,int);void ExitVehicle();void KilledMonsterCredit(int id){if(id!=43729)throw std::runtime_error("wrong credit");++credits;}void TeleportTo(WorldLocation const&){++teleports;}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){now=0;events.clear();}void Update(uint32 d){now+=d;}void ScheduleEvent(uint32 e,uint32 d){events.emplace(now+d,e);}void RescheduleEvent(uint32 e,uint32 d){for(auto i=events.begin();i!=events.end();)if(i->second==e)i=events.erase(i);else++i;ScheduleEvent(e,d);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto e=events.begin()->second;events.erase(events.begin());return e;}};
struct MotionMaster{int paths=0;void MovePath(uint32 id,bool){if(id!=4371301)throw std::runtime_error("wrong native route");++paths;}};
struct Vehicle{Creature*owner;void RemoveAllPassengers();};
struct Creature:Unit{ObjectGuid guid{5};int map=654,phase=1,despawns=0;ScriptedAI*ai=nullptr;Player*rider=nullptr;Transport*transport=&defaultTransport;Vehicle vehicle{this};MotionMaster motion;int GetMapId(){return map;}bool IsInPhase(Player*p){return p->phase==phase;}Transport*GetTransport(){return transport;}Map*GetMap(){return &worldMap;}std::list<Player*>SelectNearestPlayers(float){return selectedPlayers;}ObjectGuid GetGUID(){return guid;}ScriptedAI*AI(){return ai;}Vehicle*GetVehicleKit(){return &vehicle;}MotionMaster*GetMotionMaster(){return &motion;}template<class T>void DespawnOrUnsummon(T){++despawns;}};
struct ScriptedAI{Creature*me;ScriptedAI(Creature*c):me(c){c->ai=this;}virtual~ScriptedAI()=default;virtual ObjectGuid GetGUID(int32)const{return {};}virtual void SetGUID(ObjectGuid,int32){}virtual void PassengerBoarded(Unit*,int8,bool){}void UpdateAI(uint32){}};
void Player::EnterVehicle(Creature*c,int seat){++entries;base=c;c->rider=this;c->AI()->PassengerBoarded(this,seat,true);}
void Player::ExitVehicle(){++exits;Creature*c=base;base=nullptr;if(c){c->rider=nullptr;c->AI()->PassengerBoarded(this,0,false);}}
void Vehicle::RemoveAllPassengers(){if(owner->rider)owner->rider->ExitVehicle();}
std::map<int,Player*>players;std::map<int,Creature*>creatures;
namespace ObjectAccessor{Player*GetPlayer(Creature&me,ObjectGuid g){auto i=players.find(g.id);return i!=players.end()&&i->second->map==me.map?i->second:nullptr;}Creature*GetCreature(Creature&,ObjectGuid g){auto i=creatures.find(g.id);return i==creatures.end()?nullptr:i->second;}}
Creature*Transport::CreateNPCPassenger(int guid,CreatureData*data){++attempts;if(data->id!=43713)throw std::runtime_error("wrong escape entry");if(queue.empty())return nullptr;auto*c=queue.front();queue.pop_front();c->guid.id=guid;creatures[guid]=c;return c;}
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
'''
 ai=method(source,'    struct npc_wyvern_43713AI :')
 # Keep real virtual dispatch for the controlled native vehicle callback boundary.
 ai=ai.replace('        ObjectGuid GetGUID(', '        virtual ObjectGuid GetGUID(').replace('        void PassengerBoarded(', '        virtual void PassengerBoarded(')
 ai=ai.replace('        void SetGUID(', '        virtual void SetGUID(')
 code+=ai+';\n'
 lorna=source[source.index('    struct npc_lorna_crowley_43566AI'):]
 case=method(lorna,'                case EVENT_TALK_PART_15:');creation=method(lorna,'                case EVENT_TALK_PART_14:')
 code+='struct Boarding{Creature*me;ObjectGuid m_playerGUID{99};std::list<ObjectGuid>wList;EventMap m_events;'+method(lorna,'        bool CanJoinEscape(')+'void Run(){switch(uint32(EVENT_TALK_PART_15)){'+case+'}}void Create(){switch(uint32(EVENT_TALK_PART_14)){'+creation+'}}};\n'
 code+=r'''
int main(){using AI=npc_wyvern_43713AI;
 Player probe;Creature probeLorna;Boarding eligibility{&probeLorna,{99},{},{}};check(eligibility.CanJoinEscape(&probe),"eligible same-ship participant");
 for(int reason=0;reason<7;++reason){probe=Player{};probeLorna=Creature{};if(reason==0)probe.alive=false;if(reason==1)probe.status=QUEST_STATUS_NONE;if(reason==2)probe.phase=2;if(reason==3)probe.map=1;if(reason==4)probe.transport=nullptr;if(reason==5)probeLorna.transport=nullptr;if(reason==6)probe.base=&probeLorna;check(!eligibility.CanJoinEscape(&probe),"ineligible/off-ship/dead/wrong phase/already mounted participant rejected");}probeLorna=Creature{};
 Player a,b;a.guid.id=1;b.guid.id=2;players={{1,&a},{2,&b}};Creature wa,wb,lorna;wa.guid.id=10;wb.guid.id=11;creatures={{10,&wa},{11,&wb}};AI xa(&wa),xb(&wb);xa.Reset();xb.Reset();xa.SetGUID(a.guid,PLAYER_GUID);xb.SetGUID(b.guid,PLAYER_GUID);xa.SetGUID(b.guid,PLAYER_GUID);check(xa.GetGUID(PLAYER_GUID)==a.guid&&xa.GetGUID(0).IsEmpty(),"immutable exposed owner");
 Boarding board{&lorna,{99},{{10},{11}},{}};board.Run();check(a.base==&wa&&b.base==&wb&&a.entries==1&&b.entries==1,"each player boards their own escape vehicle despite stale Lorna owner");board.Run();check(a.entries==1&&b.entries==1,"duplicate boarding event does not replace active vehicles");
 Unit accessory;xa.PassengerBoarded(nullptr,1,true);xa.PassengerBoarded(&accessory,1,true);xa.PassengerBoarded(&accessory,1,false);xa.PassengerBoarded(&b,1,false);xa.PassengerBoarded(&a,0,true);check(!wa.despawns&&xa.m_events.events.size()==1,"accessory/foreign/duplicate callbacks do not queue duplicate flights");
 xa.UpdateAI(199);check(!wa.motion.paths,"native delay retained");xa.UpdateAI(1);check(wa.motion.paths==1,"native escape route starts");xa.MovementInform(WAYPOINT_MOTION_TYPE,1);check(!a.credits,"intermediate point no credit");xa.MovementInform(WAYPOINT_MOTION_TYPE,2);xa.MovementInform(WAYPOINT_MOTION_TYPE,2);check(xa.m_events.events.size()==1,"duplicate arrival schedules once");xa.UpdateAI(200);check(!a.base&&!a.credits,"arrival ejects before delayed completion");xa.UpdateAI(200);check(a.credits==1&&a.teleports==1&&wa.despawns==1,"successful native arrival completes once");xa.UpdateAI(1000);check(a.credits==1,"no duplicate credit");
 for(int reason=0;reason<6;++reason){Player p;p.guid.id=3;players[3]=&p;Creature c;AI x(&c);x.Reset();x.SetGUID(p.guid,PLAYER_GUID);p.EnterVehicle(&c,0);if(reason==0)p.ExitVehicle();if(reason==1)p.status=QUEST_STATUS_NONE;if(reason==2)p.alive=false;if(reason==3)p.phase=2;if(reason==4)p.map=1;if(reason==5)players.erase(3);x.UpdateAI(1000);check(!p.credits&&!p.teleports&&!c.motion.paths&&x.m_stopped,"early dismount/abandon/death/phase/map/logout cannot award completion");}
 {Player p;p.guid.id=4;players[4]=&p;Creature c;AI x(&c);x.Reset();x.SetGUID(p.guid,PLAYER_GUID);p.EnterVehicle(&c,0);x.UpdateAI(200);x.MovementInform(WAYPOINT_MOTION_TYPE,2);x.UpdateAI(200);p.status=QUEST_STATUS_NONE;x.UpdateAI(200);check(!p.credits&&!p.teleports,"late quest loss blocks delayed credit");}
 {Player p;p.guid.id=5;players[5]=&p;Creature c;AI x(&c);x.Reset();x.SetGUID(p.guid,PLAYER_GUID);p.EnterVehicle(&c,0);x.Reset();x.UpdateAI(1000);check(!c.motion.paths&&!p.credits&&!p.base&&x.m_stopped,"reset clears pending takeoff and releases rider");}
 {Player p,q,fail,outsider;p.guid.id=7;q.guid.id=8;fail.guid.id=9;outsider.guid.id=10;outsider.status=QUEST_STATUS_NONE;players[7]=&p;players[8]=&q;players[9]=&fail;players[10]=&outsider;Creature c,d,l;AI x(&c),y(&d);x.Reset();y.Reset();defaultTransport.queue={&c,&d};defaultTransport.attempts=0;selectedPlayers={&p,&q,&fail,&outsider};Boarding creating{&l,{99},{},{}};creating.Create();check(defaultTransport.attempts==3&&creating.wList.size()==2&&spawnErrors==1,"native creation skips nonparticipant and survives failed summon");creating.Run();check(p.base==&c&&q.base==&d&&!fail.base&&!outsider.base,"native creation-to-boarding uses individual owners");p.ExitVehicle();q.ExitVehicle();selectedPlayers.clear();}
 check(std::count(traceStates.begin(),traceStates.end(),"ESCAPE_COMPLETED")==1,"trace completion once only for successful owner");
 std::cout<<"PASS: native wyvern AI and Lorna boarding; two owners, arrival-only once credit, cancellation and reset\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'];subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
