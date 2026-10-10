"""Compile production rescue subclass and scoped attacker damage hook."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];full=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city1.cpp').read_text('utf8')
 horse=full[full.index('class npc_gilneas_rescue_horse_runtime'):full.index('class npc_king_greymanes_horse_35905')]
 worgen=full[full.index('class npc_bloodfang_worgen_35118'):]
 native=(root/'src/server/game/AI/SmartScripts/SmartScript.cpp').read_text('utf8')
 native=native[native.index('void SmartScript::ProcessEvent('):]
 gate=native[native.index('{')+1:native.index('    switch (e.GetEventType())')].replace('return;','return false;')
 code=r"""
#include <cstdint>
#include <vector>
#include <map>
#include <memory>
#include <algorithm>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int8=std::int8_t;
enum{NPC_KRENNAN_ARANAS=35907,NPC_BLOODFANG_WORGEN_35118=35118,NPC_GRAYMANE_HORSE_35905=35905,QUEST_SAVE_KRENNAN_ARANAS=14293,UNIT_FIELD_FLAGS=0,UNIT_FLAG_REMOVE_CLIENT_CONTROL=4,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1,WAYPOINT_MOTION_TYPE=2,TEMPSUMMON_TIMED_DESPAWN=1};
using DamageEffectType=int;
struct ObjectGuid{int id=0;explicit operator bool()const{return id!=0;}bool operator==(ObjectGuid o)const{return id==o.id;}};
struct Position{};struct Unit;struct Creature;struct Player;
struct TempSummon{Unit*owner=nullptr;Unit*GetSummoner(){return owner;}};
struct Unit{int entry=0;uint32 map=654;virtual~Unit()=default;virtual Player*ToPlayer(){return nullptr;}int GetEntry(){return entry;}uint32 GetMapId(){return map;}};
struct Player:Unit{ObjectGuid guid{1};Creature*vehicle=nullptr;bool alive=true,phase=true,control=true;int quest=3;uint32 health=200;Player*ToPlayer()override{return this;}ObjectGuid GetGUID(){return guid;}void SetClientControl(Creature*,bool b){control=b;}bool IsAlive(){return alive;}bool IsInPhase(Creature*){return phase;}Creature*GetVehicleBase(){return vehicle;}int GetQuestStatus(int){return quest;}uint32 GetMaxHealth(){return health;}};
struct Vehicle{int removed=0;void RemoveAllPassengers(){++removed;}};
struct AttackerAI{int attacks=0;Player*target=nullptr;void AttackStart(Player*p){++attacks;target=p;}};
struct SmartAI;std::map<int,Player*>players;
struct Creature:Unit{ObjectGuid guid{2};Vehicle kit;TempSummon*temp=nullptr;AttackerAI attackAI;SmartAI*smart=nullptr;int flags=0;void SetFlag(int,int f){flags|=f;}int despawns=0,spawns=0;std::vector<std::unique_ptr<Creature>>owned;Vehicle*GetVehicleKit(){return &kit;}TempSummon*ToTempSummon(){return temp;}AttackerAI*AI(){return &attackAI;}void DespawnOrUnsummon(int){++despawns;}Position GetFirstCollisionPosition(float,float){return {};}Creature*SummonCreature(int,Position,int,int);};
namespace ObjectAccessor{Player*GetPlayer(Creature&,ObjectGuid g){auto i=players.find(g.id);return i==players.end()?nullptr:i->second;}}
namespace PhasingHandler{void InheritPhaseShift(Unit*,Unit*){}}
struct SummonList:std::vector<Creature*>{explicit SummonList(Creature*){}void Summon(Creature*c){push_back(c);}void Despawn(Creature*c){erase(std::remove(begin(),end(),c),end());}void DespawnAll(){for(auto*c:*this)++c->despawns;clear();}};
struct SmartAI{Creature*me;int updates=0,boardings=0,pauses=0,resumes=0,movements=0,charms=0;uint32 pauseTime=0;explicit SmartAI(Creature*c):me(c){c->smart=this;}virtual~SmartAI()=default;virtual void OnCharmed(bool){++charms;}virtual void PassengerBoarded(Unit*,int8,bool){++boardings;}virtual void MovementInform(uint32,uint32){++movements;}virtual void JustSummoned(Creature*){}virtual void SummonedCreatureDespawn(Creature*){}virtual void UpdateAI(uint32){++updates;}void PausePath(uint32 t,bool){++pauses;pauseTime=t;}void ResumePath(){++resumes;}};
SOURCE
enum{SMART_EVENT_LINK=61,SMART_EVENT_FLAG_NOT_REPEATABLE=1,SMART_EVENT_FLAG_WHILE_CHARMED=512};
struct Holder{bool active=true,runOnce=false;struct{int event_phase_mask=0,event_flags=0;}event;int GetEventType(){return 27;}};
struct EventGate{void*me=nullptr;bool charmed=true;bool IsInPhase(int){return true;}bool IsCharmedCreature(void*){return charmed;}bool CanRun(Holder&e){GATE return true;}};
Creature*Creature::SummonCreature(int e,Position,int,int){++spawns;auto p=std::make_unique<Creature>();p->entry=e;auto*c=p.get();owned.push_back(std::move(p));smart->JustSummoned(c);return c;}
struct Worgen{Creature*me;DAMAGE};
void check(bool b,char const*m){if(!b)throw std::runtime_error(m);}
struct Scene{Player p;Creature horse,krennan;RescueAI ai;Scene():ai(&horse){horse.entry=35905;krennan.entry=35907;p.vehicle=&horse;players={{1,&p}};}void start(){ai.OnCharmed(true);ai.PassengerBoarded(&p,0,true);}};
int main(){
{EventGate gate;Holder event;check(!gate.CanRun(event),"native gate skips charmed passenger event");event.event.event_flags=513;check(gate.CanRun(event),"allow charmed boarding and retain no-repeat");event.runOnce=true;check(!gate.CanRun(event),"no-repeat retained");event.runOnce=false;event.event.event_flags=512;check(gate.CanRun(event),"allow charmed timed path and finish");gate.charmed=false;event.event.event_flags=0;check(gate.CanRun(event),"ordinary SmartAI unchanged");}
{Scene s;s.start();check((s.horse.flags&UNIT_FLAG_REMOVE_CLIENT_CONTROL)&&!s.p.control&&s.ai.charms==0&&s.ai.boardings==1,"native route remains AI controlled");s.ai.MovementInform(2,5);check(s.ai.pauses==0,"not before tree");s.ai.MovementInform(2,6);s.ai.MovementInform(2,6);check(s.ai.pauses==1&&s.ai.pauseTime==180000,"wait at tree once");s.ai.PassengerBoarded(&s.krennan,1,true);check(s.ai.resumes==1&&s.ai.m_rescued,"resume only after Krennan boards");s.ai.MovementInform(2,6);check(s.ai.pauses==1,"rescue cannot pause again");s.ai.UpdateAI(5000);check(s.horse.spawns==1&&s.horse.owned[0]->attackAI.target==&s.p,"owned attacker targets rider");s.ai.UpdateAI(8000);s.ai.UpdateAI(8000);check(s.horse.spawns==2,"bounded live attackers");s.ai.StopRide();s.ai.StopRide();check(s.horse.kit.removed==1&&s.horse.despawns==1,"cleanup once");for(auto const&c:s.horse.owned)check(c->despawns==1,"only tracked attackers removed");}
for(int mode=0;mode<7;++mode){Scene s;s.start();if(mode==0)s.p.alive=false;if(mode==1)s.p.vehicle=nullptr;if(mode==2)s.p.map=0;if(mode==3)s.p.phase=false;if(mode==4)s.p.quest=0;if(mode==5)players.clear();s.ai.UpdateAI(mode==6?180000:1);check(s.ai.m_stopped&&s.horse.despawns==1,"invalid ride owner cleanup");}
{Scene s;s.start();s.p.quest=1;s.ai.UpdateAI(1);check(!s.ai.m_stopped,"completed rescue still returns");}
{Scene s;s.start();Creature wolf;TempSummon summon{&s.horse};wolf.temp=&summon;Worgen ai{&wolf};uint32 d=100;ai.DamageDealt(&s.p,d,0);check(d==2,"scoped 1 percent damage cap");wolf.temp=nullptr;d=100;ai.DamageDealt(&s.p,d,0);check(d==100,"ordinary wolves unchanged");wolf.temp=&summon;s.p.vehicle=nullptr;d=100;ai.DamageDealt(&s.p,d,0);check(d==100,"outside ride unchanged");s.p.vehicle=&s.horse;d=0;ai.DamageDealt(&s.p,d,0);check(d==0,"zero damage stays zero");}
std::cout<<"PASS: production rescue control/tree/return, scoped attackers, damage and lifecycle\n";}
""".replace('GATE',gate).replace('SOURCE',method(horse,'    struct RescueAI')+';').replace('DAMAGE',method(worgen,'        void DamageDealt(').replace(' override',''))
 with tempfile.TemporaryDirectory() as directory:
  cpp=Path(directory)/'rescue.cpp';exe=Path(directory)/'rescue.exe';cpp.write_text(code,'utf8');flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
