#!/usr/bin/env python3
"""Execute the actual session handler and menu lifecycle under callback mutation."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def method(text,signature):
    start=text.index(signature);opening=text.index('{',start);end=opening+1;depth=1
    while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]


def main():
    p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');p.add_argument('--handler-source',type=Path);p.add_argument('--scenario',choices=['all','snapshot','native','go'],default='all');args=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    handler=method((args.handler_source or root/'src/server/game/Handlers/NPCHandler.cpp').read_text('utf8'),'void WorldSession::HandleGossipSelectOptionOpcode(')
    header=(root/'src/server/game/Entities/Creature/GossipDef.h').read_text('utf8')
    menu=header[header.index('struct GossipMenuItem\n'):header.index('class TC_GAME_API QuestMenu')].replace('TC_GAME_API','')
    source=(root/'src/server/game/Entities/Creature/GossipDef.cpp').read_text('utf8')
    methods='\n'.join(method(source,sig) for sig in ['GossipMenu::GossipMenu()','GossipMenu::~GossipMenu()','uint32 GossipMenu::AddMenuItem(int32','void GossipMenu::AddGossipMenuItemData(','void GossipMenu::ClearMenu()','uint32 GossipMenu::GetMenuItemSender(','uint32 GossipMenu::GetMenuItemAction(','void PlayerMenu::SendCloseGossip()'])
    code=r'''
#include <cassert>
#include <cstdint>
#include <functional>
#include <map>
#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t;using uint32=std::uint32_t;using uint64=std::uint64_t;using int32=std::int32_t;
using LocaleConstant=int;constexpr int DEFAULT_LOCALE=0,GOSSIP_MAX_MENU_ITEMS=32,UNIT_NPC_FLAG_GOSSIP=1,UNIT_STATE_DIED=1,SPELL_AURA_FEIGN_DEATH=1;
#define ASSERT(x) assert(x)
#define TC_LOG_DEBUG(...) ((void)0)
void check(bool ok,char const* message){if(!ok){std::cerr<<message<<std::endl;throw std::runtime_error(message);}}
struct ObjectGuid{uint32 id=0,kind=1;bool operator!=(ObjectGuid const& o)const{return id!=o.id||kind!=o.kind;}bool operator==(ObjectGuid const& o)const{return !(*this!=o);}bool IsCreatureOrVehicle()const{return kind==1;}bool IsGameObject()const{return kind==2;}void Clear(){id=0;}std::string ToString()const{return std::to_string(id);}};
MENU
struct WorldSession;
struct Interaction{ObjectGuid SourceGuid;uint32 PlayerChoiceId=0;void Reset(){SourceGuid.Clear();PlayerChoiceId=0;}};
struct PlayerMenu{GossipMenu menu;Interaction interaction;WorldSession* _session=nullptr;
 GossipMenu& GetGossipMenu(){return menu;}Interaction& GetInteractionData(){return interaction;}
 uint32 GetGossipOptionSender(uint32 i){return menu.GetMenuItemSender(i);}uint32 GetGossipOptionAction(uint32 i){return menu.GetMenuItemAction(i);}
 void ClearMenus(){menu.ClearMenu();}void SendCloseGossip();Interaction& _interactionData=interaction;};
struct Player;
struct FakeAI{std::function<void(Player*)> mutate;bool handled=false;uint32 calls=0,menu=0,index=0;std::string code;
 void invoke(Player* p,uint32 m,uint32 i,const char* c){++calls;menu=m;index=i;code=c?c:"";if(mutate)mutate(p);}
 void sGossipSelect(Player* p,uint32 m,uint32 i){invoke(p,m,i,nullptr);}void sGossipSelectCode(Player* p,uint32 m,uint32 i,const char* c){invoke(p,m,i,c);}
 bool GossipSelect(Player* p,uint32 m,uint32 i){invoke(p,m,i,nullptr);return handled;}bool GossipSelectCode(Player* p,uint32 m,uint32 i,const char* c){invoke(p,m,i,c);return handled;}};
struct Creature{FakeAI ai;uint32 LastUsedScriptID=1;FakeAI* AI(){return &ai;}uint32 GetScriptId(){return 1;}uint32 GetEntry(){return 100;}std::string GetAIName(){return "SmartAI";}};
struct GameObject:Creature{};
struct Player{PlayerMenu storage;PlayerMenu* PlayerTalkClass=&storage;Creature* creature=nullptr;GameObject* object=nullptr;uint32 nativeCalls=0;
 ObjectGuid GetGUID(){return {99,1};}Creature* GetNPCIfCanInteractWith(ObjectGuid,uint32){return creature;}
 GameObject* GetGameObjectIfCanInteractWith(ObjectGuid){return object;}bool HasUnitState(int){return false;}void RemoveAurasByType(int){}
 template<class T>void OnGossipSelect(T*,uint32,uint32){++nativeCalls;}};
struct ScriptMgr{uint32 calls=0,sender=0,action=0;std::string code;bool handled=true;std::function<void(Player*)> mutate;
 template<class T>bool OnGossipSelect(Player* p,T*,uint32 s,uint32 a){++calls;sender=s;action=a;if(mutate)mutate(p);return handled;}
 template<class T>bool OnGossipSelectCode(Player* p,T* target,uint32 s,uint32 a,const char* c){code=c;return OnGossipSelect(p,target,s,a);}} manager;auto* sScriptMgr=&manager;
struct ObjectMgr{std::string GetScriptName(uint32){return "test";}} objects;auto* sObjectMgr=&objects;
namespace WorldPackets{namespace NPC{struct GossipSelectOption{uint32 GossipID=0,GossipIndex=0;ObjectGuid GossipUnit;std::string PromotionCode;};struct GossipComplete{int Write(){return 0;}};}}
struct WorldSession{Player* _player;Player* GetPlayer(){return _player;}void SendPacket(int){}void HandleGossipSelectOptionOpcode(WorldPackets::NPC::GossipSelectOption&);};
METHODS
HANDLER
int main(){
 if(RUN_SNAPSHOT)for(uint32 kind:{1u,2u})for(bool coded:{false,true})for(int mutation:{0,1,2}){
  Player p;Creature c;GameObject g;p.creature=&c;p.object=&g;WorldSession session{&p};p.storage._session=&session;
  auto* ai=kind==1?c.AI():g.AI();ObjectGuid guid{42,kind};auto& menu=p.storage.menu;
  menu.SetMenuId(10);menu.AddMenuItem(0,0,"old",1,1001,"",0,coded);p.storage.interaction.SourceGuid=guid;
  if(mutation)ai->mutate=[mutation](Player* player){auto& m=player->storage.menu;player->storage.ClearMenus();if(mutation==2)m.AddMenuItem(0,0,"new",7,2002,"",0);};
  manager={};WorldPackets::NPC::GossipSelectOption packet{10,0,guid,coded?"secret":""};session.HandleGossipSelectOptionOpcode(packet);
  check(manager.calls==1&&manager.sender==1&&manager.action==1001,"callback read mutated sender/action");
  check(ai->calls==1&&ai->menu==10&&ai->index==0,"AI identifiers changed to sender/action");
  if(coded)check(manager.code=="secret"&&ai->code=="secret","coded text dispatch changed");
  if(mutation==2){ai->mutate={};session.HandleGossipSelectOptionOpcode(packet);check(manager.action==2002&&manager.sender==7,"next click did not use new menu");}
 }
 if(RUN_NATIVE)for(uint32 kind:{1u,2u})for(bool coded:{false,true}){
  Player p;Creature c;GameObject g;p.creature=&c;p.object=&g;WorldSession session{&p};p.storage._session=&session;
  auto* ai=kind==1?c.AI():g.AI();ObjectGuid guid{42,kind};auto& menu=p.storage.menu;
  menu.SetMenuId(11);menu.AddMenuItem(0,0,"db",1,3,"",0,coded);menu.AddGossipMenuItemData(0,12,0,0);p.storage.interaction.SourceGuid=guid;
  manager={};manager.handled=false;WorldPackets::NPC::GossipSelectOption packet{11,0,guid,coded?"text":""};session.HandleGossipSelectOptionOpcode(packet);check(p.nativeCalls==1,"unchanged DB fallback suppressed");
  ai->mutate=[](Player* player){player->storage.ClearMenus();player->storage.menu.AddMenuItem(0,0,"other db",1,5,"",0);player->storage.menu.AddGossipMenuItemData(0,99,0,8);};
  session.HandleGossipSelectOptionOpcode(packet);check(p.nativeCalls==1,"new DB menu handled old click");
  ai->mutate={};menu.SetMenuId(12);auto count=ai->calls;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count,"stale Menu A packet reached Menu B callback");
  packet.GossipID=12;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count+1,"valid nested selection rejected");
  menu.SetMenuId(0);packet.GossipID=0;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count+2,"zero scripted menu rejected");
  packet.GossipUnit.id=43;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count+2,"foreign source reached callback");
  packet.GossipUnit=guid;packet.GossipIndex=999;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count+2,"missing index reached callback");
  p.storage.interaction.PlayerChoiceId=123;p.storage.SendCloseGossip();check(p.storage.interaction.PlayerChoiceId==123&&p.storage.interaction.SourceGuid.id==0,"PlayerChoice lost on close");
  packet.GossipIndex=0;session.HandleGossipSelectOptionOpcode(packet);check(ai->calls==count+2,"closed gossip reached callback");
 }
 if(RUN_GO)for(bool coded:{false,true}){Player p;GameObject g;p.object=&g;WorldSession session{&p};p.storage._session=&session;
  p.storage.menu.AddMenuItem(0,0,"go",8,1234,"",0,coded);p.storage.interaction.SourceGuid={42,2};g.ai.handled=true;manager={};
  WorldPackets::NPC::GossipSelectOption packet{0,0,{42,2},coded?"code":""};session.HandleGossipSelectOptionOpcode(packet);
  check(g.ai.calls==1&&manager.calls==0&&p.nativeCalls==0,"handled GO selection dispatched twice");}
 Creature shared;Player a,b;a.creature=&shared;b.creature=&shared;WorldSession sa{&a},sb{&b};a.storage._session=&sa;b.storage._session=&sb;
 for(auto* player:{&a,&b}){player->storage.menu.AddMenuItem(0,0,"personal",1,player==&a?1001:3003,"",0);player->storage.interaction.SourceGuid={42,1};}
 shared.ai.mutate=[](Player* p){p->storage.ClearMenus();};manager={};WorldPackets::NPC::GossipSelectOption personal{0,0,{42,1},""};
 sa.HandleGossipSelectOptionOpcode(personal);check(manager.action==1001&&b.storage.menu.GetItem(0)->OptionType==3003,"first player polluted second menu");
 sb.HandleGossipSelectOptionOpcode(personal);check(manager.action==3003&&manager.calls==2,"shared NPC reused another player's snapshot");
 GossipMenu indices;check(indices.AddMenuItem(-1,0,"a",0,1,"",0)==0,"first index");indices.AddMenuItem(2,0,"c",0,3,"",0);check(indices.AddMenuItem(-1,0,"b",0,2,"",0)==1,"hole allocation changed");indices.ClearMenu();check(indices.AddMenuItem(-1,0,"a",0,1,"",0)==0,"clear/rebuild index changed");
 std::cout<<"PASS: actual Gossip handler/menu; clear/rebuild snapshots, creature/GO/coded dispatch, DB mutation guard, stale/zero/nested IDs, close/PlayerChoice, handled GO and hole allocation\n";
}
'''.replace('\nMENU\n','\n'+menu+'\n').replace('\nMETHODS\n','\n'+methods+'\n').replace('\nHANDLER\n','\n'+handler+'\n')
    for key,scenario in [('RUN_SNAPSHOT','snapshot'),('RUN_NATIVE','native'),('RUN_GO','go')]:code=code.replace(key,'true' if args.scenario in ('all',scenario) else 'false')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'gossip.cpp';exe=Path(tmp)/'gossip';cpp.write_text(code,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
