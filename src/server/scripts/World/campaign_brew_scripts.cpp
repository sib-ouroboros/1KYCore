// Scoped delivery lifecycle for the three Stormstout brewers (quest45440).
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "GameObjectAI.h"
#include "GameObject.h"
#include "DB2Stores.h"
#include "DBCEnums.h"
#include "Player.h"
#include "TemporarySummon.h"
#include "MotionMaster.h"
#include "SpellMgr.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellAuraEffects.h"
#include <list>

namespace CampaignBrew
{
constexpr uint32 Quest = 45440;
constexpr uint32 Returning = 4544001;
struct Delivery
{
    uint32 Object, Creature, Credit;
    float Angle;
    float Path[2][3];
};
Delivery const Deliveries[] =
{
    {268377,119620,119623,15.0f,{{796.264f,3613.06f,160.521f},{793.338f,3616.69f,160.521f}}},
    {268378,119619,119624,5.0f,{{738.549f,3620.22f,140.628f},{733.016f,3622.28f,140.625f}}},
    {268379,119621,119625,10.0f,{{750.196f,3543.7f,139.534f},{748.375f,3537.1f,139.332f}}}
};
Delivery const* Find(uint32 entry)
{
    for (auto const& delivery : Deliveries)
        if (delivery.Object == entry || delivery.Creature == entry)
            return &delivery;
    return nullptr;
}

// Resolve against loaded spell data, not the source SQL's swapped aura IDs.
uint32 SummonedEntry(SpellInfo const* info)
{
    auto aura = info ? info->GetEffect(EFFECT_0) : nullptr;
    if (!aura || aura->Effect != SPELL_EFFECT_APPLY_AURA || aura->ApplyAuraName != SPELL_AURA_LINKED_SUMMON)
        return 0;
    auto trigger = sSpellMgr->GetSpellInfo(aura->TriggerSpell);
    auto summon = trigger ? trigger->GetEffect(EFFECT_0) : nullptr;
    if (!summon || summon->Effect != SPELL_EFFECT_SUMMON ||
        summon->MiscValue < 119619 || summon->MiscValue > 119621)
        return 0;
    auto properties = sSummonPropertiesStore.LookupEntry(summon->MiscValueB);
    if (!properties || properties->Control != SUMMON_CATEGORY_ALLY || properties->Title != SUMMON_TYPE_NONE ||
        !(properties->Flags & SUMMON_PROP_FLAG_PERSONAL_SPAWN))
        return 0;
    return summon->MiscValue;
}
uint32 AuraFor(uint32 entry)
{
    uint32 result = 0;
    for (uint32 aura : {237611u,237613u,237615u})
        if (SummonedEntry(sSpellMgr->GetSpellInfo(aura)) == entry)
        {
            if (result) return 0; // Ambiguous client/hotfix data: do not deliver.
            result = aura;
        }
    return result;
}
bool Owned(Creature* creature, Unit* owner)
{
    auto summon = creature->ToTempSummon();
    return summon && summon->GetSummonerGUID() == owner->GetGUID();
}
}

struct npc_campaign_brew_companion : ScriptedAI
{
    explicit npc_campaign_brew_companion(Creature* creature) : ScriptedAI(creature) { }
    void IsSummonedBy(Unit* owner) override
    {
        auto delivery = CampaignBrew::Find(me->GetEntry());
        if (!delivery || !owner || !owner->ToPlayer() || !CampaignBrew::Owned(me, owner))
            return;
        me->GetMotionMaster()->MoveFollow(owner, 0.0f, delivery->Angle);
    }
    uint32 GetData(uint32 id) const override
    {
        return id == CampaignBrew::Returning ? _point : 0;
    }
    void SetData(uint32 id, uint32 value) override
    {
        if (id != CampaignBrew::Returning || value != 1 || _point || !CampaignBrew::Find(me->GetEntry()))
            return;
        _remaining = 30000; // Bounded cleanup if the original two-point route cannot finish.
        MoveTo(1);
    }
    void MovementInform(uint32 type, uint32 point) override
    {
        if (type != POINT_MOTION_TYPE || !_point || point != _point)
            return;
        if (point == 1) MoveTo(2);
        else me->DespawnOrUnsummon();
    }
    void UpdateAI(uint32 diff) override
    {
        if (!_point) return;
        if (diff >= _remaining) me->DespawnOrUnsummon();
        else _remaining -= diff;
    }
private:
    void MoveTo(uint32 point)
    {
        _point = point;
        auto const& position = CampaignBrew::Find(me->GetEntry())->Path[point-1];
        me->SetWalk(false);
        me->GetMotionMaster()->MovePoint(point, position[0], position[1], position[2]);
    }
    uint32 _point = 0;
    uint32 _remaining = 0;
};

