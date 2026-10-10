"""Execute production recording handlers against controlled player positions."""
import argparse, os, subprocess, tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--no-sanitizers',action='store_true'); args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/Commands/cs_wp.cpp').read_text('utf8')
    code=r"""
#include <fstream>
#include <iomanip>
#include <locale>
#include <map>
#include <memory>
#include <mutex>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cassert>
#include <sstream>
#include <vector>
using uint32=std::uint32_t;
struct Position {float x=0,y=0,z=0,o=0;void Relocate(Position const*p){*this=*p;}float GetExactDist(Position const*p)const{return std::sqrt((x-p->x)*(x-p->x)+(y-p->y)*(y-p->y)+(z-p->z)*(z-p->z));}};
struct ObjectGuid {int id;bool operator<(ObjectGuid g)const{return id<g.id;}int GetCounter()const{return id;}};
struct Player:Position {int id=1;uint32 map=654,instance=0;ObjectGuid GetGUID(){return{id};}uint32 GetMapId(){return map;}uint32 GetInstanceId(){return instance;}Player*GetSession(){return this;}Player*GetPlayer(){return this;}float GetPositionX(){return x;}float GetPositionY(){return y;}float GetPositionZ(){return z;}float GetOrientation(){return o;}};
struct ChatHandler {Player*p;ChatHandler(Player*v):p(v){}Player*GetSession(){return p;}template<class...T>void PSendSysMessage(char const*,T...){ }void SendSysMessage(char const*){}};
struct PlayerScript {PlayerScript(char const*){}virtual~PlayerScript()=default;virtual void OnUpdate(Player*,uint32){}virtual void OnLogout(Player*){}};
"""
    code+=source[source.index('namespace\n{'):source.index('class wp_commandscript')]
    code+='struct Commands {\n'+method(source,'static bool HandleRecordStart(')+method(source,'static bool HandleRecordStop(')+'};\n'
    dusk=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
    survivor=dusk[dusk.index('class npc_crash_survivor_37067'):]
    code+=r"""
enum{QUEST_STATUS_INCOMPLETE=3,QUEST_OBJECTIVE_MONSTER=0};
struct QuestObjective {int Type=0,Amount=5;};
struct Quest {std::vector<QuestObjective> goals{{}};std::vector<QuestObjective>const&GetObjectives()const{return goals;}};
struct ObjectMgr {Quest quest;Quest const*GetQuestTemplate(int id){assert(id==24468);return &quest;}} objectMgr;
ObjectMgr*sObjectMgr=&objectMgr;
struct QuestPlayer {int status=3,data=0,complete=0,updates=0;int GetQuestStatus(int id){assert(id==24468);return status;}void SetQuestObjectiveData(QuestObjective const&o,int n){assert(o.Type==0);data=n;}void CompleteQuest(int id){assert(id==24468);status=1;++complete;}void SendQuestUpdate(int id){assert(id==24468);++updates;}};
struct Creature {int map=654;bool phase=true;int GetMapId(){return map;}bool IsInPhase(QuestPlayer*){return phase;}};
"""
    code+='struct Gossip { '+method(survivor,'bool OnGossipHello(').replace('Player*','QuestPlayer*')+' };\n'

    code+=r"""
int main(){
 Gossip gossip;QuestPlayer qp;Creature npc;
 npc.map=1;gossip.OnGossipHello(&qp,&npc);assert(qp.complete==0);
 npc.map=654;npc.phase=false;gossip.OnGossipHello(&qp,&npc);assert(qp.complete==0);
 npc.phase=true;gossip.OnGossipHello(&qp,&npc);assert(qp.data==5&&qp.complete==1&&qp.updates==1);
 gossip.OnGossipHello(&qp,&npc);assert(qp.complete==1);
 qp.status=0;gossip.OnGossipHello(&qp,&npc);assert(qp.complete==1);
 Player p,q;q.id=2;ChatHandler h(&p),h2(&q);player_route_recorder script;
 assert(!Commands::HandleRecordStart(&h,"bad"));assert(routeRecordings.empty());
 assert(Commands::HandleRecordStart(&h,""));auto name=routeRecordings.at(p.GetGUID())->name;
 Commands::HandleRecordStart(&h,"");assert(routeRecordings.size()==1);
 script.OnUpdate(&p,1000);assert(routeRecordings.at(p.GetGUID())->points==1);
 p.x=1;p.z=19.05f;script.OnUpdate(&p,1000);assert(routeRecordings.at(p.GetGUID())->points==2);
 Commands::HandleRecordStart(&h2,"");assert(routeRecordings.size()==2);
 p.x=1.2f;Commands::HandleRecordStop(&h,"");assert(routeRecordings.size()==1);
 std::ifstream file(name);std::string row;std::getline(file,row);assert(row=="point,elapsed_ms,map,instance,x,y,z,orientation");
 int rows=0;while(std::getline(file,row)){++rows;assert(row.find(",654,0,")!=std::string::npos);}assert(rows==3);
 q.map=1;script.OnUpdate(&q,1);assert(routeRecordings.empty());
 Commands::HandleRecordStart(&h,"");p.x=100;script.OnUpdate(&p,1);assert(routeRecordings.empty());
 Commands::HandleRecordStart(&h,"");script.OnUpdate(&p,3600000);assert(routeRecordings.empty());
 Commands::HandleRecordStart(&h,"");script.OnLogout(&p);assert(routeRecordings.empty());
 Commands::HandleRecordStop(&h,"");
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'test.cpp'; exe=Path(tmp)/('test.exe' if os.name=='nt' else 'test');cpp.write_text(code,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++14','-Wall','-Wextra','-Werror','-pthread',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],cwd=tmp,check=True)
    print('PASS route recording: export, isolation, duplicate start, stop, logout, map, teleport, timeout')

if __name__=='__main__': main()
