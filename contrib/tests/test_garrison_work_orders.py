#!/usr/bin/env python3
"""Compile actual work-order methods with checked iterators and optional sanitizers."""
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
    header = (root/'src/server/game/Garrison/Garrison.h').read_text('utf8')
    methods = '\n'.join(re.search(r'^[^\n]+ Garrison::'+name+r'\([^\n]*\)\n\{.*?^\}', source, re.M|re.S)[0]
                        for name in ['GetWorkOrder','StartWorkOrder','DeleteWorkOrder','RewardWorkOrder','UpdateWorkOrders'])
    save_loop = re.search(r'    for \(auto const& p : _workorders\)\n    \{.*?^    \}',source,re.M|re.S)[0]
    methods += '\nvoid Garrison::SaveOrders(CharacterDatabaseTransaction& trans)\n{\n    CharacterDatabasePreparedStatement* stmt;\n'+save_loop+'\n}\n'
    order = re.search(r'    struct WorkOrder\n    \{.*?\n    \};', header, re.S)[0]
    # Check persistence width alongside actual lookup/create/delete code.
    save = source[source.index('for (auto const& p : _workorders)'):source.index('uint32 Garrison::GetWorkOrderCount')]
    assert 'if (!workorder.DatabaseID)' in save
    assert 'setUInt64(index++, workorder.DatabaseID)' in save
    assert 'uint64 dbId = fields[0].GetUInt64()' in source
    harness = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <ctime>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <unordered_map>
#include <vector>
using uint32=std::uint32_t;using uint64=std::uint64_t;using uint8=std::uint8_t;
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
std::time_t fakeTime(void*){return 200;}
#define time fakeTime
constexpr uint32 CHAR_INS_GARRISON_WORKORDER=1,CHAR_DEL_GARRISON_WORKORDER=2;
constexpr uint32 TRIGGERED_FULL_MASK=1,GAMEOBJECT_FLAGS=1,GO_FLAG_FREEZE_ANIMATION=2,GO_STATE_READY=1,WEEK=604800;
struct Position{};struct QuaternionData{};
struct SpellInfo{uint32 ID;};
struct CharShipmentEntry{uint32 ID,ShipmentContainerID,Duration,OnCompleteSpellID,DummyItemID,GarrFollowerID;};
struct CharShipmentContainerEntry{uint32 ID;};
struct GarrFollowerEntry{uint32 ID;};
template<class T>struct Store{std::unordered_map<uint32,T> rows;
 T const* LookupEntry(uint32 id)const{auto i=rows.find(id);return i==rows.end()?nullptr:&i->second;}};
Store<GarrFollowerEntry> sGarrFollowerStore;
Store<CharShipmentEntry> sCharShipmentStore;Store<CharShipmentContainerEntry> sCharShipmentContainerStore;
struct SpellMgr{Store<SpellInfo> spells;SpellInfo const* GetSpellInfo(uint32 id){return spells.LookupEntry(id);}} spellMgr;
SpellMgr* sSpellMgr=&spellMgr;
struct Statement{uint32 kind;std::array<uint64,6> values{};
 void setUInt64(uint8 i,uint64 v){values.at(i)=v;}void setUInt32(uint8 i,uint32 v){values.at(i)=v;}};
using CharacterDatabasePreparedStatement=Statement;
struct Transaction{std::vector<Statement> rows;void Append(Statement* s){rows.push_back(*s);}};
using CharacterDatabaseTransaction=std::shared_ptr<Transaction>;
struct Database{std::vector<std::unique_ptr<Statement>> allocated;std::vector<Statement> inserts;std::vector<uint64> deletes;
 Statement* GetPreparedStatement(uint32 kind){allocated.emplace_back(new Statement{kind,{}});return allocated.back().get();}
 CharacterDatabaseTransaction BeginTransaction(){return std::make_shared<Transaction>();}
 void CommitTransaction(CharacterDatabaseTransaction const& t){for(auto const& s:t->rows)inserts.push_back(s);}
 void AsyncQuery(Statement* s){deletes.push_back(s->values[0]);}
} CharacterDatabase;
struct GarrisonClassHallPlotGOInfo{uint32 GameObjectId;Position Pos;uint32 workDisplayId,completeDisplayId;};
struct GarrisonMgr{uint64 next=uint64(1)<<40;std::unordered_map<uint32,GarrisonClassHallPlotGOInfo> plots;
 uint64 GenerateWorkorderDbId(){return next++;}
 GarrisonClassHallPlotGOInfo const* GetPlotClassHallGOInfo(uint32 id){auto i=plots.find(id);return i==plots.end()?nullptr:&i->second;}
} sGarrisonMgr;
struct GameObject{uint32 display=0;bool frozen=false;uint32 state=0,calls=0;
 void SetDisplayId(uint32 id){display=id;++calls;}void SetFlag(uint32,uint32){frozen=true;}
 void RemoveFlag(uint32,uint32){frozen=false;}void SetGoState(uint32 v){state=v;}};
