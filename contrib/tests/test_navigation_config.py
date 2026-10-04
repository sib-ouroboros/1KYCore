#!/usr/bin/env python3
"""Compile actual navigation configuration selection and check legacy compatibility."""
import os
from pathlib import Path
import subprocess
import tempfile

def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/game/World/World.cpp').read_text('latin1')
    start = source.index('    bool const preloadBattlegroundNavigation = []()')
    end = source.index('    }();', start) + len('    }();')
    body = source[start:end]
    harness = r"""
#include <algorithm>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <iostream>
struct Config {
    std::map<std::string,int> values;
    std::vector<std::string> reads;
    std::vector<std::string> GetKeysByString(std::string const& prefix) {
        std::vector<std::string> keys;
        for(auto const& row:values)if(row.first.compare(0,prefix.size(),prefix)==0)keys.push_back(row.first);
        return keys;
    }
    int GetIntDefault(std::string const& key,int fallback){
        reads.push_back(key); auto found=values.find(key);
        if(found==values.end())throw std::runtime_error("unexpected missing config read");
        (void)fallback;return found->second;
    }
    bool GetBoolDefault(std::string const& key,bool fallback){return GetIntDefault(key,fallback)!=0;}
};
Config config; Config* sConfigMgr=&config;
bool selectNavigation(){
BODY
    return preloadBattlegroundNavigation;
}
void check(bool value){if(!value)throw std::runtime_error("navigation config regression");}
int main(){
    for(int bg:{0,1,-1})for(int all:{0,1,-1}){
        config.values={{"pbotbg",bg},{"pbotall",all}};config.reads.clear();
        check(selectNavigation()==(bg!=0||all!=0));
        for(int modern:{0,1}){
            config.values["Battleground.PreloadNavigation"]=modern;config.reads.clear();
            check(selectNavigation()==(modern!=0));
            check(config.reads==std::vector<std::string>{"Battleground.PreloadNavigation"});
        }
    }
    config.values.clear();config.reads.clear();check(selectNavigation());check(config.reads.empty());
    config.values={{"pbotall",0}};check(!selectNavigation());
    config.values={{"pbotbg",0}};check(selectNavigation());
    config.values={{"Battleground.PreloadNavigation.extra",0},{"pbotall.extra",0},{"pbotbg.extra",1}};
    config.reads.clear();check(selectNavigation());check(config.reads.empty());
    config.values={{"Battleground.PreloadNavigation",0}};check(!selectNavigation());
    std::cout<<"PASS: actual navigation selection, modern precedence, legacy boolean combinations, absent keys and exact prefix matching\n";
}
""".replace('BODY',body)
    with tempfile.TemporaryDirectory() as tmp:
        cpp,exe=Path(tmp)/'navigation.cpp',Path(tmp)/'navigation'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-sanitize-recover=all','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)

if __name__=='__main__':
    main()
