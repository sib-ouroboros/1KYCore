#!/usr/bin/env python3
"""Compile real Create, actor publication and source hook; check pause boundaries."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from test_conversation_packet_layout import declaration


def method(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers', action='store_true')
    parser.add_argument('--source', type=Path, help='Original Create source for regression proof.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root/'src/server/game/Entities/Conversation/Conversation.cpp').read_text('utf8')
    baseline = args.source.read_text('utf8') if args.source else source
    store = (root/'src/server/game/Globals/ConversationDataStore.h').read_text('utf8')
    header = (root/'src/server/game/Entities/Conversation/Conversation.h').read_text('utf8')
    scripts = (root/'src/server/scripts/World/conversation_scripts.cpp').read_text('utf8')
    hook = re.search(r'class conversation_campaign_source_actors : public ConversationScript\n\{.*?^\};', scripts, re.M|re.S)[0]
    assert scripts.count('new conversation_campaign_source_actors();') == 1
    registry = json.loads((root/'docs/audit-data/campaign-source-actor-conversations.json').read_text('utf8'))
    native = '\n'.join([declaration(store, 'ConversationActorTemplate'), declaration(store, 'ConversationLineTemplate'), declaration(header, 'ConversationDynamicFieldActor')])
    definitions = '\n'.join([method(baseline, 'bool Conversation::Create('), method(source, 'void Conversation::AddActor(ConversationActorTemplate const&')])
    fixtures = []
    for candidate in registry['source']:
        cid = candidate['id']
        fixtures.append(f'templateStore.templates[{cid}].LastLineEndTime={candidate["end"]};')
        for line, client in zip(candidate['lines'], candidate['client_lines']):
            raw = int(line['unk2'])
            fixtures.append('lines[%s]={%s,%s,%s,%s,%s,%s};' % (line['id'], line['id'], line['textId'], line['unk1'], raw & 255, (raw >> 8) & 255, raw >> 16))
            fixtures.append(f'templateStore.templates[{cid}].Lines.push_back(&lines[{line["id"]}]);')
            fixtures.append('sConversationLineStore.rows[%s]={%s};' % (line['id'], ','.join(str(client[k]) for k in ('BroadcastTextID','SpellVisualKitID','AnimKitID','SpeechType','StartAnimation','EndAnimation'))))
    harness = r"""
