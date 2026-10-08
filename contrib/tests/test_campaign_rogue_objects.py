#!/usr/bin/env python3
"""Compile real restored GO AI and native loot-state dispatch with source fixtures."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    text=(root/'src/server/scripts/World/go_scripts.cpp').read_text('utf8')
    ai=re.search(r'struct go_campaign_rogue_interaction : public GameObjectAI\n\{.*?^\};',text,re.M|re.S)[0]
    assert text.count('RegisterGameObjectAI(go_campaign_rogue_interaction);')==1
    registry=json.loads((root/'docs/audit-data/campaign-rogue-object-restoration.json').read_text('utf8'))
    source={int(row['entryorguid']):row for row in registry['source_smart_rows']}
    assert len(source)==2
    assert [int(source[252017][k]) for k in ('event_type','action_type','action_param1','target_type')]==[64,33,110470,7]
    assert [int(source[267041][k]) for k in ('event_type','event_param1','action_type','action_param1','target_type')]==[70,2,206,4269,7]
    original=(root/'src/server/game/Entities/GameObject/GameObject.cpp').read_text('utf8')
    start=original.index('void GameObject::SetLootState(');opening=original.index('{',start);end=opening+1;depth=1
    while depth:depth+=(original[end]=='{')-(original[end]=='}');end+=1
    dispatch=original[start:end]
    code=r'''
#include <cstdint>
#include <vector>
#include <unordered_set>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
enum LootState{GO_NOT_READY,GO_READY,GO_ACTIVATED,GO_JUST_DEACTIVATED};
constexpr uint32 GAMEOBJECT_TYPE_DOOR=0,GO_STATE_READY=1;
void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
struct Map{};struct Position{};struct Guid{void Clear(){}};struct Player;
struct Unit{virtual Player* ToPlayer(){return nullptr;}Guid GetGUID(){return {};}};
struct Player:Unit,Position{Map* map;uint32 guid;std::vector<uint32> credits;
 Player(Map* m,uint32 g):map(m),guid(g){}Player* ToPlayer()override{return this;}
 Map* GetMap(){return map;}uint32 GetGUID(){return guid;}void KilledMonsterCredit(uint32 id){credits.push_back(id);}};
struct GameObjectAI;
struct GameObject{uint32 entry;Map* map;GameObjectAI* ai=nullptr;LootState m_lootState=GO_READY;Guid m_lootStateUnitGUID{};bool m_model=false;
 uint32 GetEntry(){return entry;}Map* GetMap(){return map;}uint32 GetGoType(){return 10;}uint32 GetGoState(){return GO_STATE_READY;}
 void EnableCollision(bool){}GameObjectAI* AI(){return ai;}void SetLootState(LootState,Unit*);};
struct GameObjectAI{protected:GameObject* go;public:explicit GameObjectAI(GameObject* object):go(object){}virtual ~GameObjectAI()=default;
 virtual bool GossipHello(Player*,bool){return false;}virtual void OnStateChanged(uint32,Unit*){}};
struct ScriptMgr{void OnGameObjectLootStateChanged(GameObject*,uint32,Unit*){}} manager;auto* sScriptMgr=&manager;
struct Conversation{struct Call{uint32 id;Player* creator;Position const* position;std::unordered_set<uint32> participants;};
 static inline std::vector<Call> calls;static inline bool fail=false;
 static Conversation* CreateConversation(uint32 id,Player* p,Position const& pos,std::unordered_set<uint32>&& participants){
 calls.push_back({id,p,&pos,std::move(participants)});static Conversation result;return fail?nullptr:&result;}};
AI
DISPATCH
int main(){
 Map map,other;Player first(&map,1),second(&map,2),foreign(&other,3);Unit npc;
 GameObject eye{252017,&map},powder{267041,&map},unrelated{123,&map};
 go_campaign_rogue_interaction eyeAI(&eye),powderAI(&powder),unrelatedAI(&unrelated);eye.ai=&eyeAI;powder.ai=&powderAI;unrelated.ai=&unrelatedAI;
 check(!eyeAI.GossipHello(nullptr,true)&&!eyeAI.GossipHello(&foreign,true),"invalid use intercepted");
 check(foreign.credits.empty(),"foreign map received credit");
 check(!eyeAI.GossipHello(&first,true)&&!eyeAI.GossipHello(&second,false),"native GOOBER use suppressed");
 check(first.credits==std::vector<uint32>{110470}&&second.credits==first.credits,"source credit/invoker changed");
 eyeAI.GossipHello(&first,true);check(first.credits.size()==2,"source repeatable event suppressed");
 powderAI.GossipHello(&first,true);unrelatedAI.GossipHello(&first,true);check(first.credits.size()==2,"other object received eye credit");
 for(auto state:{GO_READY,GO_NOT_READY,GO_JUST_DEACTIVATED})powder.SetLootState(state,&first);
 powder.SetLootState(GO_ACTIVATED,nullptr);powder.SetLootState(GO_ACTIVATED,&npc);powder.SetLootState(GO_ACTIVATED,&foreign);
 unrelated.SetLootState(GO_ACTIVATED,&first);eye.SetLootState(GO_ACTIVATED,&first);check(Conversation::calls.empty(),"invalid activation created conversation");
 powder.SetLootState(GO_ACTIVATED,&first);powder.SetLootState(GO_READY,&second);powder.SetLootState(GO_ACTIVATED,&second);
 check(Conversation::calls.size()==2,"native activation dispatch lost");
 for(std::size_t i=0;i<2;++i){auto const& c=Conversation::calls[i];auto* p=i?&second:&first;
 check(c.id==4269&&c.creator==p&&c.position==static_cast<Position*>(p)&&c.participants==std::unordered_set<uint32>{p->guid},"personal creator, position or participants changed");}
 Conversation::fail=true;powder.SetLootState(GO_ACTIVATED,&first);check(Conversation::calls.size()==3,"failed creation disrupted repeatable activation");
 std::cout<<"PASS: actual source credit/invoker, ordinary use, native activation dispatch, personal participants, map isolation and failed conversation creation\n";
}
'''.replace('\nAI\n','\n'+ai+'\n').replace('\nDISPATCH\n','\n'+dispatch+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'rogue.cpp';exe=Path(tmp)/'rogue';cpp.write_text(code,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
