#!/usr/bin/env python3
"""Compile actual survivor conversation credit and per-NPC claim handlers."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
 source=(Path(__file__).resolve().parents[2]/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
 start=source.index('class npc_crash_survivor_37067');scene=source[start:]
 code=r"""
#include <cstdint>
#include <set>
#include <vector>
#include <cassert>
#include <iostream>
using int32=std::int32_t;using ObjectGuid=int;
constexpr int QUEST_STATUS_INCOMPLETE=3,QUEST_OBJECTIVE_MONSTER=0;
struct QuestObjective{int Type=0,ObjectID=37067,Amount=5,StorageIndex=0;};
struct Quest{std::vector<QuestObjective> goals{{}};auto const&GetObjectives()const{return goals;}};
struct ObjectMgr{Quest quest;Quest const*GetQuestTemplate(int id){assert(id==24468);return &quest;}} objects;auto*sObjectMgr=&objects;
struct NPCBase{virtual~NPCBase()=default;};
struct npc_crash_survivor_37067AI:NPCBase{std::set<ObjectGuid>m_rescuedPlayers;
"""+method(scene,'        bool ClaimRescue(')+method(scene,'        void SetGUID(').replace(' override','')+'};\n'
 code+=r"""
struct Creature;
struct Player{int guid=1,status=3,data=0,complete=0,updates=0;bool alive=true;float distance=1;
 bool IsAlive(){return alive;}float GetDistance(Creature*){return distance;}int GetQuestStatus(int){return status;}
 ObjectGuid GetGUID(){return guid;}int GetQuestObjectiveData(Quest const*,int){return data;}
 void SetQuestObjectiveData(QuestObjective const&,int n){data=n;}
 void SendQuestUpdateAddCredit(Quest const*,ObjectGuid,QuestObjective const&,int n){assert(n==data);++updates;}
 bool CanCompleteQuest(int){return data==5;}void CompleteQuest(int){status=1;++complete;}
};
struct Creature{int guid=101,map=654;bool alive=true,phase=true;npc_crash_survivor_37067AI ai;
 bool IsAlive(){return alive;}int GetMapId(){return map;}bool IsInPhase(Player*){return phase;}ObjectGuid GetGUID(){return guid;}NPCBase*AI(){return &ai;}};
#define CAST_AI(type,value) dynamic_cast<type*>(value)
struct Gossip{
"""+method(scene,'    bool OnGossipHello(').replace(' override','')+'};\n'
 code+=r"""
int main(){
 Gossip g;Player p,other;other.guid=2;Creature survivors[5];
 for(int i=0;i<5;++i)survivors[i].guid+=i;
 survivors[0].map=1;g.OnGossipHello(&p,&survivors[0]);assert(!p.data);survivors[0].map=654;
 survivors[0].phase=false;g.OnGossipHello(&p,&survivors[0]);assert(!p.data);survivors[0].phase=true;
 p.distance=10;g.OnGossipHello(&p,&survivors[0]);assert(!p.data);p.distance=1;
 objects.quest.goals[0].ObjectID=37078;g.OnGossipHello(&p,&survivors[0]);assert(!p.data);objects.quest.goals[0].ObjectID=37067;
 for(int i=0;i<5;++i){g.OnGossipHello(&p,&survivors[i]);assert(p.data==i+1&&p.updates==i+1);g.OnGossipHello(&p,&survivors[i]);assert(p.data==i+1&&p.updates==i+1);if(i<4)assert(!p.complete);}
 assert(p.complete==1);g.OnGossipHello(&p,&survivors[0]);assert(p.complete==1&&p.updates==5);
 g.OnGossipHello(&other,&survivors[0]);assert(other.data==1&&!other.complete);
 p.data=0;p.status=3;for(auto&npc:survivors)npc.ai.SetGUID(p.guid,24468);
 g.OnGossipHello(&p,&survivors[0]);assert(p.data==1);
 std::cout<<"PASS: five distinct conversations, +1 each, duplicate blocked, other players independent, retry claim reset and gates\n";
}
"""
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'];subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
