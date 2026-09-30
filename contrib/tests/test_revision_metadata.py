#!/usr/bin/env python3
"""Exercise real genrev.cmake in full/tagless/shallow/detached/dirty/archive fixtures."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def run(args,cwd=None):
    p=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stdout+p.stderr)
    return p.stdout.strip()


def main():
    root=Path(__file__).resolve().parents[2]
    git=shutil.which('git');cmake=shutil.which('cmake')
    assert git and cmake,'Git and CMake are required'
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        def files(path):
            path.mkdir()
            shutil.copyfile(root/'cmake/genrev.cmake',path/'genrev.cmake')
            shutil.copyfile(root/'revision_data.h.in.cmake',path/'revision_data.h.in.cmake')
            (path/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(RevisionTest NONE)\nfind_package(Git REQUIRED)\ninclude(genrev.cmake)\n',encoding='utf8')
        def configure(path,archive=False):
            build=tmp/(path.name+'-build')
            run([cmake,'-S',str(path),'-B',str(build),'-DWITHOUT_GIT='+('ON' if archive else 'OFF')])
            text=(build/'revision_data.h').read_text('utf8')
            return {key:re.search(r'#define _'+key+r'\s+"([^"]+)"',text)[1] for key in ['HASH','DATE','BRANCH']}
        def expected(path,branch,dirty=False):
            actual=configure(path)
            assert actual['HASH']==run([git,'rev-parse','--short=12','HEAD'],path)+('+' if dirty else ''),actual
            assert actual['DATE']==run([git,'show','-s','--format=%ci','HEAD'],path),actual
            assert actual['BRANCH']==branch,actual
        src=tmp/'tagless';files(src)
        run([git,'init','-b','main'],src)
        run([git,'config','user.name','Revision regression'],src)
        run([git,'config','user.email','revision-test@example.invalid'],src)
        run([git,'add','.'],src);run([git,'commit','-m','Initial fixture'],src)
        expected(src,'main')
        run([git,'tag','-a','init','-m','Legacy init tag'],src);expected(src,'main')
        tracked=src/'tracked.txt';tracked.write_text('first\n',encoding='utf8')
        run([git,'add','tracked.txt'],src);run([git,'commit','-m','After init'],src);expected(src,'main')
        tracked.write_text('dirty content\n',encoding='utf8');expected(src,'main',True)
        run([git,'checkout','--','tracked.txt'],src);expected(src,'main')
        shallow=tmp/'shallow'
        run([git,'clone','--depth','1','--no-tags',src.as_uri(),str(shallow)])
        expected(shallow,'main')
        run([git,'checkout','--detach','HEAD'],shallow);expected(shallow,'HEAD')
        archive=tmp/'archive';files(archive)
        for disabled in [False,True]:
            meta=configure(archive,disabled)
            assert meta=={'HASH':'unknown','DATE':'1970-01-01 00:00:00 +0000','BRANCH':'Archived'},meta
        print('PASS: tagless, init-tagged, cached clean/dirty, shallow, detached and archived revision metadata')


if __name__=='__main__':main()
