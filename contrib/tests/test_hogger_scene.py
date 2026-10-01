#!/usr/bin/env python3
"""Exercise production Hogger ragamuffin events against real position data."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/scripts/EasternKingdoms/Zones/zone_eastern_kingdoms_elwynn_forest.cpp').read_text('utf8')
    start=source.index('static const Position RagamuffinCoordinates[')
    coordinates=source[start:source.index('};', start)+2]
    start=source.index('                case EVENT_RAGAMUFFIN_SAY_CLAY:')
    events=source[start:source.index('                case EVENT_DISMOUNT_HAMMOND_CLAY:', start)]
    constants='\n'.join('constexpr int '+name+'='+re.search(r'\b'+name+r'\s*=\s*(\d+)',source)[1]+';' for name in
        ('EVENT_RAGAMUFFIN_SAY_CLAY','EVENT_RAGAMUFFIN_SAY_WOW','EVENT_RUN_1','EVENT_RUN_2','SAY_CLAY','SAY_WOW'))
    harness=r'''
#include <chrono>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <vector>
using namespace std::chrono_literals;
struct Position { float x,y,z; };
COORDINATES
CONSTANTS
void check(bool ok){if(!ok)throw std::runtime_error("Hogger scene regression");}
struct MotionMaster {
    unsigned moves=0;Position destination{};
    void MovePoint(unsigned id,Position const& p,bool path){check(id==0&&path);++moves;destination=p;}
};
struct Creature {
    unsigned talks=0,turns=0,walks=0;int text=-1;bool walk=true;float facing=0;MotionMaster motion;
    Creature* AI(){return this;}
    void Talk(int id){++talks;text=id;}
    float GetAngle(Creature*){return 1.25f;}
    void SetFacingTo(float value){++turns;facing=value;}
    void SetWalk(bool value){++walks;walk=value;}
    MotionMaster* GetMotionMaster(){return &motion;}
};
struct EventMap {
    std::vector<std::pair<int,long long>> scheduled;
    void ScheduleEvent(int id,std::chrono::seconds delay){scheduled.emplace_back(id,delay.count());}
};
struct Handler {
    Creature actor;Creature* me=&actor;Creature* first=nullptr;Creature* second=nullptr;EventMap _events;
    Creature* GetRagamuffin1(){return first;}
    Creature* GetRagamuffin2(){return second;}
    void Execute(int id){switch(id){
EVENTS
    }}
};
bool equal(Position const& p,Position const& q){return p.x==q.x&&p.y==q.y&&p.z==q.z;}
int main(){
    static_assert(sizeof(RagamuffinCoordinates)/sizeof(Position)==6,"six source positions");
    for(unsigned presence=0;presence<4;++presence){
        Creature first,second;Handler h;
        h.first=(presence&1)?&first:nullptr;h.second=(presence&2)?&second:nullptr;
        h.Execute(EVENT_RAGAMUFFIN_SAY_CLAY);h.Execute(EVENT_RUN_1);
        h.Execute(EVENT_RAGAMUFFIN_SAY_WOW);h.Execute(EVENT_RUN_2);
        check(h._events.scheduled.size()==2);
        check(h._events.scheduled[0]==std::make_pair(EVENT_RUN_1,5LL));
        check(h._events.scheduled[1]==std::make_pair(EVENT_RUN_2,4LL));
        check(first.talks==((presence&1)?1u:0u)&&second.talks==((presence&2)?1u:0u));
        if(presence&1){check(first.text==SAY_WOW&&first.turns==1&&first.facing==1.25f);check(!first.walk&&first.walks==1&&first.motion.moves==1);check(equal(first.motion.destination,RagamuffinCoordinates[4]));}
        if(presence&2){check(second.text==SAY_CLAY&&second.turns==1&&second.facing==1.25f);check(!second.walk&&second.walks==1&&second.motion.moves==1);check(equal(second.motion.destination,RagamuffinCoordinates[5]));}
    }
    // Actors can despawn between speech and a delayed escape event.
    Creature first,second;Handler h;h.first=&first;h.second=&second;
    h.Execute(EVENT_RAGAMUFFIN_SAY_CLAY);h.Execute(EVENT_RAGAMUFFIN_SAY_WOW);
    h.first=nullptr;h.second=nullptr;h.Execute(EVENT_RUN_1);h.Execute(EVENT_RUN_2);
    check(first.motion.moves==0&&second.motion.moves==0&&h._events.scheduled.size()==2);
    std::cout<<"PASS: actual Hogger scene events / coordinates, both escape endpoints in bounds, each missing actor, despawn between events, dialogue and timers preserved\n";
}
'''.replace('COORDINATES',coordinates).replace('CONSTANTS',constants).replace('EVENTS\n',events+'\n')
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'hogger.cpp';exe=Path(tmp)/'hogger';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all',
            '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':
    main()
