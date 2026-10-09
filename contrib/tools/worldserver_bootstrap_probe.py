#!/usr/bin/env python3
"""Run an explicitly isolated Linux server, capture ready/shutdown and audit exit.

Does not create, reset or delete databases. Use a fresh dedicated audit DB set.
Config credentials are never printed. Rejects production-like config before exec.
"""
import argparse
import os
from pathlib import Path
import queue,re,subprocess,threading,time,json
from worldserver_log_audit import audit


def check_config(text):
    if re.search(r'^\s*\[|^\s*(?:include|Include)\s*[= ]',text,re.M):
        raise ValueError('Includes/sections unsupported: provide a self-contained audit config')
    values={}
    for line in text.splitlines():
        if line.strip().startswith('#') or '=' not in line:continue
        key,value=line.split('=',1);key=key.strip()
        if key in values:raise ValueError('Duplicate config key: '+key)
        values[key]=value.strip().strip('"')
    names=[]
    for key in ('LoginDatabaseInfo','WorldDatabaseInfo','CharacterDatabaseInfo','HotfixDatabaseInfo','ShopDatabaseInfo'):
        parts=values.get(key,'').split(';')
        if len(parts)!=5 or parts[0] not in ('127.0.0.1','localhost','::1') or not re.fullmatch(r'1kycore_audit_[a-z0-9_]+',parts[4]):
            raise ValueError('Every DB must use localhost and a distinct 1kycore_audit_ name')
        names.append(parts[4])
    if len(set(names))!=5:raise ValueError('Five distinct database names required')
    if values.get('BindIP')!='127.0.0.1' or values.get('Console.Enable')!='1':
        raise ValueError('Require BindIP=127.0.0.1 and Console.Enable=1')
    for key in ('Ra.Enable','SOAP.Enabled','WorldREST.Enabled'):
        if values.get(key)!='0':raise ValueError('Explicitly disable '+key)
    port=int(values.get('WorldServerPort','0'))
    if not 1024<=port<=65535 or port==8085:raise ValueError('Choose a nondefault audit world port')
    instance_port=int(values.get('InstanceServerPort','0'))
    if not 1024<=instance_port<=65535 or instance_port in (8086,port):raise ValueError('Choose a distinct nondefault audit instance port')
    return names


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--server',type=Path,required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--startup-timeout',type=int,default=600);p.add_argument('--shutdown-timeout',type=int,default=120);p.add_argument('--gdb',action='store_true');p.add_argument('--allowlist',type=Path)
    a=p.parse_args()
    if os.name!='posix':p.error('Linux probe required; Windows is not equivalent to the reported crash')
    if a.startup_timeout<=0 or a.shutdown_timeout<=0:p.error('Timeouts must be positive')
    check_config(a.config.read_text('utf8'))
    a.output_dir.mkdir(parents=True,exist_ok=True)
    log_path=a.output_dir/'worldserver.log';command=[str(a.server.resolve()),'-c',str(a.config.resolve())]
    if a.gdb:command=['gdb','--batch','-ex','set pagination off','-ex','run','-ex','thread apply all bt full','--args',*command]
    env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=1:halt_on_error=1:abort_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
    process=subprocess.Popen(command,cwd=a.server.resolve().parent,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf8',errors='replace',bufsize=1,env=env,start_new_session=True)
    messages=queue.Queue()
    def reader():
        for line in process.stdout:messages.put(line)
        messages.put(None)
    thread=threading.Thread(target=reader,daemon=True);thread.start();deadline=time.monotonic()+a.startup_timeout;ready=False;timed_out=False;lines=[]
    try:
        with log_path.open('w',encoding='utf8') as out:
            while True:
                if time.monotonic()>=deadline:
                    timed_out=True;break
                try:line=messages.get(timeout=0.25)
                except queue.Empty:continue
                if line is None:break
                lines.append(line);out.write(line);out.flush()
                if not ready and re.search(r'worldserver-daemon\) ready',line):
                    ready=True;process.stdin.write('server shutdown 1\n');process.stdin.flush()
                    lines.append('server shutdown 1\n');out.write('server shutdown 1\n');out.flush();deadline=time.monotonic()+a.shutdown_timeout
            if timed_out:
                import signal
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL)
            process.wait(timeout=15);thread.join(timeout=5)
            while not messages.empty():
                line=messages.get_nowait()
                if line is not None:lines.append(line);out.write(line)
    finally:
        if process.poll() is None:
            import signal
            os.killpg(process.pid,signal.SIGKILL);process.wait()
        process.stdin.close();process.stdout.close()
    text=''.join(lines);exit_code=process.returncode
    if a.gdb and 'exited normally' not in text:exit_code=1
    report=audit(text,json.loads(a.allowlist.read_text('utf8')) if a.allowlist else [],exit_code)
    report['probe_timed_out']=timed_out;report['gdb_mode']=a.gdb
    report['empty_database_bootstrap_verified']=False
    report['config_sha256']=__import__('hashlib').sha256(a.config.read_bytes()).hexdigest()
    if timed_out:report['acceptance']='FAIL'
    (a.output_dir/'audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps({'acceptance':report['acceptance'],'exit_code':exit_code,'ready':ready,'timed_out':timed_out}))
    return int(report['acceptance']!='PASS')


if __name__=='__main__':raise SystemExit(main())
