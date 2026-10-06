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
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr int POINT_MOTION_TYPE=1,QUEST_HUNT_FOR_SYLVANAS=24902,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2;
ENUM
struct Player{bool alive=true;int quest=1,map=654;float distance=5;int credits=0,events=0;bool IsAlive(){return alive;}int GetQuestStatus(int){return quest;}int GetMapId(){return map;}float GetDistance2d(void*){return distance;}void AreaExploredOrEventHappens(int){++events;}void KilledMonsterCredit(int){++credits;}};
struct Motion{int moves=0;void MovePoint(int,float,float,float){++moves;}};
struct Creature{bool phase=true;int map=654;Motion motion;void SetFacingTo(float){}bool IsInPhase(Player*){return phase;}int GetMapId(){return map;}Motion*GetMotionMaster(){return &motion;}};
std::map<int,Player*>players;std::map<int,Creature*>actors;namespace ObjectAccessor{Player*GetPlayer(Creature&,int g){auto i=players.find(g);return i==players.end()?nullptr:i->second;}Creature*GetCreature(Creature&,int g){auto i=actors.find(g);return i==actors.end()?nullptr:i->second;}}
struct Events{int starts=0,waits=0,despawns=0;void ScheduleEvent(int id,int){if(id==EVENT_START_TALK)++starts;if(id==EVENT_DESPAWN)++despawns;}void RescheduleEvent(int id,int){if(id==EVENT_END)++waits;}};
struct Sylvanas{Creature*me;Events m_events;bool m_dialogueStarted=false,m_completionHandled=false;int m_playerGUID=1,m_crenshawGUID=3;
MOVEMENT
void End(){switch(int(EVENT_END)){END_CASE}}
};
void check(bool ok,char const*m){if(!ok)throw std::runtime_error(m);}
struct Scene{Player owner,foreign;Creature sylvanas,crenshaw;Sylvanas ai;Scene(){ai.me=&sylvanas;players={{1,&owner},{2,&foreign}};actors={{3,&crenshaw}};}};
int main(){try{
 {Scene s;s.ai.MovementInform(1,2005);s.ai.MovementInform(1,2005);check(s.ai.m_events.starts==1,"dialogue arrival starts once");s.ai.End();s.ai.End();check(s.owner.events==1&&s.owner.credits==1&&!s.foreign.events&&s.ai.m_events.despawns==1,"final native event and compatible kill credit dispatch once to owner only");check(s.sylvanas.motion.moves==1&&s.crenshaw.motion.moves==1,"departure once");}
 for(int mode=0;mode<5;++mode){Scene s;if(mode==0)s.owner.quest=0;if(mode==1)s.owner.quest=3;if(mode==2)s.owner.alive=false;if(mode==3)s.owner.map=0;if(mode==4)s.sylvanas.phase=false;s.ai.End();check(!s.owner.events&&!s.ai.m_completionHandled,"invalid owner cannot finish scene");}
 {Scene s;s.owner.distance=51;s.ai.End();check(!s.owner.events&&s.ai.m_events.waits==1,"distant owner waits instead of remote credit");s.owner.distance=5;s.ai.End();check(s.owner.events==1,"returning owner can finish");}
 std::cout<<"Tobias final dialogue: actual owner event gate and duplicate protection PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 code=code.replace('ENUM',method(s,'    enum eNpc')+';').replace('MOVEMENT',method(s,'        void MovementInform(')).replace('END_CASE',method(s,'                    case EVENT_END:'))
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'dialogue.cpp';exe=Path(folder)/'dialogue.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
