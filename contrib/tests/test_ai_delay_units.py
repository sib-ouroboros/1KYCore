#!/usr/bin/env python3
"""Compile actual UnitAI delayed-event forwarding and native duration aliases."""
import os
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/game/AI/CoreAI/UnitAI.cpp').read_text('utf8')
    methods='\n'.join(method(source,'void UnitAI::AddDelayedEvent('+kind) for kind in ('Minutes','Seconds'))
    harness=r'''
#include "Duration.h"
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <iostream>
#include <utility>
struct Unit {
    std::uint64_t offset=0;
    std::function<void()> callback;
    void AddDelayedEvent(std::uint64_t ms,std::function<void()>&& fn) {offset=ms;callback=std::move(fn);}
};
struct UnitAI {
    Unit* me;
    void AddDelayedEvent(Minutes,std::function<void()>&&);
    void AddDelayedEvent(Seconds,std::function<void()>&&);
};
METHODS
void check(bool value){if(!value)throw std::runtime_error("UnitAI delay unit regression");}
int main(){
    Unit unit;UnitAI ai{&unit};unsigned calls=0;
    ai.AddDelayedEvent(Seconds(3),[&]{++calls;});check(unit.offset==3000&&calls==0);unit.callback();check(calls==1);
    ai.AddDelayedEvent(Minutes(2),[&]{++calls;});check(unit.offset==120000&&calls==1);unit.callback();check(calls==2);
    ai.AddDelayedEvent(Seconds(0),[]{});check(unit.offset==0);
    ai.AddDelayedEvent(Seconds(5000000),[]{});check(unit.offset==5000000000ULL);
    std::cout<<"PASS: actual UnitAI seconds/minutes forwarding, milliseconds, zero and 64-bit delay, deferred callback\n";
}
'''.replace('METHODS',methods)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'delay.cpp';exe=Path(tmp)/'delay';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g',
            '-I',str(root/'src/common/Utilities'),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
