#!/usr/bin/env python3
"""Compile actual MySQL prepare error logging with a bounded string_view."""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    source=(root/'src/server/database/Database/MySQLConnection.cpp').read_text('utf8')
    assert re.search(r'PrepareStatement\([^)]*std::string_view sql',source)
    lines=[line.strip() for line in source.splitlines() if 'TC_LOG_ERROR' in line and ('In mysql_stmt_init()' in line or 'In mysql_stmt_prepare()' in line)]
    assert len(lines)==2
    harness=r'''
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
std::vector<std::string> messages;
void check(bool value){if(!value)throw std::runtime_error("MySQL prepare logging regression");}
void log_error(char const*,char const* format,...) __attribute__((format(printf,2,3)));
void log_error(char const*,char const* format,...){
    va_list args,copy;va_start(args,format);va_copy(copy,args);
    int length=std::vsnprintf(nullptr,0,format,copy);va_end(copy);check(length>=0);
    std::vector<char> buffer(static_cast<std::size_t>(length)+1);
    std::vsnprintf(buffer.data(),buffer.size(),format,args);va_end(args);
    messages.emplace_back(buffer.data());
}
#define TC_LOG_ERROR log_error
void failure(std::string_view sql,uint32 index){
LINES
}
int main(){
    std::vector<std::string> queries={"", "SELECT 1", "SELECT 'тест'", std::string(8192,'x')};
    for(auto const& query:queries){
        std::string backing="["+query+"]UNRELATED_SUFFIX";
        std::string_view view(backing.data()+1,query.size());
        failure(view,4000000000u);
        check(messages[messages.size()-2]=="In mysql_stmt_init() id: 4000000000, sql: \""+query+"\"");
        check(messages.back()=="In mysql_stmt_prepare() id: 4000000000, sql: \""+query+"\"");
    }
    std::cout<<"PASS: actual MySQL prepare logging, bounded/nonterminated string_view, empty/UTF8/long SQL and full statement index\n";
}
'''.replace('LINES','\n'.join(lines))
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'log.cpp';exe=Path(tmp)/'log';cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Wformat=2','-Werror',
            '-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
