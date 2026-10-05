#!/usr/bin/env python3
"""Compile actual Horn spell and tracker owner handlers with minimal native API fixtures."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <chrono>
#include <vector>
#include <list>
#include <map>
#include <memory>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using namespace std::chrono_literals;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,REACT_DEFENSIVE=1,TEMPSUMMON_TIMED_DESPAWN=2;
struct ObjectGuid{bool IsEmpty()const{return !id;}int id=0;static const ObjectGuid Empty;};const ObjectGuid ObjectGuid::Empty{};
bool operator!=(ObjectGuid a,ObjectGuid b){return a.id!=b.id;}
struct Position{float x,y,z,o;};struct Creature;struct Player;struct TempSummon;
struct Unit{uint32 entry=0,map=654;ObjectGuid guid;bool alive=true,phase=true;virtual ~Unit()=default;virtual Player* ToPlayer(){return nullptr;}virtual Creature* ToCreature(){return nullptr;}virtual Player* GetCharmerOrOwnerPlayerOrPlayerItself(){return nullptr;}
 uint32 GetEntry(){return entry;}uint32 GetMapId(){return map;}ObjectGuid GetGUID(){return guid;}bool IsAlive(){return alive;}bool IsInPhase(Unit*){return phase;}};
struct CreatureAI{Unit* attacked=nullptr;Player* talkedTo=nullptr;void Talk(int,Player* p){talkedTo=p;}void AttackStart(Unit* u){attacked=u;}};
struct Creature:Unit{bool hostile=true,despawn=false;Unit* victim=nullptr;CreatureAI ai;float threat=0;Creature* ToCreature()override{return this;}virtual TempSummon* ToTempSummon(){return nullptr;}
 bool IsHostileTo(Unit*){return hostile;}Unit* GetVictim(){return victim;}CreatureAI* AI(){return &ai;}void AddThreat(Unit*,float n){threat+=n;}
 void DespawnOrUnsummon(){despawn=true;}void SetReactState(int){}void CastSpell(Unit*,uint32,bool){} };
struct TempSummon:Creature{ObjectGuid summoner;TempSummon* ToTempSummon()override{return this;}ObjectGuid GetSummonerGUID(){return summoner;}};
struct Player:Unit{int status=QUEST_STATUS_INCOMPLETE;float distance=10;float GetDistance(Creature*){return 1;}std::vector<bool> personal;std::vector<std::unique_ptr<TempSummon>> summons;std::vector<uint32> durations;
 Player* ToPlayer()override{return this;}Player* GetCharmerOrOwnerPlayerOrPlayerItself()override{return this;}int GetQuestStatus(uint32){return status;}float GetExactDist(float,float,float){return distance;}
 Creature* GetSummonedCreatureByEntry(uint32 id){for(auto& c:summons)if(c->entry==id)return c.get();return nullptr;}
 Creature* SummonCreature(uint32 id,Position const&,int type,uint32 duration){if(type!=TEMPSUMMON_TIMED_DESPAWN)throw std::runtime_error("lifetime");auto c=std::make_unique<TempSummon>();c->entry=id;c->summoner=guid;auto* ptr=c.get();summons.push_back(std::move(c));durations.push_back(duration);personal.push_back(false);return ptr;}
 Creature* SummonCreature(uint32 id,float x,float y,float z,float o,int type,uint32 duration,bool privateActor){auto*c=SummonCreature(id,Position{x,y,z,o},type,duration);personal.back()=privateActor;return c;}};
std::list<Creature*> nearby;void GetCreatureListWithEntryInGrid(std::list<Creature*>& out,Player*,uint32 entry,float radius){if(entry!=38022||radius!=80)throw std::runtime_error("ranger filter");out=nearby;}
struct CreatureTemplate{uint32 faction=2207,ScriptID=42;};struct ObjectMgr{CreatureTemplate tracker;CreatureTemplate const* GetCreatureTemplate(uint32 id){return id==38027?&tracker:nullptr;}uint32 GetScriptId(char const*){return 42;}} objects;auto*sObjectMgr=&objects;
struct EventMap{uint32 now=0;std::multimap<uint32,uint32> events;void Reset(){now=0;events.clear();}void Update(uint32 n){now+=n;}
 template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P> d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}
 uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
std::map<int,Player*> players;struct ObjectAccessor{static Player* GetPlayer(Creature&,ObjectGuid id){auto it=players.find(id.id);return it==players.end()?nullptr:it->second;}};
struct ScriptedAI{Creature* me;explicit ScriptedAI(Creature*c):me(c){}bool UpdateVictim(){return false;}void DoMeleeAttackIfReady(){}};
using SpellEffIndex=int;enum SpellCastResult{SPELL_CAST_OK,SPELL_FAILED_BAD_TARGETS};
struct SpellScript{Unit* caster=nullptr;bool prevented=false;Unit* GetCaster(){return caster;}void PreventHitDefaultEffect(int){prevented=true;}};
"""
 code+=method(s,'enum eDuskHaven')+';\n'
 start=s.index('static Position const TaldorenTrackerPositions[]');end=s.index('class npc_gilneas_taldoren_tracker',start);code+=s[start:end]
 part=s[s.index('class npc_gilneas_taldoren_tracker :'):];code+=method(part,'    struct ai :').replace(' override','')+';\n'
 part=s[s.index('class spell_gilneas_horn_of_taldoren :'):]
 code+='struct Horn:SpellScript{'+method(part,'        SpellCastResult CheckTarget(')+method(part,'        void HandleHorn(')+'};\n'
 part=s[s.index('class npc_chance_36459 :'):]
 code+='struct Chance{'+method(part,'    bool OnGossipHello(').replace(' override','')+'};\n'
 part=s[s.index('class npc_gilneas_lucius_the_cruel :'):]
 code+=method(part,'    struct ai :').replace(' override','').replace('struct ai :','struct LuciusAI :').replace('ai(Creature*','LuciusAI(Creature*')+';\n'
 code+=r"""
void check(bool v,char const*n){if(!v)throw std::runtime_error(n);}
int main(){
 Player a,b;a.guid.id=1;b.guid.id=2;players[1]=&a;players[2]=&b;Horn horn;horn.caster=&a;
 check(horn.CheckTarget()==SPELL_CAST_OK,"valid horn");a.status=QUEST_STATUS_NONE;check(horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"quest gate");a.status=QUEST_STATUS_INCOMPLETE;
 a.distance=81;check(horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"scene area gate");a.distance=10;a.map=1;check(horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"map gate");a.map=654;
 objects.tracker.faction=16;check(horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"hostile custom template rejected");objects.tracker.faction=2207;objects.tracker.ScriptID=99;check(horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"unrelated custom AI rejected");objects.tracker.ScriptID=42;
 horn.HandleHorn(0);check(a.summons.empty(),"no rangers no summons");
 Creature target,otherFight,dead,friendly,otherAllyFight;TempSummon otherAlly;otherAlly.entry=38027;otherAlly.summoner=b.guid;otherFight.victim=&b;otherAllyFight.victim=&otherAlly;dead.alive=false;friendly.hostile=false;nearby={&target,&otherFight,&dead,&friendly,&otherAllyFight};
 horn.HandleHorn(0);check(a.summons.size()==8&&horn.prevented,"bounded native-event replacement");for(auto duration:a.durations)check(duration==45000,"temporary lifetime");check(target.ai.attacked&&target.threat==1000,"ranger distracted with threat");check(!otherFight.ai.attacked&&!otherAllyFight.ai.attacked&&!dead.ai.attacked&&!friendly.ai.attacked,"other encounter and invalid NPC preserved");
 horn.HandleHorn(0);check(a.summons.size()==8&&horn.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"active batch cannot duplicate");
 Creature tracker;ai trackerAI(&tracker);trackerAI.Reset();trackerAI.IsSummonedBy(&a);trackerAI.UpdateAI(1000);check(!tracker.despawn,"active owner");a.status=QUEST_STATUS_NONE;trackerAI.UpdateAI(1000);check(tracker.despawn,"abandon removes ally");a.status=QUEST_STATUS_INCOMPLETE;
 tracker.despawn=false;trackerAI.Reset();trackerAI.IsSummonedBy(&a);players.erase(1);trackerAI.UpdateAI(1000);check(tracker.despawn,"logout removes ally");players[1]=&a;
 tracker.despawn=false;trackerAI.Reset();trackerAI.IsSummonedBy(&a);a.alive=false;trackerAI.UpdateAI(1000);check(tracker.despawn,"death removes ally");a.alive=true;
 tracker.despawn=false;trackerAI.Reset();a.status=QUEST_STATUS_NONE;trackerAI.UpdateAI(1000);check(tracker.despawn,"evade keeps owner cleanup");a.status=QUEST_STATUS_INCOMPLETE;
 Chance chance;Creature cat;chance.OnGossipHello(&a,&cat);chance.OnGossipHello(&a,&cat);chance.OnGossipHello(&b,&cat);
 check(a.summons.size()==9&&b.summons.size()==1&&a.summons.back()->entry==36461,"each player gets exactly one Lucius");check(a.personal.back()&&b.personal.back()&&a.durations.back()==180000,"private bounded ambush leaves corpse loot time");check(a.summons.back()->ai.attacked==&a&&b.summons.back()->ai.attacked==&b,"ambush targets its own player");
 Player idle;idle.status=QUEST_STATUS_NONE;chance.OnGossipHello(&idle,&cat);check(idle.summons.empty(),"inactive Chance interaction");
 Creature lucius;LuciusAI l(&lucius);l.Reset();l.IsSummonedBy(&a);l.Reset();a.status=QUEST_STATUS_NONE;l.UpdateAI(1000);check(lucius.despawn,"Lucius abandon cleanup survives evade");a.status=QUEST_STATUS_INCOMPLETE;
 std::cout<<"Horn of Tal'doren native quest, ownership and summon guards: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8')
  cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
