#!/usr/bin/env python3
"""Exercise actual native loot processing and grouped selection for source mode 0."""
import json
import os
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root / 'docs/audit-data/campaign-wildcard-loot-restoration.json').read_text('utf8'))
    source = (root / 'src/server/game/Loot/LootMgr.cpp').read_text('utf8')
    selector = method(source, 'struct LootGroupInvalidSelector') + ';'
    roll = method(source, 'LootStoreItem const* LootTemplate::LootGroup::Roll(')
    grouped = method(source, 'void LootTemplate::LootGroup::Process(')
    process = method(source, 'void LootTemplate::Process(')
    rows = []
    for row in registry['loot']:
        assert row['LootMode'] == '65535' and row['Chance'] == '100' and row['Reference'] == '0'
        assert row['MinCount'] == row['MaxCount'] == '1'
        rows.append('{' + row['Item'] + ',' + row['GroupId'] + '}')
    harness = r'''
#include <cstdint>
#include <list>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t;using uint16=std::uint16_t;using uint32=std::uint32_t;
struct Player {};
struct LootStoreItem {
    uint32 itemid=0,reference=0,maxcount=1;uint16 lootmode=0;uint8 groupid=0;float chance=100;
    bool Roll(bool)const{return chance>=100;}
};
struct LootItem {uint32 itemid;};
struct Loot {
    std::vector<LootItem> items;uint8 maxDuplicates=2;
    void AddItem(LootStoreItem const& item,Player const* =nullptr,bool=false){items.push_back({item.itemid});}
};
using LootStoreItemList=std::list<LootStoreItem*>;
float rand_chance(){return 50;}
namespace Trinity {namespace Containers {
template<class T> typename T::value_type SelectRandomContainerElement(T const& c){return c.front();}
}}
class LootTemplate {
public:
    class LootGroup;
    using LootGroups=std::vector<LootGroup*>;
    LootStoreItemList Entries;LootGroups Groups;
    void Process(Loot&,bool,uint16,uint8,Player const* =nullptr,bool=false)const;
};
class LootTemplate::LootGroup {
public:
    LootStoreItemList ExplicitlyChanced,EqualChanced;
    LootStoreItem const* Roll(Loot&,uint16)const;
    void Process(Loot&,uint16)const;
};
struct ReferenceStore {LootTemplate const* GetLootFor(uint32)const{return nullptr;}} LootTemplates_Reference;
struct World {float getRate(int)const{return 1;}} world;
auto* sWorld=&world;constexpr int RATE_DROP_ITEM_REFERENCED_AMOUNT=1;
#define TC_LOG_ERROR(...) ((void)0)
SELECTOR
ROLL
GROUPED
PROCESS
void check(bool ok){if(!ok)throw std::runtime_error("wildcard loot mode regression");}
struct Row {uint32 item;uint8 group;};
int main(){
    Row rows[]={ROWS};
    for(auto const& row:rows){
        LootStoreItem item;item.itemid=row.item;item.groupid=row.group;
        LootTemplate lootTemplate;LootTemplate::LootGroup group;
        if(row.group){group.ExplicitlyChanced.push_back(&item);lootTemplate.Groups.push_back(&group);}
        else lootTemplate.Entries.push_back(&item);
        for(unsigned bit=0;bit<16;++bit){
            uint16 mask=static_cast<uint16>(1u<<bit);Loot before,after;
            item.lootmode=0;lootTemplate.Process(before,false,mask,0);check(before.items.empty());
            item.lootmode=65535;lootTemplate.Process(after,false,mask,0);
            check(after.items.size()==1&&after.items[0].itemid==row.item);
        }
        for(uint16 mask:{uint16(0x101),uint16(65535)}){
            Loot loot;lootTemplate.Process(loot,false,mask,0);check(loot.items.size()==1);
        }
        Loot disabled;lootTemplate.Process(disabled,false,0,0);check(disabled.items.empty());
        item.lootmode=2;Loot mismatch,match;
        lootTemplate.Process(mismatch,false,1,0);check(mismatch.items.empty());
        lootTemplate.Process(match,false,2,0);check(match.items.size()==1);
        if(row.group){
            item.lootmode=65535;Loot duplicates;duplicates.items={{row.item},{row.item}};
            lootTemplate.Process(duplicates,false,1,0);check(duplicates.items.size()==2);
            Loot selected;lootTemplate.Process(selected,false,1,1);check(selected.items.size()==1);
        }
    }
    std::cout<<"PASS: actual LootTemplate::Process, grouped Roll/Process and selector; all 16 mask bits, composite/zero modes, retained group, duplicates and unrelated restricted modes\n";
}
'''
    for name, value in [('SELECTOR', selector), ('ROLL', roll), ('GROUPED', grouped), ('PROCESS', process), ('ROWS', ','.join(rows))]:
        harness = harness.replace(name, value)
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp) / 'loot.cpp', Path(tmp) / 'loot'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
