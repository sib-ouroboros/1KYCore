#!/usr/bin/env python3
"""Disposable MySQL regression for optional GO visual schema and four restorations."""
import json
import re
from pathlib import Path


def test_visual_migration(sql, checksum):
    root=Path(__file__).resolve().parents[2]
    registry=json.loads((root/'docs/audit-data/campaign-native-visual-restoration.json').read_text('utf8'))
    schema=(root/'sql/updates/world/2026_10_05_03_world_gameobject_visual_fields.sql').read_text('utf8')
    content=(root/'sql/updates/world/2026_10_05_04_world_campaign_native_visuals.sql').read_text('utf8')
    loader_source=(root/'src/server/game/Globals/ObjectMgr.cpp').read_text('latin1')
    loader_query=re.search(r'WorldDatabase.Query\("(SELECT COUNT\(\*\) FROM information_schema.COLUMNS[^"]+)"\)',loader_source)[1]
    columns=['SpellVisualID','SpellStateVisualID','StateWorldEffectID']
    ids=','.join(map(str,registry['entries']));missing=','.join(map(str,registry['missing_template_entries']))
    guids=','.join(s['guid'] for s in registry['spawns'])
    all_tables=sql('SHOW TABLES;').stdout.splitlines();before=checksum(all_tables)
    owned=['gameobject_template','gameobject_template_addon','gameobject']
    protected=checksum([t for t in all_tables if t not in owned])
    checks=owned+['quest_template','quest_objectives','smart_scripts','gameobject_questitem']
    assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE entry IN ({missing});').stdout.strip()=='0'
    assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid IN ({guids});').stdout.strip()=='0'
    assert sql(f'SELECT COUNT(*) FROM gameobject_template_addon WHERE entry IN ({ids});').stdout.strip()=='0'
    def insert(table,row):
        sql('INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');')
    def restore_templates():
        sql(f'DELETE FROM gameobject_template WHERE entry IN ({missing});')
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({ids});')
        sql(f'DELETE FROM gameobject WHERE guid IN ({guids});')
        for row in registry['baseline']:
            sql('UPDATE gameobject_template SET '+','.join('`'+k+'`='+v for k,v in row.items() if k!='entry')+' WHERE entry='+row['entry']+';')
    def columns_present():
        return sql("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon' AND COLUMN_NAME IN ('SpellVisualID','SpellStateVisualID','StateWorldEffectID') ORDER BY COLUMN_NAME;").stdout.splitlines()
    def reject():
        original=checksum(checks);error=sql(content,ok=False);assert '_1kycore_visual_guard' in error.stderr,error.stderr;assert checksum(checks)==original
    def exact_rows(table,rows):
        for row in rows:
            filters=[]
            for key,value in row.items():
                if key=='VerifiedBuild':continue  # Compatible provenance is deliberately preserved.
                if key in ('size','position_x','position_y','position_z','orientation','rotation0','rotation1','rotation2','rotation3'):
                    filters.append(f'ABS(`{key}`-({value}))<=0.01')
                else:filters.append(f'BINARY `{key}` <=> BINARY {value}')
            assert sql('SELECT COUNT(*) FROM '+table+' WHERE '+' AND '.join(filters)+';').stdout.strip()=='1',(table,row)
    try:
        assert not columns_present(),'Schema fixture must start at the release six-column addon'
        assert sql(loader_query).stdout.strip()=='0'
        # Unknown type, nullable and missing-default columns reject before other DDL.
        for definition in ["VARCHAR(20) NOT NULL DEFAULT '0'",'INT UNSIGNED NULL DEFAULT 0','INT UNSIGNED NOT NULL']:
            sql('ALTER TABLE gameobject_template_addon ADD COLUMN SpellVisualID '+definition+';')
            try:
                ddl=sql('SHOW CREATE TABLE gameobject_template_addon;').stdout
                error=sql(schema,ok=False);assert '_1kycore_visual_schema_guard' in error.stderr
                assert sql('SHOW CREATE TABLE gameobject_template_addon;').stdout==ddl
                assert columns_present()==['SpellVisualID']
            finally:sql('ALTER TABLE gameobject_template_addon DROP COLUMN SpellVisualID;')
        # Interrupted DDL and full repeat both preserve row contents.
        sql('ALTER TABLE gameobject_template_addon ADD COLUMN SpellVisualID INT UNSIGNED NOT NULL DEFAULT 0;')
        assert sql(loader_query).stdout.strip()=='1'
        sql(schema);assert set(columns_present())==set(columns)
        assert sql(loader_query).stdout.strip()=='3'
        ddl=sql('SHOW CREATE TABLE gameobject_template_addon;').stdout;data=checksum(['gameobject_template_addon']);sql(schema)
        assert checksum(['gameobject_template_addon'])==data and sql('SHOW CREATE TABLE gameobject_template_addon;').stdout==ddl
        assert sql('SELECT COUNT(*) FROM gameobject_template_addon WHERE SpellVisualID<>0 OR SpellStateVisualID<>0 OR StateWorldEffectID<>0;').stdout.strip()=='0'
        unrelated_addons=sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({ids}) ORDER BY entry;').stdout
        unrelated_templates=sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({ids}) ORDER BY entry;').stdout
        unrelated_spawns=sql(f'SELECT * FROM gameobject WHERE guid NOT IN ({guids}) ORDER BY guid;').stdout
        sql(content);exact_rows('gameobject_template',registry['templates']);exact_rows('gameobject_template_addon',registry['addons']);exact_rows('gameobject',registry['spawns'])
        assert sql('SELECT VerifiedBuild FROM gameobject_template WHERE entry=267180;').stdout.strip()==registry['baseline'][0]['VerifiedBuild']
        canonical=checksum(checks);sql(content);assert checksum(checks)==canonical
        for field in ('SpellVisualID','SpellStateVisualID','StateWorldEffectID','flags','WorldEffectID'):
            row=registry['addons'][0];sql(f'UPDATE gameobject_template_addon SET `{field}`=999999 WHERE entry={row["entry"]};')
            try:reject()
            finally:sql(f'UPDATE gameobject_template_addon SET `{field}`={row[field]} WHERE entry={row["entry"]};')
        for field in ('name','Data32','displayId','ScriptName'):
            row=registry['templates'][0];value="'custom'" if field in ('name','ScriptName') else '999999'
            sql(f'UPDATE gameobject_template SET `{field}`={value} WHERE entry={row["entry"]};')
            try:reject()
            finally:sql(f'UPDATE gameobject_template SET `{field}`={row[field]} WHERE entry={row["entry"]};')
        objective=registry['required_objectives'][0]
        for field in ('QuestID','Type','StorageIndex','ObjectID','Amount','Flags','Flags2'):
            sql(f'UPDATE quest_objectives SET `{field}`={int(objective[field])+1} WHERE ID={objective["ID"]};')
            try:reject()
            finally:sql(f'UPDATE quest_objectives SET `{field}`={objective[field]} WHERE ID={objective["ID"]};')
        for actor in [267180,-210302577,-int(registry['spawns'][0]['guid'])]:
            sql(f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({actor},1,99,64,1,1,'custom visual GO');")
            try:reject()
            finally:sql(f'DELETE FROM smart_scripts WHERE entryorguid={actor} AND source_type=1 AND id=99;')
        row=registry['spawns'][0];sql(f'UPDATE gameobject SET map=9999 WHERE guid={row["guid"]};')
        try:reject()
        finally:sql(f'UPDATE gameobject SET map={row["map"]} WHERE guid={row["guid"]};')
        row=registry['addons'][0];sql(f'DELETE FROM gameobject_template_addon WHERE entry={row["entry"]};')
        try:reject()
        finally:insert('gameobject_template_addon',row)
        # Partial dependency publication retries; foreign GUID ownership stops all writes.
        restore_templates();split=content.index('INSERT INTO `gameobject_template` (`entry`');sql(content[:split]);sql(content);assert checksum(checks)==canonical
        restore_templates();row=dict(registry['spawns'][0]);row['id']='9000010';insert('gameobject',row)
        try:reject()
        finally:sql(f'DELETE FROM gameobject WHERE guid={row["guid"]};')
        sql(content);assert checksum(checks)==canonical
        assert sql(f'SELECT * FROM gameobject_template_addon WHERE entry NOT IN ({ids}) ORDER BY entry;').stdout==unrelated_addons
        assert sql(f'SELECT * FROM gameobject_template WHERE entry NOT IN ({ids}) ORDER BY entry;').stdout==unrelated_templates
        assert sql(f'SELECT * FROM gameobject WHERE guid NOT IN ({guids}) ORDER BY guid;').stdout==unrelated_spawns
        assert checksum([t for t in all_tables if t not in owned])==protected
        print('PASS: nine-column schema conflicts/retry, four visual objects, ten spawns, exact data, all objective/script/GUID/addon guards, repeat/partial imports and unrelated data',flush=True)
    finally:
        restore_templates()
        for column in columns_present():sql('ALTER TABLE gameobject_template_addon DROP COLUMN `'+column+'`;')
        assert checksum(all_tables)==before,'Scratch baseline mismatch'
        print('Restored release schema and all248 baseline tables',flush=True)
