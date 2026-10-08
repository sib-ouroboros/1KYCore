#!/usr/bin/env python3
"""Compile actual conversation hook and test every verified nearest-actor binding."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler',default=os.environ.get('CXX','c++'))
    p.add_argument('--no-sanitizers',action='store_true')
    a=p.parse_args();root=Path(__file__).resolve().parents[2]
    source=root/'src/server/scripts/World/conversation_scripts.cpp'
    registry=json.loads((root/'docs/audit-data/campaign-nearest-conversation-restoration.json').read_text())
    extra=json.loads((root/'docs/audit-data/campaign-packed-conversation-restoration.json').read_text())
    registry['entries']+=extra['entries'];registry['bindings']+=extra['bindings']
    timing=json.loads((root/'docs/audit-data/campaign-source-timing-conversations.json').read_text())
    registry['entries']+=timing['entries'];registry['bindings']+=timing['bindings']
    fixtures=[]
    for cid in registry['entries']:
        bindings=[b for b in registry['bindings'] if b['ConversationId']==cid]
        setup=''.join(f'creator.creatures[{b["CreatureEntry"]}] = Creature{{{b["CreatureEntry"]}}};' for b in bindings)
        expected=''.join(f'check(scene.actors[{b["Idx"]}].value=={b["CreatureEntry"]},"actor identity/index");' for b in bindings)
        failures=''.join(f'{{ creator.creatures.erase({b["CreatureEntry"]}); scene.actors.clear(); hook.OnConversationCreate(&scene,&creator); check(scene.actors.empty(),"missing actor publishes nothing"); {setup} }}' for b in bindings)
        fixtures.append(f'{{ creator.creatures.clear();creator.searches.clear();Conversation scene{{{cid}}};{setup} hook.OnConversationCreate(&scene,&creator);check(scene.actors.size()=={len(bindings)},"actor count");{expected}for(auto q:creator.searches)check(q.second==creator.GetVisibilityRange(),"source search range");{failures} }}')
    header=r"""
#pragma once
#include <cstdint>
#include <map>
#include <vector>
#include <utility>
using uint32=std::uint32_t;using uint8=std::uint8_t;
struct ObjectGuid { uint32 value=0; };
struct Creature { uint32 entry;ObjectGuid GetGUID()const{return {entry};} };
struct Unit {
 std::map<uint32,Creature> creatures;std::vector<std::pair<uint32,float>> searches;
 float GetVisibilityRange()const{return 90;}
 Creature* FindNearestCreature(uint32 entry,float range){searches.push_back({entry,range});auto i=creatures.find(entry);return i==creatures.end()?nullptr:&i->second;}
};
struct Conversation { uint32 id;std::map<uint8,ObjectGuid> actors;uint32 GetEntry()const{return id;}void AddActor(ObjectGuid guid,uint8 index){actors[index]=guid;} };
struct ConversationScript { explicit ConversationScript(char const*){}virtual ~ConversationScript()=default;virtual void OnConversationCreate(Conversation*,Unit*){} };
"""
    main=r"""
#include <iostream>
#include <stdexcept>
void check(bool ok,char const* text){if(!ok)throw std::runtime_error(text);}
int main(){try{
 conversation_campaign_nearest_actors hook;Unit creator;
 CASES
 Conversation unknown{999999};hook.OnConversationCreate(&unknown,&creator);check(unknown.actors.empty(),"unknown scene");
 hook.OnConversationCreate(nullptr,&creator);hook.OnConversationCreate(&unknown,nullptr);
 std::cout<<"PASS: actual nearest-actor hook, all39 conversations, actor indices, creator range, missing actors and null inputs\n";
}catch(std::exception const& e){std::cerr<<e.what()<<std::endl;return 1;}}
""".replace('CASES','\n'.join(fixtures))
    with tempfile.TemporaryDirectory() as d:
        d=Path(d)
        (d/'ScriptMgr.h').write_text(header)
        for name in ('Conversation.h','Creature.h'):(d/name).write_text('#include "ScriptMgr.h"\n')
        cpp=d/'nearest.cpp';cpp.write_text(source.read_text('latin1')+'\n'+main)
        flags=['-std=c++17','-Wall','-Wextra','-Werror','-Wno-missing-field-initializers']
        if not a.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        exe=d/'nearest.exe'
        subprocess.run([a.compiler,*flags,'-I',str(d),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
