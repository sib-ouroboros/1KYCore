import os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
s=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
code='''#include <set>
#include <stdexcept>
#include <iostream>
using QuestStatus=int;
enum{QUEST_ENDGAME=26706,QUEST_STATUS_NONE=0,QUEST_STATUS_COMPLETE=1,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_REWARDED=6};
struct Shift{std::set<int> phases{184,189};bool HasPhase(int id){return phases.count(id);}};
struct Player{int map=654,status=3;Shift shift;int GetMapId(){return map;}int GetQuestStatus(int){return status;}Shift&GetPhaseShift(){return shift;}};
namespace PhasingHandler{void AddPhase(Player*p,int id,bool){p->shift.phases.insert(id);}void RemovePhase(Player*p,int id,bool){p->shift.phases.erase(id);}}
struct Phase{
'''+method(s[s.index('class player_gilneas_endgame_phase'):],'    static void Synchronize(')+''' }; 
void check(bool v){if(!v)throw std::runtime_error("Endgame phase lifecycle failure");}
int main(){Player p;Phase::Synchronize(&p);check(p.shift.phases==std::set<int>({184,189,191}));Phase::Synchronize(&p);check(p.shift.phases.size()==3);
p.status=1;Phase::Synchronize(&p);check(p.shift.HasPhase(191));p.map=1;Phase::Synchronize(&p);check(p.shift.phases==std::set<int>({184,189}));p.map=654;Phase::Synchronize(&p);check(p.shift.HasPhase(191));p.status=6;Phase::Synchronize(&p,true);check(!p.shift.HasPhase(191));p.status=3;Phase::Synchronize(&p);p.status=0;Phase::Synchronize(&p,true);check(!p.shift.HasPhase(191));p.shift.phases.insert(191);Phase::Synchronize(&p);check(p.shift.HasPhase(191));std::cout<<"PASS: native Endgame phase add/complete/reward/abandon/map/relogin synchronization, original phases preserved\\n";}
'''
with tempfile.TemporaryDirectory() as t:
 cpp=Path(t)/'p.cpp';exe=Path(t)/'p.exe';cpp.write_text(code,'utf8');subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
