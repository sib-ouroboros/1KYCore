#include "DetourNavMesh.h"
#include "DetourNavMeshQuery.h"
#include "DetourAlloc.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <cstdint>
#include <cmath>
struct Header{std::uint32_t magic,dtVersion,version,size;char liquid,padding[3];};
struct Spawn{int entry;float x,y,z;};
int main(){try{
 std::ifstream paramsFile("F:/Projects/extracted-735-new/mmaps/0654.mmap",std::ios::binary);dtNavMeshParams params{};
 if(!paramsFile.read(reinterpret_cast<char*>(&params),sizeof(params)))throw std::runtime_error("missing mmap params");
 dtNavMesh* mesh=dtAllocNavMesh();if(dtStatusFailed(mesh->init(&params)))throw std::runtime_error("bad navmesh params");
 unsigned tiles=0;
 for(auto const& file:std::filesystem::directory_iterator("F:/Projects/extracted-735-new/mmaps")){
  if(file.path().extension()!=".mmtile" || file.path().filename().string().rfind("0654",0)!=0)continue;
  std::ifstream in(file.path(),std::ios::binary);Header h{};
  if(!in.read(reinterpret_cast<char*>(&h),sizeof(h))||h.magic!=0x4d4d4150||h.version!=9||h.dtVersion!=DT_NAVMESH_VERSION)throw std::runtime_error("incompatible tile header");
  auto* data=static_cast<unsigned char*>(dtAlloc(h.size,DT_ALLOC_PERM));
  if(!in.read(reinterpret_cast<char*>(data),h.size))throw std::runtime_error("truncated tile");
  if(dtStatusFailed(mesh->addTile(data,h.size,DT_TILE_FREE_DATA,0,nullptr)))throw std::runtime_error("invalid tile data");++tiles;
 }
 dtNavMeshQuery* query=dtAllocNavMeshQuery();if(dtStatusFailed(query->init(mesh,4096)))throw std::runtime_error("query init failed");
 dtQueryFilter filter;filter.setIncludeFlags(1);filter.setExcludeFlags(0);

 float points[][3]={{1603.600000f,23.131000f,-1654.680000f},{1615.850000f,20.490000f,-1664.220000f},{1621.850000f,20.490000f,-1632.820000f},{1607.130000f,21.600000f,-1589.170000f},{1631.440000f,20.589000f,-1569.750000f},{1577.880000f,20.486000f,-1490.200000f},{1577.000000f,20.486000f,-1504.730000f},{1576.880000f,26.680000f,-1529.400000f},{1571.630000f,29.200000f,-1545.550000f},{1524.960000f,29.235000f,-1594.870000f},{1537.650000f,29.300000f,-1614.230000f}};
 dtPolyRef refs[11]{};float near[11][3]{};float extent[]={3,5,3};bool all=true;
 std::cout<<"{\"map\":654,\"tiles\":"<<tiles<<",\"points\":[";
 for(unsigned i=0;i<11;++i){query->findNearestPoly(points[i],extent,&filter,&refs[i],near[i]);bool ground=refs[i]!=0;all&=ground;if(i)std::cout<<",";std::cout<<"{\"point\":"<<i+1<<",\"ground\":"<<(ground?"true":"false")<<",\"source_z\":"<<points[i][1]<<",\"nav_z\":"<<near[i][1]<<"}";}
 std::cout<<"],\"segments\":[";
 for(unsigned i=1;i<11;++i){dtPolyRef polys[4096];int count=0;dtStatus status=0;if(refs[i-1]&&refs[i])status=query->findPath(refs[i-1],refs[i],near[i-1],near[i],&filter,polys,&count,4096);bool full=dtStatusSucceed(status)&&count>0&&polys[count-1]==refs[i]&&!(status&(DT_PARTIAL_RESULT|DT_BUFFER_TOO_SMALL));all&=full;if(i>1)std::cout<<",";std::cout<<(full?"true":"false");}
 std::cout<<"],\"complete\":"<<(all?"true":"false")<<"}\n";
 dtFreeNavMeshQuery(query);dtFreeNavMesh(mesh);return all?0:1;
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 2;}}
