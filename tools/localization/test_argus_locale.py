#!/usr/bin/env python3
"""Compile actual native BroadcastText fallback and Argus helper in isolated harness.

Does not claim full server compilation or game validation. Pass --compiler g++.
Linux defaults to ASan/UBSan; --no-sanitizers documents portable Windows limit.
"""
import argparse,pathlib,subprocess,tempfile,re

def function(text,start):
    pos=text.index(start);opening=text.index('{',pos);depth=0
    for i in range(opening,len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[pos:i+1]
    raise ValueError('Unterminated function')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--compiler',default='g++');p.add_argument('--no-sanitizers',action='store_true');a=p.parse_args()
    root=pathlib.Path(a.root)
    native=(root/'src/server/game/DataStores/DB2Stores.cpp').read_bytes().decode('latin1')
    script=(root/'src/server/scripts/Argus/Zones/zone_legion_argus_krokuun.cpp').read_bytes().decode('latin1')
    assert 'AddGossipItemFor(player, GOSSIP_ICON_CHAT, GetLocalizedArgusReadyText(player), GOSSIP_SENDER_MAIN, GOSSIP_ACTION_INFO_DEF + 1);' in script
    source=r'''#include <cassert>
#include <cstdint>
#include <string>
using uint8=uint8_t; using LocaleConstant=int;
constexpr int DEFAULT_LOCALE=0, GENDER_MALE=0, GENDER_FEMALE=1, GENDER_NONE=2;
struct Localized { char const* Str[9]={"", "", "", "", "", "", "", "", ""}; };
struct BroadcastTextEntry { Localized* Text; Localized* Text1; };
struct DB2Manager { static char const* GetBroadcastTextValue(BroadcastTextEntry const*,LocaleConstant,int8_t,bool=false); };
struct Store { BroadcastTextEntry* entry=nullptr; BroadcastTextEntry const* LookupEntry(int id) { assert(id==27602); return entry; } } sBroadcastTextStore;
struct Session { int locale; int GetSessionDbLocaleIndex() { return locale; } };
struct Player { Session* session; uint8 gender; Session* GetSession() {return session;} uint8 getGender(){return gender;} };
'''.replace('int8_t,bool','uint8,bool')
    source+=function(native,'char const* DB2Manager::GetBroadcastTextValue')+'\n'
    source+=function(script,'std::string GetLocalizedArgusReadyText')+'\n'
    common=(root/'src/common/Common.h').read_text('utf8')
    enum=re.search(r'enum LocaleConstant(?:\s*:\s*uint8)?\s*\{(.*?)\};',common,re.S).group(1)
    # Count native declared locale values, including the sentinel (none).
    enum_values=[s.split('=')[0].strip() for s in re.sub(r'//[^\n]*','',enum).split(',')]
    count=enum_values.index('TOTAL_LOCALES')
    mask=re.search(r'uint32 availableDb2Locales = ([^;]+);',native).group(1)
    source+='\nusing uint32=uint32_t; constexpr int TOTAL_LOCALES='+str(count)+', LOCALE_none='+str(enum_values.index('LOCALE_none'))+';\n'
    source+='struct Config { bool all=true; bool GetBoolDefault(char const* key,bool) { assert(std::string(key)=="DB2.Files.LoadAllLocales"); return all; } } config; Config* sConfigMgr=&config;\n'
    source+='uint32 AvailableMask(bool all, int defaultLocale) { config.all=all; return '+mask+'; }\n'
    source+=r'''int main() {
    assert(AvailableMask(true,0)&(1u<<8));
    assert(!(AvailableMask(true,0)&(1u<<LOCALE_none)));
    assert(!(AvailableMask(false,0)&(1u<<8)));
    assert(AvailableMask(false,8)&(1u<<8));
    Localized male,female; male.Str[0]="I'm ready."; female.Str[0]="I'm ready.";
    male.Str[8]=u8"Я готов."; female.Str[8]=u8"Я готова.";
    BroadcastTextEntry text{&male,&female}; sBroadcastTextStore.entry=&text;
    Session session{8}; Player player{&session,GENDER_MALE};
    assert(GetLocalizedArgusReadyText(&player)==u8"Я готов.");
    player.gender=GENDER_FEMALE; assert(GetLocalizedArgusReadyText(&player)==u8"Я готова.");
    player.gender=GENDER_NONE; assert(GetLocalizedArgusReadyText(&player)==u8"Я готова.");
    for (int gender=0;gender<2;++gender) { player.gender=gender;
       session.locale=0; assert(GetLocalizedArgusReadyText(&player)=="I'm ready.");
       session.locale=2; assert(GetLocalizedArgusReadyText(&player)=="I'm ready."); }
    session.locale=8; female.Str[8]=""; player.gender=GENDER_FEMALE;
    assert(GetLocalizedArgusReadyText(&player)=="I'm ready.");
    female.Str[0]=""; assert(GetLocalizedArgusReadyText(&player)==u8"Я готов.");
    male.Str[8]=""; male.Str[0]=""; assert(GetLocalizedArgusReadyText(&player)=="I'm ready.");
    sBroadcastTextStore.entry=nullptr; assert(GetLocalizedArgusReadyText(&player)=="I'm ready.");
}'''
    with tempfile.TemporaryDirectory() as tmp:
        base=pathlib.Path(tmp);cpp=base/'test.cpp';exe=base/'test.exe'
        cpp.write_text(source,encoding='utf8')
        command=[a.compiler,'-std=c++14','-Wall','-Wextra','-Werror','-finput-charset=UTF-8',str(cpp),'-o',str(exe)]
        if not a.no_sanitizers:command+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
        subprocess.run(command,check=True);subprocess.run([str(exe)],check=True)
    print('PASS: actual helper/native fallback; session locales, gender, missing RU/entry/empty defaults; sanitizers='+str(not a.no_sanitizers))

if __name__=='__main__':main()
