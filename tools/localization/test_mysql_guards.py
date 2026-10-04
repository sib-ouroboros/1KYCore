#!/usr/bin/env python3
"""Synthetic native MyISAM/InnoDB guard regressions on a fixed scratch database."""
import argparse,os,subprocess,tempfile
from pathlib import Path
import test_localization as fixtures
from localize import analyse,packages,sql_value,equals

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mysql',required=True);p.add_argument('--port',required=True,type=int);a=p.parse_args()
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER')!='1' or a.port==3306:p.error('Explicit disposable server on a nondefault port required')
    db='test_1kycore_ru_guards'
    cmd=[a.mysql,'--no-defaults','--protocol=TCP','--host=127.0.0.1',f'--port={a.port}','--user=root','--default-character-set=utf8mb4','--batch','--raw','--skip-column-names']
    def run(sql,fail=False,database=True):
        r=subprocess.run(cmd+([db] if database else []),input=sql.encode('utf8'),capture_output=True)
        if fail:assert r.returncode and b'Duplicate entry' in r.stderr,r.stderr
        elif r.returncode:raise RuntimeError(r.stderr.decode('utf8'))
        return r.stdout
    run('CREATE DATABASE IF NOT EXISTS `'+db+'` CHARACTER SET utf8mb4;',database=False)
    for engine in ('MyISAM','InnoDB'):
        # Exact scratch-only names; DDL is a test fixture, never generated migration.
        run('DROP TABLE IF EXISTS texts_locale; DROP TABLE IF EXISTS texts;')
        run(f"CREATE TABLE texts (ID int PRIMARY KEY, Text text); CREATE TABLE texts_locale (ID int NOT NULL, locale varchar(4) NOT NULL, Text text DEFAULT NULL, Other text DEFAULT NULL, VerifiedBuild smallint DEFAULT 0, PRIMARY KEY(ID,locale)) ENGINE={engine}; INSERT INTO texts VALUES(1,'Text.');")
        target,source=fixtures.MatchingTests().fixture();_,changes,_=analyse(target,source,'fixture-sha',(fixtures.MatchingTests.rule,))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);packages(target,changes,out);apply=(out/'demo-001.apply.sql').read_text('utf8');undo=(out/'demo-001.rollback.sql').read_text('utf8')
            run("INSERT INTO texts_locale VALUES(1,'ruru','Чужой перевод.','foreign',99);")
            before=run('SELECT * FROM texts_locale;');run(apply,True);assert run('SELECT * FROM texts_locale;')==before
            run('DELETE FROM texts_locale;');run(apply);run(apply)
            run("UPDATE texts_locale SET Other='Чужой новый столбец.',VerifiedBuild=77;")
            before=run('SELECT * FROM texts_locale;');run(undo,True);assert run('SELECT * FROM texts_locale;')==before
            run('UPDATE texts_locale SET Other=NULL,VerifiedBuild=0;');run(undo);run(undo);assert run('SELECT * FROM texts_locale;')==b''
        # Existing NULL is not ''. Rollback leaves a later unowned field edit intact.
        target,source=fixtures.MatchingTests().fixture('');target['texts_locale'].rows[('1','ruRU')]['Text']=None
        _,changes,_=analyse(target,source,'fixture-sha',(fixtures.MatchingTests.rule,))
        run("INSERT INTO texts_locale VALUES(1,'ruRU',NULL,"+sql_value('Сохранить')+",42);")
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);packages(target,changes,out);apply=(out/'demo-001.apply.sql').read_text('utf8');undo=(out/'demo-001.rollback.sql').read_text('utf8')
            run("UPDATE texts_locale SET Text='';");run(apply,True)
            run('UPDATE texts_locale SET Text=NULL;');run(apply);run("UPDATE texts_locale SET Other='Later independent edit';");run(undo)
            assert run('SELECT Text IS NULL,Other,VerifiedBuild FROM texts_locale;').strip()==b'1\tLater independent edit\t42'
        print('PASS:',engine,'collation collision, exact inserted ownership, NULL vs empty, later unowned edits',flush=True)
if __name__=='__main__':main()
