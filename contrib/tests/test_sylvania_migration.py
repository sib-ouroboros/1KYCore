#!/usr/bin/env python3
"""Real release-database regression. ONLY a disposable local MySQL server."""
import gzip
import hashlib
import json
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


def test_generic_restoration(restore, registry, tables, label):
    entries = ','.join(map(str, registry['entries']))
    guids = ','.join(str(row['guid']) for row in registry['spawns'])
    first = registry['spawns'][0]
    # The original migration removed these invalid spawns; restore a small
    # verified generic-only group, protecting both ownership and custom data.
    assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == '0'
    assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN ({guids});').stdout.strip() == '0'
    sql(f"INSERT INTO gameobject(guid,id,map,position_x) VALUES ({first['guid']},9000010,1,99);")
    before = checksum(tables)
    failure = sql(restore, ok=False)
    assert '_1kycore_generic_guard' in failure.stderr and 'Duplicate entry' in failure.stderr, failure.stderr
    assert checksum(tables) == before, 'Generic GUID rejection modified data'
    sql(f"DELETE FROM gameobject WHERE guid={first['guid']};")
    assert sql(f'SELECT COUNT(*) FROM gameobject_template_addon WHERE entry IN ({entries});').stdout.strip() == '0', 'Unexpected original addon dependency'
    assert sql(f'SELECT COUNT(*) FROM gameobject_questitem WHERE GameObjectEntry IN ({entries});').stdout.strip() == '0', 'Unexpected original quest-item dependency'
    # Orphaned addon/quest-item data must not acquire a new meaning silently.
    orphan = registry['entries'][0]
    existing_addon = sql(f'SELECT * FROM gameobject_template_addon WHERE entry={orphan};').stdout
    assert not existing_addon, 'Fixture requires no original addon'
    sql(f'INSERT INTO gameobject_template_addon(entry,flags) VALUES ({orphan},1);')
    before = checksum(tables)
    assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
    assert checksum(tables) == before, 'Orphan addon rejection modified data'
    sql(f'DELETE FROM gameobject_template_addon WHERE entry={orphan};')
    assert not sql(f'SELECT * FROM gameobject_questitem WHERE GameObjectEntry={orphan};').stdout
    sql(f'INSERT INTO gameobject_questitem(GameObjectEntry,Idx,ItemId) VALUES ({orphan},0,6948);')
    before = checksum(tables)
    assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
    assert checksum(tables) == before, 'Orphan quest item rejection modified data'
    sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={orphan};')
    sql(f"INSERT INTO gameobject_template(entry,type,name) VALUES ({orphan},3,'Custom chest');")
    before = checksum(tables)
    assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
    assert checksum(tables) == before, 'Incompatible template rejection modified data'
    compatible = next((t for t in registry.get('templates', []) if int(t['entry']) == orphan), None)
    fields = ['type'] + ['Data'+str(i) for i in range(33)]
    compatible = compatible or {'type': '5'}
    assignments = ','.join('`'+k+'`='+compatible.get(k, '0') for k in fields)
    sql(f'UPDATE gameobject_template SET {assignments} WHERE entry={orphan};')
    # Matching type alone is insufficient: reject altered behavior and scripts.
    original = sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout
    for alteration in ('Data32=99', "ScriptName='custom_script'", "AIName='SmartGameObjectAI'"):
        sql(f'UPDATE gameobject_template SET {alteration} WHERE entry={orphan};')
        before = checksum(tables)
        assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
        assert checksum(tables) == before, 'Behavior conflict rejection modified data'
        sql(f"UPDATE gameobject_template SET {assignments},AIName='',ScriptName='' WHERE entry={orphan};")
        assert sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout == original
    original_template = sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout
    sql(f"INSERT INTO gameobject(guid,id,map,position_x) VALUES ({first['guid']},{first['id']},1,99);")
    original_spawn = sql(f"SELECT * FROM gameobject WHERE guid={first['guid']};").stdout
    protected_tables = [t for t in tables if t not in ('gameobject','gameobject_template')]
    protected = checksum(protected_tables)
    sql(restore)
    assert checksum(protected_tables) == protected, 'Restoration changed unrelated tables'
    assert sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout == original_template
    assert sql(f"SELECT * FROM gameobject WHERE guid={first['guid']};").stdout == original_spawn
    assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == str(len(registry['entries']))
    assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN ({guids});').stdout.strip() == str(len(registry['spawns']))
    if 'templates' in registry:
        expected_rows = []
        for template in registry['templates']:
            if int(template['entry']) == orphan:
                continue
            comparisons = []
            for key, value in template.items():
                # MySQL stores size as FLOAT; source decimal 0.65 is rounded to
                # binary32. Compare within single-precision rounding, not as an
                # exact decimal/double equality.
                if key == 'size':
                    comparisons.append(f'ABS(`size`-({value}))<=ABS({value})*0.0000001')
                else:
                    comparisons.append('`'+key+'`='+value)
            expected_rows.append('(' + ' AND '.join(comparisons) + ')')
        count = sql('SELECT COUNT(*) FROM gameobject_template WHERE ' + ' OR '.join(expected_rows) + ';').stdout.strip()
        assert count == str(len(expected_rows)), 'Source model/name/icon/size/build fields changed'
    complete = checksum(tables)
    sql(restore)
    assert checksum(tables) == complete, 'Repeated restoration changed data'
    # Reproduce interruption after templates, before restoring the spawns.
    sql(f'DELETE FROM gameobject_template WHERE entry IN ({entries}) AND entry<>{orphan};')
    sql(f"DELETE FROM gameobject WHERE guid IN ({guids}) AND guid<>{first['guid']};")
    boundary = restore.index('-- Restore exact imported spawns')
    sql(restore[:boundary])
    sql(restore)
    assert checksum(tables) == complete, 'Partial restoration retry differs'
    print('PASS: ' + label + ', repeated/partial restoration, custom data and conflict guards', flush=True)



