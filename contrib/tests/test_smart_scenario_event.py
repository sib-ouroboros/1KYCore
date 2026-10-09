#!/usr/bin/env python3
"""Compile actual new SmartAI dispatch and validation cases, including legacy205."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]

def case(path,name):
    text=(ROOT/path).read_text('utf8');start=text.index('        case '+name+':');opening=text.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compiler',default=os.environ.get('CXX','c++'));parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    header=(ROOT/'src/server/game/AI/SmartScripts/SmartScriptMgr.h').read_text('utf8')
    values={k:int(v) for k,v in re.findall(r'(SMART_ACTION_\w+)\s*=\s*(\d+)',header)}
    assert values['SMART_ACTION_SEND_EVENT_SCENARIO']==250
    assert (values['SMART_ACTION_SET_OVERRIDE_ZONE_LIGHT'],values['SMART_ACTION_START_CONVERSATION'],values['SMART_ACTION_MODIFY_THREAT'])==(205,206,207)
    dispatch=case('src/server/game/AI/SmartScripts/SmartScript.cpp','SMART_ACTION_SEND_EVENT_SCENARIO')
    light=case('src/server/game/AI/SmartScripts/SmartScript.cpp','SMART_ACTION_SET_OVERRIDE_ZONE_LIGHT')
    validate=case('src/server/game/AI/SmartScripts/SmartScriptMgr.cpp','SMART_ACTION_SEND_EVENT_SCENARIO')
    code=r'''
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr uint32 SMART_ACTION_SEND_EVENT_SCENARIO=250,SMART_ACTION_SET_OVERRIDE_ZONE_LIGHT=205,CRITERIA_TYPE_SEND_EVENT_SCENARIO=92;
struct Player;
struct WorldObject{virtual ~WorldObject()=default;virtual Player* ToPlayer(){return nullptr;}};
struct Unit:WorldObject{};
struct Player:Unit{bool scenario=true;std::vector<uint32> events;Player* ToPlayer()override{return this;}bool GetScenario(){return scenario;}
 void UpdateCriteria(uint32 type,uint32 event,uint32 second,uint32 third,Player* ref){if(type!=92||second||third||ref!=this)throw std::runtime_error("criteria arguments/invoker");events.push_back(event);} };
struct Map {uint32 zone=0,light=0,timer=0;void SetZoneOverrideLight(uint32 z,uint32 l,uint32 t){zone=z;light=l;timer=t;} };
struct Creature:Unit{Map map;Map* GetMap(){return &map;}};
struct Action{uint32 type=250;union{struct{uint32 param1,param2,param3,param4,param5,param6;}raw;struct{uint32 eventId;}sendScenarioEvent;struct{uint32 zoneId,lightId,fadeTime;}setOverrideZoneLight;};Action():raw{}{} };
struct Holder{Action action;uint32 GetActionType()const{return action.type;}};
int living=0;struct ObjectList:std::vector<WorldObject*>{ObjectList(){++living;}~ObjectList(){--living;}};
std::vector<WorldObject*> selected;bool nullTargets=false;
ObjectList* GetTargets(Holder const&,Unit*){if(nullTargets)return nullptr;auto out=new ObjectList;out->assign(selected.begin(),selected.end());return out;}
#define TC_LOG_ERROR(...) ((void)0)
bool valid(Holder const& e){switch(e.GetActionType()){@@VALIDATE@@ default:return false;}return true;}
void dispatch(Holder const& e,Unit* unit,Creature* me){switch(e.GetActionType()){@@DISPATCH@@ @@LIGHT@@ default:break;}}
void check(bool ok,char const* why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 Holder e;Player first,second,outside;outside.scenario=false;Creature npc,source;selected={&first,nullptr,&npc,&outside,&second};
 for(uint32 event:{47152u,47333u,47179u}){e.action.raw.param1=event;check(valid(e),"source scenario event validates");dispatch(e,nullptr,&source);}
 check(first.events==std::vector<uint32>({47152,47333,47179})&&second.events==first.events,"each selected player's own scenario");
 check(outside.events.empty()&&living==0,"non-scenario targets and owned list cleanup");
 selected.clear();dispatch(e,nullptr,nullptr);check(living==0,"empty target cleanup");nullTargets=true;dispatch(e,nullptr,nullptr);nullTargets=false;
 e.action.raw.param1=0;check(!valid(e),"zero event ID rejected");e.action.raw.param1=47152;
 for(uint32* field:{&e.action.raw.param2,&e.action.raw.param3,&e.action.raw.param4,&e.action.raw.param5,&e.action.raw.param6}){*field=1;check(!valid(e),"unused parameters rejected");*field=0;}
 e.action.type=205;e.action.setOverrideZoneLight={12,34,56};dispatch(e,nullptr,&source);
 check(source.map.zone==12&&source.map.light==34&&source.map.timer==56,"legacy205 remains zone lighting");dispatch(e,nullptr,nullptr);
 std::cout<<"PASS: actual SmartAI250 dispatch/validator: three source event assets, player isolation, null/empty/nonplayer targets, cleanup, all reserved parameters; legacy205 unchanged\n";
}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('@@VALIDATE@@',validate).replace('@@DISPATCH@@',dispatch).replace('@@LIGHT@@',light)
    with tempfile.TemporaryDirectory() as path:
        path=Path(path);cpp=path/'smart-event.cpp';cpp.write_text(code);exe=path/'smart-event.exe'
        flags=['-std=c++17','-Wall','-Wextra','-Werror']
        if not args.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([args.compiler,*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
