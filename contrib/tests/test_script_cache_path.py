#!/usr/bin/env python3
"""Exercise actual dynamic script cache path construction with branch separators."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/game/Scripting/ScriptReloadMgr.cpp').read_text('utf8')
    body = method(source, '    static fs::path CalculateTemporaryCachePath()')
    branches = ['development/character-tools', 'cleanup/remove-bots', 'main', 'feature\\windows',
                '../outside', '/absolute', 'C:branch', 'feature/тест', 'a_b', 'a/b', '']
    configs = ['/opt/1kycore/etc/worldserver.conf', '/other/worldserver.conf']
    fixtures = ','.join('{' + json.dumps(s, ensure_ascii=False) + ',' + json.dumps(hashlib.sha1(s.encode('utf8')).hexdigest().upper()) + '}'
                        for s in branches + configs)
    names = ','.join(json.dumps(s, ensure_ascii=False) for s in branches)
    harness = r'''
#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <cstdio>
#include <stdexcept>
#include <iostream>
namespace fs=std::filesystem;
std::string branch,config;
namespace GitRevision {char const* GetBranch(){return branch.c_str();}}
struct Config {std::string GetFilename()const{return config;}} configMgr;
auto* sConfigMgr=&configMgr;
// Dependency fixture: exact SHA1 values precomputed independently by Python.
std::map<std::string,std::string> hashes={FIXTURES};
std::string CalculateSHA1Hash(std::string const& s){return hashes.at(s);}
namespace Trinity {
std::string StringFormat(char const* format,char const* a,char const* b){
    int n=std::snprintf(nullptr,0,format,a,b);if(n<0)throw std::runtime_error("format failure");
    std::vector<char> buffer(static_cast<std::size_t>(n)+1);std::snprintf(buffer.data(),buffer.size(),format,a,b);
    return buffer.data();
}}
BODY
void check(bool ok){if(!ok)throw std::runtime_error("dynamic script cache path regression");}
int main(){
    std::vector<std::string> branches={BRANCHES};std::set<std::string> seen;
    for(auto const& name:branches){
        branch=name;config="/opt/1kycore/etc/worldserver.conf";
        auto path=CalculateTemporaryCachePath();
        check(path.parent_path()==fs::temp_directory_path());
        auto filename=path.filename().string();
        check(filename.find('/')==std::string::npos&&filename.find('\\')==std::string::npos&&filename.find(':')==std::string::npos);
        check(filename=="tc_script_cache_"+hashes.at(branch)+"_"+hashes.at(config));
        check(seen.insert(filename).second);
        check(fs::create_directory(path));check(fs::is_directory(path));check(fs::remove(path));
        config="/other/worldserver.conf";check(CalculateTemporaryCachePath()!=path);
    }
    std::cout<<"PASS: actual dynamic cache path, branch slash/backslash/traversal/absolute/unicode/empty names, distinct branch/config identities and successful single-directory creation\n";
}
'''.replace('FIXTURES', fixtures).replace('BRANCHES', names).replace('BODY', body)
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp) / 'cache.cpp', Path(tmp) / 'cache'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], env={**os.environ, 'TMPDIR': tmp}, check=True)


if __name__ == '__main__':
    main()
