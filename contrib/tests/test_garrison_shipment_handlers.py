#!/usr/bin/env python3
"""Compile actual shipment handlers and packet writers with sparse/invalid queues."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Handlers/GarrisonHandler.cpp').read_text('utf8')
    methods='\n'.join(re.search(r'^void WorldSession::'+name+r'\([^\n]*\)\n\{.*?^\}',source,re.M|re.S)[0] for name in ['HandleRequestLandingPageShipmentInfoOpcode','HandleGarrisonGetShipmentInfo','HandleGarrisonCreateShipmentOpcode'])
    packets=(root/'src/server/game/Server/Packets/GarrisonPackets.cpp').read_text('utf8')
    writers='\n'.join(re.search(r'^WorldPacket const\* WorldPackets::Garrison::'+name+r'::Write\(\)\n\{.*?^\}',packets,re.M|re.S)[0] for name in ['GarrisonLandingPageShipmentInfo','GarrisonCreateShipmentResponse'])
    core=(root/'src/server/game/Garrison/Garrison.cpp').read_text('utf8')
    building=re.search(r'^std::vector<Garrison::WorkOrder> Garrison::GetBuildingWorkOrders\([^\n]*\) const\n\{.*?^\}',core,re.M|re.S)[0]
    harness=r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <unordered_map>
#include <vector>
using uint32=std::uint32_t;using uint64=std::uint64_t;using uint8=std::uint8_t;
enum GarrisonType{GARRISON_TYPE_GARRISON=2,GARRISON_TYPE_CLASS_HALL=3};
constexpr uint32 UNIT_NPC_FLAG_SHIPMENT_CRAFTER=1,SMSG_GET_SHIPMENT_INFO_RESPONSE=2,TRIGGERED_FULL_MASK=1;
struct WorldPacket{std::vector<uint8> bytes;
 WorldPacket(uint32=0,uint32=0){}
 void WriteBit(bool value){bytes.push_back(value?128:0);}void FlushBits(){}
 template<class T>WorldPacket& operator<<(T v){static_assert(std::is_integral<T>::value,"integral packet field");for(unsigned i=0;i<sizeof(T);++i)bytes.push_back(uint8(uint64(v)>>(8*i)));return *this;}
};
namespace WorldPackets{namespace Garrison{
struct GarrisonRequestLandingPageShipmentInfo{};
struct GarrisonRequestShipmentInfo{uint64 NpcGUID=1;};
struct GarrisonCreateShipment{uint64 NpcGUID=1;uint32 Count=1;};
struct GarrisonShipment{uint32 ShipmentRecId=0;uint64 ShipmentId=0,AssignedFollowerDBID=0;uint32 CreationTime=0,ShipmentDuration=0,BuildingType=0;};
struct GarrisonLandingPageShipmentInfo{uint32 GarrisonType=0;std::vector<GarrisonShipment> Shipments;WorldPacket _worldPacket;WorldPacket const* Write();};
struct GarrisonCreateShipmentResponse{uint64 ShipmentID=0;uint32 ShipmentRecID=0,Result=0;WorldPacket _worldPacket;WorldPacket const* Write();};
}}
struct CharShipmentEntry{uint32 ID,ShipmentContainerID,SpellID,MaxShipments,GarrFollowerID;};
struct CharShipmentContainerEntry{uint32 ID,GarrTypeID;};
struct SpellInfo{uint32 ID;};
template<class T>struct Store{std::unordered_map<uint32,T> rows;
 T const* LookupEntry(uint32 id)const{auto i=rows.find(id);return i==rows.end()?nullptr:&i->second;}
 uint32 GetNumRows()const{uint32 n=0;for(auto const& p:rows)n=std::max(n,p.first+1);return n;}};
Store<CharShipmentEntry> sCharShipmentStore;Store<CharShipmentContainerEntry> sCharShipmentContainerStore;
struct SpellMgr{Store<SpellInfo> rows;SpellInfo const* GetSpellInfo(uint32 id){return rows.LookupEntry(id);}} spellMgr;SpellMgr* sSpellMgr=&spellMgr;
struct Creature{uint32 container=1,entry=123;uint32 GetShipmentContainerID()const{return container;}uint32 GetEntry()const{return entry;}};
struct Garrison{struct WorkOrder{uint64 DatabaseID;uint32 PlotInstanceID,ShipmentID,CreationTime,CompleteTime;uint64 ownerID;};
 std::unordered_map<uint64,WorkOrder> _workorders;uint32 plot=50,started=0,failAfter=std::numeric_limits<uint32>::max();uint64 sequence=uint64(1)<<40;
 GarrisonType GetType()const{return GARRISON_TYPE_CLASS_HALL;}
 auto const& GetWorkOrders()const{return _workorders;}
 uint32 GetClassHallPlotId(uint32 id)const{return id==123?plot:0;}
 uint32 GetWorkOrderCount(uint32 id)const{return std::count_if(_workorders.begin(),_workorders.end(),[id](auto const& p){return p.second.PlotInstanceID==id;});}
 std::vector<WorkOrder> GetBuildingWorkOrders(uint32)const;
 uint64 StartWorkOrder(uint32 p,uint32 s){if(started>=failAfter)return 0;auto id=sequence++;_workorders[id]={id,p,s,100,200,0};++started;return id;}
};
struct Player{Creature npc;Garrison* g=nullptr;bool inside=true,interact=true;uint32 casts=0;
 Creature* GetNPCIfCanInteractWith(uint64 id,uint32 flags){return interact&&id==1&&flags==UNIT_NPC_FLAG_SHIPMENT_CRAFTER?&npc:nullptr;}
 Garrison* GetGarrison(GarrisonType type){return type==GARRISON_TYPE_CLASS_HALL?g:nullptr;}
 bool IsInGarrison()const{return inside;}void CastSpell(Player*,SpellInfo const*,uint32){++casts;}
};
struct WorldSession{Player* _player;std::vector<WorldPacket> sent;
 void SendPacket(WorldPacket const* packet){sent.push_back(*packet);}
 void HandleRequestLandingPageShipmentInfoOpcode(WorldPackets::Garrison::GarrisonRequestLandingPageShipmentInfo&);
 void HandleGarrisonGetShipmentInfo(WorldPackets::Garrison::GarrisonRequestShipmentInfo&);
 void HandleGarrisonCreateShipmentOpcode(WorldPackets::Garrison::GarrisonCreateShipment&);
};
BUILDING
WRITERS
METHODS
void check(bool ok,char const* text){if(!ok)throw std::runtime_error(text);}
uint64 value(WorldPacket const& p,unsigned offset,unsigned size){uint64 v=0;for(unsigned i=0;i<size;++i)v|=uint64(p.bytes.at(offset+i))<<(8*i);return v;}
int main(){
 sCharShipmentStore.rows={{10,{10,1,100,3,987}},{11,{11,1,100,3,988}},{50,{50,2,100,3,989}}};
 sCharShipmentContainerStore.rows={{1,{1,3}},{2,{2,3}}};spellMgr.rows.rows={{100,{100}}};
 Garrison g;Player player;player.g=&g;WorldSession session{&player,{}};
 WorldPackets::Garrison::GarrisonRequestLandingPageShipmentInfo landing;
 WorldPackets::Garrison::GarrisonRequestShipmentInfo info;
 WorldPackets::Garrison::GarrisonCreateShipment create;
 auto hi=uint64(1)<<40;
 g._workorders={{hi,{hi,50,10,100,200,0}},{hi+7,{hi+7,50,11,90,190,0}},{hi+9,{hi+9,60,50,20,40,0}}};
 session.HandleRequestLandingPageShipmentInfoOpcode(landing);
 auto const packet=session.sent.back();check(packet.bytes.size()==8+3*32&&value(packet,0,4)==3&&value(packet,4,4)==3,"landing packet header/count");
 std::vector<uint64> ids;for(unsigned off=8;off<packet.bytes.size();off+=32){ids.push_back(value(packet,off+4,8));check(value(packet,off+12,8)==0,"DB2 follower ID sent as database identity");}
 std::sort(ids.begin(),ids.end());check(ids==std::vector<uint64>{hi,hi+7,hi+9}&&g._workorders.size()==3,"sparse queue packet identity/phantom insertion");
 session.sent.clear();session.HandleGarrisonGetShipmentInfo(info);
 check(session.sent.size()==1,"info packet missing");auto const detail=session.sent.back();
 check(detail.bytes.size()==17+2*32&&value(detail,9,4)==2&&value(detail,13,4)==50,"plot filter/count/length");
 check(g._workorders.size()==3,"info inserted phantom records");
 // Reject malformed rows, match reported count to emitted rows.
 g._workorders[hi+10]={0,50,10,0,20,0};g._workorders[hi+11]={hi+11,50,10,200,100,0};g._workorders[hi+12]={hi+12,50,999,0,100,0};
 session.sent.clear();session.HandleGarrisonGetShipmentInfo(info);check(session.sent.back().bytes.size()==81&&value(session.sent.back(),9,4)==2,"invalid order included in info count");
 session.sent.clear();session.HandleRequestLandingPageShipmentInfoOpcode(landing);check(session.sent.back().bytes.size()==104&&value(session.sent.back(),4,4)==3,"invalid landing order serialized");
 // Empty queue sends a bounded, empty packet.
 g._workorders.clear();session.sent.clear();session.HandleGarrisonGetShipmentInfo(info);check(session.sent.back().bytes.size()==17&&value(session.sent.back(),9,4)==0,"empty info response");
 session.sent.clear();session.HandleRequestLandingPageShipmentInfoOpcode(landing);check(session.sent.back().bytes.size()==8,"empty landing response");
 // Advertised capacity also bounds arbitrarily large client requests.
 create.Count=std::numeric_limits<uint32>::max();session.sent.clear();session.HandleGarrisonCreateShipmentOpcode(create);
 check(g._workorders.size()==3&&player.casts==3&&session.sent.size()==3,"unbounded client request");
 for(auto const& p:session.sent)check(p.bytes.size()==16&&value(p,0,8)>=hi&&value(p,8,4)==10&&value(p,12,4)==1,"creation packet layout/full ID");
 session.sent.clear();session.HandleGarrisonCreateShipmentOpcode(create);check(session.sent.empty()&&player.casts==3,"full queue created order");
 // Zero retains the established one-order behavior without mutating the request.
 g._workorders.clear();g.started=0;create.Count=0;session.HandleGarrisonCreateShipmentOpcode(create);
 check(g._workorders.size()==1&&create.Count==0,"zero count handling");
 g._workorders.clear();g.started=0;g.failAfter=0;session.sent.clear();auto casts=player.casts;
 session.HandleGarrisonCreateShipmentOpcode(create);check(g._workorders.empty()&&session.sent.empty()&&player.casts==casts,"failed start cast spell or announced success");
 g.failAfter=1;g.started=0;create.Count=3;session.HandleGarrisonCreateShipmentOpcode(create);check(g._workorders.size()==1&&session.sent.size()==1&&player.casts==casts+1,"partial start failure");
 g._workorders.clear();g.started=0;g.failAfter=100;session.sent.clear();
 for(unsigned mode=0;mode<7;++mode){
  auto container=sCharShipmentContainerStore.rows;auto spells=spellMgr.rows.rows;auto oldPlot=g.plot;auto max=sCharShipmentStore.rows.at(10).MaxShipments;
  if(mode==0)session._player=nullptr;
  if(mode==1)player.interact=false;
  if(mode==2)player.inside=false;
  if(mode==3)sCharShipmentContainerStore.rows.clear();
  if(mode==4)player.g=nullptr;
  if(mode==5)g.plot=0;
  if(mode==6)spellMgr.rows.rows.clear();
  if(mode!=6)session.HandleGarrisonGetShipmentInfo(info);
  session.HandleGarrisonCreateShipmentOpcode(create);
  check(g._workorders.empty()&&session.sent.empty(),"invalid owner/NPC/container/plot/spell created or disclosed orders");
  session._player=&player;player.interact=player.inside=true;player.g=&g;g.plot=oldPlot;
  sCharShipmentContainerStore.rows=container;spellMgr.rows.rows=spells;sCharShipmentStore.rows.at(10).MaxShipments=max;
 }
 sCharShipmentStore.rows.at(10).MaxShipments=0;session.HandleGarrisonCreateShipmentOpcode(create);check(g._workorders.empty(),"zero capacity ignored");
 std::cout<<"PASS: actual shipment handlers and packet writers; sparse queues, plot filters, malformed rows, capacity, missing dependencies and failed creation\n";
}
'''
    harness=harness.replace('BUILDING',building).replace('WRITERS',writers).replace('METHODS',methods)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'shipments.cpp';exe=Path(tmp)/'shipments';cpp.write_text(harness,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-D_GLIBCXX_DEBUG',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True,timeout=30)


if __name__=='__main__':main()
