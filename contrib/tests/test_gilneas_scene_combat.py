#!/usr/bin/env python3
"""Execute production scene-spawn and ambusher targeting guards."""
import argparse, os, subprocess, tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
    code=r"""
#include <cstdint>
#include <chrono>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using namespace std::chrono_literals;
constexpr int SPELL_THROW_BOULDER=1,EVENT_COOLDOWN_00=2;
struct Unit{bool player=true;int faction=2203;Unit*ToPlayer(){return player?this:nullptr;}int getFaction(){return faction;}};
struct Creature:Unit{int map=654,entry=37805;uint32 spawn=802085;bool phase=true,visible=true,attackable=true;float distance=1;int casts=0;int GetMapId(){return map;}int GetEntry(){return entry;}uint32 GetSpawnId(){return spawn;}bool IsInPhase(Unit*){return phase;}bool CanSeeOrDetect(Unit*){return visible;}bool IsValidAttackTarget(Unit*){return attackable;}float GetDistance(Unit*){return distance;}void SetFacingToObject(Unit*){}void CastSpell(Unit*,int,bool){++casts;}};
struct CreatureAI{virtual~CreatureAI()=default;virtual bool CanAIAttack(Unit const*)const{return true;}};
struct PassiveAI:CreatureAI{explicit PassiveAI(Creature*){}};
struct CreatureScript{explicit CreatureScript(char const*){}virtual~CreatureScript()=default;virtual CreatureAI*GetAI(Creature*)const{return nullptr;}};
struct EventMap{int schedules=0;template<class T>void ScheduleEvent(int,T,T){++schedules;}};
int urand(int,int){return 0;}
void check(bool ok,char const*why){if(!ok)throw std::runtime_error(why);}
"""
    start=source.index('class npc_gilneas_koroth_scene_actor :');end=source.index('// 38762',start);code+=source[start:end]
    code+='struct Ambusher{Creature*me;bool m_cast_cooldown=false;EventMap m_events;'+method(source[source.index('    struct npc_ogre_ambusher_38762AI'):],'        void MoveInLineOfSight(')+'};'
    code+=r"""
int main(){
 npc_gilneas_koroth_scene_actor script;Creature c;Unit target;
 for(uint32 guid=802085;guid<=802112;++guid){c.entry=37805;c.spawn=guid;if(guid==802086)c.entry=37807;if(guid==802087)c.entry=37806;if(guid==802103)c.entry=37808;CreatureAI*ai=script.GetAI(&c);check(ai&&!ai->CanAIAttack(&target),"all 28 persistent scene actors cannot attack");delete ai;}
 c.spawn=0;check(!script.GetAI(&c),"summons retain default AI");c.spawn=802085;c.map=0;check(!script.GetAI(&c),"other maps retain default AI");c.map=654;c.entry=37806;check(!script.GetAI(&c),"entry and GUID must match");
 for(int mode=0;mode<5;++mode){Creature ogre;Ambusher a{&ogre,false,{}};if(mode==0)ogre.phase=false;if(mode==1)ogre.visible=false;if(mode==2)ogre.attackable=false;if(mode==3)ogre.distance=61;a.MoveInLineOfSight(mode==4?nullptr:&target);check(!ogre.casts&&!a.m_cast_cooldown&&!a.m_events.schedules,"invalid or unseen target cannot receive boulder");}
 Creature ogre;Ambusher a{&ogre,false,{}};a.MoveInLineOfSight(&target);check(ogre.casts==1&&a.m_cast_cooldown&&a.m_events.schedules==1,"valid visible ambush remains enabled");a.MoveInLineOfSight(&target);check(ogre.casts==1,"cooldown remains enforced");
 std::cout<<"Gilneas scene actors and ambusher target isolation: PASS\n";
}
"""
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