def main():
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER') != '1':
        raise SystemExit('Requires MYSQL_DISPOSABLE_TEST_SERVER=1; never use a production server.')
    migration = (ROOT / 'sql/updates/world/2026_09_30_00_world_sylvania_content.sql').read_text('utf8')
    # Sources delimit complete statements, allowing an interruption at a real file boundary.
    split = migration.index('-- Source: sql/sylvania/campagne_mage_legioncore.sql')
    old = (ROOT / 'sql/updates/world/2026_09_28_00_world_1kycore_scenario_artifact.sql').read_text('utf8')
    cleanup = (ROOT / 'sql/updates/world/2026_09_29_00_world_remove_bot_tables.sql').read_text('utf8')
    restore = (ROOT / 'sql/updates/world/2026_10_01_00_world_campaign_generic_objects.sql').read_text('utf8')
    registry = json.loads((ROOT / 'docs/audit-data/campaign-generic-restoration.json').read_text('utf8'))

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

        test_generic_restoration(restore, registry, tables, 'six templates / 35 spawns')
        second = (ROOT / 'sql/updates/world/2026_10_01_02_world_campaign_generic_objects.sql').read_text('utf8')
        second_registry = json.loads((ROOT / 'docs/audit-data/campaign-generic-restoration-2.json').read_text('utf8'))
        test_generic_restoration(second, second_registry, tables, '36 templates / 116 spawns')
        third = (ROOT / 'sql/updates/world/2026_10_01_03_world_campaign_chairs_visibility.sql').read_text('utf8')
        third_registry = json.loads((ROOT / 'docs/audit-data/campaign-chairs-visibility-restoration.json').read_text('utf8'))
        test_generic_restoration(third, third_registry, tables, '21 templates / 62 spawns')

        sql('UPDATE creature SET id=9000002 WHERE guid=290300100;')
        collision = checksum(tables)
        failure = sql(migration, ok=False)
        assert 'Duplicate entry' in failure.stderr and '_1kycore_spawn_guard' in failure.stderr, failure.stderr
        assert checksum(tables) == collision, 'Collision rejection modified content'
        print('PASS: custom NPC GUID collision rejects before any content mutation', flush=True)
        command = (ROOT / 'sql/updates/world/2026_10_01_01_world_gilneas_attack_lurker.sql').read_text('utf8')
        sql("INSERT INTO spell_script_names (spell_id,ScriptName) VALUES (67805,'test_gilneas_custom');")
        previous = sql("SELECT * FROM spell_script_names ORDER BY spell_id,ScriptName;").stdout
        protected = checksum([table for table in tables if table != 'spell_script_names'])
        sql(command)
        assert sql("SELECT COUNT(*) FROM spell_script_names WHERE spell_id=67805 AND ScriptName='spell_gilneas_attack_lurker';").stdout.strip() == '1'
        retained = sql("SELECT * FROM spell_script_names WHERE ScriptName<>'spell_gilneas_attack_lurker' ORDER BY spell_id,ScriptName;").stdout
        assert retained == previous, 'Quest command overwrote unrelated spell bindings'
        assert checksum([table for table in tables if table != 'spell_script_names']) == protected
        complete = checksum(['spell_script_names'])
        sql(command)
        assert checksum(['spell_script_names']) == complete, 'Quest binding retry is not idempotent'
        print('PASS: Gilneas command binding first/repeat import preserves other scripts and all other tables', flush=True)
        sql(f'DROP DATABASE `{DB}`;', False)


if __name__ == '__main__':
    main()
