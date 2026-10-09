#!/usr/bin/env python3
"""Compile actual scenario condition54, its loader/mask, and untouched charm44."""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def case(text,name,start=0,block=True):
    pos=text.index('        case '+name+':',start)
    if not block:
        end=text.index('            break;',pos)+len('            break;');return text[pos:end]
    opening=text.index('{',pos);end=opening+1;depth=1
    while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[pos:end]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compiler',default=os.environ.get('CXX','c++'));parser.add_argument('--no-sanitizers',action='store_true');a=parser.parse_args()
    text=(ROOT/'src/server/game/Conditions/ConditionMgr.cpp').read_text('utf8');header=(ROOT/'src/server/game/Conditions/ConditionMgr.h').read_text('utf8')
    assert re.search(r'CONDITION_CHARMED\s*=\s*44',header) and re.search(r'CONDITION_SCENARIO_STEP\s*=\s*54',header)
    assert '{ "Scenario step",        true, true,  false },' in text
    evaluate=case(text,'CONDITION_SCENARIO_STEP');charm=case(text,'CONDITION_CHARMED');mask=case(text,'CONDITION_SCENARIO_STEP',text.index('uint32 Condition::GetSearcherTypeMaskForCondition()'),False)
    validate=case(text,'CONDITION_SCENARIO_STEP',text.index('bool ConditionMgr::isConditionTypeValid('))
    code=r'''
#include <cstdint>
#include <vector>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;
constexpr uint32 CONDITION_SCENARIO_STEP=54,CONDITION_CHARMED=44,GRID_MAP_TYPE_MASK_PLAYER=2;
struct ScenarioEntry {uint32 ID;};
struct ScenarioStepEntry {uint32 ScenarioID,OrderIndex;bool bonus=false;bool IsBonusObjective()const{return bonus;}};
struct Scenario {ScenarioEntry const* entry;ScenarioStepEntry const* step;ScenarioEntry const* GetEntry(){return entry;}ScenarioStepEntry const* GetStep(){return step;}};
struct Player;struct Unit;
struct WorldObject {virtual ~WorldObject()=default;virtual Player* ToPlayer(){return nullptr;}virtual Unit* ToUnit(){return nullptr;}};
struct Unit:WorldObject {bool charmed=false;Unit* ToUnit()override{return this;}bool IsCharmed(){return charmed;}};
struct Player:Unit {Scenario* scenario=nullptr;Player* ToPlayer()override{return this;}Scenario* GetScenario(){return scenario;}};
struct Condition {uint32 ConditionType=54,ConditionValue1=962,ConditionValue2=0,ConditionValue3=0;};
ScenarioEntry entry{962};ScenarioStepEntry first{962,0},next{962,1},bonus{962,2,true},foreign{963,0};
struct Store {ScenarioEntry const* LookupEntry(uint32 id){return id==962?&entry:nullptr;}} sScenarioStore;
std::vector<ScenarioStepEntry const*> sScenarioStepStore{&first,&next,&bonus};
#define TC_LOG_ERROR(...) ((void)0)
bool valid(Condition* cond){switch(cond->ConditionType){@@VALIDATE@@ default:return false;}return true;}
bool meets(WorldObject* object,uint32 type,uint32 ConditionValue1,uint32 ConditionValue2){bool condMeets=false;switch(type){@@EVALUATE@@ @@CHARM@@ default:break;}return condMeets;}
uint32 mask(uint32 type){uint32 mask=0;switch(type){@@MASK@@ default:break;}return mask;}
void check(bool ok,char const* why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 Condition condition;check(valid(&condition),"valid first step including zero order");
 Player player,other;Unit npc;Scenario scenario{&entry,&first};player.scenario=&scenario;
 check(meets(&player,54,962,0),"matching own active main step");
 check(!meets(&other,54,962,0)&&!meets(&npc,54,962,0),"no scenario and non-player fail closed");
 check(!meets(&player,54,963,0)&&!meets(&player,54,962,1),"wrong scenario/order");
 scenario.step=&next;check(meets(&player,54,962,1)&&!meets(&player,54,962,0),"step transition changes condition");
 scenario.step=&foreign;check(!meets(&player,54,962,0),"inconsistent scenario step");
 scenario.step=nullptr;check(!meets(&player,54,962,0),"completed/null step");scenario.step=&first;
 scenario.entry=nullptr;check(!meets(&player,54,962,0),"missing scenario entry");scenario.entry=&entry;
 scenario.step=&bonus;check(!meets(&player,54,962,2),"bonus not current main step");
 condition.ConditionValue1=963;check(!valid(&condition),"unknown scenario");condition.ConditionValue1=962;
 condition.ConditionValue2=99;check(!valid(&condition),"unknown step");condition.ConditionValue2=2;check(!valid(&condition),"bonus step rejected at load");condition.ConditionValue2=0;
 condition.ConditionValue3=1;check(!valid(&condition),"unused parameter rejected");
 check(mask(54)==GRID_MAP_TYPE_MASK_PLAYER,"search mask stays player-only");
 npc.charmed=true;check(meets(&npc,44,0,0),"legacy charm44 untouched");npc.charmed=false;check(!meets(&npc,44,0,0),"legacy non-charmed");
 std::cout<<"PASS: actual scenario54 evaluator, loader and search mask; own scenario/step, absent/completed/bonus/foreign data rejected; legacy charm44 unchanged\n";
}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('@@VALIDATE@@',validate).replace('@@EVALUATE@@',evaluate).replace('@@CHARM@@',charm).replace('@@MASK@@',mask)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp);cpp=path/'condition.cpp';cpp.write_text(code);exe=path/'condition.exe';flags=['-std=c++17','-Wall','-Wextra','-Werror']
        if not a.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([a.compiler,*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
