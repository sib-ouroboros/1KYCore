"""Run the native Endgame summon cast gate, including stale/GM click prevention."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
s=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
code=r'''
#include <stdexcept>
#include <iostream>
using SpellCastResult=int;
enum{QUEST_ENDGAME=26706,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_NONE=0,SPELL_FAILED_BAD_TARGETS=1,SPELL_FAILED_NOT_READY=2,SPELL_CAST_OK=0,NPC_TOBIAS_MISTMANTLE_43749=43749};
struct AI{bool ready=false;int GetData(int){return ready;}};
struct Creature{bool IsAIEnabled=true;struct AI ai;struct AI*AI(){return &ai;}};
struct Player{bool alive=true;int map=654,status=QUEST_STATUS_INCOMPLETE;void*vehicle=nullptr;Creature*tobias=nullptr;Player*ToPlayer(){return this;}bool IsAlive(){return alive;}int GetMapId(){return map;}void*GetVehicleBase(){return vehicle;}int GetQuestStatus(int){return status;}Creature*FindNearestCreature(int,float){return tobias;}};
struct Cast{Player*caster=nullptr;Player*GetCaster(){return caster;}
'''
code+=method(s[s.index('class spell_gilneas_endgame_hippogryph :'):],'    SpellCastResult CheckBoarding()')+'};\n'
code+=r'''
void check(bool b){if(!b)throw std::runtime_error("Endgame cast gate failure");}
int main(){Player p;Creature t;Cast c;c.caster=&p;p.tobias=&t;
check(c.CheckBoarding()==SPELL_FAILED_NOT_READY);t.ai.ready=true;check(c.CheckBoarding()==SPELL_CAST_OK);
p.status=QUEST_STATUS_NONE;check(c.CheckBoarding()==SPELL_FAILED_BAD_TARGETS);p.status=3;
p.alive=false;check(c.CheckBoarding()==SPELL_FAILED_BAD_TARGETS);p.alive=true;
p.map=1;check(c.CheckBoarding()==SPELL_FAILED_BAD_TARGETS);p.map=654;
p.vehicle=&t;check(c.CheckBoarding()==SPELL_FAILED_BAD_TARGETS);p.vehicle=nullptr;
p.tobias=nullptr;check(c.CheckBoarding()==SPELL_FAILED_NOT_READY);p.tobias=&t;
t.IsAIEnabled=false;check(c.CheckBoarding()==SPELL_FAILED_NOT_READY);t.IsAIEnabled=true;
t.ai.ready=false;check(c.CheckBoarding()==SPELL_FAILED_NOT_READY);
std::cout<<"PASS: native Endgame boarding cast gate rejects closed window, abandoned quest, missing controller and existing vehicle\n";}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
