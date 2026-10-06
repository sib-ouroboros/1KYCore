#!/usr/bin/env python3
"""Production Gilneas route arrays, wave lookup and movement callback bounds."""
import argparse, os, re, subprocess, tempfile
from pathlib import Path
from test_gilneas_quests import method

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    s=(root/'src/server/scripts/EasternKingdoms/Gilneas/zone_gilneas_city2.cpp').read_text('utf8')
    assert '#include "ObjectMgr.h"' in s
    # Catch the real signature/include requirement missed by the earlier entity fixture.
    object_mgr=(root/'src/server/game/Globals/ObjectMgr.h').read_text('utf8')
    assert 'GetScriptId(' in object_mgr
    arrays=[]
    for match in re.finditer(r'Position\s+const\s+(\w*Wave\w*Pos)\[\d+\]',s):
        arrays.append(method(s,match.group(0))+';')
    sections=re.split(r'    struct (npc_\w+AI) : public ScriptedAI',s)
    classes=[];exercises=[];lookups=0
    for i in range(1,len(sections),2):
        name,body=sections[i:i+2]
        if '        Position GetWavePosition()' not in body:continue
        route=method(body,'        Position GetWavePosition()')
        move=method(body,'        void MovementInform(')
        fight=method(body,'case EVENT_FIGHT_WAVE:')
        prefix=fight[:fight.index('CheckForStartAction();')]
        classes.append('struct '+name+'{Creature*me;Events m_events;uint32 m_wave=0,m_waveSize=0,m_point=0;int fights=0;\n'+route+'\n'+move+'\nvoid Fight(){switch(EVENT_FIGHT_WAVE){'+prefix+'++fights;break;}}}\n};')
        # Each real switch case is paired with its own real array, without invented coordinates.
        pairs=re.findall(r'case (\d+):\s*if \(m_point < sizeof\((\w+)\)',route)
        for wave,array in pairs:
            lookups+=1
            exercises.append('checkRoute<'+name+'>('+wave+','+array+');')
        # Unsupported waves and callbacks before/after active routes must never schedule fights.
        exercises.append('checkIdle<'+name+'>();')
    assert len(classes)==6 and lookups==31 and len(arrays)==27,(len(classes),lookups,len(arrays))
    code=r'''
#include <cstdint>
#include <stdexcept>
#include <iostream>
#include <limits>
using uint32=std::uint32_t;
constexpr int POINT_MOTION_TYPE=1,EVENT_FIGHT_WAVE=2,EVENT_MOVE_WAVE=3,EVENT_LIAM_DEATH_TALK1=4;
struct Position{float x,y,z,o;Position(float a=0,float b=0,float c=0,float d=0):x(a),y(b),z(c),o(d){}};
bool same(Position a,Position b){return a.x==b.x&&a.y==b.y&&a.z==b.z&&a.o==b.o;}
struct Creature{Position pos{11,22,33,4};Position GetPosition()const{return pos;}};
struct Events{int fight=0,move=0,dialogue=0;void RescheduleEvent(int id,int){if(id==EVENT_FIGHT_WAVE)++fight;if(id==EVENT_MOVE_WAVE)++move;}void ScheduleEvent(int id,int){if(id==EVENT_LIAM_DEATH_TALK1)++dialogue;}};
void check(bool ok,char const*msg){if(!ok)throw std::runtime_error(msg);}
ARRAYS
CLASSES
template<class AI,std::size_t N>void checkRoute(uint32 wave,Position const(&points)[N]){
 Creature me;AI ai;ai.me=&me;ai.m_wave=wave;ai.m_waveSize=N;
 for(uint32 i=0;i<N;++i){ai.m_point=i;check(same(ai.GetWavePosition(),points[i]),"all original route coordinates retained");ai.MovementInform(POINT_MOTION_TYPE,2000+wave);}
 check(ai.m_events.fight==N,"current wave callback accepted");
 ai.m_point=N;ai.MovementInform(POINT_MOTION_TYPE,2000+wave);check(ai.m_events.fight==N,"completed route callback discarded");check(same(ai.GetWavePosition(),me.pos),"one-past-end never reads array or returns origin");ai.Fight();check(!ai.fights&&ai.m_events.move==1,"queued fight at endpoint hands off through normal movement event");
 ai.m_point=std::numeric_limits<uint32>::max();check(same(ai.GetWavePosition(),me.pos),"very large route index safe");
 ai.m_point=0;ai.MovementInform(POINT_MOTION_TYPE,2000+(wave==7?6:wave+1));ai.MovementInform(2,2000+wave);check(ai.m_events.fight==N,"old wave and non-point callbacks ignored");ai.Fight();check(ai.fights==1,"valid fight still proceeds");
}
template<class AI>void checkIdle(){Creature me;AI ai;ai.me=&me;ai.MovementInform(1,2001);ai.Fight();check(!ai.m_events.fight&&!ai.m_events.move&&!ai.fights,"idle callbacks do not start movement");check(same(ai.GetWavePosition(),me.pos),"invalid wave stays at current position");}
int main(){try{EXERCISES Creature king;npc_king_genn_greymane_38470AI ai;ai.me=&king;ai.MovementInform(POINT_MOTION_TYPE,1002);check(ai.m_events.dialogue==1,"king cinematic callback preserved outside wave guards"); std::cout<<"Gilneas battle: 31 native routes, six movement callbacks and fight entry gates PASS\n";}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
    code=code.replace('ARRAYS','\n'.join(arrays)).replace('CLASSES','\n'.join(classes)).replace('EXERCISES','\n'.join(exercises))
    with tempfile.TemporaryDirectory() as folder:
        cpp=Path(folder)/'waves.cpp';exe=Path(folder)/'waves.exe';cpp.write_text(code,'utf8')
        cmd=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)]
        if not args.no_sanitizers:cmd[1:1]=['-fsanitize=address,undefined','-fno-sanitize-recover=undefined','-fno-omit-frame-pointer']
        subprocess.run(cmd,check=True);subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
