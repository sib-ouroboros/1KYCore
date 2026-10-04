#!/usr/bin/env python3
"""Destructive package tests ONLY on an explicitly enabled disposable localhost DB.

Never imports donor SQL. User creates the disposable baseline first. Reads generated
manifest, verifies SQL hashes, checks every table, and leaves baseline restored.
"""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
from localize import digest,equals,sql_value

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mysql',required=True);p.add_argument('--port',required=True,type=int)
    p.add_argument('--database',required=True);p.add_argument('--packages',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--report',required=True)
    a=p.parse_args()
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER')!='1' or not re.fullmatch(r'(ru_target|ru_hotfix_target|test_1kycore_ru_[a-z0-9_]+)',a.database) or a.port==3306:
        p.error('Require MYSQL_DISPOSABLE_TEST_SERVER=1, scratch database name and nondefault port')
    cmd=[a.mysql,'--no-defaults','--protocol=TCP','--host=127.0.0.1',f'--port={a.port}','--user=root','--default-character-set=utf8mb4','--max-allowed-packet=1G','--batch','--raw','--skip-column-names',a.database]
    def run(sql,fail=False):
        r=subprocess.run(cmd,input=sql.encode('utf8') if isinstance(sql,str) else sql,capture_output=True)
        if fail:
            assert r.returncode and b'Duplicate entry' in r.stderr,(r.returncode,r.stderr[:1000])
        elif r.returncode:raise RuntimeError(r.stderr.decode('utf8',errors='replace'))
        return r.stdout.decode('utf8')
    names=run('SHOW TABLES;').splitlines()
    assert all(re.fullmatch(r'[a-zA-Z0-9_]+',s) for s in names)
    def checksums():
        rows=run('CHECKSUM TABLE '+','.join('`'+t+'`' for t in names)+' EXTENDED;').splitlines()
        data=dict(row.split('\t') for row in rows)
        assert all(v!='NULL' for v in data.values()),'Unsupported table checksum'
        return data
    manifests=json.loads(Path(a.manifest).read_text('utf8'))
    patchdir=Path(a.packages)
    for m in manifests:
        assert re.fullmatch(r'[a-z_]+-[0-9]{3,}',m['name'])
        for mode in ('apply','rollback'):
            assert hashlib.sha256((patchdir/(m['name']+'.'+mode+'.sql')).read_bytes()).hexdigest()==m[mode+'_sha256']
    tables=sorted({m['table'] for m in manifests})
    columns={t:run(f'SHOW COLUMNS FROM `{t}`;').splitlines() for t in tables}
    columns={t:[line.split('\t')[0] for line in rows] for t,rows in columns.items()}
    primary={t:run(f"SELECT COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{t}' AND CONSTRAINT_NAME='PRIMARY' ORDER BY ORDINAL_POSITION;").splitlines() for t in tables}
    def snapshot(t):
        args=','.join(sql_value(c)+',`'+c+'`' for c in columns[t])
        rows=[json.loads(s) for s in run(f'SELECT JSON_OBJECT({args}) FROM `{t}` ORDER BY '+','.join('`'+k+'`' for k in primary[t])+';').splitlines()]
        return {tuple(None if r[k] is None else str(r[k]) for k in primary[t]):{k:None if v is None else str(v) for k,v in r.items()} for r in rows}
    initial=checksums();before={t:snapshot(t) for t in tables}
    print('Baseline captured:',len(names),'tables,',len(manifests),'packages',flush=True)
    def execute(m,mode):run((patchdir/(m['name']+'.'+mode+'.sql')).read_bytes())
    # Generation-time stale target must stop before any permanent writes.
    m=next((m for m in manifests if any(not e['inserted'] for e in m['evidence'])),manifests[0])
    e=next((e for e in m['evidence'] if not e['inserted']),None)
    stale=False
    if e:
        field=next(iter(e['before']));where=equals(e['key']);old=e['before'][field]
        run(f"UPDATE `{m['table']}` SET `{field}`={sql_value('Чужая правка после генерации.')} WHERE {where};")
        fixture=checksums();run((patchdir/(m['name']+'.apply.sql')).read_bytes(),fail=True);assert checksums()==fixture
        run(f"UPDATE `{m['table']}` SET `{field}`={sql_value(old)} WHERE {where};");assert checksums()==initial;stale=True
    for i,m in enumerate(manifests):
        execute(m,'apply')
        if (i+1)%25==0:print('Applied',i+1,flush=True)
    applied=checksums();after={t:snapshot(t) for t in tables}
    for t in names:
        if t not in tables:assert initial[a.database+'.'+t]==applied[a.database+'.'+t],('Unrelated table changed',t)
    expected={t:dict(rows) for t,rows in before.items()}
    for m in manifests:
        t=m['table']
        for e in m['evidence']:
            key=tuple(e['key'][k] for k in primary[t]);actual=after[t][key]
            if e['inserted']:
                assert key not in before[t] and digest(actual)==e['row_after_sha256'],('Inserted row mismatch',t,key)
                expected[t][key]=actual
            else:
                original=before[t][key]
                assert {k:v for k,v in original.items() if k not in e['before']}=={k:v for k,v in actual.items() if k not in e['before']},('Untouched fields changed',t,key)
                assert all(digest(actual[f])==h for f,h in e['after_hashes'].items())
                expected[t][key]=dict(original,**{f:actual[f] for f in e['before']})
    assert expected==after,'Other locales/unapproved rows changed'
    for m in manifests:execute(m,'apply')
    assert checksums()==applied,'Repeat apply changed data'
    # Rollback-time foreign edit must remain untouched; guard checks whole batch.
    m=manifests[0];e=m['evidence'][0];field=next(iter(e['before']));where=equals(e['key']);value=after[m['table']][tuple(e['key'][k] for k in primary[m['table']])][field]
    run(f"UPDATE `{m['table']}` SET `{field}`={sql_value('Чужая правка после применения.')} WHERE {where};")
    fixture=checksums();run((patchdir/(m['name']+'.rollback.sql')).read_bytes(),fail=True);assert checksums()==fixture
    run(f"UPDATE `{m['table']}` SET `{field}`={sql_value(value)} WHERE {where};");assert checksums()==applied
    for m in reversed(manifests):execute(m,'rollback')
    assert checksums()==initial,'Rollback did not restore every original table'
    for m in reversed(manifests):execute(m,'rollback')
    assert checksums()==initial,'Repeat rollback changed data'
    # Simulate interruption after the first permanent write; retry must recover.
    m=manifests[0];text=(patchdir/(m['name']+'.apply.sql')).read_text('utf8');lines=text.splitlines(True)
    write=next(i for i,line in enumerate(lines) if re.match(r'(INSERT INTO|UPDATE) `(?!_1kycore_ru_localization_guard)',line))
    run(''.join(lines[:write+1]));execute(m,'apply');execute(m,'rollback');assert checksums()==initial
    report={'database':a.database,'mysql_version':run('SELECT VERSION();').strip(),'tables_checked':len(names),'packages':len(manifests),'fields':sum(m['fields'] for m in manifests),'all_apply':'PASS','only_allowlisted_fields_and_owned_rows':'PASS','other_locales_and_gameplay_tables':'PASS','repeat_apply':'PASS','stale_apply':('PASS' if stale else 'not exercised: no updated rows'),'stale_rollback':'PASS','exact_full_database_rollback':'PASS','repeat_rollback':'PASS','partial_apply_retry':'PASS','baseline_checksums':initial,'restored_checksums':checksums()}
    Path(a.report).write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print('PASS:',json.dumps({k:v for k,v in report.items() if not k.endswith('checksums')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
