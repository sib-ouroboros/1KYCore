#!/usr/bin/env python3
"""Compile full Lorna script; individual rewards leave the shared battle intact."""
import argparse,os,subprocess,tempfile
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8');s=s[s.index('class npc_lorna_crowley_38611 :'):s.index('// 38210',s.index('class npc_lorna_crowley_38611 :'))]
 code=r'''
#include <cstdint>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr int QUEST_THE_HUNT_FOR_SYLVANAS=24902,SPELL_FORCECAST_SUMMON_TOBIAS=1,NPC_SISTER_ALMYRA=38466,ACTION_QUEST_REWARDED=2;
struct Player{};struct Quest{uint32 id;uint32 GetQuestId()const{return id;}};
struct AI{int teardowns=0;void DoAction(int){++teardowns;}};
struct Creature{struct AI ai;int casts=0;Creature*almyra=nullptr;void CastSpell(Player*,int){++casts;}Creature*FindNearestCreature(int,float){return almyra;}struct AI*AI(){return &ai;}};
struct CreatureScript{explicit CreatureScript(char const*){}virtual~CreatureScript()=default;virtual bool OnQuestAccept(Player*,Creature*,Quest const*){return true;}virtual bool OnQuestReward(Player*,Creature*,Quest const*,uint32){return false;}};
PRODUCTION
int main(){try{npc_lorna_crowley_38611 script;Creature lorna,controller;lorna.almyra=&controller;Player a,b;for(uint32 id:{24904u,24902u,24903u,1u}){Quest quest{id};if(script.OnQuestReward(&a,&lorna,&quest,0)||controller.ai.teardowns)throw std::runtime_error("one player's reward destroyed the shared event");if(script.OnQuestReward(&b,&lorna,&quest,0)||controller.ai.teardowns)throw std::runtime_error("second reward destroyed the shared event");}Quest hunt{24902},battle{24904};script.OnQuestAccept(&a,&lorna,&hunt);script.OnQuestAccept(&b,&lorna,&battle);if(lorna.casts!=1)throw std::runtime_error("native Tobias acceptance changed");std::cout<<"Lorna production script: shared battle preserved across individual rewards PASS\n";}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''.replace('PRODUCTION',s)
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'reward.cpp';exe=Path(folder)/'reward.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
