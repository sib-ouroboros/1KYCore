#!/usr/bin/env python3
"""Test actual Player::KillCreditGO for both restored False Orders entries."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root/'src/server/game/Entities/Player/Player.cpp').read_text('latin1')
    start = source.index('void Player::KillCreditGO(')
    opening = source.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    function = source[start:end]
    header = r'''
#include <cstdint>
#include <map>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t; using uint16=std::uint16_t; using uint32=std::uint32_t;
constexpr uint8 MAX_QUEST_LOG_SIZE=2;
constexpr uint32 QUEST_STATUS_INCOMPLETE=1, QUEST_OBJECTIVE_GAMEOBJECT=2, QUEST_SPECIAL_FLAGS_CAST=4;
struct ObjectGuid {};
struct QuestObjective { uint32 Type, ObjectID, Amount, StorageIndex, QuestID; };
struct Quest { uint32 Id; bool cast=true; std::vector<QuestObjective> objectives;
 bool HasSpecialFlag(uint32)const{return cast;} std::vector<QuestObjective> const& GetObjectives()const{return objectives;} };
struct QuestStatusData {uint32 Status=QUEST_STATUS_INCOMPLETE;};
struct ObjectMgr {std::map<uint32,Quest> quests; Quest const* GetQuestTemplate(uint32 id){auto i=quests.find(id);return i==quests.end()?nullptr:&i->second;}} manager;
ObjectMgr* sObjectMgr=&manager;
struct Player {
 std::map<uint32,QuestStatusData> m_QuestStatus; std::map<std::pair<uint32,uint32>,uint32> progress; uint32 slots[2]={45835,46324};uint32 credits=0,completed=0;
 uint32 GetQuestSlotQuestId(uint8 i){return slots[i];}
 uint32 GetQuestObjectiveData(Quest const* q,uint32 idx){return progress[{q->Id,idx}];}
 void SetQuestObjectiveData(QuestObjective const& obj,uint32 n){progress[{obj.QuestID,obj.StorageIndex}]=n;}
 void SendQuestUpdateAddCredit(Quest const*,ObjectGuid,QuestObjective const&,uint32){++credits;}
 bool CanCompleteQuest(uint32 id){for(auto const& o:manager.quests.at(id).objectives)if(progress[{id,o.StorageIndex}]<o.Amount)return false;return true;}
 void CompleteQuest(uint32 id){m_QuestStatus[id].Status=2;++completed;}
 void KillCreditGO(uint32 entry,ObjectGuid guid);
};
void check(bool ok,char const* message){if(!ok)throw std::runtime_error(message);}
'''
    harness = r'''
int main(){try {
 manager.quests.emplace(45835,Quest{45835,true,{{2,267492,1,0,45835},{2,268458,1,1,45835}}});
 manager.quests.emplace(46324,Quest{46324,true,{{2,267492,1,0,46324},{2,268458,1,1,46324}}});
 Player p;p.m_QuestStatus[45835]={};p.m_QuestStatus[46324]={};
 p.KillCreditGO(999999,{});check(p.credits==0,"unrelated entry");
 p.KillCreditGO(267492,{});check(p.credits==2 && p.completed==0,"first orders credit both active quests");
 p.KillCreditGO(267492,{});check(p.credits==2,"repeat is capped");
 p.KillCreditGO(268458,{});check(p.credits==4 && p.completed==2,"second orders complete both quests");
 p.KillCreditGO(268458,{});check(p.credits==4,"completed quest is unchanged");
 manager.quests.emplace(45629,Quest{45629,true,{{2,267180,4,2,45629}}});
 Player bombs;bombs.slots[0]=45629;bombs.slots[1]=0;bombs.m_QuestStatus[45629]={};
 for(uint32 n=1;n<=4;++n){bombs.KillCreditGO(267180,{});check(bombs.credits==n && bombs.progress[std::make_pair(45629U,2U)]==n,"four credits for Fel FireBomb objective");check(bombs.completed==(n==4?1U:0U),"bomb quest completes only at four");}
 bombs.KillCreditGO(267180,{});check(bombs.credits==4 && bombs.completed==1,"bomb repeat after completion capped");
 Player inactive;inactive.m_QuestStatus[45835].Status=0;inactive.m_QuestStatus[46324].Status=0;inactive.KillCreditGO(267492,{});check(inactive.credits==0,"no active quest");
 Player empty;empty.slots[0]=empty.slots[1]=0;empty.KillCreditGO(267492,{});check(empty.credits==0,"empty quest log");
 Player missing;missing.slots[0]=missing.slots[1]=999999;missing.KillCreditGO(267492,{});check(missing.credits==0,"missing quest template");
 std::cout<<"PASS: actual KillCreditGO, both False Orders entries, simultaneous quests, four Fel FireBomb uses, completion, repeats and inactive quests\n";
 }catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''
    with tempfile.TemporaryDirectory() as directory:
        cpp=Path(directory)/'credit.cpp';exe=Path(directory)/'credit.exe'
        cpp.write_text(header+'\n'+function+'\n'+harness,encoding='utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
