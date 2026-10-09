#!/usr/bin/env python3
"""Execute the actual three-brewer scripts against controlled engine boundaries."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HEADER = r'''
#pragma once
#include <cstdint>
#include <list>
#include <map>
#include <vector>
#include <functional>
using uint32=std::uint32_t;
constexpr uint32 EFFECT_0=0, SPELL_EFFECT_APPLY_AURA=6, SPELL_EFFECT_SUMMON=28,
 SPELL_AURA_LINKED_SUMMON=428, POINT_MOTION_TYPE=8, GO_ACTIVATED=2,
 QUEST_STATUS_INCOMPLETE=1, AURA_EFFECT_HANDLE_REAL=1;
using AuraEffectHandleModes=uint32;
struct Unit;struct Player;struct Creature;struct TempSummon;struct CreatureAI;
struct MotionMaster { std::vector<uint32> points;int follows=0;float angle=0;
 void MoveFollow(Unit*,float,float a){++follows;angle=a;}
 void MovePoint(uint32 id,float,float,float){points.push_back(id);} };
struct Unit { uint32 guid=0;void* map=nullptr;std::list<Creature*> creatures;
 virtual ~Unit()=default;virtual Player* ToPlayer(){return nullptr;}
 uint32 GetGUID()const{return guid;}void* GetMap(){return map;}
 void GetCreatureListWithEntryInGrid(std::list<Creature*>& out,uint32 entry,float range=250);
};
struct Player:Unit { uint32 quest=1,credit=0,removed=0;std::map<uint32,bool> auras;
 std::function<void(uint32)> remove;
 Player* ToPlayer()override{return this;}uint32 GetQuestStatus(uint32){return quest;}
 bool HasAura(uint32 id){return auras[id];}void KilledMonsterCredit(uint32 id){credit=id;}
 void RemoveAurasDueToSpell(uint32 id){removed=id;auras[id]=false;if(remove)remove(id);}
};
struct Creature:Unit { uint32 entry=0;CreatureAI* ai=nullptr;bool alive=true,phase=true,despawn=false;float distance=1;MotionMaster motion;
 uint32 GetEntry(){return entry;}virtual TempSummon* ToTempSummon(){return nullptr;}
 CreatureAI* AI(){return ai;}bool IsAlive(){return alive;}bool IsInPhase(Unit*){return phase;}
 MotionMaster* GetMotionMaster(){return &motion;}void SetWalk(bool){}
 void DespawnOrUnsummon(){despawn=true;}
};
struct TempSummon:Creature { uint32 owner=0;TempSummon* ToTempSummon()override{return this;}
 uint32 GetSummonerGUID(){return owner;}
};
void Unit::GetCreatureListWithEntryInGrid(std::list<Creature*>& out,uint32 entry,float range){
 for(auto c:creatures)if(c->entry==entry&&c->distance<=range)out.push_back(c);
}
struct CreatureAI { virtual ~CreatureAI()=default;virtual void IsSummonedBy(Unit*){}
 virtual uint32 GetData(uint32)const{return 0;}virtual void SetData(uint32,uint32){}
 virtual void MovementInform(uint32,uint32){}virtual void UpdateAI(uint32){} };
struct ScriptedAI:CreatureAI { Creature* me;explicit ScriptedAI(Creature* c):me(c){c->ai=this;} };
struct GameObject:Unit {uint32 entry=0,mapId=1514;uint32 GetEntry(){return entry;}uint32 GetMapId(){return mapId;}float GetDistance(Creature* c){return c->distance;} };
struct GameObjectAI { GameObject* go;explicit GameObjectAI(GameObject* g):go(g){}
 virtual ~GameObjectAI()=default;virtual void OnStateChanged(uint32,Unit*){} };
struct SpellEffectInfo {uint32 Effect=0,ApplyAuraName=0,TriggerSpell=0,MiscValue=0;};
struct SpellInfo { SpellEffectInfo effect;SpellEffectInfo const* GetEffect(uint32)const{return &effect;} };
struct SpellMgr {std::map<uint32,SpellInfo> spells;SpellInfo const* GetSpellInfo(uint32 id){auto p=spells.find(id);return p==spells.end()?nullptr:&p->second;} };
SpellMgr mgr;SpellMgr* sSpellMgr=&mgr;
struct AuraEffect {};
struct Hook {template<class T> void operator+=(T){} };
struct AuraScript {Unit* target=nullptr;SpellInfo const* info=nullptr;bool prevented=false;Hook OnEffectRemove;
 virtual ~AuraScript()=default;virtual bool Validate(SpellInfo const*){return true;}virtual void Register(){}
 Unit* GetTarget(){return target;}SpellInfo const* GetSpellInfo(){return info;}void PreventDefaultAction(){prevented=true;}
};
#define PrepareAuraScript(T) public:
#define AuraEffectRemoveFn(...) 0
#define RegisterCreatureAI(T) ((void)0)
#define RegisterGameObjectAI(T) ((void)0)
#define RegisterAuraScript(T) ((void)0)
'''
MAIN = r'''
#include <iostream>
#include <stdexcept>
void check(bool ok,char const* why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 int map;Player owner,other;owner.guid=1;other.guid=2;owner.map=other.map=&map;
 uint32 entries[]={119619,119620,119621};uint32 auras[]={237611,237613,237615};uint32 summons[]={237610,237612,237614};
 for(int i=0;i<3;++i){mgr.spells[auras[i]].effect={6,428,summons[i],0};mgr.spells[summons[i]].effect={28,0,0,entries[i]};}
 for(auto const& delivery:CampaignBrew::Deliveries){
  TempSummon own,foreign;own.entry=foreign.entry=delivery.Creature;own.owner=1;foreign.owner=2;own.distance=5;foreign.distance=1;
  npc_campaign_brew_companion ai(&own),foreignAI(&foreign);
  ai.IsSummonedBy(&owner);check(own.motion.follows==1&&own.motion.angle==delivery.Angle,"source follow parameters");
  GameObject barrel;barrel.entry=delivery.Object;barrel.map=&map;barrel.creatures={&foreign,&own};go_campaign_brew_delivery go(&barrel);
  uint32 aura=CampaignBrew::AuraFor(delivery.Creature);owner.auras.clear();owner.auras[aura]=true;owner.credit=owner.removed=0;
  owner.creatures=barrel.creatures;
  spell_campaign_brew_linked_summon removal;removal.target=&owner;removal.info=mgr.GetSpellInfo(aura);
  check(removal.Validate(removal.info),"loaded aura chain validates");
  owner.remove=[&](uint32){removal.Remove(nullptr,1);if(!removal.prevented)own.DespawnOrUnsummon();};
  go.OnStateChanged(1,&owner);check(owner.credit==0,"ignore other state");
  owner.quest=0;go.OnStateChanged(2,&owner);check(owner.credit==0,"no quest no credit");owner.quest=1;
  own.phase=false;go.OnStateChanged(2,&owner);check(owner.credit==0,"phase isolation");own.phase=true;
  go.OnStateChanged(2,nullptr);check(owner.credit==0,"null invoker");
  barrel.mapId=1;go.OnStateChanged(2,&owner);check(owner.credit==0,"wrong map");barrel.mapId=1514;
  owner.auras[aura]=false;go.OnStateChanged(2,&owner);check(owner.credit==0,"no aura no delivery");owner.auras[aura]=true;
  own.distance=101;go.OnStateChanged(2,&owner);check(owner.credit==0,"only foreign companion in range");own.distance=5;
  go.OnStateChanged(2,&owner);check(owner.credit==delivery.Credit&&owner.removed==aura,"matching owner and loaded aura");
  check(ai.GetData(CampaignBrew::Returning)==1&&!foreignAI.GetData(CampaignBrew::Returning),"foreign nearest untouched");
  check(removal.prevented&&!own.despawn&&!foreign.despawn,"preserve return and foreign owner");
  go.OnStateChanged(2,&owner);check(own.motion.points.size()==1,"repeat cannot start duplicate return");
  ai.MovementInform(0,1);ai.MovementInform(8,2);check(own.motion.points.size()==1,"ignore wrong motion/stale point");
  ai.MovementInform(8,1);check(own.motion.points.back()==2,"second source point");
  ai.MovementInform(8,2);check(own.despawn,"cleanup at last point");
 }
 // Old returning + new follower: cancellation must remove new follower, preserve only return.
 TempSummon old,newer,foreign;old.entry=newer.entry=foreign.entry=119619;old.owner=newer.owner=1;foreign.owner=2;
 npc_campaign_brew_companion oldAI(&old),newAI(&newer),foreignAI(&foreign);oldAI.SetData(CampaignBrew::Returning,1);
 owner.creatures={&old,&newer,&foreign};spell_campaign_brew_linked_summon removal;removal.target=&owner;removal.info=mgr.GetSpellInfo(237611);
 removal.Remove(nullptr,1);check(removal.prevented&&!old.despawn&&newer.despawn&&!foreign.despawn,"simultaneous summons and ownership");
 oldAI.UpdateAI(29999);check(!old.despawn,"return timeout boundary");oldAI.UpdateAI(1);check(old.despawn,"blocked route bounded cleanup");
 owner.creatures={&newer};removal.prevented=false;removal.Remove(nullptr,1);check(!removal.prevented,"ordinary cancellation retains native behavior");
 // Different hotfix mapping is accepted only if it remains unambiguous.
 mgr.spells[237611].effect.TriggerSpell=237612;mgr.spells[237613].effect.TriggerSpell=237610;
 check(CampaignBrew::AuraFor(119620)==237611&&CampaignBrew::AuraFor(119619)==237613,"loaded hotfix mapping, not fixed source IDs");
 mgr.spells[237611].effect.ApplyAuraName=0;check(!removal.Validate(removal.info),"reject incompatible aura");
 mgr.spells[237611].effect={6,428,237614,0};check(CampaignBrew::AuraFor(119621)==0,"ambiguous loaded mapping fails closed");
 std::cout<<"PASS: actual three delivery scripts: loaded aura mapping, owner/phase/quest isolation, repeats, cancellation, route and timeout\n";
}catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}}
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default=os.environ.get('CXX','c++'))
    parser.add_argument('--no-sanitizers',action='store_true')
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as path:
        path=Path(path)
        (path/'ScriptMgr.h').write_text(HEADER)
        for name in ('ScriptedCreature.h','GameObjectAI.h','GameObject.h','Player.h','TemporarySummon.h','MotionMaster.h','SpellMgr.h','SpellScript.h','SpellAuraEffects.h'):
            (path/name).write_text('#include "ScriptMgr.h"\n')
        cpp=path/'brew.cpp';cpp.write_text((ROOT/'src/server/scripts/World/campaign_brew_scripts.cpp').read_text(encoding='utf-8-sig')+'\n'+MAIN)
        flags=['-std=c++17','-Wall','-Wextra','-Werror']
        if not args.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        exe=path/'brew.exe'
        subprocess.run([args.compiler,*flags,'-I',str(path),str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
