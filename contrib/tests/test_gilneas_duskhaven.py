#!/usr/bin/env python3
"""Compile actual early Duskhaven quest handlers; client visuals are not emulated."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 enum=method(s,'enum eDuskHaven')+';'
 abom=s[s.index('class npc_horrid_abomination_36231 :'):s.index('// 69094')]
 ai=method(abom,'    struct npc_horrid_abomination_36231AI :')+';'
 prefix=r'''
#include <cstdint>
#include <chrono>
#include <vector>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using namespace std::chrono_literals;
constexpr int QUEST_STATUS_NONE=0,QUEST_STATUS_INCOMPLETE=3,QUEST_STATUS_COMPLETE=1;
constexpr int UNIT_STATE_ROOT=1,UNIT_STATE_STUNNED=2;
constexpr int CHAT_MSG_ADDON=0,LANG_ADDON=0,TEXT_RANGE_NORMAL=0,TEAM_OTHER=0;
struct Player;struct Creature;
struct Unit{virtual ~Unit()=default;virtual Player* ToPlayer(){return nullptr;}};
struct SpellInfo{uint32 Id;};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32> events;
 void Reset(){now=0;events.clear();}void Update(uint32 diff){now+=diff;}
 template<class R,class P>void ScheduleEvent(uint32 id,std::chrono::duration<R,P> d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),id);}
 uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto id=events.begin()->second;events.erase(events.begin());return id;}};
struct Player:Unit{int status=QUEST_STATUS_INCOMPLETE;int objectives[3]={0};std::vector<uint32> credits;
 Player* ToPlayer() override{return this;}int GetQuestStatus(uint32){return status;}
 int GetQuestObjectiveData(uint32,int slot){return objectives[slot];}
 void KilledMonsterCredit(uint32 id){credits.push_back(id);if(id==36287)objectives[0]=1;if(id==36288)objectives[1]=1;if(id==36289)objectives[2]=1;}};
struct Creature:Unit{bool alive=true;int states=0;std::vector<uint32> spells;
 bool IsAlive(){return alive;}void KillSelf(){alive=false;}void ClearUnitState(int mask){states&=~mask;}
 void AddUnitState(int mask){states|=mask;}void RemoveAurasDueToSpell(uint32){}void CastSpell(Unit*,uint32 id,bool){spells.push_back(id);}};
struct ScriptedAI{Creature* me;int talks=0,melees=0;explicit ScriptedAI(Creature*c):me(c){}
 void Talk(int,Player*){++talks;}bool UpdateVictim(){return true;}void DoMeleeAttackIfReady(){++melees;}};
struct TextMgr{template<class... T> void SendChat(T...) {}} texts;auto*sCreatureTextMgr=&texts;
'''
 code=prefix+enum+'\n'+method(abom,'    enum eHorrid')+';\n'+ai
 for name in ['npc_cynthia_36267','npc_james_36268','npc_ashley_36269']:
  part=s[s.index('class '+name+' :'):];code+='struct '+name+'{'+method(part,'    bool OnGossipHello(')+'};\n'
 code+=r'''
void check(bool value,char const* name){if(!value)throw std::runtime_error(name);}
int main(){
 check(QUEST_THE_HUNGRY_ETTIN==14416,"correct horse quest ID");
 Creature creature;Player a,b;npc_horrid_abomination_36231AI ai(&creature);ai.Reset();
 SpellInfo arbitrary{172},barrel{69094},placed{68555};Unit pet;
 ai.SpellHit(&a,&arbitrary);ai.SpellHit(&a,&placed);ai.SpellHit(&pet,&barrel);ai.SpellHit(nullptr,&barrel);ai.SpellHit(&a,nullptr);
 check(a.credits.empty()&&!ai.m_creditGiven,"only player item spell accepted");
 a.status=QUEST_STATUS_NONE;ai.SpellHit(&a,&barrel);check(a.credits.empty(),"quest gate");a.status=QUEST_STATUS_INCOMPLETE;
 ai.SpellHit(&a,&barrel);check(a.credits==std::vector<uint32>{36233}&&creature.spells==std::vector<uint32>{68555},"barrel on actor and one credit");
 ai.SpellHit(&a,&barrel);ai.SpellHit(&b,&barrel);check(a.credits.size()==1&&b.credits.empty(),"claimed target cannot be shared twice");
 ai.UpdateAI(2999);check(creature.alive&&ai.melees==0,"bounded fuse no melee");
 ai.UpdateAI(1);check(!creature.alive&&creature.spells.back()==68560,"native explosion and death");
 ai.SpellHit(&b,&barrel);check(b.credits.empty(),"dead target denied");creature.alive=true;ai.Reset();ai.SpellHit(&b,&barrel);check(b.credits.size()==1,"respawn independent");
 npc_cynthia_36267 c;npc_ashley_36269 ash;npc_james_36268 j;Player p,q;
 check(c.OnGossipHello(&p,&creature),"Cynthia interact");c.OnGossipHello(&p,&creature);check(p.credits==std::vector<uint32>{36287},"Cynthia only once");
 check(ash.OnGossipHello(&p,&creature)&&j.OnGossipHello(&p,&creature),"other children interact");
 check(p.credits==std::vector<uint32>({36287,36288,36289}),"correct distinct child entries and slots");
 c.OnGossipHello(&q,&creature);check(q.credits==std::vector<uint32>{36287},"other player independent");
 q.status=QUEST_STATUS_COMPLETE;ash.OnGossipHello(&q,&creature);check(q.credits.size()==1,"completed quest no credit");
 std::cout<<"Duskhaven barrel and child handlers: PASS\n";
}
'''
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8')
  cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
