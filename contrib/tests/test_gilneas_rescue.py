#!/usr/bin/env python3
"""Compile production rescue/horse handlers and racial gates, not a server simulation."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2]
 s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <chrono>
#include <map>
#include <set>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using int8=std::int8_t;using namespace std::chrono_literals;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1,RACE_WORGEN=22;
struct ObjectGuid{int id=0;static const ObjectGuid Empty;bool IsEmpty()const{return !id;}explicit operator bool()const{return id;}};
const ObjectGuid ObjectGuid::Empty{};
bool operator==(ObjectGuid a,ObjectGuid b){return a.id==b.id;}bool operator!=(ObjectGuid a,ObjectGuid b){return !(a==b);}
struct Player;struct Creature;
struct Unit{bool phase=true;bool IsInPhase(Unit*){return phase;}uint32 entry=0,map=654;Player* controller=nullptr;virtual ~Unit()=default;virtual Player* ToPlayer(){return nullptr;}virtual Creature* ToCreature(){return nullptr;}uint32 GetEntry(){return entry;}uint32 GetMapId(){return map;}Player* GetCharmerOrOwnerPlayerOrPlayerItself(){return controller;}ObjectGuid guid;ObjectGuid GetGUID(){return guid;}};
struct SpellInfo{uint32 Id;};
struct Position{float m_positionX=0,m_positionY=0,m_positionZ=0;float GetPositionX(){return 0;}float GetPositionY(){return 0;}float GetPositionZ(){return 0;}float GetExactDist(Unit*){return 0;}};
float frand(float a,float){return a;}
constexpr int MOVE_RUN=1,REACT_PASSIVE=0,VEHICLE_SPELL_RIDE_HARDCODED=46598,SPELLVALUE_BASE_POINT0=0;
struct EventMap{uint32 now=0;std::multimap<uint32,uint32> events;
 void Reset(){now=0;events.clear();}void Update(uint32 d){now+=d;}
 template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P> d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}
 template<class R,class P>void RescheduleEvent(uint32 id,std::chrono::duration<R,P> d){for(auto it=events.begin();it!=events.end();)if(it->second==id)it=events.erase(it);else ++it;ScheduleEvent(id,d);}
 uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
struct Vehicle{Unit* passenger=nullptr;Unit* GetPassenger(int){return passenger;}};
struct Player:Unit{Vehicle* kit=nullptr;Vehicle* GetVehicleKit(){return kit;}int status=QUEST_STATUS_INCOMPLETE,race=22,level=5;bool alive=true,water=true;float distance=100;int exits=0;std::vector<uint32> credits,learned;std::set<uint32> rewarded,spells;
 Position GetPosition(){return {};}void GetNearPoint(Player*,float&x,float&y,float&z,float,float,float){x=y=z=0;}std::set<int>auras;bool HasAura(int id){return auras.count(id);}
 Player* ToPlayer()override{return this;}int GetQuestStatus(uint32){return status;}bool IsAlive(){return alive;}bool IsInWater(){return water;}
 void KilledMonsterCredit(uint32 id){credits.push_back(id);}void CastSpell(Unit*,uint32,bool){}void RemoveAurasDueToSpell(uint32){}
 void ExitVehicle(){++exits;}float GetDistance(Creature*){return distance;}int getRace(){return race;}int getLevel(){return level;}
 bool GetQuestRewardStatus(uint32 id){return rewarded.count(id);}bool HasSpell(uint32 id){return spells.count(id);}
 void LearnSpell(uint32 id,bool){spells.insert(id);learned.push_back(id);}
 bool Gate(uint32 spellId,bool loading);
};
struct GameObject:Unit{};
constexpr int EMOTE_STATE_NONE=0;
struct MotionMaster{int flee=0;Unit* source=nullptr;void MovePoint(int,float,float,float){}void MoveFleeing(Unit* u,uint32 t){source=u;flee=t;}};
struct Creature:Unit{int customCasts=0;void CastCustomSpell(int,int,int,Player*,bool){++customCasts;}bool summon=false;bool IsSummon(){return summon;}std::vector<uint32>casts;void CastSpell(Unit*,uint32 id,bool=true){casts.push_back(id);}void SetWalk(bool){}void SetSpeed(int,float){}float GetObjectSize(){return 1;}void SetReactState(int){}float distance=1;float GetDistance(Unit*){return distance;}void HandleEmoteCommand(int){}void SetFacingToObject(Unit*){}bool alive=true;bool stopped=false;MotionMaster motion;bool IsAlive(){return alive;}void AttackStop(){stopped=true;}void CombatStop(bool){}MotionMaster* GetMotionMaster(){return &motion;}Creature* ToCreature()override{return this;}Unit* carrier=nullptr;Creature* nearest=nullptr;bool despawn=false;int exits=0;uint32 hp=100,maxhp=100;
 Unit* GetVehicleBase(){return carrier;}void ExitVehicle(){carrier=nullptr;++exits;}
 template<class... T>void DespawnOrUnsummon(T...){despawn=true;}Creature* FindNearestCreature(uint32,float){return nearest;}
 void SetMaxHealth(uint32 n){maxhp=n;}uint32 GetMaxHealth(){return maxhp;}void SetHealth(uint32 n){hp=n;}};
std::map<int,GameObject*> objects;
std::map<int,Player*> players;std::map<int,Creature*> creatures;
struct ObjectAccessor{static GameObject* GetGameObject(Creature&,ObjectGuid id){auto it=objects.find(id.id);return it==objects.end()?nullptr:it->second;}static Player* GetPlayer(Creature&,ObjectGuid id){auto it=players.find(id.id);return it==players.end()?nullptr:it->second;}static Creature* GetCreature(Creature&,ObjectGuid id){auto it=creatures.find(id.id);return it==creatures.end()?nullptr:it->second;}};
struct ScriptedAI{Creature* me;explicit ScriptedAI(Creature*c):me(c){}void Talk(int,Player*){}bool UpdateVictim(){return false;}void DoMeleeAttackIfReady(){}};
using SpellEffIndex=int;
enum SpellCastResult{SPELL_CAST_OK,SPELL_FAILED_BAD_TARGETS};
struct SpellScript{Unit* caster=nullptr;Unit* target=nullptr;bool prevented=false;Unit* GetCaster(){return caster;}Unit* GetHitUnit(){return target;}Unit* GetExplTargetUnit(){return target;}void PreventHitDefaultEffect(int){prevented=true;}};
struct PlayerScript{explicit PlayerScript(char const*){}virtual ~PlayerScript()=default;virtual void OnLogin(Player*,bool){}virtual void OnQuestStatusChange(Player*,uint32){}};
"""
 code+=method(s,'enum eDuskHaven')+';\n'
 code+=method((root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas.h').read_text('utf8'),'enum Events')+';\n'
 for name in ['npc_drowning_watchman_36440','npc_mountain_horse_36540']:
  part=s[s.index('class '+name+' :'):];ai=method(part,'    struct '+name+'AI :').replace(' override','')
  code+='struct '+name+'{'+method(part,'    enum eNpc')+';\n'+ai+';};\n'
 part=s[s.index('class npc_mountain_horse_36555 :'):];code+=method(part,'    struct npc_mountain_horse_36555AI :').replace(' override','')+';\n'
 code+='using CreatureAI=ScriptedAI;struct FollowerFactory{'+method(part,'    CreatureAI* GetAI(').replace(' override','')+'};\n'
 racials=(root/'src/server/scripts/Custom/custom_worgen_racials.cpp').read_text('utf8')
 code+=method(racials,'enum WorgenRacials')+';\n'+method(racials,'class custom_worgen_racials :')+';\n'
 player=(root/'src/server/game/Entities/Player/Player.cpp').read_text('utf8')
 gate=method(player[player.index('bool Player::AddSpell('):],'    if (!loading && getRace() == RACE_WORGEN)')
 code+='bool Player::Gate(uint32 spellId,bool loading){'+gate+'return true;}\n'
 part=s[s.index('class npc_king_genn_greymane_37876 :'):]
 code+='struct GennAI:ScriptedAI{using ScriptedAI::ScriptedAI;EventMap m_events;ObjectGuid m_godfreyGUID;bool m_sceneStarted=false;'
 for signature in ['        void DamageTaken(']:code+=method(part,signature).replace(' override','')
 code+='};\n'
 part=s[s.index('class spell_gilneas_walden_brandy :'):]
 code+='struct WaldenScript:SpellScript{'+method(part,'        void HandleInebriate(')+'};\n'
 part=s[s.index('class spell_gilneas_half_burnt_torch :'):]
 code+='struct TorchScript:SpellScript{'+method(part,'        void HandleTorch(')+'};\n'
 part=s[s.index('class npc_enslaved_villager_37694 :'):]
 code+=method(part,'    struct npc_enslaved_villager_37694AI :').replace(' override','')+';\n'
 for name,structname in [('spell_rescue_drowning_watchman_68735','RescueSpell'),('spell_round_up_horse_68903','RoundUpSpell')]:
  part=s[s.index('class '+name+' :'):];code+='struct '+structname+':SpellScript{'+method(part,'        SpellCastResult CheckTarget(')+method(part,'        void HandleEffectDummy(')+'};\n'
 code+=r"""
void check(bool v,char const* n){if(!v)throw std::runtime_error(n);}
int main(){
 Player a,b;a.guid.id=1;b.guid.id=2;players[1]=&a;players[2]=&b;Creature liam;liam.guid.id=3;creatures[3]=&liam;
 Creature watch;watch.guid.id=4;watch.nearest=&liam;npc_drowning_watchman_36440::npc_drowning_watchman_36440AI ai(&watch);ai.Reset();
 SpellInfo wrong{172},rescue{68735};ai.SpellHit(&a,&wrong);check(ai.m_playerGUID.IsEmpty(),"wrong rescue spell");
 ai.SpellHit(&a,&rescue);watch.carrier=&a;ai.SpellHit(&b,&rescue);a.water=false;ai.UpdateAI(1000);
 check(a.credits==std::vector<uint32>{36450}&&b.credits.empty()&&watch.carrier==nullptr,"shore rescue owner and objective");
 ai.UpdateAI(3000);check(watch.despawn&&a.credits.size()==1,"one rescue credit and cleanup");
 ai.Reset();watch.despawn=false;a.status=QUEST_STATUS_NONE;ai.SpellHit(&a,&rescue);check(ai.m_playerGUID.IsEmpty(),"inactive quest");
 a.status=QUEST_STATUS_INCOMPLETE;ai.SpellHit(&a,&rescue);watch.carrier=&b;ai.UpdateAI(1000);check(watch.despawn&&a.credits.size()==1,"wrong carrier denied");
 ai.Reset();watch.despawn=false;ai.SpellHit(&a,&rescue);watch.carrier=&a;a.alive=false;ai.UpdateAI(1000);check(watch.despawn,"death cleanup");a.alive=true;
 Creature lorna;lorna.guid.id=7;lorna.entry=NPC_LORNA_CROWLEY;creatures[7]=&lorna;Creature horse;horse.nearest=&lorna;npc_mountain_horse_36540::npc_mountain_horse_36540AI h(&horse);h.Reset();
 h.PassengerBoarded(nullptr,0,true);h.PassengerBoarded(&a,0,true);h.PassengerBoarded(&b,0,true);check(b.exits==1&&h.m_playerGUID==a.guid,"horse owner cannot be overwritten");
 h.PassengerBoarded(&b,0,false);check(h.m_playerGUID==a.guid,"foreign dismount ignored");
 a.distance=100;h.UpdateAI(1000);h.PassengerBoarded(&a,0,false);check(a.credits.size()==1,"early dismount no credit");
 h.PassengerBoarded(&a,0,true);a.distance=6;h.UpdateAI(1000);h.PassengerBoarded(&a,0,false);h.PassengerBoarded(&a,0,false);
 check(a.credits==std::vector<uint32>({36450,36560})&&horse.despawn,"delivery credit once");
 h.Reset();horse.despawn=false;h.PassengerBoarded(&a,0,true);a.status=QUEST_STATUS_NONE;h.UpdateAI(1000);h.PassengerBoarded(&a,0,false);check(a.credits.size()==2&&h.m_playerGUID.IsEmpty(),"abandon clears horse owner without credit");a.status=QUEST_STATUS_INCOMPLETE;
 custom_worgen_racials script;Player fresh;fresh.rewarded.insert(14375);script.OnLogin(&fresh,false);check(fresh.learned.empty()&&!fresh.Gate(68996,false),"early transformation does not grant Two Forms");
 fresh.rewarded.insert(24593);script.OnQuestStatusChange(&fresh,24593);script.OnLogin(&fresh,false);check(fresh.learned==std::vector<uint32>{68996}&&fresh.Gate(68996,false),"reward and relog exactly once");
 Player other;other.race=1;other.rewarded.insert(24593);script.OnLogin(&other,false);check(other.learned.empty()&&other.Gate(68996,false),"other races unchanged");
 Player saved;check(saved.Gate(68996,true),"saved spell load preserved");saved.level=25;check(saved.Gate(68996,false),"existing level fallback preserved");
 Creature genn,godfrey,ambient;godfrey.guid.id=5;genn.nearest=&godfrey;GennAI g(&genn);uint32 damage=500;g.DamageTaken(&ambient,damage);check(damage==0,"ambient NPC cannot kill Genn");
 damage=500;ambient.controller=&a;g.DamageTaken(&ambient,damage);check(damage==500,"player pet damage unchanged");
 damage=500;g.DamageTaken(&a,damage);check(damage==500,"player damage unchanged");genn.map=1;ambient.controller=nullptr;g.DamageTaken(&ambient,damage);check(damage==500,"other map unchanged");genn.map=654;
 Creature walden;walden.entry=37733;WaldenScript spell;spell.caster=&walden;spell.target=&a;spell.HandleInebriate(2);check(spell.prevented,"Walden quest attack cannot persist alcohol");
 spell.prevented=false;a.status=QUEST_STATUS_NONE;spell.HandleInebriate(2);check(!spell.prevented,"nonquest spell unchanged");a.status=QUEST_STATUS_INCOMPLETE;walden.map=1;spell.HandleInebriate(2);check(!spell.prevented,"other map unchanged");walden.map=654;walden.entry=1;spell.HandleInebriate(2);check(!spell.prevented,"other caster unchanged");
 TorchScript torch;Creature vermin;torch.caster=&a;torch.target=&vermin;vermin.entry=37889;torch.HandleTorch(0);check(vermin.motion.flee==5000&&vermin.stopped&&a.credits.size()==2,"torch scares rat without credit");
 vermin.motion.flee=0;vermin.entry=1;torch.HandleTorch(0);check(vermin.motion.flee==0,"other NPC unaffected");vermin.entry=37891;torch.HandleTorch(0);check(vermin.motion.flee==5000,"tunnel spider scared");vermin.motion.flee=0;vermin.entry=37892;a.status=QUEST_STATUS_NONE;torch.HandleTorch(0);check(!vermin.motion.flee,"torch quest gate");a.status=QUEST_STATUS_INCOMPLETE;a.map=1;torch.HandleTorch(0);check(!vermin.motion.flee,"torch map gate");a.map=654;
 Creature villager;GameObject ball;ball.guid.id=6;ball.entry=201775;objects[6]=&ball;npc_enslaved_villager_37694AI v(&villager);v.Reset();v.SetGUID(ball.guid,201775);v.SetGUID(a.guid,PLAYER_GUID);v.DoAction(EVENT_START_ANIM);
 check(v.m_sceneStarted&&v.GetGUID(PLAYER_GUID)==a.guid&&v.m_events.events.size()==1,"valid chain scene starts once");v.SetGUID(b.guid,PLAYER_GUID);v.DoAction(EVENT_START_ANIM);check(v.GetGUID(PLAYER_GUID)==a.guid&&v.m_events.events.size()==1,"second player cannot overwrite chain scene");
 v.UpdateAI(1000);v.UpdateAI(3000);check(villager.motion.flee==7000,"released villager runs away");v.UpdateAI(6000);check(villager.despawn&&a.credits.size()==2,"native GO credit not duplicated by AI");v.Reset();check(!v.m_sceneStarted&&v.m_events.events.empty()&&v.GetGUID(PLAYER_GUID).IsEmpty(),"chain respawn resets state");
 villager.distance=8;v.SetGUID(ball.guid,201775);v.SetGUID(a.guid,PLAYER_GUID);v.DoAction(EVENT_START_ANIM);check(!v.m_sceneStarted,"distant chain cannot release wrong NPC");villager.distance=1;
 v.SetGUID(ball.guid,201775);v.SetGUID(a.guid,PLAYER_GUID);a.status=QUEST_STATUS_NONE;v.DoAction(EVENT_START_ANIM);check(!v.m_sceneStarted,"chain quest gate");a.status=QUEST_STATUS_INCOMPLETE;
 RescueSpell rescueCast;rescueCast.caster=&a;rescueCast.target=&watch;watch.entry=36440;watch.alive=true;watch.carrier=nullptr;a.water=true;check(rescueCast.CheckTarget()==SPELL_CAST_OK,"valid rescue cast");watch.carrier=&b;check(rescueCast.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"already carried watchman denied before aura");watch.carrier=nullptr;Vehicle kit;kit.passenger=&horse;a.kit=&kit;check(rescueCast.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"occupied carry seat denied");a.kit=nullptr;rescueCast.target=nullptr;check(rescueCast.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"missing rescue target denied");
 RoundUpSpell rope;rope.caster=&a;rope.target=&horse;horse.entry=36540;check(rope.CheckTarget()==SPELL_CAST_OK,"valid rope target");horse.carrier=&b;check(rope.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"another mounted horse denied before summon");horse.carrier=nullptr;a.status=QUEST_STATUS_NONE;check(rope.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"rope quest gate prevents native summon");a.status=QUEST_STATUS_INCOMPLETE;
 for(int mode=0;mode<6;++mode){h.Reset();horse.despawn=false;horse.phase=true;lorna.phase=true;lorna.alive=true;lorna.entry=NPC_LORNA_CROWLEY;a.map=654;a.distance=6;a.alive=true;h.PassengerBoarded(&a,0,true);h.UpdateAI(1000);check(h.m_lornaIsNear,"near snapshot prepared");auto count=a.credits.size();if(mode==0)a.distance=100;if(mode==1)lorna.phase=false;if(mode==2)lorna.alive=false;if(mode==3)lorna.entry=1;if(mode==4)horse.phase=false;if(mode==5)a.map=0;h.PassengerBoarded(&a,0,false);check(a.credits.size()==count,"stale proximity or invalid phase actor cannot deliver horse");}
 horse.phase=true;lorna.phase=true;lorna.alive=true;lorna.entry=NPC_LORNA_CROWLEY;a.map=654;a.distance=6;
 for(int mode=0;mode<4;++mode){h.Reset();int exits=a.exits;if(mode==0)a.alive=false;if(mode==1)a.map=0;if(mode==2)horse.map=0;if(mode==3)horse.phase=false;h.PassengerBoarded(&a,0,true);check(h.m_playerGUID.IsEmpty()&&a.exits==exits+1,"invalid boarding cannot reserve horse");a.alive=true;a.map=654;horse.map=654;horse.phase=true;}
 for(int mode=0;mode<4;++mode){horse.despawn=false;rope.caster=&a;rope.target=&horse;if(mode==0)a.alive=false;if(mode==1)a.map=0;if(mode==2)horse.phase=false;if(mode==3)horse.carrier=&b;check(rope.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"rope rejects dead cross-map phase or mounted horse");rope.HandleEffectDummy(1);check(!horse.despawn,"hit-time revalidation preserves invalid target");a.alive=true;a.map=654;horse.phase=true;horse.carrier=nullptr;}
 {Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();f.IsSummonedBy(nullptr);check(follower.despawn,"missing rope owner fails safely");}
 {Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();f.IsSummonedBy(&a);f.IsSummonedBy(&b);check(f.m_playerGUID==a.guid&&follower.casts.size()==1,"rope owner and channel cannot be stolen");}
 for(int mode=0;mode<6;++mode){Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();a.auras={SPELL_RIDE_VEHICLE,SPELL_ROPE_CHANNEL};f.IsSummonedBy(&a);if(mode==0)a.alive=false;if(mode==1)a.map=0;if(mode==2)follower.phase=false;if(mode==3)a.status=QUEST_STATUS_NONE;if(mode==4)players.erase(a.guid.id);f.UpdateAI(mode==5?1200000:100);check(follower.despawn&&follower.casts.size()==1,"rope helper cleans death map phase abandon logout timeout without credit");a.alive=true;a.map=654;a.status=QUEST_STATUS_INCOMPLETE;players[a.guid.id]=&a;}
 {Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();f.IsSummonedBy(&a);f.MoveInLineOfSight(&lorna);a.auras={SPELL_ROPE_CHANNEL};lorna.phase=false;f.UpdateAI(100);check(follower.despawn&&follower.casts.size()==1,"invisible Lorna cannot receive rope delivery");lorna.phase=true;}
 {Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();f.IsSummonedBy(&a);f.Reset();f.IsSummonedBy(&b);check(follower.despawn&&f.m_playerGUID==a.guid&&f.m_events.events.empty(),"reset cancels rope helper without allowing reassignment");}
 {Creature follower;npc_mountain_horse_36555AI f(&follower);f.Reset();f.IsSummonedBy(&a);f.MoveInLineOfSight(&lorna);lorna.phase=false;f.CheckLornaRelated(&a);check(f.m_lornaGUID.IsEmpty(),"lost phase clears cached Lorna");lorna.phase=true;f.MoveInLineOfSight(&lorna);f.CheckLornaRelated(&a);check(f.m_isLornaNear,"visible Lorna can be reacquired");}
 {Creature follower;FollowerFactory factory;check(!factory.GetAI(&follower),"persistent horse does not get capped personal follower AI");follower.summon=true;follower.map=0;check(!factory.GetAI(&follower),"other map default AI preserved");follower.map=654;auto*ai=factory.GetAI(&follower);check(ai!=nullptr,"owned Gilneas summon receives follower AI");delete static_cast<npc_mountain_horse_36555AI*>(ai);}
 a.auras.clear();
 for(int mode=0;mode<5;++mode){ai.Reset();watch.despawn=false;watch.phase=true;watch.map=654;a.alive=true;a.map=654;if(mode==0)a.alive=false;if(mode==1)a.map=0;if(mode==2)watch.phase=false;if(mode==3)watch.map=0;if(mode==4)watch.alive=false;ai.SpellHit(&a,&rescue);check(ai.m_playerGUID.IsEmpty(),"invalid rescue owner or target cannot reserve watchman");watch.alive=true;watch.map=654;watch.phase=true;a.alive=true;a.map=654;}
 for(int mode=0;mode<4;++mode){ai.Reset();watch.despawn=false;watch.phase=true;watch.map=654;a.water=false;ai.SpellHit(&a,&rescue);watch.carrier=&a;auto count=a.credits.size();if(mode==0)watch.phase=false;if(mode==1)a.map=0;if(mode==2)liam.phase=false;if(mode==3)liam.alive=false;ai.UpdateAI(1000);check(a.credits.size()==count,"phase map or unavailable Liam cannot award rescue");liam.phase=true;liam.alive=true;watch.phase=true;a.map=654;watch.carrier=nullptr;}
 {ai.Reset();watch.despawn=false;ai.SpellHit(&a,&rescue);watch.carrier=&a;ai.UpdateAI(1000);auto count=a.credits.size();ai.SpellHit(&b,&rescue);watch.carrier=&b;ai.UpdateAI(1000);check(ai.m_delivered&&a.credits.size()==count&&b.credits.empty(),"delivered watchman cannot be credited again before despawn");watch.carrier=nullptr;}
 a.water=true;rescueCast.caster=&a;rescueCast.target=&watch;for(int mode=0;mode<3;++mode){if(mode==0)a.alive=false;if(mode==1)a.map=0;if(mode==2)watch.phase=false;check(rescueCast.CheckTarget()==SPELL_FAILED_BAD_TARGETS,"rescue precast life map and phase gate");a.alive=true;a.map=654;watch.phase=true;}
 {ai.Reset();watch.carrier=nullptr;watch.phase=true;watch.alive=true;a.alive=true;a.map=654;a.water=true;a.status=QUEST_STATUS_INCOMPLETE;Vehicle seat;a.kit=&seat;rescueCast.caster=&a;rescueCast.target=&watch;int before=watch.customCasts;rescueCast.HandleEffectDummy(1);check(watch.customCasts==before+1,"valid native rescue hit retains vehicle ride spell");watch.phase=false;rescueCast.HandleEffectDummy(1);check(watch.customCasts==before+1,"phase change between cast and hit cannot attach watchman");watch.phase=true;a.kit=nullptr;}
 std::cout<<"Gilneas rescue, horse ownership and Two Forms gates: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8')
  cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
