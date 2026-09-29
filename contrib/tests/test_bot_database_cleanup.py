#!/usr/bin/env python3
"""Exercise cleanup SQL against a disposable MySQL server (never production)."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'test_1kycore_bot_cleanup_'


def query(sql, database=None):
    command = ['mysql', '--protocol=TCP', '--host=127.0.0.1', '--port=' + os.environ.get('MYSQL_TEST_PORT', '3306'),
               '--user=root', '--batch', '--skip-column-names', '--default-character-set=utf8mb4']
    if database:
        assert database.startswith(PREFIX)
        command.append(database)
    result = subprocess.run(command, input=sql, text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def file(path, database):
    return query((ROOT / path).read_text(encoding='utf-8'), database)


def main():
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER') != '1':
        raise SystemExit('Requires MYSQL_DISPOSABLE_TEST_SERVER=1 and a disposable localhost MySQL server.')
    for scenario in ('fresh', 'existing', 'empty'):
        databases = {kind: PREFIX + scenario + '_' + kind for kind in ('auth', 'world', 'characters')}
        for database in databases.values():
            query(f'DROP DATABASE IF EXISTS `{database}`; CREATE DATABASE `{database}` CHARACTER SET utf8mb4;')
            query('CREATE TABLE gameplay_sentinel (id INT PRIMARY KEY, value VARCHAR(40)); INSERT INTO gameplay_sentinel VALUES (7, "keep player data");', database)
        auth, world, characters = (databases[k] for k in ('auth', 'world', 'characters'))
        if scenario != 'fresh':
            query("CREATE TABLE toolip (ip VARCHAR(15)); INSERT INTO toolip VALUES ('192.0.2.42');", auth)
            file('contrib/tests/fixtures/legacy-arena-positions.sql', world)
            if scenario == 'empty':
                query('DELETE FROM aiwaypoints;', world)
            else:
                file('contrib/tests/fixtures/legacy-capital-route.sql', world)
                query("UPDATE aiwaypoints SET x = 42 WHERE entry = 72; UPDATE aiwaypoints SET x = 123 WHERE entry = 1000; UPDATE aiwaypoints SET helpText = 'custom route' WHERE entry = 1001; DELETE FROM aiwaypoints WHERE entry = 7;", world)
            for kind, tables in [('auth', ['playerbot_names', 'playerbot_arena']), ('world', ['ai_playerbot_names', 'ai_playerbot_locks']), ('characters', ['capital_siege_state', 'capital_siege_history'])]:
                for table in tables:
                    query(f'CREATE TABLE `{table}` (id INT); INSERT INTO `{table}` VALUES (1);', databases[kind])
        # Changed historical hashes cause reapplication. Repeat the whole sequence to test idempotence.
        snapshots = []
        for _ in range(2):
            for path, db in [('auth/2025_08_24_00_auth.sql', auth), ('auth/2025_10_27_00_auth.sql', auth),
                             ('world/2025_08_24_00_world.sql', world), ('characters/2026_08_25_00_characters.sql', characters)]:
                file('sql/updates/' + path, db)
            for kind, database in databases.items():
                file(f'sql/updates/{kind}/2026_09_29_00_{kind}_remove_bot_tables.sql', database)
                assert query('SELECT value FROM gameplay_sentinel WHERE id=7;', database) == 'keep player data'
                assert query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('playerbot_names','playerbot_arena','ai_playerbot_names','ai_playerbot_locks','capital_siege_state','capital_siege_history');", database) == '0'
            assert query('SELECT COUNT(*) FROM toolip;', auth) == ('0' if scenario == 'fresh' else '1')
            if scenario != 'fresh':
                assert query('SELECT ip FROM toolip;', auth) == '192.0.2.42'
            if scenario == 'fresh':
                assert query('SELECT COUNT(*) FROM aiwaypoints;', world) == '61'
                assert query('SELECT map FROM aiwaypoints WHERE entry IN (72,73) ORDER BY entry;', world) == '617\n617'
            elif scenario == 'empty':
                assert query('SELECT COUNT(*) FROM aiwaypoints;', world) == '0'
            else:
                assert query('SELECT COUNT(*) FROM aiwaypoints;', world) == '62'
                assert query('SELECT x FROM aiwaypoints WHERE entry=72;', world) == '42'
                assert query('SELECT COUNT(*) FROM aiwaypoints WHERE entry=7;', world) == '0'
                assert query('SELECT entry FROM aiwaypoints WHERE entry >= 1000 ORDER BY entry;', world) == '1000\n1001'
            snapshots.append(query('SELECT * FROM aiwaypoints ORDER BY entry;', world))
        assert snapshots[0] == snapshots[1]
        # Fresh seed values must exactly match the pre-cleanup baseline.
        if scenario == 'fresh':
            baseline = PREFIX + 'baseline'
            query(f'DROP DATABASE IF EXISTS `{baseline}`; CREATE DATABASE `{baseline}` CHARACTER SET utf8mb4;')
            file('contrib/tests/fixtures/legacy-arena-positions.sql', baseline)
            assert snapshots[0] == query('SELECT * FROM aiwaypoints ORDER BY entry;', baseline)
            query(f'DROP DATABASE `{baseline}`;')
        for database in databases.values():
            query(f'DROP DATABASE `{database}`;')
        print(f'PASS: {scenario}: data preservation, module removal and repeat application')


if __name__ == '__main__':
    main()
