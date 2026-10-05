#!/usr/bin/env python3
"""Production pack controller/attackers; minimal engine fixtures, no full-server claim."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <algorithm>
#include <chrono>
#include <map>
#include <set>
#include <list>
#include <vector>
#include <memory>
#include <functional>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using uint64=std::uint64_t;using DamageEffectType=int;struct SpellInfo{};using namespace std::chrono_literals;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,REACT_PASSIVE=0,REACT_AGGRESSIVE=2,TEMPSUMMON_TIMED_DESPAWN=2,MOVE_RUN=1;
constexpr int EVENT_SEND_MORE_MASTIFF=901,EVENT_CHECK_ATTACK=7,QUEST_LEADER_OF_THE_PACK=14386,NPC_DARK_RANGER_THYALA=36312,NPC_TRIGGER=36198,NPC_MASTIFF=36405,PLAYER_GUID=10;
using EvadeReason=int;
struct ObjectGuid{int id=0;bool IsEmpty()const{return !id;}static const ObjectGuid Empty;};const ObjectGuid ObjectGuid::Empty{};
bool operator!=(ObjectGuid a,ObjectGuid b){return a.id!=b.id;}
struct Player;struct Creature;struct TempSummon;
struct Unit{uint32 map=654,entry=0;ObjectGuid guid;bool alive=true,phase=true;virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}virtual Creature*ToCreature(){return nullptr;}ObjectGuid GetGUID(){return guid;}uint32 GetMapId(){return map;}uint32 GetEntry(){return entry;}bool IsAlive(){return alive;}bool IsInWorld(){return true;}bool InSamePhase(Unit*){return phase;}};
struct MotionMaster{void MoveChase(Unit*,float,float){}void MoveIdle(){}};
struct Position{};float frand(float,float){return 0;}uint32 urand(uint32 a,uint32){return a;}
struct CreatureAI{std::map<int32,int>ids;virtual~CreatureAI()=default;virtual void SetGUID(ObjectGuid g,int32 i){ids[i]=g.id;}};
struct Creature:Unit{bool controlled=false;bool IsControlledByPlayer(){return controlled;}Creature*ToCreature()override{return this;}uint64 lowered=0,health=100;float multiplier=1;void SetLootRecipient(Player*p){tap=p;}void LowerPlayerDamageReq(uint64 d){lowered+=d;}uint64 GetHealth(){return health;}float GetHealthMultiplierForTarget(Creature*){return multiplier;}bool despawn=false;float distance=5;MotionMaster motion;CreatureAI ai;Player*tap=nullptr;Creature*nearest=nullptr;Unit*victim=nullptr;ObjectGuid owner;
 std::function<void(Creature*)>onSummon;std::vector<std::unique_ptr<Creature>>children;
 virtual TempSummon*ToTempSummon(){return nullptr;}void SetOwnerGUID(ObjectGuid g){owner=g;}CreatureAI*AI(){return &ai;}MotionMaster*GetMotionMaster(){return &motion;}Creature*FindNearestCreature(int,float){return nearest;}Player*GetLootRecipient(){return tap;}bool isTappedBy(Player*p){return tap==p;}
 void SetReactState(int){}void SetWalk(bool){}void SetSpeed(int,bool){}void DespawnOrUnsummon(){despawn=true;}void DespawnOrUnsummon(int){despawn=true;}Position GetNearPosition(float,float){return {};}
 float GetDistance(Unit*){return distance;}float GetDistance2d(Unit*){return distance;}bool IsInCombat(){return victim;}Unit*GetVictim(){return victim;}void Attack(Unit*u,bool){victim=u;}
 Creature*SummonCreature(int id,Position const&,int,uint32){auto c=std::make_unique<Creature>();c->entry=id;c->guid.id=100+children.size();auto*ptr=c.get();children.push_back(std::move(c));if(onSummon)onSummon(ptr);return ptr;}};
struct TempSummon:Creature{ObjectGuid summoner;TempSummon*ToTempSummon()override{return this;}ObjectGuid GetSummonerGUID(){return summoner;}};
struct Player:Unit{int status=QUEST_STATUS_INCOMPLETE;Creature*pack=nullptr;Player*ToPlayer()override{return this;}int GetQuestStatus(int){return status;}Creature*GetSummonedCreatureByEntry(int){return pack;}};
std::map<int,Player*>players;std::map<int,Creature*>creatures;
struct ObjectAccessor{static Player*GetPlayer(Creature&,ObjectGuid g){auto i=players.find(g.id);return i==players.end()?nullptr:i->second;}static Creature*GetCreature(Creature&,ObjectGuid g){auto i=creatures.find(g.id);return i==creatures.end()?nullptr:i->second;}};
std::list<Creature*>triggers;void GetCreatureListWithEntryInGrid(std::list<Creature*>&out,Creature*,int,float){out=triggers;}
struct SummonList{std::set<int>ids;Creature*me;explicit SummonList(Creature*c):me(c){}void Summon(Creature*c){ids.insert(c->guid.id);}void Despawn(Creature*c){ids.erase(c->guid.id);}void DespawnAll(){for(auto&c:me->children)c->despawn=true;ids.clear();}std::size_t size(){return ids.size();}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){events.clear();now=0;}void Update(uint32 d){now+=d;}template<class R,class P>void ScheduleEvent(uint32 i,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),i);}template<class R,class P>void RescheduleEvent(uint32 i,std::chrono::duration<R,P>d){ScheduleEvent(i,d);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto i=events.begin()->second;events.erase(events.begin());return i;}};
struct ScriptedAI:CreatureAI{Creature*me;int melees=0;explicit ScriptedAI(Creature*c):me(c){}bool UpdateVictim(){return me->victim;}void DoMeleeAttackIfReady(){++melees;}};
struct SpellScript{Unit*caster=nullptr;Unit*GetCaster(){return caster;}};enum SpellCastResult{SPELL_CAST_OK,SPELL_FAILED_BAD_TARGETS};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
"""
 for name in ('npc_mastiff_36409AI','npc_mastiff_36405AI'):
  part=s[s.index('    struct '+name):];code+=method(part,'    struct '+name).replace(' override','')+';\n'
 part=s[s.index('class npc_mastiff_36405 :'):]
 code+='struct Factory {'+method(part,'    CreatureAI* GetAI(').replace(' override','')+'};\n'
 code+='struct CheckCast:SpellScript {'+method(s[s.index('class spell_gilneas_leader_of_the_pack :'):],'        SpellCastResult CheckPack(')+'};\n'
 code+=r"""
int main(){
 Player p,other;p.guid.id=1;other.guid.id=2;players[1]=&p;players[2]=&other;
 Creature target;target.guid.id=3;target.entry=NPC_DARK_RANGER_THYALA;creatures[3]=&target;
 Creature trigger;triggers.assign(60,&trigger);
 Creature controller;controller.guid.id=4;controller.nearest=&target;creatures[4]=&controller;
 npc_mastiff_36409AI c(&controller);c.Reset();controller.onSummon=[&](Creature*s){c.JustSummoned(s);};c.IsSummonedBy(&p);c.UpdateAI(250);
 check(c.m_summons.size()==50&&controller.children.size()==50,"per-summon cap prevents trigger overshoot");
 c.UpdateAI(250);check(controller.children.size()==50,"cap prevents more summons");
 Creature*dead=controller.children.front().get();c.SummonedCreatureDies(dead,nullptr);c.SummonedCreatureDespawn(dead);check(c.m_summons.size()==49,"death plus despawn removes once");
 c.UpdateAI(250);check(controller.children.size()==51&&c.m_summons.size()==50,"one freed slot replenishes once");
 check(controller.children.back()->ai.ids[PLAYER_GUID]==1,"pack receives its real player owner");
 TempSummon dog;dog.summoner.id=4;npc_mastiff_36405AI d(&dog);d.Reset();d.SetGUID(p.guid,PLAYER_GUID);d.SetGUID(target.guid,NPC_DARK_RANGER_THYALA);d.UpdateAI(1000);check(dog.owner.id==1&&dog.victim==&target,"owned mastiff attacks intended Thyala with native ownership");
 uint32 hit=10;d.DamageDealt(&target,hit,0,nullptr);check(target.tap==&p&&target.lowered==10&&hit==10,"real pack damage reaches native recipient and requirement");
 target.tap=&other;d.DamageDealt(&target,hit,0,nullptr);check(target.tap==&other&&target.lowered==10,"foreign recipient not stolen");target.tap=&p;
 hit=0;d.DamageDealt(&target,hit,0,nullptr);check(target.lowered==10,"zero damage grants nothing");
 hit=10;target.multiplier=2;d.DamageDealt(&target,hit,0,nullptr);check(target.lowered==15,"native health scaling respected");target.multiplier=1;dog.controlled=true;d.DamageDealt(&target,hit,0,nullptr);check(target.lowered==15,"player-controlled damage is not counted twice");dog.controlled=false;
 Creature innocent;innocent.guid.id=99;innocent.entry=NPC_DARK_RANGER_THYALA;d.DamageDealt(&innocent,hit,0,nullptr);check(!innocent.tap&&!innocent.lowered,"other target untouched");
 Factory factory;Creature staticDog;check(!factory.GetAI(&staticDog),"persistent mastiff delegates to ordinary engine AI");std::unique_ptr<CreatureAI> ownedAI(factory.GetAI(&dog));check(bool(ownedAI),"quest summons use scoped AI");
 Creature ordinary;ordinary.victim=&target;npc_mastiff_36405AI ordinaryAI(&ordinary);ordinaryAI.Reset();ordinaryAI.UpdateAI(1000);check(!ordinary.despawn&&ordinaryAI.melees==1,"static mastiff keeps ordinary combat");
 p.status=QUEST_STATUS_NONE;c.UpdateAI(1);check(controller.despawn&&c.m_summons.size()==0,"abandon cleans entire pack");d.UpdateAI(1);check(dog.despawn,"abandon cleans child");p.status=QUEST_STATUS_INCOMPLETE;
 for(int mode=0;mode<5;++mode){Creature ctrl;ctrl.nearest=&target;target.tap=nullptr;target.alive=true;p.alive=true;players[1]=&p;npc_mastiff_36409AI a(&ctrl);a.IsSummonedBy(&p);
  if(mode==0)target.alive=false;
  if(mode==1)p.alive=false;
  if(mode==2)players.erase(1);
  if(mode==3)target.tap=&other;
  a.UpdateAI(mode==4?120000:1);check(ctrl.despawn,"target death/owner death/logout/foreign tap/timeout cleanup");}
 p.alive=true;players[1]=&p;CheckCast cast;cast.caster=&p;check(cast.CheckPack()==SPELL_CAST_OK,"native item cast allowed");p.pack=&controller;check(cast.CheckPack()==SPELL_FAILED_BAD_TARGETS,"duplicate item use denied");
 std::cout<<"Mastiff native cap, death/despawn, owner, attribution and cleanup: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
