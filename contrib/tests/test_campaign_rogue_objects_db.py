"""Complete rogue object chains on an explicitly disposable release database."""
import json
from pathlib import Path


def test_campaign_rogue_objects(sql,checksum,go_test,conversation_test):
    root=Path(__file__).resolve().parents[2]
    def migration(name):return (root/'sql/updates/world'/name).read_text('utf8')
    def registry(name):return json.loads((root/'docs/audit-data'/name).read_text('utf8'))
    # Schema updates are themselves guarded and are prerequisites in normal updater order.
    sql(migration('2026_10_07_02_world_conversation_line_padding.sql'))
    sql(migration('2026_10_05_03_world_gameobject_visual_fields.sql'))
    sql(migration('2026_10_08_00_world_gameobject_state_animation.sql'))
    tables=sql('SHOW TABLES;').stdout.splitlines()
    convo=migration('2026_10_08_06_world_campaign_gunpowder_conversation.sql')
    go=migration('2026_10_08_07_world_campaign_rogue_objects.sql')
    cr=registry('campaign-gunpowder-conversation-restoration.json')
    gr=registry('campaign-rogue-object-restoration.json')
    def reject():
        before=checksum(tables);error=sql(go,ok=False)
        assert '_1kycore_model_guard' in error.stderr,error.stderr
        assert checksum(tables)==before,'Incomplete chain modified permanent rows'
    reject()  # Neither conversation nor scenes are available yet.
    conversation_test(tables,convo,cr)
    reject()  # Complete conversation alone cannot enable incomplete scene effects.
    sql(migration('2026_10_08_05_world_campaign_scene_templates.sql'))
    for scene in (1363,1547):
        sql(f'UPDATE scene_template SET ScriptName=\'custom\' WHERE SceneId={scene};')
        reject();sql(f"UPDATE scene_template SET ScriptName='' WHERE SceneId={scene};")
    # Missing or incompatible cinematic dependencies reject before changing either GO.
    for table,field,key,alteration in [
        ('conversation_template','Id',4269,"LastLineEndTime=1"),
        ('conversation_actor_template','Id',56913,'CreatureModelId=1'),
        ('conversation_line_template','Id',9723,'Padding=1'),
        ('conversation_line_template','Id',9724,'StartTime=1'),
        ('conversation_actors','ConversationId',4269,'ConversationActorGuid=1')]:
        sql(f'CREATE TABLE saved_rogue_row AS SELECT * FROM `{table}` WHERE `{field}`={key};')
        try:
            sql(f'UPDATE `{table}` SET {alteration} WHERE `{field}`={key};');reject()
            sql(f'DELETE FROM `{table}` WHERE `{field}`={key};');reject()
        finally:
            sql(f'DELETE FROM `{table}` WHERE `{field}`={key}; INSERT INTO `{table}` SELECT * FROM saved_rogue_row; DROP TABLE saved_rogue_row;')
    # Per-spawn custom script bindings must not be activated by the model restoration.
    guid=gr['protected_spawn_guids'][0]
    assert sql(f'SELECT COUNT(*) FROM gameobject WHERE guid={guid} AND id=252017;').stdout.strip()=='1'
    sql(f"UPDATE gameobject SET ScriptName='custom_object' WHERE guid={guid};")
    try:reject()
    finally:sql(f"UPDATE gameobject SET ScriptName='' WHERE guid={guid};")
    # Optional addon fields cannot carry unrelated visual behavior into a restored model.
    addon=gr['addons'][0];columns=list(addon)
    sql('INSERT INTO gameobject_template_addon ('+','.join(columns)+') VALUES ('+','.join(addon.values())+');')
    try:
        for field in ('SpellVisualID','SpellStateVisualID','StateWorldEffectID','SpellStateAnimID'):
            sql(f'UPDATE gameobject_template_addon SET `{field}`=1 WHERE entry=252017;');reject()
            sql(f'UPDATE gameobject_template_addon SET `{field}`=0 WHERE entry=252017;')
    finally:sql('DELETE FROM gameobject_template_addon WHERE entry=252017;')
    go_test(tables,go,gr,'two complete rogue object chains / source personal conversation / native scene effects')
    print('PASS: incomplete scenes/conversation, customized dependencies, addon visuals and per-spawn scripts reject before GO publication',flush=True)
