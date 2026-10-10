"""Expanded data repair guards; caller supplies an isolated release world copy."""
from pathlib import Path

TARGETS=(36488,37685,37686,37692,37716,37718,37733,37735,38022,38210,38420)

def test_gilneas_expanded_database(sql,checksum):
    root=Path(__file__).resolve().parents[2]
    scaling=(root/'sql/updates/world/2026_10_10_01_world_gilneas_enemy_scaling.sql').read_text('utf8')
    actions=(root/'sql/updates/world/2026_10_10_02_world_gilneas_horse_action_xp.sql').read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines()
    ids=','.join(map(str,TARGETS))
    sql('DELETE FROM creature_template_scaling WHERE Entry IN('+ids+');')
    foreign=sql('SELECT * FROM creature_template_scaling WHERE Entry NOT IN('+ids+') ORDER BY Entry;').stdout
    other=checksum([t for t in tables if t!='creature_template_scaling'])
    sql(scaling)
    assert sql('SELECT Entry,LevelScalingMin,LevelScalingMax,LevelScalingDeltaMin,LevelScalingDeltaMax FROM creature_template_scaling WHERE Entry IN('+ids+') ORDER BY Entry;').stdout.splitlines()==[f'{i}\t5\t20\t0\t0' for i in TARGETS]
    assert other==checksum([t for t in tables if t!='creature_template_scaling'])
    assert foreign==sql('SELECT * FROM creature_template_scaling WHERE Entry NOT IN('+ids+') ORDER BY Entry;').stdout
    before=checksum(tables);sql(scaling);assert before==checksum(tables)
    sql('UPDATE creature_template_scaling SET LevelScalingMax=12,LevelScalingDeltaMax=2 WHERE Entry IN('+ids+');')
    before=checksum(tables);sql(scaling);assert before==checksum(tables),'custom scaling changed'
    sql('DELETE FROM creature_template_scaling WHERE Entry=38022;')
    for change,restore in [
        ('UPDATE creature_template SET maxlevel=19 WHERE entry=38022;','UPDATE creature_template SET maxlevel=20 WHERE entry=38022;'),
        ('UPDATE creature_template SET faction=35 WHERE entry=38022;','UPDATE creature_template SET faction=2213 WHERE entry=38022;'),
        ('UPDATE creature_template SET DamageModifier=2 WHERE entry=38022;','UPDATE creature_template SET DamageModifier=1 WHERE entry=38022;'),
        ('UPDATE creature SET map=0 WHERE id=38022;','UPDATE creature SET map=654 WHERE id=38022;')]:
        sql(change);before=checksum(tables);sql(scaling);assert before==checksum(tables),'scaling guard ignored';sql(restore)
    guid=sql('SELECT MIN(guid) FROM creature WHERE id=38022;').stdout.strip()
    sql('UPDATE creature SET map=0 WHERE guid='+guid+';');before=checksum(tables);sql(scaling);assert before==checksum(tables),'mixed-map enemy changed';sql('UPDATE creature SET map=654 WHERE guid='+guid+';')
    # Exercise existing bindings, empty slot and all other bit flags.
    sql("UPDATE creature_template SET AIName='',ScriptName='npc_mountain_horse_36540',spell1=0 WHERE entry=36540;")
    original=sql('SELECT entry,flags_extra FROM creature_template WHERE entry IN(35188,35456,35170,35167) ORDER BY entry;').stdout.splitlines()
    untouched=checksum([t for t in tables if t!='creature_template'])
    sql(actions)
    assert sql('SELECT spell1 FROM creature_template WHERE entry=36540;').stdout.strip()=='68903'
    expected=[line.split('\t')[0]+'\t'+str(int(line.split('\t')[1])&~64) for line in original]
    assert sql('SELECT entry,flags_extra FROM creature_template WHERE entry IN(35188,35456,35170,35167) ORDER BY entry;').stdout.splitlines()==expected
    assert untouched==checksum([t for t in tables if t!='creature_template'])
    before=checksum(tables);sql(actions);assert before==checksum(tables)
    sql('UPDATE creature_template SET spell1=172 WHERE entry=36540;');before=checksum(tables);sql(actions);assert before==checksum(tables),'custom action overwritten'
    sql("UPDATE creature_template SET spell1=0,ScriptName='custom_horse' WHERE entry=36540;");before=checksum(tables);sql(actions);assert before==checksum(tables),'custom script action overwritten'
    sql("UPDATE creature_template SET ScriptName='npc_mountain_horse_36540',VehicleId=999 WHERE entry=36540;");before=checksum(tables);sql(actions);assert before==checksum(tables),'custom vehicle action overwritten'
    dialogue=(root/'sql/updates/world/2026_10_10_03_world_gilneas_genn_dialogue.sql').read_text('utf8')
    before=checksum([t for t in tables if t!='creature_text'])
    sql(dialogue)
    assert sql('SELECT GroupID,BroadcastTextID FROM creature_text WHERE CreatureID=36332 ORDER BY GroupID,ID;').stdout.splitlines()==['0\t36340','1\t36341']
    assert before==checksum([t for t in tables if t!='creature_text'])
    before=checksum(tables);sql(dialogue);assert before==checksum(tables)
    sql('UPDATE creature_text SET BroadcastTextID=1 WHERE CreatureID=36332 AND GroupID=0 AND ID=0;')
    before=checksum(tables);sql(dialogue);assert before==checksum(tables),'custom Genn binding overwritten'
    print('PASS: Genn question36340 and answer36341, repeat/custom/locale preservation')
    print('PASS: 11 enemies, native bounds/modifier preservation, custom/mixed-map guards, horse action and XP flag idempotency')
