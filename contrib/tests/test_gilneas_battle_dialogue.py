#!/usr/bin/env python3
"""Native motivation event order/timing and coverage of every battle Talk group."""
import argparse,os,re,json,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2]
 s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
 proof=json.loads((root/'docs/audit-data/gilneas-battle-dialogue.json').read_text('utf8'))['lines'];groups={(x['entry'],x['group']) for x in proof}
 sections=re.split(r'class (npc_\w+) : public CreatureScript',s)
 for i in range(1,len(sections),2):
  name,body=sections[i:i+2];entry=int(re.search(r'_(\d+)$',name)[1])
  if entry not in {x['entry'] for x in proof}:continue
  # Cross-actor calls are checked separately below, not mistaken for the caller's own text.
  for group in re.findall(r'(?<!->)(?<!\w)Talk\((\d+)\)',body):assert (entry,int(group)) in groups,(entry,group)
 king=s[s.index('class npc_king_genn_greymane_38470 :'):s.index('class npc_lady_sylvanas_windrunner_38469 :')]
 assert re.findall(r'liam->AI\(\)->Talk\((\d+)\)',king)==['1','2']
 liam=s[s.index('class npc_prince_liam_greymane_38474 :'):s.index('class npc_lorna_crowley_38611 :')]
 assert 'king->AI()->Talk(2);' in liam
 for x in proof:assert x['en'] and re.search('[А-Яа-я]',x['ru']),x
 native=s[s.index('class npc_prince_liam_greymane_38218 :'):s.index('class npc_myriam_spellwaker_38465 :')]
 cases='\n'.join(method(native,'case EVENT_MOTIVATION_'+str(i)+':') for i in range(7))+'\n'+method(native,'case EVENT_MOTIVATION_DONE:')
 code=r'''
#include <cstdint>
#include <vector>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
ENUM;
struct AI{std::vector<int>actions;void DoAction(int action){actions.push_back(action);}};
struct Creature{struct AI ai;int sounds=0;struct AI*AI(){return &ai;}void PlayDirectSound(int){++sounds;}};Creature controller;
namespace ObjectAccessor{Creature*GetCreature(Creature&,int id){return id?&controller:nullptr;}}
struct Events{int now=0;std::map<int,int>pending;void ScheduleEvent(int id,int delay){pending[id]=now+delay;}};
struct Liam{Creature*me;Events m_events;int m_almyraGUID=1;std::vector<int>talks;void Talk(int group){talks.push_back(group);}void Start(){switch(int(ACTION_START_MOTIVATION)){START}}void Event(int event){switch(event){CASES}}};
int main(){try{Creature c;Liam ai;ai.me=&c;ai.Start();if(ai.m_events.pending.at(EVENT_MOTIVATION_0)!=1000)throw std::runtime_error("speech starts one second after controller action");
 while(!ai.m_events.pending.empty()){int id=ai.m_events.pending.begin()->first;ai.m_events.now=ai.m_events.pending.begin()->second;ai.m_events.pending.erase(id);ai.Event(id);}
 if(ai.talks!=std::vector<int>{0,1,2,3,4,5,6}||ai.m_events.now!=57500||controller.ai.actions!=std::vector<int>{ACTION_MOTIVATION_DONE}||c.sounds!=1)throw std::runtime_error("seven native lines and movement signal must retain original order/timing");
 std::cout<<"PASS: every battle Talk group restored, seven speech events and finale group order\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 for key,value in {'ENUM':method(s,'enum eZoneGilneasCity2'),'START':method(native,'case ACTION_START_MOTIVATION:'),'CASES':cases}.items():code=re.sub(r'\b'+key+r'\b',lambda m:value,code)
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'dialogue.cpp';exe=Path(tmp)/'dialogue.exe';cpp.write_text(code,'utf8');flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
