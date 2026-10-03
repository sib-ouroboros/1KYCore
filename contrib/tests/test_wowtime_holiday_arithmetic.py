#!/usr/bin/env python3
"""Check actual holiday minute arithmetic against an independent day remainder."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/common/Utilities/WowTime.cpp').read_text('latin1')
    expression = next(line.strip() for line in source.splitlines() if 'int64 newTotalMinute =' in line)
    harness = r'''
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <iostream>
using int32=std::int32_t;using int64=std::int64_t;
namespace Globals {namespace InMinutes {constexpr int Day=1440;}}
int64 actual(int32 duration){
EXPRESSION
    return newTotalMinute;
}
void check(int32 duration){
    if(actual(duration)!=duration%1440)throw std::runtime_error("holiday minute arithmetic regression");
}
int main(){
    // All reachable nonnegative remainders after the existing day/time reduction.
    for(int32 n=0;n<2880;++n)check(n);
    for(int32 n:{int32(86400),int32(525600),int32(1000000000),std::numeric_limits<int32>::max()})check(n);
    // Spread checks across the full positive int32 domain, including wide products.
    std::uint32_t state=42;
    for(unsigned n=0;n<100000;++n){state=state*1664525u+1013904223u;check(static_cast<int32>(state&0x7fffffffu));}
    std::cout<<"PASS: actual holiday arithmetic, all two-day minute boundaries, day/year/large durations and 100000 positive int32 samples; strict shift/overflow sanitizers\n";
}
'''.replace('EXPRESSION', expression)
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp) / 'time.cpp', Path(tmp) / 'time'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
