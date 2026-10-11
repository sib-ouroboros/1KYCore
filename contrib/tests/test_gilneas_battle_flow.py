#!/usr/bin/env python3
"""Native march endpoints, seven wave gates and failed Gorerot summon retry."""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
 controller=s[s.index('class npc_sister_almyra_38466 :'):s.index('class npc_prince_liam_greymane_38218 :')]
 enum=method(s,'enum eZoneGilneasCity2')+';'
 code=r'''
#include <cstdint>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
ENUM
constexpr int MOVE_RUN=1,TEMPSUMMON_DEAD_DESPAWN=1;
struct Position{};Position SpawnPosGorerot[1];
struct Motion{int moves=0;void MovePoint(uint32,Position){++moves;}};
struct AI{std::vector<int>actions;void DoAction(int action){actions.push_back(action);}};
struct Creature{Motion motion;struct AI ai;bool summonOK=true;int summons=0;void SetWalk(bool){}void SetSpeedRate(int,float){}Motion*GetMotionMaster(){return &motion;}struct AI*AI(){return &ai;}Creature*SummonCreature(int,Position,int){++summons;return summonOK?this:nullptr;}};
Creature almyra;
namespace ObjectAccessor{Creature*GetCreature(Creature&,int guid){return guid?&almyra:nullptr;}}
struct Events{std::vector<int>scheduled;void ScheduleEvent(int event,int){scheduled.push_back(event);}void RescheduleEvent(int event,int){scheduled.push_back(event);}};
CLASSES
struct Controller{Creature*me;Events m_events;uint32 m_wave=0,m_arrivedMask=0,m_ai_counter=0;bool nearby=true;std::vector<int>sent;
 bool IsPlayerNear(float){return nearby;}
 void SendActionValueToAllLeader(int action){sent.push_back(action);}
 PREDICATE
 void Sync(){switch(int(EVENT_SYNC_BEFORE_NEXT_WAVE)){SYNC}}
};
void check(bool ok,char const*msg){if(!ok)throw std::runtime_error(msg);}
template<class T>void endpoint(int action){Creature c;T ai;ai.me=&c;ai.m_wave=7;ai.m_waveSize=4;ai.m_point=3;almyra.ai.actions.clear();ai.March();check(almyra.ai.actions.empty()&&c.motion.moves==1,"unfinished route never reports arrival");ai.m_point=4;ai.March();check(almyra.ai.actions.size()==1&&almyra.ai.actions[0]==action,"each actual leader reports its own arrival");ai.m_almyraGUID=0;ai.March();check(almyra.ai.actions.size()==1,"missing controller never reports to another event");}
int main(){try{
 ENDPOINTS
 Creature c;Controller ai;ai.me=&c;
 for(uint32 wave=1;wave<=7;++wave){
  ai.m_wave=wave;uint32 mask=wave<=2?7:wave==3?15:wave<=6?31:63;ai.m_arrivedMask=mask;ai.nearby=true;ai.sent.clear();ai.m_events.scheduled.clear();ai.Sync();
  if(wave<7){check(ai.sent.size()==2&&ai.sent.back()==int(ACTION_MOVE_TO_WAVE_POSION_1+wave),"native transitions1 through6 dispatch the next wave");check(ai.m_events.scheduled.size()==1&&ai.m_events.scheduled[0]==EVENT_MOVE_WAVE,"controller follows its army");}
  else check(ai.sent.empty(),"wave7 has no invented eighth march: native timed cinematic owns finale");
  for(uint32 bit=1;bit<=32;bit*=2)if(mask&bit){ai.sent.clear();ai.m_events.scheduled.clear();ai.m_arrivedMask=mask&~bit;ai.Sync();check(ai.sent.empty()&&ai.m_events.scheduled.size()==1&&ai.m_events.scheduled[0]==EVENT_SYNC_BEFORE_NEXT_WAVE,"missing group retries without skipping required leader");}
  if(wave>=3){ai.m_arrivedMask=mask;ai.nearby=false;ai.sent.clear();ai.m_events.scheduled.clear();ai.Sync();check(ai.sent.empty()&&ai.m_events.scheduled[0]==EVENT_SYNC_BEFORE_NEXT_WAVE,"death or departure waits at shared gate");ai.nearby=true;ai.Sync();check(wave==7||!ai.sent.empty(),"returning live participant releases gate");}
 }
 ai.m_wave=4;ai.m_arrivedMask=31;ai.nearby=true;c.summonOK=false;ai.sent.clear();ai.m_events.scheduled.clear();int old=c.summons;ai.Sync();check(c.summons==old+1&&ai.sent.empty()&&ai.m_events.scheduled[0]==EVENT_SYNC_BEFORE_NEXT_WAVE,"failed boss summon retries without starting boss-free wave5");c.summonOK=true;ai.sent.clear();ai.Sync();check(ai.sent.back()==ACTION_MOVE_TO_WAVE_POSION_5,"successful retry starts the real boss stage");
 std::cout<<"PASS: five production leader notifications, seven native wave gates, death/return and failed boss summon retry\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 classes=[];endpoints=[]
 for name,action in [('npc_prince_liam_greymane_38218','ACTION_LIAM_ARRIVED'),('npc_myriam_spellwaker_38465','ACTION_MYRIAM_ARRIVED'),('npc_lorna_crowley_38426','ACTION_LORNA_ARRIVED'),('npc_lord_darius_crowley_38415','ACTION_DARIUS_ARRIVED'),('npc_king_genn_greymane_38470','ACTION_GENN_ARRIVED')]:
  body=s[s.index('class '+name+' :'):];event=method(body,'case EVENT_MOVE_WAVE:')
  classes.append('struct '+name+'{Creature*me;Events m_events;uint32 m_wave=0,m_waveSize=0,m_point=0;int m_almyraGUID=1;void CheckForStartAction(){}Position GetWavePosition(){return {};}void March(){switch(int(EVENT_MOVE_WAVE)){'+event+'}}};')
  endpoints.append(f'endpoint<{name}>({action});')
 replacements={'ENUM':enum,'CLASSES':'\n'.join(classes),'ENDPOINTS':'\n'.join(endpoints),'PREDICATE':method(controller,'        bool AreWaveLeadersReady('),'SYNC':method(controller,'case EVENT_SYNC_BEFORE_NEXT_WAVE:')}
 for key,value in replacements.items():code=re.sub(r'\b'+key+r'\b',lambda m:value,code)
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'flow.cpp';exe=Path(tmp)/'flow.exe';cpp.write_text(code,'utf8');flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
