"""Production MovebyPath guards packed-coordinate overflow, using the Exodus CSV."""
import argparse,csv,os,subprocess,tempfile
from pathlib import Path
from test_gilneas_quests import method
def main():
 p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');args=p.parse_args()
 root=Path(__file__).resolve().parents[2]
 source=(root/'src/server/game/Movement/Spline/MoveSplineInit.cpp').read_text('utf8')
 body=method(source,'void MoveSplineInit::MovebyPath(').replace('MoveSplineInit::','').replace('int32 path_offset)', 'int32 path_offset = 0)')
 code=r"""
#include <vector>
#include <algorithm>
#include <iterator>
#include <cassert>
#include <cstdint>
using int32=std::int32_t;
struct Vector3{float x,y,z;Vector3 operator+(Vector3 a)const{return{x+a.x,y+a.y,z+a.z};}Vector3 operator-(Vector3 a)const{return{x-a.x,y-a.y,z-a.z};}Vector3 operator/(float n)const{return{x/n,y/n,z/n};}};
using PointsArray=std::vector<Vector3>;
struct TransportPathTransform{bool transform;TransportPathTransform(int,bool t):transform(t){}Vector3 operator()(Vector3 v){if(transform){v.x+=1000;v.y-=500;}return v;}};
struct Init{int unit=0;struct Args{int path_Idx_offset=0;bool TransformForTransport=false;PointsArray path;bool uncompressed=false;}args;void SetUncompressed(){args.uncompressed=true;}
"""+body+r"""
};
int main(){
 for(bool transform:{false,true}){
  Init shortPath;shortPath.args.TransformForTransport=transform;shortPath.MovebyPath({{0,0,0},{2,3,1},{5,6,2}},7);assert(!shortPath.args.uncompressed&&shortPath.args.path_Idx_offset==7);
  Init x;x.MovebyPath({{0,0,0},{256,0,0},{0,0,0}});assert(!x.args.uncompressed);
  Init badX;badX.MovebyPath({{0,0,0},{-256,0,0},{0,0,0}});assert(badX.args.uncompressed);
  Init badZ;badZ.MovebyPath({{0,0,0},{0,0,-128},{0,0,0}});assert(badZ.args.uncompressed);
  Init pair;pair.MovebyPath({{0,0,0},{2000,2000,500}});assert(!pair.args.uncompressed);
 }
 Init route;PointsArray points={
"""
 with (root/'contrib/data/gilneas/24438-exodus-player-route.csv').open(encoding='utf8') as f: rows=list(csv.DictReader(f))
 code+=',\n'.join('{'+','.join(v[k]+'f' for k in ['x','y','z'])+'}' for v in rows)
 code+=r""",{-2239.38f,1805.1f,11.94f},{-2310.3f,1774.33f,11.05f},{-2376.5f,1704.52f,11.15f}};
 route.MovebyPath(points);assert(route.args.uncompressed);
 for(unsigned i=0;i<points.size();++i){assert(route.args.path[i].x==points[i].x&&route.args.path[i].y==points[i].y&&route.args.path[i].z==points[i].z);}
}
"""
 with tempfile.TemporaryDirectory() as tmp:
  cpp=Path(tmp)/'test.cpp';exe=Path(tmp)/('test.exe' if os.name=='nt' else 'test');cpp.write_text(code,encoding='utf8')
  flags=[] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),'-std=c++14','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
 print('PASS native MovebyPath: Exodus overflow, short paths, signed boundaries, transformed coordinates and exact XYZ')
if __name__=='__main__':main()
