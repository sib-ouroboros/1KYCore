#!/usr/bin/env python3
"""Compile native battle links, pending registration, gossip and participant gates."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
from test_gilneas_quests import method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    krennan = source[source.index('class npc_krennan_aranas_38553 :'):source.index('// 37803')]
    controller = source[source.index('class npc_sister_almyra_38466 :'):source.index('class npc_prince_liam_greymane_38218 :')]
    helpers = source[source.index('namespace\n{'):source.index(' // 38221 -- gilneas militia')]
    sections = re.split(r'    struct (npc_\w+AI) : public ScriptedAI', source)
    initializers = []
    for index in range(1, len(sections), 2):
        name, body = sections[index:index + 2]
        if 'case EVENT_INITIALISE:' not in body or name == 'npc_soultethered_banshee_38473AI':
            continue
        entry = int(re.search(r'_(\d+)AI$', name)[1])
        initializers.append((entry, name, method(body, 'case EVENT_INITIALISE:')))
    assert len(initializers) == 8
    code = r'''
#include <cstdint>
#include <list>
#include <map>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t; using int32=std::int32_t;
NATIVE_ENUM;
constexpr float INTERACTION_DISTANCE=5;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2,QUEST_STATUS_REWARDED=3;
constexpr int GOSSIP_SENDER_MAIN=0,GOSSIP_ACTION_INFO_DEF=1000;
struct ObjectGuid {
 int value=0; ObjectGuid()=default; ObjectGuid(int v):value(v){};
 explicit operator bool()const{return value!=0;}
 bool operator==(ObjectGuid o)const{return value==o.value;}
 bool operator!=(ObjectGuid o)const{return value!=o.value;}
 static ObjectGuid Empty;
}; ObjectGuid ObjectGuid::Empty{};
struct Menus {void ClearMenus(){}};
struct Phases {bool HasPhase(int)const{return false;}};
struct Session{std::vector<std::string>notices;void SendNotification(char const*text){notices.push_back(text);}void SendNotification(char const*,char const*text){notices.push_back(text);}};
struct Player {
 int option=-1,action=0;Session session;Session*GetSession(){return &session;}void PrepareQuestMenu(ObjectGuid){}
 bool alive=true,phase=true; uint32 map=654; int quest=QUEST_STATUS_INCOMPLETE; float distance=1;
 Menus menu; Menus* PlayerTalkClass=&menu;
 bool IsAlive()const{return alive;} uint32 GetMapId()const{return map;}
 int GetQuestStatus(int id)const{return id==QUEST_THE_BATTLE_FOR_GILNEAS_CITY?quest:QUEST_STATUS_NONE;}
 Phases GetPhaseShift()const{return {};}
};
namespace PhasingHandler {void RemovePhase(Player*,int){}}
struct Events {
 std::map<int,int>pending; int scheduled=0;
 void Reset(){pending.clear();scheduled=0;}
 void ScheduleEvent(int id,int delay){pending[id]=delay;++scheduled;}
 void RescheduleEvent(int id,int delay){pending[id]=delay;}
};
struct AI {
 virtual ~AI()=default; bool initialized=false; int talks=0; std::vector<int>actions;
 virtual void Reset(){} virtual uint32 GetData(uint32)const{return 0;}
 virtual ObjectGuid GetGUID(int32)const{return {};}
 virtual void SetGUID(ObjectGuid,int32){}
 virtual void DoAction(int32 id){actions.push_back(id);if(id==ACTION_INITIALIZE_DONE)initialized=true;}
 void Talk(int,Player*){++talks;}
};
struct Position {Position(float,float,float){}};
struct CreatureData{uint32 id=0,mapid=654,phaseId=187;float posX=0,posY=0;};
struct Creature;
struct BattleMap{std::multimap<uint32,Creature*>spawns;auto&GetCreatureBySpawnIdStore(){return spawns;}int loads=0;void LoadGrid(float,float){++loads;}} battleMap;
struct Creature {
 bool alive=true,phase=true,active=false;void setActive(bool b){active=b;} uint32 map=654,entry=0,script=0; ObjectGuid guid;
 float distance=1,baseDistance=1; int despawns=0; struct AI*ai=nullptr; std::list<Player*>players;
 BattleMap*GetMap(){return &battleMap;}bool IsAlive()const{return alive;} uint32 GetMapId()const{return map;}
 uint32 GetEntry()const{return entry;} uint32 GetScriptId()const{return script;}
 bool IsQuestGiver()const{return true;}ObjectGuid GetGUID()const{return guid;}
 bool IsInPhase(Player*p)const{return phase&&p->phase;}
 bool IsInPhase(Creature*c)const{return phase&&c->phase;}
 float GetDistance(Player*p)const{return p->distance;}
 float GetDistance(Position const&)const{return baseDistance;}
 float GetDistance2d(Creature*c)const{return c->distance;}
 struct AI*AI(){return ai;} void DespawnOrUnsummon(){++despawns;}
 Creature*FindNearestCreature(uint32,float);
 std::list<Player*>SelectNearestPlayers(float range,bool aliveOnly=true){
  std::list<Player*>out;for(Player*p:players)if(p->distance<=range&&(!aliveOnly||p->alive))out.push_back(p);return out;
 }
};
std::map<int,Creature*>actors;
Creature*Creature::FindNearestCreature(uint32 wanted,float range){
 Creature*nearest=nullptr;for(auto const& item:actors){Creature*c=item.second;
  if(c->entry==wanted&&c->alive&&c->map==map&&IsInPhase(c)&&c->distance<=range
    &&(!nearest||c->distance<nearest->distance))nearest=c;
 }return nearest;
}
namespace ObjectAccessor {Creature*GetCreature(Creature&context,ObjectGuid id){
 auto i=actors.find(id.value);return i==actors.end()||i->second->map!=context.map?nullptr:i->second;
}}
struct WaypointPath{std::vector<int>nodes;};
struct Waypoints{std::map<uint32,WaypointPath>paths={{3847401,{{1,2,3,4}}},{3846901,{{1,2,3}}}};WaypointPath const*GetPath(uint32 id){auto i=paths.find(id);return i==paths.end()?nullptr:&i->second;}}waypoints;auto*sWaypointMgr=&waypoints;
struct Manager {std::map<std::string,uint32>scripts;std::map<uint32,CreatureData>data;CreatureData const*GetCreatureData(uint32 id){auto i=data.find(id);return i==data.end()?nullptr:&i->second;}
 uint32 GetScriptId(char const*name){auto i=scripts.find(name);return i==scripts.end()?0:i->second;}
}manager;auto*sObjectMgr=&manager;
void CloseGossipMenuFor(Player*){}
void AddGossipItemFor(Player*p,int,int option,int,int action){p->option=option;p->action=action;}
void SendGossipMenuFor(Player*,int,ObjectGuid){}
#define CAST_AI(T, ptr) dynamic_cast<T*>(ptr)
NATIVE_HELPERS
struct Controller:AI {
 Creature*me=nullptr; Events m_events; bool m_battleIsStarted=false,m_doneA=false,m_doneB=false;
 uint32 m_wave=0,m_waveSize=0,m_point=0,m_arrivedMask=0,m_shootCoolDown=0; int groups=0,cleanup=0;
 ObjectGuid m_krennanGUID,m_prince1GUID,m_prince2GUID,m_myriamGUID,m_lornaGUID,m_dariusGUID,m_kingGUID,m_sylvanaGUID;
 void BuildFollowerGroup(){++groups;} void RemoveMyMember(){++cleanup;}
 CONTROLLER_DATA
 CONTROLLER_SET
 CONTROLLER_GET
 CONTROLLER_SEND
 PLAYER_NEAR
 PLAYER_BASE
 void DoAction(int32 param)override{switch(param){ CONTROLLER_START }}
};
struct npc_krennan_aranas_38553AI:AI {
 Creature*me=nullptr; Events m_events; ObjectGuid m_almyraGUID;
 bool m_battleIsStarted=false,m_playerIsInvited=false;
 KRENNAN_RESET
 KRENNAN_SET
 KRENNAN_ACTION
 KRENNAN_RUNNING
 KRENNAN_PREPARE
 KRENNAN_NOTIFY
 KRENNAN_GATE
 KRENNAN_START
 void Heartbeat(){switch(int(EVENT_CHECK_PLAYER_FOR_PHASE)){KRENNAN_HEARTBEAT}}
};
struct Gossip {GOSSIP_HELLO GOSSIP_SELECT};
struct Initializer:AI {
 Creature*me=nullptr;bool m_isInitialised=false; Events m_events;
 ObjectGuid m_krennanGUID,m_almyraGUID,m_liamGUID,m_liam2GUID,m_kingGUID,m_sylvanaGUID;
 void DoAction(int32 id)override{AI::DoAction(id);if(id==ACTION_INITIALIZE_DONE)m_isInitialised=true;}
};
NATIVE_INITIALIZERS
void check(bool ok,char const*message){if(!ok)throw std::runtime_error(message);}
struct Scene {
 Player player,other; Creature krennan,almyra,liam,myriam,lorna,darius,king,sylvanas,cinematicLiam;
 npc_krennan_aranas_38553AI starter; Controller controller; AI liamAI,myriamAI,lornaAI,dariusAI,kingAI,sylvanasAI,cinematicAI; Gossip gossip;
 Scene(){
  actors.clear();manager.scripts.clear();battleMap.spawns.clear();
  std::vector<std::pair<Creature*,AI*>>slots={{&krennan,&starter},{&almyra,&controller},{&liam,&liamAI},{&myriam,&myriamAI},{&lorna,&lornaAI},{&darius,&dariusAI},{&king,&kingAI},{&sylvanas,&sylvanasAI},{&cinematicLiam,&cinematicAI}};
  std::vector<uint32>entries={NPC_KRENNAN_ARANAS,NPC_SISTER_ALMYRA,NPC_PRINCE_LIAM_GREYMANE_BATTLE,NPC_MYRIAM_SPELLWAKER,NPC_LORNA_CROWLEY,NPC_LORD_DARIUS_CROWLEY,NPC_KING_GENN_GREYMANE,NPC_LADY_SYLVANAS_WINDRUNNER,NPC_PRINCE_LIAM_GREYMANE};
  for(unsigned i=0;i<slots.size();++i){Creature*c=slots[i].first;c->entry=entries[i];c->script=entries[i]+100000;c->guid=int(i+1);c->ai=slots[i].second;actors[c->guid.value]=c;manager.scripts[GetGilneasBattleScript(c->entry)]=c->script;}
  starter.me=&krennan;starter.m_almyraGUID=almyra.guid;controller.me=&almyra;controller.m_krennanGUID=krennan.guid;
  controller.m_prince1GUID=liam.guid;controller.m_myriamGUID=myriam.guid;controller.m_lornaGUID=lorna.guid;controller.m_dariusGUID=darius.guid;controller.m_kingGUID=king.guid;controller.m_sylvanaGUID=sylvanas.guid;controller.m_prince2GUID=cinematicLiam.guid;
 }
};
template<class T>void pendingRegistration(uint32 entry){
 Scene s;Creature*c=nullptr;for(auto const& item:actors)if(item.second->entry==entry)c=item.second;
 check(c!=nullptr,"initializer actor exists");T init;init.me=c;c->ai=&init;init.m_almyraGUID=999;init.m_krennanGUID=999;
 init.Run();check(entry==NPC_SISTER_ALMYRA?init.m_krennanGUID==s.krennan.guid:init.m_almyraGUID==s.almyra.guid,"all eight pending initializers discard despawned GUID and find current controller");
 check(init.m_isInitialised,"validated controller acknowledges registration");
}
int main(){try{
 {Scene s;check(s.starter.CanStartBattle(&s.player),"ready scene");s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1001);s.gossip.OnGossipSelect(&s.other,&s.krennan,0,1001);check(s.controller.m_events.scheduled==1&&s.starter.talks==1,"two stale menus start once");check(s.controller.m_events.pending.at(EVENT_GLOBAL_RESET)==600000&&s.starter.m_events.pending.at(EVENT_GLOBAL_RESET)==600000,"native reset timer reaches controller and starter");s.controller.DoAction(ACTION_START_EVENT);check(s.controller.m_events.scheduled==1,"duplicate direct start ignored");}
 for(int mode=0;mode<23;++mode){Scene s;
  if(mode==0){s.player.quest=QUEST_STATUS_NONE;}
  if(mode==1){s.player.alive=false;}
  if(mode==2){s.player.map=0;}
  if(mode==3){s.krennan.phase=false;}
  if(mode==4){s.player.distance=6;}

  if(mode==5){actors.erase(s.almyra.guid.value);}
  if(mode==6){s.almyra.alive=false;}
  if(mode==7){s.almyra.phase=false;}
  if(mode==8){s.almyra.distance=50;}
  if(mode==9){s.almyra.script=99;}

  if(mode==10){actors.erase(s.liam.guid.value);}
  if(mode==11){s.liam.alive=false;}
  if(mode==12){s.controller.m_battleIsStarted=true;}
  if(mode==13){s.krennan.alive=false;}

  if(mode==14){actors.erase(s.myriam.guid.value);}
  if(mode==15){s.myriam.alive=false;}
  if(mode==16){s.myriam.phase=false;}
  if(mode==17){s.myriam.script=99;}
  if(mode==18){s.liam.script=99;}

  if(mode==19){s.myriam.map=1;}
  if(mode==20){s.myriam.distance=50;}
  if(mode==21){manager.scripts[GetGilneasBattleScript(NPC_SISTER_ALMYRA)]=0;}
  if(mode==22){s.liam.ai=nullptr;}

  s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1001);check(!s.starter.m_battleIsStarted&&!s.controller.m_events.scheduled&&!s.starter.talks,"invalid actors or player never reserve battle");
 }
 {Scene s;s.gossip.OnGossipSelect(&s.player,&s.krennan,7,1001);s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1002);check(!s.starter.m_battleIsStarted,"foreign sender and cancel ignored");s.starter.m_battleIsStarted=true;check(!s.starter.StartBattle(&s.player),"starter independently blocks replay");}
 {Scene s;s.controller.m_prince1GUID={};check(!s.starter.StartBattle(&s.player),"unregistered prince blocks start");s.controller.m_prince1GUID=s.liam.guid;s.controller.m_myriamGUID={};check(!s.starter.StartBattle(&s.player),"unregistered Myriam blocks start");s.controller.m_myriamGUID=s.myriam.guid;check(s.starter.StartBattle(&s.player),"late registration makes scene startable");}
 {Scene s;s.starter.Reset();check(!s.starter.m_almyraGUID,"reset clears local controller link");s.starter.Heartbeat();check(s.starter.m_almyraGUID==s.almyra.guid&&s.starter.CanStartBattle(&s.player),"heartbeat repairs link even after controller's one-time initialization");s.starter.m_almyraGUID=999;s.starter.Heartbeat();check(s.starter.m_almyraGUID==s.almyra.guid,"nonempty missing GUID does not permanently suppress search");}
 {Scene s;s.starter.Reset();s.almyra.script=99;s.starter.Heartbeat();check(!s.starter.m_almyraGUID,"custom controller is not adopted");s.almyra.script=NPC_SISTER_ALMYRA+100000;s.starter.Heartbeat();check(s.starter.m_almyraGUID==s.almyra.guid,"retry after native controller returns");}
 {Scene s;s.starter.m_battleIsStarted=true;Creature replacement=s.almyra;replacement.guid=99;actors[99]=&replacement;s.starter.SetGUID(replacement.guid,NPC_SISTER_ALMYRA);check(s.starter.m_almyraGUID==s.almyra.guid,"active starter not redirected to another controller");}
 {Scene s;for(uint32 entry:{NPC_PRINCE_LIAM_GREYMANE_BATTLE,NPC_MYRIAM_SPELLWAKER,NPC_LORNA_CROWLEY,NPC_LORD_DARIUS_CROWLEY,NPC_KING_GENN_GREYMANE,NPC_LADY_SYLVANAS_WINDRUNNER,NPC_PRINCE_LIAM_GREYMANE}){
  Creature*c=nullptr;for(auto const& item:actors)if(item.second->entry==entry)c=item.second;ObjectGuid original=s.controller.GetGUID(entry);check(c!=nullptr,"registered role exists");
  Creature replacement=*c;AI replacementAI;replacement.ai=&replacementAI;replacement.guid=99;actors[99]=&replacement;s.controller.m_battleIsStarted=true;
  s.controller.SetGUID(replacement.guid,entry);check(s.controller.GetGUID(entry)==(entry==NPC_PRINCE_LIAM_GREYMANE?replacement.guid:original),"active leader pinned while native cinematic Liam replacement remains allowed");
  s.controller.m_battleIsStarted=false;s.controller.SetGUID(replacement.guid,entry);check(s.controller.GetGUID(entry)==replacement.guid&&replacementAI.initialized,"idle native replacement acknowledged");
  replacementAI.initialized=false;s.controller.SetGUID(replacement.guid,entry);check(replacementAI.initialized,"same GUID can regain initialization acknowledgement");
  replacement.phase=false;s.controller.SetGUID(c->guid,entry);ObjectGuid good=s.controller.GetGUID(entry);s.controller.SetGUID(replacement.guid,entry);check(s.controller.GetGUID(entry)==good,"phase-invalid registration rejected");
  replacement.phase=true;replacement.script=99;s.controller.SetGUID(replacement.guid,entry);check(s.controller.GetGUID(entry)==good,"custom script registration rejected");actors.erase(99);
 }}
 {Scene s;s.liam.script=99;s.myriam.phase=false;s.king.alive=false;s.controller.SendActionValueToAllLeader(ACTION_EVENT_RESET_TIMER);check(s.liamAI.actions.empty()&&s.myriamAI.actions.empty()&&s.kingAI.actions.empty()&&!s.lornaAI.actions.empty(),"broadcast skips replaced, wrong-phase and dead actors while valid leaders receive timer");}
 {Scene s;s.almyra.players={&s.player,&s.other};s.player.quest=QUEST_STATUS_NONE;s.other.alive=false;check(!s.controller.IsPlayerNear(25),"bystander and corpse do not release a quest wave");s.other.alive=true;check(s.controller.IsPlayerNear(25),"another living participant keeps shared wave eligible");s.other.phase=false;check(!s.controller.IsPlayerNear(25),"other phase is not participation");s.other.phase=true;s.other.map=0;check(!s.controller.IsPlayerNear(25),"other map is not participation");s.other.map=654;s.other.distance=26;check(!s.controller.IsPlayerNear(25),"native range retained");s.other.distance=1;s.other.quest=QUEST_STATUS_COMPLETE;check(!s.controller.IsPlayerNear(25),"finished quest is not a waiting participant");}
 {Scene s;s.liam.players={&s.player};s.myriam.players={&s.other};s.player.quest=QUEST_STATUS_NONE;s.other.alive=false;check(!s.controller.IsPlayerNearBase(),"base gate rejects bystanders and corpses");s.other.alive=true;check(s.controller.IsPlayerNearBase(),"living participant near either native base leader releases gate");s.liam.baseDistance=26;check(!s.controller.IsPlayerNearBase(),"both base leaders must remain at native base");}
 {Scene s;s.controller.m_lornaGUID={};s.gossip.OnGossipHello(&s.player,&s.krennan);check(s.player.option==0&&s.player.action==1001,"missing leader must not expose join-running-battle placeholder");s.starter.m_battleIsStarted=true;s.gossip.OnGossipHello(&s.player,&s.krennan);check(s.player.option==1&&s.player.action==1002,"join offered only during active battle");s.player.quest=QUEST_STATUS_REWARDED;s.player.option=-1;s.gossip.OnGossipHello(&s.player,&s.krennan);check(s.player.option==-1,"completed player gets no replay menu");}
 {Scene s;s.controller.m_lornaGUID={};s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1001);check(!s.starter.m_battleIsStarted&&!s.player.session.notices.empty(),"unready click reports failure instead of silently closing");s.starter.m_battleIsStarted=true;unsigned old=s.player.session.notices.size();s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1002);check(s.player.session.notices.size()==old+1,"join running battle gives clear status without replay");}
 {Scene s;waypoints.paths[3847401].nodes.resize(3);check(!s.starter.CanStartBattle(&s.player),"truncated Liam finale route blocks start");waypoints.paths[3847401].nodes.resize(4);auto old=waypoints.paths[3846901];waypoints.paths.erase(3846901);check(!s.starter.CanStartBattle(&s.player),"missing Sylvanas departure route blocks start");waypoints.paths[3846901]=old;check(s.starter.CanStartBattle(&s.player),"valid native finale routes allow battle");}
 {Scene s;for(uint32 role:{uint32(NPC_LORNA_CROWLEY),uint32(NPC_LORD_DARIUS_CROWLEY),uint32(NPC_KING_GENN_GREYMANE),uint32(NPC_LADY_SYLVANAS_WINDRUNNER)}){ObjectGuid id=s.controller.GetGUID(role);Creature*actor=actors.at(id.value);actors.erase(id.value);check(!s.starter.CanStartBattle(&s.player),"missing late leader blocks battle before wave3");actors[id.value]=actor;}}
 {Scene s;ObjectGuid link; s.almyra.distance=600;check(!FindGilneasBattleActor(&s.lorna,link,NPC_SISTER_ALMYRA,100),"old radius misses controller");check(FindGilneasBattleActor(&s.lorna,link,NPC_SISTER_ALMYRA,700)==&s.almyra,"late leader can bind from initial staging area");}
 {Scene s;Init38426 lorna;Init38415 darius;Init38470 king;Init38469 sylvanas;
  lorna.me=&s.lorna;darius.me=&s.darius;king.me=&s.king;sylvanas.me=&s.sylvanas;
  s.lorna.ai=&lorna;s.darius.ai=&darius;s.king.ai=&king;s.sylvanas.ai=&sylvanas;
  s.controller.m_lornaGUID={};s.controller.m_dariusGUID={};s.controller.m_kingGUID={};s.controller.m_sylvanaGUID={};
  for(auto pair:std::vector<std::pair<uint32,Creature*>>{{802754,&s.lorna},{802707,&s.darius},{802822,&s.king},{802781,&s.sylvanas}}){manager.data[pair.first]={pair.second->entry,654,187,1,2};battleMap.spawns.emplace(pair.first,pair.second);}
  check(!s.starter.CanStartBattle(&s.player),"before-registration gate remains strict");
  // The periodic readiness check must bind loaded leaders before a new gossip click.
  s.starter.Heartbeat();
  check(s.starter.CanStartBattle(&s.player),"heartbeat registers all distant leaders without visiting them or ticking their AI");
  check(s.starter.StartBattle(&s.player),"all four loaded leaders register synchronously without AI tick or grid search");
  check(lorna.m_almyraGUID==s.almyra.guid&&darius.m_almyraGUID==s.almyra.guid&&king.m_almyraGUID==s.almyra.guid&&sylvanas.m_almyraGUID==s.almyra.guid,"controller acknowledgement follows all four reverse links");
  check(lorna.m_isInitialised&&darius.m_isInitialised&&king.m_isInitialised&&sylvanas.m_isInitialised,"all distant leaders acknowledge initialization");
  Creature replacement=s.almyra;replacement.guid=999;actors[999]=&replacement;
  sylvanas.m_cinematicStarted=true;sylvanas.SetGUID(replacement.guid,NPC_SISTER_ALMYRA);check(sylvanas.m_almyraGUID==s.almyra.guid,"cinematic Sylvanas cannot switch controller");
  sylvanas.SetGUID(s.almyra.guid,NPC_SISTER_ALMYRA);check(sylvanas.m_almyraGUID==s.almyra.guid,"same controller remains valid during cinematic");
  sylvanas.m_cinematicStarted=false;sylvanas.SetGUID(replacement.guid,NPC_SISTER_ALMYRA);check(sylvanas.m_almyraGUID==replacement.guid,"idle Sylvanas can bind validated replacement controller");actors.erase(999);

  manager.data.clear();}
 {Scene s;manager.data[802754]={NPC_LORNA_CROWLEY,654,187,1,2};battleMap.spawns.emplace(802754,&s.lorna);PrimeGilneasBattleActors(&s.krennan);check(s.lorna.active,"loaded distant actor is activated so pending initialization can tick");s.lorna.active=false;s.lorna.script=0;PrimeGilneasBattleActors(&s.krennan);check(!s.lorna.active,"custom script never activated as battle actor");manager.data.clear();}
 {Scene s;manager.data[802754]={NPC_LORNA_CROWLEY,654,187,1,2};int old=battleMap.loads;PrimeGilneasBattleActors(&s.krennan);check(battleMap.loads==old+1,"only known matching late spawn grid is loaded");manager.data[802754].mapid=1;PrimeGilneasBattleActors(&s.krennan);check(battleMap.loads==old+1,"foreign map data never loaded");manager.data.clear();}
 {Scene s;s.almyra.players={&s.player};s.starter.StartBattle(&s.player);s.player.alive=false;check(!s.controller.IsPlayerNear(25)&&s.controller.m_battleIsStarted,"death waits without clearing shared battle");s.player.alive=true;check(s.controller.IsPlayerNear(25)&&s.controller.m_battleIsStarted,"resurrection resumes same participant gate");}
 NATIVE_INITIALIZER_CHECKS
 std::cout<<"Gilneas battle: native actor links, eight pending initializers, gossip recovery and participant gates PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
    replacements = {
        'NATIVE_ENUM': method(source, 'enum eZoneGilneasCity2'),
        'NATIVE_HELPERS': helpers,
        'CONTROLLER_DATA': method(controller, '        uint32 GetData('),
        'CONTROLLER_SET': method(controller, '        void SetGUID('),
        'CONTROLLER_GET': method(controller, '        ObjectGuid GetGUID('),
        'CONTROLLER_SEND': method(controller, '        void SendActionValueToAllLeader('),
        'CONTROLLER_START': method(controller, '                case ACTION_START_EVENT:'),
        'PLAYER_NEAR': method(controller, '        bool IsPlayerNear('),
        'PLAYER_BASE': method(controller, '        bool IsPlayerNearBase('),
        'KRENNAN_RESET': method(krennan, '        void Reset('),
        'KRENNAN_SET': method(krennan, '        void SetGUID('),
        'KRENNAN_ACTION': method(krennan, '        void DoAction('),
        'KRENNAN_RUNNING': method(krennan, '        bool IsBattleRunning('),
        'KRENNAN_PREPARE': method(krennan, '        void PrepareBattleController('),
        'KRENNAN_NOTIFY': method(krennan, '        void NotifyBattleStatus('),
        'KRENNAN_GATE': method(krennan, '        bool CanStartBattle('),
        'KRENNAN_START': method(krennan, '        bool StartBattle('),
        'KRENNAN_HEARTBEAT': method(krennan, '                case EVENT_CHECK_PLAYER_FOR_PHASE:'),
        'GOSSIP_HELLO': method(krennan, '    bool OnGossipHello('),
        'GOSSIP_SELECT': method(krennan, '    bool OnGossipSelect('),
        'NATIVE_INITIALIZERS': '\n'.join('struct Init'+str(entry)+':Initializer{'+('bool m_cinematicStarted=false;' if entry==38469 else 'uint32 m_wave=0;' if entry in (38426,38415,38470) else '')+((method(source[source.index('    struct '+name):], '        void SetGUID(')+method(source[source.index('    struct '+name):], '        ObjectGuid GetGUID(')) if entry in (38426,38415,38470,38469) else '')+'void Run(){switch(int(EVENT_INITIALISE)){'+case+'}}};' for entry, name, case in initializers),
        'NATIVE_INITIALIZER_CHECKS': ''.join('pendingRegistration<Init'+str(entry)+'>('+str(entry)+');' for entry, _, _ in initializers),
    }
    for key, value in replacements.items():
        code = re.sub(r'\b'+key+r'\b', lambda match: value, code)
    with tempfile.TemporaryDirectory(prefix='gilneas-battle-start-') as folder:
        cpp = Path(folder) / 'start.cpp'
        binary = Path(folder) / 'start.exe'
        cpp.write_text(code, 'utf8')
        command = [os.environ.get('CXX', 'g++'), '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(binary)]
        if not args.no_sanitizers:
            command[1:1] = ['-fsanitize=address,undefined', '-fno-sanitize-recover=undefined', '-fno-omit-frame-pointer']
        subprocess.run(command, check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    main()
