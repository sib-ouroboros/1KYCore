#!/usr/bin/env python3
"""Production personal Grandma/Lucius scene, route callbacks and native loot gate."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 # Verify the real summon ordering makes private state available to GetAI.
 object_cpp=(root/'src/server/game/Entities/Object/Object.cpp').read_text('utf8')
 private=object_cpp.index('summon->SetVisibleBySummonerOnly(visibleBySummonerOnly);')
 assert private<object_cpp.index('AddToMap(summon->ToCreature());',private)<object_cpp.index('summon->InitSummon(summonSpell);',private)
 native_h=(root/'src/server/game/Entities/Creature/Creature.h').read_text('utf8')
 native_cpp=(root/'src/server/game/Entities/Creature/Creature.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <map>
#include <vector>
#include <memory>
#include <stdexcept>
#include <iostream>
using uint64=std::uint64_t;using uint32=std::uint32_t;using int32=std::int32_t;using namespace std::chrono_literals;
constexpr int POINT_MOTION_TYPE=1,UNIT_FIELD_FLAGS=0,UNIT_NPC_FLAGS=1,UNIT_NPC_FLAG_QUESTGIVER=2,UNIT_NPC_FLAG_GOSSIP=1,UNIT_FLAG_NON_ATTACKABLE=1,UNIT_FLAG_IMMUNE_TO_NPC=2,REACT_PASSIVE=0,REACT_DEFENSIVE=1,REACT_AGGRESSIVE=2,EMOTE_ONESHOT_KNEEL=1,EMOTE_ONESHOT_NONE=0,TEMPSUMMON_TIMED_DESPAWN=3;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2;
struct ObjectGuid{int id=0;bool IsEmpty()const{return !id;}bool operator==(ObjectGuid o)const{return id==o.id;}bool operator!=(ObjectGuid o)const{return id!=o.id;}static ObjectGuid const Empty;};ObjectGuid const ObjectGuid::Empty{};
struct Position{float x=0,y=0,z=0,o=0;};
constexpr uint32 CREATURE_FLAG_EXTRA_NO_PLAYER_DAMAGE_REQ=1;struct CreatureTemplate{uint32 ScriptID=7,flags_extra=0;};
struct Creature;struct Player;struct CreatureAI;struct TempSummon;
struct Unit{ObjectGuid guid;uint32 entry=0,map=654;bool alive=true;Player*owner=nullptr;virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}virtual Creature*ToCreature(){return nullptr;}ObjectGuid GetGUID()const{return guid;}uint32 GetMapId()const{return map;}uint32 GetEntry()const{return entry;}bool IsAlive()const{return alive;}virtual Player*GetCharmerOrOwnerPlayerOrPlayerItself(){return owner;}virtual bool IsInPhase(Unit const*)const{return true;}};
struct MotionMaster{std::vector<uint32>points;Position dest;int clears=0;void MovePoint(uint32 id,Position const&p){points.push_back(id);dest=p;}void MovePoint(uint32 id,float x,float y,float z){MovePoint(id,Position{x,y,z,0});}void Clear(){++clears;}};
struct Creature:Unit{CreatureAI*ai=nullptr;MotionMaster motion;Unit*victim=nullptr;bool phase=true,summon=false,personal=false,despawn=false;CreatureTemplate templateData;CreatureTemplate const*m_creatureInfo=&templateData;uint64 m_PlayerDamageReq=50;ObjectGuid loot;uint32 script=7,display=30288;int flags=0,npcflags=3,talks=0,melees=0,shots=0,emotes=0;float distance=10;Creature*ToCreature()override{return this;}CreatureAI*AI(){return ai;}uint32 GetScriptId()const{return script;}bool IsSummon()const{return summon;}bool IsVisibleBySummonerOnly()const{return personal;}bool IsInPhase(Unit const*)const override{return phase;}void RemoveFlag64(int,int f){npcflags&=~f;}void SetFlag(int,int f){flags|=f;}void RemoveFlag(int,int f){flags&=~f;}void SetReactState(int){}void SetWalk(bool){}void SetDisplayId(uint32 id){display=id;}void CombatStop(bool){victim=nullptr;}MotionMaster*GetMotionMaster(){return &motion;}void DespawnOrUnsummon(){despawn=true;}void HandleEmoteCommand(int){++emotes;}NATIVE_LOOT_GATE
 void LowerPlayerDamageReq(uint64 unDamage);ObjectGuid GetLootRecipientGUID()const{return loot;}bool hasLootRecipient()const{return !loot.IsEmpty();}void SetLootRecipient(Player*);Unit*GetVictim(){return victim;}float GetDistance(Unit*)const{return distance;}};
struct TempSummon:Creature{};
struct Player:Unit{int quest=1;float distance=1;bool phase=true;std::vector<std::unique_ptr<TempSummon>>summons;std::vector<std::unique_ptr<CreatureAI>>ais;std::vector<uint32>lifetimes;Player*ToPlayer()override{return this;}Player*GetCharmerOrOwnerPlayerOrPlayerItself()override{return this;}int GetQuestStatus(int)const{return quest;}float GetDistance(Creature*)const{return distance;}bool IsInPhase(Unit const*)const override{return phase;}Creature*GetSummonedCreatureByEntry(uint32 e){for(auto const&s:summons)if(s->entry==e&&!s->despawn)return s.get();return nullptr;}Creature*SummonCreature(uint32,float,float,float,float,int,uint32,bool);};
void Creature::SetLootRecipient(Player*p){loot=p->guid;}
struct CreatureAI{Creature*me;explicit CreatureAI(Creature*c):me(c){c->ai=this;}virtual~CreatureAI()=default;virtual void Reset(){}virtual void IsSummonedBy(Unit*){}virtual void SetGUID(ObjectGuid,int32){}virtual ObjectGuid GetGUID(int32)const{return {};}virtual void DoAction(int32){}virtual void MovementInform(uint32,uint32){}virtual void DamageTaken(Unit*,uint32&){}virtual void JustDied(Unit*){}virtual void UpdateAI(uint32){}virtual void AttackStart(Unit*u){me->victim=u;}void Talk(int,Unit const*){++me->talks;}void Talk(int,ObjectGuid){++me->talks;}};
struct ScriptedAI:CreatureAI{using CreatureAI::CreatureAI;bool UpdateVictim(){return me->victim&&me->victim->IsAlive();}void DoMeleeAttackIfReady(){++me->melees;}void DoCastVictim(uint32){++me->shots;}void SetCombatMovement(bool){}};
struct CreatureScript{explicit CreatureScript(char const*){}virtual~CreatureScript()=default;virtual CreatureAI*GetAI(Creature*)const{return nullptr;}virtual bool OnGossipHello(Player*,Creature*){return false;}};
std::map<int,Unit*>units;struct ObjectAccessor{static Player*GetPlayer(Creature&,ObjectGuid id){auto i=units.find(id.id);return i==units.end()?nullptr:i->second->ToPlayer();}static Creature*GetCreature(Creature&,ObjectGuid id){auto i=units.find(id.id);return i==units.end()?nullptr:i->second->ToCreature();}};
struct ObjectMgr{uint32 id=7;CreatureTemplate info;uint32 GetScriptId(char const*)const{return id;}CreatureTemplate const*GetCreatureTemplate(uint32)const{return &info;}}objects;auto*sObjectMgr=&objects;
struct DisplayStore{bool exists=true;void const*LookupEntry(uint32)const{return exists?this:nullptr;}}sCreatureDisplayInfoStore;
struct TextMgr{bool exists=true;bool TextExist(uint32,uint32)const{return exists;}}texts;auto*sCreatureTextMgr=&texts;
int logs=0;
#define TC_LOG_ERROR(...) (++logs)
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){now=0;events.clear();}void Update(uint32 d){now+=d;}void CancelEvent(uint32 id){for(auto i=events.begin();i!=events.end();)if(i->second==id)i=events.erase(i);else++i;}template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
'''
 code=code.replace('NATIVE_LOOT_GATE',method(native_h,'bool IsDamageEnoughForLootingAndReward() const'))
 code+=method(native_cpp,'void Creature::LowerPlayerDamageReq(uint64 unDamage)')+'\n'
 code+=method(source,'enum eDuskHaven')+';\n'
 code+=source[source.index('// Personal actor route'):source.index('// 36488')]
 code+=r'''
using G=npc_gilneas_grandma_scene::ai;using L=npc_gilneas_lucius_the_cruel::ai;
int nextId=10;
Creature*Player::SummonCreature(uint32 entry,float,float,float,float,int type,uint32 lifetime,bool privateActor){if(type!=3||lifetime!=180000||!privateActor)throw std::runtime_error("bounded private actors");auto c=std::make_unique<TempSummon>();c->entry=entry;c->guid={nextId++};c->summon=true;c->personal=privateActor;auto*ptr=c.get();units[ptr->guid.id]=ptr;summons.push_back(std::move(c));std::unique_ptr<CreatureAI>ai;if(entry==36461)ai=std::make_unique<L>(ptr);else ai=std::make_unique<G>(ptr);ai->Reset();ai->IsSummonedBy(this);ais.push_back(std::move(ai));lifetimes.push_back(lifetime);return ptr;}
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
struct Scene{Player a,b;Creature cat;npc_chance_36459 chance;Scene(){units.clear();nextId=10;objects.id=7;objects.info.ScriptID=7;texts.exists=true;sCreatureDisplayInfoStore.exists=true;logs=0;a.guid={1};b.guid={2};units[1]=&a;units[2]=&b;cat.entry=36459;}L*start(Player&p){chance.OnGossipHello(&p,&cat);auto*c=p.GetSummonedCreatureByEntry(36461);return c?dynamic_cast<L*>(c->AI()):nullptr;}G*helper(L*l){l->MovementInform(POINT_MOTION_TYPE,1);l->UpdateAI(5500);auto*c=a.GetSummonedCreatureByEntry(36458);return c?dynamic_cast<G*>(c->AI()):nullptr;}};
int main(){try{
 {Scene s;L*l=s.start(s.a);check(l&&l->m_stage==L::APPROACH&&l->me->motion.points==std::vector<uint32>{1},"Lucius approaches cat instead of attacking immediately");s.chance.OnGossipHello(&s.a,&s.cat);check(s.a.summons.size()==1,"duplicate ambush denied");l->UpdateAI(1000);check(l->me->talks==1,"actual text group0 used");l->MovementInform(2,1);check(l->m_stage==L::APPROACH,"wrong motion ignored");G*g=s.helper(l);check(g&&g->m_stage==G::APPROACH_0&&l->me->victim==&s.a,"catch starts own fight and own helper");check(g->me->npcflags==0&&s.cat.npcflags==3,"only private helper loses quest flags");g->MovementInform(1,0);g->MovementInform(1,0);check(g->me->motion.points==std::vector<uint32>({0,1}),"duplicate route callback ignored");g->MovementInform(1,1);g->MovementInform(1,1);check(g->me->display==36852&&g->me->talks==1,"transform and text once");g->UpdateAI(799);check(!g->me->victim,"attack delay");g->UpdateAI(1);check(g->me->victim==l->me,"helper targets own Lucius");g->AttackStart(&s.b);l->AttackStart(&s.b);check(g->me->victim==l->me&&l->me->victim==&s.a,"foreign targets cannot redirect personal combat");uint32 damage=20;l->DamageTaken(g->me,damage);check(!damage&&!l->me->hasLootRecipient(),"helper cannot steal cat before real participation");damage=20;l->DamageTaken(&s.a,damage);check(damage==20&&l->me->loot==s.a.guid,"positive player hit gets native tap");l->me->LowerPlayerDamageReq(damage);Unit pet;pet.owner=&s.a;damage=10;l->DamageTaken(&pet,damage);check(damage==10,"own pet allowed");l->me->LowerPlayerDamageReq(damage);damage=20;l->DamageTaken(g->me,damage);check(!damage,"tap alone does not bypass native damage requirement");damage=20;l->DamageTaken(&s.a,damage);l->me->LowerPlayerDamageReq(damage);check(l->me->IsDamageEnoughForLootingAndReward(),"actual native half-health requirement satisfied");damage=200;l->DamageTaken(g->me,damage);check(damage==200,"eligible helper lethal damage has no artificial health floor");damage=20;l->DamageTaken(&s.b,damage);check(!damage,"foreign owner damage rejected");l->me->alive=false;l->JustDied(&s.a);check(!l->me->despawn&&g->m_stage==G::RETURN_WAIT,"lootable corpse retained and helper returns");s.a.quest=QUEST_STATUS_COMPLETE;g->UpdateAI(4000);check(g->m_stage==G::RETURN_2,"completed loot does not cancel return");g->MovementInform(1,2);g->MovementInform(1,3);check(g->me->despawn&&g->m_stage==G::DONE,"helper walks home and despawns");}
 {Scene s;auto*l=s.start(s.a);auto*other=s.start(s.b);auto*g=s.helper(l);other->MovementInform(1,1);other->UpdateAI(5500);auto*otherG=dynamic_cast<G*>(s.b.GetSummonedCreatureByEntry(36458)->AI());check(g&&otherG&&g->m_luciusGUID!=otherG->m_luciusGUID,"two independent encounters");l->me->alive=false;l->JustDied(&s.a);check(g->m_stage==G::RETURN_WAIT&&otherG->m_stage==G::APPROACH_0,"death never returns another player helper");g->SetGUID(other->me->guid,36461);check(g->m_luciusGUID==l->me->guid,"active helper link cannot be stolen");}
 for(int mode=0;mode<5;++mode){Scene s;auto*l=s.start(s.a);auto*g=s.helper(l);if(mode==0)s.a.quest=0;if(mode==1)s.a.alive=false;if(mode==2)s.a.map=0;if(mode==3)l->me->phase=false;if(mode==4)units.erase(1);l->UpdateAI(1000);check(l->me->despawn&&g->me->despawn,"cancel death map phase logout clean only own actors");}
 {Scene s;auto*l=s.start(s.a);auto*g=s.helper(l);l->Reset();check(l->me->despawn&&g->me->despawn&&l->m_events.events.empty(),"evade cleanup prevents repeated ambush");}
 {Scene s;auto*l=s.start(s.a);auto*g=s.helper(l);g->UpdateAI(180000);check(g->me->despawn,"bounded stalled helper");}
 {Scene s;auto*l=s.start(s.a);auto*g=s.helper(l);sCreatureDisplayInfoStore.exists=false;g->MovementInform(1,0);g->MovementInform(1,1);check(g->me->despawn&&logs==1&&!l->me->despawn,"missing model removes helper, retains normal quest combat");}
 {Scene s;auto*l=s.start(s.a);objects.info.ScriptID=99;l->MovementInform(1,1);l->UpdateAI(5500);check(!s.a.GetSummonedCreatureByEntry(36458),"custom Grandma template never commandeered");}
 {Scene s;s.a.quest=0;check(!s.start(s.a),"quest gate");s.a.quest=1;s.a.phase=false;check(!s.start(s.a),"phase gate");s.a.phase=true;s.a.distance=6;check(!s.start(s.a),"distance gate");s.a.distance=1;objects.info.ScriptID=99;check(!s.start(s.a),"foreign Lucius script gate");}
 {Creature c;npc_gilneas_grandma_scene g;npc_gilneas_lucius_the_cruel l;check(!g.GetAI(&c)&&!l.GetAI(&c),"persistent NPC default AI preserved");c.summon=true;check(!g.GetAI(&c)&&!l.GetAI(&c),"public summons default AI preserved");c.personal=true;c.map=0;check(!g.GetAI(&c)&&!l.GetAI(&c),"foreign map default AI preserved");}
 std::cout<<"Grandma personal route, transform, fight, loot gate and owner cleanup: PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
