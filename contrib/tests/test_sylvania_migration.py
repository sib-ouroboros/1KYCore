#!/usr/bin/env python3
"""Real release-database regression. ONLY a disposable local MySQL server."""
import argparse
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

from test_gilneas_database import test_gilneas_database
from test_campaign_visual_migration import test_visual_migration
from test_campaign_required_level_migration import test_required_level_objects
from test_campaign_packed_conversations import test_packed_conversations
from test_campaign_cage_states import test_cage_state_restoration

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
        raise AssertionError('Expected a conflict to reject the migration')
    return p


def checksum(tables):
    return sql('CHECKSUM TABLE ' + ','.join('`'+t+'`' for t in tables) + ' EXTENDED;').stdout


def test_generic_restoration(restore, registry, tables, label):
    entries = ','.join(map(str, registry['entries']))
    guids = ','.join(str(row['guid']) for row in registry['spawns'])
    first = registry['spawns'][0]
    # The original migration removed these invalid spawns; restore a small
    # verified native-object group, protecting both ownership and custom data.
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
    # A missing page is restored atomically with respect to conflict checks.
    # Keep matching pages and every unrelated page unchanged.
    pages = registry.get('pages', [])
    original_pages = None
    if pages:
        assert len(pages) == 1
        page = pages[0]
        page_id = int(page['ID'])
        assert not sql(f'SELECT * FROM page_text WHERE ID={page_id};').stdout
        assert not sql(f'SELECT * FROM page_text_locale WHERE ID={page_id};').stdout
        sql(f"INSERT INTO page_text_locale(ID,locale,Text) VALUES ({page_id},'ruRU','orphan custom page');")
        before = checksum(tables)
        failure = sql(restore, ok=False)
        assert '_1kycore_generic_guard' in failure.stderr, failure.stderr
        assert checksum(tables) == before, 'Orphan page translation modified permanent data'
        sql(f'DELETE FROM page_text_locale WHERE ID={page_id};')
        columns = ','.join('`'+k+'`' for k in page)
        sql(f"INSERT INTO page_text ({columns}) VALUES ({','.join(page.values())});")
        page_assignments = ','.join('`'+k+'`='+v for k,v in page.items() if k != 'ID')
        original_page = sql(f'SELECT * FROM page_text WHERE ID={page_id};').stdout
        for alteration in ("Text='custom page'", 'Text=NULL', 'NextPageID=5121', 'PlayerConditionID=1', 'Flags=0', 'VerifiedBuild=0'):
            sql(f'UPDATE page_text SET {alteration} WHERE ID={page_id};')
            before = checksum(tables)
            failure = sql(restore, ok=False)
            assert '_1kycore_generic_guard' in failure.stderr, failure.stderr
            assert checksum(tables) == before, 'Page conflict modified permanent data'
            sql(f'UPDATE page_text SET {page_assignments} WHERE ID={page_id};')
            assert sql(f'SELECT * FROM page_text WHERE ID={page_id};').stdout == original_page
        original_pages = sql('SELECT * FROM page_text ORDER BY ID;').stdout
    destinations = registry.get('destinations', [])
    original_destinations = {}
    unrelated_destinations = None
    if destinations:
        selected = ' OR '.join(f"(ID={row['ID']} AND EffectIndex={row['EffectIndex']})" for row in destinations)
        for row in destinations:
            where = f"ID={row['ID']} AND EffectIndex={row['EffectIndex']}"
            original_destinations[(row['ID'],row['EffectIndex'])] = sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout
        probe = destinations[0]
        where = f"ID={probe['ID']} AND EffectIndex={probe['EffectIndex']}"
        assert original_destinations[(probe['ID'],probe['EffectIndex'])], 'Fixture requires original route'
        for field in ('MapID','PositionX','PositionY','PositionZ'):
            sql(f'UPDATE spell_target_position SET `{field}`={probe[field]}+10 WHERE '+where+';')
            before = checksum(tables)
            failure = sql(restore, ok=False)
            assert '_1kycore_generic_guard' in failure.stderr, failure.stderr
            assert checksum(tables) == before, 'Destination conflict changed permanent data'
            sql(f'UPDATE spell_target_position SET `{field}`={probe[field]} WHERE '+where+';')
            assert sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout == original_destinations[(probe['ID'],probe['EffectIndex'])]
        # VerifiedBuild is provenance, not a reason to overwrite a valid route.
        sql('UPDATE spell_target_position SET VerifiedBuild=12345 WHERE '+where+';')
        original_destinations[(probe['ID'],probe['EffectIndex'])] = sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout
        # Other effects of the same spell belong to administrators as well.
        sql("INSERT INTO spell_target_position(ID,EffectIndex,MapID,PositionX) VALUES (233947,9,1,99);")
        unrelated_destinations = sql('SELECT * FROM spell_target_position WHERE NOT ('+selected+') ORDER BY ID,EffectIndex;').stdout
    scripts = registry.get('scripts', [])
    original_script = None
    unrelated_scripts = None
    if scripts:
        assert len(scripts) == 1
        script = dict(scripts[0])
        owner = script['entryorguid']
        family = f'entryorguid={owner} AND source_type=1'
        assert not sql('SELECT * FROM smart_scripts WHERE '+family+';').stdout
        def script_insert(row):
            sql('INSERT INTO smart_scripts ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');')
        def script_rejection():
            before = checksum(tables)
            failure = sql(restore, ok=False)
            assert '_1kycore_generic_guard' in failure.stderr and 'Duplicate entry' in failure.stderr, failure.stderr
            assert checksum(tables) == before, 'SmartScript conflict changed permanent data'
        script['comment'] = "'Administrator compatible wall comment'"
        script_insert(script)
        for field,value in (('action_type','54'),('event_type','61'),('event_param1','1'),('target_type','7'),('event_flags','0'),('event_param_string',"'custom'")):
            sql(f'UPDATE smart_scripts SET `{field}`={value} WHERE '+family+';')
            script_rejection()
            sql(f'UPDATE smart_scripts SET `{field}`={script[field]} WHERE '+family+';')
        extra_script = dict(script)
        extra_script['id'] = '99'
        script_insert(extra_script)
        script_rejection()
        sql('DELETE FROM smart_scripts WHERE '+family+' AND id=99;')
        guid_override = dict(script)
        guid_override['entryorguid'] = '-'+str(first['guid'])
        script_insert(guid_override)
        script_rejection()
        sql(f"DELETE FROM smart_scripts WHERE entryorguid={guid_override['entryorguid']} AND source_type=1;")
        other_source = dict(script)
        other_source['source_type'] = '0'
        script_insert(other_source)
        original_script = sql('SELECT * FROM smart_scripts WHERE '+family+';').stdout
        unrelated_scripts = sql('SELECT * FROM smart_scripts WHERE NOT ('+family+') ORDER BY entryorguid,source_type,id,link;').stdout
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
    expected_addon = next((a for a in registry.get('addons', []) if int(a['entry']) == orphan), None)
    def install_expected_addon():
        columns = ','.join('`'+k+'`' for k in expected_addon)
        values = ','.join(expected_addon.values())
        sql(f'INSERT INTO gameobject_template_addon ({columns}) VALUES ({values});')
    if expected_addon:
        install_expected_addon()  # compatible orphan data must remain unchanged
    sql(f"INSERT INTO gameobject_template(entry,type,name) VALUES ({orphan},3,'Custom chest');")
    before = checksum(tables)
    assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
    assert checksum(tables) == before, 'Incompatible template rejection modified data'
    compatible = next((t for t in registry.get('templates', []) if int(t['entry']) == orphan), None)
    fields = ['type','AIName','ScriptName'] + ['Data'+str(i) for i in range(33)]
    compatible = compatible or {'type': '5'}
    assignments = ','.join('`'+k+'`='+compatible.get(k, "''" if k in ('AIName','ScriptName') else '0') for k in fields)
    sql(f'UPDATE gameobject_template SET {assignments} WHERE entry={orphan};')
    if expected_addon:
        original_addon = sql(f'SELECT * FROM gameobject_template_addon WHERE entry={orphan};').stdout
        sql(f'DELETE FROM gameobject_template_addon WHERE entry={orphan};')
        before = checksum(tables)
        assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
        assert checksum(tables) == before, 'Missing addon on custom template changed data'
        install_expected_addon()
        addon_assignments = ','.join('`'+k+'`='+v for k,v in expected_addon.items() if k != 'entry')
        # Every probe must differ from this object's source value; zero flags
        # and faction 114 are legitimate values in later restoration groups.
        for field in ('flags', 'faction', 'maxgold', 'WorldEffectID'):
            conflicting = int(expected_addon[field]) ^ 1
            alteration = f'`{field}`={conflicting}'
            sql(f'UPDATE gameobject_template_addon SET {alteration} WHERE entry={orphan};')
            before = checksum(tables)
            assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
            assert checksum(tables) == before, 'Addon conflict rejection modified data'
            sql(f'UPDATE gameobject_template_addon SET {addon_assignments} WHERE entry={orphan};')
            assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry={orphan};').stdout == original_addon
    # Matching type alone is insufficient: reject altered behavior and scripts.
    original = sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout
    for alteration in ('Data32=99', "ScriptName='custom_script'", "AIName='custom_conflicting_ai'"):
        sql(f'UPDATE gameobject_template SET {alteration} WHERE entry={orphan};')
        before = checksum(tables)
        assert '_1kycore_generic_guard' in sql(restore, ok=False).stderr
        assert checksum(tables) == before, 'Behavior conflict rejection modified data'
        sql(f"UPDATE gameobject_template SET {assignments} WHERE entry={orphan};")
        assert sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout == original
    original_template = sql(f'SELECT * FROM gameobject_template WHERE entry={orphan};').stdout
    sql(f"INSERT INTO gameobject(guid,id,map,position_x) VALUES ({first['guid']},{first['id']},1,99);")
    original_spawn = sql(f"SELECT * FROM gameobject WHERE guid={first['guid']};").stdout
    mutable = ('gameobject','gameobject_template') + (('gameobject_template_addon',) if expected_addon else ())
    if destinations:
        mutable += ('spell_target_position',)
    if scripts:
        mutable += ('smart_scripts',)
    protected_tables = [t for t in tables if t not in mutable]
    if expected_addon:
        unrelated_addons = sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout
    protected = checksum(protected_tables)
    sql(restore)
    assert checksum(protected_tables) == protected, 'Restoration changed unrelated tables'
    if scripts:
        assert sql('SELECT * FROM smart_scripts WHERE '+family+';').stdout == original_script
        assert sql('SELECT * FROM smart_scripts WHERE NOT ('+family+') ORDER BY entryorguid,source_type,id,link;').stdout == unrelated_scripts

    if destinations:
        assert sql('SELECT * FROM spell_target_position WHERE NOT ('+selected+') ORDER BY ID,EffectIndex;').stdout == unrelated_destinations
        for row in destinations:
            where = f"ID={row['ID']} AND EffectIndex={row['EffectIndex']}"
            previous = original_destinations[(row['ID'],row['EffectIndex'])]
            if previous:
                assert sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout == previous
            else:
                assert sql('SELECT VerifiedBuild FROM spell_target_position WHERE '+where+';').stdout.strip() == '0'
            comparisons = [f'ID={row["ID"]}', f'EffectIndex={row["EffectIndex"]}', f'MapID={row["MapID"]}']
            comparisons += [f'ABS(`{k}`-({row[k]}))<=ABS({row[k]})*0.0000001' for k in ('PositionX','PositionY','PositionZ')]
            assert sql('SELECT COUNT(*) FROM spell_target_position WHERE '+' AND '.join(comparisons)+';').stdout.strip() == '1'
    if original_pages is not None:
        assert sql('SELECT * FROM page_text ORDER BY ID;').stdout == original_pages
    if expected_addon:
        assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout == unrelated_addons
        assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry={orphan};').stdout == original_addon
        predicates = ['('+' AND '.join('`'+k+'`='+v for k,v in a.items())+')' for a in registry['addons']]
        assert sql('SELECT COUNT(*) FROM gameobject_template_addon WHERE '+' OR '.join(predicates)+';').stdout.strip() == str(len(predicates))
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
        count = sql('SELECT COUNT(*) FROM gameobject_template WHERE ' + (' OR '.join(expected_rows) or '0') + ';').stdout.strip()
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
    if expected_addon:
        # Interrupt after addon insertion, before creating ANY new templates.
        sql(f'DELETE FROM gameobject_template WHERE entry IN ({entries}) AND entry<>{orphan};')
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({entries}) AND entry<>{orphan};')
        sql(f"DELETE FROM gameobject WHERE guid IN ({guids}) AND guid<>{first['guid']};")
        sql(restore[:restore.index('-- Add only absent templates')])
        assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == '1'
        assert sql(f'SELECT COUNT(*) FROM gameobject_template_addon WHERE entry IN ({entries});').stdout.strip() == str(len(registry['addons']))
        sql(restore)
        assert checksum(tables) == complete, 'Addon-only interruption retry differs'
    if pages:
        sql(f'DELETE FROM gameobject WHERE guid IN ({guids});')
        sql(f'DELETE FROM gameobject_template WHERE entry IN ({entries});')
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({entries});')
        sql(f'DELETE FROM page_text WHERE ID={page_id};')
        unrelated_pages = sql(f'SELECT * FROM page_text WHERE ID<>{page_id} ORDER BY ID;').stdout
        # Stop immediately after the first permanent write (page), then retry.
        boundary = restore.index('-- Restore exact source addons before templates')
        sql(restore[:boundary])
        assert sql(f'SELECT * FROM page_text WHERE ID={page_id};').stdout == original_page
        assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == '0'
        sql(restore)
        assert sql(f'SELECT * FROM page_text WHERE ID<>{page_id} ORDER BY ID;').stdout == unrelated_pages
        assert sql(f'SELECT * FROM page_text WHERE ID={page_id};').stdout == original_page
        # Custom original records were deliberately removed for this test;
        # compare restored source counts and idempotence instead of their checksum.
        assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == str(len(registry['entries']))
        assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN ({guids});').stdout.strip() == str(len(registry['spawns']))
        missing_page_complete = checksum(tables)
        sql(restore)
        assert checksum(tables) == missing_page_complete
    if destinations:
        # Stop after restoring absent target rows, before addons/templates/spawns.
        for row in destinations:
            if not original_destinations[(row['ID'],row['EffectIndex'])]:
                sql(f"DELETE FROM spell_target_position WHERE ID={row['ID']} AND EffectIndex={row['EffectIndex']};")
        protected = checksum([t for t in tables if t != 'spell_target_position'])
        sql(restore[:restore.index('-- Restore exact source addons before templates')])
        assert checksum([t for t in tables if t != 'spell_target_position']) == protected
        sql(restore)
        assert checksum(tables) == complete, 'Destination-only interruption retry differs'
    if scripts:
        # Restore an absent entry script first, before its template or addon.
        sql(f'DELETE FROM gameobject WHERE guid IN ({guids});')
        sql(f'DELETE FROM gameobject_template WHERE entry IN ({entries});')
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({entries});')
        sql('DELETE FROM smart_scripts WHERE '+family+';')
        protected = checksum([t for t in tables if t != 'smart_scripts'])
        sql(restore[:restore.index('-- Restore exact source addons before templates')])
        assert checksum([t for t in tables if t != 'smart_scripts']) == protected
        row = scripts[0]
        checks = ['`'+k+'`='+v for k,v in row.items()]
        assert sql('SELECT COUNT(*) FROM smart_scripts WHERE '+' AND '.join(checks)+';').stdout.strip() == '1'
        sql(restore)
        assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({entries});').stdout.strip() == str(len(registry['entries']))
        assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN ({guids});').stdout.strip() == str(len(registry['spawns']))
        for template in registry.get('templates', []):
            checks = ['`'+k+'`='+v for k,v in template.items() if k != 'size']
            size = template['size']
            checks.append(f'ABS(`size`-({size}))<=ABS({size})*0.0000001')
            assert sql('SELECT COUNT(*) FROM gameobject_template WHERE '+' AND '.join(checks)+';').stdout.strip() == '1', 'Native wall source template changed'
        complete = checksum(tables)
        sql(restore)
        assert checksum(tables) == complete, 'Script-only wall interruption retry differs'
        assert sql('SELECT * FROM smart_scripts WHERE NOT ('+family+') ORDER BY entryorguid,source_type,id,link;').stdout == unrelated_scripts
    print('PASS: ' + label + ', repeated/partial restoration, custom data and conflict guards', flush=True)




