#!/usr/bin/env python3
"""Compile the actual Avery event chain, Lorna impact hooks and knockback gate.

Fixtures replace map geometry, client packets and cast delivery. This checks
server ordering/isolation, not the client's visual timing or collision physics.
"""
from pathlib import Path
import argparse,os,subprocess,tempfile

def method(source,marker):
 start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end].replace(' override','')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2]
 city=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city1.cpp').read_text('utf8')
 scene=city[city.index('class npc_josiah_avery_trigger_50415 :'):]
 actor=city[city.index('class npc_josiah_avery_scene_35370 :'):]
 shot=city[city.index('class spell_gilneas_lorna_shot :'):]
 event=(root/'src/common/Utilities/EventMap.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <cmath>
#include <list>
#include <map>
#include <vector>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;using uint64=std::uint64_t;using ObjectGuid=int;
using namespace std::chrono_literals;
constexpr int NPC_JOSIAH_AVERY_35369=35369,NPC_JOSIAH_AVERY_35370=35370,NPC_LORNA_CROWLEY_35378=35378;
constexpr int SPELL_COSMETIC_COMBAT_ATTACK=69873,SPELL_SHOOT=6660,SPELL_GET_SHOT=67349;
constexpr int QUEST_THE_REBEL_LORDS_ARSENAL=14159,QUEST_STATUS_REWARDED=3;
constexpr int JUST_DIED=1,REACT_PASSIVE=0,TEMPSUMMON_MANUAL_DESPAWN=0;
struct Player;struct Creature;struct TempSummon;
struct Unit{
 int entry=0;bool alive=true,sameMap=true,samePhase=true;float x=0,y=0,z=12;
 std::vector<int> casts;
 virtual ~Unit()=default;virtual Player* ToPlayer(){return nullptr;}
 int GetEntry(){return entry;}bool IsAlive(){return alive;}
 bool IsInMap(Unit*){return sameMap;}bool IsInPhase(Unit*){return samePhase;}
 float GetPositionX(){return x;}float GetPositionY(){return y;}float GetPositionZ(){return z;}
 float GetAngle(Unit* target){return std::atan2(target->y-y,target->x-x);}
 void CastSpell(Unit*,int spell,bool){casts.push_back(spell);}
};
struct Player:Unit{
 int quest=QUEST_STATUS_REWARDED;bool vehicle=false,transport=false,flight=false,los=true;
 float supportDelta=0;unsigned knocks=0;float impulseXY=0,impulseZ=0;
 Player* ToPlayer()override{return this;}int GetQuestStatus(int){return quest;}
 void* GetVehicle(){return vehicle?this:nullptr;}void* GetDirectTransport(){return transport?this:nullptr;}
 bool IsInFlight(){return flight;}bool IsWithinLOS(float,float,float){return los;}
 float GetExactDist2d(Unit* target){return std::hypot(x-target->x,y-target->y);}
 void UpdateAllowedPositionZ(float,float,float& value){value+=supportDelta;}
 void KnockbackFrom(float,float,float xy,float vertical){++knocks;impulseXY=xy;impulseZ=vertical;}
};
struct Creature:Unit{
 ObjectGuid guid=0;unsigned display=36785,native=36785,corpseDelay=0,faces=0;int reaction=1;
 std::vector<unsigned> despawns;
 virtual TempSummon* ToTempSummon(){return nullptr;}
 ObjectGuid GetGUID(){return guid;}void SetDisplayId(unsigned id){display=id;}unsigned GetNativeDisplayId(){return native;}
 void SetCorpseDelay(unsigned value){corpseDelay=value;}void SetReactState(int value){reaction=value;}
 void SetFacingToObject(Unit*){++faces;}void setDeathState(int){alive=false;}
 template<typename R,typename P>void DespawnOrUnsummon(std::chrono::duration<R,P> d){despawns.push_back(std::chrono::duration_cast<std::chrono::milliseconds>(d).count());}
 void GetCreatureListWithEntryInGrid(std::list<Creature*>&,int,float);
};
struct TempSummon:Creature{
 Unit* owner=nullptr;ObjectGuid ownerGuid=0;int type=99;
 TempSummon* ToTempSummon()override{return this;}Unit* GetSummoner(){return owner;}
 ObjectGuid GetSummonerGUID(){return ownerGuid;}void SetTempSummonType(int value){type=value;}
};
std::map<ObjectGuid,Creature*> creatures;std::map<ObjectGuid,Player*> players;std::vector<Creature*> candidates;
void Creature::GetCreatureListWithEntryInGrid(std::list<Creature*>& result,int entryId,float){
 for(auto* creature:candidates)if(creature->entry==entryId)result.push_back(creature);
}
namespace ObjectAccessor{
 Player* GetPlayer(Creature&,ObjectGuid id){auto i=players.find(id);return i==players.end()?nullptr:i->second;}
 Creature* GetCreature(Creature&,ObjectGuid id){auto i=creatures.find(id);return i==creatures.end()?nullptr:i->second;}
}
struct CreatureTemplate{unsigned GetFirstValidModelId()const{return 36784;}};
struct ObjectMgr{CreatureTemplate human;CreatureTemplate const* GetCreatureTemplate(int){return &human;}} mgr;
ObjectMgr* sObjectMgr=&mgr;
KNOCK
KEEP
struct ActorAI{Creature* me=nullptr;
ACTOR_INIT
};
struct EventMap{
 using EventStore=std::multimap<uint32,uint64>;EventStore _eventMap;
 uint32 _time=0;uint64 _lastEvent=0;unsigned _phase=0;
 bool Empty()const{return _eventMap.empty();}void Update(uint32 diff){_time+=diff;}
 template<typename R,typename P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P> d){_eventMap.emplace(_time+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}
EXECUTE
};
struct Scene{
ENUM
 Creature* me=nullptr;EventMap m_events;ObjectGuid m_playerGUID=1,m_badAveryGUID=0,m_lornaGUID=3;
 uint32 m_actorRetries=0,m_impactRetries=0;unsigned talks=0;
 void Talk(int,Player*){++talks;}
UPDATE
};
struct Shot{
 Unit* caster=nullptr;Creature* hit=nullptr;int damage=100;
 Unit* GetCaster(){return caster;}Creature* GetHitCreature(){return hit;}void SetHitDamage(int value){damage=value;}
TARGET
DAMAGE
IMPACT
};
void check(bool value){if(!value)throw std::runtime_error("Gilneas scene regression");}
int main(){
 Player player;player.x=1;Creature trigger,lorna;lorna.entry=35378;lorna.guid=3;
 TempSummon avery,other;avery.entry=other.entry=35370;avery.guid=2;avery.owner=&player;avery.ownerGuid=1;other.ownerGuid=99;
 players[1]=&player;creatures[2]=&avery;creatures[3]=&lorna;candidates={&other,&avery};
 ActorAI actor;actor.me=&avery;actor.IsSummonedBy(&player);
 check(avery.display==36784&&avery.native==36785&&avery.reaction==REACT_PASSIVE);
 ActorAI unrelatedActor;unrelatedActor.me=&other;unrelatedActor.IsSummonedBy(nullptr);check(other.display==36785);
 Scene scene;scene.me=&trigger;scene.m_events.ScheduleEvent(scene.EVENTS_START_ANIM,25ms);
 scene.UpdateAI(25);scene.UpdateAI(200);
 check(scene.m_badAveryGUID==2&&avery.display==36784&&other.display==36785&&avery.type==TEMPSUMMON_MANUAL_DESPAWN);
 scene.UpdateAI(600);check(avery.display==36785&&avery.casts.empty());
 scene.UpdateAI(300);check(avery.casts==std::vector<int>{69873}&&player.knocks==1&&scene.talks==1&&lorna.casts.empty());
 scene.UpdateAI(600);check(lorna.casts==std::vector<int>{6660}&&lorna.faces==1&&avery.alive);
 scene.UpdateAI(200);check(avery.alive); // no timer-driven death before impact
 Shot shot;shot.caster=&lorna;shot.hit=&avery;shot.HandleDamage();check(shot.damage==0);
 shot.HandleImpact();check(!avery.alive&&avery.casts.back()==67349&&avery.despawns.back()==5000);
 auto n=avery.casts.size();shot.HandleImpact();check(avery.casts.size()==n); // duplicate impact
 scene.UpdateAI(100);scene.UpdateAI(1000);check(trigger.despawns.back()==10);
 Creature normal;normal.entry=42;Shot ordinary;ordinary.caster=&lorna;ordinary.hit=&normal;
 ordinary.HandleDamage();ordinary.HandleImpact();check(ordinary.damage==100&&normal.alive&&normal.casts.empty());
 avery.alive=true;ordinary.hit=&avery;ordinary.caster=&normal;ordinary.HandleDamage();ordinary.HandleImpact();check(avery.alive&&ordinary.damage==100);
 ordinary.caster=&lorna;player.quest=0;ordinary.HandleDamage();ordinary.HandleImpact();check(avery.alive&&ordinary.damage==100);player.quest=3;
 lorna.samePhase=false;ordinary.HandleDamage();ordinary.HandleImpact();check(avery.alive);lorna.samePhase=true;
 player.los=false;KnockGilneasPlayerBack(&player,&avery);check(player.knocks==1);player.los=true;
 player.supportDelta=-3;KnockGilneasPlayerBack(&player,&avery);check(player.knocks==1);player.supportDelta=0;
 player.vehicle=true;KnockGilneasPlayerBack(&player,&avery);check(player.knocks==1);player.vehicle=false;
 player.samePhase=false;KnockGilneasPlayerBack(&player,&avery);check(player.knocks==1);player.samePhase=true;
 player.x=20;KnockGilneasPlayerBack(&player,&avery);check(player.knocks==1);player.x=1;
 candidates.clear();Creature orphan;Scene missing;missing.me=&orphan;missing.m_events.ScheduleEvent(missing.EVENTS_ANIM_1,1ms);
 missing.UpdateAI(1);for(int i=0;i<20;++i)missing.UpdateAI(100);check(!orphan.despawns.empty());
 Creature missedTrigger;Scene missed;missed.me=&missedTrigger;missed.m_badAveryGUID=2;missed.m_events.ScheduleEvent(missed.EVENTS_ANIM_4,1ms);
 missed.UpdateAI(1);for(int i=0;i<55;++i)missed.UpdateAI(100);check(avery.alive); // missing/missed shot must not kill
 std::cout<<"PASS: actual Avery transformation/bite/shot order, impact-only death, owner isolation, bounded retries and guarded small knockback\n";
}
'''
 replacements={'KNOCK':method(city,'    void KnockGilneasPlayerBack('),'KEEP':method(city,'    void KeepGilneasAveryForScene('),
  'ACTOR_INIT':method(actor,'        void IsSummonedBy('),
  'ENUM':method(scene,'    enum eNpc')+';','UPDATE':method(scene,'        void UpdateAI('),
  'EXECUTE':method(event,'uint32 EventMap::ExecuteEvent(').replace('EventMap::',''),
  'TARGET':method(shot,'        Creature* GetSceneAvery('),'DAMAGE':method(shot,'        void HandleDamage('),'IMPACT':method(shot,'        void HandleImpact(')}
 for token,value in replacements.items():code=code.replace('\n'+token+'\n','\n'+value+'\n')
 with tempfile.TemporaryDirectory(prefix='gilneas-scene-') as temp:
  temp=Path(temp);cpp=temp/'scene.cpp';exe=temp/('scene.exe' if os.name=='nt' else 'scene');cpp.write_text(code,encoding='utf8')
  cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True,timeout=60)
if __name__=='__main__':main()
