#!/usr/bin/env python3
"""Production Lorna follower setup survives partial summons and stale helper GUIDs."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();r=Path(__file__).resolve().parents[2]
 s=(r/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8');s=s[s.index('class npc_lorna_crowley_38426 :'):s.index('class npc_lord_darius_crowley_38415 :')]
 code=r'''
#include <cstdint>
#include <list>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using ObjectGuid=int;
constexpr int MOVE_RUN=1,NPC_LEADER_GUID=99994;
float frand(float a,float){return a;}
struct Creature;
struct Motion{Creature*follow=nullptr;float distance=0,angle=0;void MoveFollow(Creature*c,float d,float a){follow=c;distance=d;angle=a;}};
struct AI{int leader=0;void SetGUID(int guid,int){leader=guid;}};
struct Creature{int guid=0;bool walking=true;float speed=0;Motion motion;struct AI ai;int GetGUID(){return guid;}void SetWalk(bool b){walking=b;}void SetSpeed(int,float f){speed=f/7.0f;}void SetSpeedRate(int,float f){speed=f;}float GetSpeed(int)const{return speed*7.0f;}Motion*GetMotionMaster(){return &motion;}struct AI*AI(){return &ai;}};
std::map<int,Creature*>actors;namespace ObjectAccessor{Creature*GetCreature(Creature&,int guid){auto i=actors.find(guid);return i==actors.end()?nullptr:i->second;}}
struct Lorna{Creature*me;std::list<int>my_cannonList,my_cannonerList,my_followerList;BUILD};
void check(bool ok,char const*msg){if(!ok)throw std::runtime_error(msg);}
int main(){try{Creature lorna,c1,c2,c3,h[6],militia;
 Lorna ai;ai.me=&lorna;lorna.guid=100;actors={{1,&c1},{2,&c2},{3,&c3},{20,&militia}};for(int i=0;i<6;++i)actors[10+i]=&h[i];ai.my_cannonList={1,2,3};ai.my_cannonerList={10,11,12,13,14,15};ai.my_followerList={20};ai.BuildFollowerGroup();
 check(c1.motion.follow==&lorna&&c2.motion.follow==&lorna&&c3.motion.follow==&lorna&&c1.motion.distance==2&&c2.motion.distance==2&&c3.motion.distance==4,"three native cannon offsets preserved");
 for(Creature*actor:{&c1,&c2,&c3,&militia})check(!actor->walking&&actor->GetSpeed(MOVE_RUN)>8.39f&&actor->GetSpeed(MOVE_RUN)<8.41f,"all cannons and militia use actual run velocity");
 for(int i=0;i<6;++i){check(h[i].motion.follow==(i<2?&c1:i<4?&c2:&c3)&&h[i].speed==1.2f&&h[i].GetSpeed(MOVE_RUN)>8.39f&&h[i].GetSpeed(MOVE_RUN)<8.41f&&!h[i].walking,"each helper pairs with its own cannon and runs");}check(militia.motion.follow==&lorna&&militia.ai.leader==100,"militia follows and records native leader");
 for(int i=0;i<6;++i){h[i].motion.follow=nullptr;}actors.erase(10);ai.BuildFollowerGroup();check(h[1].motion.follow==&c1&&h[2].motion.follow==&c2&&h[3].motion.follow==&c2&&h[4].motion.follow==&c3,"missing first helper never shifts later pairs");
 ai.my_cannonList={1};ai.my_cannonerList={11};militia.motion.follow=nullptr;ai.BuildFollowerGroup();check(militia.motion.follow==&lorna&&h[1].motion.follow==&c1,"partial artillery still moves remaining cannon and militia");
 ai.my_cannonList.clear();ai.my_cannonerList.clear();militia.motion.follow=nullptr;ai.BuildFollowerGroup();check(militia.motion.follow==&lorna,"missing guns do not immobilize infantry");
 std::cout<<"PASS: native artillery offsets, stable helper pairing and movement after partial summons\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''.replace('BUILD',method(s,'        void BuildFollowerGroup('))
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'artillery.cpp';exe=Path(tmp)/'artillery.exe';cpp.write_text(code,'utf8');flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
