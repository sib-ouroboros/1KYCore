import io
import json
from pathlib import Path
import tempfile
import unittest
from sql_dump import DumpError,Table,statements,literal,read_dump
from rules import Rule
from localize import analyse,packages
from text_checks import quality,game_signature,csv_cell

class ParserTests(unittest.TestCase):
    schema="CREATE TABLE `texts` (\n `ID` int NOT NULL,\n `locale` varchar(4) NOT NULL,\n `Text` text DEFAULT NULL,\n PRIMARY KEY (`ID`,`locale`)\n) ENGINE=MyISAM;\n"
    def dump(self,text):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.sql';path.write_text(text,encoding='utf8',newline='')
            return read_dump(path,{'texts'})[0]['texts']
    def test_escape_multiline_columns(self):
        d=self.dump(self.schema+"INSERT INTO `texts` (`Text`,`locale`,`ID`) VALUES ('It\\'s \\nслово\\\\путь;','ruRU',1),(NULL,'ruRU',2); REPLACE INTO `texts` VALUES (3,'ruRU','строка\nвторая');")
        self.assertEqual(d.rows[('1','ruRU')]['Text'],"It's \nслово\\путь;")
        self.assertIsNone(d.rows[('2','ruRU')]['Text'])
        self.assertEqual(d.rows[('3','ruRU')]['Text'],'строка\nвторая')
    def test_duplicate(self):
        d=self.dump(self.schema+"INSERT INTO `texts` VALUES (1,'ruRU','Один'),(1,'ruRU','Другой');")
        self.assertIn(('1','ruRU'),d.duplicates)
    def test_fail_closed(self):
        for statement in ("INSERT INTO `texts` VALUES (1,'ruRU',CONCAT('a','b'));","UPDATE `texts` SET Text='bad';","INSERT INTO `texts` VALUES (1,'ruRU','one') ON DUPLICATE KEY UPDATE Text='two';"):
            with self.subTest(statement=statement),self.assertRaises(DumpError):self.dump(self.schema+statement)
    def test_qualified_unquoted_selected_headers_fail(self):
        for statement in ("INSERT INTO texts VALUES(1,'ruRU','Текст');", "INSERT INTO `world`.`texts` VALUES(1,'ruRU','Текст');", "INSERT LOW_PRIORITY INTO `texts` VALUES(1,'ruRU','Текст');"):
            with self.subTest(statement=statement),self.assertRaises(DumpError):self.dump(self.schema+statement)
    def test_comments_and_doubled_quotes(self):
        self.assertEqual(literal("'can''t'"),"can't")
        d=self.dump("/* header ; */\n"+self.schema+"-- comment ;\nINSERT INTO `texts` VALUES(1,'ruRU','/*literal*/');")
        self.assertEqual(d.rows[('1','ruRU')]['Text'],'/*literal*/')
    def test_chunk_boundary(self):
        d=self.dump(self.schema+"INSERT INTO `texts` VALUES (1,'ruRU','"+('a'*1048500)+"'';слово');")
        self.assertTrue(d.rows[('1','ruRU')]['Text'].endswith("';слово"))
    def test_invalid_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.sql';path.write_bytes(self.schema.encode()+b'\xff')
            with self.assertRaises(UnicodeDecodeError):read_dump(path,{'texts'})

class TextTests(unittest.TestCase):
    def test_gender_and_long_name(self):
        text='$gГотов:Готова;, $n!'
        self.assertIsNone(quality('Ready, $n!',text))
        self.assertIsNotNone(quality('Ready, $n!','$gГотов $n:Готова;'))
        for female in (False,True):self.assertEqual(game_signature(text,female),game_signature('Ready, $n!',female))
        self.assertEqual('Здравствуйте, $n!'.replace('$n','Оченьдлинноеимяперсонажа'),'Здравствуйте, Оченьдлинноеимяперсонажа!')
    def test_parameters_links_and_encoding(self):
        self.assertIsNotNone(quality('Count %llu','Количество %u',mode='printf'))
        self.assertIsNotNone(quality('Name %s','Имя %n',mode='printf'))
        self.assertIsNotNone(quality('Value {id}','Значение {other}',mode='fmt'))
        self.assertIsNone(quality('|Hquest:1|h[Quest]|h','|Hquest:1|h[Задание]|h'))
        self.assertIsNotNone(quality('|Hquest:1|h[Quest]|h','|Hquest:2|h[Задание]|h'))
        for text in ('Текст\\n.','Текст\ufffd.','Текст\0.','Обрезано'):
            self.assertIsNotNone(quality('Text.',text))
        self.assertIsNotNone(quality('Text.','Текст.',('bytes',3)))
    def test_csv(self):
        for value in ('=HYPERLINK("bad")','  +SUM(1,2)','@bad','\tbad','-formula'):
            self.assertTrue(csv_cell(value).startswith("'"))

