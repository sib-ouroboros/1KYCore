#!/usr/bin/env python3
"""Exercise actual weapon planning and equipment queue with Legion specialization fixtures."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Entities/Player/PlayerCharacterSetup.cpp').read_text('utf8')
    player=(root/'src/server/game/Entities/Player/Player.h').read_text('utf8')
    item=(root/'src/server/game/Entities/Item/ItemTemplate.h').read_text('utf8')
    enums=[]
    for name,text in [('TalentSpecialization',player),('EquipmentSlots',player),('InventoryType',item)]:
        enums.append(re.search(r'^enum '+name+r'\b.*?^\};',text,re.M|re.S)[0])
    functions=[]
    for name in ['RandomWeaponsForSpecialization','AddEquipFromAll']:
        functions.append(re.search(r'^void PlayerCharacterSetup::'+name+r'\(\)\n\{.*?^\}',source,re.M|re.S)[0])
    harness=r'''
#include <cstdint>
#include <vector>
#include <map>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
using uint8=std::uint8_t;
constexpr uint32 MAX_CLASSES=13;
constexpr uint8 NULL_SLOT=255;
'''+'\n'.join(enums)+r'''
struct ItemTemplate {InventoryType type;uint32 id;};
struct Player {
    uint32 spec=105;
    bool dual=true,titan=true;
    uint32 getLevel() const{return 110;}
    uint8 getClass() const{return 11;}
    uint32 GetSpecializationId() const{return spec;}
    bool CanDualWield() const{return dual;}
    bool CanTitanGrip() const{return titan;}
};
struct PlayerCharacterSetup {
    Player* m_Player;
    std::vector<ItemTemplate> available;
    std::vector<std::pair<ItemTemplate const*,uint8>> m_NeedEquips;
    void RandomWeaponsForSpecialization();
    void AddEquipFromAll();
    void AddOnceEquip(ItemTemplate const* item,uint8 slot=NULL_SLOT){if(item)m_NeedEquips.emplace_back(item,slot);}
    ItemTemplate const* GetRandomItemFromLoopLV(uint32,InventoryType type,uint32,ItemTemplate const* exclude=nullptr){
        for(auto const& item:available)if(item.type==type && &item!=exclude)return &item;
        return nullptr;
    }
};
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
int main(){
    Player p;
    PlayerCharacterSetup setup{&p,{}, {}};
    for(InventoryType type:{INVTYPE_2HWEAPON,INVTYPE_WEAPON,INVTYPE_WEAPONMAINHAND,INVTYPE_WEAPONOFFHAND,
                           INVTYPE_RANGED,INVTYPE_RANGEDRIGHT,INVTYPE_SHIELD,INVTYPE_HOLDABLE,
                           INVTYPE_FINGER,INVTYPE_TRINKET}){
        setup.available.push_back({type,uint32(setup.available.size()+1)});
        setup.available.push_back({type,uint32(setup.available.size()+1)});
    }
    // Numeric client specialization IDs keep these expectations independent of switch labels.
    std::map<uint32,std::pair<InventoryType,InventoryType>> expected;
    for(uint32 id:{71,70,250,252,255,103,104,268,62,63,64,256,257,258,265,266,267,102,105,270})
        expected[id]={INVTYPE_2HWEAPON,INVTYPE_NON_EQUIP};
    expected[72]={INVTYPE_2HWEAPON,INVTYPE_2HWEAPON};
    for(uint32 id:{251,259,260,261,263,269,577,581})expected[id]={INVTYPE_WEAPON,INVTYPE_WEAPON};
    for(uint32 id:{73,65,66,262,264})expected[id]={INVTYPE_WEAPON,INVTYPE_SHIELD};
    for(uint32 id:{253,254})expected[id]={INVTYPE_RANGED,INVTYPE_NON_EQUIP};
    check(expected.size()==36,"all Legion specs must be covered");
    for(auto const& fixture:expected){
        p.spec=fixture.first;setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
        auto const& queue=setup.m_NeedEquips;
        bool off=fixture.second.second!=INVTYPE_NON_EQUIP;
        check(queue.size()==(off?2u:1u),"wrong weapon count");
        check(queue[0].first->type==fixture.second.first && queue[0].second==EQUIPMENT_SLOT_MAINHAND,"wrong main hand");
        if(off){
            check(queue[1].first->type==fixture.second.second && queue[1].second==EQUIPMENT_SLOT_OFFHAND,"wrong off hand");
            check(queue[0].first!=queue[1].first,"same template selected twice");
        }
    }
    p.spec=72;p.titan=false;setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips[0].first->type==INVTYPE_WEAPON,"Titan Grip capability ignored");
    p.dual=false;setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.size()==1,"dual wield capability ignored");
    p.dual=true;p.spec=105;
    setup.AddEquipFromAll();
    std::map<uint8,uint32> slots;
    for(auto const& selected:setup.m_NeedEquips){
        check(!slots.count(selected.second),"paired items overwrite the same slot");
        slots[selected.second]=selected.first->id;
    }
    check(slots.count(EQUIPMENT_SLOT_FINGER1) && slots.count(EQUIPMENT_SLOT_FINGER2),"missing ring pair");
    check(slots.count(EQUIPMENT_SLOT_TRINKET1) && slots.count(EQUIPMENT_SLOT_TRINKET2),"missing trinket pair");
    setup.available={{INVTYPE_WEAPONMAINHAND,1},{INVTYPE_HOLDABLE,2}};
    setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.size()==2 && setup.m_NeedEquips[1].second==EQUIPMENT_SLOT_OFFHAND,"caster fallback");
    p.spec=251;setup.available={{INVTYPE_WEAPONMAINHAND,1},{INVTYPE_WEAPONOFFHAND,2}};
    setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.size()==2,"dedicated one-handed fallback");
    p.spec=254;setup.available={{INVTYPE_RANGEDRIGHT,1}};
    setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.size()==1,"gun fallback");
    p.spec=0;setup.m_NeedEquips.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.empty(),"unknown specialization generated weapons");
    p.spec=105;setup.available.clear();setup.RandomWeaponsForSpecialization();
    check(setup.m_NeedEquips.empty(),"empty item pool");
    std::cout<<"PASS: 36 specialization weapon layouts, native capabilities, paired slots and fallbacks\n";
}
'''
    harness=harness.replace('int main(){','\n'.join(functions)+'\nint main(){')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'weapons.cpp';exe=Path(tmp)/'weapons'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
