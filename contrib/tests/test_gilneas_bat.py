#!/usr/bin/env python3
"""Compile native captured-bat ownership, waypoint and return handlers."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <chrono>
#include <map>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint8=std::uint8_t;using int8=std::int8_t;using int32=std::int32_t;using QuestStatus=int;using EvadeReason=int;using namespace std::chrono_literals;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1,REACT_PASSIVE=0,MOVE_FLIGHT=1,PLAYER_GUID=10,WAYPOINT_MOTION_TYPE=2;
struct ObjectGuid{int id=0;static const ObjectGuid Empty;};const ObjectGuid ObjectGuid::Empty{};bool operator==(ObjectGuid a,ObjectGuid b){return a.id==b.id;}bool operator!=(ObjectGuid a,ObjectGuid b){return !(a==b);}
struct Player;struct Creature;
struct PhaseShift {};
struct Unit{ObjectGuid guid;uint32 entry=0,map=654;bool alive=true,phase=true;int exits=0;virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}virtual Creature*ToCreature(){return nullptr;}bool IsAlive(){return alive;}uint32 GetMapId(){return map;}uint32 GetEntry(){return entry;}ObjectGuid GetGUID(){return guid;}PhaseShift const& GetPhaseShift()const{static PhaseShift value;return value;}bool InSamePhase(PhaseShift const&){return phase;}void ExitVehicle(){++exits;}};
struct CreatureAI{virtual~CreatureAI()=default;virtual ObjectGuid GetGUID(int32)const{return {};}virtual void DoAction(int32){}};
struct MotionMaster{std::vector<uint32>paths;int clears=0;void Clear(){++clears;}void MovePath(uint32 p,bool repeat){if(repeat)throw std::runtime_error("unverified loop");paths.push_back(p);}};
struct Vehicle{int removals=0;void RemoveAllPassengers(){++removals;}};
struct Creature:Unit{bool despawn=false,gravity=false,fly=false;float speed=0;CreatureAI*ai=nullptr;MotionMaster motion;Vehicle vehicle;Creature*ToCreature()override{return this;}CreatureAI*AI(){return ai;}void SetReactState(int){}void SetCanFly(bool b){fly=b;}void SetDisableGravity(bool b){gravity=b;}void SetSpeed(int,float n){speed=n;}void DespawnOrUnsummon(){despawn=true;}template<class R,class P>void DespawnOrUnsummon(std::chrono::duration<R,P>){despawn=true;}MotionMaster*GetMotionMaster(){return &motion;}Vehicle*GetVehicleKit(){return &vehicle;}};
struct Player:Unit{QuestStatus status=QUEST_STATUS_INCOMPLETE;Unit*base=nullptr;Creature*existing=nullptr,*source=nullptr;Player*ToPlayer()override{return this;}int GetQuestStatus(int){return status;}Unit*GetVehicleBase(){return base;}Creature*GetSummonedCreatureByEntry(int){return existing;}Creature*FindNearestCreature(int,float){return source;}};
std::map<int,Player*>players;struct ObjectAccessor{static Player*GetPlayer(Creature&,ObjectGuid g){auto i=players.find(g.id);return i==players.end()?nullptr:i->second;}};
struct ScriptedAI:CreatureAI{Creature*me;explicit ScriptedAI(Creature*c):me(c){c->ai=this;}};
struct SpellScript{Unit*caster=nullptr;Unit*GetCaster(){return caster;}};using SpellEffIndex=int;enum SpellCastResult{SPELL_CAST_OK,SPELL_FAILED_BAD_TARGETS};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
"""
 part=source[source.index('    struct npc_captured_riding_bat_38540AI'):];code+=method(part,'    struct npc_captured_riding_bat_38540AI').replace(' override','')+';\n'
 part=source[source.index('class spell_gilneas_captured_bat_summon :'):];code+='struct Cast:SpellScript {'+method(part,'        SpellCastResult CheckBat(')+'};\n'
 part=source[source.index('class spell_fly_back_72849 :'):];code+='struct Return:SpellScript {'+method(part,'        void HandleDummy(')+'};\n'
 code+=r"""
int main(){
 using AI=npc_captured_riding_bat_38540AI;Player p,other;p.guid.id=1;other.guid.id=2;players[1]=&p;players[2]=&other;Creature clicker;clicker.entry=38615;p.source=&clicker;
 Cast cast;cast.caster=&p;check(cast.CheckBat()==SPELL_CAST_OK,"native summon allowed");p.source=nullptr;check(cast.CheckBat()==SPELL_FAILED_BAD_TARGETS,"no clicker no summon");p.source=&clicker;
 Creature bat;bat.entry=38540;AI a(&bat);a.Reset();a.IsSummonedBy(&p);a.PassengerBoarded(&other,0,true);check(other.exits==1&&bat.motion.paths.empty(),"foreign rider denied");p.base=&bat;
 a.PassengerBoarded(&p,0,true);a.PassengerBoarded(&p,0,true);check(!p.exits&&bat.motion.paths.size()==1&&bat.motion.paths.back()==3854001&&bat.fly&&bat.gravity,"one owner starts actual circuit");
 check(cast.CheckBat()==SPELL_FAILED_BAD_TARGETS,"already riding cannot create second bat");a.PassengerBoarded(&other,0,false);check(!bat.despawn,"foreign dismount ignored");
 a.MovementInform(WAYPOINT_MOTION_TYPE,3);check(!bat.vehicle.removals,"old intermediate point does not land");
 Return ret;ret.caster=&p;ret.HandleDummy(0);check(a.m_flightState==3&&bat.motion.paths.back()==3854003&&bat.motion.paths.size()==2,"return button changes state and real route");ret.HandleDummy(0);check(bat.motion.paths.size()==2,"return idempotent");
 a.MovementInform(WAYPOINT_MOTION_TYPE,3);check(!bat.vehicle.removals,"return waits for real last point");a.MovementInform(WAYPOINT_MOTION_TYPE,14);a.MovementInform(WAYPOINT_MOTION_TYPE,14);check(bat.vehicle.removals==1&&bat.despawn&&!bat.gravity,"safe final-point landing once");
 p.base=nullptr;for(int mode=0;mode<6;++mode){Creature c;c.entry=38540;AI ai(&c);p.status=QUEST_STATUS_INCOMPLETE;p.alive=true;players[1]=&p;ai.IsSummonedBy(&p);p.base=&c;ai.PassengerBoarded(&p,0,true);
  if(mode==0)p.status=QUEST_STATUS_NONE;
  if(mode==1)p.status=QUEST_STATUS_COMPLETE;
  if(mode==2)p.alive=false;
  if(mode==3)players.erase(1);
  if(mode==4)p.base=nullptr;
  ai.UpdateAI(mode==5?120000:1000);
  if(mode==0||mode==5)check(!c.despawn&&c.motion.paths.back()==3854003,"cancel/timeout return living rider");
  if(mode==1)check(!c.despawn&&ai.m_flightState==1,"completed objectives keep return button available");
  if(mode>=2&&mode<=4)check(c.despawn,"death/logout/early dismount cleanup");}
 p.status=QUEST_STATUS_INCOMPLETE;p.alive=true;p.base=nullptr;players[1]=&p;Creature unused;AI u(&unused);u.IsSummonedBy(&p);u.UpdateAI(10000);check(unused.despawn,"failed native boarding is bounded");
 std::cout<<"Captured bat native circuit, return, landing and ownership: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
