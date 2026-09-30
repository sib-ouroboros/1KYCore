#!/usr/bin/env python3
"""Real release-database regression. ONLY a disposable local MySQL server."""
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DB = 'test_1kycore_sylvania_release'
ASSET = '1kycore_world_20260926_no_mercenaries.sql.gz'
SHA = 'b311837633e148df178045fd448cbaeb7e40d10b97690377866ce4560f68bac7'
URL = 'https://github.com/sib-ouroboros/1KYCore/releases/download/db-sylvania-20260926-no-mercenaries-r1/' + ASSET
MYSQL = ['mysql', '--protocol=TCP', '-h127.0.0.1', '-P3306', '-uroot',
         '--batch', '--skip-column-names', '--default-character-set=utf8mb4', '--max-allowed-packet=1G']


def sql(text, database=True, ok=True):
    p = subprocess.run(MYSQL + ([DB] if database else []), input=text, text=True, capture_output=True)
    if ok and p.returncode:
        raise RuntimeError(p.stderr[-6000:])
    if not ok and not p.returncode:
        raise AssertionError('Expected a GUID collision to reject the migration')
    return p


def checksum(tables):
    return sql('CHECKSUM TABLE ' + ','.join('`'+t+'`' for t in tables) + ' EXTENDED;').stdout


def main():
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER') != '1':
        raise SystemExit('Requires MYSQL_DISPOSABLE_TEST_SERVER=1; never use a production server.')
    migration = (ROOT / 'sql/updates/world/2026_09_30_00_world_sylvania_content.sql').read_text('utf8')
    # Sources delimit complete statements, allowing an interruption at a real file boundary.
    split = migration.index('-- Source: sql/sylvania/campagne_mage_legioncore.sql')
    old = (ROOT / 'sql/updates/world/2026_09_28_00_world_1kycore_scenario_artifact.sql').read_text('utf8')
    cleanup = (ROOT / 'sql/updates/world/2026_09_29_00_world_remove_bot_tables.sql').read_text('utf8')
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / ASSET
        urllib.request.urlretrieve(URL, archive)
        assert hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() == SHA, 'Release checksum changed'

        def reset():
            sql(f'DROP DATABASE IF EXISTS `{DB}`; CREATE DATABASE `{DB}` CHARACTER SET utf8mb4;', False)
            with gzip.open(archive, 'rb') as source:
                p = subprocess.Popen(MYSQL + [DB], stdin=subprocess.PIPE)
                try:
                    shutil.copyfileobj(source, p.stdin, length=1024*1024)
                finally:
                    p.stdin.close()
                assert p.wait() == 0, 'Release import failed'
            sql(old + '\n' + cleanup)
            # Neither the old wide GUID delete nor missing-template cleanup may touch these.
            sql("INSERT INTO gameobject (guid,id,map,position_x,position_y,position_z,orientation) VALUES "
                "(4290000000,9000000,1,1,2,3,0),(210300260,9000001,1,4,5,6,0);")

        reset()
        tables = sql('SHOW TABLES;').stdout.splitlines()
        changed = set(re.findall(r'(?:UPDATE|INSERT INTO|DELETE FROM)\s+`?(\w+)', migration, re.I))
        changed |= {'creature', 'gameobject'}  # aliased DELETE statements
        untouched = [t for t in tables if t not in changed]
        protected = checksum(untouched)
        custom = sql('SELECT * FROM gameobject WHERE guid IN (4290000000,210300260) ORDER BY guid;').stdout
        sql(migration)
        assert checksum(untouched) == protected, 'Unrelated table changed'
        assert sql('SELECT * FROM gameobject WHERE guid IN (4290000000,210300260) ORDER BY guid;').stdout == custom
        canonical = checksum(tables)
        sql(migration)
        assert checksum(tables) == canonical, 'Second application changed data'
        assert sql('SELECT COUNT(*) FROM gameobject WHERE guid=210300217 AND id=1000203;').stdout.strip() == '1'
        assert sql('SELECT COUNT(*) FROM gameobject WHERE guid BETWEEN 210300200 AND 210300210 AND id IN (1000200,1000201);').stdout.strip() == '0'
        print('PASS: real release import, prior migrations, first application, repeat, custom data', flush=True)

        reset()
        sql(migration[:split])
        sql(migration)
        assert checksum(tables) == canonical, 'Recovery after partial application differs'
        print('PASS: partial application followed by full retry', flush=True)

        sql('UPDATE creature SET id=9000002 WHERE guid=290300100;')
        collision = checksum(tables)
        failure = sql(migration, ok=False)
        assert 'Duplicate entry' in failure.stderr and '_1kycore_spawn_guard' in failure.stderr, failure.stderr
        assert checksum(tables) == collision, 'Collision rejection modified content'
        print('PASS: custom NPC GUID collision rejects before any content mutation', flush=True)
        sql(f'DROP DATABASE `{DB}`;', False)


if __name__ == '__main__':
    main()
