#!/usr/bin/env python3
"""Compile actual point-path/normalization/collision code with analytical geometry.

This is a C++ control-flow regression, not a substitute for real MMAP/VMAP tests.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def function(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default=os.environ.get('CXX', 'c++'))
    parser.add_argument('--no-sanitizers', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/game/Movement/PathGenerator.cpp').read_text('latin1')
    bodies = '\n'.join(function(source, signature) for signature in (
        'void PathGenerator::BuildPointPath(', 'bool PathGenerator::NormalizePath(',
        'void PathGenerator::ValidatePathAgainstCollision(', 'void PathGenerator::BuildShortcut('))
    harness = r"""
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using uint32 = uint32_t;
using dtStatus = unsigned;
using dtPolyRef = unsigned;
constexpr dtStatus DT_FAILURE=0, DT_SUCCESS=1;
bool dtStatusFailed(dtStatus s){return !s;}
#define TC_LOG_DEBUG(...) do {} while(false)
#define MAX_POINT_PATH_LENGTH 7400
#define VERTEX_SIZE 3
#define SMOOTH_PATH_STEP_SIZE 2.0f
#define SMOOTH_PATH_SLOP 0.3f
constexpr float INVALID_HEIGHT=-100000;
constexpr int TYPEID_UNIT=3;
namespace VMAP { enum class ModelIgnoreFlags { Nothing }; }
namespace G3D {
struct Vector3 {
    float x=0,y=0,z=0;
    Vector3()=default;
    Vector3(float a,float b,float c):x(a),y(b),z(c){}
    Vector3 operator-(Vector3 p)const{return {x-p.x,y-p.y,z-p.z};}
    Vector3& operator+=(Vector3 p){x+=p.x;y+=p.y;z+=p.z;return *this;}
    Vector3& operator*=(float a){x*=a;y*=a;z*=a;return *this;}
    float length()const{return std::sqrt(x*x+y*y+z*z);}
};
}
enum PathType { PATHFIND_BLANK=0,PATHFIND_NORMAL=1,PATHFIND_SHORTCUT=2,
    PATHFIND_INCOMPLETE=4,PATHFIND_NOPATH=8,PATHFIND_NOT_USING_PATH=16,PATHFIND_SHORT=32 };
