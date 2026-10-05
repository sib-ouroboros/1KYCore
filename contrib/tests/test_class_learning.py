#!/usr/bin/env python3
"""Compile production talent initialization, race filter and trainer bounds.

Uses fixtures for sessions/DB2, not a full worldserver or client test.
"""
from pathlib import Path
import argparse, os, subprocess, tempfile

def method(source, signature):
    start=source.index(signature); opening=source.index('{',start); depth=1; end=opening+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}'); end+=1
    return source[start:end]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    player=(root/'src/server/game/Entities/Player/Player.cpp').read_text('utf8')
    give=method(player,'void Player::GiveLevel(')
    assert give.count('LearnSpecializationSpells();')==1
    assert give.index('InitTalentForLevel();') < give.index('LearnSpecializationSpells();')
    handler=(root/'src/server/game/Handlers/NPCHandler.cpp').read_text('utf8')
    begin=handler.index('        uint8 maxReq = 0;'); end=handler.index('        packet.Spells.push_back(spell);',begin)
    bounds=handler[begin:end]
    loader=(root/'src/server/game/Globals/ObjectMgr.cpp').read_text('utf8')
    start=loader.index('void ObjectMgr::AddSpellToTrainer(')
    begin=loader.index('    // Validate before inserting:',start);end=loader.index('    TrainerSpellData& data =',begin)
    validation=loader[begin:end]
    prefix=r'''
#include <array>
#include <vector>
#include <map>
#include <cstdint>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t;using uint32=std::uint32_t;using uint64=std::uint64_t;
#define ASSERT_NOTNULL(x) (x)
#define TC_LOG_ERROR(...) do {} while(0)
constexpr int MIN_SPECIALIZATION_LEVEL=10,MAX_TALENT_TIERS=7,MAX_TALENT_COLUMNS=3,PLAYER_FIELD_CURRENT_SPEC_ID=0,PLAYER_FIELD_MAX_TALENT_TIERS=1;
namespace rbac{constexpr int RBAC_PERM_SKIP_CHECK_MORE_TALENTS_THAN_ALLOWED=0;}
struct TalentEntry{};struct ChrSpecializationEntry{uint32 ID;uint8 OrderIndex;};
struct DB2Manager{ChrSpecializationEntry spec{265,0};std::vector<TalentEntry const*> talents{nullptr};
 ChrSpecializationEntry const* GetDefaultChrSpecializationForClass(int){return &spec;}
 std::vector<TalentEntry const*> const& GetTalentsByPosition(int,int,int){return talents;}} db2;
auto& sDB2Manager=db2;
struct Session{bool loading=false;bool HasPermission(int){return false;}bool PlayerLoading(){return loading;}};
struct Ability{uint64 RaceMask;uint32 ClassMask;};
using SkillLineAbilityMap=std::multimap<uint32,Ability const*>;
using SkillLineAbilityMapBounds=std::pair<SkillLineAbilityMap::const_iterator,SkillLineAbilityMap::const_iterator>;
struct SpellManager{
 SkillLineAbilityMap abilities;std::map<uint32,uint32> previous;std::map<uint32,std::vector<std::pair<uint32,uint32>>> required;
 SkillLineAbilityMapBounds GetSkillLineAbilityMapBounds(uint32 id){return abilities.equal_range(id);}
 uint32 GetPrevSpellInChain(uint32 id){return previous[id];}
 auto const& GetSpellsRequiredForSpellBounds(uint32 id){return required[id];}
} manager;auto* sSpellMgr=&manager;
struct Player{
 uint8 level=1,group=0;uint32 current=265,primary=265,klass=9;uint64 race=1;uint32 classMask=256;
 int resets=0,notifications=0,removedTalents=0,sent=0;bool known=false;Session session;
 uint8 getLevel(){return level;}int getClass(){return klass;}Session* GetSession(){return &session;}
 uint32 GetUInt32Value(int){return current;}uint32 GetPrimarySpecialization(){return primary;}uint8 GetActiveTalentGroup(){return group;}
 void SetUInt32Value(int,uint32){}uint32 CalculateTalentsTiers(){return level<15?0:1;}
 void RemoveTalent(TalentEntry const*){++removedTalents;}void SendTalentsInfoData(){++sent;}
 void LearnSpecializationSpells(){if(level>=3&&!known){known=true;++notifications;}}
 void ResetTalentSpecialization(){++resets;known=false;current=primary=db2.spec.ID;group=db2.spec.OrderIndex;LearnSpecializationSpells();}
 uint64 getRaceMask() const{return race;}uint32 getClassMask() const{return classMask;}
 void InitTalentForLevel();bool IsSpellFitByClassAndRace(uint32) const;
 void Level(uint8 value){level=value;InitTalentForLevel();LearnSpecializationSpells();}
};
constexpr int MAX_TRAINERSPELL_ABILITY_REQS=3,SPELL_EFFECT_LEARN_SPELL=36,DIFFICULTY_NONE=0;
struct TrainerSpell{std::array<uint32,3> ReqAbility{};};
struct PacketSpell{std::array<int,3> ReqAbility{};};
PacketSpell prerequisites(TrainerSpell const* tSpell){PacketSpell spell;
'''
    code=prefix+bounds+'return spell;}\n'+method(player,'void Player::InitTalentForLevel()')+'\n'+method(player,'bool Player::IsSpellFitByClassAndRace(')+r'''
struct SpellEffectInfo{int Effect;uint32 EffectIndex;};
struct SpellInfo{std::vector<SpellEffectInfo const*> effects;auto const& GetEffectsForDifficulty(int) const{return effects;}};
void validate(SpellInfo const* spellinfo,bool& accepted){
'''+validation+r'''
 accepted=true;}
void check(bool value,char const* label){if(!value)throw std::runtime_error(label);}
int main(){
 // All classes share this initialization; changing the fixture spec ID exercises default selection.
 for(uint32 c=1;c<=12;++c){db2.spec.ID=100+c;db2.spec.OrderIndex=c%4;
  Player p;p.klass=c;p.current=p.primary=db2.spec.ID;p.group=db2.spec.OrderIndex;
  p.Level(2);check(!p.known&&p.notifications==0,"below ability level");
  p.Level(3);check(p.known&&p.notifications==1&&p.resets==0,"new ability learned once");
  for(int l=4;l<=12;++l)p.Level(l);
  check(p.notifications==1&&p.resets==0,"known ability not relearned on levels");
  p.level=4;p.session.loading=true;p.InitTalentForLevel();check(p.notifications==1,"stable relog");
  check(p.removedTalents>0,"talent level limits still enforced");
  for(int mismatch=0;mismatch<3;++mismatch){Player q;q.level=4;q.current=q.primary=db2.spec.ID;q.group=db2.spec.OrderIndex;
   if(mismatch==0)q.current=0;
   if(mismatch==1)q.primary=0;
   if(mismatch==2)q.group=255;
   q.Level(4);check(q.resets==1&&q.notifications==1&&q.current==db2.spec.ID,"invalid default reset once");}
  Player high;high.level=98;high.current=999;high.InitTalentForLevel();check(high.current==999&&high.resets==0,"chosen high level spec preserved");
 }
 for(int bit:{0,9,31,32,34,63}){Ability a{uint64(1)<<bit,256};manager.abilities.clear();manager.abilities.emplace(172,&a);
  Player p;p.race=a.RaceMask;check(p.IsSpellFitByClassAndRace(172),"full width race accepted");
  p.race=a.RaceMask^~uint64(0);check(!p.IsSpellFitByClassAndRace(172),"wrong race rejected");
  p.race=a.RaceMask;p.classMask=1;check(!p.IsSpellFitByClassAndRace(172),"wrong class rejected");
  a.RaceMask=0;a.ClassMask=0;check(p.IsSpellFitByClassAndRace(172),"unrestricted accepted");
  check(p.IsSpellFitByClassAndRace(999),"spell without ability row accepted");}
 for(int count=0;count<=20;++count){manager.previous.clear();manager.required.clear();TrainerSpell t;t.ReqAbility={10,20,30};
  manager.previous[10]=9;for(int n=0;n<count;++n)manager.required[10].push_back({10,uint32(100+n)});
  auto packet=prerequisites(&t);check(packet.ReqAbility[0]==9,"previous rank first");
  for(int n=0;n<2&&n<count;++n)check(packet.ReqAbility[n+1]==100+n,"bounded requirements preserved");}
 for(uint32 index:{0u,1u,2u,3u,31u}){SpellEffectInfo effect{SPELL_EFFECT_LEARN_SPELL,index};SpellInfo info{{nullptr,&effect}};bool accepted=false;validate(&info,accepted);check(accepted==(index<3),"effect index validated before cache write");}
 SpellEffectInfo other{0,31};SpellInfo info{{&other}};bool accepted=false;validate(&info,accepted);check(accepted,"unrelated effects unchanged");
 std::cout<<"Class learning, 64-bit race masks and trainer bounds: PASS\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        source=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';source.write_text(code,'utf8')
        command=[os.environ.get('CXX','g++'),'-std=c++14','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)]
        if not args.no_sanitizers:command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
        subprocess.run(command,check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
