#!/usr/bin/env python3
"""Actual object AI, player criteria routing, scenario gate and loot-state callback."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    script=(root/'src/server/scripts/World/go_scripts.cpp').read_text('utf8')
    ai=re.search(r'struct go_campaign_scenario_interaction : public GameObjectAI\n\{.*?^\};',script,re.M|re.S)[0]
    assert script.count('RegisterGameObjectAI(go_campaign_scenario_interaction);')==1
    def method(path,signature):
        source=(root/path).read_text('utf8');start=source.index(signature);opening=source.index('{',start);end=opening+1;depth=1
        while depth:depth+=(source[end]=='{')-(source[end]=='}');end+=1
        return source[start:end]
    route=method('src/server/game/Entities/Player/Player.cpp','void Player::UpdateCriteria(')
    gate=method('src/server/game/Scenarios/Scenario.cpp','bool Scenario::CanUpdateCriteriaTree(')
    dispatch=method('src/server/game/Entities/GameObject/GameObject.cpp','void GameObject::SetLootState(')
    group=method('src/server/game/Achievements/CriteriaHandler.h','static bool IsGroupCriteriaType(')
    enums=(root/'src/server/game/DataStores/DBCEnums.h').read_text('utf8')
    assert re.search(r'CRITERIA_TYPE_SEND_EVENT_SCENARIO\s*= 92',enums)
    code=r'''
#include <cstdint>
#include <stdexcept>
#include <vector>
#include <iostream>
using uint32=std::uint32_t;using uint64=std::uint64_t;
enum CriteriaTypes{CRITERIA_TYPE_SEND_EVENT_SCENARIO=92,CRITERIA_TYPE_KILL_CREATURE=0,CRITERIA_TYPE_WIN_BG=1,CRITERIA_TYPE_BE_SPELL_TARGET=2,CRITERIA_TYPE_WIN_RATED_ARENA=3,CRITERIA_TYPE_BE_SPELL_TARGET2=4,CRITERIA_TYPE_WIN_RATED_BATTLEGROUND=5};
enum LootState{GO_NOT_READY=0,GO_READY=1,GO_ACTIVATED=2,GO_JUST_DEACTIVATED=3};
constexpr uint32 GAMEOBJECT_TYPE_DOOR=0,GO_STATE_READY=1;
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
struct Map{uint32 id;};struct Player;struct Scenario;
struct Guid{bool empty=false;void Clear(){empty=true;}};
struct Unit{virtual Player* ToPlayer(){return nullptr;}Guid GetGUID(){return {};}};
struct Call{CriteriaTypes type;uint64 event,second,third;Unit* invoker;Player* reference;};
struct Tracker{std::vector<Call> calls;void UpdateCriteria(CriteriaTypes t,uint64 a,uint64 b,uint64 c,Unit* u,Player* p){calls.push_back({t,a,b,c,u,p});}};
struct Guild:Tracker{};struct GuildMgr{Guild* GetGuildById(uint32){return nullptr;}} guildMgr;GuildMgr* sGuildMgr=&guildMgr;
struct CriteriaMgr{GROUP};
struct Criteria{};struct ScenarioEntry{uint32 ID;};struct ScenarioData{ScenarioEntry* Entry;};
struct ScenarioStepEntry{uint32 ScenarioID;bool bonus=false;bool IsBonusObjective()const{return bonus;}};
struct CriteriaTree{ScenarioStepEntry const* ScenarioStep;};
struct Scenario:Tracker{ScenarioData const* _data;ScenarioStepEntry const* current;
 Scenario(ScenarioData const* data,ScenarioStepEntry const* step):_data(data),current(step){}
 ScenarioStepEntry const* GetStep()const{return current;}
 bool CanUpdateCriteriaTree(Criteria const*,CriteriaTree const*,Player*)const;};
struct Player:Unit{Map* map;Scenario* scenario;Tracker achievement,quest;
 Tracker* m_achievementMgr=&achievement;Tracker* m_questObjectiveCriteriaMgr=&quest;
 Player(Map* m,Scenario* s):map(m),scenario(s){}
 Player* ToPlayer()override{return this;}Map* GetMap(){return map;}Scenario* GetScenario(){return scenario;}
 uint32 GetGuildId(){return 0;}void UpdateCriteria(CriteriaTypes,uint64,uint64,uint64,Unit*);};
struct GameObjectAI;
struct GameObject{uint32 entry;Map* map;GameObjectAI* ai=nullptr;LootState m_lootState=GO_READY;Guid m_lootStateUnitGUID{};bool m_model=false;
 uint32 GetEntry(){return entry;}uint32 GetMapId(){return map->id;}Map* GetMap(){return map;}
 uint32 GetGoType(){return entry==251591?GAMEOBJECT_TYPE_DOOR:10;}uint32 GetGoState(){return GO_STATE_READY;}
 void EnableCollision(bool){}GameObjectAI* AI(){return ai;}void SetLootState(LootState,Unit*);};
struct GameObjectAI{protected:GameObject* go;public:explicit GameObjectAI(GameObject* g):go(g){}virtual ~GameObjectAI()=default;
 virtual void Reset(){}virtual bool GossipHello(Player*,bool){return false;}virtual void OnStateChanged(uint32,Unit*){}};
struct ScriptMgr{void OnGameObjectLootStateChanged(GameObject*,uint32,Unit*){}} scriptMgr;ScriptMgr* sScriptMgr=&scriptMgr;
AI
ROUTE
GATE
DISPATCH
int main(){
 Map monastery{1625},mage{1583},elsewhere{1},otherInstance{1625};
 ScenarioEntry entry{100};ScenarioData data{&entry};ScenarioStepEntry current{100,false},later{100,false},other{101,false},bonus{100,true};
 Scenario scenario(&data,&current);Player p(&monastery,&scenario),second(&monastery,&scenario),absent(&monastery,nullptr),foreign(&otherInstance,&scenario);
 GameObject door{251591,&monastery};go_campaign_scenario_interaction doorAI(&door);door.ai=&doorAI;
 check(!doorAI.GossipHello(nullptr,true)&&!doorAI.GossipHello(&absent,true)&&!doorAI.GossipHello(&foreign,true),"invalid invoker intercepted object use");
 check(scenario.calls.empty(),"invalid invoker credited");
 check(!doorAI.GossipHello(&p,true),"door handler suppresses native opening");
 check(scenario.calls.size()==1&&p.achievement.calls.size()==1&&p.quest.calls.size()==1,"native player routing missing");
 auto call=scenario.calls.back();check(call.type==CRITERIA_TYPE_SEND_EVENT_SCENARIO&&call.event==52452&&call.second==0&&call.third==0&&call.invoker==&p&&call.reference==&p,"source door arguments changed");
 doorAI.GossipHello(&p,true);doorAI.GossipHello(&second,false);check(scenario.calls.size()==1,"source once-per-object flag lost");
 doorAI.Reset();doorAI.GossipHello(&second,true);check(scenario.calls.size()==2&&scenario.calls.back().reference==&second,"reset or caller routing wrong");
 door.map=&elsewhere;doorAI.Reset();doorAI.GossipHello(&p,true);check(scenario.calls.size()==2,"wrong map credited");
 GameObject scroll{254253,&mage};go_campaign_scenario_interaction scrollAI(&scroll);scroll.ai=&scrollAI;Player reader(&mage,&scenario);Unit npc;
 scroll.SetLootState(GO_READY,&reader);scroll.SetLootState(GO_JUST_DEACTIVATED,&reader);scroll.SetLootState(GO_ACTIVATED,nullptr);scroll.SetLootState(GO_ACTIVATED,&npc);
 check(scenario.calls.size()==2,"wrong state or non-player credited");
 check(!scrollAI.GossipHello(&reader,true),"scroll handler consumes native use");check(scenario.calls.size()==2,"scroll credited before activation");
 scroll.SetLootState(GO_ACTIVATED,&reader);check(scenario.calls.size()==3&&scenario.calls.back().event==54147&&scenario.calls.back().reference==&reader,"native state callback not credited");
 scroll.SetLootState(GO_READY,&reader);scroll.SetLootState(GO_ACTIVATED,&reader);check(scenario.calls.size()==4,"repeatable source scroll reaction lost");
 GameObject unrelated{123,&mage};go_campaign_scenario_interaction unrelatedAI(&unrelated);unrelated.ai=&unrelatedAI;unrelated.SetLootState(GO_ACTIVATED,&reader);unrelatedAI.GossipHello(&reader,true);check(scenario.calls.size()==4,"unrelated object affected");
 CriteriaTree active{&current},future{&later},different{&other},extra{&bonus},missing{nullptr};
 check(scenario.CanUpdateCriteriaTree(nullptr,&active,&p)&&!scenario.CanUpdateCriteriaTree(nullptr,&future,&p)&&!scenario.CanUpdateCriteriaTree(nullptr,&different,&p)&&!scenario.CanUpdateCriteriaTree(nullptr,&missing,&p),"native scenario current-step gate changed");
 check(scenario.CanUpdateCriteriaTree(nullptr,&extra,&p),"native bonus gate changed");scenario.current=nullptr;check(!scenario.CanUpdateCriteriaTree(nullptr,&active,&p),"missing step accepted");
 std::cout<<"PASS: actual source object reactions, native criteria routing, activation callback, one-shot/reset, invoker/map isolation and scenario step gate\n";
}
'''
    for key,value in [('GROUP',group),('AI',ai),('ROUTE',route),('GATE',gate),('DISPATCH',dispatch)]:
        code=code.replace('\n'+key+'\n','\n'+value+'\n') if key!='GROUP' else code.replace('{GROUP}','{'+value+'}')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'scenario.cpp';exe=Path(tmp)/'scenario';cpp.write_text(code,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
