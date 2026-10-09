"""First/repeated/partial activation and conflict checks on a disposable world DB."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_brew_delivery(sql,checksum):
    registry=json.loads((ROOT/'docs/audit-data/campaign-brew-restoration.json').read_text('utf8'))
    restore=(ROOT/'sql/updates/world'/registry['migration']).read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines()
    owned=['gameobject_template','creature_template','spell_script_names']
    filters={'gameobject_template':'entry IN(268377,268378,268379)',
             'creature_template':'entry IN(119619,119620,119621)',
             'spell_script_names':'spell_id IN(237611,237613,237615)'}
    before=checksum(tables)
    for table in owned:sql(f'CREATE TABLE `_brew_saved_{table}` AS SELECT * FROM `{table}` WHERE {filters[table]};')
    def reset():
        for table in owned:
            sql(f'DELETE FROM `{table}` WHERE {filters[table]}; INSERT INTO `{table}` SELECT * FROM `_brew_saved_{table}`;')
    def snapshot():
        return sql('SELECT * FROM gameobject_template WHERE entry IN(268377,268378,268379) ORDER BY entry; SELECT * FROM creature_template WHERE entry IN(119619,119620,119621) ORDER BY entry; SELECT * FROM spell_script_names WHERE spell_id IN(237611,237613,237615) ORDER BY spell_id,ScriptName;').stdout
    def reject():
        saved=snapshot()
        failed=sql(restore,ok=False)
        assert '_1kycore_brew_guard' in failed.stderr,failed.stderr
        assert snapshot()==saved,'Guard failure changed delivery data'
    def verify():
        for row in registry['rows']:
            predicates=' AND '.join(('BINARY ' if key in ('AIName','ScriptName','IconName','castBarCaption','unk1') else '')+f'`{key}`={value}' for key,value in row.items() if key!='size')
            assert sql(f'SELECT COUNT(*) FROM gameobject_template WHERE {predicates} AND ABS(size-1.3)<0.000001;').stdout.strip()=='1'
        assert sql("SELECT COUNT(*) FROM creature_template WHERE entry IN(119619,119620,119621) AND ScriptName='npc_campaign_brew_companion' AND AIName='';").stdout.strip()=='3'
        assert sql("SELECT COUNT(*) FROM spell_script_names WHERE spell_id IN(237611,237613,237615) AND ScriptName='spell_campaign_brew_linked_summon';").stdout.strip()=='3'
    try:
        protected=[t for t in tables if t not in owned];safe=checksum(protected)
        sql(restore);verify();complete=checksum(tables)
        sql(restore);assert checksum(tables)==complete
        # Every owned field conflict rejects before changing NPC/spell dependencies.
        for field in registry['rows'][0]:
            if field=='entry':continue
            saved=sql(f'SELECT `{field}` FROM gameobject_template WHERE entry=268377;').stdout.strip()
            value="'custom'" if field in ('AIName','ScriptName','IconName','castBarCaption','unk1') else '42'
            sql(f'UPDATE gameobject_template SET `{field}`={value} WHERE entry=268377;');reject()
            value="'"+saved+"'" if field in ('AIName','ScriptName','IconName','castBarCaption','unk1') else saved
            sql(f'UPDATE gameobject_template SET `{field}`={value} WHERE entry=268377;')
        sql("UPDATE creature_template SET AIName='SmartAI' WHERE entry=119619;");reject();sql("UPDATE creature_template SET AIName='' WHERE entry=119619;")
        sql("UPDATE creature_template SET ScriptName='custom' WHERE entry=119620;");reject();sql("UPDATE creature_template SET ScriptName='npc_campaign_brew_companion' WHERE entry=119620;")
        sql("INSERT INTO spell_script_names VALUES(237611,'custom');");reject();sql("DELETE FROM spell_script_names WHERE spell_id=237611 AND ScriptName='custom';")
        sql('INSERT INTO gameobject_template_addon(entry) VALUES(268377);');reject();sql('DELETE FROM gameobject_template_addon WHERE entry=268377;')
        sql("INSERT INTO smart_scripts(entryorguid,source_type,id,comment) VALUES(119619,0,0,'custom');");reject();sql('DELETE FROM smart_scripts WHERE entryorguid=119619 AND source_type=0;')
        sql("INSERT INTO conditions(SourceTypeOrReferenceId,SourceEntry,Comment) VALUES(17,237611,'custom');");reject();sql('DELETE FROM conditions WHERE SourceTypeOrReferenceId=17 AND SourceEntry=237611;')
        sql("INSERT INTO gameobject(guid,id,map,ScriptName) VALUES(4290000090,268377,1514,'custom');");reject();sql('DELETE FROM gameobject WHERE guid=4290000090;')
        sql("INSERT INTO creature(guid,id,map,ScriptName) VALUES(4290000091,119619,1514,'custom');");reject();sql('DELETE FROM creature WHERE guid=4290000091;')
        # Existing localized labels and provenance are intentionally preserved.
        sql("UPDATE gameobject_template SET name='custom localized label',VerifiedBuild=26972 WHERE entry=268377;")
        sql(restore);assert sql('SELECT name,VerifiedBuild FROM gameobject_template WHERE entry=268377;').stdout.strip()=='custom localized label\t26972'
        reset()
        # Missing dependencies, unlike a recoverable interrupted prefix, must reject.
        for table,key,ident in [('creature_template','entry',119623),('quest_objectives','ID',289212),('gameobject_template','entry',268379)]:
            sql(f'CREATE TABLE `_brew_missing` AS SELECT * FROM `{table}` WHERE `{key}`={ident}; DELETE FROM `{table}` WHERE `{key}`={ident};')
            try:reject()
            finally:sql(f'INSERT INTO `{table}` SELECT * FROM `_brew_missing`; DROP TABLE `_brew_missing`;')
        # Interrupted NPC/auras prefix can retry without overwriting a custom value.
        boundary=restore.index('UPDATE gameobject_template a JOIN')
        sql(restore[:boundary]);sql(restore);verify()
        reset();sql(restore)
        sql("DELETE FROM spell_script_names WHERE spell_id=237615;");sql(restore);verify()
        assert checksum(protected)==safe,'Quest/spawn/AI/loot tables changed'
        print('PASS: brew SQL first/repeat/partial activation, all template fields, AI/spell conflicts, missing dependencies, labels and protected tables',flush=True)
    finally:
        reset()
        for table in owned:sql(f'DROP TABLE `_brew_saved_{table}`;')
        assert checksum(tables)==before,'Fixture failed to restore disposable release data'
