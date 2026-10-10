"""Native summon event and vehicle target selection with two adjacent players."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    script=(root/'src/server/game/AI/SmartScripts/SmartScript.cpp').read_text('utf8')
    ai=(root/'src/server/game/AI/SmartScripts/SmartAI.cpp').read_text('utf8')
    begin=script.index('        case SMART_TARGET_ACTION_INVOKER_VEHICLE:')
    branch=script[begin:script.index('        case SMART_TARGET_INVOKER_PARTY:',begin)]
    callback=method(ai,'void SmartAI::IsSummonedBy(')
    code=r"""
#include <vector>
#include <stdexcept>
#include <iostream>
enum{SMART_TARGET_ACTION_INVOKER_VEHICLE=22};enum{SMART_EVENT_JUST_SUMMONED=54};
struct Unit;
struct Vehicle{Unit*base;Unit*GetBase(){return base;}};
struct Unit{Vehicle*vehicle=nullptr;Vehicle*GetVehicle(){return vehicle;}};
std::vector<Unit*> targets(Unit*scriptTrigger){std::vector<Unit*>result;auto*l=&result;switch(SMART_TARGET_ACTION_INVOKER_VEHICLE){BRANCH}return result;}
struct Script{std::vector<Unit*>chosen;int event=0;void ProcessEventsFor(int type,Unit*unit){event=type;chosen=targets(unit);}};
struct SmartAI{Script script;Script*GetScript(){return &script;}void IsSummonedBy(Unit*);};
CALLBACK
void check(bool b){if(!b)throw std::runtime_error("owner vehicle regression");}
int main(){Unit horse1,horse2,player1,player2;Vehicle v1{&horse1},v2{&horse2};player1.vehicle=&v1;player2.vehicle=&v2;SmartAI first,second;
first.IsSummonedBy(&player1);second.IsSummonedBy(&player2);
check(first.script.event==54&&first.script.chosen==std::vector<Unit*>{&horse1});
check(second.script.chosen==std::vector<Unit*>{&horse2});
player1.vehicle=nullptr;first.IsSummonedBy(&player1);check(first.script.chosen.empty());
first.IsSummonedBy(nullptr);check(first.script.chosen.empty());
v2.base=nullptr;second.IsSummonedBy(&player2);check(second.script.chosen.empty());
std::cout<<"PASS: actual SmartAI summon event and owner vehicle target, two players and no-vehicle guards\n";}
""".replace('BRANCH',branch).replace('CALLBACK',callback)
    with tempfile.TemporaryDirectory() as directory:
        cpp=Path(directory)/'rescue.cpp';exe=Path(directory)/'rescue.exe';cpp.write_text(code,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
