#!/usr/bin/env python3
"""Actual MySQL schema and conflict regression; caller supplies a disposable release database."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_packed_conversations(sql,checksum):
    schema=(ROOT/'sql/updates/world/2026_10_07_02_world_conversation_line_padding.sql').read_text('utf8')
    restore=(ROOT/'sql/updates/world/2026_10_07_03_world_campaign_packed_conversations.sql').read_text('utf8')
    registry=json.loads((ROOT/'docs/audit-data/campaign-packed-conversation-restoration.json').read_text('utf8'))
    rows=registry['rows'];owned=list(rows);tables=sql('SHOW TABLES;').stdout.splitlines()
    assert sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding';").stdout.strip()=='0'
    before=checksum(tables)
    keys={t:','.join(x['Id'] for x in data) for t,data in rows.items()}
    assert all(sql(f'SELECT COUNT(*) FROM `{t}` WHERE Id IN ({ids});').stdout.strip()=='0' for t,ids in keys.items())
    def clear():
        for t in reversed(owned):sql(f'DELETE FROM `{t}` WHERE Id IN ({keys[t]});')
    def insert(t,row):return 'INSERT INTO `'+t+'` ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(row.values())+');'
    def verify():
        for t,data in rows.items():
            for row in data:
                fields=[k for k in row if k!='VerifiedBuild']
                expected=' AND '.join('`'+k+'`='+row[k] for k in fields)
                assert sql(f'SELECT COUNT(*) FROM `{t}` WHERE {expected};').stdout.strip()=='1'
    def reject():
        original=checksum(owned+['conversation_actors'])
        result=sql(restore,ok=False)
        assert '_1kycore_packed_guard' in result.stderr,result.stderr
        assert checksum(owned+['conversation_actors'])==original,'Rejected import changed permanent data'
    try:
        # An old schema must reject the data before writing; never drop the high word.
        reject()
        for definition in ['INT UNSIGNED NOT NULL DEFAULT 0','SMALLINT NOT NULL DEFAULT 0','SMALLINT UNSIGNED NULL DEFAULT 0','SMALLINT UNSIGNED NOT NULL DEFAULT 1']:
            sql('ALTER TABLE conversation_line_template ADD COLUMN Padding '+definition+';')
            original=checksum(tables)
            failure=sql(schema,ok=False)
            assert '_1kycore_line_schema_guard' in failure.stderr,failure.stderr
            assert checksum(tables)==original
            reject()
            sql('ALTER TABLE conversation_line_template DROP COLUMN Padding;')
        sql(schema);same=checksum(tables);sql(schema);assert checksum(tables)==same
        assert sql('SELECT COUNT(*) FROM conversation_line_template WHERE Padding<>0;').stdout.strip()=='0'
        protected=[t for t in tables if t not in owned];untouched=checksum(protected)
        sql(restore);verify();canonical=checksum(owned);complete=checksum(tables)
        sql(restore);assert checksum(tables)==complete
        assert checksum(protected)==untouched
        # Every substantive field is guarded, including the two opaque bytes.
        for t,data in rows.items():
            for row in data:
                for field in row:
                    if field in ['Id','VerifiedBuild']:continue
                    altered="'custom_script'" if field=='ScriptName' else str(int(row[field])+1)
                    sql(f"UPDATE `{t}` SET `{field}`={altered} WHERE Id={row['Id']};")
                    reject()
                    sql(f"UPDATE `{t}` SET `{field}`={row[field]} WHERE Id={row['Id']};")
        # Compatible provenance is retained; the migration does not rewrite existing rows.
        for t,data in rows.items():
            sql(f"UPDATE `{t}` SET VerifiedBuild=12345 WHERE Id={data[0]['Id']};")
        compatible=checksum(owned);sql(restore);verify();assert checksum(owned)==compatible
        cid=registry['entries'][0]
        sql(f'INSERT INTO conversation_actors(ConversationId,ConversationActorGuid,Idx) VALUES ({cid},1,0);')
        try:reject()
        finally:sql(f'DELETE FROM conversation_actors WHERE ConversationId={cid};')
        first=rows['conversation_line_template'][0]
        sql('DELETE FROM conversation_line_template WHERE Id='+first['Id']+';');reject();sql(insert('conversation_line_template',first))
        # The source nearest lookup requires actual templates, not an unrelated GUID substitute.
        entry=registry['required_creatures'][0]
        assert sql('SELECT COUNT(*) FROM creature_template WHERE entry=9000008;').stdout.strip()=='0'
        sql(f'UPDATE creature_template SET entry=9000008 WHERE entry={entry};')
        try:reject()
        finally:sql(f'UPDATE creature_template SET entry={entry} WHERE entry=9000008;')
        # Retry after line publication and after only one template has been published.
        clear();boundary=restore.index('INSERT INTO `conversation_template` (`Id`')
        sql(restore[:boundary]);sql(restore);verify();assert checksum(owned)==canonical
        clear()
        for t,data in rows.items():
            for row in (data[:1] if t=='conversation_template' else data):sql(insert(t,row))
        sql(restore);verify();assert checksum(owned)==canonical
        assert checksum(protected)==untouched
        print('PASS: two source conversations/five opaque line packets; legacy/schema conflicts, all content conflicts, first/repeat/interrupted import, provenance, missing actors and unchanged NPC/quest/spawn data',flush=True)
    finally:
        clear()
        present=sql("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='conversation_line_template' AND COLUMN_NAME='Padding';").stdout.strip()=='1'
        if present:sql('ALTER TABLE conversation_line_template DROP COLUMN Padding;')
        assert checksum(tables)==before,'Disposable test did not restore its original baseline'
