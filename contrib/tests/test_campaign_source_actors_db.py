"""Conflict and retry checks for source actors on a disposable release copy."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_source_actor_conversations(sql, checksum):
    registry=json.loads((ROOT/'docs/audit-data/campaign-source-actor-conversations.json').read_text('utf8'))
    restore=(ROOT/'sql/updates/world/2026_10_09_00_world_campaign_source_actor_conversations.sql').read_text('utf8')
    schema=(ROOT/'sql/updates/world/2026_10_07_02_world_conversation_line_padding.sql').read_text('utf8')
    tables=sql('SHOW TABLES;').stdout.splitlines()
    rows=registry['rows'];owned=list(rows)
    keys={t:','.join(x['Id'] for x in data) for t,data in rows.items()}
    assert all(sql(f'SELECT COUNT(*) FROM `{t}` WHERE Id IN({keys[t]});').stdout.strip()=='0' for t in owned)
    before=checksum(tables)
    had_padding=sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding';").stdout.strip()=='1'
    def reject():
        saved=checksum(owned+['conversation_actors','conversation_actor_template'])
        failed=sql(restore,ok=False)
        assert '_1kycore_source_actor_guard' in failed.stderr,failed.stderr
        assert checksum(owned+['conversation_actors','conversation_actor_template'])==saved
    def clear():
        for t in reversed(owned):sql(f'DELETE FROM `{t}` WHERE Id IN({keys[t]});')
    def verify():
        for t,data in rows.items():
            for row in data:
                predicates=' AND '.join(('BINARY ' if k=='ScriptName' else '')+'`'+k+'`='+v for k,v in row.items() if k!='VerifiedBuild')
                assert sql(f'SELECT COUNT(*) FROM `{t}` WHERE {predicates};').stdout.strip()=='1'
    try:
        if not had_padding:reject()
        sql(schema)
        protected=[t for t in tables if t not in owned]
        safe=checksum(protected)
        sql(restore);verify();complete=checksum(tables)
        sql(restore);assert checksum(tables)==complete
        # The existing actor51642 has different content: no global replacement.
        assert checksum(protected)==safe
        for t,data in rows.items():
            for row in data:
                for field in row:
                    if field in ('Id','VerifiedBuild'):continue
                    modified="'custom'" if field=='ScriptName' else str(int(row[field])+1)
                    sql(f"UPDATE `{t}` SET `{field}`={modified} WHERE Id={row['Id']};")
                    reject()
                    sql(f"UPDATE `{t}` SET `{field}`={row[field]} WHERE Id={row['Id']};")
        for cid in registry['entries']:
            sql(f'INSERT INTO conversation_actors(ConversationId,ConversationActorGuid,Idx) VALUES({cid},1,0);')
            try:reject()
            finally:sql(f'DELETE FROM conversation_actors WHERE ConversationId={cid};')
        for entry in registry['required_creatures']:
            assert sql('SELECT COUNT(*) FROM creature_template WHERE entry=9000008;').stdout.strip()=='0'
            sql(f'UPDATE creature_template SET entry=9000008 WHERE entry={entry};')
            try:reject()
            finally:sql(f'UPDATE creature_template SET entry={entry} WHERE entry=9000008;')
        for row in rows['conversation_line_template']:
            sql(f"DELETE FROM conversation_line_template WHERE Id={row['Id']};")
            reject()
            sql('INSERT INTO conversation_line_template ('+','.join('`'+k+'`' for k in row)+') VALUES('+','.join(row.values())+');')
        for t,data in rows.items():sql(f"UPDATE `{t}` SET VerifiedBuild=12345 WHERE Id={data[0]['Id']};")
        provenance=checksum(owned);sql(restore);verify();assert checksum(owned)==provenance
        clear()
        boundary=restore.index('INSERT INTO `conversation_template` (`Id`')
        sql(restore[:boundary]);sql(restore);verify()
        # Each complete conversation can be published before the other.
        sql('DELETE FROM conversation_template WHERE Id=4576;');sql(restore);verify()
        assert checksum(protected)==safe
        print('PASS: two source conversations: all field conflicts, lost lines, existing actor bindings, missing NPCs, first/repeat/partial imports and preserved global actors',flush=True)
    finally:
        clear()
        if not had_padding:
            present=sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding';").stdout.strip()=='1'
            if present:sql('ALTER TABLE conversation_line_template DROP COLUMN Padding;')
        assert checksum(tables)==before,'Disposable schema baseline not restored'
