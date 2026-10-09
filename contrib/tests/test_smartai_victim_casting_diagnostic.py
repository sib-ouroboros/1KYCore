#!/usr/bin/env python3
"""Exercise the actual victim-casting validation branch and logged invalid ID."""
import argparse,os,subprocess,tempfile
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[2];text=(root/'src/server/game/AI/SmartScripts/SmartScriptMgr.cpp').read_text('utf8')
    start=text.index('            case SMART_EVENT_VICTIM_CASTING:');end=text.index('            case SMART_EVENT_PASSENGER_BOARDED:',start);branch=text[start:end]
    harness='''#include <cstdint>
#include <tuple>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
enum { SMART_EVENT_VICTIM_CASTING=13 };
uint32 logged=0; unsigned calls=0;
template<class... A> void Log(char const*,char const*,A... args) { logged=std::get<sizeof...(A)-1>(std::make_tuple(args...));++calls; }
#define TC_LOG_ERROR Log
#define SI64FMTD "%lld"
struct Event { union { struct { uint32 repeatMin,repeatMax,spellId; } targetCasting; struct { uint32 spell,school,min,max; } spellHit; }; };
struct Holder { long long entryOrGuid=120808;unsigned event_id=3;Event event{};unsigned GetScriptType() const { return 0; } unsigned GetActionType() const { return 11; } unsigned GetEventType() const { return 13; } };
struct Spells { bool GetSpellInfo(uint32 id) const { return id==241027; } } spells;
auto* sSpellMgr=&spells;
bool IsMinMaxValid(Holder const&,uint32 min,uint32 max) { return min<=max; }
bool Validate(Holder const& e) { switch(e.GetEventType()) {
BRANCH
default:return false;
} return true; }
void check(bool ok) { if(!ok) throw std::runtime_error("victim casting diagnostic/validation regression"); }
int main() { Holder e;
 e.event.targetCasting={5000,8000,20000};check(!Validate(e)&&logged==20000&&calls==1);
 e.event.targetCasting={2000,3000,999999};check(!Validate(e)&&logged==999999&&calls==2);
 e.event.targetCasting={5000,8000,241027};check(Validate(e)&&calls==2);
 e.event.targetCasting={5000,8000,0};check(Validate(e)&&calls==2);
 e.event.targetCasting={8000,5000,0};check(!Validate(e)&&calls==2);
 std::cout<<"PASS: invalid third-parameter Spell ID logged; cooldowns not mislabeled; validation unchanged\\n";
}
'''.replace('BRANCH',branch)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'check.cpp';exe=Path(tmp)/'check';cpp.write_text(harness,encoding='utf8')
        flags=[] if a.no_sanitizers else ['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,str(cpp),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