class MatchingTests(unittest.TestCase):
    rule=Rule('demo','texts_locale','texts_locale','texts','texts',('ID',),('ID',),('ID',),('ID',),(('Text','Text','Text','Text'),))
    def fixture(self,current=None,english='Text.',exists=True):
        base=Table(['ID','Text'],['ID'],'',{('1',):{'ID':'1','Text':'Text.'}} if exists else {})
        locale=Table(['ID','locale','Text','Other','VerifiedBuild'],['ID','locale'],'',{},limits={'Text':('bytes',65535),'Other':('bytes',65535)},defaults={'Text':None,'Other':None,'VerifiedBuild':'0'})
        if current is not None:locale.rows[('1','ruRU')]={'ID':'1','locale':'ruRU','Text':current,'Other':'Сохранить','VerifiedBuild':'42'}
        sb=Table(['ID','Text'],['ID'],'',{('1',):{'ID':'1','Text':english}})
        sl=Table(['ID','locale','Text'],['ID','locale'],'',{('1','ruRU'):{'ID':'1','locale':'ruRU','Text':'Текст.'}})
        return {'texts':base,'texts_locale':locale},{'texts':sb,'texts_locale':sl}
    def check(self,current=None,english='Text.',exists=True):
        a,b=self.fixture(current,english,exists);return analyse(a,b,'sha',(self.rule,))
    def test_empty_null_and_english_copy(self):
        for current in (None,'','Text.'):
            self.assertEqual(len(self.check(current)[1]),1)
    def test_existing_translations(self):
        for text in ('Другой текст.','Latin proper name'):
            self.assertFalse(self.check(text)[1])
            self.assertEqual(self.check(text)[0][0]['status'],'existing_translation_conflict')
    def test_preserved_conflict_retains_donor_for_review(self):
        records,changes,_=self.check('Другой текст.')
        self.assertEqual(records[0]['proposal'],'Текст.')
        self.assertEqual(records[0]['donor_english'],'Text.')
        self.assertFalse(changes)
    def test_native_primary_collision_guard_and_full_row_hash(self):
        a,b=self.fixture();_,changes,_=analyse(a,b,'sha',(self.rule,))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);manifest=packages(a,changes,out)
            text=(out/'demo-001.apply.sql').read_text('utf8')
            self.assertIn('WHERE `ID` <=>',text)
            self.assertIn('`locale` <=>',text)
            self.assertEqual(len(manifest[0]['evidence'][0]['row_after_sha256']),64)
    def test_plan_roundtrip_is_byte_identical(self):
        a,b=self.fixture('');_,changes,_=analyse(a,b,'sha',(self.rule,))
        with tempfile.TemporaryDirectory() as tmp:
            first=Path(tmp)/'first';second=Path(tmp)/'second';first.mkdir();second.mkdir()
            packages(a,changes,first)
            packages(a,json.loads(json.dumps(changes,sort_keys=True)),second)
            self.assertEqual({p.name:p.read_bytes() for p in first.iterdir()},{p.name:p.read_bytes() for p in second.iterdir()})
    def test_mismatch_absent_duplicates_schema(self):
        self.assertFalse(self.check(english='Different.')[1])
        self.assertEqual(self.check(exists=False)[0][0]['status'],'entity_absent')
        a,b=self.fixture();b['texts_locale'].duplicates.add(('1','ruRU'))
        self.assertFalse(analyse(a,b,'sha',(self.rule,))[1])
        b['texts_locale'].columns.remove('Text')
        with self.assertRaises(DumpError):analyse(a,b,'sha',(self.rule,))
    def test_composite_key(self):
        rule=Rule('demo','texts_locale','texts_locale','texts','texts',('ID','Sub'),('ID','Sub'),('ID','Sub'),('ID','Sub'),(('Text','Text','Text','Text'),))
        a,b=self.fixture()
        for data in (a,b):
            for table in data.values():
                table.columns.append('Sub');table.primary.append('Sub')
                table.rows={tuple(list(k)+['2']):dict(v,Sub='2') for k,v in table.rows.items()}
        self.assertEqual(len(analyse(a,b,'sha',(rule,))[1]),1)
    def test_determinism_and_scope(self):
        a,b=self.fixture('');changes=analyse(a,b,'sha',(self.rule,))[1]
        with tempfile.TemporaryDirectory() as one,tempfile.TemporaryDirectory() as two:
            packages(a,changes,Path(one));packages(a,changes,Path(two))
            for p in Path(one).iterdir():self.assertEqual(p.read_bytes(),(Path(two)/p.name).read_bytes())
            apply=(Path(one)/'demo-001.apply.sql').read_text()
            self.assertIn('BINARY `Text`',apply)
            self.assertNotIn('SET `Other`',apply)
            self.assertNotIn('REPLACE INTO',apply)
            self.assertNotIn('DROP',apply)

if __name__=='__main__':unittest.main()
