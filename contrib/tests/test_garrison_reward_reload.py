#!/usr/bin/env python3
"""Actual reward loader/getter and trainer gossip gate with strict sanitizers."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Globals/ObjectMgr.cpp').read_text('utf8')
    header=(root/'src/server/game/Globals/ObjectMgr.h').read_text('utf8')
    def function(name):
        return re.search(r'^[^\n]+ ObjectMgr::'+name+r'\([^\n]*\)\n\{.*?^\}',source,re.M|re.S)[0]
    reward=re.search(r'struct GarrssionMissionReward\n\{.*?\n\};',header,re.S)[0]
    pet=(root/'src/server/scripts/World/PetBattleTrainer.cpp').read_text('utf8')
    begin=pet.index('    bool OnGossipSelect(');opening=pet.index('{',begin);depth=1;end=opening+1
    while depth:
        depth+=(pet[end]=='{')-(pet[end]=='}');end+=1
    method=pet[begin:end]
    # Test the actual eligibility gate and return paths. Battle construction stays
    # in the real script and is verified by the full build, not simulated here.
    prefix=method[:method.index('            if (uiAction == 0)')]
    tail=method[method.rindex('            return true;'):]
    gate=(prefix+'            ++handled;\n'+tail).replace(' override','').replace('uint32 uiAction','uint32 /*uiAction*/')
    harness=r'''
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
using uint32=std::uint32_t;
template<typename... Args> void discardLog(Args const&...){}
#define TC_LOG_INFO(...) discardLog(__VA_ARGS__)
uint32 getMSTime(){return 0;}
uint32 GetMSTimeDiffToNow(uint32){return 0;}
void check(bool ok,char const* msg){if(!ok)throw std::runtime_error(msg);}
struct Field{uint32 value;uint32 GetUInt32()const{return value;}};
struct Result{
    std::vector<std::array<Field,4>> rows;std::size_t position=0;
    Field* Fetch(){return rows[position].data();}
    bool NextRow(){return ++position<rows.size();}
};
using QueryResult=std::shared_ptr<Result>;
struct Database{
    std::vector<std::array<Field,4>> rows;
    QueryResult Query(char const*){return rows.empty()?nullptr:std::make_shared<Result>(Result{rows});}
} WorldDatabase;
REWARD
struct ObjectMgr{
    std::vector<GarrssionMissionReward> GarrssionMissionRewardMap;
    void LoadGarrssionMissionReward();
    std::vector<GarrssionMissionReward> GetGarrssionMissionReward(uint32);
};
struct Menu{unsigned clears=0;void ClearMenus(){++clears;}};
struct Player{bool eligible=false;Menu menu;Menu* PlayerTalkClass=&menu;
    bool QuestObjectiveActiveInPlayerByObject(uint32)const{return eligible;}
};
struct Creature{uint32 GetEntry()const{return 123;}};
struct Trainer{unsigned handled=0;
GATE
};
METHODS
int main(){
    ObjectMgr mgr;mgr.GarrssionMissionRewardMap.push_back({999,9,9,9});
    WorldDatabase.rows={{{{10},{1},{100},{2}}},{{{10},{2},{200},{3}}},{{{11},{3},{300},{4}}}};
    for(unsigned i=0;i<100;++i){
        mgr.LoadGarrssionMissionReward();check(mgr.GarrssionMissionRewardMap.size()==3,"reload appends stale rewards");
        auto rewards=mgr.GetGarrssionMissionReward(10);
        check(rewards.size()==2 && rewards[0].MissionId==10 && rewards[0].RewardId==100 && rewards[1].RewardCount==3,"reward fields/order changed");
        rewards[0].RewardCount=999;
        check(mgr.GetGarrssionMissionReward(10)[0].RewardCount==2,"getter leaks mutable state");
    }
    WorldDatabase.rows={{{{12},{4},{400},{5}}}};mgr.LoadGarrssionMissionReward();
    check(mgr.GetGarrssionMissionReward(10).empty() && mgr.GetGarrssionMissionReward(12).size()==1,"deleted reward retained");
    WorldDatabase.rows.clear();mgr.LoadGarrssionMissionReward();check(mgr.GarrssionMissionRewardMap.empty(),"empty reload retains rewards");
    Trainer trainer;Player player;Creature creature;
    check(!trainer.OnGossipSelect(&player,&creature,0,0),"ineligible gossip treated as handled");
    check(player.menu.clears==0 && trainer.handled==0,"fallback menu destroyed");
    player.eligible=true;check(trainer.OnGossipSelect(&player,&creature,0,0),"eligible gate rejected");
    check(player.menu.clears==1 && trainer.handled==1,"eligible menu not handled");
    player.eligible=false;check(!trainer.OnGossipSelect(&player,&creature,0,0),"eligibility carried between interactions");
    check(player.menu.clears==1,"second fallback clears menu");
    std::cout<<"PASS: reward reload replaces values without invalid free/leak, getter independence, trainer fallback gate\n";
}
'''
    harness=harness.replace('REWARD',reward).replace('GATE',gate).replace('METHODS',function('LoadGarrssionMissionReward')+'\n'+function('GetGarrssionMissionReward'))
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'reward.cpp';exe=Path(tmp)/'reward';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
