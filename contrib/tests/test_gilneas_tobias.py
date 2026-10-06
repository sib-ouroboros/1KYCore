#!/usr/bin/env python3
"""Compile actual Tobias path validation, ownership and cleanup methods."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8');s=s[s.index('class npc_tobias_mistmantle_38507 :'):s.index('// 38530',s.index('class npc_tobias_mistmantle_38507 :'))];native=(root/'src/server/game/Movement/Waypoints/WaypointDefines.h').read_text('utf8')
 code=r'''
#include <cstdint>
#include <cmath>
#include <vector>
#include <map>
#include <limits>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint8=std::uint8_t;
constexpr int QUEST_HUNT_FOR_SYLVANAS=24902,QUEST_STATUS_INCOMPLETE=1,QUEST_STATUS_COMPLETE=2,WAYPOINT_MOVE_TYPE_RUN=1,WAYPOINT_MOVE_TYPE_WALK=0,POINT_MOTION_TYPE=1,WAYPOINT_MOTION_TYPE=2,EFFECT_MOTION_TYPE=3,TEMPSUMMON_MANUAL_DESPAWN=8;
PRODUCTION_ENUM
struct Position{float x,y,z,o;};
PRODUCTION_ROUTE
struct ObjectGuid{int id=0;bool IsEmpty()const{return !id;}static ObjectGuid const Empty;bool operator==(ObjectGuid o)const{return id==o.id;}};ObjectGuid const ObjectGuid::Empty{};
NATIVE_TYPES
struct Manager{std::map<uint32,WaypointPath>paths;WaypointPath const*GetPath(uint32 id){auto i=paths.find(id);return i==paths.end()?nullptr:&i->second;}}manager;auto*sWaypointMgr=&manager;
struct Player;struct Unit{virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}};
struct Player:Unit{int quest=1;bool alive=true;float distance=5;uint32 map=654;ObjectGuid guid{1};Player*ToPlayer()override{return this;}bool IsAlive(){return alive;}uint32 GetMapId(){return map;}ObjectGuid GetGUID(){return guid;}int GetQuestStatus(int){return quest;}float GetDistance2d(void*){return distance;}};
struct TempSummon{int type=0;uint32 expiry=0;void SetTempSummonType(int t){type=t;}void UnSummon(uint32 time){expiry=time;}};
struct Motion{int clears=0,jumps=0,moves=0;uint32 lastPoint=0;Position last{};void Clear(){++clears;}void MovePoint(uint32 id,Position p){++moves;lastPoint=id;last=p;}void MoveJump(float,float,float,float,float,int){++jumps;}};struct Creature{uint32 map=654;bool phase=true,summon=false;int despawns=0;Motion motion;TempSummon timer;TempSummon*ToTempSummon(){return &timer;}bool IsSummon(){return summon;}void SetWalk(bool){}void SetFacingTo(float){}uint32 GetMapId(){return map;}bool IsInPhase(Player*){return phase;}Motion*GetMotionMaster(){return &motion;}void DespawnOrUnsummon(){++despawns;}};
std::map<int,Player*>players;std::map<int,Creature*>actors;
namespace ObjectAccessor{Player*GetPlayer(Creature&,ObjectGuid g){auto i=players.find(g.id);return i==players.end()?nullptr:i->second;}Creature*GetCreature(Creature&,ObjectGuid g){auto i=actors.find(g.id);return i==actors.end()?nullptr:i->second;}}
struct Events{int scheduled=0,resets=0;void Reset(){scheduled=0;++resets;}void RescheduleEvent(int,int){++scheduled;}};
int logs=0;
#define TC_LOG_ERROR(...) ++logs
struct Tobias{Tobias()=default;explicit Tobias(Creature*c):me(c){}Creature*me;Events m_events;ObjectGuid m_playerGUID,m_sylvanasGUID,m_warhowlGUID,m_crenshawGUID;uint32 m_eventPhase=0,m_lifetime=0,m_walkPoint=0;bool m_stopped=false,m_walkingRoute=false,m_walkMoving=false,m_sceneActorsSpawned=false;int talks=0;void Talk(int,Player*){++talks;}METHODS};
using CreatureAI=Tobias;struct Factory{using npc_tobias_mistmantle_38507AI=Tobias;FACTORY};
void check(bool ok,char const*m){if(!ok)throw std::runtime_error(m);}
struct Scene{Player p,other;Creature tobias,one,two,three;Tobias ai;Scene(){ai.me=&tobias;other.guid={2};players={{1,&p},{2,&other}};actors={{3,&one},{4,&two},{5,&three}};manager.paths.clear();uint32 end[]={1,1,3,5,23};for(uint32 i=0;i<5;++i){WaypointPath path;path.nodes={WaypointNode{0,1,2,3},WaypointNode{end[i],4,5,6}};manager.paths[3850701+i]=path;}}void start(){ai.IsSummonedBy(&p);ai.m_sylvanasGUID={3};ai.m_warhowlGUID={4};ai.m_crenshawGUID={5};}};
int main(){try{
 {Scene s;s.start();s.ai.IsSummonedBy(&s.other);check(s.ai.m_playerGUID==s.p.guid&&s.ai.m_events.scheduled==1,"owner cannot be replaced or start duplicated");check(s.tobias.timer.expiry==600000&&s.tobias.timer.type==TEMPSUMMON_MANUAL_DESPAWN,"native summon timer does not remove escort before dialogue");check(s.ai.UpdateSceneOwner(599999),"valid owner before bounded timeout");check(!s.ai.UpdateSceneOwner(1)&&s.tobias.despawns==1&&s.one.despawns==1&&s.two.despawns==1&&s.three.despawns==1,"timeout clears tracked scene actors");s.ai.StopScene();check(s.one.despawns==1,"cleanup once");}
 for(int mode=0;mode<6;++mode){Scene s;s.start();if(mode==0)s.p.quest=0;if(mode==1)s.p.alive=false;if(mode==2)s.p.map=0;if(mode==3)s.tobias.phase=false;if(mode==4)players.erase(1);if(mode==5)s.ai.Reset();check(!s.ai.UpdateSceneOwner(1000)&&s.ai.m_events.scheduled==0&&s.tobias.despawns==1,"cancel death map phase logout reset cleanup");}
 {Scene s;s.p.quest=2;s.start();check(s.ai.m_playerGUID==s.p.guid&&!s.ai.m_stopped,"native COMPLETE status before accept hook still initializes escort");check(s.ai.UpdateSceneOwner(1000),"completed scene remains until reward or timeout");s.p.quest=3;check(!s.ai.UpdateSceneOwner(1000),"reward cleans own scene");}
 for(int mode=0;mode<3;++mode){Scene s;if(mode==0)manager.paths.erase(3850703);if(mode==1)manager.paths[3850705].nodes.back().id=22;if(mode==2)manager.paths[3850702].nodes.back().x=std::numeric_limits<float>::quiet_NaN();s.ai.IsSummonedBy(&s.p);check(!s.ai.m_stopped&&s.ai.m_playerGUID==s.p.guid&&s.ai.m_walkingRoute,"missing invalid or incompatible legacy route uses verified walking route");}
 {Scene s;manager.paths.clear();s.start();s.p.distance=21;s.ai.StartWalkingPoint();check(!s.tobias.motion.moves,"escort waits for owner");s.p.distance=5;for(uint32 i=0;i<11;++i){s.ai.StartWalkingPoint();check(s.ai.m_walkMoving&&s.tobias.motion.lastPoint==3000+i,"walk step starts");check(s.tobias.motion.last.x==TobiasWalkingRoute[i].x&&s.tobias.motion.last.z==TobiasWalkingRoute[i].z,"native source coordinates retained");s.ai.StartWalkingPoint();s.ai.MovementInform(POINT_MOTION_TYPE,4000+i);check(s.ai.m_walkPoint==i,"wrong callback cannot advance");s.ai.MovementInform(POINT_MOTION_TYPE,3000+i);s.ai.MovementInform(POINT_MOTION_TYPE,3000+i);check(s.ai.m_walkPoint==i+1,"arrival advances once");}check(s.tobias.motion.moves==11&&s.tobias.motion.jumps==1&&s.ai.m_eventPhase==5&&s.ai.talks==4,"full escort reaches native hiding jump with four dialogue lines");s.ai.MovementInform(EFFECT_MOTION_TYPE,2004);check(s.ai.m_events.scheduled>=2,"native hiding callback schedules original scene");}
 {Scene s;Unit npc;s.ai.IsSummonedBy(&npc);check(s.ai.m_stopped,"non-player owner rejected");}
 {Factory factory;Creature c;check(!factory.GetAI(&c),"persistent NPC uses native default AI");c.summon=true;c.map=0;check(!factory.GetAI(&c),"other maps preserve default AI");c.map=654;auto*ai=factory.GetAI(&c);check(ai!=nullptr,"Gilneas summon receives scene AI");delete ai;}
 std::cout<<"Tobias production owner lifecycle, native waypoint validation and cleanup PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 full=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
 code=code.replace('PRODUCTION_ENUM',method(s,'    enum eNpc')+';').replace('PRODUCTION_ROUTE',method(full,'Position const TobiasWalkingRoute[]')+';').replace('NATIVE_TYPES',method(native,'struct WaypointNode')+';\n'+method(native,'struct WaypointPath')+';').replace('METHODS','\n'.join(method(s,marker) for marker in ['        void Reset(','        bool HasScenePaths(','        void StopScene(','        bool UpdateSceneOwner(','        void IsSummonedBy(','        bool IsPlayerNear(','        void StartWalkingPoint(','        void MovementInform('])).replace('FACTORY',method(s,'    CreatureAI* GetAI('))
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'tobias.cpp';exe=Path(folder)/'tobias.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
