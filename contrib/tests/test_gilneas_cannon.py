"""Production cannon handlers: own targets, duplicate start and scoped cleanup."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city1.cpp').read_text('utf8')
    source=source[source.index('class npc_commandeered_cannon_35914'):source.index('class npc_lord_godfrey_35906')]
    code=r"""
#include <chrono>
#include <cstdint>
#include <map>
#include <vector>
#include <memory>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using namespace std::chrono_literals;
enum{UNIT_FIELD_FLAGS,UNIT_FLAG_REMOVE_CLIENT_CONTROL,TEMPSUMMON_TIMED_DESPAWN,NPC_BLOODFANG_WORGEN_35118=35118,SPELL_CANNON_FIRE=68235};
struct ObjectGuid{int id;};
struct Creature;struct Cannon;std::map<int,Creature*>registry;
struct Creature{int entry=35118,id=0,despawns=0,casts=0,target=0,attempts=0;bool alive=true,phase=true,near=true,fail=false;Cannon*ai=nullptr;std::vector<std::unique_ptr<Creature>>owned;
bool IsAlive(){return alive;}int GetEntry(){return entry;}bool IsInPhase(Creature*){return phase;}bool IsWithinDistInMap(Creature*c,float){return c->near;}void SetFlag(int,int){}void CastSpell(Creature*c,int,bool){++casts;target=c->id;}Creature*SummonCreature(int,float,float,float,int,int,int);};
namespace ObjectAccessor{Creature*GetCreature(Creature&,ObjectGuid g){auto it=registry.find(g.id);return it==registry.end()?nullptr:it->second;}}
struct SummonList:std::vector<ObjectGuid>{explicit SummonList(Creature*){}void Summon(Creature*c){push_back({c->id});}void Despawn(Creature*c){for(auto it=begin();it!=end();++it)if(it->id==c->id){erase(it);break;}}void DespawnAll(){for(auto g:*this){auto i=registry.find(g.id);if(i!=registry.end())++i->second->despawns;}clear();}};
struct EventMap{uint32 now=0;std::multimap<uint32,uint32>pending;void Reset(){pending.clear();}void Update(uint32 d){now+=d;}void ScheduleEvent(uint32 e,uint32 t){pending.emplace(now+t,e);}void ScheduleEvent(uint32 e,std::chrono::milliseconds t){ScheduleEvent(e,uint32(t.count()));}uint32 ExecuteEvent(){auto i=pending.begin();if(i==pending.end()||i->first>now)return 0;uint32 e=i->second;pending.erase(i);return e;}};
int irand(int,int){return 0;}int urand(int,int){return 0;}
struct Cannon{Creature*me;EventMap m_events;SummonList m_summons;bool m_sceneActive=false;explicit Cannon(Creature*c):me(c),m_summons(c){c->ai=this;}ENUM METHODS};
Creature*Creature::SummonCreature(int,float,float,float,int,int,int){++attempts;if(fail)return nullptr;auto p=std::make_unique<Creature>();p->id=int(owned.size())+1;auto*c=p.get();owned.push_back(std::move(p));registry[c->id]=c;ai->JustSummoned(c);return c;}
void check(bool b,char const*m){if(!b)throw std::runtime_error(m);}
struct Scene{Creature gun,foreign;Cannon ai;Scene():ai(&gun){registry.clear();foreign.id=999;registry[999]=&foreign;}void start(){ai.DoAction(101);ai.DoAction(101);ai.UpdateAI(25);}};
int main(){
{Scene s;s.start();check(s.gun.attempts==12,"duplicate start spawned multiple waves");s.ai.UpdateAI(400);check(s.gun.casts==1&&s.gun.target!=999,"must shoot own actor");s.ai.DoAction(101);s.ai.UpdateAI(100);check(s.gun.attempts==12,"active scene started again");s.ai.Reset();check(s.foreign.despawns==0&&s.ai.m_summons.empty()&&s.ai.m_events.pending.empty(),"scoped reset");for(auto const&c:s.gun.owned)check(c->despawns==1,"own cleanup once");s.ai.Reset();for(auto const&c:s.gun.owned)check(c->despawns==1,"reset repeated cleanup");}
{Scene s;s.gun.fail=true;s.start();s.ai.UpdateAI(400);check(s.gun.casts==0,"summon failure must not hit foreign target");}
for(int mode=0;mode<3;++mode){Scene s;s.start();for(auto const&c:s.gun.owned){if(mode==0)c->alive=false;if(mode==1)c->phase=false;if(mode==2)c->near=false;}s.ai.UpdateAI(400);check(s.gun.casts==0,"invalid owned targets must not hit foreign NPC");}
{Scene s;s.start();auto*c=s.gun.owned.front().get();s.ai.SummonedCreatureDespawn(c);registry.erase(c->id);s.ai.UpdateAI(400);check(s.gun.casts==1&&s.gun.target!=c->id,"expired summon skipped");s.ai.UpdateAI(4600);check(!s.ai.m_sceneActive,"bounded scene ends");}
std::cout<<"PASS: cannon production own-target selection, duplicate waves, summon failure and scoped cleanup\n";}
"""
    code=code.replace('ENUM',method(source,'    enum eNpc')+';').replace('METHODS','\n'.join(method(source,m).replace(' override','') for m in ['        void Reset(','        void JustSummoned(','        void SummonedCreatureDespawn(','        void DoAction(','        void UpdateAI(']))
    with tempfile.TemporaryDirectory() as directory:
        cpp=Path(directory)/'cannon.cpp';exe=Path(directory)/'cannon.exe';cpp.write_text(code,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
