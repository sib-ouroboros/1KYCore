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
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("usage: tobias-navmesh <mmaps directory>");
 std::filesystem::path directory(argv[1]);
 std::ifstream paramsFile(directory / "0654.mmap",std::ios::binary);dtNavMeshParams params{};
 if(!paramsFile.read(reinterpret_cast<char*>(&params),sizeof(params)))throw std::runtime_error("missing mmap params");
 dtNavMesh* mesh=dtAllocNavMesh();if(dtStatusFailed(mesh->init(&params)))throw std::runtime_error("bad navmesh params");
 unsigned tiles=0;
 for(auto const& file:std::filesystem::directory_iterator(directory)){
  if(file.path().extension()!=".mmtile" || file.path().filename().string().rfind("0654",0)!=0)continue;
  std::ifstream in(file.path(),std::ios::binary);Header h{};
  if(!in.read(reinterpret_cast<char*>(&h),sizeof(h))||h.magic!=0x4d4d4150||h.version!=9||h.dtVersion!=DT_NAVMESH_VERSION)throw std::runtime_error("incompatible tile header");
  auto* data=static_cast<unsigned char*>(dtAlloc(h.size,DT_ALLOC_PERM));
  if(!in.read(reinterpret_cast<char*>(data),h.size))throw std::runtime_error("truncated tile");
  if(dtStatusFailed(mesh->addTile(data,h.size,DT_TILE_FREE_DATA,0,nullptr)))throw std::runtime_error("invalid tile data");++tiles;
 }
 dtNavMeshQuery* query=dtAllocNavMeshQuery();if(dtStatusFailed(query->init(mesh,4096)))throw std::runtime_error("query init failed");
 dtQueryFilter filter;filter.setIncludeFlags(1);filter.setExcludeFlags(0);

 float points[][3]={{1617.035000f,19.971870f,-1623.235000f},{1605.623000f,20.742690f,-1624.289000f},{1607.080000f,21.598900f,-1589.440000f},{1606.710000f,21.598900f,-1588.550000f},{1612.120000f,21.593800f,-1586.860000f},{1617.840000f,20.647600f,-1583.960000f},{1618.980000f,20.603100f,-1570.640000f},{1620.730000f,20.793600f,-1553.420000f},{1618.410000f,23.178800f,-1548.650000f},{1616.660000f,20.570200f,-1546.690000f},{1599.580000f,20.485700f,-1514.130000f},{1582.930000f,20.485700f,-1500.370000f},{1573.470000f,20.485700f,-1496.070000f},{1575.800000f,20.485700f,-1491.170000f},{1577.630000f,20.486900f,-1491.750000f},{1585.360000f,21.164500f,-1508.600000f},{1586.070000f,22.959300f,-1513.000000f},{1586.120000f,25.381400f,-1518.900000f},{1585.740000f,26.536800f,-1528.260000f},{1582.020000f,26.976200f,-1535.760000f},{1582.020000f,26.976200f,-1535.760000f},{1580.220000f,27.704000f,-1537.270000f},{1580.220000f,27.704000f,-1537.270000f},{1578.090000f,28.575700f,-1539.090000f},{1575.430000f,29.207300f,-1541.380000f},{1567.130000f,29.220800f,-1549.640000f},{1567.130000f,29.220800f,-1549.640000f},{1570.570000f,29.191000f,-1555.670000f},{1570.570000f,29.191000f,-1555.670000f},{1559.650000f,29.190300f,-1567.430000f},{1559.650000f,29.190300f,-1567.430000f},{1552.390000f,29.222500f,-1565.010000f},{1552.390000f,29.222500f,-1565.010000f},{1545.110000f,29.202100f,-1571.410000f},{1534.370000f,29.222400f,-1583.740000f},{1528.490000f,29.229700f,-1590.250000f},{1526.850000f,29.236600f,-1598.510000f},{1533.040000f,29.230000f,-1612.350000f}};
 dtPolyRef refs[38]{};float near[38][3]{};float extent[]={3,5,3};bool all=true;
 std::cout<<"{\"map\":654,\"tiles\":"<<tiles<<",\"points\":[";
 for(unsigned i=0;i<38;++i){query->findNearestPoly(points[i],extent,&filter,&refs[i],near[i]);bool ground=refs[i]!=0;all&=ground;if(i)std::cout<<",";std::cout<<"{\"point\":"<<i+1<<",\"ground\":"<<(ground?"true":"false")<<",\"source_z\":"<<points[i][1]<<",\"nav_z\":"<<near[i][1]<<"}";}
 std::cout<<"],\"segments\":[";
 for(unsigned i=1;i<38;++i){if(i==2||i==4||i==8||i==14)continue;dtPolyRef polys[4096];int count=0;dtStatus status=0;if(refs[i-1]&&refs[i])status=query->findPath(refs[i-1],refs[i],near[i-1],near[i],&filter,polys,&count,4096);bool full=dtStatusSucceed(status)&&count>0&&polys[count-1]==refs[i]&&!(status&(DT_PARTIAL_RESULT|DT_BUFFER_TOO_SMALL));all&=full;if(i>1)std::cout<<",";std::cout<<(full?"true":"false");}
 std::cout<<"],\"complete\":"<<(all?"true":"false")<<"}\n";
 dtFreeNavMeshQuery(query);dtFreeNavMesh(mesh);return all?0:1;
}catch(std::exception const&e){std::cerr<<e.what()<<"\n";return 2;}}
