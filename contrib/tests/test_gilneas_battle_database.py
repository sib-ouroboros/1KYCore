"""Native battle/Godfrey data on an explicitly disposable release schema only."""
from pathlib import Path
import json


def test_gilneas_battle_database(sql, checksum):
    root = Path(__file__).resolve().parents[2]
    battle = (root/'sql/updates/world/2026_10_07_00_world_gilneas_battle_source_data.sql').read_text('utf8')
    godfrey = (root/'sql/updates/world/2026_10_07_01_world_gilneas_godfrey_departure_route.sql').read_text('utf8')
    proof = json.loads((root/'docs/audit-data/gilneas-battle-source-restoration.json').read_text('utf8'))
    tables = sql('SHOW TABLES;').stdout.splitlines()
    other = [t for t in tables if t not in ('creature','waypoint_data')]
    untouched = checksum(other)
    foreign = sql('SELECT * FROM creature WHERE guid NOT IN (802761,802707,802754,802671,802670,802781,802822,802851) ORDER BY guid;').stdout
    sql('CREATE TABLE `_test_cinematic_liam_backup` AS SELECT * FROM creature WHERE guid=802851;')
    sql(battle)
    sql(godfrey)
    for actor in proof['spawns']:
        x,y,z,o = actor['position']
        assert sql(f'SELECT COUNT(*) FROM creature WHERE guid={actor["guid"]} AND id={actor["entry"]} AND map=654 AND PhaseId=187 AND PhaseGroup=0 AND ABS(position_x-({x}))<0.01 AND ABS(position_y-({y}))<0.01 AND ABS(position_z-({z}))<0.01 AND ABS(orientation-({o}))<0.01 AND MovementType=0 AND spawndist=0 AND spawntimesecs=90 AND VerifiedBuild=0;').stdout.strip()=='1',actor
    assert sql('SELECT COUNT(*) FROM creature WHERE guid=802851;').stdout.strip()=='0','Permanent cinematic Liam duplicate survived'
    routes = dict(proof['battle_routes'])
    routes['802361'] = proof['godfrey_route']['points']
    for path,points in routes.items():
        assert sql(f'SELECT COUNT(*) FROM waypoint_data WHERE id={path};').stdout.strip()==str(len(points)),path
        for point in points:
            x,y,z,o=point['position']
            assert sql(f'SELECT COUNT(*) FROM waypoint_data WHERE id={path} AND point={point["point"]} AND ABS(position_x-({x}))<0.01 AND ABS(position_y-({y}))<0.01 AND ABS(position_z-({z}))<0.01 AND ABS(orientation-({o}))<0.01 AND delay=0 AND move_type={point["move_type"]} AND action=0 AND action_chance=100;').stdout.strip()=='1',(path,point)
    assert checksum(other)==untouched,'Native restoration changed a non-target table'
    assert sql('SELECT * FROM creature WHERE guid NOT IN (802761,802707,802754,802671,802670,802781,802822,802851) ORDER BY guid;').stdout==foreign,'Unrelated spawn changed'
    before=checksum(tables);sql(battle);sql(godfrey)
    assert checksum(tables)==before,'Repeated import changed data'

    # Global preservation is checked above. Guard cases compare complete candidate rows
    # and their ownership/binding records, keeping this regression practical on a full dump.
    def target_snapshot():
        guids='802361,802761,802707,802754,802671,802670,802781,802822,802851'
        queries=[
            f'SELECT * FROM creature WHERE guid IN ({guids}) ORDER BY guid;',
            'SELECT * FROM waypoint_data WHERE id IN (3847401,3846901,802361) ORDER BY id,point;',
            'SELECT * FROM creature_template WHERE entry IN (37875,37876,38218,38415,38426,38465,38466,38469,38470,38474) ORDER BY entry;',
            f'SELECT * FROM creature_addon WHERE guid IN ({guids}) ORDER BY guid;',
            f'SELECT * FROM smart_scripts WHERE entryorguid IN (-802361,-802761,-802707,-802754,-802671,-802670,-802781,-802822,-802851) ORDER BY entryorguid,source_type,id;',
            f'SELECT * FROM game_event_creature WHERE guid IN ({guids}) ORDER BY guid,eventEntry;',
            f'SELECT * FROM pool_creature WHERE guid IN ({guids}) ORDER BY guid;',
            f'SELECT * FROM creature_formations WHERE leaderGUID IN ({guids}) OR memberGUID IN ({guids}) ORDER BY memberGUID;',
            'SELECT * FROM creature_queststarter WHERE id=38474 ORDER BY quest;',
            'SELECT * FROM creature_questender WHERE id=38474 ORDER BY quest;',
        ]
        return [sql(query).stdout for query in queries]

    first=proof['spawns'][0]
    guid=first['guid'];entry=first['entry'];script=first['script'];ox,oy,oz,oo=first['old_position']
    reset=f"UPDATE creature SET position_x={ox},position_y={oy},position_z={oz},orientation={oo},MovementType={first['old_movement']},spawndist={first['old_distance']},spawntimesecs=7200,map=654,PhaseId=187,PhaseGroup=0,ScriptName='' WHERE guid={guid};"
    guards=[
        (f"UPDATE creature_template SET ScriptName='custom_battle' WHERE entry={entry};",f"UPDATE creature_template SET ScriptName='{script}' WHERE entry={entry};"),
        (f"UPDATE creature_template SET AIName='SmartAI' WHERE entry={entry};",f"UPDATE creature_template SET AIName='' WHERE entry={entry};"),
        (f"UPDATE creature SET ScriptName='custom_spawn' WHERE guid={guid};",reset),
        (f'UPDATE creature SET position_x=position_x+1 WHERE guid={guid};',reset),
        (f'UPDATE creature SET orientation=orientation+1 WHERE guid={guid};',reset),
        (f'UPDATE creature SET spawntimesecs=600 WHERE guid={guid};',reset),
        (f'UPDATE creature SET MovementType=2 WHERE guid={guid};',reset),
        (f'UPDATE creature SET spawndist=12 WHERE guid={guid};',reset),
        (f'UPDATE creature SET map=0 WHERE guid={guid};',reset),
        (f'UPDATE creature SET PhaseId=188 WHERE guid={guid};',reset),
        (f'UPDATE creature SET PhaseGroup=440 WHERE guid={guid};',reset),
        (f'INSERT INTO creature_addon (guid,path_id) VALUES ({guid},999999);',f'DELETE FROM creature_addon WHERE guid={guid};'),
        (f"INSERT INTO smart_scripts (entryorguid,source_type,id,comment) VALUES (-{guid},0,0,'fixture');",f'DELETE FROM smart_scripts WHERE entryorguid=-{guid};'),
        (f'INSERT INTO game_event_creature (eventEntry,guid) VALUES (12,{guid});',f'DELETE FROM game_event_creature WHERE guid={guid};'),
        (f"INSERT INTO pool_creature (guid,pool_entry,chance,description) VALUES ({guid},1234,0,'fixture');",f'DELETE FROM pool_creature WHERE guid={guid};'),
        (f'INSERT INTO creature_formations (leaderGUID,memberGUID,dist,angle,groupAI) VALUES ({guid},{guid},0,0,2);',f'DELETE FROM creature_formations WHERE memberGUID={guid};'),
    ]
    for setup,cleanup in guards:
        sql(reset);sql(setup);before=target_snapshot();sql(battle)
        assert target_snapshot()==before,('Custom battle spawn/ownership was overwritten',setup)
        sql(cleanup);sql(reset);sql(battle)

    for path in (3847401,3846901,802361):
        sql(f'DELETE FROM waypoint_data WHERE id={path}; INSERT INTO waypoint_data (id,point,position_x,position_y,position_z) VALUES ({path},99,1,2,3);')
        before=target_snapshot();sql(battle if path!=802361 else godfrey)
        assert target_snapshot()==before,'Existing partial/custom route was mixed with source data'
        sql(f'DELETE FROM waypoint_data WHERE id={path};')
        sql(battle if path!=802361 else godfrey)

    for entry,script,path in [(38474,'npc_prince_liam_greymane_38474',3847401),(38469,'npc_lady_sylvanas_windrunner_38469',3846901)]:
        for setup in (f"UPDATE creature_template SET ScriptName='custom_route_actor' WHERE entry={entry};",f"UPDATE creature_template SET AIName='SmartAI' WHERE entry={entry};"):
            sql(f'DELETE FROM waypoint_data WHERE id={path};');sql(setup)
            before=target_snapshot();sql(battle);assert target_snapshot()==before,'Custom route actor changed'
            sql(f"UPDATE creature_template SET ScriptName='{script}',AIName='' WHERE entry={entry};");sql(battle)

    for setup,cleanup in [
        ("UPDATE creature_template SET ScriptName='custom_godfrey' WHERE entry=37875;","UPDATE creature_template SET ScriptName='npc_gilneas_godfrey_departure' WHERE entry=37875;"),
        ("UPDATE creature_template SET AIName='SmartAI' WHERE entry=37875;","UPDATE creature_template SET AIName='' WHERE entry=37875;"),
        ("UPDATE creature_template SET ScriptName='custom_genn' WHERE entry=37876;","UPDATE creature_template SET ScriptName='npc_king_genn_greymane_37876' WHERE entry=37876;"),
        ("UPDATE creature_template SET AIName='SmartAI' WHERE entry=37876;","UPDATE creature_template SET AIName='' WHERE entry=37876;"),
        ("UPDATE creature SET ScriptName='custom_godfrey_spawn' WHERE guid=802361;","UPDATE creature SET ScriptName='' WHERE guid=802361;"),
        ('UPDATE creature SET PhaseId=187 WHERE guid=802361;','UPDATE creature SET PhaseId=186 WHERE guid=802361;'),
        ('UPDATE creature SET position_x=position_x+1 WHERE guid=802361;','UPDATE creature SET position_x=position_x-1 WHERE guid=802361;'),
        ('INSERT INTO creature_addon (guid,path_id) VALUES (802361,999999);','DELETE FROM creature_addon WHERE guid=802361;'),
        ("INSERT INTO smart_scripts (entryorguid,source_type,id,comment) VALUES (-802361,0,0,'fixture');",'DELETE FROM smart_scripts WHERE entryorguid=-802361;'),
    ]:
        sql('DELETE FROM waypoint_data WHERE id=802361;');sql(setup)
        before=target_snapshot();sql(godfrey);assert target_snapshot()==before,('Custom Godfrey data changed',setup)
        sql(cleanup);sql(godfrey)

    for setup,cleanup in [
        ("UPDATE creature_template SET ScriptName='custom_cinematic' WHERE entry=38474;","UPDATE creature_template SET ScriptName='npc_prince_liam_greymane_38474' WHERE entry=38474;"),
        ('UPDATE creature SET position_x=position_x+1 WHERE guid=802851;',''),
        ('INSERT INTO creature_addon (guid) VALUES (802851);','DELETE FROM creature_addon WHERE guid=802851;'),
        ('INSERT INTO creature_queststarter (id,quest) VALUES (38474,999999);','DELETE FROM creature_queststarter WHERE id=38474 AND quest=999999;'),
        ('INSERT INTO creature_questender (id,quest) VALUES (38474,999999);','DELETE FROM creature_questender WHERE id=38474 AND quest=999999;'),
    ]:
        sql('INSERT INTO creature SELECT * FROM `_test_cinematic_liam_backup`;');sql(setup)
        before=target_snapshot();sql(battle);assert target_snapshot()==before,('Custom/dependent cinematic spawn deleted',setup)
        sql(cleanup);sql('DELETE FROM creature WHERE guid=802851;')
    sql('DROP TABLE `_test_cinematic_liam_backup`;')
    print('PASS: battle/Godfrey source SQL first/repeat, native coordinates/routes, scoped duplicate, custom actor/spawn/timer/ownership/route/quest and unrelated preservation')
