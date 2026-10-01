#!/usr/bin/env python3
"""Compile actual VMAP normalization and length used for serialization."""
import os
from pathlib import Path
import subprocess
import tempfile


def function(source, marker):
    start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def main():
    root=Path(__file__).resolve().parents[2]
    model=(root/'src/tools/vmap4_extractor/model.cpp').read_text('utf8')
    adt=(root/'src/tools/vmap4_extractor/adtfile.cpp').read_text('utf8')
    start=model.index('        std::string modelName =')
    end=model.index('        FILE* input = fopen',start)
    block=model[start:end].replace('GetPlainName(&doodadData.Paths[doodad.NameIndex])','GetPlainName(raw.c_str())')
    helpers='\n'.join(function(adt, marker) for marker in
        ('char const* GetPlainName(', 'void FixNameCase(', 'void FixNameSpaces('))
    start=model.index('    std::string tempname =')
    direct=model[start:model.index('\n',start)]
    harness=r'''
#include <cstdint>
#include <cstring>
#include <cctype>
#include <string>
#include <iostream>
#include <stdexcept>
using uint32=std::uint32_t;
HELPERS
struct Result{std::string name,path,serialized;uint32 length=0;};
Result normalize(std::string const& raw,char const* szWorkDirWmo){
    for(int once=0;once<1;++once){
BLOCK
        return {ModelInstName,tempname,std::string(ModelInstName,nlen),nlen};
    }
    return {};
}
std::string direct(char const* ModelInstName,char const* szWorkDirWmo){
DIRECT
    return tempname;
}
void check(bool ok){if(!ok)throw std::runtime_error("VMAP model name regression failed");}
int main(){
    for(std::string extension:{".mdx",".mdl",".m2"}){
        auto result=normalize("World\\Models\\Test_Model"+extension,"Buildings");
        check(result.name=="Test_Model.m2");
        check(result.length==result.name.size()&&result.serialized==result.name);
        check(result.path=="Buildings/"+result.name);
    }
    auto shortName=normalize("A","B");check(shortName.name=="A"&&shortName.length==1);
    auto empty=normalize("","B");check(empty.name.empty()&&empty.path.empty());
    std::string directory(1500,'d'),name(2000,'a');
    auto large=normalize(name+".mdx",directory.c_str());
    check(large.name.size()==2003&&large.length==2003&&large.serialized==large.name);
    check(large.path.size()==3504&&large.path==directory+"/"+large.name);
    check(direct(name.c_str(),directory.c_str())==directory+"/"+name);
    std::cout<<"PASS: actual VMAP normalization, extension length and long paths\n";
}
'''.replace('HELPERS',helpers).replace('BLOCK',block).replace('DIRECT',direct)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'vmap.cpp';exe=Path(tmp)/'vmap';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=undefined',
            '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
