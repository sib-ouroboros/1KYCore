#!/usr/bin/env python3
"""Compile native active-list cleanup and grid unloader with lifetime fixtures."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

def block(s,signature):
 start=s.index(signature);opening=s.index('{',start);end=opening+1;depth=1
 while depth:
  depth+=(s[end]=='{')-(s[end]=='}');end+=1
 return s[start:end]

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2]
 cpp=(root/'src/server/game/Maps/Map.cpp').read_text('latin1');header=(root/'src/server/game/Maps/Map.h').read_text('latin1')
 grid=(root/'src/server/game/Grids/ObjectGridLoader.cpp').read_text('latin1');obj=(root/'src/server/game/Entities/Object/Object.cpp').read_text('latin1')
 helper=block(header,'void RemoveFromActiveHelper(')
 generic='template<class T>\n'+block(cpp,'void Map::RemoveFromActive(T* obj)')
 removal='template<class T>\n'+block(cpp,'void Map::RemoveFromMap(T *obj, bool remove)')
 unload='template<class T>\n'+block(grid,'void ObjectGridUnloader::Visit(GridRefManager<T> &m)')
 code=r'''
#include <cstdint>
#include <set>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
struct Map;struct Creature;
struct WorldObject {Map* map=nullptr;bool active=true;bool inWorld=true;bool resetOnCleanup=false;std::vector<WorldObject*>* manager=nullptr;bool* destroyed=nullptr;
 virtual ~WorldObject();void RemoveFromWorld(){inWorld=false;}bool isActiveObject()const{return active;}
 void UpdateObjectVisibility(bool){}void RemoveFromGrid(){}void ResetMap(){map=nullptr;}Creature* ToCreature(){return nullptr;}
 void SaveRespawnTime(){}void CleanupsBeforeDelete(){if(resetOnCleanup)map=nullptr;}Map* FindMap(){return map;}};
struct Creature:WorldObject {};
struct Map {using ActiveNonPlayers=std::set<WorldObject*>;ActiveNonPlayers m_activeNonPlayers;ActiveNonPlayers::iterator m_activeNonPlayersIter=m_activeNonPlayers.end();
 HELPER
 void PurgeFromActive(WorldObject* obj){RemoveFromActiveHelper(obj);}
 template<class T>void RemoveFromActive(T* obj);
 template<class T>void RemoveFromMap(T* obj,bool remove);
 void RemoveBattlePet(Creature*){}template<class T>void DeleteFromWorld(T* p){delete p;}
};
WorldObject::~WorldObject(){if(map&&map->m_activeNonPlayers.count(this))std::terminate();if(manager)manager->erase(manager->begin());if(destroyed)*destroyed=true;}
enum {CONFIG_SAVE_RESPAWN_TIME_IMMEDIATELY};struct World {bool getBoolConfig(int){return true;}}world;World* sWorld=&world;
template<class T>struct GridRefManager {std::vector<WorldObject*> objects;struct Ref {T* source;T* GetSource(){return source;}} ref;
 bool isEmpty(){return objects.empty();}Ref* getFirst(){ref.source=static_cast<T*>(objects.front());return &ref;}};
struct ObjectGridUnloader {template<class T>void Visit(GridRefManager<T>&);};
GENERIC
REMOVAL
UNLOAD
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
int main(){try{
 Map map;WorldObject a,b,c;map.m_activeNonPlayers={&a,&b,&c};map.m_activeNonPlayersIter=map.m_activeNonPlayers.begin();
 auto first=*map.m_activeNonPlayersIter;map.RemoveFromActive(first);check(map.m_activeNonPlayers.size()==2,"generic removes current iterator");check(map.m_activeNonPlayersIter!=map.m_activeNonPlayers.end(),"iterator advances");
 map.PurgeFromActive(first);check(map.m_activeNonPlayers.size()==2,"purge idempotent");map.m_activeNonPlayersIter=map.m_activeNonPlayers.end();
 map.PurgeFromActive(&a);map.PurgeFromActive(&b);map.PurgeFromActive(&c);check(map.m_activeNonPlayers.empty(),"all types removed");
 for(bool active:{false,true}){bool destroyed=false;auto* object=new WorldObject;object->map=&map;object->active=active;object->destroyed=&destroyed;map.m_activeNonPlayers.insert(object);map.RemoveFromMap(object,true);check(destroyed&&map.m_activeNonPlayers.empty(),"removal regardless of active flag");}
 for(bool resetMap:{false,true}){GridRefManager<WorldObject> manager;bool destroyed=false;auto* object=new WorldObject;object->map=&map;object->manager=&manager.objects;object->destroyed=&destroyed;object->resetOnCleanup=resetMap;manager.objects.push_back(object);map.m_activeNonPlayers.insert(object);ObjectGridUnloader unloader;unloader.Visit(manager);check(destroyed&&manager.isEmpty()&&map.m_activeNonPlayers.empty(),"grid purge precedes cleanup/reset and delete");}
 // Iterate after destruction: ASan would detect retained pointers here.
 for(auto* object:map.m_activeNonPlayers)check(object->inWorld,"live retained object");
 std::cout<<"PASS: actual active membership, iteration, removal and grid destruction\n";
 }catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('HELPER',helper).replace('GENERIC',generic).replace('REMOVAL',removal).replace('UNLOAD',unload)
 # Deactivation remains specialized for creatures/dynamic objects, with a generic membership purge.
 activation=block(obj,'void WorldObject::setActive(')
 assert 'map->PurgeFromActive(this);' in activation
 with tempfile.TemporaryDirectory(prefix='map-active-lifetime-') as tmp:
  tmp=Path(tmp);source=tmp/'test.cpp';source.write_text(code,encoding='utf-8');output=tmp/('test.exe' if os.name=='nt' else 'test')
  command=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(output)]
  if not args.no_sanitizers:command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
  subprocess.run(command,check=True);subprocess.run([str(output)],check=True,timeout=60)
if __name__=='__main__':main()
