#!/usr/bin/env python3
"""Compile production finale actions, death-credit case and Liam SpellHit."""
import argparse,os,subprocess,tempfile,re
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8');a=s[s.index('class npc_lady_sylvanas_windrunner_38469 :'):s.index('class npc_soultethered_banshee_38473 :')];l=s[s.index('class npc_prince_liam_greymane_38474 :'):]
 code=r'''
#include <cstdint>
#include <list>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;
enum{NPC_LADY_SYLVANAS_WINDRUNNER=38469,SPELL_SHOOT_LIAM=1,SPELL_LIAM_SLAIN_DUMMY=2,SPELL_BFGC_COMPLETE=3,QUEST_THE_BATTLE_FOR_GILNEAS_CITY=24904,QUEST_STATUS_INCOMPLETE=1,ACTION_SYLVANAS_HAS_ENOUGH=10,ACTION_LIAM_IS_DEATH=11,EVENT_SYLVANAS_ATTACK1=20,EVENT_LIAM_IS_DEATH=21,EVENT_GLOBAL_RESET=22};
struct Unit{int guid=0,entry=0;int GetGUID(){return guid;}int GetEntry(){return entry;}};
struct Player:Unit{int quest=1,credits=0;int GetQuestStatus(int){return quest;}void KilledMonsterCredit(int){++credits;}};
struct Motion{int moves=0,paths=0;void MovePoint(int,float,float,float){++moves;}void MovePath(int,bool){++paths;}};
struct AI{virtual~AI()=default;int talks=0;virtual void DoAction(int32){}void Talk(int){++talks;}};
struct Creature:Unit{bool phase=true;int casts=0,despawns=0;Motion motion;struct AI*ai=nullptr;std::list<Player*>players;bool IsInPhase(Unit*){return phase;}void CastSpell(Unit*,int){++casts;}struct AI*AI(){return ai;}Motion*GetMotionMaster(){return &motion;}std::list<Player*>SelectNearestPlayers(float){return players;}void DespawnOrUnsummon(int){++despawns;}};
std::map<int,Creature*>actors;namespace ObjectAccessor{Creature*GetCreature(Creature&,int id){auto i=actors.find(id);return i==actors.end()?nullptr:i->second;}}
struct SpellInfo{int Id;};struct Events{int scheduled=0,resets=0;void ScheduleEvent(int,int){++scheduled;}void Reset(){++resets;scheduled=0;}};
struct Sylvanas:AI{Creature*me;bool m_cinematicStarted=false,m_liamDeathQueued=false,m_completionHandled=false;Events m_events;int cleanup=0,groups=0;void RemoveMyMember(){++cleanup;}void BuildFollowerGroup(){++groups;}
 void DoAction(int32 param)override{switch(param){START DEATH}}
 void Event(int event){switch(event){RESET COMPLETE}}
};
struct Liam{Creature*me;int m_sylvanaGUID=1,m_kingGUID=3;bool m_shootHandled=false;HIT};
void check(bool ok,char const*m){if(!ok)throw std::runtime_error(m);}
int main(){try{Creature syl,liam,king;Player p,done;done.quest=2;Sylvanas ai;AI kingAI;ai.me=&syl;syl.ai=&ai;syl.guid=1;syl.entry=NPC_LADY_SYLVANAS_WINDRUNNER;king.ai=&kingAI;actors={{1,&syl},{3,&king}};Liam la;la.me=&liam;SpellInfo spell{SPELL_SHOOT_LIAM};syl.players={&p,&done};
 ai.DoAction(ACTION_LIAM_IS_DEATH);check(!ai.m_events.scheduled,"premature completion ignored");ai.Event(EVENT_LIAM_IS_DEATH);check(!p.credits,"no credit without native death notification");ai.DoAction(ACTION_SYLVANAS_HAS_ENOUGH);ai.DoAction(ACTION_SYLVANAS_HAS_ENOUGH);check(ai.m_events.scheduled==1&&ai.talks==1,"cinematic starts once");Creature foreign;foreign.entry=NPC_LADY_SYLVANAS_WINDRUNNER;foreign.guid=99;la.SpellHit(&foreign,&spell);check(!la.m_shootHandled,"foreign Sylvanas cannot kill this Liam");liam.phase=false;la.SpellHit(&syl,&spell);check(!la.m_shootHandled,"phase mismatch ignored");liam.phase=true;la.SpellHit(&syl,&spell);la.SpellHit(&syl,&spell);check(liam.casts==1&&king.motion.moves==1&&kingAI.talks==1&&ai.m_events.scheduled==2,"native death and king reaction once");ai.DoAction(ACTION_LIAM_IS_DEATH);check(ai.m_events.scheduled==2,"duplicate death action ignored");ai.Event(EVENT_LIAM_IS_DEATH);ai.Event(EVENT_LIAM_IS_DEATH);check(p.credits==1&&!done.credits&&syl.casts==1&&syl.motion.paths==1,"native credit and departure once for incomplete quest");ai.Event(EVENT_GLOBAL_RESET);check(ai.cleanup==1&&syl.despawns==1&&ai.m_events.resets==1,"existing timeout cleans followers and stops queued events");std::cout<<"Gilneas finale production callbacks and native credit dispatch PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
 for key,val in {'START':method(a,'                case ACTION_SYLVANAS_HAS_ENOUGH:'),'DEATH':method(a,'                case ACTION_LIAM_IS_DEATH:'),'RESET':method(a,'                case EVENT_GLOBAL_RESET:'),'COMPLETE':method(a,'                case EVENT_LIAM_IS_DEATH:'),'HIT':method(l,'        void SpellHit(')}.items():code=re.sub(r'(?<![A-Za-z_])'+key+r'(?![A-Za-z_])',lambda match:val,code)
 with tempfile.TemporaryDirectory() as folder:
  cpp=Path(folder)/'finale.cpp';exe=Path(folder)/'finale.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
