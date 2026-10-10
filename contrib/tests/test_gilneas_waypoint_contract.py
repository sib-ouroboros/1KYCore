#!/usr/bin/env python3
"""Real waypoint callback dispatch plus native Manor and captured bat endpoints."""
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    movement=(root/'src/server/game/Movement/MovementGenerators/WaypointMovementGenerator.cpp').read_text('utf8')
    dusk=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_duskhaven.cpp').read_text('utf8')
    city=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city3.cpp').read_text('utf8')
    route_counts={}
    for sql in ['2026_10_06_09_world_gilneas_manor_ride.sql','2026_10_06_12_world_gilneas_bat_flight.sql']:
        text=(root/'sql/updates/world'/sql).read_text('utf8')
        for route in [3674101,3854001,3854003]:
            points=[int(p) for p in re.findall(r'\('+str(route)+r',(\d+),',text)]
            if points:
                assert points==list(range(1,len(points)+1)),(route,points)
                route_counts[route]=len(points)
    code=r'''
#include <cstdint>
#include <chrono>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using namespace std::chrono_literals;
enum{WAYPOINT_MOTION_TYPE=2};
struct NativeAI{virtual~NativeAI()=default;virtual void MovementInform(uint32,uint32)=0;};
struct Vehicle{int removals=0;void RemoveAllPassengers(){++removals;}};
struct Creature{NativeAI*ai=nullptr;Vehicle vehicle;int despawns=0;bool gravity=true;NativeAI*AI(){return ai;}Vehicle*GetVehicleKit(){return &vehicle;}void SetDisableGravity(bool b){gravity=b;}template<class T>void DespawnOrUnsummon(T){++despawns;}};
template<class T>struct WaypointMovementGenerator{uint32 i_currentNode=0;void MovementInform(T*);};
'''
    # Compile the engine's real dispatch, without rewriting index semantics.
    code+=method(movement,'void WaypointMovementGenerator<Creature>::MovementInform(').replace('void WaypointMovementGenerator<Creature>::','template<> void WaypointMovementGenerator<Creature>::')
    code+='struct Manor:NativeAI{Creature*me;bool m_boarded=true,m_arrived=false;'
    code+=method(dusk[dusk.index('    struct npc_swift_mountain_horse_36741AI'):],'        void MovementInform(')+'};\n'
    code+='struct Bat:NativeAI{Creature*me;bool m_boarded=true;uint32 m_flightState=1;'
    code+=method(city[city.index('    struct npc_captured_riding_bat_38540AI'):],'        void MovementInform(')+'};\n'
    code+=r'''
void check(bool b,char const*m){if(!b)throw std::runtime_error(m);}
template<class Handler>void drive(Handler&handler,Creature&c,uint32 count){c.ai=&handler;WaypointMovementGenerator<Creature>gen;for(uint32 i=0;i<count;++i){gen.i_currentNode=i;gen.MovementInform(&c);check(c.vehicle.removals==(i==count-1?1:0),"native dispatch must land only at the last index");}gen.MovementInform(&c);check(c.vehicle.removals==1,"duplicate final callback must not land twice");}
int main(){
'''
    code+=f'Creature horse;Manor manor;manor.me=&horse;drive(manor,horse,{route_counts[3674101]});check(manor.m_arrived&&horse.despawns==1,"manor last callback ejects rider");\n'
    for route,state in [(3854001,1),(3854003,3)]:
        code+=f'{{Creature c;Bat bat;bat.me=&c;bat.m_flightState={state};drive(bat,c,{route_counts[route]});check(bat.m_flightState==4&&!bat.m_boarded&&!c.gravity&&c.despawns==1,"bat endpoint landing");}}\n'
    code+='std::cout<<"PASS: native WaypointMovementGenerator callback indices, 28-point Manor and 60/14-point bat routes\\n";}\n'
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8')
        flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
