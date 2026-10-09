#!/usr/bin/env python3
"""Actual StopDB and pool Close: release all started connections before Library_End.

Controlled connection/thread boundaries verify ordering, not a full server crash fix.
The deliberately missing-close mutation must reproduce the lifetime contract failure.
"""
import argparse,os,re,subprocess,tempfile
from pathlib import Path


def function(text,signature):
    start=text.index(signature+'\n{');opening=text.index('{',start);depth=1;i=opening+1
    while depth:
        depth+=(text[i]=='{')-(text[i]=='}');i+=1
    return text[start:i]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    main_source=(root/'src/server/worldserver/Main.cpp').read_text('utf8')
    stop=function(main_source,'void StopDB()')
    start=function(main_source,'bool StartDB()')
    names=re.findall(r'\.AddDatabase\((\w+),',start)
    assert len(names)==len(set(names))==5
    pool_source=(root/'src/server/database/Database/DatabaseWorkerPool.cpp').read_text('utf8')
    close=function(pool_source,'void DatabaseWorkerPool<T>::Close()')
    legacy=stop.replace('void StopDB()','void LegacyStopDB()')
    legacy=legacy.replace('    HotfixDatabase.Close();\n','').replace('    ShopDatabase.Close();\n','')
    assert stop!=legacy
    definitions='\n'.join('DatabaseWorkerPool<Connection> '+name+';' for name in names)
    opens='\n'.join(name+'.OpenTest();' for name in names)
    checks='\n'.join('check('+name+'.Empty(),"pool retained resources");' for name in names)
    harness=r'''#include <array>
#include <memory>
#include <vector>
#include <stdexcept>
#include <iostream>
#include <cstddef>
bool libraryAlive=true; unsigned connections=0,workers=0; bool lateAccess=false;
void check(bool ok,char const* message) { if(!ok) throw std::runtime_error(message); }
struct Connection {
 bool worker;
 explicit Connection(bool async):worker(async) { ++connections;if(worker)++workers; }
 ~Connection() { if(!libraryAlive)lateAccess=true;--connections;if(worker)--workers; }
};
struct IoContext { bool stopped=false; void stop() { stopped=true; } };
#define TC_LOG_INFO(...) ((void)0)
template<class T> class DatabaseWorkerPool {
 enum { IDX_ASYNC=0, IDX_SYNCH=1, IDX_SIZE=2 };
 std::unique_ptr<IoContext> _ioContext;
 std::array<std::vector<std::unique_ptr<T>>,IDX_SIZE> _connections;
public:
 void Close();
 void OpenTest() { _ioContext=std::make_unique<IoContext>();
  _connections[IDX_ASYNC].push_back(std::make_unique<T>(true));
  _connections[IDX_ASYNC].push_back(std::make_unique<T>(true));
  _connections[IDX_SYNCH].push_back(std::make_unique<T>(false)); }
 bool Empty() const { return !_ioContext&&_connections[0].empty()&&_connections[1].empty(); }
};
template<class T>
CLOSE
DEFINITIONS
namespace MySQL { void Library_End() {
 check(connections==0&&workers==0,"library finalized while connections/workers are alive");libraryAlive=false;
} }
STOP
LEGACY
int main() {
 OPENS
 check(connections==15&&workers==10,"incomplete startup fixture");
 bool rejected=false;try { LegacyStopDB(); } catch(std::runtime_error const&) { rejected=true; }
 check(rejected&&libraryAlive&&connections==6&&workers==4,"missing two closes did not expose the lifetime failure");
 StopDB();check(!libraryAlive&&!connections&&!workers&&!lateAccess,"shutdown contract failed");
 CHECKS
 // Already closed pools contain no handles for later global destruction.
 std::cout<<"PASS: native StopDB and native pool Close; five pools/15 connections/10 workers closed before Library_End; missing-close mutation rejected\n";
}
'''
    for key,value in {'CLOSE':close,'DEFINITIONS':definitions,'STOP':stop,'LEGACY':legacy,'OPENS':opens,'CHECKS':checks}.items():harness=re.sub(r'^ *'+key+r'$' ,lambda _:value,harness,flags=re.M)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'shutdown.cpp';exe=Path(tmp)/'shutdown';cpp.write_text(harness,encoding='utf8')
        flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
