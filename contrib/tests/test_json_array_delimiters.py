#!/usr/bin/env python3
"""Compile the actual bundled JSON library and verify array separator parsing."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    library = root/'src/server/game/Server/Json'
    harness = r'''
#include "json.h"
#include <stdexcept>
#include <iostream>
void check(bool result) { if (!result) throw std::runtime_error("JSON delimiter regression"); }
int main() {
    Json::Reader reader; Json::Value value;
    check(reader.parse("[1,2,3]",value));
    check(value.size()==3 && value[0u].asInt()==1 && value[1u].asInt()==2 && value[2u].asInt()==3);
    check(reader.parse("[]",value) && value.size()==0);
    check(reader.parse("[1 /*comment*/, [2,3], {\"x\":4}]",value));
    check(value.size()==3 && value[1].size()==2 && value[2]["x"].asInt()==4);
    for (auto malformed : {"[1 2 3]", "[1 true 3]", "[1 : 3]", "[1 } 3]", "[1 {\"x\":2},3]", "[[1 2 3]]", "[1,]", "[1,,2]"}) {
        check(!reader.parse(malformed,value));
        check(!reader.getFormattedErrorMessages().empty());
    }
    check(reader.parse("[4,5]",value) && value.size()==2 && value[1].asInt()==5);
    std::cout << "PASS: actual JSON library preserves valid arrays and rejects missing or invalid separators without discarding tokens\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp)/'arrays.cpp', Path(tmp)/'arrays'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra',
                        '-Werror=return-type','-fsanitize=address,undefined','-fno-sanitize-recover=all','-g',
                        '-I'+str(library),'-I'+str(root/'src/common'),str(cpp),
                        str(library/'json_reader.cpp'),str(library/'json_value.cpp'),str(library/'json_writer.cpp'),
                        '-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__ == '__main__':
    main()