def test_placeholder_models(tables):
    restore = (ROOT / 'sql/updates/world/2026_10_02_01_world_campaign_placeholder_models.sql').read_text('utf8')
    registry = json.loads((ROOT / 'docs/audit-data/campaign-placeholder-model-restoration.json').read_text('utf8'))
    entries = ','.join(map(str, registry['entries']))
    first = registry['baseline'][0]
    entry = int(first['entry'])
    def assignments(row):
        return ','.join('`'+k+'`='+v for k,v in row.items() if k != 'entry')
    def insert_row(row):
        sql('INSERT INTO gameobject_template ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');')
    def assert_rows(rows):
        predicates = ['('+' AND '.join('BINARY `'+k+'` <=> BINARY '+v if k in ('name','IconName','castBarCaption','unk1','AIName','ScriptName','Text') else f'ABS(`size`-({v}))<=ABS({v})*0.0000001' if k=='size' else '`'+k+'` <=> '+v for k,v in row.items())+')' for row in rows]
        assert sql('SELECT COUNT(*) FROM gameobject_template WHERE '+' OR '.join(predicates)+';').stdout.strip() == str(len(rows)), 'Placeholder/source template fields differ'
    assert_rows(registry['baseline'])
    assert sql(f'SELECT COUNT(*) FROM gameobject_template_addon WHERE entry IN ({entries});').stdout.strip() == '0'
    assert sql(f'SELECT COUNT(*) FROM gameobject_questitem WHERE GameObjectEntry IN ({entries});').stdout.strip() == '0'
    def rejection():
        before = checksum(tables)
        failure = sql(restore, ok=False)
        assert '_1kycore_model_guard' in failure.stderr and 'Duplicate entry' in failure.stderr, failure.stderr
        assert checksum(tables) == before, 'Model guard changed permanent data'
    # Do not recreate rows that an administrator deliberately removed.
    sql(f'DELETE FROM gameobject_template WHERE entry={entry};')
    rejection()
    insert_row(first)
    for alteration in ("name='Custom decoration'", 'displayId=12345', 'RequiredLevel=80', 'Data32=99', "AIName='SmartGameObjectAI'", "ScriptName='custom_script'"):
        sql(f'UPDATE gameobject_template SET {alteration} WHERE entry={entry};')
        rejection()
        sql(f'UPDATE gameobject_template SET {assignments(first)} WHERE entry={entry};')
    for column in ('faction','flags','mingold','maxgold','WorldEffectID'):
        sql(f'INSERT INTO gameobject_template_addon(entry,`{column}`) VALUES ({entry},1);')
        rejection()
        sql(f'DELETE FROM gameobject_template_addon WHERE entry={entry};')
    sql(f'INSERT INTO gameobject_questitem(GameObjectEntry,Idx,ItemId) VALUES ({entry},0,6948);')
    rejection()
    sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={entry};')
    # Neutral custom addon is retained; no addon or questitem records are added.
    sql(f'INSERT INTO gameobject_template_addon(entry) VALUES ({entry});')
    protected_tables = [t for t in tables if t != 'gameobject_template']
    protected = checksum(protected_tables)
    unrelated = sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout
    sql(restore)
    assert_rows(registry['templates'])
    assert checksum(protected_tables) == protected, 'Models changed spawns or unrelated tables'
    assert sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout == unrelated
    complete = checksum(tables)
    sql(restore)
    assert checksum(tables) == complete, 'Repeated model restoration changed data'
    # Simulate interruption after any subset of the15 templates was restored.
    for row in registry['baseline'][3:]:
        sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
    sql(restore)
    assert checksum(tables) == complete, 'Partial model restoration retry differs'
    # A customized already-restored row also rejects before touching another placeholder.
    row = registry['baseline'][1]
    sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
    sql(f"UPDATE gameobject_template SET ScriptName='custom_native' WHERE entry={entry};")
    rejection()
    sql(f"UPDATE gameobject_template SET {assignments(registry['templates'][0])} WHERE entry={entry};")
    sql(restore)
    assert checksum(tables) == complete
    print('PASS:15 placeholder models, exact source data, custom/missing/dependency guards, repeated/partial restoration and unchanged spawns', flush=True)



