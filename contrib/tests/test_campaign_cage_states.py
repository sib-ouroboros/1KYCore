#!/usr/bin/env python3
"""Native cage models/animations against a disposable real-release database."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def test_cage_state_restoration(sql,checksum):
    registry=json.loads((ROOT/'docs/audit-data/campaign-cage-state-restoration.json').read_text('utf8'))
    schema=(ROOT/'sql/updates/world/2026_10_08_00_world_gameobject_state_animation.sql').read_text('utf8')
    visuals=(ROOT/'sql/updates/world/2026_10_05_03_world_gameobject_visual_fields.sql').read_text('utf8')
    restore=(ROOT/'sql/updates/world/2026_10_08_01_world_campaign_cage_state_animations.sql').read_text('utf8')
    ids=','.join(map(str,registry['entries']));tables=sql('SHOW TABLES;').stdout.splitlines();owned=['gameobject_template','gameobject_template_addon'];checks=owned+['quest_objectives','smart_scripts','gameobject','gameobject_questitem']
    before=checksum(tables)
    original_columns=sql("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon';").stdout.splitlines()
    new_columns=['SpellVisualID','SpellStateVisualID','StateWorldEffectID','SpellStateAnimID']
    original_addons=sql(f'SELECT * FROM gameobject_template_addon WHERE entry IN ({ids});').stdout
    assert not original_addons,'Unexpected clean-release addon ownership needs explicit review'
    def exact(table,rows):
        for row in rows:
            pred=' AND '.join(f'ABS(`{k}`-({v}))<=0.000001' if k=='size' else f'BINARY `{k}` <=> BINARY {v}' for k,v in row.items() if k!='VerifiedBuild')
            assert sql(f'SELECT COUNT(*) FROM `{table}` WHERE {pred};').stdout.strip()=='1',(table,row)
    def clear():
        sql(f'DELETE FROM gameobject_template_addon WHERE entry IN ({ids});')
        for row in registry['baseline']:
            sql('UPDATE gameobject_template SET '+','.join('`'+k+'`='+v for k,v in row.items() if k!='entry')+' WHERE entry='+row['entry']+';')
    def reject():
        saved=checksum(checks);failure=sql(restore,ok=False)
        assert '_1kycore_cage_guard' in failure.stderr,failure.stderr
        assert checksum(checks)==saved,'Rejected cage import changed permanent data'
    try:
        exact('gameobject_template',registry['baseline'])
        # Verify incompatible schema rejection before any alteration/data write.
        for definition in ['SMALLINT UNSIGNED NOT NULL DEFAULT 0','INT NOT NULL DEFAULT 0','INT UNSIGNED NULL DEFAULT 0','INT UNSIGNED NOT NULL DEFAULT 1']:
            sql('ALTER TABLE gameobject_template_addon ADD COLUMN SpellStateAnimID '+definition+';')
            saved=checksum(tables);failure=sql(schema,ok=False);assert '_1kycore_animation_schema_guard' in failure.stderr;assert checksum(tables)==saved
            sql('ALTER TABLE gameobject_template_addon DROP COLUMN SpellStateAnimID;')
        sql(visuals);sql(schema);saved=checksum(tables);sql(schema);assert checksum(tables)==saved
        protected=[t for t in tables if t not in owned];untouched=checksum(protected)
        sql(restore);exact('gameobject_template',registry['templates']);exact('gameobject_template_addon',registry['addons']);canonical=checksum(owned)
        sql(restore);assert checksum(owned)==canonical;assert checksum(protected)==untouched
        # Every content field of the first model and addon protects administrator customization.
        for table,row in [('gameobject_template',registry['templates'][0]),('gameobject_template_addon',registry['addons'][0])]:
            for key,value in row.items():
                if key in ['entry','VerifiedBuild']:continue
                altered="'custom'" if value.startswith("'") else str(float(value)+1) if key=='size' else str(int(value)+1)
                sql(f"UPDATE `{table}` SET `{key}`={altered} WHERE entry={row['entry']};");reject();sql(f"UPDATE `{table}` SET `{key}`={value} WHERE entry={row['entry']};")
        sql(f'UPDATE gameobject_template SET VerifiedBuild=12345 WHERE entry={registry["entries"][0]};');saved=checksum(owned);sql(restore);assert checksum(owned)==saved
        first=registry['addons'][0];sql('DELETE FROM gameobject_template_addon WHERE entry='+first['entry']+';');reject();sql('INSERT INTO gameobject_template_addon ('+','.join(first)+') VALUES ('+','.join(first.values())+');')
        for obj in registry['required_objectives']:
            sql('UPDATE quest_objectives SET Amount=99 WHERE ID='+obj['ID']+';');reject();sql('UPDATE quest_objectives SET Amount='+obj['Amount']+' WHERE ID='+obj['ID']+';')
        cid=registry['entries'][0]
        sql(f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES ({cid},1,0,64,33,1,'custom cage');")
        try:reject()
        finally:sql(f'DELETE FROM smart_scripts WHERE entryorguid={cid} AND source_type=1;')
        sql(f'INSERT INTO gameobject_questitem(GameObjectEntry,Idx,ItemId) VALUES ({cid},0,146310);')
        try:reject()
        finally:sql(f'DELETE FROM gameobject_questitem WHERE GameObjectEntry={cid};')
        spawn=sql(f'SELECT guid FROM gameobject WHERE id={cid} LIMIT 1;').stdout.strip()
        fixture_spawn=not spawn
        if fixture_spawn:
            spawn='19000001'
            assert sql('SELECT COUNT(*) FROM gameobject WHERE guid='+spawn+';').stdout.strip()=='0'
            sql(f'INSERT INTO gameobject(guid,id,map) VALUES ({spawn},{cid},1604);')
        if spawn:
            sql(f"UPDATE gameobject SET ScriptName='custom_cage' WHERE guid={spawn};")
            try:reject()
            finally:sql(f"UPDATE gameobject SET ScriptName='' WHERE guid={spawn};")
            sql(f"INSERT INTO smart_scripts(entryorguid,source_type,id,event_type,action_type,target_type,comment) VALUES (-{spawn},1,0,64,33,1,'custom spawn cage');")
            try:reject()
            finally:sql(f'DELETE FROM smart_scripts WHERE entryorguid=-{spawn} AND source_type=1;')
        if fixture_spawn:sql('DELETE FROM gameobject WHERE guid='+spawn+';')
        # Existing empty release addons can be upgraded only under exact baseline templates.
        clear();sql(f'INSERT INTO gameobject_template_addon(entry) VALUES ({registry["entries"][0]});');sql(restore);exact('gameobject_template',registry['templates']);exact('gameobject_template_addon',registry['addons']);assert checksum(owned)==canonical
        # Retry after only addons are published, and with one native template already published.
        clear();boundary=restore.index('UPDATE gameobject_template a JOIN');sql(restore[:boundary]);exact('gameobject_template',registry['baseline']);sql(restore);assert checksum(owned)==canonical
        clear();sql(restore[:boundary]);row=registry['templates'][0];sql('UPDATE gameobject_template SET '+','.join('`'+k+'`='+v for k,v in row.items() if k not in ['entry','VerifiedBuild'])+' WHERE entry='+row['entry']+';');sql(restore);assert checksum(owned)==canonical
        assert checksum(protected)==untouched
        print('PASS: three cage models/source animations, all field conflicts, six unchanged objectives, schema/repeat/interruption/provenance and protected NPC/quest/spawn data',flush=True)
    finally:
        clear()
        current=sql("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='gameobject_template_addon';").stdout.splitlines()
        for col in new_columns:
            if col in current and col not in original_columns:sql('ALTER TABLE gameobject_template_addon DROP COLUMN `'+col+'`;')
        assert checksum(tables)==before,'Disposable cage test baseline was not restored'
