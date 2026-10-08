#!/usr/bin/env python3
"""Exercise native garrison identity, roster arithmetic and ability lookup."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root/'src/server/game/Garrison/Garrison.cpp').read_text('utf8')
    names = ['GetFollower', 'GetMission', 'GetMissionByID', 'DeleteMission',
             'GetMissionFollowers', 'GetActiveFollowersCount', 'GetAverageFollowerILevel',
             'GetMaxFollowerLevel', 'Follower::GetItemLevel', 'Follower::HasAbility']
    methods = '\n'.join(re.search(r'^[^\n]+ Garrison::'+re.escape(name)+r'\([^\n]*\)(?: const)?\n\{.*?^\}', source, re.M|re.S)[0] for name in names)
    harness = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using uint32=std::uint32_t;using uint64=std::uint64_t;
constexpr uint32 FOLLOWER_STATUS_INACTIVE=1;
struct GarrAbilityEntry{uint32 ID;};
struct Garrison{struct Follower{
 struct {uint64 DbID=0;uint32 FollowerStatus=0,FollowerLevel=0,ItemLevelWeapon=0,ItemLevelArmor=0,CurrentMissionID=0;std::vector<GarrAbilityEntry const*> AbilityID;} PacketInfo;
 uint32 GetItemLevel() const;bool HasAbility(uint32) const;
};struct Mission{struct{uint64 DbID=0;uint32 MissionRecID=0;}PacketInfo;};
 std::unordered_map<uint64,Follower> _followers;
 std::unordered_map<uint64,Mission> _missions;std::unordered_set<uint32> _missionIds;
 Follower* GetFollower(uint64);Mission* GetMission(uint64);Mission* GetMissionByID(uint32);
 void DeleteMission(uint64);std::vector<Follower*> GetMissionFollowers(uint32);
 uint32 GetActiveFollowersCount() const;uint32 GetAverageFollowerILevel() const;uint32 GetMaxFollowerLevel() const;
};
METHODS
void check(bool ok,char const* msg){if(!ok)throw std::runtime_error(msg);}
int main(){
 Garrison g;auto const hi=uint64(1)<<40;auto const max=std::numeric_limits<uint64>::max();
 check(!g.GetFollower(1)&&!g.GetMission(1),"empty lookup");
 for(uint64 id:std::vector<uint64>{7,hi+7,uint64(1)<<32,max}){
  g._followers[id].PacketInfo.DbID=id;
  g._missions[id].PacketInfo={id,uint32(g._missions.size()+100)};
 }
 for(uint64 id:std::vector<uint64>{7,hi+7,uint64(1)<<32,max}){
  check(g.GetFollower(id)==&g._followers.at(id),"follower selected colliding ID");
  check(g.GetMission(id)==&g._missions.at(id),"mission selected colliding ID");
 }
 auto fs=g._followers.size(),ms=g._missions.size();
 for(uint64 id:std::vector<uint64>{0,8,hi+8,(uint64(1)<<32)+7})
  check(!g.GetFollower(id)&&!g.GetMission(id),"missing ID aliases another record");
 check(fs==g._followers.size()&&ms==g._missions.size(),"lookup inserted phantom record");
 // Rehash must preserve full identity; no dependence on traversal order.
 for(uint64 id=1000;id<2000;++id){g._followers[id].PacketInfo.DbID=id;g._missions[id].PacketInfo.DbID=id;}
 check(g.GetFollower(hi+7)->PacketInfo.DbID==hi+7&&g.GetMission(hi+7)->PacketInfo.DbID==hi+7,"rehash identity");
 uint32 rec=g.GetMission(hi+7)->PacketInfo.MissionRecID;
 g._missionIds.insert(rec);check(g.GetMissionByID(rec)==g.GetMission(hi+7),"DB ID versus client record ID");
 g.DeleteMission(hi+7);check(!g.GetMission(hi+7)&&g.GetMission(7)&&!g._missionIds.count(rec),"delete colliding mission");
 ms=g._missions.size();g.DeleteMission(hi+7);check(ms==g._missions.size(),"repeated delete");
 g._followers.clear();check(g.GetAverageFollowerILevel()==0&&g.GetActiveFollowersCount()==0&&g.GetMaxFollowerLevel()==0,"empty roster");
 auto& a=g._followers[hi];a.PacketInfo.ItemLevelWeapon=600;a.PacketInfo.ItemLevelArmor=601;a.PacketInfo.FollowerLevel=100;a.PacketInfo.CurrentMissionID=42;
 auto& b=g._followers[hi+1];b.PacketInfo.ItemLevelWeapon=601;b.PacketInfo.ItemLevelArmor=602;b.PacketInfo.FollowerLevel=110;b.PacketInfo.CurrentMissionID=42;
 auto& inactive=g._followers[hi+2];inactive.PacketInfo.FollowerStatus=FOLLOWER_STATUS_INACTIVE;inactive.PacketInfo.ItemLevelWeapon=999;inactive.PacketInfo.ItemLevelArmor=999;inactive.PacketInfo.FollowerLevel=120;
 check(a.GetItemLevel()==600&&b.GetItemLevel()==601,"individual rounding");
 check(g.GetAverageFollowerILevel()==601&&g.GetActiveFollowersCount()==2&&g.GetMaxFollowerLevel()==110,"active roster selection and ceiling");
 check(g.GetMissionFollowers(42).size()==2&&g.GetMissionFollowers(43).empty(),"mission roster matching");
 a.PacketInfo.FollowerStatus=b.PacketInfo.FollowerStatus=FOLLOWER_STATUS_INACTIVE;
 check(g.GetAverageFollowerILevel()==0,"inactive-only division by zero");
 uint32 const top=std::numeric_limits<uint32>::max();
 a.PacketInfo.ItemLevelWeapon=a.PacketInfo.ItemLevelArmor=top;a.PacketInfo.FollowerStatus=0;
 b.PacketInfo.ItemLevelWeapon=b.PacketInfo.ItemLevelArmor=top;b.PacketInfo.FollowerStatus=0;
 check(a.GetItemLevel()==top&&g.GetAverageFollowerILevel()==top,"item level addition overflow");
 GarrAbilityEntry ability{23};a.PacketInfo.AbilityID={nullptr,&ability};
 check(a.HasAbility(23)&&!a.HasAbility(24)&&!a.HasAbility(0),"null ability or incorrect matching");
 a.PacketInfo.AbilityID.clear();check(!a.HasAbility(23),"empty abilities");
 std::cout<<"PASS: ten native garrison methods; full-width identity, collision, rehash, roster arithmetic, mission membership and ability safety\n";
}
'''
    harness=harness.replace('METHODS',methods)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'identity.cpp';exe=Path(tmp)/'identity'
        cpp.write_text(harness,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-D_GLIBCXX_DEBUG',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True,timeout=30)


if __name__=='__main__':main()