def test_simple_goober_models(tables, restore=None, registry=None, label="two native GOOBER models/addons"):
    if restore is None:
        restore = (ROOT / 'sql/updates/world/2026_10_02_02_world_campaign_simple_goober_models.sql').read_text('utf8')
        registry = json.loads((ROOT / 'docs/audit-data/campaign-simple-goober-restoration.json').read_text('utf8'))
    entries = ','.join(map(str,registry['entries']))
    first = registry['baseline'][0]
    entry = int(first['entry'])
    addon = registry['addons'][0]
    def assignments(row):
        return ','.join('`'+k+'`='+v for k,v in row.items() if k != 'entry')
    def insert_row(table,row):
        sql('INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');')
    def assert_rows(table,rows):
        predicates = ['('+' AND '.join('BINARY `'+k+'` <=> BINARY '+v if k in ('name','IconName','castBarCaption','unk1','AIName','ScriptName','Text') else f'ABS(`size`-({v}))<=ABS({v})*0.0000001' if k=='size' else '`'+k+'` <=> '+v for k,v in row.items())+')' for row in rows]
        assert sql('SELECT COUNT(*) FROM '+table+' WHERE '+' OR '.join(predicates)+';').stdout.strip() == str(len(rows))
    assert_rows('gameobject_template',registry['baseline'])
    baseline_addons = registry.get('baseline_addons', [])
    assert sql(f'SELECT COUNT(*) FROM gameobject_template_addon WHERE entry IN ({entries});').stdout.strip() == str(len(baseline_addons))
    if baseline_addons:
        assert_rows('gameobject_template_addon',baseline_addons)
    assert sql(f'SELECT COUNT(*) FROM gameobject_questitem WHERE GameObjectEntry IN ({entries});').stdout.strip() == '0'
    def rejection():
        before = checksum(tables)
        failure = sql(restore,ok=False)
        assert '_1kycore_model_guard' in failure.stderr and 'Duplicate entry' in failure.stderr, failure.stderr
        assert checksum(tables) == before, 'GOOBER conflict changed permanent data'
    # Restoring native interactions must not silently activate administrator scripts.
    if registry.get('protected_spells'):
        spell = registry['protected_spells'][0]
        spawn_guid = registry['protected_spawn_guids'][0]
        overrides = [
            (f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({entry},1,99,64,1,1,'test native override');",
             f'DELETE FROM smart_scripts WHERE entryorguid={entry} AND source_type=1 AND id=99;'),
            (f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({-spawn_guid},1,99,64,1,1,'test native override');",
             f'DELETE FROM smart_scripts WHERE entryorguid={-spawn_guid} AND source_type=1 AND id=99;'),
            (f"INSERT INTO spell_script_names(spell_id,ScriptName) VALUES ({spell},'test_native_interaction');",
             f"DELETE FROM spell_script_names WHERE spell_id={spell} AND ScriptName='test_native_interaction';"),
            (f'INSERT INTO conditions(SourceTypeOrReferenceId,SourceGroup,SourceEntry,ConditionTypeOrReference,ConditionValue1) VALUES (13,1,{spell},1,6948);',
             f'DELETE FROM conditions WHERE SourceTypeOrReferenceId=13 AND SourceGroup=1 AND SourceEntry={spell} AND ConditionValue1=6948;')]
        for addition, removal in overrides:
            sql(addition)
            try:
                rejection()
            finally:
                sql(removal)
    for event in registry.get('protected_events', []):
        spawn_guid = registry['protected_spawn_guids'][0]
        overrides = [
            (f"INSERT INTO event_scripts(id,delay,command,datalong) VALUES ({event},0,0,1);", f'DELETE FROM event_scripts WHERE id={event};'),
            (f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({event},2,99,64,1,1,'test event override');", f'DELETE FROM smart_scripts WHERE entryorguid={event} AND source_type=2 AND id=99;'),
            (f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({entry},1,99,64,1,1,'test GO override');", f'DELETE FROM smart_scripts WHERE entryorguid={entry} AND source_type=1 AND id=99;'),
            (f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({-spawn_guid},1,99,64,1,1,'test spawn override');", f'DELETE FROM smart_scripts WHERE entryorguid={-spawn_guid} AND source_type=1 AND id=99;')]
        for addition, removal in overrides:
            sql(addition)
            try:
                rejection()
            finally:
                sql(removal)
    pages = registry.get('pages', [])
    page_ids = ','.join(p['ID'] for p in pages)
    if pages:
        assert sql(f'SELECT COUNT(*) FROM page_text WHERE ID IN ({page_ids});').stdout.strip() == '0'
        assert sql(f'SELECT COUNT(*) FROM page_text_locale WHERE ID IN ({page_ids});').stdout.strip() == '0'
        unrelated_pages = sql(f'SELECT * FROM page_text WHERE ID NOT IN ({page_ids}) ORDER BY ID;').stdout
        for page in pages:
            page_id = page['ID']
            sql(f"INSERT INTO page_text_locale(ID,locale,Text) VALUES ({page_id},'ruRU','orphan custom translation');")
            rejection()
            sql(f'DELETE FROM page_text_locale WHERE ID={page_id};')
            insert_row('page_text',page)
            page_assignments = ','.join('`'+k+'`='+v for k,v in page.items() if k != 'ID')
            alterations = ["Text='custom page'", 'Text=NULL', f"NextPageID={page_id}", 'PlayerConditionID=1', f"Flags={int(page['Flags'])^1}", 'VerifiedBuild=0']
            for alteration in alterations:
                sql(f'UPDATE page_text SET {alteration} WHERE ID={page_id};')
                rejection()
                sql(f'UPDATE page_text SET {page_assignments} WHERE ID={page_id};')
            sql(f'DELETE FROM page_text WHERE ID={page_id};')
        # A matching source page with an administrator translation must survive.
        insert_row('page_text',pages[0])
        sql(f"INSERT INTO page_text_locale(ID,locale,Text) VALUES ({pages[0]['ID']},'ruRU','preserved custom translation');")
        preserved_locales = sql('SELECT * FROM page_text_locale ORDER BY ID,locale;').stdout
        sql(f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({entry},1,99,64,1,1,'custom book action');")
        rejection()
        sql(f'DELETE FROM smart_scripts WHERE entryorguid={entry} AND source_type=1 AND id=99;')
        sql('INSERT INTO conditions(SourceTypeOrReferenceId,SourceGroup,SourceEntry,ConditionTypeOrReference,ConditionValue1) VALUES (13,1,218330,1,6948);')
        rejection()
        sql('DELETE FROM conditions WHERE SourceTypeOrReferenceId=13 AND SourceEntry=218330;')
        sql("INSERT INTO spell_script_names(spell_id,ScriptName) VALUES (218330,'custom_book_credit');")
        rejection()
        sql("DELETE FROM spell_script_names WHERE spell_id=218330 AND ScriptName='custom_book_credit';")
    if baseline_addons:
        legacy = baseline_addons[0]
        for field in ('faction','flags','mingold','maxgold','WorldEffectID'):
            sql(f"UPDATE gameobject_template_addon SET `{field}`=1 WHERE entry={legacy['entry']};")
            rejection()
            sql(f"UPDATE gameobject_template_addon SET `{field}`={legacy[field]} WHERE entry={legacy['entry']};")
    expected_loot = registry.get('loot', [])
    expected_items = registry.get('questitems', [])
    unrelated_loot = unrelated_items = None
    if expected_loot:
        assert sql(f'SELECT COUNT(*) FROM gameobject_loot_template WHERE Entry IN ({entries});').stdout.strip() == '0'
        unrelated_loot = sql(f'SELECT * FROM gameobject_loot_template WHERE Entry NOT IN ({entries}) ORDER BY Entry,Item;').stdout
        unrelated_items = sql(f'SELECT * FROM gameobject_questitem WHERE GameObjectEntry NOT IN ({entries}) ORDER BY GameObjectEntry,Idx;').stdout
        probe = expected_loot[0]
        insert_row('gameobject_loot_template',probe)
        for field in ('Chance','QuestRequired','Reference','LootMode','GroupId','MinCount','MaxCount'):
            changed = dict(probe)
            changed[field] = str(int(probe[field]) ^ 1) if field=='LootMode' else str(int(probe[field]) + 1)
            sql(f"UPDATE gameobject_loot_template SET `{field}`={changed[field]} WHERE Entry={probe['Entry']} AND Item={probe['Item']};")
            rejection()
            sql(f"UPDATE gameobject_loot_template SET `{field}`={probe[field]} WHERE Entry={probe['Entry']} AND Item={probe['Item']};")
        custom = dict(probe);custom['Item'] = '6948'
        insert_row('gameobject_loot_template',custom)
        rejection()
        sql(f"DELETE FROM gameobject_loot_template WHERE Entry={probe['Entry']} AND Item=6948;")
        sql(f"DELETE FROM gameobject_loot_template WHERE Entry={probe['Entry']};")
        hint = expected_items[0]
        insert_row('gameobject_questitem',hint)
        sql(f"INSERT INTO gameobject_questitem(GameObjectEntry,Idx,ItemId) VALUES ({entry},1,6948);")
        rejection()
        sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={entry};')
        sql(f'INSERT INTO conditions(SourceTypeOrReferenceId,SourceGroup,SourceEntry,ConditionTypeOrReference,ConditionValue1) VALUES (4,{entry},6948,2,6948);')
        rejection()
        sql(f'DELETE FROM conditions WHERE SourceTypeOrReferenceId=4 AND SourceGroup={entry};')
    destinations = registry.get('destinations', [])
    selected_destinations = ' OR '.join(f"(ID={row['ID']} AND EffectIndex={row['EffectIndex']})" for row in destinations)
    preserved_destination = None
    unrelated_destinations = None
    if destinations:
        for row in destinations:
            assert not sql(f"SELECT * FROM spell_target_position WHERE ID={row['ID']} AND EffectIndex={row['EffectIndex']};").stdout
        probe = dict(destinations[0])
        probe['VerifiedBuild'] = '12345'
        insert_row('spell_target_position',probe)
        where = f"ID={probe['ID']} AND EffectIndex={probe['EffectIndex']}"
        preserved_destination = sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout
        for field in ('MapID','PositionX','PositionY','PositionZ'):
            sql(f'UPDATE spell_target_position SET `{field}`={probe[field]}+10 WHERE '+where+';')
            rejection()
            sql(f'UPDATE spell_target_position SET `{field}`={probe[field]} WHERE '+where+';')
            assert sql('SELECT * FROM spell_target_position WHERE '+where+';').stdout == preserved_destination
        sql("INSERT INTO spell_target_position(ID,EffectIndex,MapID,PositionX) VALUES (232727,9,1,99);")
        unrelated_destinations = sql('SELECT * FROM spell_target_position WHERE NOT ('+selected_destinations+') ORDER BY ID,EffectIndex;').stdout
    # Missing/wrong native dependencies must reject before installing any route/addon/model.
    for creature in registry.get('required_creatures', []):
        sql(f'UPDATE creature_template SET entry=9000020 WHERE entry={creature};')
        rejection()
        sql(f'UPDATE creature_template SET entry={creature} WHERE entry=9000020;')
    for objective in registry.get('required_objectives', []):
        for field in registry.get('protected_objective_fields', ('ObjectID','QuestID','Type','Amount')):
            changed = int(objective[field]) + 1
            sql(f"UPDATE quest_objectives SET `{field}`={changed} WHERE ID={objective['ID']};")
            rejection()
            sql(f"UPDATE quest_objectives SET `{field}`={objective[field]} WHERE ID={objective['ID']};")
    for quest in registry.get('required_quests', []):
        sql(f'UPDATE quest_template SET ID=9000022 WHERE ID={quest};')
        rejection()
        sql(f'UPDATE quest_template SET ID={quest} WHERE ID=9000022;')
    sql(f'DELETE FROM gameobject_template WHERE entry={entry};')
    rejection()
    insert_row('gameobject_template',first)
    for alteration in ("name='Custom GOOBER'", 'displayId=12345', 'RequiredLevel=80', 'Data32=99', "AIName='SmartGameObjectAI'", "ScriptName='custom_script'"):
        sql(f'UPDATE gameobject_template SET {alteration} WHERE entry={entry};')
        rejection()
        sql(f'UPDATE gameobject_template SET {assignments(first)} WHERE entry={entry};')
    insert_row('gameobject_template_addon',addon)
    for field in ('faction','flags','mingold','maxgold','WorldEffectID'):
        sql(f'UPDATE gameobject_template_addon SET `{field}`={int(addon[field])^1} WHERE entry={entry};')
        rejection()
        sql(f'UPDATE gameobject_template_addon SET {assignments(addon)} WHERE entry={entry};')
    sql(f'INSERT INTO gameobject_questitem(GameObjectEntry,Idx,ItemId) VALUES ({entry},0,6948);')
    rejection()
    sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={entry};')
    original_addon = sql(f'SELECT * FROM gameobject_template_addon WHERE entry={entry};').stdout
    mutable = ('gameobject_template','gameobject_template_addon') + (('page_text',) if pages else ()) + (('spell_target_position',) if destinations else ()) + (('gameobject_loot_template','gameobject_questitem') if expected_loot else ())
    protected_tables = [t for t in tables if t not in mutable]
    protected = checksum(protected_tables)
    unrelated_templates = sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout
    unrelated_addons = sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout
    sql(restore)
    assert_rows('gameobject_template',registry['templates'])
    assert_rows('gameobject_template_addon',registry['addons'])
    if pages:
        assert_rows('page_text',pages)
        assert sql(f'SELECT * FROM page_text WHERE ID NOT IN ({page_ids}) ORDER BY ID;').stdout == unrelated_pages
        assert sql('SELECT * FROM page_text_locale ORDER BY ID,locale;').stdout == preserved_locales

    if expected_loot:
        assert_rows('gameobject_loot_template',expected_loot)
        assert_rows('gameobject_questitem',expected_items)
        assert sql(f'SELECT * FROM gameobject_loot_template WHERE Entry NOT IN ({entries}) ORDER BY Entry,Item;').stdout == unrelated_loot
        assert sql(f'SELECT * FROM gameobject_questitem WHERE GameObjectEntry NOT IN ({entries}) ORDER BY GameObjectEntry,Idx;').stdout == unrelated_items
    assert checksum(protected_tables) == protected, 'GOOBER models changed spawns/other tables'
    assert sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout == unrelated_templates
    assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({entries}) ORDER BY entry;').stdout == unrelated_addons
    assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry={entry};').stdout == original_addon
    if destinations:
        probe = destinations[0]
        assert sql(f"SELECT * FROM spell_target_position WHERE ID={probe['ID']} AND EffectIndex={probe['EffectIndex']};").stdout == preserved_destination
        for row in destinations:
            checks = [f'ID={row["ID"]}',f'EffectIndex={row["EffectIndex"]}',f'MapID={row["MapID"]}']
            checks += [f'ABS(`{k}`-({row[k]}))<=ABS({row[k]})*0.0000001' for k in ('PositionX','PositionY','PositionZ')]
            assert sql('SELECT COUNT(*) FROM spell_target_position WHERE '+' AND '.join(checks)+';').stdout.strip() == '1'
        row = destinations[1]
        assert sql(f"SELECT VerifiedBuild FROM spell_target_position WHERE ID={row['ID']} AND EffectIndex={row['EffectIndex']};").stdout.strip() == '0'
        assert sql('SELECT * FROM spell_target_position WHERE NOT ('+selected_destinations+') ORDER BY ID,EffectIndex;').stdout == unrelated_destinations
    complete = checksum(tables)
    sql(restore)
    assert checksum(tables) == complete
    sql(f'DELETE FROM gameobject_template_addon WHERE entry={entry};')
    rejection()  # native template without its source flags/faction is unsafe
    insert_row('gameobject_template_addon',addon)
    if expected_loot:
        hint = expected_items[0];probe = expected_loot[0]
        sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={entry};')
        rejection()
        insert_row('gameobject_questitem',hint)
        sql(f'DELETE FROM gameobject_loot_template WHERE Entry={entry};')
        rejection()
        insert_row('gameobject_loot_template',probe)
    if pages:
        for page in pages:
            sql(f"DELETE FROM page_text WHERE ID={page['ID']};")
            rejection()  # do not silently repair a damaged native page dependency
            insert_row('page_text',page)
    for row in registry['baseline'][1:]:
        sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
    sql(restore)
    assert checksum(tables) == complete, 'Mixed baseline/native GOOBER retry differs'
    for row in registry['baseline']:
        sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
    sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({entries});')
    sql(restore[:restore.index('-- Rewrite only byte-compatible release placeholders')])
    assert_rows('gameobject_template',registry['baseline'])
    assert_rows('gameobject_template_addon',registry['addons'])
    sql(restore)
    assert checksum(tables) == complete, 'Addon-only GOOBER interruption retry differs'
    if pages:
        for row in registry['baseline']:
            sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
        sql(f'DELETE FROM page_text_locale WHERE ID IN ({page_ids});')
        sql(f'DELETE FROM page_text WHERE ID IN ({page_ids});')
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({entries});')
        protected = checksum([t for t in tables if t != 'page_text'])
        sql(restore[:restore.index('-- Install missing source addons first')])
        assert_rows('page_text',pages)
        assert_rows('gameobject_template',registry['baseline'])
        assert checksum([t for t in tables if t != 'page_text']) == protected
        sql(f"INSERT INTO page_text_locale(ID,locale,Text) VALUES ({pages[0]['ID']},'ruRU','preserved custom translation');")
        sql(restore)
        assert checksum(tables) == complete, 'Page-only GOOBER interruption retry differs'
    if expected_loot:
        # Interrupt after addon / item-hint writes, before loot and native templates.
        for row in registry['baseline']:
            sql(f"UPDATE gameobject_template SET {assignments(row)} WHERE entry={row['entry']};")
        sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry IN ({entries});')
        sql(f'DELETE FROM gameobject_loot_template WHERE Entry IN ({entries});')
        sql(restore[:restore.index('INSERT INTO gameobject_loot_template (')])
        assert_rows('gameobject_template',registry['baseline'])
        assert_rows('gameobject_questitem',expected_items)
        assert sql(f'SELECT COUNT(*) FROM gameobject_loot_template WHERE Entry IN ({entries});').stdout.strip() == '0'
        sql(restore)
        assert checksum(tables) == complete, 'Quest-item-only interruption retry differs'
        # Matching quest-item provenance is retained, never forced to invented source builds.
        hint = expected_items[0]
        sql(f"UPDATE gameobject_questitem SET VerifiedBuild=12345 WHERE GameObjectEntry={hint['GameObjectEntry']} AND Idx={hint['Idx']};")
        compatible = checksum(tables)
        sql(restore)
        assert checksum(tables) == compatible, 'Compatible quest-item provenance changed'
    if destinations:
        row = destinations[1]
        sql(f"DELETE FROM spell_target_position WHERE ID={row['ID']} AND EffectIndex={row['EffectIndex']};")
        protected = checksum([t for t in tables if t != 'spell_target_position'])
        sql(restore[:restore.index('-- Install missing source addons first')])
        assert checksum([t for t in tables if t != 'spell_target_position']) == protected
        sql(restore)
        assert checksum(tables) == complete, 'Destination-only GOOBER interruption retry differs'
    print('PASS:'+label+', full conflict/dependency guards, repeated/partial restoration and unchanged spawns',flush=True)




def test_simple_conversations(tables, restore, registry):
    """Exercise real MyISAM dependencies, shared actors and interrupted publication."""
    rows = registry['rows']
    owned = list(rows)
    keys = {table: ('ConversationId','Idx') if table == 'conversation_actors' else ('Id',) for table in owned}
    def predicate(table, row):
        return ' AND '.join(f'`{key}`={row[key]}' for key in keys[table])
    def insert(table, row):
        return f"INSERT INTO `{table}` ({','.join('`'+key+'`' for key in row)}) VALUES ({','.join(row.values())});"
    def clear():
        for table in reversed(owned):
            sql(f"DELETE FROM `{table}` WHERE " + ' OR '.join('('+predicate(table,row)+')' for row in rows[table]) + ';')
    def reject():
        before = checksum(owned)
        failure = sql(restore, ok=False)
        assert 'Duplicate entry' in failure.stderr and '_1kycore_conversation_guard' in failure.stderr, failure.stderr
        assert checksum(owned) == before, 'Rejected conversation migration changed permanent dependencies'
    def verify():
        for table, expected in rows.items():
            for row in expected:
                columns = [key for key in row if key != 'VerifiedBuild']
                result = sql(f"SELECT {','.join('`'+key+'`' for key in columns)} FROM `{table}` WHERE {predicate(table,row)};").stdout.rstrip('\r\n').split('\t')
                assert result == [row[key].strip("'") for key in columns], (table,row,result)
    for table in owned:
        assert sql(f"SELECT COUNT(*) FROM `{table}` WHERE " + ' OR '.join('('+predicate(table,row)+')' for row in rows[table]) + ';').stdout.strip() == '0'
    protected_tables = [table for table in tables if table not in owned]
    protected = checksum(protected_tables)
    # Test every runtime content field. Matching provenance is intentionally not a conflict.
    for table in owned:
        original = rows[table][0]
        for column in original:
            if column in keys[table] or column == 'VerifiedBuild':
                continue
            bad = dict(original)
            bad[column] = "'custom_scene'" if column == 'ScriptName' else str(int(original[column])+1)
            sql(insert(table,bad))
            reject()
            sql(f"DELETE FROM `{table}` WHERE {predicate(table,original)};")
    extra = dict(rows['conversation_actors'][-1]); extra['Idx']='1'
    sql(insert('conversation_actors',extra)); reject()
    sql(f"DELETE FROM conversation_actors WHERE {predicate('conversation_actors',extra)};")
    # Required NPC disappearance must reject before inserting any conversations.
    creature = rows['conversation_actor_template'][0]['CreatureId']
    sql(f'CREATE TABLE saved_conversation_creature AS SELECT * FROM creature_template WHERE entry={creature}; DELETE FROM creature_template WHERE entry={creature};')
    reject()
    sql('INSERT INTO creature_template SELECT * FROM saved_conversation_creature; DROP TABLE saved_conversation_creature;')
    sql(restore); verify()
    canonical = checksum(owned)
    sql(restore)
    assert checksum(owned) == canonical, 'Conversation retry changed content'
    # An already published conversation with missing native dependencies is a conflict.
    for table in ('conversation_line_template','conversation_actors','conversation_actor_template'):
        for row in rows[table]:
            sql(f"DELETE FROM `{table}` WHERE {predicate(table,row)};")
            reject()
            sql(insert(table,row))
    # Actual migration prefixes: shared templates, lines, then bindings; publish last.
    for next_table in owned[1:]:
        clear()
        cutoff = restore.index(f'-- Install {next_table};')
        sql(restore[:cutoff]); sql(restore); verify()
        assert checksum(owned) == canonical, 'Interrupted conversation import differs after retry'
    # A fully published prefix and unfinished remaining conversations can also resume.
    clear()
    for table in owned:
        for row in (rows[table][:1] if table == 'conversation_template' else rows[table]):
            sql(insert(table,row))
    sql(restore); verify()
    assert checksum(owned) == canonical
    # Keep compatible administrator build provenance, including shared actor templates.
    for table in owned:
        row = rows[table][0]
        sql(f"UPDATE `{table}` SET VerifiedBuild=12345 WHERE {predicate(table,row)};")
    shared = rows['conversation_actor_template'][0]['Id']
    unrelated_id = 4290000000 + registry['entries'][0]
    assert sql(f'SELECT COUNT(*) FROM conversation_actors WHERE ConversationId={unrelated_id};').stdout.strip() == '0'
    sql(f'INSERT INTO conversation_actors (ConversationId,ConversationActorId,Idx,VerifiedBuild) VALUES ({unrelated_id},{shared},0,54321);')
    compatible = checksum(owned)
    sql(restore); verify()
    assert checksum(owned) == compatible, 'Matching provenance or unrelated shared actor binding changed'
    assert checksum(protected_tables) == protected, 'Conversation migration changed NPCs, quests, spawns or other tables'
    print(f"PASS: {len(registry['entries'])} complete conversation chains / exact actors and lines / all content conflicts / repeated and interrupted import / shared provenance", flush=True)

def test_nearest_conversations():
    registry = json.loads((ROOT/'docs/audit-data/campaign-nearest-conversation-restoration.json').read_text('utf8'))
    sql_text = (ROOT/'sql/updates/world/2026_10_05_01_world_campaign_nearest_conversations.sql').read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines();owned=list(registry['rows']);before=checksum(tables)
    ids={t:','.join(x['Id'] for x in rows) for t,rows in registry['rows'].items()}
    assert all(sql(f'SELECT COUNT(*) FROM {t} WHERE Id IN ({keys});').stdout.strip()=='0' for t,keys in ids.items()),'Already-existing line requires separate ownership review'
    def clean():
     for t in reversed(owned):sql(f'DELETE FROM {t} WHERE Id IN ({ids[t]});')
    try:
     protected=checksum([t for t in tables if t not in owned]);sql(sql_text)
     complete=checksum(tables);canonical=checksum(owned);sql(sql_text);assert checksum(tables)==complete
     assert checksum([t for t in tables if t not in owned])==protected
     print('PASS: native nearest conversations first/repeat and unchanged unrelated tables',flush=True)
     # Existing provenance survives, but content conflicts must stop before writes.
     cid=registry['entries'][0];sql(f'UPDATE conversation_template SET VerifiedBuild=12345 WHERE Id={cid};');compatible=checksum(owned);sql(sql_text);assert checksum(owned)==compatible
     for table,field,value in [('conversation_template','ScriptName',"'custom'"),('conversation_template','LastLineEndTime','1'),('conversation_line_template','ActorIdx','99'),('conversation_line_template','Flags','1')]:
      row=registry['rows'][table][0];id=row['Id'];sql(f'UPDATE {table} SET {field}={value} WHERE Id={id};');conflict=checksum(owned);result=sql(sql_text,ok=False);assert '_1kycore_nearest_guard' in result.stderr;assert checksum(owned)==conflict;sql(f'UPDATE {table} SET {field}={row[field]} WHERE Id={id};')
     first_line=registry['rows']['conversation_line_template'][0]
     sql('DELETE FROM conversation_line_template WHERE Id='+first_line['Id']+';');conflict=checksum(owned);sql(sql_text,ok=False);assert checksum(owned)==conflict
     sql('INSERT INTO conversation_line_template ('+','.join(first_line)+') VALUES ('+','.join(first_line.values())+');')
     clean();split=sql_text.index('INSERT INTO `conversation_template` (`Id`')
     sql(sql_text[:split]);sql(sql_text);assert checksum(owned)==canonical
     sql(f'INSERT INTO conversation_actors(ConversationId,ConversationActorGuid,Idx) VALUES ({cid},1,0);')
     try:
      conflict=checksum(owned+['conversation_actors']);sql(sql_text,ok=False);assert checksum(owned+['conversation_actors'])==conflict
     finally:sql(f'DELETE FROM conversation_actors WHERE ConversationId={cid};')
     print('PASS: content/provenance, missing lines, unexpected actor bindings, interrupted dependency publication',flush=True)

    finally:
     clean();assert checksum(tables)==before;print('Restored scratch baseline',flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gilneas-chain-only', action='store_true', help='Test audited Gilneas bindings and object spawns.')
    parser.add_argument('--smart-wall-only', action='store_true', help='Run the complete wall conflict/retry tests against the real release, before the full suite.')
    parser.add_argument('--wildcard-loot-only', action='store_true', help='Run source wildcard loot translation against the real release.')
    parser.add_argument('--source-loot-only', action='store_true', help='Run the complete source loot object group against the real release.')
    parser.add_argument('--native-goobers-only', action='store_true', help='Run all seven native GOOBER dependency and retry checks against the real release.')
    parser.add_argument('--conversation-chains-only', action='store_true', help='Run multi-line conversation chain and actor-index checks.')
    parser.add_argument('--simple-conversations-only', action='store_true', help='Run terminal conversation dependency and publication checks.')
    parser.add_argument('--council-books-only', action='store_true', help='Run page-chain and quest-credit dependency checks for two source books.')
    parser.add_argument('--required-level-only', action='store_true', help='Test exact source RequiredLevel mapping, conflicts and retries.')
    parser.add_argument('--native-visuals-only', action='store_true', help='Test optional GO visual schema and four restorations.')
    args = parser.parse_args()
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
        if args.gilneas_chain_only:
            test_gilneas_database(sql,checksum)
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.required_level_only:
            sql(migration)
            test_required_level_objects(sql,checksum)
            test_required_level_objects(sql,checksum,'campaign-scenario-object-restoration.json','2026_10_08_04_world_campaign_scenario_objects.sql')
            sql(f'DROP DATABASE `{DB}`;', False)
            return
        if args.native_visuals_only:
            sql(migration)
            test_visual_migration(sql,checksum)
            test_cage_state_restoration(sql,checksum)
            test_cage_state_restoration(sql,checksum,'campaign-fel-boiler-restoration.json','2026_10_08_03_world_campaign_fel_boiler_loot.sql')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.conversation_chains_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_04_02_world_campaign_conversation_chains.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-conversation-chain-restoration.json').read_text('utf8'))
            test_simple_conversations(tables,restore,registry)
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.simple_conversations_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_04_01_world_campaign_simple_conversations.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-simple-conversation-restoration.json').read_text('utf8'))
            test_simple_conversations(tables,restore,registry)
            test_packed_conversations(sql,checksum)
            test_packed_conversations(sql,checksum,'campaign-source-timing-conversations.json','2026_10_08_02_world_campaign_source_timing_conversations.sql')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.council_books_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_04_00_world_campaign_council_books.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-council-books-restoration.json').read_text('utf8'))
            test_simple_goober_models(tables,restore,registry,'two council books / two exact terminal pages / quest-credit dependencies')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.native_goobers_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_02_04_world_campaign_native_goobers.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-native-goober-restoration.json').read_text('utf8'))
            test_simple_goober_models(tables,restore,registry,'focused seven native GOOBER objects / exact objective amounts / two teleport routes')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.wildcard_loot_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_03_01_world_campaign_wildcard_loot_objects.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-wildcard-loot-restoration.json').read_text('utf8'))
            test_simple_goober_models(tables,restore,registry,'two wildcard loot objects / all native modes / preserved group and quest loot')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.source_loot_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            restore = (ROOT / 'sql/updates/world/2026_10_03_00_world_campaign_source_loot_objects.sql').read_text('utf8')
            registry = json.loads((ROOT / 'docs/audit-data/campaign-source-loot-restoration.json').read_text('utf8'))
            test_simple_goober_models(tables,restore,registry,'five source loot objects / quest hints / compatible native loot')
            sql(f'DROP DATABASE `{DB}`;',False)
            return
        if args.smart_wall_only:
            sql(migration)
            tables = sql('SHOW TABLES;').stdout.splitlines()
            wall = (ROOT / 'sql/updates/world/2026_10_02_05_world_campaign_smart_wall.sql').read_text('utf8')
            wall_registry = json.loads((ROOT / 'docs/audit-data/campaign-smart-wall-restoration.json').read_text('utf8'))
            test_generic_restoration(wall, wall_registry, tables, 'focused native Smart wall / two spawns / complete guards')
            sql(f'DROP DATABASE `{DB}`;', False)
            return
        # Validate the existing release path before importing any new objects:
        # enum naming is not a flags whitelist; this exact pair is native data.
        assert sql('SELECT COUNT(*) FROM gameobject_template t JOIN gameobject_template_addon a ON a.entry=t.entry WHERE t.type=5 AND (a.flags & 8192)<>0 AND t.Data7=1;').stdout.strip() == '193'
        assert sql('SELECT COUNT(*) FROM gameobject_template t JOIN gameobject_template_addon a ON a.entry=t.entry WHERE t.type=5 AND (a.flags & 8192)<>0 AND t.Data7<>1;').stdout.strip() == '0'
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
        fourth = (ROOT / 'sql/updates/world/2026_10_01_04_world_campaign_generic_addons.sql').read_text('utf8')
        fourth_registry = json.loads((ROOT / 'docs/audit-data/campaign-generic-addon-restoration.json').read_text('utf8'))
        test_generic_restoration(fourth, fourth_registry, tables, '25 templates / 60 spawns / 25 addons')
        fifth = (ROOT / 'sql/updates/world/2026_10_01_05_world_campaign_visibility_phaseable.sql').read_text('utf8')
        fifth_registry = json.loads((ROOT / 'docs/audit-data/campaign-visibility-phaseable-restoration.json').read_text('utf8'))
        test_generic_restoration(fifth, fifth_registry, tables, '38 templates / 90 spawns / 38 addons')
        sixth = (ROOT / 'sql/updates/world/2026_10_02_00_world_campaign_doors_book.sql').read_text('utf8')
        sixth_registry = json.loads((ROOT / 'docs/audit-data/campaign-doors-book-restoration.json').read_text('utf8'))
        test_generic_restoration(sixth, sixth_registry, tables, 'five doors / one book / 10 spawns / page5121')

        native_interactions = (ROOT / 'sql/updates/world/2026_10_05_00_world_campaign_native_interactions.sql').read_text('utf8')
        interaction_registry = json.loads((ROOT / 'docs/audit-data/campaign-native-interactions-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables,native_interactions,interaction_registry,'native portal and brew interactions / protected credit dependencies')

        false_orders = (ROOT / 'sql/updates/world/2026_10_05_02_world_campaign_false_orders.sql').read_text('utf8')
        orders_registry = json.loads((ROOT / 'docs/audit-data/campaign-false-orders-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables,false_orders,orders_registry,'two False Orders / four objectives / protected event and spawn overrides')

        test_nearest_conversations()
        test_packed_conversations(sql,checksum)
        test_packed_conversations(sql,checksum,'campaign-source-timing-conversations.json','2026_10_08_02_world_campaign_source_timing_conversations.sql')

        test_placeholder_models(tables)
        test_simple_goober_models(tables)
        client_group = (ROOT / 'sql/updates/world/2026_10_02_03_world_campaign_client_validated_objects.sql').read_text('utf8')
        client_registry = json.loads((ROOT / 'docs/audit-data/campaign-client-validated-restoration.json').read_text('utf8'))
        test_generic_restoration(client_group, client_registry, tables, '12 client-validated templates / 12 spawns / native portal destinations')
        native_goobers = (ROOT / 'sql/updates/world/2026_10_02_04_world_campaign_native_goobers.sql').read_text('utf8')
        native_registry = json.loads((ROOT / 'docs/audit-data/campaign-native-goober-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables, native_goobers, native_registry, 'seven native GOOBER templates/addons and two teleport routes')
        smart_wall = (ROOT / 'sql/updates/world/2026_10_02_05_world_campaign_smart_wall.sql').read_text('utf8')
        wall_registry = json.loads((ROOT / 'docs/audit-data/campaign-smart-wall-restoration.json').read_text('utf8'))
        test_generic_restoration(smart_wall, wall_registry, tables, 'one native Smart wall / two spawns / compatible entry script')

        source_loot = (ROOT / 'sql/updates/world/2026_10_03_00_world_campaign_source_loot_objects.sql').read_text('utf8')
        source_loot_registry = json.loads((ROOT / 'docs/audit-data/campaign-source-loot-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables,source_loot,source_loot_registry,'five source loot objects / quest hints / compatible native loot')
        wildcard_loot = (ROOT / 'sql/updates/world/2026_10_03_01_world_campaign_wildcard_loot_objects.sql').read_text('utf8')
        wildcard_registry = json.loads((ROOT / 'docs/audit-data/campaign-wildcard-loot-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables,wildcard_loot,wildcard_registry,'two wildcard loot objects / all native modes / preserved group and quest loot')

        council_books = (ROOT / 'sql/updates/world/2026_10_04_00_world_campaign_council_books.sql').read_text('utf8')
        council_registry = json.loads((ROOT / 'docs/audit-data/campaign-council-books-restoration.json').read_text('utf8'))
        test_simple_goober_models(tables,council_books,council_registry,'two council books / two exact terminal pages / quest-credit dependencies')

        conversations = (ROOT / 'sql/updates/world/2026_10_04_01_world_campaign_simple_conversations.sql').read_text('utf8')
        conversation_registry = json.loads((ROOT / 'docs/audit-data/campaign-simple-conversation-restoration.json').read_text('utf8'))
        test_simple_conversations(tables,conversations,conversation_registry)

        chains = (ROOT / 'sql/updates/world/2026_10_04_02_world_campaign_conversation_chains.sql').read_text('utf8')
        chain_registry = json.loads((ROOT / 'docs/audit-data/campaign-conversation-chain-restoration.json').read_text('utf8'))
        test_simple_conversations(tables,chains,chain_registry)

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
        test_gilneas_database(sql,checksum)
        test_visual_migration(sql,checksum)
        test_cage_state_restoration(sql,checksum)
        test_cage_state_restoration(sql,checksum,'campaign-fel-boiler-restoration.json','2026_10_08_03_world_campaign_fel_boiler_loot.sql')
        test_required_level_objects(sql,checksum)
        test_required_level_objects(sql,checksum,'campaign-scenario-object-restoration.json','2026_10_08_04_world_campaign_scenario_objects.sql')
        sql(f'DROP DATABASE `{DB}`;', False)


if __name__ == '__main__':
    main()
