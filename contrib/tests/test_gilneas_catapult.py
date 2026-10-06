#!/usr/bin/env python3
"""Compile production catapult AI and launch spell; no running server required."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <map>
#include <memory>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int8=std::int8_t;using namespace std::chrono_literals;
constexpr int UNIT_FIELD_FLAGS=0,UNIT_FLAG_IMMUNE_TO_PC=1,UNIT_FLAG_IMMUNE_TO_NPC=2,UNIT_FLAG_NOT_SELECTABLE=4,REACT_PASSIVE=0,TEMPSUMMON_DEAD_DESPAWN=7;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2;
struct ObjectGuid{int id=0;bool IsEmpty()const{return !id;}bool operator==(ObjectGuid o)const{return id==o.id;}bool operator!=(ObjectGuid o)const{return id!=o.id;}static ObjectGuid const Empty;};ObjectGuid const ObjectGuid::Empty{};
struct PhaseShift{};
struct Position{float x=0,y=0,z=0;bool IsPositionValid()const{return std::isfinite(x)&&std::isfinite(y)&&std::isfinite(z)&&std::abs(x)<17066&&std::abs(y)<17066&&std::abs(z)<17066;}float GetPositionX()const{return x;}float GetPositionY()const{return y;}float GetPositionZ()const{return z;}};
struct Creature;struct Player;struct CreatureAI;struct TempSummon;
struct MotionMaster{int jumps=0;Position dest;float xy=0,z=0;void MoveJump(Position const&p,float a,float b){++jumps;dest=p;xy=a;z=b;}};
struct Unit{ObjectGuid guid;uint32 map=654,entry=0;bool alive=true;Creature*base=nullptr;MotionMaster motion;virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}virtual Creature*ToCreature(){return nullptr;}ObjectGuid GetGUID()const{return guid;}uint32 GetMapId()const{return map;}uint32 GetEntry()const{return entry;}bool IsAlive()const{return alive;}Creature*GetVehicleBase()const{return base;}PhaseShift const&GetPhaseShift()const{static PhaseShift p;return p;}void ExitVehicle();void EnterVehicle(Creature*,int8);MotionMaster*GetMotionMaster(){return &motion;}};
struct Vehicle{Unit*passengers[3]{};Unit*GetPassenger(int s){return passengers[s];}};
struct Player:Unit{int quest=1,exits=0,auras=0;Player*ToPlayer()override{return this;}int GetQuestStatus(int)const{return quest;}};
struct Creature:Unit{CreatureAI*ai=nullptr;Vehicle vehicle;bool hasVehicle=true,phase=true;int faction=0,flags=0,boulders=0,summons=0;uint32 script=7;Player*near=nullptr;Position pos;Creature*ToCreature()override{return this;}CreatureAI*AI(){return ai;}uint32 GetScriptId()const{return script;}Vehicle*GetVehicleKit(){return hasVehicle?&vehicle:nullptr;}bool InSamePhase(PhaseShift const&)const{return phase;}void SetFlag(int,int f){flags|=f;}void RemoveFlag(int,int f){flags&=~f;}void setFaction(int f){faction=f;}void SetReactState(int){}Player*SelectNearestPlayer(float){return near;}void CastSpell(Unit*,uint32,bool){++boulders;}void AddAura(uint32,Player*p){++p->auras;}Position const&GetPosition()const{return pos;}float GetExactDist2d(Position const*p){return std::hypot(pos.x-p->x,pos.y-p->y);}TempSummon*SummonCreature(uint32,Position const&,int);};
struct TempSummon:Creature{};
struct CreatureAI{Creature*me;int attacks=0;explicit CreatureAI(Creature*c):me(c){c->ai=this;}virtual~CreatureAI()=default;virtual void OnCharmed(bool){}virtual void Reset(){}virtual void JustSummoned(Creature*){}virtual void SummonedCreatureDies(Creature*,Unit*){}virtual void PassengerBoarded(Unit*,int8,bool){}virtual void UpdateAI(uint32){}void AttackStart(Player*){++attacks;}};
struct ScriptedAI:CreatureAI{using CreatureAI::CreatureAI;};
std::map<int,Unit*> units;
struct ObjectAccessor{static Player*GetPlayer(Creature&,ObjectGuid id){auto i=units.find(id.id);return i==units.end()?nullptr:i->second->ToPlayer();}static Creature*GetCreature(Creature&,ObjectGuid id){auto i=units.find(id.id);return i==units.end()?nullptr:i->second->ToCreature();}};
std::unique_ptr<TempSummon> lastSummon;std::unique_ptr<CreatureAI> lastAI;
TempSummon*Creature::SummonCreature(uint32 e,Position const&,int){++summons;lastSummon=std::make_unique<TempSummon>();lastSummon->entry=e;lastSummon->guid={50};lastAI=std::make_unique<CreatureAI>(lastSummon.get());units[50]=lastSummon.get();ai->JustSummoned(lastSummon.get());return lastSummon.get();}
void Unit::ExitVehicle(){if(!base)return;Creature*c=base;int s=0;while(s<3&&c->vehicle.passengers[s]!=this)++s;base=nullptr;if(s<3){c->vehicle.passengers[s]=nullptr;c->ai->PassengerBoarded(this,s,false);}if(auto*p=ToPlayer())++p->exits;}
void Unit::EnterVehicle(Creature*c,int8 s){base=c;c->vehicle.passengers[s]=this;c->ai->PassengerBoarded(this,s,true);}
struct CreatureScript{explicit CreatureScript(char const*){}virtual~CreatureScript()=default;virtual CreatureAI*GetAI(Creature*)const{return nullptr;}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){now=0;events.clear();}void Update(uint32 d){now+=d;}void CancelEvent(uint32 id){for(auto i=events.begin();i!=events.end();)if(i->second==id)i=events.erase(i);else++i;}template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}template<class R,class P>void RescheduleEvent(uint32 id,std::chrono::duration<R,P>d){CancelEvent(id);ScheduleEvent(id,d);}template<class A,class B>void ScheduleEvent(uint32 id,A a,B){ScheduleEvent(id,a);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
enum SpellCastResult{SPELL_CAST_OK,SPELL_FAILED_DONT_REPORT,SPELL_FAILED_NOT_READY,SPELL_FAILED_BAD_TARGETS};using SpellEffIndex=int;
struct Targets{bool traj=true;float xy=35,z=25;bool HasTraj()const{return traj;}float GetSpeedXY()const{return xy;}float GetSpeedZ()const{return z;}};
struct Spell{Targets m_targets;};struct SpellInfo{float range=200;float GetMaxRange(bool)const{return range;}};
struct Hook{void operator+=(int){}};
struct SpellScript{Creature*caster=nullptr;Position*dest=nullptr;Spell spell;SpellInfo info;int prevented=0;Hook OnCheckCast,OnEffectHitTarget,AfterCast;virtual~SpellScript()=default;virtual void Register(){}Creature*GetCaster()const{return caster;}Position const*GetExplTargetDest()const{return dest;}Spell*GetSpell(){return &spell;}SpellInfo*GetSpellInfo(){return &info;}void PreventHitDefaultEffect(int){++prevented;}};
struct SpellScriptLoader{explicit SpellScriptLoader(char const*){}virtual~SpellScriptLoader()=default;virtual SpellScript*GetSpellScript()const{return nullptr;}};
struct ObjectMgr{uint32 id=7;uint32 GetScriptId(char const*)const{return id;}}objectMgr;auto*sObjectMgr=&objectMgr;
#define CAST_AI(a,b) dynamic_cast<a*>(b)
#define PrepareSpellScript(a) public:
#define SpellCheckCastFn(...) 0
#define SpellEffectFn(...) 0
#define SpellCastFn(...) 0
'''
 code+=method(source,'enum eDuskHaven')+';\n'
 code+=source[source.index('// 36283:'):source.index('// 96185 trigger')]
 code+=r'''
using AI=npc_forsaken_catapult_36283::npc_forsaken_catapult_36283AI;using Launch=spell_launch_68659::spell_launch_68659_SpellScript;
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
struct Scene{Creature cat,operatorNpc;Player p,other;AI ai;CreatureAI operatorAI;Position dest{100,20,30};Launch spell;Scene():ai(&cat),operatorAI(&operatorNpc){units.clear();objectMgr.id=7;cat.entry=36283;cat.guid={1};p.guid={2};other.guid={3};operatorNpc.guid={4};operatorNpc.entry=36292;units[1]=&cat;units[2]=&p;units[3]=&other;units[4]=&operatorNpc;spell.caster=&cat;spell.dest=&dest;ai.Reset();ai.JustSummoned(&operatorNpc);operatorNpc.EnterVehicle(&cat,2);}void defeat(){operatorNpc.ExitVehicle();operatorNpc.alive=false;ai.SummonedCreatureDies(&operatorNpc,&p);}void board(){p.EnterVehicle(&cat,0);}void launch(){check(spell.CheckLaunch()==SPELL_CAST_OK,"launch gate");spell.PreserveControlSeat(1);spell.Launch();}};
int main(){try{
 {Scene s;s.board();check(!s.p.base&&s.cat.flags&UNIT_FLAG_NOT_SELECTABLE,"operator locks player seat");s.cat.near=&s.p;s.ai.UpdateAI(500);check(!s.operatorNpc.base&&s.operatorAI.attacks==1,"machinist exits to fight");s.board();check(!s.p.base,"live dismounted machinist still locks catapult");s.defeat();s.board();check(s.p.base==&s.cat&&s.ai.m_playerGUID==s.p.guid,"defeated machinist unlocks control seat");s.ai.OnCharmed(true);s.launch();check(!s.p.motion.jumps&&s.ai.m_launchPending&&s.spell.prevented==1,"manual button queues launch, native seat transfer suppressed");check(s.spell.CheckLaunch()==SPELL_FAILED_NOT_READY,"duplicate launch rejected");s.ai.UpdateAI(1999);check(!s.p.motion.jumps,"launch delay");s.ai.UpdateAI(1);check(s.p.motion.jumps==1&&!s.p.base&&s.p.auras==1,"safe fall and real jump");check(s.p.motion.dest.x==100&&s.p.motion.dest.z==30&&s.p.motion.xy==35&&s.p.motion.z==25,"aim and speeds retained");s.ai.UpdateAI(2000);check(s.p.motion.jumps==1,"exactly one launch");}
 {Scene s;s.defeat();s.other.quest=0;s.other.EnterVehicle(&s.cat,0);check(!s.other.base,"non quest player rejected");s.p.EnterVehicle(&s.cat,1);check(!s.p.base,"wrong seat rejected");s.board();s.ai.PassengerBoarded(&s.other,0,false);check(s.ai.m_playerGUID==s.p.guid,"foreign unboard does not clear owner");s.launch();s.p.ExitVehicle();s.ai.UpdateAI(2000);check(!s.p.motion.jumps&&!s.ai.m_launchPending,"early dismount cancels launch");}
 for(int mode=0;mode<6;++mode){Scene s;s.defeat();s.board();s.launch();if(mode==0)s.p.quest=0;if(mode==1)s.p.alive=false;if(mode==2)s.p.map=0;if(mode==3)s.cat.phase=false;if(mode==4)units.erase(2);if(mode==5)s.ai.Reset();s.ai.UpdateAI(2000);check(!s.p.motion.jumps&&!s.ai.m_launchPending,"cancel death logout phase map reset never launch");}
 {Scene s;s.defeat();s.board();s.p.quest=QUEST_STATUS_COMPLETE;check(s.spell.CheckLaunch()==SPELL_CAST_OK,"completed but unrewarded quest retains transport");s.spell.dest=nullptr;check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"missing aim rejected");s.spell.dest=&s.dest;s.dest.x=std::numeric_limits<float>::quiet_NaN();check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"NaN aim rejected");s.dest.x=500;check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"out of native spell range rejected");s.dest.x=100;s.spell.spell.m_targets.traj=false;check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"trajectory required");s.spell.spell.m_targets.traj=true;s.spell.spell.m_targets.xy=0;check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"zero speed rejected");s.spell.spell.m_targets.xy=std::numeric_limits<float>::infinity();check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"infinite speed rejected");s.spell.spell.m_targets.xy=35;s.spell.spell.m_targets.z=-1;check(s.spell.CheckLaunch()==SPELL_FAILED_BAD_TARGETS,"negative arc rejected");s.spell.spell.m_targets.z=25;s.cat.script=9;check(s.spell.CheckLaunch()==SPELL_FAILED_DONT_REPORT,"custom AI untouched");s.cat.script=7;objectMgr.id=0;check(s.spell.CheckLaunch()==SPELL_FAILED_DONT_REPORT,"missing binding rejected");}
 {Scene s;s.ai.UpdateAI(5000);check(s.cat.boulders==1,"operated catapult fires native boulder");s.defeat();s.ai.UpdateAI(15000);check(s.cat.boulders==1,"defeated operator cannot fire");s.ai.UpdateAI(180000);check(s.cat.summons==1&&lastSummon->base==&s.cat&&s.cat.vehicle.GetPassenger(2)==lastSummon.get(),"reset operator returns to seat2");s.ai.UpdateAI(180000);check(s.cat.summons==1,"live operator never duplicated");}
 {Scene s;s.defeat();s.board();s.ai.UpdateAI(180000);check(!s.cat.summons,"occupied catapult never reset");s.cat.map=0;npc_forsaken_catapult_36283 factory;check(!factory.GetAI(&s.cat),"other maps retain ordinary AI");}
 std::cout<<"Catapult operator gate, aimed jump, cast ownership and cancellation: PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
