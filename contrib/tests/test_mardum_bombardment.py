#!/usr/bin/env python3
"""Compile actual quest 38727 handlers against the shared Mardum fixtures.

Not a worldserver/client visual test; covers ordering, ownership and rollback.
"""
from pathlib import Path
import argparse,ast,os,subprocess,tempfile
from test_mardum_invasion import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2]
 source=(root/'src/server/scripts/BrokenIsles/DemonHunterZones/zone_mardum.cpp').read_text('utf8')
 tree=ast.parse((root/'contrib/tests/test_mardum_invasion.py').read_text('utf8'))
 # Reuse the same minimal entity interfaces, without running the other test.
 prefix=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign)
     and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets) and isinstance(n.value,ast.Constant))
 prefix=prefix.replace('REAL_QUEST_STATUS',method((root/'src/server/game/Quests/QuestDef.h').read_text('utf8'),'enum QuestStatus : uint8')+';')
 prefix=prefix.replace('using uint32=', 'using int8=std::int8_t;using uint32=')
 prefix=prefix.replace('struct Player;struct Creature;', 'constexpr uint32 EMOTE_ONESHOT_SPELL_CAST=51;\nstruct Player;struct Creature;')
 prefix=prefix.replace('int entry=0,map=1481,guid=0;', 'bool dead=false;int freezes=0,hides=0;\n int entry=0,map=1481,guid=0;')
 prefix=prefix.replace('void SetWalk(bool value)', '''Position const& GetPosition(){return position;}
 void SetFacingToObject(Creature*){}bool IsAlive(){return !dead;}void KillSelf(){dead=true;}
 void CastSpell(Creature* target,uint32 spell,bool){if(target!=this||spell!=191568)throw std::runtime_error("unsafe spell execution");++freezes;}
 void RemoveAurasDueToSpell(uint32){}void DestroyForPlayer(Player*){++hides;}
 void SetWalk(bool value)''')
 prefix=prefix.replace('unsigned summons=0,failAt=99;', 'bool failAI=false;int objective[6]={0};std::vector<uint32> credits;unsigned summons=0,failAt=99;')
 prefix=prefix.replace('Session* GetSession()', 'int GetQuestObjectiveData(uint32,int8 slot){return objective[slot];}void KilledMonsterCredit(uint32 id){credits.push_back(id);}\n Session* GetSession()')
 prefix=prefix.replace('c->ai=new ScriptedAI(c);actors.push_back(c);', 'c->guid=int(world.size())+10;c->initOK=!failAI;c->ai=new ScriptedAI(c);actors.push_back(c);')
 prefix+=r'''
namespace ObjectAccessor{Creature* GetCreature(Creature&,int guid){for(auto* c:world)if(c->guid==guid&&!c->removed)return c;return nullptr;}}
namespace WorldPackets{namespace Spells{struct PlaySpellVisual{
 int Source=0,Target=0;uint32 SpellVisualID=0;float TravelSpeed=0;bool SpeedAsTime=false;FakePacket packet;
 FakePacket* Write(){packet.value=int(SpellVisualID);return &packet;}
};}}
struct GameObject{
 uint32 entry=0;Creature* original=nullptr;Position position{0,0,0,0};
 uint32 GetEntry(){return entry;}Position const& GetPosition(){return position;}
 void GetCreatureListWithEntryInGrid(std::list<Creature*>& out,uint32 id,float){if(!original)return;for(auto*c:world)if(c!=original&&c->entry==int(id)&&!c->removed)out.push_back(c);if(original->entry==int(id))out.push_back(original);}
};
struct GameObjectScript{explicit GameObjectScript(char const*){}virtual ~GameObjectScript()=default;virtual bool OnGossipHello(Player*,GameObject*){return false;}};
'''
 prefix=prefix.replace('struct Session{', 'using WorldPacket=FakePacket;struct UpdateData{explicit UpdateData(int){}void BuildPacket(FakePacket* p){p->value=999;}};\nstruct Session{')
 prefix=prefix.replace('bool dead=false;int freezes=0,hides=0;', 'bool dead=false;int freezes=0,hides=0,recreates=0;void BuildCreateUpdateBlockForPlayer(UpdateData*,Player*){++recreates;}int GetDisplayId(){return 66377;}void SetDisplayId(int){}')
 actor=source[source.index('struct MardumInvasionSpawn'):source.index('struct MardumInvasionActorAI :')]+method(source,'struct MardumInvasionActorAI :')+';'
 start=source.index('namespace\n{\nconstexpr uint32 QuestStopBombardment');end=source.index('class go_mardum_tome_of_fel_secrets :',start)
 block=source[start:end]
 updates=(root/'src/server/game/Entities/Object/Updates/UpdateFields.h').read_text('utf8')
 assert '    UNIT_NPC_FLAGS ' in updates and 'UNIT_FIELD_NPC_FLAGS' not in block
 suffix=r'''
int main(){
 go_mardum_illidari_banner handler;
 Player a,b;b.guid=2;players[1]=&a;players[2]=&b;
 textMgr.texts[96877][0]={{0,12,0,55037,0,0}};
 textMgr.texts[96884][0]={{0,12,0,55083,0,0}};
 textMgr.texts[96888][0]={{0,12,0,55354,0,0}};
 Creature shared;shared.guid=1;world.push_back(&shared);GameObject flag;flag.original=&shared;
 for(auto const& row:BombardmentTargets){
  flag.entry=row.banner;shared.entry=row.devastator;a.credits.clear();a.sounds.clear();a.lines.clear();
  auto n=a.actors.size();require(handler.OnGossipHello(&a,&flag),"handled flag");
  require(a.actors.size()==n+2&&a.credits.empty(),"scene before credit");
  auto* copy=a.actors[n];auto* helper=a.actors[n+1];
  require(copy->personal&&helper->personal&&helper->owner==a.guid&&copy->lifetime==20000,"private bounded actors");
  handler.OnGossipHello(&a,&flag);require(a.actors.size()==n+2,"repeat click blocked");
  auto nb=b.actors.size();handler.OnGossipHello(&b,&flag);require(b.actors.size()==nb+2&&copy->hides==0,"other owner independent; private copies excluded as source");
  helper->ai->UpdateAI(100);require(a.lines.back()==int(row.helper)*10&&b.lines.empty(),"owner dialogue");
  helper->ai->UpdateAI(1900);require(a.sounds.back()==51328&&!copy->dead&&a.credits.empty(),"visual attack without immediate kill/credit");
  require(copy->freezes==(row.helper==96884?1:0),"Coilskar freeze only");
  helper->ai->UpdateAI(4000);require(copy->dead&&a.credits==std::vector<uint32>({row.devastator,row.credit}),"paired credit after destruction");
  require(a.sounds.back()==49571&&!shared.dead&&!shared.removed,"private fire; shared spawn intact");
  helper->ai->UpdateAI(1);require(a.credits.size()==2,"no duplicate credit");
  a.objective[row.storageIndex]=a.objective[row.storageIndex-1]=1;handler.OnGossipHello(&a,&flag);require(a.actors.size()==n+2,"completed target cannot repeat");
  helper->ai->UpdateAI(8000);require(helper->removed&&copy->removed,"normal cleanup");
  a.objective[row.storageIndex]=a.objective[row.storageIndex-1]=0;players.erase(2);b.actors[nb+1]->ai->UpdateAI(1);
  require(b.actors[nb]->removed&&b.actors[nb+1]->removed&&b.credits.empty(),"logout cancels only owner");players[2]=&b;
 }
 a.objective[1]=1;flag.entry=243965;shared.entry=93762;
 auto partial=a.actors.size();handler.OnGossipHello(&a,&flag);require(a.actors.size()==partial+2,"partial objective remains repairable");a.actors.back()->ai->UpdateAI(20000);a.objective[1]=0;
 auto n=a.actors.size();a.status=QUEST_STATUS_NONE;handler.OnGossipHello(&a,&flag);require(a.actors.size()==n,"quest required");
 a.status=QUEST_STATUS_INCOMPLETE;a.map=1;handler.OnGossipHello(&a,&flag);require(a.actors.size()==n,"map required");
 a.map=1481;a.klass=1;handler.OnGossipHello(&a,&flag);require(a.actors.size()==n,"class required");a.klass=12;
 flag.original=nullptr;handler.OnGossipHello(&a,&flag);require(a.actors.size()==n,"missing machine has no credit");flag.original=&shared;
 for(unsigned fail:{a.summons,a.summons+1}){a.failAt=fail;handler.OnGossipHello(&a,&flag);for(auto*c:a.actors)require(c->removed,"partial summon rollback");}
 a.failAt=999;a.failAI=true;handler.OnGossipHello(&a,&flag);for(auto*c:a.actors)require(c->removed,"failed AI rollback");a.failAI=false;
 handler.OnGossipHello(&a,&flag);auto* copy=a.actors[a.actors.size()-2];auto* helper=a.actors.back();a.status=QUEST_STATUS_NONE;helper->ai->UpdateAI(6000);require(shared.recreates==1,"cancel restores shared client object");require(copy->removed&&helper->removed&&!copy->dead,"abandon before credit");
 a.status=QUEST_STATUS_INCOMPLETE;handler.OnGossipHello(&a,&flag);helper=a.actors.back();a.near=false;helper->ai->UpdateAI(6000);require(helper->removed,"leave scene cancels");a.near=true;
 handler.OnGossipHello(&a,&flag);helper=a.actors.back();a.credits.clear();helper->ai->UpdateAI(20000);require(a.credits.size()==2&&helper->removed,"large tick remains ordered and bounded");
 for(auto*c:world)if(c!=&shared)delete c;
 std::cout<<"PASS: actual quest 38727 handlers, three crews, delayed credit, safe visuals, multiplayer, rollback and cancellation\n";
}
'''
 with tempfile.TemporaryDirectory(prefix='mardum-bombardment-') as tmp:
  src=Path(tmp)/'test.cpp';exe=Path(tmp)/('test.exe' if os.name=='nt' else 'test');src.write_text(prefix+actor+block+suffix,encoding='utf8')
  flags=['-std=c++17','-Wall','-Wextra','-Werror','-g']
  if not args.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),*flags,str(src),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