struct go_campaign_brew_delivery : GameObjectAI
{
    explicit go_campaign_brew_delivery(GameObject* object) : GameObjectAI(object) { }
    void OnStateChanged(uint32 state, Unit* unit) override
    {
        auto player = unit ? unit->ToPlayer() : nullptr;
        auto delivery = CampaignBrew::Find(go->GetEntry());
        if (state != GO_ACTIVATED || !player || !delivery || go->GetMapId() != 1514 ||
            player->GetMap() != go->GetMap() || player->GetQuestStatus(CampaignBrew::Quest) != QUEST_STATUS_INCOMPLETE)
            return;
        uint32 aura = CampaignBrew::AuraFor(delivery->Creature);
        if (!aura || !player->HasAura(aura)) return;
        std::list<Creature*> creatures;
        go->GetCreatureListWithEntryInGrid(creatures, delivery->Creature, 100.0f);
        Creature* selected = nullptr;
        for (auto creature : creatures)
            if (CampaignBrew::Owned(creature, player) && creature->IsAlive() && creature->IsInPhase(player) &&
                dynamic_cast<npc_campaign_brew_companion*>(creature->AI()) &&
                !creature->AI()->GetData(CampaignBrew::Returning) &&
                (!selected || go->GetDistance(creature) < go->GetDistance(selected)))
                selected = creature;
        if (!selected) return;
        selected->AI()->SetData(CampaignBrew::Returning, 1);
        player->KilledMonsterCredit(delivery->Credit);
        player->RemoveAurasDueToSpell(aura);
    }
};

class spell_campaign_brew_linked_summon : public AuraScript
{
    PrepareAuraScript(spell_campaign_brew_linked_summon);
    bool Validate(SpellInfo const* info) override
    {
        return CampaignBrew::SummonedEntry(info) != 0;
    }
    void Remove(AuraEffect const*, AuraEffectHandleModes)
    {
        auto owner = GetTarget();
        uint32 entry = CampaignBrew::SummonedEntry(GetSpellInfo());
        if (!owner || !entry) return;
        std::list<Creature*> creatures;
        owner->GetCreatureListWithEntryInGrid(creatures, entry);
        // Only delivered brewers may finish their route after their aura goes away.
        // Other followers retain normal despawn behavior, including a newly summoned one.
        bool returning = false;
        for (auto creature : creatures)
            if (CampaignBrew::Owned(creature, owner) &&
                dynamic_cast<npc_campaign_brew_companion*>(creature->AI()) &&
                creature->AI()->GetData(CampaignBrew::Returning))
                returning = true;
        if (!returning) return; // Preserve native removal for ordinary cancellation.
        PreventDefaultAction();
        for (auto creature : creatures)
            if (CampaignBrew::Owned(creature, owner) &&
                !(dynamic_cast<npc_campaign_brew_companion*>(creature->AI()) &&
                  creature->AI()->GetData(CampaignBrew::Returning)))
                creature->DespawnOrUnsummon();
    }
    void Register() override
    {
        OnEffectRemove += AuraEffectRemoveFn(spell_campaign_brew_linked_summon::Remove, EFFECT_0,
                                             SPELL_AURA_LINKED_SUMMON, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_campaign_brew_scripts()
{
    RegisterCreatureAI(npc_campaign_brew_companion);
    RegisterGameObjectAI(go_campaign_brew_delivery);
    RegisterAuraScript(spell_campaign_brew_linked_summon);
}
