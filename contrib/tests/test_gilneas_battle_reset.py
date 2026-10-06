#!/usr/bin/env python3
"""Run seven actual reset cases; no queued fight executes after actor teardown."""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8');sections=re.split(r'    struct (npc_\w+AI) : public ScriptedAI',s);classes=[];calls=[]
 for i in range(1,len(sections),2):
  name,body=sections[i:i+2]
  if 'case EVENT_GLOBAL_RESET:' not in body or name=='npc_krennan_aranas_38553AI':continue
  case=method(body,'case EVENT_GLOBAL_RESET:');assert 'm_events.Reset();' in case and 'return;' in case
  classes.append('struct '+name+'{Creature*me;Events m_events;int cleaned=0,fought=0;void RemoveMyMember(){++cleaned;}void Update(){while(int id=m_events.ExecuteEvent()){switch(id){'+case+'case FIGHT:++fought;break;}}}};');calls.append('exercise<'+name+'>();')
 assert len(classes)==7
 code=r'''
#include <vector>
#include <stdexcept>
#include <iostream>
constexpr int EVENT_GLOBAL_RESET=1,FIGHT=2;
struct Creature{int despawns=0,delay=0;void DespawnOrUnsummon(int d){++despawns;delay=d;}};
struct Events{std::vector<int>queue{EVENT_GLOBAL_RESET,FIGHT,FIGHT};int resets=0;void Reset(){queue.clear();++resets;}int ExecuteEvent(){if(queue.empty())return 0;int id=queue.front();queue.erase(queue.begin());return id;}};
PRODUCTION
template<class AI>void exercise(){Creature c;AI ai;ai.me=&c;ai.Update();if(ai.cleaned!=1||ai.fought||c.despawns!=1||c.delay!=100||ai.m_events.resets!=1||!ai.m_events.queue.empty())throw std::runtime_error("queued combat survived teardown");ai.Update();if(ai.cleaned!=1)throw std::runtime_error("repeated cleanup");}
int main(){try{EXERCISES std::cout<<"Seven Gilneas production reset cases stop queued combat PASS\n";}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''.replace('PRODUCTION','\n'.join(classes)).replace('EXERCISES',''.join(calls))
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'reset.cpp';exe=Path(folder)/'reset.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
