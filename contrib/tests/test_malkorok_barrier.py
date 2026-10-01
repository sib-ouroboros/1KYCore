#!/usr/bin/env python3
"""Compile the actual Malkorok absorption handler against boundary fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/scripts/Pandaria/SiegeOfOrgrimmar/boss_malkorok.cpp').read_text('utf8')
    start = source.index('            void HandleOnAbsorb(')
    opening = source.index('{', start)
    end, depth = opening + 1, 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    method = source[start:end]
    harness = r'''
#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <iostream>
using uint32=std::uint32_t;using uint64=std::uint64_t;using int32=std::int32_t;
constexpr int SPELL_ANCIENT_BARRIER=1,EFFECT_0=0;
struct DamageInfo{};
struct AuraEffect{
    int32 amount=0;unsigned writes=0;
    int32 GetAmount()const{return amount;}
    int32 CalculateAmount(void*)const{return amount;}
    void SetAmount(int32 value){amount=value;++writes;}
};
struct Unit{
    uint64 health=0;AuraEffect* aura=nullptr;int32 castAmount=-1;unsigned casts=0;
    uint64 GetMaxHealth()const{return health;}
    AuraEffect* GetAuraEffect(int,int){return aura;}
    void CastCustomSpell(Unit*,int,int32* amount,void*,void*,bool){castAmount=*amount;++casts;}
};
struct Handler{
    Unit* owner=nullptr;
    Unit* GetUnitOwner(){return owner;}
    void* GetCaster(){return nullptr;}
METHOD
};
void check(bool ok){if(!ok)throw std::runtime_error("barrier boundary failed");}
void run(uint64 health,int32 old,int32 absorbed,int32 expected,bool existing){
    AuraEffect barrier{old},incoming{absorbed};Unit owner{health,existing?&barrier:nullptr};
    Handler handler{&owner};DamageInfo damage;uint32 result=0;
    handler.HandleOnAbsorb(&incoming,damage,result);
    check(result==uint32(absorbed));
    if(existing){check(barrier.amount==expected);check(barrier.writes==unsigned(old!=expected));check(owner.casts==0);}
    else{check(owner.castAmount==expected);check(owner.casts==1);}
}
int main(){
    for(bool existing:{false,true}){
        run(100,existing?40:0,60,existing?100:60,existing);
        run(100,existing?40:0,100,100,existing);
        run(100,existing?40:0,101,100,existing);
        run(100,existing?40:0,0,existing?40:0,existing);
        run(0,40,60,0,existing);
        run(uint64(1)<<40,2147483647,2147483647,2147483647,existing);
    }
    run(100,100,20,100,true);
    run(100,-1,20,20,true);
    Handler handler;AuraEffect incoming{10};DamageInfo damage;uint32 amount=0;
    handler.HandleOnAbsorb(&incoming,damage,amount);check(amount==10);
    std::cout<<"PASS: actual Malkorok handler, equality, saturation, 64-bit health and unchanged shield\n";
}
'''.replace('METHOD', method)
    with tempfile.TemporaryDirectory() as tmp:
        cpp=Path(tmp)/'barrier.cpp';exe=Path(tmp)/'barrier'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',
            '-Wno-unused-parameter','-fsanitize=address,undefined','-fno-sanitize-recover=undefined',
            '-fno-omit-frame-pointer','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__ == '__main__':
    main()