#include <cstdint>
#include <cstring>
#include <map>
#include <set>
#include <vector>
#include <iostream>
#include <stdexcept>
#include <utility>
using uint8=std::uint8_t;using uint16=std::uint16_t;using uint32=std::uint32_t;
struct ObjectGuid{using LowType=std::uint64_t;std::uint64_t low=0,high=0;bool IsEmpty()const{return !low&&!high;}template<auto Kind,class...T>static ObjectGuid Create(T...){return {1,0};}};
#pragma pack(push,1)
NATIVE
#pragma pack(pop)
struct Position{};struct SpellInfo{};enum class HighGuid{Conversation};
constexpr uint32 CONVERSATION_LAST_LINE_END_TIME=1,IN_MILLISECONDS=1000,CONVERSATION_DYNAMIC_FIELD_ACTORS=1,CONVERSATION_DYNAMIC_FIELD_LINES=2;
#define ASSERT(x) do{if(!(x))throw std::runtime_error("assert");}while(false)
#define TC_LOG_ERROR(...) do{}while(false)
using GuidUnorderedSet=std::set<uint32>;
struct Conversation;struct Creature{ObjectGuid GetGUID(){return {123,0};}};
struct Map{bool added=false;std::multimap<std::uint64_t,Creature*> creatures;uint32 GetId(){return 1;}auto& GetCreatureBySpawnIdStore(){return creatures;}bool AddToMap(Conversation*){added=true;return true;}};
struct Unit{ObjectGuid guid{42,0};ObjectGuid GetGUID(){return guid;}};
struct ConversationTemplate{uint32 LastLineEndTime=0;std::vector<ConversationActorTemplate const*> Actors;std::vector<ObjectGuid::LowType> ActorGuids;std::vector<ConversationLineTemplate const*> Lines;};
struct TemplateStore{std::map<uint32,ConversationTemplate> templates;ConversationTemplate const* GetConversationTemplate(uint32 id){auto i=templates.find(id);return i==templates.end()?nullptr:&i->second;}}templateStore;auto* sConversationDataStore=&templateStore;
struct ConversationLineEntry{uint32 BroadcastTextID=0,SpellVisualKitID=0,AnimKitID=0,SpeechType=0,StartAnimation=60,EndAnimation=60;};
struct LineStore{std::map<uint32,ConversationLineEntry> rows;ConversationLineEntry const* LookupEntry(uint32 id){auto i=rows.find(id);return i==rows.end()?nullptr:&i->second;}}sConversationLineStore;
namespace Trinity::Containers{template<class M,class K>auto MapEqualRange(M& map,K key){return map.equal_range(key);}}
template<class T>struct Range{T first,last;T begin(){return first;}T end(){return last;}};
namespace Trinity::Containers{template<class M>Range<typename M::iterator> MapEqualRange(M& map,ObjectGuid::LowType key){auto p=map.equal_range(key);return {p.first,p.second};}}
struct Object{void _Create(ObjectGuid){}};
struct Conversation:Object{ObjectGuid _creatorGuid;GuidUnorderedSet _participants;uint32 _duration=0,entry=0,end=0;Map* map=nullptr;std::map<uint16,ConversationDynamicFieldActor> actors;
 void SetMap(Map* m){map=m;}Map* GetMap(){return map;}uint32 GetMapId(){return map->GetId();}void Relocate(Position const&){}void SetEntry(uint32 id){entry=id;}uint32 GetEntry(){return entry;}void SetObjectScale(float){}void SetUInt32Value(uint32,uint32 v){end=v;}
 void AddActor(ObjectGuid const& guid,uint16 idx){ConversationDynamicFieldActor a;a.ActorGuid=guid;actors[idx]=a;}
 void AddActor(ConversationActorTemplate const&,uint16);
 template<class T>void SetDynamicStructuredValue(uint32,uint16 idx,T const* value){actors[idx]=*value;}
 template<class T>T const* GetDynamicStructuredValue(uint32,uint16 idx){auto i=actors.find(idx);return i==actors.end()?nullptr:&i->second;}
 template<class T>void AddDynamicStructuredValue(uint32,T const*){}
 bool Create(ObjectGuid::LowType,uint32,Map*,Unit*,Position const&,GuidUnorderedSet&&,SpellInfo const*);
};
struct PhasingHandler{static void InheritPhaseShift(Conversation*,Unit*){}};
struct ConversationScript{explicit ConversationScript(char const*){}virtual ~ConversationScript()=default;virtual void OnConversationCreate(Conversation*,Unit*){}};
HOOK
struct ScriptMgr{void OnConversationCreate(Conversation* c,Unit* u){conversation_campaign_source_actors hook;hook.OnConversationCreate(c,u);}}scriptMgr;auto* sScriptMgr=&scriptMgr;
DEFINITIONS
void check(bool x,char const* msg){if(!x)throw std::runtime_error(msg);}
int main(){try{
 std::map<uint32,ConversationLineTemplate> lines;
FIXTURES
 Unit first,second;second.guid={43,0};Position pos;Map map;
 Conversation a,b,chest;
 check(a.Create(1,4304,&map,&first,pos,{42},nullptr),"silent first line rejected");
 check(a.actors.count(0)==0&&a.actors.size()==2,"ignored player sentinel merged");
 check(a.actors.at(1).ActorTemplate.Id==57431&&a.actors.at(2).ActorTemplate.Id==51642&&a.actors.at(2).ActorTemplate.CreatureId==117443,"source actor identity changed");
 check(a.end==54554&&a._duration==64554,"source actor-branch timing changed");
 check(b.Create(2,4304,&map,&second,pos,{43},nullptr)&&b._creatorGuid.low==43&&a._creatorGuid.low==42,"second creator contaminated");
 check(a._participants==GuidUnorderedSet{42}&&b._participants==GuidUnorderedSet{43},"participants leaked to another player");
 check(chest.Create(3,4576,&map,&first,pos,{42},nullptr)&&chest.actors.at(0).ActorTemplate.Id==57350&&chest.end==39764,"chest dependency lost");
 for(unsigned mode=0;mode<11;++mode){
  auto old=sConversationLineStore.rows.at(9822);auto line=lines.at(9822);
  if(mode==0)sConversationLineStore.rows.at(9822).BroadcastTextID=1;
  if(mode==1)sConversationLineStore.rows.at(9822).SpellVisualKitID=1;
  if(mode==2)sConversationLineStore.rows.at(9822).AnimKitID=1;
  if(mode==3)sConversationLineStore.rows.at(9822).SpeechType=1;
  if(mode==4)sConversationLineStore.rows.at(9822).StartAnimation=1;
  if(mode==5)sConversationLineStore.rows.at(9822).EndAnimation=1;
  if(mode==6)lines.at(9822).Flags=1;
  if(mode==7)lines.at(9822).UiCameraID=1;
  if(mode==8)lines.at(9822).Padding=1;
  if(mode==9)sConversationLineStore.rows.erase(9822);
  // Same actor index used by a later speaking line must remain required.
  if(mode==10)lines.at(10101).ActorIdx=0;
  Conversation rejected;Map isolated;check(!rejected.Create(4,4304,&isolated,&first,pos,{42},nullptr)&&!isolated.added,"actor-requiring line incorrectly accepted");
  sConversationLineStore.rows[9822]=old;lines[9822]=line;lines[10101].ActorIdx=1;
 }
 ConversationActorTemplate ordinaryActor{51642,121263,76255};ConversationLineTemplate ordinaryLine{30000,0,0,0,0,0};
 templateStore.templates[999].Actors={&ordinaryActor};templateStore.templates[999].Lines={&ordinaryLine};
 sConversationLineStore.rows[30000].BroadcastTextID=1;
 Conversation ordinary;check(ordinary.Create(5,999,&map,&first,pos,{42},nullptr),"ordinary actor broken");
 check(ordinary.actors.at(0).ActorTemplate.CreatureId==121263&&ordinaryActor.CreatureModelId==76255,"global actor overwritten");
 std::cout<<"PASS: actual Create, source hook, silent pause, strict required actors, local shared-ID payload, two creators and unchanged ordinary actors\n";
}catch(std::exception const& e){std::cerr<<e.what()<<"\n";return 1;}
}
"""
    for key, value in {'NATIVE':native,'HOOK':hook,'DEFINITIONS':definitions,'FIXTURES':'\n'.join(fixtures)}.items():
        harness = harness.replace('\n'+key+'\n', '\n'+value+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp)/'source.cpp', Path(tmp)/'source'
        cpp.write_text(harness,encoding='utf8')
        flags = [] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-D_GLIBCXX_DEBUG',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
