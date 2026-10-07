#!/usr/bin/env python3
"""Native AI reuse on respawn: seven Initialize/Reset/owned-cleanup handlers."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
from test_gilneas_quests import method


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    native=(root/'src/server/game/Entities/Creature/Creature.cpp').read_text('utf8')
    respawn=method(native,'void Creature::Respawn(')
    assert 'AI()->Reset();' in respawn,'Fixture must model reuse of the existing AI'
    sections=re.split(r'    struct (npc_\w+AI) : public ScriptedAI',source)
    classes=[];checks=[]
    for index in range(1,len(sections),2):
        name,body=sections[index:index+2]
        if 'case EVENT_GLOBAL_RESET:' not in body or name=='npc_krennan_aranas_38553AI':continue
        members=body[body.index('        EventMap m_events;'):body.index('        void Initialize()')]
        methods='\n'.join(method(body,'        void '+n+'(') for n in ('Initialize','Reset','RemoveMyMember'))
        classes.append('struct '+name+':BaseAI{'+members+'\n'+methods+'\nvoid SummonMyMember(){++summons;my_followerList.push_back(10+summons);}};')
        dirty=[];clean=[]
        for field in re.findall(r'ObjectGuid\s+(\w+)',members):
            dirty.append('ai.'+field+'=99;');clean.append('!ai.'+field)
        for field in ['m_isInitialised','m_battleIsStarted','m_doneA','m_doneB','m_cinematicStarted','m_liamDeathQueued','m_completionHandled']:
            if field in members:dirty.append('ai.'+field+'=true;');clean.append('!ai.'+field)
        for field in ['m_wave','m_waveSize','m_point','m_ai_counter','m_arrivedMask','m_ridingWorgen']:
            if re.search(r'\b'+field+r'\b',members):dirty.append('ai.'+field+'=99;');clean.append('ai.'+field+'==0')
        if 'm_targetList' in members:
            dirty+=['ai.m_targetList.push_back(&foreign);','ai.m_nearestTarget=&foreign;','ai.m_nearestDistance=99;','ai.m_checkDistance=99;']
            clean+=['ai.m_targetList.empty()','!ai.m_nearestTarget','ai.m_nearestDistance==0','ai.m_checkDistance==0']
        if 'm_shootCoolDown' in members:clean.append('ai.m_shootCoolDown==4000')
        victims='ai.my_victimList.push_back(3);' if 'my_victimList' in members else ''
        victim_check='victim.despawns==1&&ai.my_victimList.empty()' if victims else 'victim.despawns==0'
        checks.append('''{
 Creature owner,first,second,victim,foreign;actors={{1,&first},{2,&second},{3,&victim},{4,&foreign}};
 NAME ai;ai.me=&owner;ai.Initialize();ai.my_followerList={1,2};VICTIMS
 DIRTY ai.m_events.ScheduleEvent(EVENT_GLOBAL_RESET,1);ai.m_events.ScheduleEvent(EVENT_FIGHT_WAVE,1);ai.m_events.ScheduleEvent(EVENT_SYLVANAS_ATTACK1,1);
 ai.Reset();check(CLEAN,"respawn clears every stale registration, wave, target and cinematic latch");
 check(first.despawns==1&&second.despawns==1&&VICTIM_CHECK&&!foreign.despawns,"native owned cleanup leaves unrelated actor intact");
 check(ai.summons==1&&ai.my_followerList.size()==1&&ai.m_events.timers.count(EVENT_INITIALISE),"one fresh member group and pending registration after reset");
 check(!ai.m_events.timers.count(EVENT_GLOBAL_RESET)&&!ai.m_events.timers.count(EVENT_FIGHT_WAVE)&&!ai.m_events.timers.count(EVENT_SYLVANAS_ATTACK1),"old timeout/combat/cinematic queue cannot survive respawn");
 DIRTY ai.Reset();check(CLEAN&&ai.summons==2&&ai.my_followerList.size()==1,"second reset reuses the same AI without stale fields or accumulated groups");
}
'''.replace('NAME',name).replace('VICTIMS',victims).replace('DIRTY',''.join(dirty)).replace('check(CLEAN,', ''.join('check('+condition+',"'+name+' '+condition+'");' for condition in clean)+'check(CLEAN,').replace('CLEAN','&&'.join(clean)).replace('VICTIM_CHECK',victim_check))
    assert len(classes)==7
    king=source[source.index('class npc_king_genn_greymane_38470 :'):source.index('class npc_lady_sylvanas_windrunner_38469 :')]
    code=r'''
#include <cstdint>
#include <list>
#include <map>
#include <set>
#include <string>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;
NATIVE_ENUM;
constexpr int REACT_PASSIVE=0,MOVE_RUN=1;
struct ObjectGuid{int value=0;ObjectGuid()=default;ObjectGuid(int v):value(v){};explicit operator bool()const{return value!=0;}bool operator==(ObjectGuid o)const{return value==o.value;}bool operator!=(ObjectGuid o)const{return value!=o.value;}static ObjectGuid Empty;};ObjectGuid ObjectGuid::Empty{};
struct Unit{};
struct AI{virtual~AI()=default;virtual ObjectGuid GetGUID(int32)const{return {};}int talks=0;void Talk(int){++talks;}};
struct Creature:Unit{ObjectGuid guid;bool alive=true,phase=true;uint32 entry=0,map=654,script=7;int despawns=0;std::set<int>auras;struct AI*ai=nullptr;
 bool IsAlive()const{return alive;}uint32 GetEntry()const{return entry;}uint32 GetMapId()const{return map;}uint32 GetScriptId()const{return script;}bool IsInPhase(Creature*c)const{return phase&&c->phase;}struct AI*AI(){return ai;}
 void DespawnOrUnsummon(int){++despawns;}void SetReactState(int){}void setActive(bool){}bool HasAura(int id){return auras.count(id);}void AddAura(int id,Creature*){auras.insert(id);}void SetSpeed(int,float){}
};
std::map<int,Creature*>actors;namespace ObjectAccessor{Creature*GetCreature(Creature&context,ObjectGuid guid){auto i=actors.find(guid.value);return i==actors.end()||i->second->map!=context.map?nullptr:i->second;}}
struct Manager{uint32 GetScriptId(char const*){return 7;}}manager;auto*sObjectMgr=&manager;
ROLE_SCRIPT
ROLE_LOOKUP
struct EventMap{std::map<uint32,uint32>timers;void Reset(){timers.clear();}void ScheduleEvent(uint32 id,uint32 delay){timers[id]=delay;}void RescheduleEvent(uint32 id,uint32 delay){timers[id]=delay;}};
struct BaseAI:AI{Creature*me=nullptr;int summons=0;virtual void Reset(){}};
PRODUCTION_CLASSES
struct LinkedController:AI{ObjectGuid cinematic;ObjectGuid GetGUID(int32)const override{return cinematic;}};
struct King:AI{Creature*me=nullptr;ObjectGuid m_almyraGUID,m_liam2GUID;EventMap m_events;
 KING_REFRESH
 void FirstTalk(){switch(int(EVENT_LIAM_DEATH_TALK1)){KING_FIRST}}
 void SecondTalk(){switch(int(EVENT_LIAM_DEATH_TALK2)){KING_SECOND}}
};
void check(bool ok,char const*message){if(!ok)throw std::runtime_error(message);}
int main(){try{
 PRODUCTION_CHECKS
 {Creature king,almyra,oldLiam,newLiam;AI oldAI,newAI;LinkedController controller;King ai;ai.me=&king;ai.m_almyraGUID=1;ai.m_liam2GUID=2;almyra.entry=NPC_SISTER_ALMYRA;almyra.ai=&controller;oldLiam.ai=&oldAI;newLiam.ai=&newAI;newLiam.alive=false;actors={{1,&almyra},{2,&oldLiam},{3,&newLiam}};controller.cinematic=3;
  ai.FirstTalk();ai.SecondTalk();check(!oldAI.talks&&newAI.talks==2&&ai.m_liam2GUID==ObjectGuid(3),"king's native last words follow new cinematic actor, including corpse dialogue");
  actors.erase(1);ai.FirstTalk();check(newAI.talks==2&&!ai.m_liam2GUID,"lost controller cannot dispatch stale dialogue");
 }
 std::cout<<"Gilneas battle: seven reused AI resets/owned cleanups and fresh cinematic Liam dialogue PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
    values={'NATIVE_ENUM':method(source,'enum eZoneGilneasCity2'),'ROLE_SCRIPT':method(source,'    char const* GetGilneasBattleScript('),'ROLE_LOOKUP':method(source,'    Creature* GetGilneasBattleActor('),'PRODUCTION_CLASSES':'\n'.join(classes),'PRODUCTION_CHECKS':'\n'.join(checks),'KING_REFRESH':method(king,'        void RefreshCinematicLiam('),'KING_FIRST':method(king,'                case EVENT_LIAM_DEATH_TALK1:'),'KING_SECOND':method(king,'                case EVENT_LIAM_DEATH_TALK2:')}
    for key,value in values.items():code=re.sub(r'\b'+key+r'\b',lambda match:value,code)
    with tempfile.TemporaryDirectory(prefix='gilneas-battle-lifecycle-') as folder:
        cpp=Path(folder)/'lifecycle.cpp';exe=Path(folder)/'lifecycle.exe';cpp.write_text(code,'utf8')
        command=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
        if not args.no_sanitizers:command[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
        subprocess.run(command,check=True);subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
