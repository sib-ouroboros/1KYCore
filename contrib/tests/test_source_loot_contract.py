#!/usr/bin/env python3
"""Exercise native loot-key selection and item eligibility for restored objects."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def method(source,marker):
    start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    registry=json.loads((root/'docs/audit-data/campaign-source-loot-restoration.json').read_text('utf8'))
    key=method((root/'src/server/game/Entities/GameObject/GameObjectData.h').read_text('utf8'),'    uint32 GetLootId() const')
    allowed=method((root/'src/server/game/Loot/Loot.cpp').read_text('utf8'),'bool LootItem::AllowedForPlayer(')
    registry2=json.loads((root/'docs/audit-data/campaign-wildcard-loot-restoration.json').read_text('utf8'))
    boiler=json.loads((root/'docs/audit-data/campaign-fel-boiler-restoration.json').read_text('utf8'))
    rows=[]
    for template,loot in zip(registry['templates']+registry2['templates']+boiler['templates'],registry['loot']+registry2['loot']+boiler['loot']):
        assert template['entry']==loot['Entry']==template['Data1'] and template['Data30']=='0'
        assert loot['Reference']=='0' and loot['LootMode'] in ('1','65535') and loot['Chance']=='100'
        rows.append('{'+','.join((template['type'],template['Data1'],loot['Item'],loot['QuestRequired']))+'}')
    harness=r'''
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;
constexpr uint32 GAMEOBJECT_TYPE_CHEST=3,GAMEOBJECT_TYPE_FISHINGHOLE=25,GAMEOBJECT_TYPE_GATHERING_NODE=50,GAMEOBJECT_TYPE_CHALLENGE_MODE_REWARD=51;
constexpr uint32 ITEM_FLAG_HIDE_UNUSABLE_RECIPE=1,ITEM_FLAG2_FACTION_HORDE=1,ITEM_FLAG2_FACTION_ALLIANCE=2,ITEM_FLAGS_CU_IGNORE_QUEST_STATUS=1;
constexpr uint32 HORDE=1,ALLIANCE=2,QUEST_STATUS_NONE=0;
struct Effect {uint32 SpellID=0;};
struct ItemTemplate {
    uint32 FlagsCu=0,flags=0,flags2=0;Effect effect;Effect* Effects[2]={&effect,&effect};
    uint32 GetFlags()const{return flags;}uint32 GetFlags2()const{return flags2;}
    uint32 GetRequiredSkill()const{return 0;}uint32 GetStartQuest()const{return 0;}
};
struct Player {
    bool needs=true;uint32 questItem=0;
    bool HasQuestForItem(uint32 item)const{return needs&&questItem==item;}
    bool HasSkill(uint32)const{return true;}bool HasSpell(uint32)const{return false;}
    uint32 GetTeam()const{return HORDE;}uint32 GetQuestStatus(uint32)const{return QUEST_STATUS_NONE;}
};
struct ConditionMgr {bool valid=true;bool IsObjectMeetToConditions(Player*,int)const{return valid;}} conditionsMgr;
auto* sConditionMgr=&conditionsMgr;
struct ObjectMgr {ItemTemplate proto;bool exists=true;ItemTemplate const* GetItemTemplate(uint32)const{return exists?&proto:nullptr;}} objectMgr;
auto* sObjectMgr=&objectMgr;
struct LootItem {bool currency=false,needs_quest=false;uint32 itemid=0;int conditions=0;bool AllowedForPlayer(Player const*)const;};
ALLOWED
struct GameObjectTemplate {
    uint32 type=0;
    struct Part {uint32 chestLoot=0;};Part chest,fishingHole,gatheringNode,challengeModeReward;
KEY
};
void check(bool value){if(!value)throw std::runtime_error("source loot contract regression");}
struct Row {uint32 type,loot,item,quest;};
int main(){
    Row rows[]={ROWS};
    for(auto const& row:rows){
        GameObjectTemplate object;object.type=row.type;
        if(row.type==3)object.chest.chestLoot=row.loot;else object.fishingHole.chestLoot=row.loot;
        check(object.GetLootId()==row.loot);
        Player player;player.questItem=row.item;LootItem item;item.itemid=row.item;item.needs_quest=row.quest;
        check(item.AllowedForPlayer(&player));
        player.needs=false;check(item.AllowedForPlayer(&player)==!row.quest);
        conditionsMgr.valid=false;check(!item.AllowedForPlayer(&player));conditionsMgr.valid=true;
        objectMgr.exists=false;check(!item.AllowedForPlayer(&player));objectMgr.exists=true;
        if(row.quest){player.needs=true;player.questItem=6948;check(!item.AllowedForPlayer(&player));}
        objectMgr.proto.flags2=ITEM_FLAG2_FACTION_ALLIANCE;check(!item.AllowedForPlayer(&player));objectMgr.proto.flags2=0;
    }
    GameObjectTemplate unrelated;unrelated.type=5;unrelated.chest.chestLoot=123;check(unrelated.GetLootId()==0);
    std::cout<<"PASS: actual native loot ID and item eligibility, all eight source rows, needed/completed/unrelated quest, conditions, missing item and faction restriction\n";
}
'''.replace('ALLOWED',allowed).replace('KEY',key).replace('ROWS',','.join(rows))
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'loot.cpp';exe=Path(tmp)/'loot';cpp.write_text(harness,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
