#!/usr/bin/env python3
"""Exercise actual mission completion, rewards, deletion and Legion packet writer."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
from test_map_active_lifetime import block

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];cpp=(root/'src/server/game/Garrison/Garrison.cpp').read_text('latin1')
 packet=(root/'src/server/game/Server/Packets/GarrisonPackets.cpp').read_text('latin1')
 methods='\n'.join(block(cpp,s) for s in ['void Garrison::DeleteMission(','std::vector<Garrison::Follower*> Garrison::GetMissionFollowers(', 'void Garrison::CompleteMission(', 'void Garrison::CalculateMissonBonusRoll(', 'void Garrison::RewardMission('])
 writer=block(packet,'WorldPacket const* WorldPackets::Garrison::GarrisonCompleteMissionResult::Write()')
 code=r'''
#include <cstdint>
#include <map>
#include <set>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint64=std::uint64_t;using int32=std::int32_t;
uint64 now=100;uint64 testTime(void*){return now;}
#define time testTime
bool rollSuccess=true;bool roll_chance_i(uint32){return rollSuccess;}
constexpr int CRITERIA_TYPE_COMPLETE_GARRISON_MISSION=1;
namespace GarrisonMission {namespace State {enum{Offered,InProgress,Completed,Reward2Claimed};}namespace Result{enum{Success,Fail};}}
struct WorldPacket {std::vector<std::uint8_t> bytes;template<class T>WorldPacket& operator<<(T value){for(unsigned i=0;i<sizeof(T);++i)bytes.push_back(std::uint8_t(uint64(value)>>(i*8)));return *this;}void WriteBit(bool bit){bytes.push_back(bit?128:0);}void FlushBits(){}};
namespace WorldPackets {namespace Garrison {
struct GarrisonMission {uint64 DbID=42;uint32 MissionRecID=929,StartTime=50,MissionDuration=50,MissionState=::GarrisonMission::State::InProgress,SuccessChance=100;};
struct GarrisonMissionReward {int32 ItemID=0;uint32 ItemQuantity=0,CurrencyID=0,CurrencyQuantity=0,FollowerXP=0;};
struct GarrMissionFollowerData {uint64 FollowerDbID=0;uint32 unk32=0;};
struct GarrisonCompleteMissionResult {WorldPacket _worldPacket;uint32 Result=0;GarrisonMission MissionData;uint32 MissionRecID=0;std::vector<GarrMissionFollowerData> Followers;bool Succeeded=false;WorldPacket const* Write();};
struct GarrisonMissionBonusRollResult {GarrisonMission Mission;uint32 Result=0;WorldPacket packet;WorldPacket const* Write(){return &packet;}};
}}
WorldPacket& operator<<(WorldPacket& packet,WorldPackets::Garrison::GarrisonMission const& mission){return packet<<mission.DbID<<mission.MissionRecID;}
struct Owner {unsigned items=0,currency=0,criteria=0;WorldPacket last;void AddItem(int32,uint32 count){items+=count;}void ModifyCurrency(uint32,uint32 count){currency+=count;}void UpdateCriteria(int,uint32){++criteria;}void SendDirectMessage(WorldPacket const* p){last=*p;}};
struct GarrMissionEntry {uint32 ID=929;};struct Store {GarrMissionEntry entry;GarrMissionEntry const* LookupEntry(uint32 id){return id==929?&entry:nullptr;}}sGarrMissionStore;
struct Garrison {
struct Follower {struct {uint64 DbID=0;uint32 CurrentMissionID=929;}PacketInfo;unsigned xp=0;void EarnXP(Owner*,uint32 value){xp+=value;}};
struct Mission {WorldPackets::Garrison::GarrisonMission PacketInfo;std::vector<WorldPackets::Garrison::GarrisonMissionReward> Rewards,BonusRewards;};
std::map<uint64,Mission> _missions;std::set<uint32> _missionIds;std::map<uint64,Follower> _followers;Owner owner;Owner* _owner=&owner;
Owner* GetOwner(){return _owner;}Mission* GetMissionByID(uint32 id){for(auto& m:_missions)if(m.second.PacketInfo.MissionRecID==id)return &m.second;return nullptr;}
void DeleteMission(uint64);std::vector<Follower*> GetMissionFollowers(uint32);void CompleteMission(uint32);void CalculateMissonBonusRoll(uint32);void RewardMission(Mission*,bool);
};
METHODS
WRITER
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
uint64 read(WorldPacket const& p,unsigned offset,unsigned size){uint64 n=0;for(unsigned i=0;i<size;++i)n|=uint64(p.bytes.at(offset+i))<<(8*i);return n;}
void setup(Garrison& g){g._missions[42]={};g._missionIds={929};for(uint64 id:{11u,22u}){g._followers[id].PacketInfo.DbID=id;g._followers[id].PacketInfo.CurrentMissionID=929;}}
int main(){try{
 Garrison g;setup(g);rollSuccess=false;g.CompleteMission(929);
 check(g.GetMissionFollowers(929).empty(),"failure releases followers");check(g._missions.empty()&&g._missionIds.empty(),"failure frees mission for re-offer");
 check(read(g.owner.last,16,4)==929&&read(g.owner.last,20,4)==2,"mission id and follower count layout");
 check(read(g.owner.last,24,8)==11&&read(g.owner.last,36,8)==22,"followers captured before release");check(g.owner.last.bytes.size()==49&&g.owner.last.bytes.back()==0,"failed packet layout");
 g.CalculateMissonBonusRoll(929);check(g.owner.items==0,"failure cannot claim chest");
 g.DeleteMission(42);check(g._missions.empty()&&g._missionIds.empty(),"both indexes deleted");g.DeleteMission(42);
 setup(g);rollSuccess=true;now=99;g.CompleteMission(929);check(g._missions[42].PacketInfo.MissionState==GarrisonMission::State::InProgress,"early completion rejected");
 g.CalculateMissonBonusRoll(929);check(g._missions.size()==1,"early bonus roll rejected");now=100;g.CompleteMission(929);
 check(g.owner.criteria==1&&g.GetMissionFollowers(929).size()==2,"success retains followers until rewards");
 check(g.owner.last.bytes.back()==128,"successful packet bit");rollSuccess=false;g.CompleteMission(929);check(g._missions[42].PacketInfo.MissionState==GarrisonMission::State::Completed&&g.owner.criteria==1,"completion cannot reroll");
 g._missions[42].Rewards={{1,1,0,0,0}};g.CalculateMissonBonusRoll(929);check(g.owner.items==1&&g.GetMissionFollowers(929).empty()&&g._missionIds.empty(),"no-XP reward releases champions");g.CalculateMissonBonusRoll(929);check(g.owner.items==1,"no duplicate rewards");
 setup(g);auto& mission=g._missions[42];mission.Rewards={{0,0,0,0,10},{0,0,0,0,20}};mission.BonusRewards={{0,0,0,0,30}};g.RewardMission(&mission,true);
 for(auto const& follower:g._followers)check(follower.second.xp==60&&follower.second.PacketInfo.CurrentMissionID==0,"all normal/bonus XP before release");
 WorldPackets::Garrison::GarrisonCompleteMissionResult empty;check(empty.Write()->bytes.size()==25&&read(empty._worldPacket,20,4)==0,"empty follower count serialized");
 std::cout<<"PASS: native mission lifecycle, failed/no-XP releases, replay guards and Legion packet order\n";
 }catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''.replace('METHODS',methods).replace('WRITER',writer)
 with tempfile.TemporaryDirectory(prefix='garrison-lifecycle-') as tmp:
  tmp=Path(tmp);p=tmp/'test.cpp';p.write_text(code,encoding='utf-8');output=tmp/('test.exe' if os.name=='nt' else 'test')
  command=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(p),'-o',str(output)]
  if not args.no_sanitizers:command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
  subprocess.run(command,check=True);subprocess.run([str(output)],check=True)
if __name__=='__main__':main()
