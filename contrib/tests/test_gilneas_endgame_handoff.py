"""Native Endgame handoff and rope selection on a rotated transport."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parents[2];s=(r/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
code=r'''
#include <cmath>
#include <algorithm>
#include <vector>
#include <stdexcept>
#include <iostream>
using QuestStatus=int;enum{GO_WORGEN_GUNSHIP=203428,QUEST_ENDGAME=26706,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1,PLAYER_GUID=1,EVENT_TELEPORT_01=1,ACTION_ENDGAME_SCENE_START=2670603,NPC_GILNEAS_VEHICLE_ROPE=43793};
struct Position{float m_positionX=0,m_positionY=0,m_positionZ=0,m_orientation=0;float GetPositionZ()const{return m_positionZ;}float GetExactDist2d(Position const*p)const{return std::hypot(m_positionX-p->m_positionX,m_positionY-p->m_positionY);}};
struct Player;struct Creature;struct ShipAI{int started=0;void DoAction(int id){if(id==ACTION_ENDGAME_SCENE_START)++started;}};
struct Transport{std::vector<Player*>passengers;std::vector<Player*>const&GetPassengers(){return passengers;}int entry=GO_WORGEN_GUNSHIP,removed=0,added=0;float x=1000,y=500,z=100,angle=0.5;ShipAI ai;int GetEntry(){return entry;}ShipAI*AI(){return &ai;}void RemovePassenger(Player*);void AddPassenger(Player*);void CalculatePassengerPosition(float&a,float&b,float&c,float*o){float dx=a,dy=b;a=x+std::cos(angle)*dx-std::sin(angle)*dy;b=y+std::sin(angle)*dx+std::cos(angle)*dy;c+=z;*o+=angle;}};
struct Movement{struct State{Position pos;int seat=0;}transport;};
struct Motion{int jumps=0;Position destination;void MoveJump(Position const&p,float xy,float z){if(xy!=10||z!=5)throw std::runtime_error("wrong jump velocity");destination=p;++jumps;}};
struct Player{int map=654,status=3,exits=0,teleports=0;bool alive=true;Transport*ship=nullptr;Movement m_movementInfo;Position world;std::vector<Creature*>anchors;Motion motion;Player*ToPlayer(){return this;}void TeleportTo(int m,float x,float y,float z,float o){if(ship)ship->RemovePassenger(this);map=m;world={x,y,z,o};++teleports;}int GetMapId(){return map;}bool IsAlive(){return alive;}int GetQuestStatus(int){return status;}void ExitVehicle(){++exits;}Transport*GetTransport(){return ship;}void NearTeleportTo(Position const&p){if(!ship)throw std::runtime_error("teleport before attachment");world=p;++teleports;}int GetGUID(){return 1;}Position const&GetTransOffset(){return m_movementInfo.transport.pos;}std::vector<Creature*>FindNearestCreatures(int,float range){if(range!=90)throw std::runtime_error("rope search radius");return anchors;}Motion*GetMotionMaster(){return &motion;}};
void Transport::RemovePassenger(Player*p){++removed;passengers.erase(std::remove(passengers.begin(),passengers.end(),p),passengers.end());p->ship=nullptr;}void Transport::AddPassenger(Player*p){++added;passengers.push_back(p);p->ship=this;}
struct ActorAI{int starts=0,bound=0;void SetGUID(int,int){++bound;}void DoAction(int){++starts;}};
struct Creature{Transport*ship=nullptr;Position offset;bool phase=true;ActorAI ai;Transport*GetTransport(){return ship;}bool IsInPhase(Player*){return phase;}Position const&GetTransOffset(){return offset;}Position GetPosition(){Position p=offset;ship->CalculatePassengerPosition(p.m_positionX,p.m_positionY,p.m_positionZ,&p.m_orientation);return p;}ActorAI*AI(){return &ai;}};
struct GameObject{Transport*ship=nullptr;Transport*GetTransport(){return ship;}};
'''
code+=method(s,'static void ReturnEndgamePlayerToHarbor(')+method(s,'static void EvacuateEndgameShip(')+method(s,'static bool BoardEndgameShip(')
part=s[s.index('class go_rope_204428 :'):];code+='struct Rope{'+method(part,'    bool OnGossipHello(')+method(part,'    Creature* FindRopeLowerDeckAnchor(')+'};\n'
code+=r'''
void check(bool v){if(!v)throw std::runtime_error("Endgame handoff/rope failure");}
int main(){Transport ship,other;Player p;p.ship=&other;Creature lorna;lorna.ship=&ship;lorna.offset={5,4,84.797f,0.2};check(BoardEndgameShip(&p,&lorna));check(p.ship==&ship&&other.removed==1&&ship.added==1&&p.teleports==1&&p.exits==1&&p.m_movementInfo.transport.seat==-1);check(std::fabs(p.world.m_positionZ-184.997f)<0.001&&std::fabs(p.m_movementInfo.transport.pos.m_positionZ-84.997f)<0.001);check(lorna.ai.bound==1&&lorna.ai.starts==1&&ship.ai.started==1);
Player invalid;invalid.status=0;check(!BoardEndgameShip(&invalid,&lorna)&&!invalid.exits);invalid.status=3;lorna.phase=false;check(!BoardEndgameShip(&invalid,&lorna)&&!invalid.exits);lorna.phase=true;
Creature upper,near,far,bottom,foreign;for(auto*c:{&upper,&near,&far,&bottom,&foreign})c->ship=&ship;upper.offset={5,4,84,0};near.offset={6,4,34,0};far.offset={20,4,34.5f,0};bottom.offset={5,4,9,0};foreign.offset={5,4,35,0};foreign.ship=&other;p.anchors={&upper,&far,&bottom,&foreign,&near};Rope rope;GameObject go;go.ship=&ship;check(rope.FindRopeLowerDeckAnchor(&p)==&near);rope.OnGossipHello(&p,&go);check(p.motion.jumps==1&&std::fabs(p.motion.destination.m_positionZ-134)<0.001);go.ship=&other;rope.OnGossipHello(&p,&go);check(p.motion.jumps==1);p.anchors={&upper,&foreign};check(!rope.FindRopeLowerDeckAnchor(&p));
Player bystander,completed;bystander.status=0;completed.status=1;ship.AddPassenger(&bystander);ship.AddPassenger(&completed);EvacuateEndgameShip(&ship);check(p.teleports==2&&completed.teleports==1&&!bystander.teleports&&p.status==3&&completed.status==1&&ship.passengers.size()==1&&ship.passengers[0]==&bystander);
std::cout<<"PASS: actual ship attachment before teleport, local/world offsets, scene handoff, next-deck rope and foreign transport gates\n";}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

