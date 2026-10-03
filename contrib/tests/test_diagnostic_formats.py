#!/usr/bin/env python3
"""Compile actual diagnostic calls and retain full container sizes and GUIDs."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    cases = [
        ('src/server/game/ChallengeMode/ChallengeModeMgr.cpp', 'GenerateOploteLoot manual'),
        ('src/server/game/Globals/BattlePetDataStore.cpp', 'battlepet template in'),
        ('src/server/game/Globals/ObjectMgr.cpp', 'with `movementmode`'),
        ('src/server/game/Handlers/QuestHandler.cpp', 'POIs to player'),
        ('src/server/game/Server/CustomTalkMenu.cpp', 'Talk menu info in'),
        ('src/server/game/Instances/InstanceScript.cpp', 'InstanceScript::Complete'),
    ]
    lines = []
    for filename, marker in cases:
        source = (root / filename).read_text('latin1')
        selected = [line.strip() for line in source.splitlines() if 'TC_LOG_' in line and marker in line]
        assert len(selected) == (2 if 'ObjectMgr.cpp' in filename or 'InstanceScript.cpp' in filename else 1)
        lines.extend(selected)
    macro = next(line for line in (root / 'src/common/Define.h').read_text('latin1').splitlines()
                 if line.startswith('#define UI64FMTD '))
    harness = r'''
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <cinttypes>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
MACRO
std::vector<std::string> messages;
void check(bool ok){if(!ok)throw std::runtime_error("diagnostic format regression");}
void logger(char const*,char const* format,...) __attribute__((format(printf,2,3)));
void logger(char const*,char const* format,...){
    va_list args,copy;va_start(args,format);va_copy(copy,args);
    int n=std::vsnprintf(nullptr,0,format,copy);va_end(copy);check(n>=0);
    std::vector<char> buffer(static_cast<std::size_t>(n)+1);
    std::vsnprintf(buffer.data(),buffer.size(),format,args);va_end(args);
    messages.emplace_back(buffer.data());
}
#define TC_LOG_DEBUG logger
#define TC_LOG_INFO logger
#define TC_LOG_ERROR logger
struct Store {std::size_t count;std::size_t size()const{return count;}};
uint32 GetMSTimeDiffToNow(uint32){return 654;}
void emit(std::size_t count,std::uint64_t guid){
    Store _challengeWeekList{count},_battlePetTemplateStore{count},m_MenuItems{count};
    struct {Store Pois;} response{{count}};
    struct {uint32 id;} data{4294967295u};
    bool manual=true;uint32 oldMSTime=0;
LINES
}
int main(){
    static_assert(sizeof(std::size_t)==8,"Run the 64-bit boundary test on x64");
    for(std::size_t count:{std::size_t(0),std::size_t(1099511627783ULL)}){
        std::uint64_t guid=0xfedcba9876543210ULL;
        messages.clear();emit(count,guid);check(messages.size()==8);
        auto n=std::to_string(count),g=std::to_string(guid);
        check(messages[0]=="GenerateOploteLoot manual 1 _challengeWeekList "+n);
        check(messages[1]==">> Loaded "+n+" battlepet template in 654 ms.");
        check(messages[2]=="Table `creature` has creature (GUID: "+g+" Entry: 4294967295) with `movementmode`< 0, set to 0.");
        check(messages[3]=="Table `creature` has creature (GUID: "+g+" Entry: 4294967295) with `movementmode` > 1, set to 1.");
        check(messages[4]=="Sending "+n+" POIs to player");
        check(messages[5]==">> Loaded "+n+" Talk menu info in 654 ms");
        check(messages[6]=="InstanceScript::CompleteScenario() fail");
        check(messages[7]=="InstanceScript::CompleteCurrStep() fail");
    }
    std::cout<<"PASS: eight actual diagnostic calls, zero/64-bit container counts, full GUID and entry, exact scenario messages, strict printf format checks\n";
}
'''.replace('MACRO', macro).replace('LINES', '\n'.join(lines))
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp) / 'formats.cpp', Path(tmp) / 'formats'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Wformat=2', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
