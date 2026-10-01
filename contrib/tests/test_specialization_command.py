#!/usr/bin/env python3
"""Compile actual reset/activation/item selection bodies with minimal DB2/player doubles."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/game/Entities/Player/PlayerCharacterSetup.cpp').read_text('utf8')
    defines = (root / 'src/server/game/Miscellaneous/SharedDefines.h').read_text('utf8')
    def function(name):
        match = re.search(r'^[^\n]+ PlayerCharacterSetup::' + name + r'\([^\n]*\)\n\{.*?^\}', source, re.M | re.S)
        assert match, name
        return match[0]
    harness = r'''
#include <cstdint>
#include <map>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
using uint8=std::uint8_t;
using int8=std::int8_t;
constexpr uint32 MAX_CLASSES=13, PLAYER_XP=0, EQUIP_ERR_OK=0;
enum InventoryType { INVTYPE_NON_EQUIP, INVTYPE_CHEST, INVTYPE_RELIC=28 };
struct ChrSpecializationEntry {
    int8 ClassID,OrderIndex;
    uint32 ID;
    bool IsPetSpecialization() const {return ClassID==0;}
};
struct Store {
    std::map<uint32,ChrSpecializationEntry> entries;
    ChrSpecializationEntry const* LookupEntry(uint32 id) const {
        auto i=entries.find(id);return i==entries.end()?nullptr:&i->second;
    }
    uint32 GetNumRows() const {return 1000;}
} sChrSpecializationStore;
struct Manager {
    ChrSpecializationEntry const* GetChrSpecializationByIndex(uint32 cls,uint32 index) const {
        for(auto const& pair:sChrSpecializationStore.entries)
            if(pair.second.ClassID==int8(cls) && pair.second.OrderIndex==int8(index))return &pair.second;
        return nullptr;
    }
} sDB2Manager;
struct ItemTemplate {
    uint32 spec;
    bool usable=true;
    bool IsUsableBySpecialization(uint32 s,uint32,bool) const {return spec==0 || spec==s;}
};
struct Player {
    uint8 cls=11;
    uint32 spec=100,level=100,xp=123,activations=0;
    uint8 getClass() const {return cls;}
    uint32 GetSpecializationId() const {return spec;}
    uint32 getLevel() const {return level;}
    void GiveLevel(uint32 value){level=value;}
    void SetUInt32Value(uint32,uint32 value){xp=value;}
    void ActivateTalentGroup(ChrSpecializationEntry const* s){spec=s->ID;++activations;}
    uint32 CanUseItem(ItemTemplate const* item) const {return item->usable?0:1;}
};
using LevelItems=std::vector<ItemTemplate const*>;
struct ItemsForLevel {LevelItems m_Items,m_TenacityItems;};
uint32 urand(uint32 low,uint32){return low;}
struct PlayerCharacterSetup {
    using EquipmentByLevel=std::map<uint32,ItemsForLevel>;
    inline static EquipmentByLevel classesEquips[MAX_CLASSES][INVTYPE_RELIC+1];
    Player* m_Player;
    uint32 m_TargetLevel=0,m_SetupFailures=0;
    bool m_Finish=true,m_TenacitySetting=false;
    uint32 m_ActiveTalentType=255,m_ResetStep=14;
    bool ResetPlayerToLevel(uint32,uint32,bool=false);
    void ActivateSpecialization();
    ItemTemplate const* GetRandomItemFromLoopLV(uint32,InventoryType,uint32,ItemTemplate const*=nullptr);
};
void check(bool condition,char const* message){if(!condition)throw std::runtime_error(message);}
'''.replace('const*=nullptr', 'const* = nullptr')
    for name in ('MAX_SPECIALIZATIONS', 'PLAYER_SPECIALIZATION_KEEP'):
        harness += '\n' + re.search(r'^#define '+name+r'\s+[^\n]+', defines, re.M)[0] + '\n'
    for name in ('ResetPlayerToLevel', 'ActivateSpecialization', 'GetRandomItemFromLoopLV'):
        harness += function(name) + '\n'
    harness += r'''
int main(){
    for(int8 order=0;order<4;++order)
        sChrSpecializationStore.entries[100+order]={11,order,uint32(100+order)};
    sChrSpecializationStore.entries[200]={12,0,200};
    sChrSpecializationStore.entries[201]={12,1,201};
    for(uint32 order=0;order<4;++order){
        Player p;PlayerCharacterSetup setup{&p};
        check(setup.ResetPlayerToLevel(110,order),"valid druid specialization rejected");
        setup.ActivateSpecialization();
        check(p.spec==100+order && p.level==100 && p.xp==123 && setup.m_TargetLevel==110,"wrong activation/level");
        check(!setup.ResetPlayerToLevel(20,0),"concurrent reset accepted");
        check(p.level==100,"concurrent reset changed level");
    }
    Player p;p.spec=102;
    PlayerCharacterSetup keep{&p};
    check(keep.ResetPlayerToLevel(100,PLAYER_SPECIALIZATION_KEEP),"KEEP rejected");
    keep.ActivateSpecialization();
    check(p.spec==102 && p.xp==123,"KEEP changed current spec or unchanged-level XP");
    p.cls=12;p.spec=201;
    for(uint32 invalid:{2u,3u,4u,254u,256u,0xffffffffu}){
        PlayerCharacterSetup bad{&p};
        check(!bad.ResetPlayerToLevel(20,invalid),"invalid class/index accepted");
        check(p.level==100 && bad.m_Finish,"rejected request mutated state");
    }
    for(uint32 id:{0u,100u,300u,301u,302u}){
        sChrSpecializationStore.entries[300]={0,0,300};
        sChrSpecializationStore.entries[301]={12,-1,301};
        sChrSpecializationStore.entries[302]={12,4,302};
        p.spec=id;PlayerCharacterSetup bad{&p};
        check(!bad.ResetPlayerToLevel(20,PLAYER_SPECIALIZATION_KEEP),"invalid current DB2 accepted");
    }
    PlayerCharacterSetup noPlayer{nullptr};
    check(!noPlayer.ResetPlayerToLevel(110,0),"null player accepted");
    p.cls=11;p.spec=103;p.level=110;
    PlayerCharacterSetup gear{&p};
    ItemTemplate guardian{102},resto{103},restricted{103,false},shared{0};
    auto& pools=PlayerCharacterSetup::classesEquips[11][INVTYPE_CHEST];
    pools[110].m_Items={&guardian,&restricted,&resto};
    check(gear.GetRandomItemFromLoopLV(11,INVTYPE_CHEST,110)==&resto,"wrong fourth-spec equipment");
    pools[109].m_Items={&shared};
    check(gear.GetRandomItemFromLoopLV(11,INVTYPE_CHEST,110,&resto)==&shared,"excluded item / lower level fallback");
    gear.m_TenacitySetting=true;pools[110].m_TenacityItems={&guardian};
    check(gear.GetRandomItemFromLoopLV(11,INVTYPE_CHEST,110)==&resto,"incompatible tenacity equipment");
    pools[110].m_TenacityItems.push_back(&shared);
    check(gear.GetRandomItemFromLoopLV(11,INVTYPE_CHEST,110)==&shared,"tenacity preference lost");
    check(!gear.GetRandomItemFromLoopLV(MAX_CLASSES,INVTYPE_CHEST,110),"invalid class reservoir accepted");
    pools.clear();check(!gear.GetRandomItemFromLoopLV(11,INVTYPE_CHEST,110),"empty reservoir");
    std::cout<<"PASS: command reset, four specs, KEEP, rejection without mutation, equipment filtering\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'regression.cpp'; exe=Path(tmp)/'regression'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
