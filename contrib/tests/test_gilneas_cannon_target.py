"""Compile the production cannon destination hook, including corpse anchors."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2]
 source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city1.cpp').read_text('utf8')
 source=source[source.index('class spell_gilneas_cannon_scene_target'):]
 code=r"""
#include <stdexcept>
#include <iostream>
enum{NPC_COMMANDEERED_CANNON=35914,NPC_BLOODFANG_WORGEN_35118=35118,QUEST_SAVE_KRENNAN_ARANAS=14293};
struct ObjectGuid{int id=0;explicit operator bool()const{return id!=0;}};
struct Creature;struct TempSummon{Creature*owner=nullptr;Creature*GetSummoner(){return owner;}};
struct AI{ObjectGuid guid{1};ObjectGuid GetGUID(int){return guid;}};
struct WorldObject{virtual ~WorldObject()=default;};
struct Creature:WorldObject{int entry=35914,map=654;bool phase=true,alive=true,temporary=false;::AI ai;TempSummon summon;Creature*ToCreature(){return this;}int GetEntry(){return entry;}int GetMapId(){return map;}::AI*AI(){return &ai;}TempSummon*ToTempSummon(){return temporary?&summon:nullptr;}bool IsInPhase(Creature*){return phase;}};
Creature*resolved=nullptr;namespace ObjectAccessor{Creature*GetCreature(Creature&,ObjectGuid){return resolved;}}
struct Hook{Creature*caster;Creature*GetCaster(){return caster;}METHOD};
void check(bool b){if(!b)throw std::runtime_error("destination hook invariant");}
int main(){Creature cannon,actor,foreign;actor.entry=35118;actor.temporary=true;actor.summon.owner=&cannon;resolved=&actor;Hook hook{&cannon};WorldObject*target=&foreign;hook.SelectSceneTarget(target);check(target==&actor);
actor.alive=false;target=&foreign;hook.SelectSceneTarget(target);check(target==&actor);
actor.summon.owner=&foreign;hook.SelectSceneTarget(target);check(target==nullptr);
actor.summon.owner=&cannon;actor.phase=false;target=&foreign;hook.SelectSceneTarget(target);check(!target);
actor.phase=true;resolved=nullptr;target=&foreign;hook.SelectSceneTarget(target);check(!target);
cannon.ai.guid.id=0;target=&foreign;hook.SelectSceneTarget(target);check(target==&foreign);
cannon.ai.guid.id=1;cannon.map=1;hook.SelectSceneTarget(target);check(target==&foreign);
cannon.map=654;cannon.entry=1;hook.SelectSceneTarget(target);check(target==&foreign);
hook.caster=nullptr;hook.SelectSceneTarget(target);check(target==&foreign);
std::cout<<"PASS: production destination hook, corpse anchor, ownership, phase and unrelated casts\n";}
"""
 code=code.replace('METHOD',method(source,'        void SelectSceneTarget('))
 with tempfile.TemporaryDirectory() as directory:
  cpp=Path(directory)/'target.cpp';exe=Path(directory)/'target.exe';cpp.write_text(code,'utf8')
  flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
