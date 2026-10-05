#!/usr/bin/env python3
"""Compile the native SpellArea predicate for the audited phase182->183 handoff."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/game/Spells/SpellMgr.cpp').read_text('utf8')
 code=r"""
#include <cstdint>
#include <map>
#include <set>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using int32=std::int32_t;using uint64=std::uint64_t;
constexpr int GENDER_NONE=2,SPELL_AURA_MOD_INCREASE_MOUNTED_FLIGHT_SPEED=1,SPELL_AURA_FLY=2,BATTLEFIELD_WG=1,BATTLEFIELD_BATTLEID_WG=1,TEAM_HORDE=1,TEAM_ALLIANCE=0;
struct Player;
struct Battleground{bool IsSpellAllowed(uint32,Player const*){return true;}};
struct Player{std::map<uint32,int> quests;int GetQuestStatus(uint32 id)const{auto it=quests.find(id);return it==quests.end()?0:it->second;}
 int getGender()const{return 0;}int GetTeamId()const{return 0;}uint64 getRaceMask()const{return uint64(1)<<21;}bool HasAura(int)const{return false;}bool HasAuraType(int)const{return false;}uint32 GetZoneId()const{return 4714;}Battleground* GetBattleground()const{return nullptr;}};
struct Battlefield{bool CanFlyIn(){return false;}int GetTypeId(){return 0;}uint32 GetData(uint32){return 0;}bool IsEnabled(){return false;}int GetDefenderTeam(){return 0;}bool IsWarTime(){return false;}};
struct BattlefieldMgr{Battlefield* GetBattlefieldToZoneId(uint32){return nullptr;}Battlefield* GetBattlefieldByBattleId(int){return nullptr;}} battlefields;auto*sBattlefieldMgr=&battlefields;
struct GameEventMgr{bool IsSpellAreaEventActive(uint32,uint32){return true;}} events;auto*sGameEventMgr=&events;
struct SpellArea{int gender=2,teamId=-1;uint64 raceMask=0;uint32 areaId=4714,questStart=0,questEnd=0,questStartStatus=0,questEndStatus=0;int auraSpell=0;uint32 spellId=0;bool IsFitToRequirements(Player const*,uint32,uint32)const;};
"""+method(source,'bool SpellArea::IsFitToRequirements(')+r"""
void check(bool v,char const*n){if(!v)throw std::runtime_error(n);}
int main(){
 SpellArea oldPhase,newPhase;oldPhase.spellId=68482;oldPhase.questStart=14321;oldPhase.questStartStatus=64;oldPhase.questEnd=14396;oldPhase.questEndStatus=74;
 newPhase.spellId=68483;newPhase.questStart=14396;newPhase.questStartStatus=74;newPhase.questEnd=14465;newPhase.questEndStatus=64;
 Player p;p.quests[14321]=6;check(oldPhase.IsFitToRequirements(&p,4714,4808)&&!newPhase.IsFitToRequirements(&p,4714,4808),"before accept");
 for(int status:{3,1,6}){p.quests[14396]=status;check(!oldPhase.IsFitToRequirements(&p,4714,4808)&&newPhase.IsFitToRequirements(&p,4714,4808),"accept complete reward handoff");}
 Player relog=p;relog.quests[14396]=3;check(newPhase.IsFitToRequirements(&relog,4714,4808),"saved active quest after relog");
 p.quests[14396]=0;check(oldPhase.IsFitToRequirements(&p,4714,4808)&&!newPhase.IsFitToRequirements(&p,4714,4808),"abandon returns prior phase");
 p.quests[14396]=6;p.quests[14465]=6;check(!newPhase.IsFitToRequirements(&p,4714,4808),"next stage ends phase183");
 p.quests[14465]=0;check(!newPhase.IsFitToRequirements(&p,1,1),"other zone not affected");
 std::cout<<"Native Gilneas phase handoff predicate: PASS\n";
}
"""
 with tempfile.TemporaryDirectory() as temp:
  cpp=Path(temp)/'test.cpp';exe=Path(temp)/'test.exe';cpp.write_text(code,'utf8')
  cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
  if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
  subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
