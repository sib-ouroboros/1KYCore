#!/usr/bin/env python3
"""Exercise real Krennan gates and controller start case, including stale gossip."""
import argparse, os, subprocess, tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    k=s[s.index('class npc_krennan_aranas_38553 :'):s.index('// 37803')]
    a=s[s.index('class npc_sister_almyra_38466 :'):s.index('class npc_prince_liam_greymane_38218 :')]
    code=r'''
#include <cstdint>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;
constexpr int ACTION_START_EVENT=1,ACTION_EVENT_RESET_TIMER=2,EVENT_GLOBAL_RESET=3,EVENT_START_LIAMS_FIRST_ANIM=4,DATA_IS_BATTLE_STARTED=5,NPC_SISTER_ALMYRA=38466,NPC_PRINCE_LIAM_GREYMANE_BATTLE=38218,QUEST_THE_BATTLE_FOR_GILNEAS_CITY=24904,QUEST_STATUS_INCOMPLETE=1,GOSSIP_SENDER_MAIN=0,GOSSIP_ACTION_INFO_DEF=1000;
constexpr float INTERACTION_DISTANCE=5;
using ObjectGuid=int;
struct Menus{void ClearMenus(){}};
struct Player{bool alive=true;uint32 map=654;int quest=1;Menus menu;Menus*PlayerTalkClass=&menu;bool IsAlive()const{return alive;}uint32 GetMapId()const{return map;}int GetQuestStatus(int)const{return quest;}};
struct Events{int scheduled=0;void Reset(){scheduled=0;}void ScheduleEvent(int,int){++scheduled;}void RescheduleEvent(int,int){}};
struct AI{virtual~AI()=default;virtual uint32 GetData(uint32)const{return 0;}virtual ObjectGuid GetGUID(int32)const{return 0;}virtual void DoAction(int32){}int talks=0;void Talk(int,Player*){++talks;}};
struct Creature{bool alive=true,phase=true;uint32 map=654,entry=0,script=7;float distance=1;struct AI*ai=nullptr;bool IsAlive()const{return alive;}uint32 GetMapId()const{return map;}uint32 GetEntry()const{return entry;}uint32 GetScriptId()const{return script;}bool IsInPhase(Player*)const{return phase;}bool IsInPhase(Creature*c)const{return phase&&c->phase;}float GetDistance(Player*)const{return distance;}float GetDistance2d(Creature*c)const{return c->distance;}struct AI*AI(){return ai;}};
std::map<int,Creature*> actors;
namespace ObjectAccessor{Creature*GetCreature(Creature&,ObjectGuid id){auto i=actors.find(id);return i==actors.end()?nullptr:i->second;}}
struct Manager{uint32 script=7;uint32 GetScriptId(char const*){return script;}}manager;auto*sObjectMgr=&manager;
void CloseGossipMenuFor(Player*){}
#define CAST_AI(T, ptr) dynamic_cast<T*>(ptr)
struct Controller:AI{bool m_battleIsStarted=false;Events m_events;ObjectGuid prince=3;int broadcasts=0;void SendActionValueToAllLeader(int){++broadcasts;}ObjectGuid GetGUID(int32)const override{return prince;}
CONTROLLER_DATA
void DoAction(int32 param)override{switch(param){ CONTROLLER_CASE }}
};
struct npc_krennan_aranas_38553AI:AI{Creature*me;Events m_events;ObjectGuid m_almyraGUID=2;bool m_battleIsStarted=false,m_playerIsInvited=false;
KRENNAN_ACTION
KRENNAN_GATE
KRENNAN_START
};
struct Gossip { GOSSIP_SELECT };
void check(bool ok,char const*msg){if(!ok)throw std::runtime_error(msg);}
struct Scene{Player player,other;Creature krennan,almyra,liam;npc_krennan_aranas_38553AI ai;Controller controller;Gossip gossip;Scene(){actors={{2,&almyra},{3,&liam}};manager.script=7;krennan.ai=&ai;ai.me=&krennan;almyra.entry=NPC_SISTER_ALMYRA;almyra.ai=&controller;liam.entry=NPC_PRINCE_LIAM_GREYMANE_BATTLE;}};
int main(){try{
 {Scene s;check(s.ai.CanStartBattle(&s.player),"ready scene");s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1001);s.gossip.OnGossipSelect(&s.other,&s.krennan,0,1001);check(s.controller.m_events.scheduled==1&&s.controller.broadcasts==1&&s.ai.talks==1,"two stale menus start once");s.controller.DoAction(1);check(s.controller.m_events.scheduled==1,"direct duplicate controller callback ignored");}
 for(int mode=0;mode<14;++mode){Scene s;if(mode==0)s.player.quest=0;if(mode==1)s.player.alive=false;if(mode==2)s.player.map=0;if(mode==3)s.krennan.phase=false;if(mode==4)s.krennan.distance=6;if(mode==5)actors.erase(2);if(mode==6)s.almyra.alive=false;if(mode==7)s.almyra.phase=false;if(mode==8)s.almyra.distance=50;if(mode==9)s.almyra.script=99;if(mode==10)actors.erase(3);if(mode==11)s.liam.alive=false;if(mode==12)s.controller.m_battleIsStarted=true;if(mode==13)s.krennan.alive=false;s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1001);check(!s.ai.m_battleIsStarted&&!s.controller.m_events.scheduled&&!s.ai.talks,"invalid stale gossip never reserves or starts scene");}
 {Scene s;s.gossip.OnGossipSelect(&s.player,&s.krennan,7,1001);s.gossip.OnGossipSelect(&s.player,&s.krennan,0,1002);check(!s.ai.m_battleIsStarted,"foreign sender and cancel ignored");s.ai.m_battleIsStarted=true;check(!s.ai.StartBattle(&s.player),"Krennan reservation independently blocks replay");}
 {Scene s;s.controller.prince=0;check(!s.ai.StartBattle(&s.player),"nearby but unregistered prince cannot start");s.controller.prince=3;check(s.ai.StartBattle(&s.player),"initialization retry available");}
 std::cout<<"Gilneas battle start: production gossip, gates and duplicate controller action PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
    for key,value in {
        'CONTROLLER_DATA':method(a,'        uint32 GetData('),
        'CONTROLLER_CASE':method(a,'                case ACTION_START_EVENT:'),
        'KRENNAN_ACTION':method(k,'        void DoAction('),
        'KRENNAN_GATE':method(k,'        bool CanStartBattle('),
        'KRENNAN_START':method(k,'        bool StartBattle('),
        'GOSSIP_SELECT':method(k,'    bool OnGossipSelect('),
    }.items():code=code.replace(key,value)
    with tempfile.TemporaryDirectory() as folder:
        cpp=Path(folder)/'start.cpp';exe=Path(folder)/'start.exe';cpp.write_text(code,'utf8')
        cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
        if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
        subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
