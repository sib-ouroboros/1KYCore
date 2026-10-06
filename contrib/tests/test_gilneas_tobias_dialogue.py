#!/usr/bin/env python3
"""Compile actual dialogue-start and final event cases; only the owner earns completion."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8');s=s[s.index('class npc_lady_sylvanas_windrunner_38530 :'):s.index('// 38540',s.index('class npc_lady_sylvanas_windrunner_38530 :'))]
 code=r'''
#include <cstdint>
#include <map>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr int POINT_MOTION_TYPE=1,QUEST_HUNT_FOR_SYLVANAS=24902,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2,NPC_TOBIAS_MISTMANTLE=38507,PLAYER_GUID=100,NPC_GENERAL_WARHOWL=38533,NPC_HIGH_EXECUTOR_CRENSHAW=38537;
ENUM
struct ObjectGuid{static constexpr int Empty=0;};
struct Player{bool alive=true;int quest=1,map=654;float distance=5;int credits=0,events=0;int GetGUID(){return 1;}bool IsAlive(){return alive;}int GetQuestStatus(int){return quest;}int GetMapId(){return map;}float GetDistance2d(void*){return distance;}void AreaExploredOrEventHappens(int){++events;}void KilledMonsterCredit(int){++credits;}};
struct Motion{int moves=0;void MovePoint(int,float,float,float){++moves;}};
struct ActorAI{int owner=1;std::vector<int>talks;void Talk(int n){talks.push_back(n);}int GetGUID(int id){return id==PLAYER_GUID?owner:(id==NPC_GENERAL_WARHOWL?5:3);}};
struct Creature{ActorAI ai;bool alive=true;int entry=38507;bool IsAlive(){return alive;}int GetEntry(){return entry;}ActorAI*AI(){return &ai;}bool phase=true;int map=654;int despawns=0;Motion motion;void DespawnOrUnsummon(int){++despawns;}void SetFacingToObject(Creature*){}void SetFacingTo(float){}bool IsInPhase(Player*){return phase;}int GetMapId(){return map;}Motion*GetMotionMaster(){return &motion;}};
std::map<int,Player*>players;std::map<int,Creature*>actors;namespace ObjectAccessor{Player*GetPlayer(Creature&,int g){auto i=players.find(g);return i==players.end()?nullptr:i->second;}Creature*GetCreature(Creature&,int g){auto i=actors.find(g);return i==actors.end()?nullptr:i->second;}}
struct Events{int starts=0,waits=0,despawns=0;int now=0;std::multimap<int,int>queue;void Update(int d){now+=d;}int ExecuteEvent(){if(queue.empty()||queue.begin()->first>now)return 0;int id=queue.begin()->second;queue.erase(queue.begin());return id;}void Reset(){starts=waits=despawns=now=0;queue.clear();}void ScheduleEvent(int id,int delay){queue.emplace(now+delay,id);if(id==EVENT_START_TALK)++starts;if(id==EVENT_DESPAWN)++despawns;}void RescheduleEvent(int id,int delay){for(auto it=queue.begin();it!=queue.end();)if(it->second==id)it=queue.erase(it);else++it;queue.emplace(now+delay,id);if(id==EVENT_END)++waits;}};
struct Sylvanas{Creature*me;Events m_events;bool m_dialogueStarted=false,m_completionHandled=false;int m_playerGUID=1,m_crenshawGUID=3,m_tobiasGUID=4,m_sylvanasGUID=0,m_warhowlGUID=0;
void Talk(int n){me->ai.Talk(n);}bool UpdateVictim(){return false;}void DoMeleeAttackIfReady(){}
UPDATE
RESET
MOVEMENT
void End(){switch(int(EVENT_END)){END_CASE}}
};
void check(bool ok,char const*m){if(!ok)throw std::runtime_error(m);}
struct Scene{Player owner,foreign;Creature sylvanas,crenshaw,tobias,warhowl;Sylvanas ai;Scene(){ai.me=&sylvanas;players={{1,&owner},{2,&foreign}};actors={{3,&crenshaw},{4,&tobias},{5,&warhowl}};}};
int main(){try{
 {Scene s;s.ai.MovementInform(1,2005);s.ai.MovementInform(1,2005);for(int i=0;i<74;++i)s.ai.UpdateAI(1000);check(!s.owner.events,"whole dialogue cannot complete early");s.ai.UpdateAI(1000);check(s.owner.events==1&&s.owner.credits==1&&!s.foreign.events,"actual complete conversation awards once to owner");check(s.warhowl.ai.talks==std::vector<int>({0,1,2})&&s.sylvanas.ai.talks==std::vector<int>({0,1,2,3})&&s.crenshaw.ai.talks==std::vector<int>({0}),"all eight native dialogue groups run in order per actor");check(s.warhowl.despawns==1&&!s.sylvanas.despawns,"Warhowl leaves before final cleanup");for(int i=0;i<8;++i)s.ai.UpdateAI(1000);check(s.tobias.despawns==1&&s.crenshaw.despawns==1&&s.sylvanas.despawns==1&&s.ai.m_events.queue.empty(),"final cleanup after native eight-second departure");}
 {Scene s;s.ai.MovementInform(1,2005);s.ai.UpdateAI(1000);s.ai.Reset();s.ai.UpdateAI(100000);check(!s.owner.events&&s.ai.m_events.queue.empty(),"reset cancels the whole scheduled chain");}

 {Scene s;s.ai.MovementInform(1,2005);s.ai.MovementInform(1,2005);check(s.ai.m_events.starts==1,"dialogue arrival starts once");s.ai.End();s.ai.End();check(s.owner.events==1&&s.owner.credits==1&&!s.foreign.events&&s.ai.m_events.despawns==1,"final native event and compatible kill credit dispatch once to owner only");check(s.sylvanas.motion.moves==1&&s.crenshaw.motion.moves==1,"departure once");}
 for(int mode=0;mode<5;++mode){Scene s;if(mode==0)s.owner.quest=0;if(mode==1)s.owner.quest=3;if(mode==2)s.owner.alive=false;if(mode==3)s.owner.map=0;if(mode==4)s.sylvanas.phase=false;s.ai.End();check(!s.owner.events&&!s.ai.m_completionHandled,"invalid owner cannot finish scene");}
 {Scene s;s.ai.MovementInform(1,2005);s.ai.Reset();check(!s.ai.m_events.starts&&!s.ai.m_dialogueStarted&&!s.ai.m_completionHandled&&!s.ai.m_playerGUID&&!s.ai.m_tobiasGUID,"reset clears old events and actor ownership");s.ai.End();check(!s.owner.events,"reset scene cannot issue delayed completion");}
 for(int mode=0;mode<6;++mode){Scene s;if(mode==0)actors.erase(4);if(mode==1)s.tobias.alive=false;if(mode==2)s.tobias.map=0;if(mode==3)s.tobias.phase=false;if(mode==4)s.tobias.entry=1;if(mode==5)s.tobias.ai.owner=2;s.ai.End();check(!s.owner.events&&!s.owner.credits&&!s.ai.m_completionHandled,"missing dead foreign map phase entry or owner Tobias cannot complete");}
 {Scene s;s.owner.distance=51;s.ai.End();check(!s.owner.events&&s.ai.m_events.waits==1,"distant owner waits instead of remote credit");s.owner.distance=5;s.ai.End();check(s.owner.events==1,"returning owner can finish");}
 std::cout<<"Tobias final dialogue: actual owner event gate and duplicate protection PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 code=code.replace('ENUM',method(s,'    enum eNpc')+';').replace('UPDATE',method(s,'        void UpdateAI(')).replace('RESET',method(s,'        void Reset(')).replace('MOVEMENT',method(s,'        void MovementInform(')).replace('END_CASE',method(s,'                    case EVENT_END:'))
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'dialogue.cpp';exe=Path(folder)/'dialogue.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
