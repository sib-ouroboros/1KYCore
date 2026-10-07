#!/usr/bin/env python3
"""Compile production Genn/Godfrey handlers and actual waypoint structures."""
import argparse,os,subprocess,tempfile,json
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 waypoint=(root/'src/server/game/Movement/Waypoints/WaypointDefines.h').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <map>
#include <vector>
#include <memory>
#include <limits>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint64=std::uint64_t;using uint8=std::uint8_t;using int32=std::int32_t;using namespace std::chrono_literals;
constexpr uint32 WAYPOINT_MOTION_TYPE=2,WAYPOINT_MOVE_TYPE_WALK=0,WAYPOINT_MOVE_TYPE_RUN=1;
struct ObjectGuid{int id=0;bool IsEmpty()const{return !id;}static ObjectGuid const Empty;};ObjectGuid const ObjectGuid::Empty{};
struct PhaseShift{};struct Creature;struct Player;struct CreatureAI;
struct Unit{uint32 map=654,entry=0;ObjectGuid guid;bool alive=true;Player*controller=nullptr;virtual~Unit()=default;virtual Creature*ToCreature(){return nullptr;}virtual Player*ToPlayer(){return nullptr;}uint32 GetEntry()const{return entry;}uint32 GetMapId()const{return map;}ObjectGuid GetGUID()const{return guid;}bool IsAlive()const{return alive;}Player*GetCharmerOrOwnerPlayerOrPlayerItself(){return controller;}PhaseShift const&GetPhaseShift()const{static PhaseShift p;return p;}};
struct MotionMaster{int starts=0,clears=0,idles=0;uint32 path=0;bool repeat=true;void MovePath(uint32 p,bool r){path=p;repeat=r;++starts;}void Clear(){++clears;}void MoveIdle(){++idles;}};
struct Creature:Unit{CreatureAI*ai=nullptr;Creature*nearest=nullptr;MotionMaster motion;uint64 spawn=802361;uint32 script=7;bool phase=true,summon=false,gravityDisabled=false,despawn=false;int talks=0,stops=0;Creature*ToCreature()override{return this;}CreatureAI*AI(){return ai;}uint64 GetSpawnId()const{return spawn;}uint32 GetScriptId()const{return script;}bool IsSummon()const{return summon;}bool InSamePhase(PhaseShift const&)const{return phase;}Creature*FindNearestCreature(uint32,float){return nearest;}MotionMaster*GetMotionMaster(){return &motion;}void StopMoving(){++stops;}template<class T>void DespawnOrUnsummon(T){despawn=true;}};
struct Player:Unit{int casts=0,removed=0;Player*ToPlayer()override{return this;}void CastSpell(Unit*,uint32,bool=false){++casts;}void RemoveAura(uint32){++removed;}};
struct Quest{uint32 id;uint32 GetQuestId()const{return id;}};
struct CreatureAI{Creature*me;explicit CreatureAI(Creature*c):me(c){c->ai=this;}virtual~CreatureAI()=default;virtual void Reset(){}virtual void JustDied(Unit*){}virtual void SetGUID(ObjectGuid,int32){}virtual uint32 GetData(uint32)const{return 0;}virtual void DoAction(int32){}virtual void MovementInform(uint32,uint32){}virtual void UpdateAI(uint32){}virtual void DamageTaken(Unit*,uint32&){}void Talk(uint32){++me->talks;}};
struct ScriptedAI:CreatureAI{using CreatureAI::CreatureAI;bool UpdateVictim(){return false;}void DoMeleeAttackIfReady(){}};
struct CreatureScript{explicit CreatureScript(char const*){}virtual~CreatureScript()=default;virtual CreatureAI*GetAI(Creature*)const{return nullptr;}virtual bool OnQuestReward(Player*,Creature*,Quest const*,uint32){return false;}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Reset(){now=0;events.clear();}void Update(uint32 d){now+=d;}template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
std::map<int,Creature*>actors;struct ObjectAccessor{static Creature*GetCreature(Creature&,ObjectGuid id){auto i=actors.find(id.id);return i==actors.end()?nullptr:i->second;}};
struct ObjectMgr{uint32 id=7;uint32 GetScriptId(char const*)const{return id;}}objectMgr;auto*sObjectMgr=&objectMgr;
struct TextMgr{bool exists=false;bool TextExist(uint32,uint8)const{return exists;}}textMgr;auto*sCreatureTextMgr=&textMgr;
int logs=0;
#define TC_LOG_ERROR(...) (++logs)
'''
 code+=method(waypoint,'struct WaypointNode')+';\n'+method(waypoint,'struct WaypointPath')+';\n'
 code+=r'''
struct WaypointMgr{std::map<uint32,WaypointPath>paths;WaypointPath const*GetPath(uint32 id)const{auto i=paths.find(id);return i==paths.end()?nullptr:&i->second;}}waypointMgr;auto*sWaypointMgr=&waypointMgr;
'''
 code+=method(source,'enum eDuskHaven')+';\n'+method((root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas.h').read_text('utf8'),'enum Events')+';\n'
 code+=source[source.index('// Godfrey owns'):source.index('// 38764')]
 code+=r'''
using F=npc_gilneas_godfrey_departure::ai;using G=npc_king_genn_greymane_37876::npc_king_genn_greymane_37876AI;
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
struct Scene{Creature genn,godfrey;F f;G g;Scene():f(&godfrey),g(&genn){actors.clear();waypointMgr.paths.clear();objectMgr.id=7;textMgr.exists=false;genn.entry=37876;godfrey.entry=37875;genn.guid.id=1;godfrey.guid.id=2;genn.nearest=&godfrey;actors[1]=&genn;actors[2]=&godfrey;f.Reset();g.Reset();}void path(){std::vector<WaypointNode>nodes;SOURCE_ROUTE_NODESwaypointMgr.paths.emplace(802361,WaypointPath(802361,std::move(nodes)));}void tick(uint32 diff){g.UpdateAI(diff);f.UpdateAI(diff);}void dialogue(){g.DoAction(1);tick(100);tick(100);tick(5000);tick(3000);}};
int main(){try{
 {Scene s;s.dialogue();check(!s.g.m_sceneStarted&&!s.f.m_running&&!s.f.GetData(1)&&!s.godfrey.motion.starts&&!s.godfrey.gravityDisabled&&!s.godfrey.despawn,"missing route releases reservation without flight or fake departure");int count=logs;s.dialogue();check(logs==count,"missing route logged once per actor");check(s.genn.talks==2&&s.godfrey.talks==0,"known Genn dialogue retained; missing Godfrey text not requested");}
 {Scene s;s.path();textMgr.exists=true;s.g.DoAction(1);s.g.DoAction(1);check(s.g.m_events.events.size()==1&&s.f.GetData(1)==1,"scene and actor reserved once");s.tick(100);s.tick(100);s.tick(5000);s.tick(3000);check(s.f.m_running&&s.godfrey.motion.starts==1&&s.godfrey.motion.path==802361&&!s.godfrey.motion.repeat&&!s.godfrey.gravityDisabled&&s.godfrey.talks==1,"existing captured endpoint path starts only on Godfrey");s.g.MovementInform(WAYPOINT_MOTION_TYPE,4);check(!s.godfrey.despawn,"Genn callback cannot end Godfrey movement");s.f.MovementInform(999,4);s.f.MovementInform(WAYPOINT_MOTION_TYPE,3);check(!s.godfrey.despawn,"wrong motion and intermediate point ignored");s.f.MovementInform(WAYPOINT_MOTION_TYPE,4);check(s.godfrey.despawn&&s.f.m_finished&&!s.g.m_sceneStarted&&s.g.m_events.events.empty(),"own endpoint ends scene");s.g.DoAction(1);check(!s.g.m_sceneStarted,"departed actor cannot restart before respawn");s.f.Reset();check(!s.f.GetData(1),"respawn resets departure state");}
 for(int mode=0;mode<4;++mode){Scene s;s.path();if(mode==0)waypointMgr.paths[802361].nodes.clear();if(mode==1)waypointMgr.paths[802361].nodes.resize(1);if(mode==2)waypointMgr.paths[802361].nodes.back().id=99;if(mode==3)waypointMgr.paths[802361].nodes[1].x=std::numeric_limits<float>::quiet_NaN();s.dialogue();check(!s.godfrey.motion.starts&&!s.godfrey.gravityDisabled&&!s.f.GetData(1),"empty/short/incomplete/nonfinite route rejected");}
 {Scene s;s.godfrey.spawn=uint64(std::numeric_limits<uint32>::max())+1;s.dialogue();check(!s.godfrey.motion.starts&&!s.f.GetData(1),"64-bit spawn ID cannot truncate into another route");}
 for(int mode=0;mode<5;++mode){Scene s;s.path();s.dialogue();if(mode==0)actors.erase(1);if(mode==1)s.genn.alive=false;if(mode==2)s.genn.map=0;if(mode==3)s.godfrey.phase=false;s.f.UpdateAI(mode==4?60000:1);check(!s.f.GetData(1)&&!s.f.m_running&&s.godfrey.motion.clears==1&&s.godfrey.motion.idles==1&&s.godfrey.stops==1&&!s.godfrey.despawn,"lost owner/death/map/phase/watchdog cancels without fake completion");}
 {Scene s;s.path();s.dialogue();s.g.Reset();check(!s.f.m_running&&!s.f.GetData(1)&&s.g.m_events.events.empty(),"Genn reset cancels own departure");}
 {Scene s;s.path();s.g.DoAction(1);actors.erase(2);s.g.UpdateAI(1000);check(!s.g.m_sceneStarted&&s.g.m_events.events.empty(),"lost Godfrey cannot permanently lock Genn");}
 {Scene s;s.path();s.dialogue();s.f.JustDied(nullptr);check(s.f.m_finished&&!s.g.m_sceneStarted,"actual death releases controller");}
 {Scene s;s.path();Creature otherGenn;otherGenn.guid.id=3;otherGenn.entry=37876;otherGenn.nearest=&s.godfrey;actors[3]=&otherGenn;G other(&otherGenn);other.Reset();s.g.DoAction(1);other.DoAction(1);check(!other.m_sceneStarted&&s.f.m_gennGUID.id==1,"another controller cannot steal actor reservation");}
 for(int mode=0;mode<4;++mode){Scene s;if(mode==0)s.genn.phase=false;if(mode==1)s.godfrey.map=0;if(mode==2)s.godfrey.summon=true;if(mode==3)s.genn.entry=1;s.g.DoAction(1);check(!s.g.m_sceneStarted&&!s.f.GetData(1),"foreign map/phase/temporary actor/controller cannot reserve scene");}
 {Scene s;s.path();s.dialogue();s.genn.script=99;s.f.UpdateAI(1);check(!s.f.m_running&&!s.f.GetData(1)&&s.g.m_sceneStarted,"changed controller script cancels movement without calling foreign AI");}
 {Scene s;s.path();s.dialogue();s.genn.entry=1;s.f.UpdateAI(1);check(!s.f.m_running&&!s.f.GetData(1)&&s.g.m_sceneStarted,"changed controller entry cancels without foreign notification");}
 {Scene s;objectMgr.id=0;s.godfrey.script=0;s.g.DoAction(1);check(!s.g.m_sceneStarted&&!s.f.GetData(1),"missing SQL binding ID0 is rejected");objectMgr.id=7;s.godfrey.script=99;s.g.DoAction(1);check(!s.g.m_sceneStarted,"foreign custom AI untouched");}
 {Scene s;s.genn.map=0;s.g.DoAction(1);check(!s.g.m_sceneStarted,"other map does not start scene");npc_gilneas_godfrey_departure factory;s.godfrey.map=0;check(!factory.GetAI(&s.godfrey),"outside Gilneas default AI preserved");s.godfrey.map=654;s.godfrey.summon=true;check(!factory.GetAI(&s.godfrey),"other temporary Godfrey actors untouched");}
 {Scene s;Player player;npc_king_genn_greymane_37876 script;Quest unrelated{1},quest{24592};script.OnQuestReward(&player,&s.genn,&unrelated,0);check(!player.casts&&!player.removed,"other rewards unchanged");script.OnQuestReward(&player,&s.genn,&quest,0);check(player.casts==1&&player.removed==1,"native reaction and stealth removal preserved");}
 std::cout<<"Godfrey native path guard, actor callback, reservation and controller cleanup: PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 manifest=json.loads((root/'docs/audit-data/gilneas-battle-source-restoration.json').read_text('utf8'))
 nodes=manifest['godfrey_route']['points']
 assert [p['point'] for p in nodes]==[0,1,2,3,4]
 code=code.replace('SOURCE_ROUTE_NODES',''.join('nodes.emplace_back('+str(p['point'])+','+','.join(str(v)+'f' for v in p['position'])+');nodes.back().moveType='+str(p['move_type'])+';' for p in nodes))
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
