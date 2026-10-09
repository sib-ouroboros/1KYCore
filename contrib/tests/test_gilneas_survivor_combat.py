#!/usr/bin/env python3
"""Native survivor/crocodile handlers with controlled actors and combat boundaries."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 code=r'''
#include <cstdint>
#include <chrono>
#include <map>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;using namespace std::chrono_literals;
enum{REACT_DEFENSIVE=1,EVENT_CHECK_FOR_CREATURE=1,EMOTE_ONESHOT_NONE=0};
struct Unit{uint32 entry=0;virtual~Unit()=default;uint32 GetEntry(){return entry;}};
struct Creature;struct ScriptedAI;
struct MotionMaster{int chases=0;void MoveChase(Unit*){++chases;}};
struct Creature:Unit{ScriptedAI*ai=nullptr;Creature*croc=nullptr;Unit*victim=nullptr;bool alive=true,attackAllowed=true;int phase=1,melees=0;MotionMaster motion;bool IsAlive(){return alive;}bool IsInCombat(){return victim!=nullptr;}bool IsInPhase(Creature*c){return phase==c->phase;}bool Attack(Unit*u,bool){if(!attackAllowed)return false;victim=u;return true;}void SetReactState(int){}void HandleEmoteCommand(int){}void SetFacingToObject(Unit*){}Creature*FindNearestCreature(int e,float){return croc&&croc->entry==uint32(e)?croc:nullptr;}ScriptedAI*AI(){return ai;}MotionMaster*GetMotionMaster(){return &motion;}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>events;void Update(uint32 d){now+=d;}template<class R,class P>void ScheduleEvent(uint32 e,std::chrono::duration<R,P>d){events.emplace(now+std::chrono::duration_cast<std::chrono::milliseconds>(d).count(),e);}template<class R,class P>void RescheduleEvent(uint32 e,std::chrono::duration<R,P>d){events.clear();ScheduleEvent(e,d);}uint32 ExecuteEvent(){if(events.empty()||events.begin()->first>now)return 0;auto e=events.begin()->second;events.erase(events.begin());return e;}};
struct ScriptedAI{Creature*me;ScriptedAI(Creature*c):me(c){c->ai=this;}virtual~ScriptedAI()=default;virtual void AttackStart(Unit*u){me->Attack(u,true);}void AttackStartNoMove(Unit*u){me->Attack(u,true);}bool UpdateVictim(){return me->victim;}void DoMeleeAttackIfReady(){++me->melees;}};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
'''
 for name in ['npc_crash_survivor_37067AI','npc_swamp_crocolisk_37078AI']:code+=method(source,'    struct '+name+' :')+';\n'
 code+=r'''
int main(){Creature survivor,croc;survivor.entry=37067;croc.entry=37078;survivor.croc=&croc;npc_crash_survivor_37067AI s(&survivor);npc_swamp_crocolisk_37078AI c(&croc);s.Reset();c.Reset();s.UpdateAI(1000);check(survivor.victim==&croc&&croc.victim==&survivor&&survivor.melees==1,"both defensive NPCs must acquire native victims");
 uint32 damage=10;s.DamageTaken(&croc,damage);check(!damage,"native survivor survival gate preserved");damage=10;c.DamageTaken(&survivor,damage);check(!damage,"native croc survival gate preserved");Unit player;player.entry=0;damage=10;c.DamageTaken(&player,damage);check(damage==10,"player damage remains effective");c.AttackStart(&player);check(croc.victim==&player&&croc.motion.chases==1,"player intervention starts chase");
 survivor.victim=nullptr;s.UpdateAI(1000);check(!survivor.victim&&croc.victim==&player,"idle survivor must not steal croc fighting a player");
 for(int reason=0;reason<3;++reason){survivor.victim=nullptr;croc.victim=nullptr;croc.alive=reason!=0;croc.phase=reason==1?2:1;survivor.attackAllowed=reason!=2;s.UpdateAI(1000);check(!survivor.victim&&!croc.victim,"invalid pairing must not start combat");}
 std::cout<<"PASS: native survivor/crocodile pairing, existing NPC damage gates, player damage/chase and occupied/dead/phase/failed-attack guards\n";}
'''
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'];subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
