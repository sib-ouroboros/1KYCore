"""Native facing and home movement methods with rotating transport coordinates."""
import argparse,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parents[2]
code=r'''
#include <cmath>
#include <stdexcept>
#include <iostream>
enum{UNIT_STATE_ROOT=1,UNIT_STATE_STUNNED=2,UNIT_STATE_DISTRACTED=4,UNIT_STATE_ALL_ERASABLE=255,UNIT_STATE_EVADE=8};
struct Ship{float x=1000,y=-2000,z=100,angle=0.5;};struct Creature;
struct Reset{bool GetResetPosition(Creature*,float&,float&,float&){return false;}};
struct Motion{Reset reset;bool empty(){return true;}Reset*top(){return &reset;}};
struct Unit{Ship*ship=nullptr;bool stopped=true;float x=10,y=20,z=30;bool IsStopped(){return stopped;}Ship*GetTransport(){return ship;}float GetPositionX(){return x;}float GetPositionY(){return y;}float GetPositionZMinusOffset(){return z;}void SetFacingTo(float,bool);};
struct Creature:Unit{Motion motion;float tx=7,ty=8,tz=86,to=0.4;bool HasUnitState(int){return false;}void GetTransportHomePosition(float&x,float&y,float&z,float&o){x=tx;y=ty;z=tz;o=to;}Motion*GetMotionMaster(){return &motion;}void GetHomePosition(float&a,float&b,float&c,float&o){a=10;b=20;c=30;o=0.6;}void ClearUnitState(int){}};
struct Record{float x=0,y=0,z=0,o=0;bool nav=true,walk=true;int launches=0;}record;
namespace Movement{struct MoveSplineInit{Unit*u;bool transform=true;float x=0,y=0,z=0,o=0;bool nav=true,walk=true;MoveSplineInit(Unit*p):u(p){}void DisableTransportPathTransformations(){transform=false;}void MoveTo(float a,float b,float c,bool n=true){x=a;y=b;z=c;nav=n;}void SetFacing(float a){o=a;}void SetWalk(bool b){walk=b;}void Launch(){if(u->ship&&transform){auto*s=u->ship;float dx=x-s->x,dy=y-s->y;x=std::cos(s->angle)*dx+std::sin(s->angle)*dy;y=-std::sin(s->angle)*dx+std::cos(s->angle)*dy;z-=s->z;o-=s->angle;}record={x,y,z,o,nav,walk,record.launches+1};}};}
struct Home{bool skipToHome=false,arrived=false;void Target(Creature*);};
'''
code+=method((r/'src/server/game/Entities/Unit/Unit.cpp').read_text('utf8'),'void Unit::SetFacingTo(float')
code+=method((r/'src/server/game/Movement/MovementGenerators/HomeMovementGenerator.cpp').read_text('utf8'),'void HomeMovementGenerator<Creature>::_setTargetLocation(').replace('void HomeMovementGenerator<Creature>::_setTargetLocation','void Home::Target')
code+=r'''
void check(bool b){if(!b)throw std::runtime_error("transport coordinate regression");}bool near(float a,float b){return std::fabs(a-b)<0.001;}
int main(){Ship ship;Creature c;c.ship=&ship;c.x=ship.x+std::cos(ship.angle)*5-std::sin(ship.angle)*4;c.y=ship.y+std::sin(ship.angle)*5+std::cos(ship.angle)*4;c.z=186;
c.SetFacingTo(1.2,true);check(near(record.x,5)&&near(record.y,4)&&near(record.z,86)&&near(record.o,0.7));c.stopped=false;int prior=record.launches;c.SetFacingTo(2,false);check(record.launches==prior);
Home h;h.Target(&c);check(near(record.x,7)&&near(record.y,8)&&near(record.z,86)&&near(record.o,0.4)&&!record.nav&&!record.walk);
ship.x+=500;ship.y-=400;ship.angle+=1;h.Target(&c);check(near(record.x,7)&&near(record.y,8)&&near(record.z,86));
c.ship=nullptr;c.x=10;c.y=20;c.z=30;c.SetFacingTo(1,true);check(near(record.x,10)&&near(record.y,20)&&near(record.z,30)&&near(record.o,1));h.Target(&c);check(near(record.x,10)&&near(record.y,20)&&near(record.z,30)&&record.nav);
std::cout<<"PASS: native facing/home on moving rotated transport and unchanged non-transport movement\n";}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/'test.exe';cpp.write_text(code,'utf8');flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)

