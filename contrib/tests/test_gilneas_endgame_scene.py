#!/usr/bin/env python3
"""Execute native Lorna spawn cases with controlled transport creation failures."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path
from test_gilneas_quests import method


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    source = (Path(__file__).resolve().parents[2] / 'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
    lorna = source[source.index('    struct npc_lorna_crowley_43566AI'):]
    code = r'''
#include <map>
#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>
enum {EVENT_TALK_PART_09=9,EVENT_SPAWN_OBJECT=10,EVENT_MOVE_PART2=11};
enum class HighGuid{GameObject,Creature};
struct ObjectGuid{using LowType=int;int id=0;static const ObjectGuid Empty;};
const ObjectGuid ObjectGuid::Empty{};
struct Data{int id=0;float posX=0,posY=0,posZ=0,orientation=0;};
using GameObjectData=Data;using CreatureData=Data;
struct Map{int next=1;template<HighGuid>int GenerateLowGuid(){return next++;}};
struct GameObject{float scale=0;void SetObjectScale(float s){scale=s;}};
struct Creature;
struct Transport{
 int failGO=-1,goAttempts=0,npcAttempts=0;bool failNPC=false;
 GameObject objects[3];std::vector<Data>positions;
 GameObject*CreateGOPassenger(int,Data*d){positions.push_back(*d);int i=goAttempts++;return i==failGO?nullptr:&objects[i];}
 Creature*CreateNPCPassenger(int,Data*d);
};
struct Motion{int paths=0;void MovePath(int id,bool){if(id!=4356607)throw std::runtime_error("wrong route");++paths;}};
struct Creature{Transport*transport;Map map;Motion motion;ObjectGuid GetGUID(){return {123};}Transport*GetTransport(){return transport;}Map*GetMap(){return &map;}Motion*GetMotionMaster(){return &motion;}};
Creature*Transport::CreateNPCPassenger(int,Data*d){++npcAttempts;if(d->id!=43567)throw std::runtime_error("wrong orc");static Creature npc{nullptr,{}, {}};return failNPC?nullptr:&npc;}
struct ObjectMgr{std::map<int,Data>data;int goAdds=0,npcAdds=0;Data&NewGOData(int g){return data[g];}Data&NewOrExistCreatureData(int g){return data[g];}void AddGameobjectToGrid(int,Data*){++goAdds;}void AddCreatureToGrid(int,Data*){++npcAdds;}}mgr;
auto*sObjectMgr=&mgr;
int errors=0;
#define TC_LOG_ERROR(...) (++errors)
struct Events{std::vector<int>ids;void ScheduleEvent(int id,int){ids.push_back(id);}};
void check(bool v,char const*m){if(!v)throw std::runtime_error(m);}
struct Scene{Creature*me;ObjectGuid m_bigOrcGUID{999};int m_wp_point=0,talks=0;Events m_events;void Talk(int id){if(id!=5)throw std::runtime_error("wrong talk");++talks;}void Run(int eventId){switch(eventId){
'''
    code += method(lorna, '                case EVENT_TALK_PART_09:')
    code += method(lorna, '                case EVENT_SPAWN_OBJECT:')
    code += r'''
}}};
int main(){
 for(int failure=-1;failure<3;++failure){mgr=ObjectMgr{};errors=0;Transport t;t.failGO=failure;Creature c{&t,{}, {}};Scene s{&c,{999},0,0,{}};s.Run(EVENT_TALK_PART_09);
 check(t.goAttempts==3&&mgr.goAdds==(failure<0?3:2)&&errors==(failure<0?0:1),"failed barrel skips dereference/grid registration but other barrels still spawn");
 check(s.talks==1&&s.m_wp_point==7&&c.motion.paths==1&&s.m_events.ids==std::vector<int>{EVENT_SPAWN_OBJECT},"original scene progression retained");
 check(t.positions.size()==3&&t.positions[0].posX==53.6417f&&t.positions[1].posY==-2.18513f&&t.positions[2].posY==2.12947f,"native transport offsets unchanged");
 for(int i=0;i<3;++i)check(t.objects[i].scale==(i==failure?0.0f:2.0f),"scale only applied to created objects");
 }
 for(bool failure:{false,true}){mgr=ObjectMgr{};errors=0;Transport t;t.failNPC=failure;Creature c{&t,{}, {}};Scene s{&c,{999},0,0,{}};s.Run(EVENT_SPAWN_OBJECT);
 check(t.npcAttempts==1&&mgr.npcAdds==(failure?0:1)&&errors==(failure?1:0),"orc registration only after successful creation");
 check(s.m_bigOrcGUID.id==(failure?0:123),"failure clears stale orc GUID");
 check(s.m_events.ids==(failure?std::vector<int>{}:std::vector<int>{EVENT_MOVE_PART2}),"failed creation cannot queue nonexistent orc movement");
 }
 std::cout<<"PASS: native Endgame three barrel and orc creation cases, success and every null failure\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp = Path(tmp) / 'test.cpp'
        exe = Path(tmp) / 'test.exe'
        cpp.write_text(code, 'utf8')
        flags = [] if args.no_sanitizers else ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++17', '-Wall', '-Wextra', '-Werror', *flags, str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
