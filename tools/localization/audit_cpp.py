#!/usr/bin/env python3
"""Read-only heuristic queue of visible C++ literals; not an AST or automatic translator."""
import argparse,json,re
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    calls=re.compile(r'\b(AddGossipItemFor|AddMenuItem|SendSysMessage|PSendSysMessage|SendNotification|Talk|MonsterSay|MonsterYell)\s*\(')
    literal=re.compile(r'"((?:\\.|[^"\\])*)"')
    records=[]
    for path in sorted((a.root/'src/server').rglob('*.cpp')):
        data=path.read_bytes()
        try:text=data.decode('utf8');encoding='utf8'
        except UnicodeError:text=data.decode('cp1251');encoding='cp1251'
        for n,line in enumerate(text.splitlines(),1):
            if match:=calls.search(line):
                strings=literal.findall(line[match.start():])
                if strings:records.append({'file':path.relative_to(a.root).as_posix(),'line':n,'call':match.group(1),'literals':strings,'encoding':encoding,'status':'manual_review','reason':'heuristic visible-call literal; semantic/source/formatter review required'})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(records,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8');print(len(records),'candidate call sites; no changes')
if __name__=='__main__':main()
