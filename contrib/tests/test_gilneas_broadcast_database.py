"""Real source BroadcastText dependencies; caller supplies disposable hotfix copy."""
from pathlib import Path

IDS=tuple(range(132352,132364))+(132367,)

def test_gilneas_broadcast_database(sql,checksum):
    text=(Path(__file__).resolve().parents[2]/'sql/updates/hotfixes/2026_10_10_00_hotfixes_broadcast_text_fr_dependencies.sql').read_text('utf8')
    ids=','.join(map(str,IDS));tables=sql('SHOW TABLES;').stdout.splitlines()
    sql('DELETE FROM broadcast_text WHERE ID IN('+ids+');')
    locales=checksum([t for t in tables if t!='broadcast_text'])
    foreign=sql('SELECT * FROM broadcast_text WHERE ID NOT IN('+ids+') ORDER BY ID;').stdout
    sql(text)
    assert sql('SELECT ID FROM broadcast_text WHERE ID IN('+ids+') ORDER BY ID;').stdout.splitlines()==list(map(str,IDS))
    assert sql('SELECT COUNT(*) FROM broadcast_text WHERE ID IN('+ids+') AND VerifiedBuild=26124 AND (Text<>\'\' OR Text1<>\'\');').stdout.strip()=='13'
    assert sql('SELECT Text1 FROM broadcast_text WHERE ID=132355;').stdout.strip()=="I can't-- I-- Argh!"
    assert sql('SELECT SoundEntriesID1 FROM broadcast_text WHERE ID=132352;').stdout.strip()=='87858'
    assert locales==checksum([t for t in tables if t!='broadcast_text']),'locale rows changed'
    assert foreign==sql('SELECT * FROM broadcast_text WHERE ID NOT IN('+ids+') ORDER BY ID;').stdout
    assert sql("SELECT COUNT(*) FROM broadcast_text_locale l LEFT JOIN broadcast_text b ON b.ID=l.ID WHERE l.ID IN("+ids+") AND l.locale='frFR' AND b.ID IS NULL;").stdout.strip()=='0'
    before=checksum(tables);sql(text);assert before==checksum(tables),'repeat modified dependencies'
    sql("UPDATE broadcast_text SET Text='custom original',SoundEntriesID1=1,VerifiedBuild=0 WHERE ID=132352;")
    before=checksum(tables);sql(text);assert before==checksum(tables),'custom base record changed'
    print('PASS: 13 real base dependencies, escaped text, sound metadata, all locale bytes and custom base preservation')

def main():
    import os,subprocess,uuid,hashlib
    if os.environ.get('MYSQL_DISPOSABLE_TEST_SERVER')!='1':
        raise SystemExit('Requires MYSQL_DISPOSABLE_TEST_SERVER=1; never use a deployed server')
    db='test_gilneas_broadcast_'+uuid.uuid4().hex[:12]
    command=[os.environ.get('MYSQL_CLIENT','mysql'),'--host=127.0.0.1','--port='+os.environ.get('MYSQL_PORT','3306'),'--user=root','--batch','--skip-column-names','--default-character-set=utf8mb4']
    def raw(s,d=None):return subprocess.run(command+([d] if d else [])+['-e',s],capture_output=True,text=True,encoding='utf8',check=True)
    def sql(s):return raw(s,db)
    def checksum(tables):return hashlib.sha256(''.join(sql('SELECT * FROM `'+t+'` ORDER BY 1,2;').stdout for t in sorted(tables)).encode()).hexdigest()
    raw('CREATE DATABASE `'+db+'` CHARACTER SET utf8mb4;')
    try:
        columns='ID INT UNSIGNED PRIMARY KEY, Text TEXT, Text1 TEXT,'
        columns+=','.join(n+' INT NOT NULL DEFAULT 0' for n in ['EmoteID1','EmoteID2','EmoteID3','EmoteDelay1','EmoteDelay2','EmoteDelay3','EmotesID','LanguageID','Flags','ConditionID','SoundEntriesID1','SoundEntriesID2','VerifiedBuild'])
        sql('CREATE TABLE broadcast_text ('+columns+'); CREATE TABLE broadcast_text_locale (ID INT,locale VARCHAR(4),Text_lang TEXT,Text1_lang TEXT,VerifiedBuild SMALLINT,PRIMARY KEY(ID,locale));')
        sql("INSERT INTO broadcast_text (ID,Text) VALUES(1,'unrelated base'); INSERT INTO broadcast_text_locale VALUES(1,'ruRU','Русский текст','',26972),(132352,'frFR','Texte original','',26124);")
        test_gilneas_broadcast_database(sql,checksum)
    finally:raw('DROP DATABASE `'+db+'`;')

if __name__=='__main__':main()
