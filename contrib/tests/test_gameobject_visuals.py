#!/usr/bin/env python3
"""Compile real addon loader and GO visual/state methods with test interfaces."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def block(text, signature):
    start=text.index(signature);opening=text.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    go=(root/'src/server/game/Entities/GameObject/GameObject.cpp').read_text('latin1')
    mgr=(root/'src/server/game/Globals/ObjectMgr.cpp').read_text('latin1')
    data=(root/'src/server/game/Entities/GameObject/GameObjectData.h').read_text('latin1')
    addon=block(data,'struct GameObjectTemplateAddon\n')+';'
    functions='\n'.join([block(mgr,'void ObjectMgr::LoadGameObjectTemplateAddons()'),block(go,'void GameObject::ApplyTemplateVisuals('),block(go,'void GameObject::SetGoState(')])
    create=block(go,'bool GameObject::Create(')
    assert create.index('SetGoState(goState);') < create.index('ApplyTemplateVisuals(true, goState);')
    header=r'''
#include <cstdint>
#include <map>
#include <array>
#include <vector>
#include <memory>
#include <string>
#include <iostream>
#include <stdexcept>
using uint16=std::uint16_t;using uint32=std::uint32_t;
ADDON
constexpr uint32 GO_STATE_ACTIVE=0,GO_STATE_READY=1,GO_STATE_ACTIVE_ALTERNATIVE=2;
using GOState=uint32;
constexpr uint32 GAMEOBJECT_BYTES_1=100,GAMEOBJECT_SPELL_VISUAL_ID=101,GAMEOBJECT_STATE_SPELL_VISUAL_ID=102,GAMEOBJECT_STATE_WORLD_EFFECT_ID=103;
constexpr uint32 GAMEOBJECT_TYPE_CHEST=3,GAMEOBJECT_TYPE_FISHINGHOLE=25;
struct GameObjectTemplate {uint32 type=5;};
struct Field {uint32 value=0;uint32 GetUInt32()const{return value;}uint16 GetUInt16()const{return static_cast<uint16>(value);}};
struct Result {std::vector<std::array<Field,9>> rows;std::size_t position=0;Field* Fetch(){return rows[position].data();}bool NextRow(){return ++position<rows.size();}};
using QueryResult=std::unique_ptr<Result>;
struct Database {std::vector<std::array<Field,9>> fixture;std::string query;uint32 visualColumnCount=3;QueryResult Query(char const* q){query=q;if(query.find("information_schema.COLUMNS")!=std::string::npos){std::array<Field,9> count{};count[0].value=visualColumnCount;return std::make_unique<Result>(Result{{count}});}if(fixture.empty())return nullptr;return std::make_unique<Result>(Result{fixture});}} WorldDatabase;
uint32 getMSTime(){return 0;}uint32 GetMSTimeDiffToNow(uint32){return 0;}
template<class... Args>void testLog(Args const&...){}
#define TC_LOG_INFO(...) testLog(__VA_ARGS__)
#define TC_LOG_ERROR(...) testLog(__VA_ARGS__)
struct Store {bool LookupEntry(uint32 id){return id==5424 || id==1;}} sWorldEffectStore,sFactionTemplateStore;
struct ObjectMgr {std::map<uint32,GameObjectTemplate> templates;std::map<uint32,GameObjectTemplateAddon> _gameObjectTemplateAddonStore;
GameObjectTemplate const* GetGameObjectTemplate(uint32 id){auto i=templates.find(id);return i==templates.end()?nullptr:&i->second;}void LoadGameObjectTemplateAddons();} manager;
ObjectMgr* sObjectMgr=&manager;
struct Scripts {uint32 calls=0;bool alterState=false;template<class T>void OnGameObjectStateChanged(T* object,uint32){++calls;if(alterState)object->state=GO_STATE_READY;}} scripts;
Scripts* sScriptMgr=&scripts;
struct GameObject {GameObjectTemplateAddon const* m_goTemplateAddon=nullptr;bool m_model=false,inWorld=true,transport=false;uint32 state=GO_STATE_ACTIVE;std::map<uint32,uint32> fields;uint32 collisions=0;
uint32 GetGoState()const{return state;}bool IsTransport()const{return transport;}bool IsInWorld()const{return inWorld;}
void SetUInt32Value(uint32 f,uint32 v){fields[f]=v;}void SetByteValue(uint32,uint32,uint32 s){state=s;}void EnableCollision(bool){++collisions;}
void ApplyTemplateVisuals(bool initial, GOState state);void SetGoState(GOState state);};
void check(bool ok,char const* reason){if(!ok)throw std::runtime_error(reason);}
'''.replace('ADDON',addon)
    harness=r'''
int main(){try {
manager.templates.emplace(267180,GameObjectTemplate{});
std::array<Field,9> row{};row[0].value=267180;row[2].value=262144;row[6].value=8742;row[7].value=8743;row[8].value=5424;
WorldDatabase.fixture={row};manager.LoadGameObjectTemplateAddons();
check(WorldDatabase.query=="SELECT entry, faction, flags, mingold, maxgold, WorldEffectID, SpellVisualID, SpellStateVisualID, StateWorldEffectID FROM gameobject_template_addon","actual loader selects all nine fields");
auto const& loaded=manager._gameObjectTemplateAddonStore.at(267180);check(loaded.SpellVisualID==8742 && loaded.SpellStateVisualID==8743 && loaded.StateWorldEffectID==5424,"exact loader columns");
for(uint32 count:{0U,1U,2U}){WorldDatabase.visualColumnCount=count;manager.LoadGameObjectTemplateAddons();check(WorldDatabase.query=="SELECT entry, faction, flags, mingold, maxgold, WorldEffectID FROM gameobject_template_addon","legacy query fallback");check(loaded.flags==262144 && loaded.SpellVisualID==0 && loaded.SpellStateVisualID==0 && loaded.StateWorldEffectID==0,"legacy addon flags preserved, optional fields disabled");}
WorldDatabase.visualColumnCount=3;
row[8].value=999999;WorldDatabase.fixture={row};manager.LoadGameObjectTemplateAddons();check(loaded.StateWorldEffectID==0,"invalid world effect rejected");
row[8].value=5424;WorldDatabase.fixture={row};manager.LoadGameObjectTemplateAddons();
GameObject object;object.m_goTemplateAddon=&loaded;object.m_model=true;object.inWorld=false;object.SetGoState(GO_STATE_ACTIVE);check(object.fields.empty(),"pre-world state path keeps source early return");
object.ApplyTemplateVisuals(true, GO_STATE_ACTIVE);check(object.fields.at(101)==8742 && object.fields.at(102)==8743 && object.fields.at(103)==5424,"Create initializes visuals even for active spawn");
object.inWorld=true;object.SetGoState(GO_STATE_ACTIVE);check(object.fields.at(101)==0 && object.fields.at(102)==8743 && object.fields.at(103)==0,"activation clears ordinary/world visuals and retains state visual");
object.SetGoState(GO_STATE_READY);check(object.fields.at(101)==8742 && object.fields.at(102)==8743 && object.fields.at(103)==5424,"ready restores visuals");
object.SetGoState(GO_STATE_ACTIVE_ALTERNATIVE);check(object.fields.at(101)==0 && object.fields.at(102)==8743 && object.fields.at(103)==0,"alternative active follows source");
check(object.collisions==3 && scripts.calls==4,"collision and script callbacks preserved");
scripts.alterState=true;object.SetGoState(GO_STATE_ACTIVE);check(object.GetGoState()==GO_STATE_READY && object.fields.at(101)==0 && object.fields.at(103)==0,"source state parameter retained across callbacks");scripts.alterState=false;
GameObjectTemplateAddon empty{};object.m_goTemplateAddon=&empty;object.fields={{101,11},{102,22},{103,33}};auto original=object.fields;object.ApplyTemplateVisuals(true, GO_STATE_ACTIVE);object.SetGoState(GO_STATE_READY);object.SetGoState(GO_STATE_ACTIVE);check(object.fields==original,"zero defaults do not overwrite script fields");
object.m_goTemplateAddon=nullptr;object.ApplyTemplateVisuals(true, GO_STATE_ACTIVE);object.SetGoState(GO_STATE_READY);check(object.fields==original,"no addon unchanged");
row[0].value=999999;WorldDatabase.fixture={row};manager.LoadGameObjectTemplateAddons();check(manager._gameObjectTemplateAddonStore.size()==1,"orphan addon rejected");
row[0].value=267180;row[6].value=row[7].value=row[8].value=0;WorldDatabase.fixture={row};manager.LoadGameObjectTemplateAddons();check(loaded.SpellVisualID==0 && loaded.SpellStateVisualID==0 && loaded.StateWorldEffectID==0,"reload clears removed configuration");
std::cout<<"PASS: actual addon loader, initial/ready/active visuals, collision/early-return callbacks, invalid effects, reload and zero-default compatibility\n";
}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''
    with tempfile.TemporaryDirectory() as directory:
        cpp=Path(directory)/'visual.cpp';exe=Path(directory)/'visual.exe';cpp.write_text(header+'\n'+functions+'\n'+harness,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
