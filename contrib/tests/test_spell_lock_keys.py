#!/usr/bin/env python3
"""Exercise actual key item, skill and spell validation against decoded locks."""
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile


def method(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def main():
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root / 'docs/audit-data/campaign-wildcard-loot-restoration.json').read_text('utf8'))
    tree, crystal = registry['decoded_locks']['2584'], registry['decoded_locks']['1691']
    assert tree['Type'][1] == 3 and tree['Index'][1] == 219181
    assert crystal['Type'][1] == 2 and crystal['Index'][1] == 5
    defines = (root / 'src/server/game/Miscellaneous/SharedDefines.h').read_text('latin1')
    enum = method(defines, 'enum LockKeyType') + ';'
    item_target = re.search(r'TARGET_GAMEOBJECT_ITEM_TARGET\s*=\s*(\d+)', defines)[1]
    body = method((root / 'src/server/game/Spells/Spell.cpp').read_text('latin1'), 'SpellCastResult Spell::CanOpenLock(')
    harness = r'''
#include <cstdint>
#include <map>
#include <stdexcept>
#include <iostream>
using int32=std::int32_t;using uint32=std::uint32_t;
constexpr int MAX_LOCK_CASE=8;
enum SpellCastResult {SPELL_CAST_OK,SPELL_FAILED_BAD_TARGETS,SPELL_FAILED_LOW_CASTLEVEL};
enum SkillType {SKILL_NONE,SKILL_TEST};
enum LockType {LOCKTYPE_PICKLOCK=1,LOCKTYPE_TEST=2};
KEY_ENUM
constexpr int TARGET_GAMEOBJECT_ITEM_TARGET=ITEM_TARGET;
SkillType SkillByLockType(LockType type){return type==LOCKTYPE_TEST?SKILL_TEST:SKILL_NONE;}
struct LockEntry {int32 Index[8]={};uint32 Skill[8]={},Type[8]={};};
struct LockStore {
    std::map<uint32,LockEntry> entries;
    LockEntry const* LookupEntry(uint32 id)const{auto i=entries.find(id);return i==entries.end()?nullptr:&i->second;}
} sLockStore;
struct Item {uint32 entry=0;uint32 GetEntry()const{return entry;}};
struct Target {int value=0;int GetTarget()const{return value;}};
struct SpellEffectInfo {int32 MiscValue=0,bonus=0;Target TargetA,TargetB;int32 CalcValue()const{return bonus;}};
struct Caster {
    uint32 level=5,skill=0;bool player=true,accessAura=false;
    uint32 getLevel()const{return level;}bool IsPlayer()const{return player;}
    Caster* ToPlayer(){return this;}uint32 GetSkillValue(SkillType)const{return skill;}
    bool HasAura(uint32 id)const{return accessAura&&id==146589;}
};
struct SpellInfo {uint32 Id=219181;};
struct Spell {
    SpellInfo info;Caster caster;SpellEffectInfo effect;bool hasEffect=true;
    SpellInfo* m_spellInfo=&info;Caster* m_caster=&caster;Item* m_CastItem=nullptr;
    SpellEffectInfo const* GetEffect(uint32 idx)const{return hasEffect&&idx==0?&effect:nullptr;}
    SpellCastResult CanOpenLock(uint32,uint32,SkillType&,int32&,int32&);
    SpellCastResult open(uint32 id){SkillType skill=SKILL_NONE;int32 needed=0,actual=0;return CanOpenLock(0,id,skill,needed,actual);}
};
BODY
void check(bool ok){if(!ok)throw std::runtime_error("spell lock key regression");}
int main(){
    LockEntry tree;tree.Type[1]=3;tree.Index[1]=219181;sLockStore.entries[2584]=tree;
    LockEntry crystal;crystal.Type[1]=2;crystal.Index[1]=5;sLockStore.entries[1691]=crystal;
    Spell spell;spell.effect.MiscValue=5;
    check(spell.open(2584)==SPELL_CAST_OK);spell.info.Id=1804;check(spell.open(2584)==SPELL_FAILED_BAD_TARGETS);
    check(spell.open(1691)==SPELL_CAST_OK);spell.effect.MiscValue=99;check(spell.open(1691)==SPELL_FAILED_BAD_TARGETS);
    check(spell.open(0)==SPELL_CAST_OK);check(spell.open(99999)==SPELL_FAILED_BAD_TARGETS);
    spell.hasEffect=false;check(spell.open(2584)==SPELL_FAILED_BAD_TARGETS);spell.hasEffect=true;
    sLockStore.entries[10]=LockEntry{};check(spell.open(10)==SPELL_CAST_OK);
    LockEntry itemLock;itemLock.Type[0]=LOCK_KEY_ITEM;itemLock.Index[0]=6948;sLockStore.entries[11]=itemLock;
    check(spell.open(11)==SPELL_FAILED_BAD_TARGETS);Item item{6948};spell.m_CastItem=&item;check(spell.open(11)==SPELL_CAST_OK);
    item.entry=999;check(spell.open(11)==SPELL_FAILED_BAD_TARGETS);spell.m_CastItem=nullptr;
    LockEntry skillLock;skillLock.Type[0]=LOCK_KEY_SKILL;skillLock.Index[0]=LOCKTYPE_TEST;skillLock.Skill[0]=25;sLockStore.entries[12]=skillLock;
    spell.effect.MiscValue=LOCKTYPE_TEST;spell.caster.skill=24;check(spell.open(12)==SPELL_FAILED_LOW_CASTLEVEL);
    spell.caster.skill=25;check(spell.open(12)==SPELL_CAST_OK);
    spell.caster.skill=0;spell.effect.TargetA.value=TARGET_GAMEOBJECT_ITEM_TARGET;spell.effect.bonus=25;check(spell.open(12)==SPELL_CAST_OK);
    spell.effect.TargetA.value=0;spell.effect.bonus=0;spell.effect.MiscValue=LOCKTYPE_PICKLOCK;
    skillLock.Index[0]=LOCKTYPE_PICKLOCK;sLockStore.entries[12]=skillLock;check(spell.open(12)==SPELL_CAST_OK);
    spell.caster.level=4;check(spell.open(12)==SPELL_FAILED_LOW_CASTLEVEL);
    LockEntry alternatives=tree;alternatives.Type[2]=LOCK_KEY_ITEM;alternatives.Index[2]=6948;sLockStore.entries[13]=alternatives;
    item.entry=6948;spell.m_CastItem=&item;check(spell.open(13)==SPELL_CAST_OK);spell.m_CastItem=nullptr;
    check(spell.open(13)==SPELL_FAILED_BAD_TARGETS);
    LockEntry legacy;legacy.Type[0]=LOCK_KEY_SPELL;legacy.Index[0]=143917;sLockStore.entries[14]=legacy;
    check(spell.open(14)==SPELL_FAILED_BAD_TARGETS);spell.caster.accessAura=true;check(spell.open(14)==SPELL_CAST_OK);
    spell.caster.accessAura=false;spell.info.Id=143917;check(spell.open(14)==SPELL_CAST_OK);
    legacy.Index[0]=-1;sLockStore.entries[14]=legacy;check(spell.open(14)==SPELL_FAILED_BAD_TARGETS);
    std::cout<<"PASS: actual CanOpenLock, decoded tree/crystal, wrong spell/skill rejection, item alternatives, skill/level/bonus boundaries, missing data and source access aura\n";
}
'''.replace('KEY_ENUM', enum).replace('BODY', body).replace('ITEM_TARGET;', item_target + ';')
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp) / 'lock.cpp', Path(tmp) / 'lock'
        cpp.write_text(harness, encoding='utf8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-fno-omit-frame-pointer', '-g', str(cpp), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)


if __name__ == '__main__':
    main()
