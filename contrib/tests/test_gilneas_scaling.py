#!/usr/bin/env python3
"""Execute actual Creature level selection and target scaling methods."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/game/Entities/Creature/Creature.cpp').read_text('utf8')
 code=r"""
#include <algorithm>
#include <cstdint>
#include <optional>
#include <map>
#include <iostream>
#include <stdexcept>
using uint8=std::uint8_t;using int8=std::int8_t;using uint32=std::uint32_t;using int32=std::int32_t;
enum{UNIT_FIELD_SCALING_LEVEL_MIN,UNIT_FIELD_SCALING_LEVEL_MAX,UNIT_FIELD_SCALING_LEVEL_DELTA,PLAYER_FIELD_SCALING_PLAYER_LEVEL_DELTA,CONFIG_WORLD_BOSS_LEVEL_DIFF};
uint8 urand(uint8,uint8 max){return max;}int8 irand(int8,int8 max){return max;}
template<class T,class A,class B>T RoundToInterval(T v,A a,B b){return std::max<T>(a,std::min<T>(b,v));}
struct Unit;
struct WorldObject{virtual~WorldObject()=default;virtual Unit const*ToUnit()const{return nullptr;}virtual bool IsPlayer()const{return false;}virtual uint32 GetUInt32Value(int)const{return 0;}};
struct Unit:WorldObject{uint8 level=9;Unit const*ToUnit()const override{return this;}uint8 GetEffectiveLevel()const{return level;}virtual uint8 GetLevelForTarget(WorldObject const*)const{return level;}};
struct Player:Unit{bool IsPlayer()const override{return true;}};
struct World{int getIntConfig(int)const{return 3;}}world;auto*sWorld=&world;
struct Scaling{uint8 MinLevel=5,MaxLevel=20;int8 DeltaLevelMin=0,DeltaLevelMax=0;};
struct CreatureTemplate{uint8 minlevel=5,maxlevel=20;std::optional<Scaling>levelScaling;};
struct Creature:Unit{CreatureTemplate info;std::map<int,int32>values;bool pet=false,boss=false;CreatureTemplate const*GetCreatureTemplate()const{return &info;}bool IsPet()const{return pet;}bool isWorldBoss()const{return boss;}void SetLevel(uint8 l){level=l;}void SetUInt32Value(int f,uint32 v){values[f]=v;}void SetInt32Value(int f,int32 v){values[f]=v;}uint32 GetUInt32Value(int f)const override{auto it=values.find(f);return it==values.end()?0:it->second;}int32 GetInt32Value(int f)const{return GetUInt32Value(f);}void UpdateLevelDependantStats(){}
"""
 for signature in ['bool Creature::HasScalableLevels() const','void Creature::SelectLevel()','uint8 Creature::GetLevelForTarget(WorldObject const* target) const']:
  code+=method(source,signature).replace('Creature::','')+'\n'
 code+=r"""
};
void check(bool v){if(!v)throw std::runtime_error("native scaling regression");}
int main(){try{Creature c;Player p;c.SelectLevel();check(c.level==20&&c.GetLevelForTarget(&p)==20);c.info.levelScaling=Scaling{};c.SelectLevel();check(c.level==20);int levels[]={1,4,7,10,12,15,20,30},expected[]={5,5,7,10,12,15,20,20};for(int i=0;i<8;++i){p.level=levels[i];check(c.GetLevelForTarget(&p)==expected[i]);}c.pet=true;check(!c.HasScalableLevels());std::cout<<"Native Creature selection and target scaling: PASS\n";}catch(std::exception const&e){std::cerr<<e.what();return 1;}}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8');cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