struct Floor {float first,last,z;bool dynamic=true;};
struct Map {
    std::vector<Floor> floors;
    int extraHeightQueries=0;
    bool water=false,wall=false;
    float height(float x,float z,float range)const {
        float result=INVALID_HEIGHT;
        for(auto const& f:floors){
            float origin=z+(f.dynamic?0.5f:2.0f);
            if(x>=f.first&&x<f.last&&origin>=f.z&&origin-f.z<=range)
                result=std::max(result,f.z);
        }
        return result;
    }
    float GetHeight(int,float x,float,float z,bool,float range){
        ++extraHeightQueries;return height(x,z,range);
    }
    bool IsInWater(int,float,float,float)const{return water;}
    bool isInLineOfSight(int,float x,float,float z,float tx,float,float tz,VMAP::ModelIgnoreFlags)const {
        if(wall&&x<3&&tx>=3)return false;
        for(auto const& f:floors){
            if(std::fabs(tz-z)<0.00001f)continue;
            float t=(f.z-z)/(tz-z);
            if(t>0.00001f&&t<0.99999f){
                float ix=x+t*(tx-x);
                if(ix>=f.first&&ix<f.last)return false;
            }
        }
        return true;
    }
};
struct Unit {
    Map* map;
    bool fly=false,swim=false,transport=false;
    int type=TYPEID_UNIT;
    int GetTypeId()const{return type;}
    bool GetTransport()const{return transport;}
    Unit const* ToCreature()const{return this;}
    bool CanFly()const{return fly;}
    bool IsInWater()const{return swim;}
    bool IsUnderWater()const{return swim;}
    Map* GetMap()const{return map;}
    int GetPhaseShift()const{return 0;}
    void UpdateAllowedPositionZ(float x,float,float& z)const {
        if(transport)return;
        float floor=map->height(x,z,10000);
        if(floor>INVALID_HEIGHT&&(!fly||floor>z))z=floor;
    }
};
struct NavQuery {
    std::vector<G3D::Vector3> points;
    bool fail=false;
    dtStatus findStraightPath(float const*,float const*,dtPolyRef*,uint32,float* out,
        void*,void*,int* count,uint32 limit){
        *count=std::min<uint32>(points.size(),limit);
        for(int i=0;i<*count;++i){out[3*i]=points[i].y;out[3*i+1]=points[i].z;out[3*i+2]=points[i].x;}
        return fail?DT_FAILURE:DT_SUCCESS;
    }
};
struct PathGenerator {
    Unit const* _sourceUnit;
    NavQuery* _navMeshQuery;
    std::vector<G3D::Vector3> _pathPoints;
    PathType _type=PATHFIND_NORMAL;
    bool _straightLine=false,_useStraightPath=true,_forceDestination=false;
    uint32 _pointPathLimit=MAX_POINT_PATH_LENGTH,_polyLength=1;
    dtPolyRef _pathPolyRefs[1]={1};
    G3D::Vector3 start,end,actualEnd;
    PathGenerator(Unit* u,NavQuery* n,G3D::Vector3 s,G3D::Vector3 e):
        _sourceUnit(u),_navMeshQuery(n),start(s),end(e),actualEnd(e){}
    G3D::Vector3 const& GetStartPosition()const{return start;}
    G3D::Vector3 const& GetEndPosition()const{return end;}
    G3D::Vector3 const& GetActualEndPosition()const{return actualEnd;}
    void SetActualEndPosition(G3D::Vector3 p){actualEnd=p;}
    void Clear(){_polyLength=0;_pathPoints.clear();}
    float Dist3DSqr(G3D::Vector3 a,G3D::Vector3 b)const{auto d=a-b;return d.x*d.x+d.y*d.y+d.z*d.z;}
    bool InRange(G3D::Vector3 a,G3D::Vector3 b,float r,float h)const{
        auto d=a-b;return d.x*d.x+d.y*d.y<=r*r&&std::fabs(d.z)<=h;
    }
    dtStatus FindSmoothPath(float const* a,float const* b,dtPolyRef* p,uint32 n,
        float* out,int* count,uint32 limit){return _navMeshQuery->findStraightPath(a,b,p,n,out,nullptr,nullptr,count,limit);}
    void BuildPointPath(float const*,float const*);
    bool NormalizePath(bool preserveSurface=false);
    void ValidatePathAgainstCollision();
    void BuildShortcut();
    void build(){float s[]={start.y,start.z,start.x},e[]={end.y,end.z,end.x};BuildPointPath(s,e);}
};
BODY
void check(bool ok,char const* name){if(!ok)throw std::runtime_error(name);}
void near(float actual,float expected,char const* name){check(std::fabs(actual-expected)<0.001f,name);}
int main(){try {
    Map map;map.floors={{-100,100,38,false},{-10,10,45,true}};
    Unit unit{&map};NavQuery nav;nav.points={{0,0,38},{2,0,38},{4,0,38}};
    PathGenerator platform(&unit,&nav,{0,0,45},{4,0,45});platform.build();
    for(auto p:platform._pathPoints)near(p.z,45,"platform floor");
    check(platform._type==PATHFIND_NORMAL,"platform path type");
    std::cout<<"Evidence: source Z=45, MMAP Z=38, old normalized Z=38, new Z="<<platform._pathPoints[1].z<<"\n";
    // An upper storey must not attract a query from the current storey.
    map.floors.push_back({-10,10,49,true});platform.build();
    for(auto p:platform._pathPoints)near(p.z,45,"upper storey");
    map.floors={{-100,100,38,false},{-10,2,45,true},{2,4,44,true},{4,6,43,true},
        {6,8,42,true},{8,10,41,true},{10,12,40,true},{12,14,39,true}};
    nav.points={{0,0,38},{2,0,38},{4,0,38},{6,0,38},{8,0,38},{10,0,38},{12,0,38},{14,0,38},{16,0,38}};
    PathGenerator stairs(&unit,&nav,{0,0,45},{16,0,38});stairs.build();
    float expected[]={45,44,43,42,41,40,39,38,38};
    check(stairs._pathPoints.size()==9,"stairs point count");
    for(unsigned i=0;i<9;++i)near(stairs._pathPoints[i].z,expected[i],"stairs descent/bridge exit");
    // A target below an intact platform cannot be reached by forcing the last vertex.
    map.floors={{-100,100,38,false},{-10,10,45,true}};
    nav.points={{0,0,38},{2,0,38},{4,0,38}};
    PathGenerator below(&unit,&nav,{0,0,45},{4,0,38});below._forceDestination=true;below.build();
    near(below.actualEnd.z,45,"forced destination through floor");
    check(below._type==PATHFIND_INCOMPLETE,"unreachable lower destination");
    // Loss of support over the same floor must be rejected from the real start.
    map.floors={{-100,100,38,false},{-10,1,45,true}};
    nav.points={{0,0,38},{2,0,38}};
    PathGenerator edge(&unit,&nav,{0,0,45},{2,0,38});edge.build();
    check(edge._type==PATHFIND_NOPATH,"vertical drop through platform edge");
    near(edge._pathPoints[0].z,45,"collision start anchor");
    // A wall truncates a corrected path rather than creating a shortcut.
    map.floors={{-100,100,38,false},{-10,10,45,true}};map.wall=true;
    nav.points={{0,0,38},{2,0,38},{4,0,38}};
    PathGenerator wall(&unit,&nav,{0,0,45},{4,0,45});wall.build();
    check(wall._pathPoints.size()==2&&(wall._type&PATHFIND_INCOMPLETE),"wall truncation");
    near(wall.actualEnd.x,2,"wall endpoint");map.wall=false;
    // Bad spawn: no floor supports Z=47, so no new correction is activated.
    PathGenerator badSpawn(&unit,&nav,{0,0,47},{4,0,38});badSpawn._pathPoints=nav.points;
    check(!badSpawn.NormalizePath(true),"invalid spawn not hidden");
    near(badSpawn._pathPoints[1].z,38,"bad spawn legacy normalization");
    // Terrain/caves with the correct MMAP layer have exactly the old normalization.
    map.floors={{-100,100,38,false},{-10,10,45,true}};
    nav.points={{0,0,38},{2,0,38},{4,0,38}};
    PathGenerator terrain(&unit,&nav,{0,0,38},{4,0,38});
    map.extraHeightQueries=0;terrain.build();
    check(map.extraHeightQueries==0,"ordinary terrain overhead");
    for(auto p:terrain._pathPoints)near(p.z,38,"terrain/cave lower level");
    // Flying, swimming, transport, player-controlled paths keep their old rules.
    for(int mode=0;mode<4;++mode){
        unit.fly=mode==0;unit.swim=mode==1;unit.transport=mode==2;unit.type=mode==3?4:TYPEID_UNIT;
        PathGenerator bypass(&unit,&nav,{0,0,45},{4,0,38});bypass._pathPoints=nav.points;
        map.extraHeightQueries=0;check(!bypass.NormalizePath(true),"special movement bypass");
        check(map.extraHeightQueries==0,"special movement overhead");
    }
    unit.fly=false;unit.swim=false;unit.transport=false;unit.type=TYPEID_UNIT;
    // Empty paths and unavailable height data are safe.
    PathGenerator empty(&unit,&nav,{0,0,45},{4,0,38});check(!empty.NormalizePath(true),"empty path");
    map.floors.clear();empty._pathPoints=nav.points;check(!empty.NormalizePath(true),"missing collision height");
    // BuildShortcut must not opt into surface re-projection (NOPATH/SHORT/fly fallback).
    map.floors={{-100,100,38,false},{-10,10,45,true}};
    PathGenerator shortcut(&unit,&nav,{0,0,45},{4,0,38});shortcut.BuildShortcut();
    near(shortcut._pathPoints.back().z,38,"shortcut unchanged");
    check(shortcut._type==PATHFIND_SHORTCUT,"shortcut status");
    nav.fail=true;shortcut.build();check(shortcut._type==PATHFIND_NOPATH,"Detour failure");nav.fail=false;
    shortcut._pointPathLimit=nav.points.size();shortcut.build();check(shortcut._type==PATHFIND_SHORT,"path point limit");
    // Partial native corridors are also normalized without changing their status.
    PathGenerator partial(&unit,&nav,{0,0,45},{4,0,45});partial._type=PATHFIND_INCOMPLETE;partial.build();
    check(partial._type==PATHFIND_INCOMPLETE,"partial path status");near(partial.actualEnd.z,45,"partial height");
    std::cout<<"PASS: actual point-path control flow, platform, stairs, storeys, walls, forced endpoint, invalid spawn, terrain, special movement and path statuses\n";
} catch(std::exception const& e){std::cerr<<e.what()<<std::endl;return 1;}
}
""".replace('BODY', bodies)
    with tempfile.TemporaryDirectory() as directory:
        cpp, exe = Path(directory)/'surface.cpp', Path(directory)/'surface.exe'
        cpp.write_text(harness, encoding='utf-8')
        flags = ['-std=c++17', '-Wall', '-Wextra', '-Werror', '-g']
        if not args.no_sanitizers:
            flags += ['-fsanitize=address,undefined', '-fno-sanitize-recover=all']
        subprocess.run([args.compiler, *flags, str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
