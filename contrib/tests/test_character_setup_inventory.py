#!/usr/bin/env python3
"""Actual pending-item and bag methods; model deletion/movement between reset ticks."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Entities/Player/PlayerCharacterSetup.cpp').read_text('utf8')
    header=(root/'src/server/game/Entities/Player/PlayerCharacterSetup.h').read_text('utf8')
    methods='\n'.join(re.search(r'^void PlayerCharacterSetup::'+name+r'\(\)\n\{.*?^\}',source,re.M|re.S)[0]
                      for name in ['CheckInventroy','UpequipFromAll'])
    queue=re.search(r'typedef [^;]+ PendingEquipment;',header)[0]
    harness=r'''
#include <cstdint>
#include <map>
#include <memory>
#include <list>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t;using uint16=std::uint16_t;using uint32=std::uint32_t;
using ObjectGuid=std::uint64_t;
enum InventoryType {INVTYPE_AMMO=24,INVTYPE_BAG=18,INVTYPE_WEAPON=13};
constexpr uint8 INVENTORY_SLOT_BAG_START=19,INVENTORY_SLOT_BAG_END=23,INVENTORY_SLOT_BAG_0=255;
constexpr uint8 NULL_BAG=0,NULL_SLOT=255;
constexpr uint32 EQUIP_ERR_OK=0;
using ItemPosCountVec=std::vector<uint16>;
#define TC_LOG_ERROR(...) ((void)0)
uint32 GenerateItemRandomPropertyId(uint32){return 0;}
struct ItemTemplate {
    InventoryType type=INVTYPE_BAG;
    uint32 GetId() const{return 21876;}
    InventoryType GetInventoryType() const{return type;}
};
struct Item {ItemTemplate prototype;uint16 pos=30;
    ItemTemplate const* GetTemplate() const{return &prototype;}
    uint16 GetPos() const{return pos;}
};
struct ObjectMgr {bool exists=true;ItemTemplate bag;
    ItemTemplate const* GetItemTemplate(uint32) const{return exists?&bag:nullptr;}
} manager;
ObjectMgr* sObjectMgr=&manager;
struct Player {
    std::map<ObjectGuid,std::unique_ptr<Item>> items;
    std::map<uint8,Item*> bags;
    bool canStore=true,canEquip=true;
    uint32 created=0;
    Item* GetItemByGuid(ObjectGuid guid) const{auto i=items.find(guid);return i==items.end()?nullptr:i->second.get();}
    bool IsInventoryPos(uint16 pos) const{return (pos>=23 && pos<1000) || pos==2000;}
    bool IsBankPos(uint16 pos) const{return pos>=1000;}
    Item* GetItemByPos(uint8,uint8 slot) const{auto i=bags.find(slot);return i==bags.end()?nullptr:i->second;}
    uint32 CanStoreNewItem(uint8,uint8,ItemPosCountVec& dest,uint32,uint32){if(!canStore)return 1;dest.push_back(30);return 0;}
    Item* StoreNewItem(ItemPosCountVec const&,uint32,bool,uint32){auto guid=100+(++created);items[guid]=std::make_unique<Item>();return items[guid].get();}
};
struct PlayerCharacterSetup {
    QUEUE
    Player* m_Player;
    PendingEquipment m_NeedEquips;
    std::vector<std::pair<uint16,uint8>> equipped;
    uint32 m_SetupFailures=0;
    void CheckInventroy();void UpequipFromAll();
    bool EquipItem(Item* item,uint8 slot){
        if(!m_Player->canEquip)return false;
        equipped.emplace_back(item->GetPos(),slot);
        if(item->prototype.type==INVTYPE_BAG)m_Player->bags[slot]=item;
        return true;
    }
};
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
METHODS
int main(){
    Player p;PlayerCharacterSetup setup{&p,{}, {}};
    manager.exists=false;setup.CheckInventroy();check(p.created==0,"missing template created items");manager.exists=true;
    p.canStore=false;setup.CheckInventroy();check(p.created==0,"full inventory created items");p.canStore=true;
    setup.CheckInventroy();check(p.bags.size()==4 && p.created==4,"not all four bag slots filled");
    setup.CheckInventroy();check(p.created==4,"existing bags replaced");
    p.bags.erase(22);setup.CheckInventroy();check(p.bags.count(22) && p.created==5,"fourth bag slot ignored");
    Player failed;failed.canEquip=false;PlayerCharacterSetup bad{&failed,{}, {}};bad.CheckInventroy();
    check(failed.created==1 && failed.bags.empty(),"repeated creation after failed equip");
    p.items[1]=std::make_unique<Item>();p.items[1]->prototype.type=INVTYPE_WEAPON;
    p.items[2]=std::make_unique<Item>();p.items[2]->prototype.type=INVTYPE_WEAPON;
    p.items[3]=std::make_unique<Item>();p.items[3]->prototype.type=INVTYPE_WEAPON;
    setup.m_NeedEquips={{1,15},{2,16},{3,15}};
    p.items.erase(1); // Deleted between AddEquipFromAll and UpequipFromAll.
    p.items[2]->pos=260; // Moved to another inventory bag; resolve its current position.
    p.items[3]->pos=2000; // Banked; should not be pulled back into equipment.
    setup.equipped.clear();setup.UpequipFromAll();
    check(setup.equipped.size()==1 && setup.equipped[0].first==260 && setup.equipped[0].second==16,"stale/moved item handling");
    check(setup.m_NeedEquips.empty(),"pending queue not cleared");
    std::cout<<"PASS: missing bag template, all bag slots, full inventory, equip failure, deleted/moved/banked items\n";
}
'''.replace('QUEUE',queue).replace('METHODS',methods)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'inventory.cpp';exe=Path(tmp)/'inventory'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
