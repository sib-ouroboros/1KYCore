#!/usr/bin/env python3
"""Compile the production Manor vehicle lifecycle on native handler extracts."""
import argparse,os,subprocess,tempfile
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <chrono>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int8=std::int8_t;using namespace std::chrono_literals;
using QuestStatus=int;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1,QUEST_STATUS_REWARDED=6;
constexpr int QUEST_TO_GREYMANE_MANOR=14465,SPELL_PHASE_QUEST_ZONE_SPECIFIC_08=68483,SPELL_PHASE_QUEST_ZONE_SPECIFIC_09=69077,SPELL_FORCECAST_UPDATE_ZONE_AURAS=94828;
constexpr int WAYPOINT_ID=3674101,WAYPOINT_MOTION_TYPE=2,REACT_PASSIVE=0;
struct ObjectGuid{int id=0;static const ObjectGuid Empty;};const ObjectGuid ObjectGuid::Empty{};
bool operator==(ObjectGuid a,ObjectGuid b){return a.id==b.id;}bool operator!=(ObjectGuid a,ObjectGuid b){return !(a==b);}
struct Player;struct Creature;
struct Unit{virtual ~Unit()=default;virtual Player*ToPlayer(){return nullptr;}int exits=0;void ExitVehicle(){++exits;}};
struct MotionMaster{uint32 path=0;bool repeat=true;int starts=0;void MovePath(uint32 p,bool r){path=p;repeat=r;++starts;}};
struct Vehicle{int removals=0;void RemoveAllPassengers(){++removals;}};
struct Creature:Unit{bool despawn=false;MotionMaster motion;Vehicle vehicle;void SetReactState(int){}void DespawnOrUnsummon(){despawn=true;}void DespawnOrUnsummon(std::chrono::seconds){despawn=true;}Vehicle*GetVehicleKit(){return &vehicle;}MotionMaster*GetMotionMaster(){return &motion;}void CastSpell(Player*,int,bool){}};
struct Player:Unit{ObjectGuid guid;bool alive=true;int map=654,status=QUEST_STATUS_INCOMPLETE;Creature*base=nullptr;int credits=0;Player*ToPlayer()override{return this;}bool IsAlive(){return alive;}int GetMapId(){return map;}ObjectGuid GetGUID(){return guid;}int GetQuestStatus(int){return status;}Creature*GetVehicleBase(){return base;}void AddAura(int,Player*){}};
std::map<int,Player*>players;namespace ObjectAccessor{Player*GetPlayer(Creature&,ObjectGuid g){auto i=players.find(g.id);return i==players.end()?nullptr:i->second;}}
struct ScriptedAI{Creature*me;ScriptedAI(Creature*c):me(c){}virtual~ScriptedAI()=default;virtual void Reset(){}virtual void IsSummonedBy(Unit*){}virtual void MovementInform(uint32,uint32){}virtual void PassengerBoarded(Unit*,int8,bool){}virtual void UpdateAI(uint32){}};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
"""
 start=s.index('    struct npc_swift_mountain_horse_36741AI');end=s.index('    CreatureAI* GetAI',start);code+=s[start:end]
 code+=r"""
int main(){
 using AI=npc_swift_mountain_horse_36741AI;
 Player owner,other;owner.guid.id=1;other.guid.id=2;players[1]=&owner;players[2]=&other;
 Creature horse;AI ai(&horse);ai.Reset();ai.IsSummonedBy(&owner);owner.base=&horse;
 ai.PassengerBoarded(&other,0,true);check(other.exits==1&&!horse.motion.starts,"foreign rider rejected");
 ai.PassengerBoarded(&owner,1,true);check(owner.exits==1&&!horse.motion.starts,"wrong seat rejected");
 owner.status=QUEST_STATUS_COMPLETE;ai.PassengerBoarded(&owner,0,true);
 check(horse.motion.path==3674101&&!horse.motion.repeat&&horse.motion.starts==1,"complete empty-objective quest can ride");
 ai.PassengerBoarded(&other,0,false);check(!horse.despawn,"foreign dismount does not terminate ride");
 ai.MovementInform(WAYPOINT_MOTION_TYPE,11);check(horse.vehicle.removals==0,"legacy intermediate point is not arrival");
 ai.UpdateAI(1000);check(!horse.despawn,"active owner ride survives tick");
 ai.MovementInform(999,28);check(horse.vehicle.removals==0,"wrong movement type ignored");
 ai.MovementInform(WAYPOINT_MOTION_TYPE,28);check(horse.vehicle.removals==1&&horse.despawn,"actual final point lands once");
 ai.MovementInform(WAYPOINT_MOTION_TYPE,28);check(horse.vehicle.removals==1,"duplicate arrival ignored");
 Creature early;AI e(&early);e.IsSummonedBy(&owner);owner.base=&early;e.PassengerBoarded(&owner,0,true);e.PassengerBoarded(&owner,0,false);check(early.despawn&&!e.m_arrived&&!owner.credits,"early dismount no fake arrival or credit");
 for(int mode=0;mode<5;++mode){
  Creature mount;AI a(&mount);owner.status=QUEST_STATUS_INCOMPLETE;owner.alive=true;owner.base=&mount;players[1]=&owner;a.IsSummonedBy(&owner);a.PassengerBoarded(&owner,0,true);
  if(mode==0)owner.status=QUEST_STATUS_NONE;
  if(mode==1)owner.alive=false;
  if(mode==2)players.erase(1);
  if(mode==3)owner.base=nullptr;
  a.UpdateAI(mode==4?360000:1000);check(mount.despawn,"abandon/death/logout/lost passenger/timeout cleanup");
 }
 owner.status=QUEST_STATUS_REWARDED;owner.alive=true;Creature stale;AI z(&stale);z.IsSummonedBy(&owner);check(stale.despawn,"rewarded quest cannot summon ride");
 std::cout<<"Manor native route endpoint, owner and vehicle lifecycle: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
