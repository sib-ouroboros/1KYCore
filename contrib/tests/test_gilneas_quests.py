#!/usr/bin/env python3
"""Actual quest gates, mastiff command, stocks transition and Avery reward hook.

Entity/AI/spell visuals are fixtures; full server builds and client acceptance
are still required for movement, phase visibility and cinematic presentation.
"""
import os
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end].replace(' override','')


def main():
    root=Path(__file__).resolve().parents[2]
    city=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city1.cpp').read_text('utf8')
    dusk=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
    assert 'SPELL_IN_STOCKS                             = 69196,' in dusk
    helpers=method(city,'    bool CanFightGilneasLurker(')+'\n'+method(city,'    void StartGilneasMastiffAttack(')
    lurker=city[city.index('class npc_bloodfang_lurker_35463 :'):]
    attack=method(lurker,'        void AttackStart(')
    damage=method(lurker,'        void DamageTaken(')
    king=dusk[dusk.index('class npc_king_genn_greymane_36332 :'):]
    recovery=dusk[dusk.index('class player_gilneas_stocks_recovery :'):]
    avery=city[city.index('class npc_josiah_avery_35369 :'):]
    command=city[city.index('class spell_gilneas_attack_lurker :'):]
    event_source=(root/'src/common/Utilities/EventMap.cpp').read_text('utf8')
    harness=r'''
#include "EventProcessor.h"
#include <cstdint>
#include <chrono>
#include <functional>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
using uint32=std::uint32_t;using uint64=std::uint64_t;
using namespace std::chrono_literals;
constexpr int QUEST_AMONG_HUMANS_AGAIN=14313,QUEST_FROM_THE_SHADOWS=14204,QUEST_LAST_CHANCE_AT_HUMANITY=14375,QUEST_THE_REBEL_LORDS_ARSENAL=14159;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2,QUEST_STATUS_REWARDED=3;
constexpr int NPC_GILNEAN_MASTIFF=35631,NPC_BLOODFANG_LURKER=35463;
constexpr int SPELL_SHADOWSTALKER_STEALTH=5916,SPELL_IN_STOCKS=69196,SPELL_SELF_ROOT=42716;
constexpr int SPELL_FADE_BACK=94053,SPELL_PHASE_QUEST_ZONE_SPECIFIC_06=68481;
constexpr int SPELL_FORCE_CAST_SUMMON_JOSIAH=67352,SPELL_WORGEN_BITE=72870;
constexpr unsigned UNIT_FIELD_FLAGS_2=0,UNIT_FLAG2_DISABLE_TURN=0x8000;
constexpr int REACT_DEFENSIVE=1;
struct Player;struct Creature;struct Unit;struct TempSummon;
constexpr int EFFECT_MOTION_TYPE=16,CHASE_MOTION_TYPE=5,TYPEID_UNIT=3;
constexpr int UNIT_STATE_CONFUSED=1,UNIT_STATE_FLEEING=2;
struct Guid{bool IsEmpty()const{return true;}};
struct MotionMaster{int type=CHASE_MOTION_TYPE;unsigned chases=0;Unit* target=nullptr;
    int GetCurrentMovementGeneratorType(){return type;}
    void MoveChase(Unit* victim){type=CHASE_MOTION_TYPE;target=victim;++chases;}};
struct CharmInfo{
    bool following=true,returning=true,stay=true,commandFollow=true,commandAttack=false;
    void SetIsFollowing(bool v){following=v;}void SetIsReturning(bool v){returning=v;}
    void SetIsAtStay(bool v){stay=v;}void SetIsCommandFollow(bool v){commandFollow=v;}
    void SetIsCommandAttack(bool v){commandAttack=v;}
};
struct Unit{
    bool sameMap=true,samePhase=true;bool IsInMap(Unit*){return sameMap;}bool IsInPhase(Unit*){return samePhase;}
    int entry=0;bool alive=true;Player* player=nullptr;CharmInfo* charm=nullptr;MotionMaster motion;
    MotionMaster* GetMotionMaster(){return &motion;}
    int GetTypeId(){return TYPEID_UNIT;}bool HasUnitState(int){return false;}
    virtual Unit* GetVictim(){return nullptr;}
    void CastSpell(Unit*,int,bool){}
    virtual ~Unit()=default;
    Player* GetCharmerOrOwnerPlayerOrPlayerItself(){return player;}
    int GetEntry()const{return entry;}bool IsAlive()const{return alive;}
    CharmInfo* GetCharmInfo(){return charm;}virtual Creature* ToCreature(){return nullptr;}
    virtual void RemoveAura(int){}
};
struct Aura{int duration=0,maxDuration=0;void SetDuration(int v){duration=v;}void SetMaxDuration(int v){maxDuration=v;}};
struct Player:Unit{
    int nextQuest=QUEST_STATUS_NONE;int quest=QUEST_STATUS_NONE,map=654,area=4786;unsigned flags=UNIT_FLAG2_DISABLE_TURN|0x100;
    std::map<int,Aura> auras;std::vector<int> casts;EventProcessor m_Events;
    int GetQuestStatus(int id)const{return id==QUEST_AMONG_HUMANS_AGAIN?nextQuest:quest;}int GetMapId()const{return map;}int GetAreaId()const{return area;}
    void RemoveAura(int id)override{auras.erase(id);}bool HasAura(int id)const{return auras.count(id);}
    Aura* GetAura(int id){return HasAura(id)?&auras[id]:nullptr;}
    void RemoveFlag(unsigned,unsigned bit){flags&=~bit;}
    void CastSpell(Player*,int id,bool){casts.push_back(id);auras[id]={};}
};
struct AI{Unit* victim=nullptr;unsigned attacks=0;virtual ~AI()=default;
    MotionMaster* motion=nullptr;void MovementInform(int,int){}
    virtual void AttackStart(Unit* target){victim=target;++attacks;if(motion)motion->MoveChase(target);}};
struct Creature:Unit{
    ::AI ai;bool stealth=true;int reaction=0;std::vector<int> casts;unsigned bites=0;
    Creature* ToCreature()override{return this;}::AI* AI(){return &ai;}
    void RemoveAura(int id)override{if(id==SPELL_SHADOWSTALKER_STEALTH)stealth=false;}
    unsigned corpseDelay=0,despawnMs=0;
    void Update(uint32){}virtual TempSummon* ToTempSummon(){return nullptr;}
    void SetCorpseDelay(unsigned v){corpseDelay=v;}
    template<typename Rep,typename Period>void DespawnOrUnsummon(std::chrono::duration<Rep,Period> v){despawnMs=std::chrono::duration_cast<std::chrono::milliseconds>(v).count();}
    Creature(){ai.motion=&motion;}
    void SetReactState(int value){reaction=value;}Unit* GetVictim()override{return ai.victim;}
    bool Attack(Unit* target,bool){ai.victim=target;return true;}
    void CastSpell(Player*,int id,bool){casts.push_back(id);}void AddAura(int,Player*){++bites;}
};
enum {DEAD=0,CORPSE=1,TEMPSUMMON_MANUAL_DESPAWN=0,TEMPSUMMON_TIMED_DESPAWN,
    TEMPSUMMON_TIMED_DESPAWN_OUT_OF_COMBAT,TEMPSUMMON_CORPSE_TIMED_DESPAWN,
    TEMPSUMMON_CORPSE_DESPAWN,TEMPSUMMON_DEAD_DESPAWN,TEMPSUMMON_TIMED_OR_CORPSE_DESPAWN,
    TEMPSUMMON_TIMED_OR_DEAD_DESPAWN};
#define TC_LOG_ERROR(...) ((void)0)
struct TempSummon:Creature{
    int m_type=TEMPSUMMON_CORPSE_DESPAWN,m_deathState=CORPSE;
    uint32 m_timer=0,m_lifetime=0;bool removed=false;
    TempSummon* ToTempSummon()override{return this;}
    void SetTempSummonType(int value){m_type=value;}
    bool IsInCombat(){return false;}void UnSummon(){removed=true;}
TEMP_SUMMON_UPDATE
};
AVERY_LIFETIME
HELPERS
namespace ObjectAccessor{Unit* GetUnit(Unit&,Guid){return nullptr;}}
struct EffectMovementGenerator{
    unsigned _arrivalSpellId=0,_id=0;Guid _arrivalSpellCasterGuid,_arrivalSpellTargetGuid;
EFFECT_FINALIZE
};
using SpellCastResult=int;
constexpr int SPELL_CAST_OK=0,SPELL_FAILED_BAD_TARGETS=1;
struct Command{
    Unit* caster=nullptr;Unit* GetCaster(){return caster;}
CHECKCAST
};
struct ScriptedAI{Creature* me;explicit ScriptedAI(Creature* c):me(c){};
    void AttackStart(Unit* target){me->ai.AttackStart(target);}};
struct Lurker:ScriptedAI{using ScriptedAI::ScriptedAI;
ATTACK
DAMAGE
};
STOCKS_EVENT
STOCKS
struct Quest{int id,reward;int GetQuestId()const{return id;}int GetRewSpell()const{return reward;}};
struct King{
KING
};
struct Recovery{
RECOVERY
};
struct Avery{
AVERY
};
struct EventMap{
    using EventStore=std::multimap<uint32,uint64>;
    EventStore _eventMap;uint32 _time=0;uint64 _lastEvent=0;unsigned _phase=0;
    bool Empty()const{return _eventMap.empty();}
    void Update(uint32 diff){_time+=diff;}
    template<typename Rep,typename Period> void ScheduleEvent(uint32 id,std::chrono::duration<Rep,Period> delay){
        _eventMap.emplace(_time+std::chrono::duration_cast<std::chrono::milliseconds>(delay).count(),id);
    }
EVENT_EXECUTE
};
namespace ObjectAccessor{Player* GetPlayer(Creature&,int){return nullptr;}}
constexpr int EVENT_START_ANIM=999;
struct AveryDialogue{
AVERY_EVENTS
    Creature* me=nullptr;EventMap m_events;int m_playerGUID=0;std::vector<unsigned> lines;
    void Talk(unsigned line){lines.push_back(line);}
AVERY_UPDATE
};
void check(bool ok){if(!ok)throw std::runtime_error("Gilneas quest regression failed");}
int main(){
    Player owner;owner.player=&owner;Creature dog,target;dog.entry=35631;dog.player=&owner;target.entry=35463;
    CharmInfo charm;dog.charm=&charm;
    for(int status:{QUEST_STATUS_NONE,QUEST_STATUS_COMPLETE,QUEST_STATUS_REWARDED}){
        owner.quest=status;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==0&&target.stealth);
    }
    owner.quest=QUEST_STATUS_INCOMPLETE;StartGilneasMastiffAttack(&dog,&target);
    Command command;command.caster=&dog;check(command.CheckTarget()==SPELL_CAST_OK);
    owner.quest=QUEST_STATUS_NONE;check(command.CheckTarget()==SPELL_FAILED_BAD_TARGETS);
    owner.quest=QUEST_STATUS_INCOMPLETE;command.caster=&owner;check(command.CheckTarget()==SPELL_FAILED_BAD_TARGETS);
    check(!target.stealth&&dog.ai.victim==&target&&target.ai.victim==&dog);
    check(charm.commandAttack&&!charm.following&&!charm.returning&&!charm.stay&&!charm.commandFollow);
    unsigned attacks=dog.ai.attacks;target.alive=false;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);
    target.alive=true;target.entry=1;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);
    target.entry=35463;dog.player=nullptr;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);dog.player=&owner;
    dog.samePhase=false;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);dog.samePhase=true;
    dog.sameMap=false;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);dog.sameMap=true;
    dog.alive=false;StartGilneasMastiffAttack(&dog,&target);check(dog.ai.attacks==attacks);dog.alive=true;
    Creature jumping;jumping.entry=35631;jumping.player=&owner;jumping.charm=&charm;
    jumping.motion.type=EFFECT_MOTION_TYPE;owner.quest=QUEST_STATUS_INCOMPLETE;
    StartGilneasMastiffAttack(&jumping,&target);
    check(jumping.GetVictim()==&target&&jumping.motion.type==EFFECT_MOTION_TYPE&&jumping.ai.attacks==0);
    EffectMovementGenerator effect;effect.Finalize(&jumping);
    check(jumping.motion.type==CHASE_MOTION_TYPE&&jumping.motion.target==&target&&jumping.motion.chases==1);
    Creature enemy;Lurker lurker(&enemy);uint32 dmg=1;
    owner.quest=QUEST_STATUS_NONE;lurker.DamageTaken(&owner,dmg);check(enemy.ai.attacks==0);
    owner.quest=QUEST_STATUS_INCOMPLETE;lurker.DamageTaken(&dog,dmg);check(enemy.ai.victim==&dog&&dmg==1);
    Quest stocks{14375,68639};King king;Player player;player.quest=QUEST_STATUS_REWARDED;
    for(int aura:{69196,42716,50220,58284,68630})player.auras[aura]={};
    check(king.OnQuestReward(&player,nullptr,&stocks,0));check(!player.HasAura(68481));
    check(player.flags==0x100&&!player.HasAura(69196)&&!player.HasAura(42716));
    check(player.HasAura(94053)&&player.GetAura(94053)->duration==3000&&!player.HasAura(68481));
    player.m_Events.Update(2999);check(!player.HasAura(68481)&&player.HasAura(94053));
    player.m_Events.Update(1);check(player.HasAura(68481)&&!player.HasAura(94053));
    auto casts=player.casts.size();player.m_Events.Update(10000);check(player.casts.size()==casts);
    Player cancelled;cancelled.quest=QUEST_STATUS_REWARDED;
    king.OnQuestReward(&cancelled,nullptr,&stocks,0);cancelled.m_Events.KillAllEvents(false);
    cancelled.m_Events.Update(3000);check(!cancelled.HasAura(68481));
    Player moved;moved.quest=QUEST_STATUS_REWARDED;
    king.OnQuestReward(&moved,nullptr,&stocks,0);moved.map=1;
    moved.m_Events.Update(3000);check(!moved.HasAura(68481));
    Player abandoned;abandoned.quest=QUEST_STATUS_REWARDED;
    king.OnQuestReward(&abandoned,nullptr,&stocks,0);abandoned.quest=QUEST_STATUS_NONE;
    abandoned.m_Events.Update(3000);check(!abandoned.HasAura(68481));
    {Player destroyed;destroyed.quest=QUEST_STATUS_REWARDED;king.OnQuestReward(&destroyed,nullptr,&stocks,0);}

    Player login;login.quest=QUEST_STATUS_REWARDED;login.auras[69196]={};Recovery recovery;
    recovery.OnLogin(&login,false);check(login.HasAura(68481)&&!login.HasAura(69196)&&login.flags==0x100);
    Player partial;partial.quest=QUEST_STATUS_REWARDED;partial.auras[42716]={};
    recovery.OnLogin(&partial,false);check(!partial.HasAura(42716)&&partial.flags==0x100&&partial.HasAura(68481));
    Player progressed;progressed.quest=QUEST_STATUS_REWARDED;progressed.nextQuest=QUEST_STATUS_REWARDED;
    recovery.OnLogin(&progressed,false);check(progressed.casts.empty()&&progressed.flags==(UNIT_FLAG2_DISABLE_TURN|0x100));
    Player unrelated;unrelated.quest=QUEST_STATUS_NONE;unrelated.auras[69196]={};recovery.OnLogin(&unrelated,false);
    check(unrelated.HasAura(69196)&&unrelated.casts.empty());
    AveryDialogue dialogue;dialogue.m_events.ScheduleEvent(dialogue.EVENT_SAY_JOSIAH_AVERY_TEXT_00,10s);
    for(uint32 delta:{10000,30000,25000,30000,25000,30000})dialogue.UpdateAI(delta);
    check(dialogue.lines==std::vector<unsigned>({0,1,2,3,4,5}));
    dialogue.UpdateAI(25000);check(dialogue.lines.back()==0&&dialogue.lines.size()==7);
    TempSummon oldAvery;oldAvery.Update(1);check(oldAvery.removed);
    TempSummon sceneAvery;KeepGilneasAveryForScene(&sceneAvery);
    sceneAvery.Update(1000);check(!sceneAvery.removed&&sceneAvery.corpseDelay==10&&sceneAvery.despawnMs==30000);
    sceneAvery.m_deathState=DEAD;sceneAvery.Update(1);check(sceneAvery.removed);
    Creature ordinary;KeepGilneasAveryForScene(&ordinary);check(ordinary.corpseDelay==0&&ordinary.despawnMs==0);
    Avery avery;Creature giver;Quest arsenal{14159,67352};
    avery.OnQuestReward(&owner,&giver,&arsenal,0);check(giver.bites==1&&giver.casts.empty());
    arsenal.reward=0;avery.OnQuestReward(&owner,&giver,&arsenal,0);check(giver.casts.size()==1&&giver.casts[0]==67352);
    std::cout<<"PASS: actual Gilneas quest gates, mastiff command, stocks release/3s transition/relogin, Avery single summon fallback\n";
}
'''
    for token,value in {'HELPERS':helpers,'ATTACK':attack,'DAMAGE':damage,
        'CHECKCAST':method(command,'        SpellCastResult CheckTarget('),
        'AVERY_LIFETIME':method(city,'    void KeepGilneasAveryForScene('),
        'TEMP_SUMMON_UPDATE':method((root/'src/server/game/Entities/Creature/TemporarySummon.cpp').read_text('utf8'),'void TempSummon::Update(').replace('TempSummon::',''),
        'EFFECT_FINALIZE':method((root/'src/server/game/Movement/MovementGenerators/PointMovementGenerator.cpp').read_text('utf8'),'void EffectMovementGenerator::Finalize(').replace('EffectMovementGenerator::',''),
        'STOCKS_EVENT':method(dusk,'    class GilneasStocksTransitionEvent final')+';',
        'STOCKS':method(dusk,'    void ReleaseGilneasStocks('),
        'KING':method(king,'    bool OnQuestReward('),
        'RECOVERY':method(recovery,'    void OnLogin('),
        'EVENT_EXECUTE':method(event_source,'uint32 EventMap::ExecuteEvent(').replace('EventMap::',''),
        'AVERY_EVENTS':method(avery,'    enum eNpc')+';',
        'AVERY_UPDATE':method(avery,'        void UpdateAI('),
        'AVERY':method(avery,'    bool OnQuestReward(')}.items():
        harness=harness.replace('\n'+token+'\n','\n'+value+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        processor=root/'src/common/Utilities/EventProcessor.cpp'
        (Path(tmp)/'Define.h').write_text('#pragma once\n#include <cstdint>\n#include <mutex>\nusing uint8=std::uint8_t;using uint32=std::uint32_t;using uint64=std::uint64_t;\n#define TC_COMMON_API\n',encoding='utf8')
        (Path(tmp)/'Errors.h').write_text('#pragma once\n#include <cassert>\n#define ASSERT(value) assert(value)\n',encoding='utf8')
        cpp=Path(tmp)/'gilneas.cpp';exe=Path(tmp)/'gilneas';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=undefined',
            '-fno-omit-frame-pointer','-g','-pthread','-I',tmp,'-I',str(processor.parent),str(cpp),str(processor),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
