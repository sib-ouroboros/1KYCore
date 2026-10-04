#!/usr/bin/env python3
"""Deterministic optional SQL bundles, offline verified extraction and text review."""
import argparse,gzip,hashlib,json,re
from pathlib import Path
from rules import RULES,HOTFIX_RULES,POI_RULES

TABLES={r.target for r in RULES+HOTFIX_RULES+POI_RULES}|{'gossip_menu_option_locale'}
def sha(data):return hashlib.sha256(data).hexdigest()
def write_gzip(path,data):
    with path.open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9) as f:f.write(data)
def json_bytes(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def valid(manifest):
    names=set()
    for m in manifest:
        if not re.fullmatch(r'[a-z_]+-[0-9]{3,}',m['name']) or m['name'] in names or m['table'] not in TABLES:raise ValueError('Unknown/duplicate package or destination table')
        names.add(m['name'])
def pack(src,out):
    manifest=json.loads((src/'manifest.json').read_text('utf8'));valid(manifest)
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Bundle output must be empty')
    catalog=[]
    for m in manifest:
        for mode in ('apply','rollback'):
            name=m['name']+'.'+mode+'.sql';data=(src/'packages'/name).read_bytes()
            if sha(data)!=m[mode+'_sha256']:raise ValueError('SQL hash mismatch')
            dest=out/(name+'.gz');write_gzip(dest,data)
            catalog.append({'file':dest.name,'sql_sha256':sha(data),'gzip_sha256':sha(dest.read_bytes()),'sql_bytes':len(data)})
    write_gzip(out/'manifest.json.gz',json_bytes(manifest))
    records=json.loads((src/'candidates.json').read_text('utf8'))
    accepted=[r for r in records if r['status']=='automatic']
    write_gzip(out/'accepted-fields.jsonl.gz',b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n').encode('utf8') for r in accepted))
    queue=[];counts={}
    for r in records:
        if r['status']=='automatic':continue
        key=(r['category'],r['status'],r['reason']);counts[key]=counts.get(key,0)+1
        if counts[key]<=2:queue.append(r)
    (out/'queue-samples.json').write_bytes(json_bytes({'scope':'Two samples per category/status/reason. Reproduce complete JSON/CSV with localize.py. No silent deletion of candidates.','counts':[{'category':k[0],'status':k[1],'reason':k[2],'fields_or_absent_rows':v} for k,v in sorted(counts.items())],'samples':queue}))
    (out/'summary.json').write_bytes(json_bytes(json.loads((src/'summary.json').read_text('utf8'))))
    if (src/'mysql-test.json').exists():
        test=json.loads((src/'mysql-test.json').read_text('utf8'))
        checksums={k:test.pop(k) for k in list(test) if k.endswith('checksums')}
        write_gzip(out/'database-checksums.json.gz',json_bytes(checksums))
        (out/'test-result.json').write_bytes(json_bytes(test))
    integrity={p.name:sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
    (out/'catalog.json').write_bytes(json_bytes({'format':1,'packages':catalog,'files_sha256':integrity}))
    print('Packed',len(manifest),'packages;',sum(p.stat().st_size for p in out.iterdir()),'bytes')
def extract(bundle,out):
    catalog=json.loads((bundle/'catalog.json').read_text('utf8'))
    for name,want in catalog['files_sha256'].items():
        if Path(name).name!=name or not re.fullmatch(r'[a-zA-Z0-9_.-]+',name):raise ValueError('Unsafe bundle filename')
        if sha((bundle/name).read_bytes())!=want:raise ValueError('Bundle integrity mismatch: '+name)
    manifest=json.loads(gzip.decompress((bundle/'manifest.json.gz').read_bytes()));valid(manifest)
    expected={m['name']+'.'+s+'.sql.gz':m[s+'_sha256'] for m in manifest for s in ('apply','rollback')}
    if set(expected)!={r['file'] for r in catalog['packages']}:raise ValueError('Incomplete SQL catalog')
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Extract output must be empty')
    for r in catalog['packages']:
        name=r['file'];size=r['sql_bytes']
        if not isinstance(size,int) or not 0<size<=100_000_000:raise ValueError('Invalid SQL size')
        with gzip.open(bundle/name,'rb') as f:
            data=f.read(size+1)
        if len(data)!=size or sha(data)!=expected[name] or sha(data)!=r['sql_sha256']:raise ValueError('Uncompressed SQL mismatch')
        (out/name[:-3]).write_bytes(data)
    (out/'manifest.json').write_bytes(json_bytes(manifest))
    print('Verified/extracted',len(expected),'SQL files. No database accessed.')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for cmd in ('pack','extract'):
        q=sub.add_parser(cmd);q.add_argument('--input',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('inspect');q.add_argument('--input',type=Path,required=True);q.add_argument('--category');q.add_argument('--limit',type=int,default=10)
    a=p.parse_args()
    try:
        if a.command=='pack':pack(a.input,a.output)
        elif a.command=='extract':extract(a.input,a.output)
        else:
            count=0
            with gzip.open(a.input/'accepted-fields.jsonl.gz','rt',encoding='utf8') as f:
                for line in f:
                    row=json.loads(line)
                    if a.category and row['category']!=a.category:continue
                    print(json.dumps(row,ensure_ascii=False,indent=2));count+=1
                    if count>=a.limit:break
    except (OSError,ValueError,KeyError) as e:p.exit(1,'ERROR: '+str(e)+'\n')
if __name__=='__main__':main()
