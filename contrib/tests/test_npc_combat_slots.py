#!/usr/bin/env python3
"""Compile actual CombatSlot, ObjectPosSelector and all chase/follow specializations.

Geometry/navmesh/unit interfaces are fixtures, not real server maps. Reported
timings measure helper CPU only; they are not world update or real MMAP results.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-sanitizers',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    fixtures=root/'contrib/tests/fixtures'
    movement=root/'src/server/game/Movement'
    objects=root/'src/server/game/Entities/Object'
    with tempfile.TemporaryDirectory(prefix='npc-combat-slots-') as temp:
        temp=Path(temp)
        (temp/'interfaces.h').write_bytes((fixtures/'crowd_test_interfaces.h').read_bytes())
        for name in ('Common','Creature','Unit','World','PathGenerator','MotionMaster','MoveSpline','Log',
                     'MovementGenerator','FollowerReference','Timer','ByteBuffer','Errors','CreatureAI',
                     'MoveSplineInit','Player','VehicleDefines'):
            (temp/(name+'.h')).write_text('#include "interfaces.h"\n',encoding='utf-8')
        for source in (movement/'CombatSlot.cpp', movement/'CombatSlot.h', objects/'ObjectPosSelector.cpp', objects/'ObjectPosSelector.h', movement/'MovementGenerators/TargetedMovementGenerator.cpp', movement/'MovementGenerators/TargetedMovementGenerator.h'):
            (temp/source.name).write_bytes(source.read_bytes())
        output=temp/('test.exe' if os.name=='nt' else 'test')
        command=[os.environ.get('CXX','g++'),'-std=c++17','-O2','-Wall','-Wextra','-Werror',
                 '-I'+str(temp),'-I'+str(movement),'-I'+str(movement/'MovementGenerators'),'-I'+str(objects),
                 str(temp/'CombatSlot.cpp'),str(temp/'ObjectPosSelector.cpp'),
                 str(temp/'TargetedMovementGenerator.cpp'),
                 str(fixtures/'crowd_test_main.cpp'),'-o',str(output)]
        if not args.no_sanitizers:
            command[1:1]=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie']
        subprocess.run(command,check=True)
        subprocess.run([str(output)],check=True,timeout=60)


if __name__=='__main__':
    main()
