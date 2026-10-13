"""Execute Endgame boarding/localization SQL, preserving custom and foreign text."""
import sqlite3
from pathlib import Path
sql=(Path(__file__).resolve().parents[2]/'sql/updates/world/2026_10_13_02_world_gilneas_endgame_boarding_ruru.sql').read_text('utf8').replace('SET NAMES utf8mb4;','')
c=sqlite3.connect(':memory:');c.executescript('''CREATE TABLE creature_template(entry INTEGER,VehicleId INTEGER,ScriptName TEXT,AIName TEXT);
CREATE TABLE npc_spellclick_spells(npc_entry INTEGER,spell_id INTEGER,cast_flags INTEGER,user_type INTEGER);
CREATE TABLE creature_text(CreatureID INTEGER,GroupID INTEGER,ID INTEGER,Text TEXT);
CREATE TABLE creature_text_locale(CreatureID INTEGER,GroupID INTEGER,ID INTEGER,Locale TEXT,Text TEXT,PRIMARY KEY(CreatureID,GroupID,ID));
CREATE TABLE quest_template(ID INTEGER);CREATE TABLE quest_template_locale(ID INTEGER,locale TEXT,LogTitle TEXT,LogDescription TEXT,QuestDescription TEXT);
CREATE TABLE quest_offer_reward(ID INTEGER);CREATE TABLE quest_offer_reward_locale(ID INTEGER,locale TEXT,RewardText TEXT);
CREATE TABLE quest_request_items(ID INTEGER);CREATE TABLE quest_request_items_locale(ID INTEGER,locale TEXT,CompletionText TEXT);
INSERT INTO creature_template VALUES(43751,641,'npc_hippogryph_43751','');INSERT INTO quest_template VALUES(26706);INSERT INTO quest_offer_reward VALUES(26706);INSERT INTO quest_request_items VALUES(26706);
''')
c.execute('INSERT INTO creature_text VALUES(43749,1,0,?)',("Hop on a hippogryph, now's our chance!",))
c.execute('INSERT INTO creature_text VALUES(43749,0,0,?)',("Hold your horses, friend.  We'll hit them when we're all ready.",))
c.executescript(sql)
assert c.execute('SELECT * FROM npc_spellclick_spells').fetchone()==(43751,46598,1,0)
assert c.execute('SELECT Text FROM creature_text_locale WHERE CreatureID=43749 AND GroupID=1').fetchone()==('Садись на гиппогрифа, сейчас наш шанс!',)
assert c.execute('SELECT LogTitle FROM quest_template_locale').fetchone()==('Эндшпиль',)
assert c.execute('SELECT COUNT(*) FROM quest_offer_reward_locale').fetchone()==(1,)
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
c.execute("UPDATE creature_text_locale SET Locale='frFR',Text='Texte' WHERE GroupID=1")
c.execute("UPDATE creature_text_locale SET Text='Свой перевод' WHERE GroupID=0")
before=list(c.iterdump());c.executescript(sql);assert list(c.iterdump())==before
c.execute('DELETE FROM npc_spellclick_spells');c.execute("UPDATE creature_template SET ScriptName='custom'");c.executescript(sql)
assert not c.execute('SELECT * FROM npc_spellclick_spells').fetchall()
print('PASS: actual Endgame ride binding and Russian locale SQL; repeat/custom/foreign preservation (SQLite semantics)')
