#!/usr/bin/env python3
"""Exercise actual SceneMgr and scene-aura code under recursive script callbacks."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Entities/Player/SceneMgr.cpp').read_text('utf8')
    names=['PlaySceneByTemplate','PlaySceneByPackageId','CancelScene','OnSceneTrigger','OnSceneCancel','OnSceneComplete','HasScene','AddInstanceIdToSceneMap','CancelSceneBySceneId','CancelSceneByPackageId','RemoveSceneInstanceId','RemoveAurasDueToSceneId','GetSceneTemplateFromInstanceId','GetActiveSceneCount']
    methods='\n'.join(re.search(r'^[^\n]+ SceneMgr::'+name+r'\([^\n]*\)(?: const)?\n\{.*?^\}',source,re.M|re.S)[0] for name in names)
    guard=re.search(r'    struct SceneEndGuard\n    \{.*?\n    \};',source,re.S)[0]
    aura_source=(root/'src/server/game/Spells/Auras/SpellAuraEffects.cpp').read_text('utf8')
    aura=re.search(r'^void AuraEffect::HandlePlayScene\([^\n]*\) const\n\{.*?^\}',aura_source,re.M|re.S)[0]
    header=(root/'src/server/game/Entities/Player/SceneMgr.h').read_text('utf8')
    assert 'std::set<uint32> _endingScenes;' in header
    harness=r'''
#include <cstdint>
#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
using uint32=std::uint32_t;using uint8=std::uint8_t;
constexpr uint32 SCENEFLAG_UNK16=16,SCENEFLAG_CANCEL_AT_END=2,AURA_EFFECT_HANDLE_REAL=1,SPELL_AURA_PLAY_SCENE=430;
constexpr uint32 LANG_COMMAND_SCENE_DEBUG_PLAY=1,LANG_COMMAND_SCENE_DEBUG_TRIGGER=2,LANG_COMMAND_SCENE_DEBUG_CANCEL=3,LANG_COMMAND_SCENE_DEBUG_COMPLETE=4;
struct Position{float x=1;};struct Packet{uint32 kind,id;};
namespace WorldPackets{namespace Scenes{
struct PlayScene{uint32 SceneID=0,PlaybackFlags=0,SceneInstanceID=0,SceneScriptPackageID=0;Position Location;uint32 TransportGUID=0;Packet packet;Packet const* Write(){packet={1,SceneInstanceID};return &packet;}};
struct CancelScene{uint32 SceneInstanceID=0;Packet packet;Packet const* Write(){packet={2,SceneInstanceID};return &packet;}};
}}
struct SceneTemplate{uint32 SceneId=0,PlaybackFlags=0,ScenePackageId=0,ScriptId=0;};
struct SceneScriptPackageEntry{uint32 ID;};
struct PackageStore{std::map<uint32,SceneScriptPackageEntry> rows;SceneScriptPackageEntry const* LookupEntry(uint32 id){auto i=rows.find(id);return i==rows.end()?nullptr:&i->second;}} sSceneScriptPackageStore;
struct ObjectMgr{std::map<uint32,SceneTemplate> rows;SceneTemplate const* GetSceneTemplate(uint32 id){auto i=rows.find(id);return i==rows.end()?nullptr:&i->second;}} objectMgr;ObjectMgr* sObjectMgr=&objectMgr;
struct ChatHandler{explicit ChatHandler(void*){}template<class...T>void PSendSysMessage(T...) {}};
struct Player;struct Aura;struct AuraEffect;struct AuraApplication;
struct SceneMgr{Player* _player;bool _isDebuggingScenes=false;uint32 next=0;
 std::map<uint32,SceneTemplate> _scenesByInstance;std::set<uint32> _endingScenes;
 explicit SceneMgr(Player* player):_player(player){}Player* GetPlayer()const{return _player;}
 uint32 GetNewStandaloneSceneInstanceID(){return ++next;}
 uint32 PlaySceneByTemplate(SceneTemplate,Position const* =nullptr);uint32 PlaySceneByPackageId(uint32,uint32=16,Position const* =nullptr);
 void CancelScene(uint32,bool=true);void OnSceneTrigger(uint32,std::string const&);void OnSceneCancel(uint32);void OnSceneComplete(uint32);
 bool HasScene(uint32,uint32=0)const;void AddInstanceIdToSceneMap(uint32,SceneTemplate);
 void CancelSceneBySceneId(uint32);void CancelSceneByPackageId(uint32);void RemoveSceneInstanceId(uint32);void RemoveAurasDueToSceneId(uint32);
 SceneTemplate const* GetSceneTemplateFromInstanceId(uint32)const;uint32 GetActiveSceneCount(uint32=0)const;
};
struct Player:Position{using AuraEffectList=std::list<AuraEffect*>;SceneMgr* mgr=nullptr;AuraEffectList effects;std::vector<Packet> sent;unsigned auraRemovals=0;
 Player* ToPlayer(){return this;}void* GetSession(){return nullptr;}uint32 GetTransGUID(){return 0;}
 SceneMgr& GetSceneMgr(){return *mgr;}void SendDirectMessage(Packet const* p){sent.push_back(*p);}
 AuraEffectList const& GetAuraEffectsByType(uint32)const{return effects;}void RemoveAura(Aura*);
};
struct Aura{AuraEffect* effect=nullptr;};
struct AuraEffect{uint32 misc;Aura* base=nullptr;uint32 GetMiscValue()const{return misc;}Aura* GetBase()const{return base;}
 void HandlePlayScene(AuraApplication const*,uint8,bool)const;
};
struct AuraApplication{Player* target;Player* GetTarget()const{return target;}};
struct ScriptMgr{unsigned modern=0,legacy=0,triggers=0,legacyTriggers=0,starts=0;
 std::function<void(Player*,uint32,SceneTemplate const*)> finish;
 std::function<void(Player*,uint32)> oldFinish;
 std::function<void(Player*,uint32,SceneTemplate const*)> trigger;
 void OnSceneStart(Player*,uint32,SceneTemplate const*){++starts;}void OnSceneStart(Player*,uint32,uint32){}
 void OnSceneTrigger(Player* p,uint32 id,SceneTemplate const* t,std::string const&){++triggers;if(trigger)trigger(p,id,t);}
 void OnSceneTriggerEvent(Player*,uint32,std::string const&){++legacyTriggers;}
 void OnSceneComplete(Player* p,uint32 id,SceneTemplate const* t){++modern;if(finish)finish(p,id,t);}
 void OnSceneCancel(Player* p,uint32 id,SceneTemplate const* t){++modern;if(finish)finish(p,id,t);}
 void OnSceneComplete(Player* p,uint32 id){++legacy;if(oldFinish)oldFinish(p,id);}
 void OnSceneCancel(Player* p,uint32 id){++legacy;if(oldFinish)oldFinish(p,id);}
} scriptMgr;ScriptMgr* sScriptMgr=&scriptMgr;
GUARD
METHODS
AURA
void Player::RemoveAura(Aura* a){++auraRemovals;AuraApplication app{this};a->effect->HandlePlayScene(&app,AURA_EFFECT_HANDLE_REAL,false);effects.remove(a->effect);}
void check(bool ok,char const* text){if(!ok)throw std::runtime_error(text);}
int main(){
 Player player;SceneMgr mgr(&player);player.mgr=&mgr;sSceneScriptPackageStore.rows={{9,{9}},{10,{10}}};
 SceneTemplate one{100,2,9,0},two{101,2,9,0};objectMgr.rows={{100,one},{101,two}};
 check(!mgr.PlaySceneByTemplate({102,2,99,0}),"missing package started scene");
 auto a=mgr.PlaySceneByTemplate(one),b=mgr.PlaySceneByTemplate(two);
 check(a&&b&&a!=b&&mgr.GetActiveSceneCount()==2&&mgr.GetActiveSceneCount(9)==2&&scriptMgr.starts==2,"scene creation identity or package count");
 Aura base;AuraEffect effect{100,&base};base.effect=&effect;AuraApplication application{&player};
 effect.HandlePlayScene(&application,AURA_EFFECT_HANDLE_REAL,false);
 check(!mgr.HasScene(a)&&mgr.HasScene(b),"aura removal cancelled different scene sharing package");
 effect.HandlePlayScene(&application,0,true);check(mgr.GetActiveSceneCount()==1,"non-real aura mode played scene");
 effect.HandlePlayScene(&application,AURA_EFFECT_HANDLE_REAL,true);check(mgr.GetActiveSceneCount()==2,"native aura application did not start scene");
 mgr.CancelSceneBySceneId(100);mgr.CancelSceneByPackageId(9);check(!mgr.GetActiveSceneCount(),"ID/package cancellation snapshot");
 // Modern callback erases its map entry and then still reads the template.
 for(bool completed:{false,true}){
  scriptMgr.finish=[&](Player* p,uint32 id,SceneTemplate const* t){p->GetSceneMgr().CancelScene(id);check(t->SceneId==100&&t->PlaybackFlags==2&&t->ScenePackageId==9,"callback used freed scene template");};
  scriptMgr.oldFinish={};auto id=mgr.PlaySceneByTemplate(one);auto modern=scriptMgr.modern,legacy=scriptMgr.legacy;auto packets=player.sent.size();
  if(completed)mgr.OnSceneComplete(id);else mgr.OnSceneCancel(id);
  check(!mgr.HasScene(id)&&scriptMgr.modern==modern+1&&scriptMgr.legacy==legacy+1&&player.sent.size()==packets+1,"erasing callback or duplicate cancel packet");
  mgr.OnSceneComplete(id);mgr.OnSceneCancel(id);check(scriptMgr.modern==modern+1,"duplicate terminal event replay");
 }
 // Reentry through modern and legacy callbacks must not duplicate rewards.
 for(bool completed:{false,true}){
  scriptMgr.finish=[&](Player* p,uint32 id,SceneTemplate const*){p->GetSceneMgr().OnSceneComplete(id);p->GetSceneMgr().OnSceneCancel(id);p->GetSceneMgr().OnSceneTrigger(id,"late");};
  scriptMgr.oldFinish=[&](Player* p,uint32 id){p->GetSceneMgr().OnSceneComplete(id);p->GetSceneMgr().OnSceneCancel(id);};
  auto id=mgr.PlaySceneByTemplate(one);auto modern=scriptMgr.modern,legacy=scriptMgr.legacy,triggers=scriptMgr.triggers;
  if(completed)mgr.OnSceneComplete(id);else mgr.OnSceneCancel(id);
  check(scriptMgr.modern==modern+1&&scriptMgr.legacy==legacy+1&&scriptMgr.triggers==triggers&&mgr._endingScenes.empty(),"recursive terminal callback duplicated or leaked guard");
 }
 // Finishing another instance remains allowed while this instance is ending.
 scriptMgr.oldFinish={};auto outer=mgr.PlaySceneByTemplate(one),other=mgr.PlaySceneByTemplate(two);
 scriptMgr.finish=[&](Player* p,uint32 id,SceneTemplate const*){if(id==outer)p->GetSceneMgr().OnSceneComplete(other);};
 auto modern=scriptMgr.modern;mgr.OnSceneComplete(outer);check(scriptMgr.modern==modern+2&&!mgr.HasScene(other)&&mgr._endingScenes.empty(),"guard blocked unrelated instance");
 // A legacy callback may erase the entry, too.
 scriptMgr.finish={};scriptMgr.oldFinish=[](Player* p,uint32 id){p->GetSceneMgr().CancelScene(id);};
 auto id=mgr.PlaySceneByTemplate(one);mgr.OnSceneComplete(id);check(!mgr.HasScene(id),"legacy cancellation");
 scriptMgr.oldFinish={};
 // Trigger snapshot survives callback cancellation and the legacy hook still runs.
 scriptMgr.trigger=[](Player* p,uint32 id,SceneTemplate const* t){p->GetSceneMgr().CancelScene(id);check(t->SceneId==100,"trigger snapshot invalidated");};
 id=mgr.PlaySceneByTemplate(one);auto legacyTriggers=scriptMgr.legacyTriggers;mgr.OnSceneTrigger(id,"done");
 check(!mgr.HasScene(id)&&scriptMgr.legacyTriggers==legacyTriggers+1,"trigger cancellation ordering");scriptMgr.trigger={};
 // Erase map entry before removing the aura; do not cancel another scene.
 player.effects.push_back(&effect);id=mgr.PlaySceneByTemplate(one);other=mgr.PlaySceneByTemplate(two);auto removals=player.auraRemovals;
 mgr.OnSceneComplete(id);check(player.auraRemovals==removals+1&&player.effects.empty()&&mgr.HasScene(other),"aura removal reached other scene or reentered completion");mgr.CancelScene(other);
 // Scope cleanup on exception permits a later valid completion.
 scriptMgr.finish=[](Player*,uint32,SceneTemplate const*){throw std::runtime_error("fixture");};id=mgr.PlaySceneByTemplate(one);
 bool threw=false;try{mgr.OnSceneComplete(id);}catch(std::runtime_error const&){threw=true;}check(threw,"callback exception not propagated");
 check(mgr._endingScenes.empty()&&mgr.HasScene(id),"exception leaked ending guard");scriptMgr.finish={};mgr.OnSceneComplete(id);
 // Standalone package scene with SceneId=0 must not remove an aura.
 id=mgr.PlaySceneByPackageId(9);removals=player.auraRemovals;mgr.OnSceneComplete(id);check(removals==player.auraRemovals&&!mgr.GetActiveSceneCount(),"standalone scene removed aura");
 std::cout<<"PASS: fourteen native SceneMgr methods and scene-aura handler; callback lifetime, reentry, duplicate events, scoped cancellation and cleanup\n";
}
'''
    harness=harness.replace('GUARD',guard).replace('METHODS',methods).replace('\nAURA\n','\n'+aura+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'scenes.cpp';exe=Path(tmp)/'scenes';cpp.write_text(harness,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-D_GLIBCXX_DEBUG',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True,timeout=30)


if __name__=='__main__':main()