struct Guid{uint64 GetCounter()const{return 9876543210ULL;}};
struct Player{bool inside=true,failSummon=false,failItem=false;std::unordered_map<uint32,GameObject> objects;unsigned casts=0,items=0,summons=0;
 Guid GetGUID()const{return {};}
 void CastSpell(Player*,SpellInfo const*,uint32){++casts;}bool AddItem(uint32,uint32 n){if(failItem)return false;items+=n;return true;}
 bool IsInGarrison()const{return inside;}
 GameObject* FindNearestGameObject(uint32 id,float){auto i=objects.find(id);return i==objects.end()?nullptr:&i->second;}
 GameObject* SummonGameObject(uint32 id,Position const&,QuaternionData,uint32,bool){++summons;return failSummon?nullptr:&objects[id];}
};
class Garrison{public:
ORDER
 Player* _owner;std::unordered_map<uint64,WorkOrder> _workorders;unsigned followers=0;
 explicit Garrison(Player* p):_owner(p){}
 Player* GetOwner(){return _owner;}
 WorkOrder* GetWorkOrder(uint64);uint64 StartWorkOrder(uint32,uint32);void DeleteWorkOrder(uint64);
 void RewardWorkOrder(uint32);void UpdateWorkOrders();void SaveOrders(CharacterDatabaseTransaction&);bool AddShipmentFollower(uint32){++followers;return true;}
};
METHODS
int main(){
 sCharShipmentStore.rows={{10,{10,1,10,100,200,300}},{11,{11,1,20,100,200,300}},{12,{12,2,10,0,200,0}},{13,{13,99,10,0,0,0}}};
 sCharShipmentContainerStore.rows={{1,{1}},{2,{2}}};spellMgr.spells.rows={{100,{100}}};
 sGarrFollowerStore.rows={{300,{300}}};
 Player player;Garrison g(&player);
 uint64 const high=uint64(1)<<40;
 g._workorders.emplace(7,Garrison::WorkOrder{7,50,10,100,300,0});
 g._workorders.emplace(high+7,Garrison::WorkOrder{high+7,60,11,100,900,0});
 check(g.GetWorkOrder(high+7)->PlotInstanceID==60,"lookup truncated 64-bit ID");
 check(!g.GetWorkOrder(high+8),"missing lookup found another order");
 auto id=g.StartWorkOrder(50,10);
 check(id==high,"new ID truncated");check(g._workorders.size()==3,"phantom orders inserted");
 check(g.GetWorkOrder(id)->CreationTime==300&&g.GetWorkOrder(id)->CompleteTime==310,"wrong plot queue time");
 check(CharacterDatabase.inserts.back().values[0]==high,"insert ID truncated");
 check(CharacterDatabase.inserts.back().values[1]==9876543210ULL,"owner ID truncated");
 auto next=g.StartWorkOrder(50,11);check(g.GetWorkOrder(next)->CreationTime==310&&g.GetWorkOrder(next)->CompleteTime==330,"next order not serialized");
 auto size=g._workorders.size();auto sequence=sGarrisonMgr.next;
 check(!g.StartWorkOrder(50,999)&&g._workorders.size()==size,"missing shipment writes data");
 g._workorders.emplace(high+9,Garrison::WorkOrder{high+9,90,10,0,std::numeric_limits<uint32>::max()-5,0});
 check(!g.StartWorkOrder(90,10)&&sGarrisonMgr.next==sequence,"timestamp overflow not rejected before allocation");
 g.DeleteWorkOrder(high+7);check(g.GetWorkOrder(7)&&!g.GetWorkOrder(high+7),"delete removed colliding low ID");
 check(CharacterDatabase.deletes.back()==high+7,"database delete ID truncated");
 size=CharacterDatabase.deletes.size();g.DeleteWorkOrder(high+99);check(CharacterDatabase.deletes.size()==size,"missing delete sent database request");
 g._workorders.clear();CharacterDatabase.inserts.clear();
 g._workorders={{uint64(1)<<32,{uint64(1)<<32,50,10,0,200,0}},{0,{0,50,10,0,200,0}}};
 auto transaction=CharacterDatabase.BeginTransaction();g.SaveOrders(transaction);CharacterDatabase.CommitTransaction(transaction);
 check(CharacterDatabase.inserts.size()==1&&CharacterDatabase.inserts[0].values[0]==(uint64(1)<<32),"save skipped high ID with zero low word");
 g._workorders.clear();CharacterDatabase.deletes.clear();
 g._workorders={{high,{high,50,10,0,200,0}},{high+1,{high+1,50,11,0,199,0}},{high+2,{high+2,50,10,0,201,0}},
 {high+3,{high+3,60,12,0,100,0}},{high+4,{high+4,70,999,0,100,0}},{high+5,{high+5,80,13,0,100,0}}};
 g.RewardWorkOrder(99);check(g._workorders.size()==6,"invalid container claimed order");
 g.RewardWorkOrder(1);check(g._workorders.size()==4&&player.casts==2&&player.items==2&&g.followers==2,"multiple recipes not collected exactly once");
 check(!g.GetWorkOrder(high)&&!g.GetWorkOrder(high+1)&&g.GetWorkOrder(high+2),"completed boundary or future order incorrect");
 g.RewardWorkOrder(1);check(player.items==2&&CharacterDatabase.deletes.size()==2,"repeat awarded twice");
 g.RewardWorkOrder(2);check(player.items==3&&g.GetWorkOrder(high+4),"other container or invalid shipment mishandled");
 // Refused delivery must keep the order before any follower/spell side effect.
 g._workorders.clear();CharacterDatabase.deletes.clear();
 g._workorders.emplace(high,Garrison::WorkOrder{high,50,10,0,200,0});
 auto casts=player.casts,items=player.items,followers=g.followers;
 player.failItem=true;g.RewardWorkOrder(1);
 check(g.GetWorkOrder(high)&&CharacterDatabase.deletes.empty()&&player.casts==casts&&player.items==items&&g.followers==followers,"inventory failure lost order or granted partial reward");
 player.failItem=false;g.RewardWorkOrder(1);g.RewardWorkOrder(1);
 check(!g.GetWorkOrder(high)&&player.items==items+1&&player.casts==casts+1&&g.followers==followers+1&&CharacterDatabase.deletes.size()==1,"inventory retry duplicated or failed");
 for(unsigned mode=0;mode<3;++mode){
  g._workorders.emplace(high,Garrison::WorkOrder{high,50,10,0,200,0});
  auto recipe=sCharShipmentStore.rows.at(10);
  if(mode==0)sCharShipmentStore.rows.at(10).OnCompleteSpellID=999;
  if(mode==1)sCharShipmentStore.rows.at(10).GarrFollowerID=999;
  if(mode==2){sCharShipmentStore.rows.at(10).OnCompleteSpellID=0;sCharShipmentStore.rows.at(10).DummyItemID=0;sCharShipmentStore.rows.at(10).GarrFollowerID=0;}
  items=player.items;casts=player.casts;followers=g.followers;
  g.RewardWorkOrder(1);check(g.GetWorkOrder(high)&&items==player.items&&casts==player.casts&&followers==g.followers,"missing completion dependency discarded order or delivered partial reward");
  sCharShipmentStore.rows.at(10)=recipe;g.RewardWorkOrder(1);check(!g.GetWorkOrder(high),"dependency repair cannot retry");
 }
 // A mixed ready/pending plot remains ready regardless of insertion order.
 sGarrisonMgr.plots={{50,{500,{},1000,2000}},{60,{600,{},1001,2001}}};
 for(bool reverse:{false,true}){
  g._workorders.clear();player.objects.clear();
  Garrison::WorkOrder ready{high,50,10,0,200,0},pending{high+1,50,11,0,300,0};
  if(reverse){g._workorders.emplace(high+1,pending);g._workorders.emplace(high,ready);}
  else{g._workorders.emplace(high,ready);g._workorders.emplace(high+1,pending);}
  g._workorders.emplace(high+2,Garrison::WorkOrder{high+2,999,10,0,100,0});
  g._workorders.emplace(high+3,Garrison::WorkOrder{high+3,60,999,0,100,0});
  g.UpdateWorkOrders();check(player.objects.size()==1,"missing plot or shipment created object");
  auto const& object=player.objects.at(500);check(object.display==2000&&object.frozen&&object.state==GO_STATE_READY&&object.calls==1,"ready state depends on iteration order");
 }
 g._workorders={{high,{high,50,10,0,300,0}}};g.UpdateWorkOrders();check(player.objects.at(500).display==1000&&!player.objects.at(500).frozen,"pending visual not restored");
 player.objects.clear();player.failSummon=true;g.UpdateWorkOrders();check(player.objects.empty(),"failed summon dereferenced");
 auto summons=player.summons;player.inside=false;g.UpdateWorkOrders();check(player.summons==summons,"outside garrison updated objects");
 std::cout<<"PASS: actual work-order queue, uint64 identity, reward erasure, recipes, repeat, missing dependencies and deterministic plot visuals\n";
}
'''
    harness = harness.replace('\nORDER\n','\n'+order+'\n').replace('\nMETHODS\n','\n'+methods+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'orders.cpp';exe=Path(tmp)/'orders'
        cpp.write_text(harness,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-D_GLIBCXX_DEBUG',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True,timeout=30)


if __name__=='__main__':main()
