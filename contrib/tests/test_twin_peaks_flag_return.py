#!/usr/bin/env python3
"""Compile real Twin Peaks dropped-flag handling and preserve the opposing flag."""
import os
from pathlib import Path
import subprocess
import tempfile

def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Battlegrounds/Zones/BattlegroundTP.cpp').read_text('latin1')
    start=source.index('void BattlegroundTP::RespawnFlagAfterDrop(uint32 team)')
    end=source.index('\nvoid BattlegroundTP::EventPlayerCapturedFlag',start)
    body=source[start:end]
    harness=r"""
#include <cstdint>
#include <array>
#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
constexpr uint32 ALLIANCE=469,HORDE=67,STATUS_IN_PROGRESS=3;
constexpr uint32 BG_TP_OBJECT_A_FLAG=10,BG_TP_OBJECT_H_FLAG=11,RESPAWN_IMMEDIATELY=0;
constexpr uint32 BG_TP_TEXT_FLAGS_PLACED=1,CHAT_MSG_BG_SYSTEM_NEUTRAL=2,BG_TP_SOUND_FLAGS_RESPAWNED=3;
struct ObjectGuid {
    uint32 value;
    static ObjectGuid const Empty;
    std::string ToString()const{return std::to_string(value);}
};
ObjectGuid const ObjectGuid::Empty{0};
struct GameObject {bool deleted=false;void Delete(){deleted=true;}};
struct Map {
    std::array<GameObject,2> ground;
    bool missing=false;
    GameObject* GetGameObject(ObjectGuid guid){return missing?nullptr:&ground.at(guid.value-1);}
};
#define TC_LOG_ERROR(...) (++errors)
struct BattlegroundTP {
    uint32 status=STATUS_IN_PROGRESS;
    std::array<uint32,2> flagState{{2,2}};
    std::array<ObjectGuid,2> dropped{{{1},{2}}};
    bool _bothFlagsKept=true;
    Map map;
    std::vector<uint32> spawned;
    uint32 texts=0,sounds=0,errors=0,respawns=0;
    uint32 GetStatus()const{return status;}
    uint32 GetTeamIndexByTeamId(uint32 team)const{return team==ALLIANCE?0:1;}
    void RespawnFlag(uint32 team,bool captured){if(captured)throw std::runtime_error("capture changed");++respawns;flagState[GetTeamIndexByTeamId(team)]=0;}
    void SpawnBGObject(uint32 object,uint32 delay){if(delay!=0)throw std::runtime_error("delay changed");spawned.push_back(object);}
    void SendBroadcastText(uint32,uint32){++texts;}
    void PlaySoundToAll(uint32){++sounds;}
    Map* GetBgMap(){return &map;}
    ObjectGuid GetDroppedFlagGUID(uint32 team)const{return dropped[GetTeamIndexByTeamId(team)];}
    void SetDroppedFlagGUID(ObjectGuid guid,uint32 index){dropped[index]=guid;}
    void RespawnFlagAfterDrop(uint32 team);
};
BODY
void check(bool value){if(!value)throw std::runtime_error("Twin Peaks dropped flag regression");}
int main(){
    for(uint32 team:{ALLIANCE,HORDE})for(uint32 oppositeState:{0u,1u,2u})for(bool missing:{false,true}){
        BattlegroundTP bg;uint32 own=bg.GetTeamIndexByTeamId(team),other=1-own;
        bg.flagState[other]=oppositeState;bg.map.missing=missing;
        bg.RespawnFlagAfterDrop(team);
        check(bg.spawned==std::vector<uint32>{team==ALLIANCE?BG_TP_OBJECT_A_FLAG:BG_TP_OBJECT_H_FLAG});
        check(bg.flagState[own]==0&&bg.flagState[other]==oppositeState);
        check(bg.dropped[own].value==0&&bg.dropped[other].value==other+1);
        check(!bg.map.ground[other].deleted&&bg.map.ground[own].deleted==!missing);
        check(bg.respawns==1&&bg.texts==1&&bg.sounds==1&&bg.errors==static_cast<uint32>(missing));
        check(!bg._bothFlagsKept);
    }
    for(uint32 team:{ALLIANCE,HORDE})for(uint32 status:{0u,1u,2u,4u}){
        BattlegroundTP bg;bg.status=status;bg.RespawnFlagAfterDrop(team);
        check(bg.spawned.empty()&&bg.respawns==0&&bg.texts==0&&bg.sounds==0&&bg.errors==0);
        check(bg.flagState[0]==2&&bg.flagState[1]==2&&bg.dropped[0].value==1&&bg.dropped[1].value==2);
        check(!bg.map.ground[0].deleted&&!bg.map.ground[1].deleted&&bg._bothFlagsKept);
    }
    std::cout<<"PASS: actual Twin Peaks flag return, both teams, opposing flag state, dropped GUID deletion, missing object and inactive match\n";
}
""".replace('BODY',body)
    with tempfile.TemporaryDirectory() as tmp:
        cpp,exe=Path(tmp)/'flags.cpp',Path(tmp)/'flags'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-sanitize-recover=all','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)

if __name__=='__main__':
    main()
