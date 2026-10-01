#!/usr/bin/env python3
"""Exercise actual character-operation bodies and real JsonCpp with sanitizers."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    setup = (root/'src/server/game/Entities/Player/PlayerCharacterSetup.cpp').read_text('utf8')
    player = (root/'src/server/game/Entities/Player/Player.cpp').read_text('utf8')
    online = (root/'src/server/game/Server/OnlineMgr.cpp').read_text('utf8')
    session = (root/'src/server/game/Server/WorldSession.cpp').read_text('utf8')

    def body(source, name):
        match = re.search(r'^[^\n]+ '+re.escape(name)+r'\([^)]*\)\n\{.*?^\}', source, re.M|re.S)
        assert match, name
        return match[0]

    # Keep the production save guard and logout hook under regression coverage.
    save = body(player, 'Player::SaveToDB')
    guard = re.search(r'    if \(m_CharacterSetup && m_CharacterSetup->HasPendingReset\(\)\)\n        return;[^\n]*', save)[0]
    logout = body(session, 'WorldSession::LogoutPlayer')
    assert logout.index('_player->CompleteCharacterSetup();') < logout.index('_player->SaveToDB();')
    assert 'ViderLesSacs' not in setup

    harness = r'''
#include "json.h"
#include <cstdint>
#include <map>
#include <mutex>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
using uint8=std::uint8_t;
using int8=std::int8_t;
constexpr uint32 MAX_SPECIALIZATIONS=4,PLAYER_SPECIALIZATION_KEEP=255,PLAYER_XP=0;
void check(bool value,char const* message){if(!value)throw std::runtime_error(message);}
struct ChrSpecializationEntry {
    int8 ClassID,OrderIndex; uint32 ID;
    bool IsPetSpecialization() const{return !ClassID;}
};
struct Store {
    std::map<uint32,ChrSpecializationEntry> entries;
    ChrSpecializationEntry const* LookupEntry(uint32 id)const{
        auto i=entries.find(id);return i==entries.end()?nullptr:&i->second;
    }
    uint32 GetNumRows()const{return 1000;}
} sChrSpecializationStore;
struct Manager {
    ChrSpecializationEntry const* GetChrSpecializationByIndex(uint32 cls,uint32 order)const{
        for(auto const& p:sChrSpecializationStore.entries)
            if(p.second.ClassID==int8(cls)&&p.second.OrderIndex==int8(order))return &p.second;
        return nullptr;
    }
} sDB2Manager;
struct WorldSession {uint32 GetAccountId() const{return 1;}};
struct ToolAccountInfo {
    uint32 id=0;
    std::string username;
    struct {uint32 guid=0;} online;
    Json::Value operation;
    Json::Value SerializerInfo(){
        Json::Value data;data["id"]=id;data["username"]=username;
        if(!operation.isNull())data["operation"]=operation;
        return data;
    }
};
struct OnlineMgr {
    inline static std::mutex g_uniqueMgrLock;
    std::map<uint32,ToolAccountInfo> m_OnlinePlayerAcc;
    uint32 m_OperationSequence=0;
    std::string SerializerPlayerAccount(uint32=0,uint32=99);
    bool SetCharacterOperation(uint32,uint32,std::string const&,std::string const&,uint32);
    std::string SerializerCharacterOperation(uint32);
    bool CharaterState(uint32,uint32,uint32,uint32){return true;}
};
OnlineMgr* sOnlineMgr=nullptr;
struct PlayerCharacterSetup;
struct Player {
    PlayerCharacterSetup* m_CharacterSetup=nullptr;
    WorldSession session;
    uint32 spec=100,level=100,xp=123,saved=0,resets=0,levelChanges=0;
    uint32 talentsSent=0,stats=0,skills=0,health=0,activations=0;
    uint8 cls=11;
    bool combat=false,refuseActivation=false;
    std::vector<uint32> items{6948,12345,67890};
    uint32 GetSpecializationId()const{return spec;}
    uint8 getClass()const{return cls;}
    uint32 getLevel()const{return level;}
    uint32 GetGUID()const{return 42;}
    WorldSession* GetSession(){return &session;}
    bool IsInCombat()const{return combat;}
    void CombatStop(bool){combat=false;}
    void GiveLevel(uint32 value){++levelChanges;level=value;SaveToDB();}
    void SetUInt32Value(uint32,uint32 value){xp=value;}
    void ActivateTalentGroup(ChrSpecializationEntry const* value){
        ++activations;if(!refuseActivation)spec=value->ID;
    }
    void ResetTalents(bool){++resets;SaveToDB();}
    void SendTalentsInfoData(){++talentsSent;}
    void SetFullHealth(){++health;}
    void UpdateSkillsForLevel(){++skills;}
    void UpdateAllStats(){++stats;}
    void SaveToDB(bool=false);
    void CompleteCharacterSetup();
};
struct PlayerCharacterSetup {
    Player* m_Player;
    bool m_Finish=true,m_TenacitySetting=false,inventoryFailure=false;
    uint32 m_ResetStep=0,m_ActiveTalentType=255,m_TargetLevel=0,m_SetupFailures=0;
    std::vector<std::string> steps;
    bool HasPendingReset()const{return !m_Finish;}
    bool ResetPlayerToLevel(uint32,uint32,bool=false);
    bool ChangeSpecialization(uint32);
    void ActivateSpecialization();
    void UpdateReset();
    static uint32 FindPlayerTalentType(Player* p){
        auto s=sChrSpecializationStore.LookupEntry(p->spec);return s?s->OrderIndex:255;
    }
    static void ClearUnknowMount(Player*){}
    void LearnTalents(){steps.push_back("talents");}
    void RemoveSpells(){steps.push_back("remove");}
    void LearnCommonSpells(){steps.push_back("common");}
    void LearnSpells(){steps.push_back("spells");}
    void CheckInventroy(){steps.push_back("bags");if(inventoryFailure)++m_SetupFailures;}
    void AddEquipFromAll(){steps.push_back("generate");}
    void UpequipFromAll(){steps.push_back("equip");}
    void SupplementOtherItems(){steps.push_back("supplement");}
};
'''
    harness += 'void Player::SaveToDB(bool)\n{\n'+guard+'\n    ++saved;\n}\n'
    harness += body(player, 'Player::CompleteCharacterSetup')+'\n'
    for name in ('SerializerPlayerAccount', 'SetCharacterOperation', 'SerializerCharacterOperation'):
        harness += body(online, 'OnlineMgr::'+name)+'\n'
    for name in ('ResetPlayerToLevel', 'ActivateSpecialization', 'ChangeSpecialization', 'UpdateReset'):
        harness += body(setup, 'PlayerCharacterSetup::'+name)+'\n'
    harness += r'''
Json::Value parse(std::string const& value){
    Json::Value result;Json::Reader reader;check(reader.parse(value,result),"bad response JSON");return result;
}
std::string state(){return parse(sOnlineMgr->SerializerCharacterOperation(1))["operation"]["state"].asString();}
int main(){
    OnlineMgr manager;sOnlineMgr=&manager; // Match the production singleton constructed after JsonCpp initialization.
    for(int8 order=0;order<4;++order)sChrSpecializationStore.entries[100+order]={11,order,uint32(100+order)};
    sChrSpecializationStore.entries[200]={12,0,200};
    sOnlineMgr->m_OnlinePlayerAcc[1].id=1;sOnlineMgr->m_OnlinePlayerAcc[1].online.guid=42;
    Player p;PlayerCharacterSetup s{&p};p.m_CharacterSetup=&s;
    auto original=p.items;
    for(uint32 order=0;order<4;++order){
        check(s.ChangeSpecialization(order),"ordinary specialization rejected");
        check(p.spec==100+order,"wrong ordinary specialization");
        check(p.items==original && p.resets==0 && p.levelChanges==0 && s.steps.empty(),"ordinary change prepared character");
    }
    check(s.ChangeSpecialization(255),"KEEP rejected");
    auto saves=p.saved;
    for(uint32 bad:{4u,254u,256u,0xffffffffu})check(!s.ChangeSpecialization(bad),"invalid specialization accepted");
    p.cls=12;check(!s.ChangeSpecialization(3),"nonexistent class specialization accepted");p.cls=11;
    p.refuseActivation=true;check(!s.ChangeSpecialization(0),"native activation failure hidden");p.refuseActivation=false;
    check(p.saved==saves && p.items==original,"failed activation saved/changed inventory");
    check(s.ResetPlayerToLevel(110,2),"preparation rejected");
    check(p.level==100 && p.xp==123 && p.items==original,"acceptance changed player");
    check(sOnlineMgr->SetCharacterOperation(1,42,"preparation","queued",0),"queue metadata missing");
    auto id=parse(sOnlineMgr->SerializerCharacterOperation(1))["operation"]["id"].asUInt();
    check(state()=="queued","queued state");
    check(!s.ChangeSpecialization(1) && !s.ResetPlayerToLevel(20,1),"busy preparation overwritten");
    p.SaveToDB();check(p.saved==saves,"pending character persisted");
    p.combat=true;p.CompleteCharacterSetup(); // Same completion entry called before logout save.
    check(s.m_Finish && s.m_ResetStep==14 && p.saved==saves+1,"preparation not completed/saved in one call");
    check(p.level==110 && p.spec==102 && p.xp==0 && !p.combat,"preparation state");
    check(p.resets==1 && p.items==original && s.steps.size()==8,"preparation lost items/skipped steps");
    check(state()=="completed" && parse(sOnlineMgr->SerializerCharacterOperation(1))["operation"]["id"].asUInt()==id,"completion status/identity");
    p.CompleteCharacterSetup();check(p.saved==saves+1,"completion ran twice");
    p.SaveToDB();check(p.saved==saves+2,"ordinary saves remain blocked");
    check(s.ResetPlayerToLevel(110,255),"repeat preparation rejected");
    s.inventoryFailure=true;sOnlineMgr->SetCharacterOperation(1,42,"preparation","queued",0);s.UpdateReset();
    check(state()=="completed_with_warnings","inventory warning lost");
    check(parse(sOnlineMgr->SerializerCharacterOperation(1))["operation"]["item_failures"].asUInt()==1,"warning count");
    check(p.items==original && p.xp==0,"repeat preparation erased inventory");
    check(!sOnlineMgr->SetCharacterOperation(1,43,"preparation","completed",0),"another character operation overwritten");
    check(!sOnlineMgr->SetCharacterOperation(999,42,"preparation","queued",0),"unknown account accepted");
    check(parse(sOnlineMgr->SerializerCharacterOperation(999))["result"].asString()=="error","unknown status");
    sOnlineMgr->m_OnlinePlayerAcc[1].online.guid=0;
    check(state()=="completed_with_warnings","logout lost last outcome");

    OnlineMgr pages;
    for(uint32 i=1;i<=251;++i){auto& acc=pages.m_OnlinePlayerAcc[i*3];acc.id=i*3;acc.username="account";}
    uint32 cursor=0,seen=0;
    do{
        auto wire=pages.SerializerPlayerAccount(cursor,100);auto page=parse(wire);
        check(wire.size()<65535 && page["total"].asUInt()==251,"page frame/total");
        auto const& rows=page["accounts"];check(rows.size()<=100,"page limit");
        for(auto const& row:rows){check(row["id"].asUInt()>cursor,"duplicate/out-of-order account");cursor=row["id"].asUInt();++seen;}
        check(cursor==page["next_after"].asUInt(),"next cursor");
        if(!page["has_more"].asBool())break;
    }while(true);
    check(seen==251,"accounts missing after first page");
    auto empty=parse(pages.SerializerPlayerAccount(cursor));check(empty["accounts"].size()==0 && !empty["has_more"].asBool(),"empty final page");
    check(parse(pages.SerializerPlayerAccount())["accounts"].size()==99,"legacy page size changed");
    pages.m_OnlinePlayerAcc[3].username=std::string(40000,'x');
    pages.m_OnlinePlayerAcc[6].username=std::string(40000,'y');
    auto bounded=parse(pages.SerializerPlayerAccount());check(bounded["accounts"].size()==1 && bounded["next_after"].asUInt()==3 && bounded["has_more"].asBool(),"byte limit skips row");
    auto resumed=parse(pages.SerializerPlayerAccount(3));check(resumed["accounts"][Json::UInt(0)]["id"].asUInt()==6,"byte-limited continuation skips row");
    pages.m_OnlinePlayerAcc[3].username=std::string(70000,'z');
    auto oversized=parse(pages.SerializerPlayerAccount());check(oversized["result"].asString()=="error" && oversized["error"].asString()=="account_too_large","oversized account hidden");
    std::cout<<"PASS: ordinary specialization, deferred preparation, save/logout guard, item preservation, warnings, status identity, bounded pagination\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);cpp=tmp/'operations.cpp';exe=tmp/'operations'
        (tmp/'Define.h').write_text('#pragma once\n#include <cstdint>\n',encoding='utf8')
        cpp.write_text(harness,encoding='utf8')
        json=root/'src/server/game/Server/Json'
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-fsanitize=address,undefined','-fno-sanitize-recover=undefined',
            '-fno-omit-frame-pointer','-g','-I'+str(tmp),'-I'+str(json),str(cpp),
            *[str(json/f) for f in ('json_reader.cpp','json_value.cpp','json_writer.cpp')],'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
