#!/usr/bin/env python3
"""Source scene mapping conflicts/retries on an isolated disposable release database."""
from pathlib import Path


def test_campaign_scene_templates(sql,checksum):
    root=Path(__file__).resolve().parents[2]
    content=(root/'sql/updates/world/2026_10_08_05_world_campaign_scene_templates.sql').read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines();original=checksum(tables)
    assert sql('SELECT COUNT(*) FROM scene_template WHERE SceneId IN(1363,1547);').stdout.strip()=='0','Unexpected original scene mappings'
    def clear():sql('DELETE FROM scene_template WHERE SceneId IN(1363,1547);')
    def exact():
        assert sql("SELECT SceneId,Flags,ScriptPackageID,ScriptName FROM scene_template WHERE SceneId IN(1363,1547) ORDER BY SceneId;").stdout.splitlines()==['1363\t27\t1680\t','1547\t20\t1784\t']
    protected=[t for t in tables if t!='scene_template'];before=checksum(protected)
    sql(content);exact();once=checksum(tables);sql(content);assert checksum(tables)==once
    assert checksum(protected)==before
    for scene,flags,package in [(1363,27,1680),(1547,20,1784)]:
        for field,custom in [('Flags','0'),('ScriptPackageID',str(package+1)),('ScriptName',"'custom_scene'"),('ScriptName',"' '")]:
            clear();sql(f"INSERT INTO scene_template VALUES({scene},{flags},{package},'');")
            sql(f'UPDATE scene_template SET `{field}`={custom} WHERE SceneId={scene};')
            before=checksum(tables);error=sql(content,ok=False)
            assert 'Duplicate entry' in error.stderr and '_1kycore_scene_guard' in error.stderr,error.stderr
            assert checksum(tables)==before,'Scene conflict changed permanent rows'
        clear();sql(f"INSERT INTO scene_template VALUES({scene},{flags},{package},'');");sql(content);exact()
    for prefix in range(1,len(content.split(';'))):
        clear();sql(';'.join(content.split(';')[:prefix])+';');sql(content);exact()
    clear();assert checksum(tables)==original,'Scene test changed unrelated/release content'
    print('PASS: source scene templates; first/repeat, compatible partial state, conflicts, every interrupted prefix and unrelated tables preserved',flush=True)
