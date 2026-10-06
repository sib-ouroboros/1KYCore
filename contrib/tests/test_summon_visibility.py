#!/usr/bin/env python3
"""Native personal visibility API and detection block through base/derived pointers."""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');p.add_argument('--temporary-summon-header',type=Path);args=p.parse_args()
 root=Path(__file__).resolve().parents[2]
 header=(root/'src/server/game/Entities/Object/Object.h').read_text('utf8');source=(root/'src/server/game/Entities/Object/Object.cpp').read_text('utf8');summon=(args.temporary_summon_header or root/'src/server/game/Entities/Creature/TemporarySummon.h').read_text('utf8')
 part=summon[summon.index('class TC_GAME_API TempSummon'):];part=part[:part.index('class TC_GAME_API Minion')]
 api='';field=''
 for name in ('void SetVisibleBySummonerOnly(', 'bool IsVisibleBySummonerOnly('):
  if name in part:api+=method(part,name)+'\n'
 if re.search(r'bool m_visibleBySummonerOnly;',part):field='bool m_visibleBySummonerOnly=false;'
 setter=method(header,'        void SetVisibleBySummonerOnly(');getter=method(header,'        bool IsVisibleBySummonerOnly(')
 detection=method(source,'            if (obj->IsVisibleBySummonerOnly())')
 native_assignment=re.search(r'    summon->SetVisibleBySummonerOnly\(visibleBySummonerOnly\);',source)[0]
 code=r"""
#include <stdexcept>
#include <iostream>
struct Guid{int id=0;};bool operator!=(Guid a,Guid b){return a.id!=b.id;}
struct Creature;struct TempSummon;struct GameObject;
struct WorldObject{bool m_visibleBySummonerOnly=false;Guid guid;
 virtual ~WorldObject()=default;virtual Creature const*ToCreature()const{return nullptr;}virtual GameObject const*ToGameObject()const{return nullptr;}Guid GetGUID()const{return guid;}
"""+setter+getter+r"""
 bool Visible(WorldObject const*obj)const;
};
struct Creature:WorldObject{Creature const*ToCreature()const override{return this;}virtual TempSummon const*ToTempSummon()const{return nullptr;}};
struct TempSummon:Creature{Guid summoner;TempSummon const*ToTempSummon()const override{return this;}Guid GetSummonerGUID()const{return summoner;}
"""+api+field+r"""
};
struct GameObject:WorldObject{Guid owner;GameObject const*ToGameObject()const override{return this;}Guid GetOwnerGUID()const{return owner;}};
bool WorldObject::Visible(WorldObject const*obj)const {
"""+detection+r"""
return true;}
void NativeMapVisibility(TempSummon* summon,bool visibleBySummonerOnly){
"""+native_assignment+r"""
}
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
int main(){try{WorldObject owner,stranger;owner.guid.id=1;stranger.guid.id=2;TempSummon npc;npc.summoner.id=1;WorldObject*base=&npc;
 check(!npc.IsVisibleBySummonerOnly()&&!base->IsVisibleBySummonerOnly()&&owner.Visible(base)&&stranger.Visible(base),"public summon unchanged");
 NativeMapVisibility(&npc,true);check(npc.IsVisibleBySummonerOnly()&&base->IsVisibleBySummonerOnly(),"native Map setter shares WorldObject flag");
 check(owner.Visible(base)&&!stranger.Visible(base),"only owner detects private summon");
 npc.SetVisibleBySummonerOnly(false);check(owner.Visible(base)&&stranger.Visible(base),"derived reset restores public visibility");
 base->SetVisibleBySummonerOnly(true);check(npc.IsVisibleBySummonerOnly()&&!stranger.Visible(base),"base setter and derived getter agree");
 Creature ordinary;check(owner.Visible(&ordinary)&&stranger.Visible(&ordinary),"ordinary public NPC unchanged");
 GameObject go;go.owner.id=1;go.SetVisibleBySummonerOnly(true);check(owner.Visible(&go)&&!stranger.Visible(&go),"private GO behavior unchanged");
 std::cout<<"Native summon visibility state, owner isolation and public NPC behavior: PASS\n";
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
