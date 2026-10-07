#!/usr/bin/env python3
"""Compile the actual conversation line loader against legacy and updated database layouts."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
from test_conversation_packet_layout import declaration


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--no-sanitizers',action='store_true')
    a=p.parse_args();root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/Globals/ConversationDataStore.cpp').read_text('utf8')
    start=source.index('    QueryResult paddingColumns =')
    end=source.index('    if (QueryResult actors =',start)
    body=source[start:end]
    native=declaration((root/'src/server/game/Globals/ConversationDataStore.h').read_text('utf8'),'ConversationLineTemplate')
    header=r"""
#include <cstdint>
#include <memory>
#include <vector>
#include <unordered_map>
#include <string>
#include <stdexcept>
#include <iostream>
using uint8=std::uint8_t;using uint16=std::uint16_t;using uint32=std::uint32_t;
#define SZFMTD "%zu"
template<class... Args> void log(Args const&...){}
#define TC_LOG_INFO(...) log(__VA_ARGS__)
#define TC_LOG_ERROR(...) log(__VA_ARGS__)
uint32 getMSTime(){return 1;}uint32 GetMSTimeDiffToNow(uint32){return 0;}
struct Field{uint32 value;uint32 GetUInt32()const{return value;}uint8 GetUInt8()const{return uint8(value);}uint16 GetUInt16()const{return uint16(value);}};
struct Result{std::vector<std::vector<Field>> rows;std::size_t current=0;Field* Fetch(){return rows.at(current).data();}bool NextRow(){return ++current<rows.size();}};
using QueryResult=std::shared_ptr<Result>;
struct Database{
 int layout=0;bool empty=false;bool selectedPadding=false;
 QueryResult Query(char const* query){
  std::string q=query;
  if(q.find("information_schema")!=std::string::npos)return std::make_shared<Result>(Result{{{{uint32(layout==1)}}},0});
  selectedPadding=q.find("Flags, Padding")!=std::string::npos;
  if(selectedPadding!=(layout==1))throw std::runtime_error("incompatible query layout");
  if(empty)return nullptr;
  std::vector<std::vector<Field>> rows={{{8926},{0},{0},{0},{0}},{{8928},{4095},{0},{0},{0}},{{8931},{12480},{0},{1},{0}},{{9883},{0},{0},{0},{0}},{{9570},{8129},{0},{0},{0}},{{9999},{0},{0},{0},{0}}};
  if(selectedPadding){for(auto& row:rows)row.push_back({0});rows[1][5].value=100;rows[4][5].value=2078;}
  return std::make_shared<Result>(Result{rows,0});
 }
}WorldDatabase;
struct LineStore{bool LookupEntry(uint32 id)const{return id!=9999;}}sConversationLineStore;
#pragma pack(push,1)
"""
    harness=header+native+r"""
#pragma pack(pop)
std::unordered_map<uint32,ConversationLineTemplate> _conversationLineTemplateStore;
void load(){
"""+body+r"""
}
void check(bool x){if(!x)throw std::runtime_error("loaded line mismatch");}
int main(){try{
 for(int layout:{0,1,2}){
  WorldDatabase.layout=layout;WorldDatabase.empty=false;_conversationLineTemplateStore.clear();
  _conversationLineTemplateStore[8928].Padding=65535;
  load();check(_conversationLineTemplateStore.size()==5);check(!_conversationLineTemplateStore.count(9999));
  check(_conversationLineTemplateStore.at(8928).Padding==(layout==1?100:0));
  check(_conversationLineTemplateStore.at(9570).Padding==(layout==1?2078:0));
  check(_conversationLineTemplateStore.at(8931).ActorIdx==1);
  check(_conversationLineTemplateStore.at(8928).StartTime==4095);
  check(_conversationLineTemplateStore.at(8928).Flags==0);
  WorldDatabase.empty=true;_conversationLineTemplateStore.clear();load();check(_conversationLineTemplateStore.empty());
 }
 std::cout<<"PASS: actual line loader, legacy/compatible/incompatible schemas, exact high words, indices, empty and invalid DB2 rows\n";
}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
"""
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);cpp=d/'line.cpp';exe=d/'line.exe';cpp.write_text(harness,'utf8')
        flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
