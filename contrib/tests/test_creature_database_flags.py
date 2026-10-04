#!/usr/bin/env python3
"""Test actual DB-only flag sanitizer and preserve legitimate unrelated flags."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
from test_map_active_lifetime import block

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];source=(root/'src/server/game/Globals/ObjectMgr.cpp').read_text('latin1')
 helper=block(source,'static uint32 SanitizeCreatureDatabaseUnitFlags(')
 assert 'SanitizeCreatureDatabaseUnitFlags(cInfo->unit_flags)' in block(source,'void ObjectMgr::CheckCreatureTemplate(')
 assert 'SanitizeCreatureDatabaseUnitFlags(data.unit_flags)' in block(source,'void ObjectMgr::LoadCreatures()')
 defines=(root/'src/server/game/Entities/Unit/UnitDefines.h').read_text('latin1')
 import re
 flags=['UNIT_FLAG_PVP_ATTACKABLE','UNIT_FLAG_RENAME','UNIT_FLAG_SKINNABLE']
 definitions='\n'.join('constexpr uint32 '+f+' = '+re.search(r'\b'+f+r'\s*=\s*(0x[0-9A-Fa-f]+)',defines)[1]+';' for f in flags)
 code='''#include <cstdint>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;
DEFINITIONS
HELPER
int main(){uint32 mask=UNIT_FLAG_PVP_ATTACKABLE|UNIT_FLAG_RENAME|UNIT_FLAG_SKINNABLE;
 for(uint32 bit=1;bit;bit<<=1){uint32 expected=bit&~mask;if(SanitizeCreatureDatabaseUnitFlags(bit)!=expected)throw std::runtime_error("unexpected flag change");}
 if(SanitizeCreatureDatabaseUnitFlags(0xffffffff)!=~mask)throw std::runtime_error("combined flags");
 uint32 live=SanitizeCreatureDatabaseUnitFlags(mask);live|=UNIT_FLAG_SKINNABLE;
 if(!(live&UNIT_FLAG_SKINNABLE))throw std::runtime_error("runtime skinning remains available");
 std::cout<<"PASS: native sanitizer clears only 0x8, 0x10 and corpse skinning DB flags\\n";}
'''.replace('DEFINITIONS',definitions).replace('HELPER',helper)
 with tempfile.TemporaryDirectory(prefix='creature-db-flags-') as tmp:
  tmp=Path(tmp);p=tmp/'test.cpp';p.write_text(code,encoding='utf-8');output=tmp/('test.exe' if os.name=='nt' else 'test')
  command=[os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',str(p),'-o',str(output)]
  if not args.no_sanitizers:command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
  subprocess.run(command,check=True);subprocess.run([str(output)],check=True)
if __name__=='__main__':main()
