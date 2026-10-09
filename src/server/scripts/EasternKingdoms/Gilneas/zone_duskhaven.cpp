/*
 * Copyright (C) 2017-2018 AshamaneProject <https://github.com/AshamaneProject>
 * Copyright (C) 2011-2016 ArkCORE <http://www.arkania.net/>
 * Copyright (C) 2008-2014 TrinityCore <http://www.trinitycore.org/>
 * Copyright (C) 2006-2009 ScriptDev2 <https://scriptdev2.svn.sourceforge.net/>
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include <algorithm>
#include <cmath>
#include <limits>

#include "CreatureTextMgr.h"
#include "DB2Stores.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "MoveSplineInit.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "ScriptedEscortAI.h"
#include "ScriptedFollowerAI.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "Spell.h"
#include "SpellScript.h"
#include "TemporarySummon.h"
#include "Vehicle.h"
#include "WaypointManager.h"
#include "WorldSession.h"
#include "zone_gilneas.h"

enum eDuskHaven
{
    NPC_GENERIC_TRIGGER_LAB_MP                  = 35374, // target on ship
    NPC_LORD_GODFREY_36170                      = 36170,
    NPC_TRIGGER                                 = 36198,
    NPC_HORRID_ABOMINATION                      = 36231,
    NPC_QUEST_14348_KILL_CREDIT                 = 36233,
    NPC_FORSAKEN_CATAPULT                       = 36283,
    NPC_GENERIC_TRIGGER_LAB_AOI                 = 36286, // target on land
    NPC_CYNTIA_CREDIT                           = 36287,
    NPC_JAMES_CREDIT                            = 36289,
    NPC_ASHLEY_CREDIT                           = 36288,
    NPC_FORSAKEN_MACHINIST                      = 36292,
    NPC_DARK_RANGER_THYALA                      = 36312,
    NPC_LORD_GODFREY_36330                      = 36330,
    NPC_KRENNAN_ARANAS_36331                    = 36331,
    NPC_KING_GENN_GREYMANE_36332                = 36332,
    NPC_MASTIFF                                 = 36405,
    NPC_DROWNING_WATCHMANN_CREDIT               = 36450,
    NPC_PRINCE_LIAM_GREYMANE                    = 36451,
    NPC_LORNA_CROWLEY                           = 36457,
    NPC_CAT                                     = 36459,
    NPC_LUCIUS                                  = 36461,
    NPC_SWIFT_MOUNTAIN_HORSE                    = 36741,
    NPC_LORD_DARIUS_CROWLEY                     = 37195,
    NPC_ENSLAVED_VILLAGER                       = 37694,
    NPC_KOROTH                                  = 37808,
    NPC_LORD_GODFREY                            = 37875,
    NPC_DARK_SCOUT                              = 37953,
    NPC_HARNESS_38755                           = 38755,
    NPC_HARNESS_43336                           = 43336,
    NPC_CARRIAGE_43337                          = 43337,
    NPC_STAGECOACH_CARRIAGE                     = 44928,
    NPC_LORNA_CRAWLEY                           = 51409,

    GO_BALL_AND_CHAIN                           = 201775,

    QUEST_AMONG_HUMANS_AGAIN                    = 14313,
    QUEST_INVASION                              = 14321,
    QUEST_LAST_CHANCE_AT_HUMANITY               = 14375,
    QUEST_LAST_STAND                            = 14222,
    QUEST_KILL_OR_BE_KILLED                     = 14336,
    QUEST_YOU_CANT_TAKE_EM_ALONE                = 14348,
    QUEST_SAVE_THE_CHILDREN                     = 14368,
    QUEST_LEADER_OF_THE_PACK                    = 14386,
    QUEST_GASPING_FOR_BREATH                    = 14395,
    QUEST_AS_THE_LAND_SHATTERS                  = 14396,
    QUEST_GRANDMAS_CAT                          = 14401,
    QUEST_TO_GREYMANE_MANOR                     = 14465,
    QUEST_THE_KINGS_OBSERVATORY                 = 14466,
    QUEST_ALAS_GILNEAS                          = 14467,
    QUEST_EXODUS                                = 24438,
    QUEST_INTRODUCTIONS_ARE_IN_ORDER            = 24472,
    QUEST_STORMGLEN                             = 24483,
    QUEST_LIBERATION_DAY                        = 24575,
    QUEST_BETRAYAL_AT_TEMPESTS_REACH            = 24592,
    QUEST_LOSING_YOUR_TAIL                      = 24616,
    QUEST_AT_OUR_DOORSTEP                       = 24627,
    QUEST_PUSH_THEM_OUT                         = 24676,
    QUEST_FLANK_THE_FORSAKEN                    = 24677,
    QUEST_THE_HUNGRY_ETTIN                      = 14416,

    SPELL_RANDOM_POINT_POISON                   = 42266,
    SPELL_RANDOM_POINT_BONE                     = 42267,
    SPELL_RANDOM_POINT_BONE_2                   = 42274,
    SPELL_SELF_ROOT                             = 42716,
    SPELL_CORPSE_EXPLOSION                      = 43999,
    SPELL_PARACHUTE                             = 45472,
    SPELL_DANS_EJECT_ALL_PASSENGERS             = 51254,
    SPELL_FORCE_REACTION_1                      = 61899,
    SPELL_LAUNCH3                               = 66227,
    SPELL_LAUNCH2                               = 66251,
    SPELL_FORCECAST_SUMMON_FORSAKEN_ASSASSIN    = 68492,
    SPELL_BARREL_KEG_PLACED                     = 68555,
    SPELL_ABOMINATION_KILL_ME                   = 68558,
    SPELL_FIERY_BOULDER                         = 68591,
    SPELL_HORRID_ABOMINATION_EXPLOSION          = 68560,
    SPELL_LAUNCH1                               = 68659,
    SPELL_RESCUE_DROWNING_WATCHMANN             = 68735,
    SPELL_SAVE_DROWNING_MILITIA_EFFECT          = 68737,
    SPELL_EXIT_VEHICLE                          = 68741,
    SPELL_ROUND_UP_HORSE                        = 68903,
    SPELL_ROPE_IN_HORSE                         = 68908,
    SPELL_MOUNTAIN_HORSE_CREDIT                 = 68917,
    SPELL_ROPE_CHANNEL                          = 68940,
    SPELL_CATACLYSM_1                           = 68953,
    SPELL_FORCECAST_CATACLYSM_I                 = 69027,
    SPELL_BARREL_KEG                            = 69094,
    SPELL_IN_STOCKS                             = 69196,
    SPELL_FORCECAST_SUMMON_SWIFT_MOUNTAIN_HORSE = 69256,
    SPELL_FORCECAST_GILNEAS_TELESCOPE           = 69258,
    SPELL_STEALTH_70456                         = 70456,
    SPELL_FREEZING_TRAP_EFFECT                  = 70794,
    SPELL_AIMED_SHOOT                           = 70796,
    SPELL_RIDE_VEHICLE_72764                    = 72764,
    SPELL_SUMMON_CARRIAGE                       = 72767,
    SPELL_THROW_BOULDER                         = 72768,
    SPELL_LAST_STAND_COMPLETE                   = 72799,
    SPELL_CATACLYSM_3                           = 80133,
    SPELL_CATACLYSM_2                           = 80134,
    SPELL_UPDATE_BIND_TO_GREYMANE_MANOR         = 82892,
    SPELL_GENERIC_QUEST_INVISIBLE_DETECTION_10  = 84481,
    SPELL_UPDATE_ZONE_AURAS                     = 89180,
    SPELL_FADE_BACK                             = 94053,
    SPELL_RIDE_VEHICLE                          = 94654,
    SPELL_FORCECAST_UPDATE_ZONE_AURAS           = 94828,
    SPELL_LAUNCH4                               = 96185,

    SPELL_PHASE_QUEST_ZONE_SPECIFIC_06          = 68481, // 181
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_07          = 68482, // 182
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_08          = 68483, // 183
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_09          = 69077, // 184
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_10          = 69078, // 185
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_11          = 69484, // 186
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_12          = 69485, // 187
    SPELL_PHASE_QUEST_ZONE_SPECIFIC_19          = 74096  // 194
};

// Phase 1/169
// Phase 4096/181 is used from reward quest 14222 and forward

// 36205
class npc_slain_watchman_36205 : public CreatureScript
{
public:
    npc_slain_watchman_36205() : CreatureScript("npc_slain_watchman_36205") { }

    bool OnQuestAccept(Player* player, Creature* creature, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_INVASION)
        {
            creature->CastSpell(player, SPELL_FORCECAST_SUMMON_FORSAKEN_ASSASSIN, true);
            return true;
        }
        return false;
    }
};

namespace
{
    // Unit::AddDelayedEvent uses a dormant function queue in this core.
    // Use the player's updated and lifetime-owned BasicEvent queue instead.
    class GilneasStocksTransitionEvent final : public BasicEvent
    {
    public:
        explicit GilneasStocksTransitionEvent(Player* player) : _player(player) { }

        bool Execute(uint64 /*time*/, uint32 /*diff*/) override
        {
            if (_player->GetMapId() == 654 && _player->GetAreaId() == 4786 &&
                _player->GetQuestStatus(QUEST_LAST_CHANCE_AT_HUMANITY) == QUEST_STATUS_REWARDED)
            {
                _player->CastSpell(_player, SPELL_PHASE_QUEST_ZONE_SPECIFIC_06, true);
                _player->RemoveAura(SPELL_FADE_BACK);
            }
            return true;
        }

    private:
        Player* _player;
    };

    void ReleaseGilneasStocks(Player* player)
    {
        player->RemoveAura(SPELL_IN_STOCKS);
        player->RemoveAura(SPELL_SELF_ROOT);
        player->RemoveFlag(UNIT_FIELD_FLAGS_2, UNIT_FLAG2_DISABLE_TURN);
        player->RemoveAura(50220);
        player->RemoveAura(58284);
        player->RemoveAura(68630);
    }
}

class player_gilneas_stocks_recovery : public PlayerScript
{
public:
    player_gilneas_stocks_recovery() : PlayerScript("player_gilneas_stocks_recovery") { }

    void OnLogin(Player* player, bool /*firstLogin*/) override
    {
        if (player->GetMapId() != 654 || player->GetAreaId() != 4786 ||
            player->GetQuestStatus(QUEST_LAST_CHANCE_AT_HUMANITY) != QUEST_STATUS_REWARDED ||
            player->GetQuestStatus(QUEST_AMONG_HUMANS_AGAIN) == QUEST_STATUS_REWARDED)
            return;
        // A partial transition can persist the root/turn lock without stocks.
        // Restrict recovery to this rewarded scene, preserving unrelated flags.
        if (player->HasAura(SPELL_IN_STOCKS) || player->HasAura(SPELL_SELF_ROOT) ||
            !player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06))
            ReleaseGilneasStocks(player);
        if (!player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06))
            player->CastSpell(player, SPELL_PHASE_QUEST_ZONE_SPECIFIC_06, true);
        player->RemoveAura(SPELL_FADE_BACK);
    }
};

// 36332
class npc_king_genn_greymane_36332 : public CreatureScript
{
public:
    npc_king_genn_greymane_36332() : CreatureScript("npc_king_genn_greymane_36332") { }

    bool OnQuestReward(Player* player, Creature* /*creature*/, const Quest* quest, uint32) override
    {
        if (quest->GetQuestId() == QUEST_LAST_CHANCE_AT_HUMANITY)
        {
            player->CastSpell(player, SPELL_FADE_BACK, true);
            if (Aura* fade = player->GetAura(SPELL_FADE_BACK))
            {
                fade->SetMaxDuration(3000);
                fade->SetDuration(3000);
            }
            ReleaseGilneasStocks(player);
            // Owned by the player, so despawning the old phase's questgiver
            // cannot cancel the transition or leave a dangling NPC pointer.
            player->m_Events.AddEvent(new GilneasStocksTransitionEvent(player),
                player->m_Events.CalculateTime(3000));
            return true;
        }
        return false;
    }
};

// 36331
class npc_krennan_aranas_36331 : public CreatureScript
{
public:
    npc_krennan_aranas_36331() : CreatureScript("npc_krennan_aranas_36331") { }

    struct npc_krennan_aranas_36331AI : public ScriptedAI
    {
        npc_krennan_aranas_36331AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        bool m_videoStarted = false;
        ObjectGuid m_playerGUID;
        ObjectGuid m_kingGUID;
        ObjectGuid m_godfreyGUID;
        std::set<ObjectGuid> pList;

        void Reset() override
        {
            m_kingGUID = ObjectGuid::Empty;
            m_godfreyGUID = ObjectGuid::Empty;
            m_events.RescheduleEvent(EVENT_CHECK_ARRIVEL_PLAYER, 1s);
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_ARRIVEL_PLAYER:
                    {
                        CheckVideoMember();

                        if (!m_videoStarted)
                            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            {
                                player->CastSpell(player, SPELL_IN_STOCKS, true);
                                player->CastSpell(player, SPELL_SELF_ROOT, true);
                                player->SetFlag(UNIT_FIELD_FLAGS_2, UNIT_FLAG2_DISABLE_TURN);
                                m_videoStarted = true;

                                m_events.ScheduleEvent(EVENT_TALK_PART_00, 4s);
                                return;
                            }

                        m_videoStarted = false;
                        m_playerGUID = ObjectGuid::Empty;
                        m_events.ScheduleEvent(EVENT_CHECK_ARRIVEL_PLAYER, 1s);
                        break;
                    }
                    case EVENT_TALK_PART_00:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(0, player);
                        if (Creature* king = ObjectAccessor::GetCreature(*me, m_kingGUID))
                            king->RemoveFlag(UNIT_NPC_FLAGS, UNIT_NPC_FLAG_QUESTGIVER);

                        m_events.ScheduleEvent(EVENT_TALK_PART_01, 14s);
                        break;
                    }
                    case EVENT_TALK_PART_01:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* lord = ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                            {
                                player->CastSpell(player, SPELL_CATACLYSM_1);
                                lord->AI()->Talk(0, player);
                            }
                        m_events.ScheduleEvent(EVENT_TALK_PART_02, 8s);
                        break;
                    }
                    case EVENT_TALK_PART_02:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* king = ObjectAccessor::GetCreature(*me, m_kingGUID))
                            {
                                player->CastSpell(player, SPELL_CATACLYSM_2);
                                king->AI()->Talk(0, player);
                            }
                        m_events.ScheduleEvent(EVENT_TALK_PART_03, 9s);
                        break;
                    }
                    case EVENT_TALK_PART_03:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* king = ObjectAccessor::GetCreature(*me, m_kingGUID))
                            {
                                player->CastSpell(player, SPELL_CATACLYSM_3);
                                king->AI()->Talk(1, player);
                            }
                        m_events.ScheduleEvent(EVENT_TALK_PART_04, 8s);
                        break;
                    }
                    case EVENT_TALK_PART_04:
                    {
                        if (ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            //player->CastSpell(player, SPELL_LAST_STAND_COMPLETE_2);
                            AddPlayer();
                        }

                        if (Creature* king = ObjectAccessor::GetCreature(*me, m_kingGUID))
                            king->SetFlag(UNIT_NPC_FLAGS, UNIT_NPC_FLAG_QUESTGIVER);

                        m_videoStarted = false;
                        m_playerGUID = ObjectGuid::Empty;
                        m_events.ScheduleEvent(EVENT_CHECK_ARRIVEL_PLAYER, 1s);
                        break;
                    }
                }
            }
        }

        void CheckVideoMember()
        {
            if (!m_kingGUID)
                if (Creature* king = me->FindNearestCreature(NPC_KING_GENN_GREYMANE_36332, 25.0f))
                    m_kingGUID = king->GetGUID();

            if (!m_godfreyGUID)
                if (Creature* lord = me->FindNearestCreature(NPC_LORD_GODFREY_36330, 25.0f))
                    m_godfreyGUID = lord->GetGUID();

            if (m_videoStarted)
                return;

            if (Player* player = me->SelectNearestPlayer(10.0f))
                if (!HasPlayer(player->GetGUID()))
                    if (player->GetQuestStatus(QUEST_LAST_STAND) == QUEST_STATUS_REWARDED && player->GetQuestStatus(QUEST_LAST_CHANCE_AT_HUMANITY) == QUEST_STATUS_NONE)
                        if (player->GetAreaId() == 4786)
                        {
                            m_playerGUID = player->GetGUID();
                            return;
                        }

            m_playerGUID = ObjectGuid::Empty;
        }

        void AddPlayer()
        {
            if (!HasPlayer(m_playerGUID))
                pList.insert(m_playerGUID);
        }

        bool HasPlayer(ObjectGuid guid)
        {
            return (pList.find(guid) != pList.end());
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_krennan_aranas_36331AI(creature);
    }
};

// 34571
class npc_gwen_armstead_34571 : public CreatureScript
{
public:
    npc_gwen_armstead_34571() : CreatureScript("npc_gwen_armstead_34571") { }

    bool OnQuestAccept(Player* player, Creature* /*creature*/, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_KILL_OR_BE_KILLED)
        {
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06);
            player->CastSpell(player, SPELL_PHASE_QUEST_ZONE_SPECIFIC_07);
            return true;
        }
        return false;
    }
};

// 196394
class go_mandragore_196394 : public GameObjectScript
{
public:
    go_mandragore_196394() : GameObjectScript("go_mandragore_196394") { }

    bool OnQuestReward(Player* player, GameObject* /*gameObject*/, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == 14320)
        {
            player->SendCinematicStart(168);
            player->PlayDirectSound(23676);
            return true;
        }

        return false;
    }
};

// Phase 8192/182

// 36231  // Quest - You Can't Take 'Em Alone - 14348
class npc_horrid_abomination_36231 : public CreatureScript
{
public:
    npc_horrid_abomination_36231() : CreatureScript("npc_horrid_abomination_36231") { }

    enum eHorrid
    {
        SAY_BARREL                              = 0,

        EVENT_KEG_PLACED                        = 101,
        EVENT_KEG_CREDIT,
    };

    struct npc_horrid_abomination_36231AI : public ScriptedAI
    {
        npc_horrid_abomination_36231AI(Creature* creature) : ScriptedAI(creature) { }

        bool m_creditGiven;
        EventMap m_events;

        void Reset() override
        {
            me->ClearUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED);
            m_creditGiven = false;
            m_events.Reset();
            me->RemoveAurasDueToSpell(SPELL_BARREL_KEG_PLACED);
        }

        void SpellHit(Unit* caster, SpellInfo const* spell) override
        {
            if (!caster || !spell || spell->Id != SPELL_BARREL_KEG || m_creditGiven || !me->IsAlive())
                return;

            Player* player = caster->ToPlayer();
            if (!player || player->GetQuestStatus(QUEST_YOU_CANT_TAKE_EM_ALONE) != QUEST_STATUS_INCOMPLETE)
                return;

            // Claim this abomination before casts can re-enter its AI.
            m_creditGiven = true;
            Talk(SAY_BARREL, player);
            me->CastSpell(me, SPELL_BARREL_KEG_PLACED, true);
            me->AddUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED);
            player->KilledMonsterCredit(NPC_QUEST_14348_KILL_CREDIT);
            m_events.ScheduleEvent(EVENT_KEG_PLACED, 3s);
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);
            while (uint32 eventId = m_events.ExecuteEvent())
                if (eventId == EVENT_KEG_PLACED)
                {
                    me->CastSpell(me, SPELL_HORRID_ABOMINATION_EXPLOSION, true);
                    me->KillSelf();
                    return;
                }

            if (!m_creditGiven && UpdateVictim())
                DoMeleeAttackIfReady();
        }

    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_horrid_abomination_36231AI(creature);
    }
};

// 69094
class spell_cast_keg_69094 : public SpellScriptLoader
{
public:
    spell_cast_keg_69094() : SpellScriptLoader("spell_cast_keg_69094") { }

    class spell_cast_keg_69094_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_cast_keg_69094_SpellScript);

        void CheckTarget(WorldObject*& target)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Creature* abomination = target ? target->ToCreature() : nullptr;
            if (!player || player->GetQuestStatus(QUEST_YOU_CANT_TAKE_EM_ALONE) != QUEST_STATUS_INCOMPLETE
                || !abomination || abomination->GetEntry() != NPC_HORRID_ABOMINATION || !abomination->IsAlive())
                target = nullptr;
        }

        void HandleKeg(SpellEffIndex effIndex)
        {
            // The default ForceCast makes the abomination cast the barrel on the player.
            // Its AI handles the successful item hit and applies the barrel to itself.
            PreventHitDefaultEffect(effIndex);
        }

        void Register() override
        {
            OnEffectHitTarget += SpellEffectFn(spell_cast_keg_69094_SpellScript::HandleKeg, EFFECT_0, SPELL_EFFECT_FORCE_CAST);
            OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_cast_keg_69094_SpellScript::CheckTarget, EFFECT_0, TARGET_UNIT_TARGET_ANY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_cast_keg_69094_SpellScript();
    }
};

// 36287  // Quest save the children 14368
class npc_cynthia_36267 : public CreatureScript
{
public:
    npc_cynthia_36267() : CreatureScript("npc_cynthia_36267") { }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        if (player->GetQuestStatus(QUEST_SAVE_THE_CHILDREN) == QUEST_STATUS_INCOMPLETE
            && player->GetQuestObjectiveData(QUEST_SAVE_THE_CHILDREN, 0) == 0)
        {
            sCreatureTextMgr->SendChat(creature, 0, NULL, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            sCreatureTextMgr->SendChat(creature, 1, nullptr, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            player->KilledMonsterCredit(NPC_CYNTIA_CREDIT);
            return true;
        }
        return false;
    }
};

// 36288
class npc_james_36268 : public CreatureScript
{
public:
    npc_james_36268() : CreatureScript("npc_james_36268") { }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        if (player->GetQuestStatus(QUEST_SAVE_THE_CHILDREN) == QUEST_STATUS_INCOMPLETE
            && player->GetQuestObjectiveData(QUEST_SAVE_THE_CHILDREN, 2) == 0)
        {
            sCreatureTextMgr->SendChat(creature, 0, NULL, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            sCreatureTextMgr->SendChat(creature, 1, nullptr, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            player->KilledMonsterCredit(NPC_JAMES_CREDIT);
            return true;
        }
        return false;
    }
};

// 36289
class npc_ashley_36269 : public CreatureScript
{
public:
    npc_ashley_36269() : CreatureScript("npc_ashley_36269") { }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        if (player->GetQuestStatus(QUEST_SAVE_THE_CHILDREN) == QUEST_STATUS_INCOMPLETE
            && player->GetQuestObjectiveData(QUEST_SAVE_THE_CHILDREN, 1) == 0)
        {
            sCreatureTextMgr->SendChat(creature, 0, NULL, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            sCreatureTextMgr->SendChat(creature, 1, nullptr, CHAT_MSG_ADDON, LANG_ADDON, TEXT_RANGE_NORMAL, 0, TEAM_OTHER, false, player);
            player->KilledMonsterCredit(NPC_ASHLEY_CREDIT);
            return true;
        }
        return false;
    }
};

// 36283: the machinist must be defeated before a quest player can control seat 0.
class npc_forsaken_catapult_36283 : public CreatureScript
{
public:
    npc_forsaken_catapult_36283() : CreatureScript("npc_forsaken_catapult_36283") { }
    struct npc_forsaken_catapult_36283AI : public ScriptedAI
    {
        npc_forsaken_catapult_36283AI(Creature* creature) : ScriptedAI(creature) { }
        enum Events { CHECK = 1, BOULDER, REARM, LAUNCH };
        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_forsakenGUID;
        bool m_defeated = false;
        bool m_launchPending = false;
        Position m_destination;
        float m_speedXY = 0.0f;
        float m_speedZ = 0.0f;

        void OnCharmed(bool) override { } // Keep this vehicle AI while the player aims.

        bool QuestPlayer(Player* player) const
        {
            return player && player->IsAlive() && player->GetMapId() == 654
                && me->InSamePhase(player->GetPhaseShift())
                && (player->GetQuestStatus(14382) == QUEST_STATUS_INCOMPLETE
                    || player->GetQuestStatus(14382) == QUEST_STATUS_COMPLETE);
        }

        void Availability()
        {
            me->setFaction(m_defeated ? 35 : 1735);
            if (m_defeated && m_playerGUID.IsEmpty())
                me->RemoveFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NOT_SELECTABLE);
            else
                me->SetFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NOT_SELECTABLE);
        }

        void CancelLaunch()
        {
            m_events.CancelEvent(LAUNCH);
            m_launchPending = false;
        }

        void Reset() override
        {
            CancelLaunch();
            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                if (player->GetVehicleBase() == me)
                    player->ExitVehicle();
            m_playerGUID = ObjectGuid::Empty;
            m_events.Reset();
            me->SetFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_IMMUNE_TO_NPC);
            me->SetReactState(REACT_PASSIVE);
            Availability();
            m_events.ScheduleEvent(CHECK, 500ms);
            m_events.ScheduleEvent(BOULDER, 5s);
            m_events.ScheduleEvent(REARM, 3min);
        }

        void JustSummoned(Creature* summon) override
        {
            if (summon->GetEntry() == NPC_FORSAKEN_MACHINIST)
            {
                m_forsakenGUID = summon->GetGUID();
                m_defeated = false;
                Availability();
            }
        }

        void SummonedCreatureDies(Creature* summon, Unit*) override
        {
            if (summon->GetGUID() == m_forsakenGUID)
            {
                m_defeated = true;
                m_events.RescheduleEvent(REARM, 3min);
                Availability();
            }
        }

        void PassengerBoarded(Unit* passenger, int8 seat, bool apply) override
        {
            if (Player* player = passenger->ToPlayer())
            {
                if (apply)
                {
                    if (seat != 0 || !m_defeated || !QuestPlayer(player)
                        || (!m_playerGUID.IsEmpty() && m_playerGUID != player->GetGUID()))
                    {
                        player->ExitVehicle();
                        return;
                    }
                    m_playerGUID = player->GetGUID();
                }
                else if (m_playerGUID == player->GetGUID())
                {
                    CancelLaunch();
                    m_playerGUID = ObjectGuid::Empty;
                    m_events.RescheduleEvent(REARM, 3min);
                }
                Availability();
            }
            // Native accessory 36292 belongs in seat 2, not the player control seat.
        }

        bool QueueLaunch(Player* player, Position const* destination, float speedXY, float speedZ)
        {
            if (m_launchPending || !m_defeated || !QuestPlayer(player)
                || player->GetGUID() != m_playerGUID || player->GetVehicleBase() != me
                || !me->GetVehicleKit() || me->GetVehicleKit()->GetPassenger(0) != player
                || !destination || !destination->IsPositionValid() || !std::isfinite(destination->GetPositionX())
                || !std::isfinite(destination->GetPositionY()) || !std::isfinite(destination->GetPositionZ())
                || !std::isfinite(speedXY) || !std::isfinite(speedZ) || speedXY < 0.01f || speedZ < 0.0f)
                return false;
            m_destination = *destination;
            m_speedXY = speedXY;
            m_speedZ = speedZ;
            m_launchPending = true;
            m_events.ScheduleEvent(LAUNCH, 2s);
            return true;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);
            while (uint32 event = m_events.ExecuteEvent())
            {
                switch (event)
                {
                    case CHECK:
                    {
                        if (Creature* machinist = ObjectAccessor::GetCreature(*me, m_forsakenGUID))
                        {
                            if (!machinist->IsAlive())
                                m_defeated = true;
                            else if (machinist->GetVehicleBase() == me)
                                if (Player* player = me->SelectNearestPlayer(7.0f))
                                    if (QuestPlayer(player))
                                    {
                                        machinist->ExitVehicle();
                                        machinist->AI()->AttackStart(player);
                                    }
                        }
                        if (!m_playerGUID.IsEmpty())
                        {
                            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                            if (!QuestPlayer(player) || player->GetVehicleBase() != me)
                            {
                                CancelLaunch();
                                m_playerGUID = ObjectGuid::Empty;
                                if (player && player->GetVehicleBase() == me)
                                    player->ExitVehicle();
                                m_events.RescheduleEvent(REARM, 3min);
                            }
                        }
                        Availability();
                        m_events.ScheduleEvent(CHECK, 500ms);
                        break;
                    }
                    case BOULDER:
                        if (Creature* machinist = ObjectAccessor::GetCreature(*me, m_forsakenGUID))
                            if (machinist->IsAlive() && machinist->GetVehicleBase() == me)
                                me->CastSpell(me, SPELL_FIERY_BOULDER, true);
                        m_events.ScheduleEvent(BOULDER, 8s, 15s);
                        break;
                    case REARM:
                    {
                        Creature* machinist = ObjectAccessor::GetCreature(*me, m_forsakenGUID);
                        if (m_playerGUID.IsEmpty() && (!machinist || !machinist->IsAlive()))
                            if (me->GetVehicleKit() && !me->GetVehicleKit()->GetPassenger(2))
                                if (TempSummon* summon = me->SummonCreature(NPC_FORSAKEN_MACHINIST,
                                    me->GetPosition(), TEMPSUMMON_DEAD_DESPAWN))
                                    summon->EnterVehicle(me, 2);
                        m_events.ScheduleEvent(REARM, 3min);
                        break;
                    }
                    case LAUNCH:
                    {
                        Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                        if (m_launchPending && QuestPlayer(player) && player->GetVehicleBase() == me
                            && me->GetVehicleKit() && me->GetVehicleKit()->GetPassenger(0) == player)
                        {
                            // Native safe-fall aura; the aimed destination is supplied by the spell.
                            me->AddAura(SPELL_LAUNCH2, player);
                            player->ExitVehicle();
                            player->GetMotionMaster()->MoveJump(m_destination, m_speedXY, m_speedZ);
                        }
                        CancelLaunch();
                        break;
                    }
                }
            }
        }
    };
    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 ? new npc_forsaken_catapult_36283AI(creature) : nullptr;
    }
};

// 68659: retain the player's trajectory destination, never teleport to a nearby NPC.
class spell_launch_68659 : public SpellScriptLoader
{
public:
    spell_launch_68659() : SpellScriptLoader("spell_launch_68659") { }
    class spell_launch_68659_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_launch_68659_SpellScript);
        using CatapultAI = npc_forsaken_catapult_36283::npc_forsaken_catapult_36283AI;

        CatapultAI* Catapult() const
        {
            Creature* creature = GetCaster()->ToCreature();
            uint32 script = sObjectMgr->GetScriptId("npc_forsaken_catapult_36283");
            if (!creature || creature->GetEntry() != NPC_FORSAKEN_CATAPULT
                || creature->GetMapId() != 654 || !script || creature->GetScriptId() != script)
                return nullptr;
            return CAST_AI(CatapultAI, creature->AI());
        }

        SpellCastResult CheckLaunch()
        {
            CatapultAI* ai = Catapult();
            if (!ai || !GetCaster()->GetVehicleKit())
                return SPELL_FAILED_DONT_REPORT;
            Unit* passenger = GetCaster()->GetVehicleKit()->GetPassenger(0);
            Player* player = passenger ? passenger->ToPlayer() : nullptr;
            if (!ai->QuestPlayer(player) || !ai->m_defeated || ai->m_launchPending)
                return SPELL_FAILED_NOT_READY;
            Position const* destination = GetExplTargetDest();
            float speedXY = GetSpell()->m_targets.GetSpeedXY();
            float speedZ = GetSpell()->m_targets.GetSpeedZ();
            if (!destination || !destination->IsPositionValid() || !GetSpell()->m_targets.HasTraj()
                || !std::isfinite(destination->GetPositionX()) || !std::isfinite(destination->GetPositionY())
                || !std::isfinite(destination->GetPositionZ()) || !std::isfinite(speedXY) || !std::isfinite(speedZ)
                || speedXY < 0.01f || speedZ < 0.0f
                || GetCaster()->GetExactDist2d(destination) > GetSpellInfo()->GetMaxRange(false))
                return SPELL_FAILED_BAD_TARGETS;
            return SPELL_CAST_OK;
        }

        void PreserveControlSeat(SpellEffIndex index)
        {
            // Retail data switches to passenger seat 1. This core does not implement
            // its eject arc; keep seat 0 until the explicitly queued spline launch.
            PreventHitDefaultEffect(index);
        }

        void Launch()
        {
            if (CatapultAI* ai = Catapult())
                if (Vehicle* vehicle = GetCaster()->GetVehicleKit())
                    if (Unit* passenger = vehicle->GetPassenger(0))
                        ai->QueueLaunch(passenger->ToPlayer(), GetExplTargetDest(),
                            GetSpell()->m_targets.GetSpeedXY(), GetSpell()->m_targets.GetSpeedZ());
        }

        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(spell_launch_68659_SpellScript::CheckLaunch);
            OnEffectHitTarget += SpellEffectFn(spell_launch_68659_SpellScript::PreserveControlSeat, EFFECT_1, SPELL_EFFECT_FORCE_CAST);
            AfterCast += SpellCastFn(spell_launch_68659_SpellScript::Launch);
        }
    };
    SpellScript* GetSpellScript() const override { return new spell_launch_68659_SpellScript(); }
};

// 96185 trigger 66251
class spell_launch_96185 : public SpellScriptLoader
{
public:
    spell_launch_96185() : SpellScriptLoader("spell_launch_96185") { }

    class spell_launch_96185_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_launch_96185_SpellScript);

        ObjectGuid m_playerGUID;
        Position pos = Position();

        void CheckTarget(WorldObject*& target)
        {
            if (Vehicle* cat = GetCaster()->GetVehicleKit())
                if (Unit* pas = cat->GetPassenger(1))
                    if (Player* player = pas->ToPlayer())
                        target = player;
        }

        void Register() override
        {
            OnObjectTargetSelect += SpellObjectTargetSelectFn(spell_launch_96185_SpellScript::CheckTarget, EFFECT_0, TARGET_UNIT_CASTER);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_launch_96185_SpellScript();
    }
};

// 68591
class spell_fire_boulder_68591 : public SpellScriptLoader
{
public:
    spell_fire_boulder_68591() : SpellScriptLoader("spell_fire_boulder_68591") { }

    class IsNotEntryButPlayer
    {
    public:
        explicit IsNotEntryButPlayer(Unit const* caster, uint32 entry) : _caster(caster), _entry(entry) { }

        bool operator()(WorldObject* obj) const
        {
            if (_caster->GetExactDist2d(obj) < 5.0f || _caster->GetExactDist2d(obj) > 80.0f)
                return true;
            if (Player* player = obj->ToPlayer())
                return player->IsMounted();
            else if (Creature* target = obj->ToCreature())
                return target->GetEntry() != _entry;

            return false;
        }

    private:
        const Unit* _caster;
        uint32 _entry;
    };

    class spell_fire_boulder_68591_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_fire_boulder_68591_SpellScript);

        void CheckTargets(std::list<WorldObject*>& targets)
        {
            targets.remove_if(IsNotEntryButPlayer(GetCaster(), NPC_GENERIC_TRIGGER_LAB_AOI));

            if (!targets.empty())
            {
                WorldObject* target = Trinity::Containers::SelectRandomContainerElement(targets);
                if (target)
                    GetCaster()->SetFacingToObject(target);
                else
                    this->FinishCast(SPELL_CAST_OK);
            }    
        }

        void Register() override
        {
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_fire_boulder_68591_SpellScript::CheckTargets, EFFECT_0, TARGET_UNIT_SRC_AREA_ENTRY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_fire_boulder_68591_SpellScript();
    }
};
// 36409
class npc_mastiff_36409 : public CreatureScript
{
public:
    npc_mastiff_36409() : CreatureScript("npc_mastiff_36409") { }

    enum eNPC
    {
        EVENT_SEND_MORE_MASTIFF                 = 901
    };

    struct npc_mastiff_36409AI : public ScriptedAI
    {
        npc_mastiff_36409AI(Creature* creature) : ScriptedAI(creature), m_summons(creature),
            m_thyalaGUID(ObjectGuid::Empty), m_player_GUID(ObjectGuid::Empty) { }

        EventMap m_events;
        SummonList m_summons;
        ObjectGuid m_thyalaGUID;
        ObjectGuid m_player_GUID;
        uint32 m_lifetime = 0;

        void Reset() override
        {
            m_events.Reset();
            m_summons.DespawnAll();
            me->SetReactState(REACT_PASSIVE);
            if (!m_player_GUID.IsEmpty())
                m_events.ScheduleEvent(EVENT_SEND_MORE_MASTIFF, 250ms);
        }

        void IsSummonedBy(Unit* summoner) override
        {
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || player->GetQuestStatus(QUEST_LEADER_OF_THE_PACK) != QUEST_STATUS_INCOMPLETE)
            {
                me->DespawnOrUnsummon();
                return;
            }
            Creature* existing = player->GetSummonedCreatureByEntry(36409);
            Creature* thyala = me->FindNearestCreature(NPC_DARK_RANGER_THYALA, 100.0f);
            if ((existing && existing != me) || !thyala || !thyala->InSamePhase(player->GetPhaseShift())
                || (thyala->GetLootRecipient() && !thyala->isTappedBy(player)))
            {
                me->DespawnOrUnsummon();
                return;
            }
            m_player_GUID = player->GetGUID();
            m_thyalaGUID = thyala->GetGUID();
            m_events.Reset();
            m_events.ScheduleEvent(EVENT_SEND_MORE_MASTIFF, 250ms);
            me->GetMotionMaster()->MoveChase(thyala, 3.0f, 0.0f);
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage) override
        {
            damage = 0; // Invisible encounter controller only, not ordinary NPC.
        }

        void JustSummoned(Creature* summon) override
        {
            m_summons.Summon(summon);
            summon->AI()->SetGUID(m_player_GUID, PLAYER_GUID);
            summon->AI()->SetGUID(m_thyalaGUID, NPC_DARK_RANGER_THYALA);
        }

        void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
        {
            m_summons.Despawn(summon);
        }

        void SummonedCreatureDespawn(Creature* summon) override
        {
            m_summons.Despawn(summon); // Idempotent after death, cannot underflow.
        }

        void JustDied(Unit* /*killer*/) override
        {
            m_summons.DespawnAll();
        }

        void UpdateAI(uint32 diff) override
        {
            m_lifetime += diff;
            Player* player = ObjectAccessor::GetPlayer(*me, m_player_GUID);
            Creature* thyala = ObjectAccessor::GetCreature(*me, m_thyalaGUID);
            if (m_lifetime >= 120000 || !player || !player->IsAlive() || player->GetMapId() != 654
                || player->GetQuestStatus(QUEST_LEADER_OF_THE_PACK) != QUEST_STATUS_INCOMPLETE
                || !me->InSamePhase(player->GetPhaseShift()) || !thyala || !thyala->IsAlive()
                || !thyala->InSamePhase(player->GetPhaseShift()) || me->GetDistance(player) > 100.0f
                || (thyala->GetLootRecipient() && !thyala->isTappedBy(player)))
            {
                m_events.Reset();
                m_summons.DespawnAll();
                me->DespawnOrUnsummon();
                return;
            }
            m_events.Update(diff);
            if (m_events.ExecuteEvent() == EVENT_SEND_MORE_MASTIFF)
            {
                std::list<Creature*> triggers;
                GetCreatureListWithEntryInGrid(triggers, me, NPC_TRIGGER, 100.0f);
                for (Creature* trigger : triggers)
                {
                    if (m_summons.size() >= 50)
                        break;
                    if (trigger->InSamePhase(player->GetPhaseShift()))
                        me->SummonCreature(NPC_MASTIFF, trigger->GetNearPosition(5.0f, frand(0.0f, 6.28f)),
                            TEMPSUMMON_TIMED_DESPAWN, urand(30000, 60000));
                }
                m_events.ScheduleEvent(EVENT_SEND_MORE_MASTIFF, 250ms);
            }
            // Owner-attributed mastiff damage uses the normal Unit::Kill reward path.
            // Merely observing an unrelated dead Thyala never grants quest credit.
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_mastiff_36409AI(creature);
    }
};

//49240 ->68682 summons the controller through its native effect.
class spell_gilneas_leader_of_the_pack : public SpellScriptLoader
{
public:
    spell_gilneas_leader_of_the_pack() : SpellScriptLoader("spell_gilneas_leader_of_the_pack") { }
    class spell_gilneas_leader_of_the_pack_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_gilneas_leader_of_the_pack_SpellScript);
        SpellCastResult CheckPack()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || player->GetQuestStatus(QUEST_LEADER_OF_THE_PACK) != QUEST_STATUS_INCOMPLETE
                || player->GetSummonedCreatureByEntry(36409))
                return SPELL_FAILED_BAD_TARGETS;
            return SPELL_CAST_OK;
        }
        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(spell_gilneas_leader_of_the_pack_SpellScript::CheckPack);
        }
    };
    SpellScript* GetSpellScript() const override
    {
        return new spell_gilneas_leader_of_the_pack_SpellScript();
    }
};

// 36405
class npc_mastiff_36405 : public CreatureScript
{
public:
    npc_mastiff_36405() : CreatureScript("npc_mastiff_36405") { }

    struct npc_mastiff_36405AI : public ScriptedAI
    {
        npc_mastiff_36405AI(Creature* creature) : ScriptedAI(creature),
            m_thyalaGUID(ObjectGuid::Empty), m_player_GUID(ObjectGuid::Empty) { }

        EventMap m_events;
        ObjectGuid m_thyalaGUID;
        ObjectGuid m_player_GUID;

        void Reset() override
        {
            me->SetWalk(true);
            me->SetSpeed(MOVE_RUN, true);
            me->SetReactState(REACT_AGGRESSIVE);
            m_events.Reset();
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1s);
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            switch (id)
            {
                case PLAYER_GUID:
                {
                    m_player_GUID = guid;
                    me->SetOwnerGUID(guid); // Attribute real damage/kills to the quest participant.
                    break;
                }
                case NPC_DARK_RANGER_THYALA:
                {
                    m_thyalaGUID = guid;
                    break;
                }
            }
        }

        void DamageDealt(Unit* victim, uint32& damage, DamageEffectType /*type*/, SpellInfo const* /*spell*/) override
        {
            Creature* thyala = victim ? victim->ToCreature() : nullptr;
            Player* player = ObjectAccessor::GetPlayer(*me, m_player_GUID);
            if (!damage || !thyala || thyala->GetEntry() != NPC_DARK_RANGER_THYALA
                || thyala->GetGUID() != m_thyalaGUID || !player || !player->IsAlive()
                || player->GetMapId() != 654 || !me->InSamePhase(player->GetPhaseShift())
                || player->GetQuestStatus(QUEST_LEADER_OF_THE_PACK) != QUEST_STATUS_INCOMPLETE
                || (thyala->GetLootRecipient() && !thyala->isTappedBy(player)))
                return;
            // These NPC summons are not player-controlled pets. Bridge only their
            // real damage to the ordinary loot/damage requirement and Unit::Kill path.
            float multiplier = thyala->GetHealthMultiplierForTarget(me);
            if (multiplier <= 0.0f)
                return;
            uint32 effectiveDamage = static_cast<uint32>(damage / multiplier);
            if (!effectiveDamage)
                return;
            if (!thyala->GetLootRecipient())
                thyala->SetLootRecipient(player);
            if (!me->IsControlledByPlayer())
                thyala->LowerPlayerDamageReq(std::min<uint64>(effectiveDamage, thyala->GetHealth()));
        }

        void EnterEvadeMode(EvadeReason /*reason*/) override
        {
            StartAttackThyala();
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1s);
        }

        void UpdateAI(uint32 diff) override
        {
            // Existing unsummoned mastiffs keep ordinary NPC combat behavior.
            if (!m_player_GUID.IsEmpty())
            {
                Player* player = ObjectAccessor::GetPlayer(*me, m_player_GUID);
                TempSummon* summon = me->ToTempSummon();
                if (!player || !player->IsAlive() || player->GetMapId() != 654
                    || player->GetQuestStatus(QUEST_LEADER_OF_THE_PACK) != QUEST_STATUS_INCOMPLETE
                    || !me->InSamePhase(player->GetPhaseShift()) || !summon
                    || !ObjectAccessor::GetCreature(*me, summon->GetSummonerGUID()))
                {
                    me->DespawnOrUnsummon();
                    return;
                }
            }
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_ATTACK:
                    {
                        StartAttackThyala();
                        m_events.ScheduleEvent(EVENT_CHECK_ATTACK, 1s);
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }

        void StartAttackThyala()
        {
            Creature* thyala = ObjectAccessor::GetCreature(*me, m_thyalaGUID);
            if (!thyala)
                return;

            if (!thyala->IsAlive() || !thyala->IsInWorld())
            {
                me->DespawnOrUnsummon(1);
                return;
            }

            if (me->IsInCombat())
                if (Unit* npc = me->GetVictim())
                    if (npc->GetEntry() == NPC_DARK_RANGER_THYALA)
                        return;

            me->SetReactState(REACT_AGGRESSIVE);
            me->GetMotionMaster()->MoveChase(thyala, 3.0f, frand(0.0f, 6.28f));
            me->Attack(thyala, true);
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        if (!creature->ToTempSummon())
            return nullptr; // selectAI retains the normal factory for persistent NPC.
        return new npc_mastiff_36405AI(creature);
    }
};

// 36290
class npc_lord_godfrey_36290 : public CreatureScript
{
public:
    npc_lord_godfrey_36290() : CreatureScript("npc_lord_godfrey_36290") { }

    bool OnQuestAccept(Player* player, Creature* /*creature*/, Quest const* quest) override
    {
        if (quest->GetQuestId() == 14396)
        {
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_07);
            player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08, player);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_10);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_12);
        }

        return true;
    }
};

// Phase 183(16384) // from here: WorldMap 678 and TerrainSwap 655

// 36440
class npc_drowning_watchman_36440 : public CreatureScript
{
public:
    npc_drowning_watchman_36440() : CreatureScript("npc_drowning_watchman_36440") { }

    enum eNpc
    {
        EVENT_CHECK_NEAR_GREYMANE               = 901
    };

    struct npc_drowning_watchman_36440AI : public ScriptedAI
    {
        npc_drowning_watchman_36440AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        bool m_isOnPlayer;
        bool m_delivered = false;

        void Reset() override
        {
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
            m_isOnPlayer = false;
            m_delivered = false;
        }

        void SpellHit(Unit* caster, SpellInfo const* spell) override
        {
            if (caster && spell && !m_isOnPlayer && !m_delivered)
                if (spell->Id == SPELL_RESCUE_DROWNING_WATCHMANN)
                    if (Player* player = caster->ToPlayer())
                        if (player->IsAlive() && me->IsAlive() && me->GetMapId() == 654
                            && player->GetMapId() == me->GetMapId() && me->IsInPhase(player)
                            && player->GetQuestStatus(QUEST_GASPING_FOR_BREATH) == QUEST_STATUS_INCOMPLETE)
                        {
                            m_isOnPlayer = true;
                            m_playerGUID = player->GetGUID();
                            m_events.ScheduleEvent(EVENT_MASTER_RESET, 1min);
                            m_events.ScheduleEvent(EVENT_CHECK_NEAR_GREYMANE, 1s);
                        }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_MASTER_RESET:
                        me->DespawnOrUnsummon(10ms);
                        break;
                    case EVENT_CHECK_NEAR_GREYMANE:
                    {
                        Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                        if (!player || !player->IsAlive() || player->GetMapId() != me->GetMapId()
                            || !me->IsInPhase(player)
                            || player->GetQuestStatus(QUEST_GASPING_FOR_BREATH) != QUEST_STATUS_INCOMPLETE
                            || me->GetVehicleBase() != player)
                        {
                            me->ExitVehicle();
                            me->DespawnOrUnsummon(10ms);
                            return;
                        }

                        Creature* liam = me->FindNearestCreature(NPC_PRINCE_LIAM_GREYMANE, 15.0f);
                        if (m_isOnPlayer && !m_delivered && !player->IsInWater()
                            && liam && liam->IsAlive() && liam->GetMapId() == me->GetMapId()
                            && liam->IsInPhase(player))
                        {
                            m_isOnPlayer = false;
                            m_delivered = true;
                            player->KilledMonsterCredit(NPC_DROWNING_WATCHMANN_CREDIT);
                            player->CastSpell(me, SPELL_SAVE_DROWNING_MILITIA_EFFECT, true);
                            me->ExitVehicle();
                            player->RemoveAurasDueToSpell(SPELL_RESCUE_DROWNING_WATCHMANN);
                            Talk(0, player);
                            m_events.ScheduleEvent(EVENT_DESPAWN_PART_00, 3s);
                            break;
                        }

                        m_events.ScheduleEvent(EVENT_CHECK_NEAR_GREYMANE, 1s);
                        break;
                    }
                    case EVENT_DESPAWN_PART_00:
                        me->DespawnOrUnsummon(10ms);
                        break;
                }
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_drowning_watchman_36440AI(creature);
    }
};

// 68735
class spell_rescue_drowning_watchman_68735 : public SpellScriptLoader
{
public:
    spell_rescue_drowning_watchman_68735() : SpellScriptLoader("spell_rescue_drowning_watchman_68735") { }

    class spell_rescue_drowning_watchman_68735_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_rescue_drowning_watchman_68735_SpellScript);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ 68735 });
        }

        SpellCastResult CheckTarget()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Creature* watchman = GetExplTargetUnit() ? GetExplTargetUnit()->ToCreature() : nullptr;
            if (!player || !player->IsAlive() || !watchman || watchman->GetEntry() != 36440 || !watchman->IsAlive()
                || player->GetMapId() != 654 || watchman->GetMapId() != player->GetMapId() || !watchman->IsInPhase(player)
                || watchman->GetVehicleBase() || !player->IsInWater()
                || player->GetQuestStatus(QUEST_GASPING_FOR_BREATH) != QUEST_STATUS_INCOMPLETE
                || (player->GetVehicleKit() && player->GetVehicleKit()->GetPassenger(0)))
                return SPELL_FAILED_BAD_TARGETS;
            return SPELL_CAST_OK;
        }

        void HandleEffectDummy(SpellEffIndex /*effIndex*/)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Creature* watchman = GetHitUnit() ? GetHitUnit()->ToCreature() : nullptr;
            if (!player || !player->IsAlive() || !watchman || watchman->GetEntry() != 36440 || !watchman->IsAlive()
                || player->GetMapId() != 654 || watchman->GetMapId() != player->GetMapId() || !watchman->IsInPhase(player))
                return;

            if (player->GetQuestStatus(QUEST_GASPING_FOR_BREATH) != QUEST_STATUS_INCOMPLETE)
            {
                player->RemoveAurasDueToSpell(SPELL_RESCUE_DROWNING_WATCHMANN);
                return;
            }

            if (watchman->GetVehicleBase())
                return; // An already carried watchman cannot be stolen or credited twice.

            if (!player->GetVehicleKit() || !player->IsInWater())
            {
                player->RemoveAurasDueToSpell(SPELL_RESCUE_DROWNING_WATCHMANN);
                return;
            }

            watchman->CastCustomSpell(VEHICLE_SPELL_RIDE_HARDCODED, SPELLVALUE_BASE_POINT0, 1, player, false);
        }

        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(spell_rescue_drowning_watchman_68735_SpellScript::CheckTarget);
            OnEffectHitTarget += SpellEffectFn(spell_rescue_drowning_watchman_68735_SpellScript::HandleEffectDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_rescue_drowning_watchman_68735_SpellScript();
    }
};

// Personal actor route from pinned Pandaria5.4.8; shared questgiver36458 is untouched.
static Position const GrandmaSceneRoute[] =
{
    { -2106.54f, 2342.69f, 6.93668f, 0.0f },
    { -2106.12f, 2334.90f, 7.36691f, 0.0f },
    { -2117.80f, 2357.15f, 5.88139f, 0.0f },
    { -2111.46f, 2366.22f, 7.17151f, 0.0f }
};

class npc_gilneas_grandma_scene : public CreatureScript
{
public:
    npc_gilneas_grandma_scene() : CreatureScript("npc_gilneas_grandma_scene") { }
    struct ai : public ScriptedAI
    {
        ai(Creature* creature) : ScriptedAI(creature) { }
        enum Stage { IDLE, APPROACH_0, APPROACH_1, FIGHT, RETURN_WAIT, RETURN_2, RETURN_3, DONE };
        enum Events { CHECK = 1, ATTACK, RETURN };
        EventMap m_events;
        ObjectGuid m_ownerGUID;
        ObjectGuid m_luciusGUID;
        Stage m_stage = IDLE;
        uint32 m_elapsed = 0;

        void Reset() override
        {
            m_events.Reset();
            if (!m_ownerGUID.IsEmpty())
                me->DespawnOrUnsummon(); // Never replay a personal scene on evade.
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (Player* player = summoner ? summoner->ToPlayer() : nullptr)
            {
                m_ownerGUID = player->GetGUID();
                me->RemoveFlag64(UNIT_NPC_FLAGS, UNIT_NPC_FLAG_QUESTGIVER | UNIT_NPC_FLAG_GOSSIP);
                me->SetReactState(REACT_PASSIVE);
                me->SetFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NON_ATTACKABLE);
                me->SetWalk(true);
                m_events.ScheduleEvent(CHECK, 1s);
            }
            else
                me->DespawnOrUnsummon();
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            if (id == 36461 && m_stage == IDLE)
                m_luciusGUID = guid;
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            return id == 0 ? m_ownerGUID : ObjectGuid::Empty;
        }

        Creature* Lucius() const
        {
            Creature* lucius = ObjectAccessor::GetCreature(*me, m_luciusGUID);
            uint32 script = sObjectMgr->GetScriptId("npc_gilneas_lucius_the_cruel");
            return lucius && script && lucius->GetScriptId() == script
                && lucius->AI()->GetGUID(0) == m_ownerGUID ? lucius : nullptr;
        }

        void DoAction(int32 action) override
        {
            if (action == 1 && m_stage == IDLE && Lucius())
            {
                m_stage = APPROACH_0;
                me->GetMotionMaster()->MovePoint(0, GrandmaSceneRoute[0]);
            }
            else if (action == 2 && m_stage != IDLE && m_stage < RETURN_WAIT)
            {
                m_events.CancelEvent(ATTACK);
                me->CombatStop(true);
                me->SetReactState(REACT_PASSIVE);
                me->GetMotionMaster()->Clear();
                m_stage = RETURN_WAIT;
                m_events.ScheduleEvent(RETURN, 4s);
            }
        }

        void MovementInform(uint32 type, uint32 point) override
        {
            if (type != POINT_MOTION_TYPE)
                return;
            if (m_stage == APPROACH_0 && point == 0)
            {
                m_stage = APPROACH_1;
                me->GetMotionMaster()->MovePoint(1, GrandmaSceneRoute[1]);
            }
            else if (m_stage == APPROACH_1 && point == 1)
            {
                if (!sCreatureDisplayInfoStore.LookupEntry(36852))
                {
                    TC_LOG_ERROR("sql.sql", "Gilneas Grandma14401: missing display36852; helper removed");
                    me->DespawnOrUnsummon();
                    return;
                }
                m_stage = FIGHT;
                me->SetDisplayId(36852);
                if (sCreatureTextMgr->TextExist(36458, 0))
                    Talk(0, m_ownerGUID);
                me->RemoveFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_IMMUNE_TO_NPC);
                m_events.ScheduleEvent(ATTACK, 800ms);
            }
            else if (m_stage == RETURN_2 && point == 2)
            {
                m_stage = RETURN_3;
                me->GetMotionMaster()->MovePoint(3, GrandmaSceneRoute[3]);
            }
            else if (m_stage == RETURN_3 && point == 3)
            {
                m_stage = DONE;
                m_events.Reset();
                me->DespawnOrUnsummon();
            }
        }

        void AttackStart(Unit* target) override
        {
            if (m_stage == FIGHT && target && target->GetGUID() == m_luciusGUID)
                ScriptedAI::AttackStart(target);
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            if (!attacker || attacker->GetGUID() != m_luciusGUID)
                damage = 0; // This private helper fights only her own ambusher.
        }

        void UpdateAI(uint32 diff) override
        {
            m_elapsed += diff;
            m_events.Update(diff);
            while (uint32 event = m_events.ExecuteEvent())
            {
                if (event == CHECK)
                {
                    Player* player = ObjectAccessor::GetPlayer(*me, m_ownerGUID);
                    if (!player || !player->IsAlive() || player->GetMapId() != 654 || !me->IsInPhase(player)
                        || (player->GetQuestStatus(QUEST_GRANDMAS_CAT) != QUEST_STATUS_INCOMPLETE
                            && player->GetQuestStatus(QUEST_GRANDMAS_CAT) != QUEST_STATUS_COMPLETE)
                        || m_elapsed >= 180000 || (m_stage < RETURN_WAIT && !Lucius()))
                    {
                        me->DespawnOrUnsummon();
                        return;
                    }
                    m_events.ScheduleEvent(CHECK, 1s);
                }
                else if (event == ATTACK && m_stage == FIGHT)
                {
                    if (Creature* lucius = Lucius())
                        if (lucius->IsAlive())
                        {
                            me->SetReactState(REACT_DEFENSIVE);
                            AttackStart(lucius);
                        }
                }
                else if (event == RETURN && m_stage == RETURN_WAIT)
                {
                    m_stage = RETURN_2;
                    me->GetMotionMaster()->MovePoint(2, GrandmaSceneRoute[2]);
                }
            }
            if (m_stage == FIGHT && UpdateVictim())
                DoMeleeAttackIfReady();
        }
    };
    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 && creature->IsSummon() && creature->IsVisibleBySummonerOnly() ? new ai(creature) : nullptr;
    }
};

// Chance stays shared; ambush, helper and loot belong to each interacting player.
class npc_chance_36459 : public CreatureScript
{
public:
    npc_chance_36459() : CreatureScript("npc_chance_36459") { }
    bool OnGossipHello(Player* player, Creature* creature) override
    {
        if (!player || !player->IsAlive() || player->GetMapId() != 654 || creature->GetMapId() != 654
            || !player->IsInPhase(creature) || player->GetQuestStatus(QUEST_GRANDMAS_CAT) != QUEST_STATUS_INCOMPLETE
            || player->GetDistance(creature) > 5.0f || player->GetSummonedCreatureByEntry(NPC_LUCIUS))
            return true;
        CreatureTemplate const* info = sObjectMgr->GetCreatureTemplate(NPC_LUCIUS);
        uint32 script = sObjectMgr->GetScriptId("npc_gilneas_lucius_the_cruel");
        if (!info || !script || info->ScriptID != script)
            return true;
        if (Creature* lucius = player->SummonCreature(NPC_LUCIUS, -2111.533f, 2329.95f, 7.390349f,
            0.151307f, TEMPSUMMON_TIMED_DESPAWN, 180000, true))
            lucius->AI()->DoAction(1);
        return true;
    }
};

class npc_gilneas_lucius_the_cruel : public CreatureScript
{
public:
    npc_gilneas_lucius_the_cruel() : CreatureScript("npc_gilneas_lucius_the_cruel") { }
    struct ai : public ScriptedAI
    {
        ai(Creature* creature) : ScriptedAI(creature) { }
        enum Stage { IDLE, APPROACH, CATCH, FIGHT, DEAD };
        enum Events { CHECK = 1, TAUNT, FIGHT_START, GRANDMA, SHOOT };
        ObjectGuid m_ownerGUID;
        ObjectGuid m_grandmaGUID;
        EventMap m_events;
        Stage m_stage = IDLE;

        void Cleanup()
        {
            m_events.Reset();
            if (Creature* grandma = ObjectAccessor::GetCreature(*me, m_grandmaGUID))
                if (grandma->AI()->GetGUID(0) == m_ownerGUID)
                    grandma->DespawnOrUnsummon();
            m_grandmaGUID = ObjectGuid::Empty;
            me->DespawnOrUnsummon();
        }

        void Reset() override
        {
            m_events.Reset();
            if (!m_ownerGUID.IsEmpty())
                Cleanup();
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            return id == 0 ? m_ownerGUID : ObjectGuid::Empty;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (Player* player = summoner ? summoner->ToPlayer() : nullptr)
            {
                m_ownerGUID = player->GetGUID();
                SetCombatMovement(false);
                me->SetReactState(REACT_PASSIVE);
                me->SetFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NON_ATTACKABLE);
                m_events.ScheduleEvent(CHECK, 1s);
            }
            else
                Cleanup();
        }

        void DoAction(int32 action) override
        {
            if (action != 1 || m_stage != IDLE || m_ownerGUID.IsEmpty())
                return;
            m_stage = APPROACH;
            me->GetMotionMaster()->MovePoint(1, -2106.372f, 2331.106f, 7.360674f);
            m_events.ScheduleEvent(TAUNT, 1s);
        }

        void MovementInform(uint32 type, uint32 point) override
        {
            if (type != POINT_MOTION_TYPE || point != 1 || m_stage != APPROACH)
                return;
            m_stage = CATCH;
            me->HandleEmoteCommand(EMOTE_ONESHOT_KNEEL);
            m_events.ScheduleEvent(FIGHT_START, 5s); // 4s catch +1s in the pinned scene.
            m_events.ScheduleEvent(GRANDMA, 5500ms); // 4s catch +1.5s summon.
        }

        void AttackStart(Unit* target) override
        {
            Player* player = target ? target->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
            if (m_stage == FIGHT && target && (target->GetGUID() == m_grandmaGUID
                || (player && player->GetGUID() == m_ownerGUID)))
                ScriptedAI::AttackStart(target);
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            if (m_ownerGUID.IsEmpty())
                return;
            if (attacker && attacker->GetGUID() == m_grandmaGUID)
            {
                // Native loot requires real player damage. The helper may finish only
                // after that requirement is satisfied; no fake credit or health floor.
                if (!me->IsDamageEnoughForLootingAndReward() || me->GetLootRecipientGUID() != m_ownerGUID)
                    damage = 0;
                return;
            }
            Player* player = attacker ? attacker->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
            if (!player || player->GetGUID() != m_ownerGUID)
                damage = 0;
            else if (damage && !me->hasLootRecipient())
                me->SetLootRecipient(player); // Actual owner/pet hit only.
        }

        void JustDied(Unit*) override
        {
            m_stage = DEAD;
            m_events.Reset();
            if (Creature* grandma = ObjectAccessor::GetCreature(*me, m_grandmaGUID))
                if (grandma->AI()->GetGUID(0) == m_ownerGUID)
                    grandma->AI()->DoAction(2);
            // Keep the native lootable corpse; item49281 is not granted by script.
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);
            while (uint32 event = m_events.ExecuteEvent())
            {
                Player* player = ObjectAccessor::GetPlayer(*me, m_ownerGUID);
                if (!player || !player->IsAlive() || player->GetMapId() != 654 || !me->IsInPhase(player)
                    || player->GetQuestStatus(QUEST_GRANDMAS_CAT) != QUEST_STATUS_INCOMPLETE)
                {
                    Cleanup();
                    return;
                }
                if (event == CHECK)
                    m_events.ScheduleEvent(CHECK, 1s);
                else if (event == TAUNT && sCreatureTextMgr->TextExist(NPC_LUCIUS, 0))
                    Talk(0, player);
                else if (event == FIGHT_START && m_stage == CATCH)
                {
                    m_stage = FIGHT;
                    me->SetReactState(REACT_AGGRESSIVE);
                    me->HandleEmoteCommand(EMOTE_ONESHOT_NONE);
                    m_events.ScheduleEvent(SHOOT, 500ms);
                    me->RemoveFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NON_ATTACKABLE);
                    AttackStart(player);
                }
                else if (event == SHOOT && m_stage == FIGHT)
                {
                    if (UpdateVictim() && me->GetDistance(me->GetVictim()) > 2.0f)
                        DoCastVictim(41440);
                    m_events.ScheduleEvent(SHOOT, 1s);
                }
                else if (event == GRANDMA && m_stage == FIGHT && m_grandmaGUID.IsEmpty())
                {
                    CreatureTemplate const* info = sObjectMgr->GetCreatureTemplate(36458);
                    uint32 script = sObjectMgr->GetScriptId("npc_gilneas_grandma_scene");
                    if (info && script && info->ScriptID == script)
                        if (Creature* grandma = player->SummonCreature(36458, -2098.366f, 2352.075f,
                            7.160643f, 0.0f, TEMPSUMMON_TIMED_DESPAWN, 180000, true))
                        {
                            m_grandmaGUID = grandma->GetGUID();
                            grandma->AI()->SetGUID(me->GetGUID(), 36461);
                            grandma->AI()->DoAction(1);
                        }
                }
            }
            if (m_stage == FIGHT && UpdateVictim())
                DoMeleeAttackIfReady();
        }
    };
    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 && creature->IsSummon() && creature->IsVisibleBySummonerOnly() ? new ai(creature) : nullptr;
    }
};

// 36488
class npc_forsaken_castaway_36488 : public CreatureScript
{
public:
    npc_forsaken_castaway_36488() : CreatureScript("npc_forsaken_castaway_36488") { }

    struct npc_forsaken_castaway_36488AI : public ScriptedAI
    {
        npc_forsaken_castaway_36488AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_luciusGUID;
        ObjectGuid m_playerGUID;
        bool m_isLucisKilled;

        void DamageDealt(Unit* victim, uint32& damage, DamageEffectType /*damageType*/) override
        {
            uint8 rol = urand(0, 100);
            if (victim->GetEntry() == 36454 || victim->GetEntry() == 36455 || victim->GetEntry() == 36492 || victim->GetEntry() == 36456)
            {
                if (rol < 70 || victim->GetHealthPct() < 70.0f)
                    damage = 0;
                else
                    damage = 1;
            }
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            uint8 rol = urand(0, 100);
            if (attacker->GetEntry() == 36454 || attacker->GetEntry() == 36455 || attacker->GetEntry() == 36492 || attacker->GetEntry() == 36456)
            {
                if (rol < 70)
                    damage = 0;
                else
                    damage = 1;
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_forsaken_castaway_36488AI(creature);
    }
};

// 36555
class npc_mountain_horse_36555 : public CreatureScript
{
public:
    npc_mountain_horse_36555() : CreatureScript("npc_mountain_horse_36555") { }

    struct npc_mountain_horse_36555AI : public ScriptedAI
    {
        npc_mountain_horse_36555AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_lornaGUID;
        float m_dist;
        float m_angle;
        float m_size;
        Position m_oldPosition;
        bool m_isLornaNear;
        bool m_isPlayerMounted;
        bool m_hasPlayerRope;
        uint32 m_lifetime = 0; // Spell68908 duration40: twenty minutes.

        void Reset() override
        {
            m_events.Reset();
            if (!m_playerGUID.IsEmpty())
            {
                me->DespawnOrUnsummon();
                return;
            }
            m_lifetime = 0;
            m_playerGUID = ObjectGuid::Empty;
            m_lornaGUID = ObjectGuid::Empty;
            m_isLornaNear = false;
            m_isPlayerMounted = false;
            m_hasPlayerRope = false;
            me->SetWalk(false);
            me->SetSpeed(MOVE_RUN, 1.4f);
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (!m_playerGUID.IsEmpty())
                return;
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || me->GetMapId() != 654
                || player->GetMapId() != me->GetMapId() || !me->IsInPhase(player)
                || player->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE)
            {
                me->DespawnOrUnsummon();
                return;
            }
            m_playerGUID = player->GetGUID();
            me->SetReactState(REACT_PASSIVE);
            me->CastSpell(player, SPELL_ROPE_CHANNEL, true);
            m_dist = frand(3.0f, 5.0f);
            m_angle = frand(2.59f, 3.53f);
            m_size = me->GetObjectSize();
            m_oldPosition = player->GetPosition();
            m_events.ScheduleEvent(EVENT_START_FOLLOWING, 100ms);
        }

        void MoveInLineOfSight(Unit* who) override
        {
            if (!m_lornaGUID)
                if (Creature* lorna = who->ToCreature())
                    if (lorna->GetEntry() == NPC_LORNA_CROWLEY && lorna->IsAlive()
                        && lorna->GetMapId() == me->GetMapId() && me->IsInPhase(lorna))
                        m_lornaGUID = lorna->GetGUID();
        }

        void UpdateAI(uint32 diff) override
        {
            if (diff >= 1200000 - m_lifetime)
            {
                m_events.Reset();
                me->DespawnOrUnsummon();
                return;
            }
            m_lifetime += diff;
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_FOLLOWING:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            if (!player->IsAlive() || player->GetMapId() != me->GetMapId() || !me->IsInPhase(player)
                                || player->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE)
                            {
                                me->DespawnOrUnsummon();
                                return;
                            }
                            CheckLornaRelated(player);
                            if (m_oldPosition.GetExactDist(player) > 0.5f)
                            {
                                Position pos;
                                player->GetNearPoint(player, pos.m_positionX, pos.m_positionY, pos.m_positionZ, m_size, m_dist, m_angle);
                                me->GetMotionMaster()->MovePoint(0, pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ());
                                m_oldPosition = player->GetPosition();
                            }

                            if (!m_isPlayerMounted && m_hasPlayerRope)
                            {
                                if (m_isLornaNear)
                                    me->CastSpell(player, SPELL_MOUNTAIN_HORSE_CREDIT);

                                me->DespawnOrUnsummon();
                                return;
                            }
                        }
                        else
                        {
                            me->DespawnOrUnsummon();
                            return;
                        }
                        m_events.ScheduleEvent(EVENT_START_FOLLOWING, 100ms);
                        break;
                    }
                }
            }
        }

        void CheckLornaRelated(Player* player)
        {
            if (!player)
                return;

            m_isLornaNear = false;
            m_isPlayerMounted = player->HasAura(SPELL_RIDE_VEHICLE);
            m_hasPlayerRope = player->HasAura(SPELL_ROPE_CHANNEL);

            if (!m_lornaGUID.IsEmpty())
            {
                Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID);
                if (!lorna || lorna->GetEntry() != NPC_LORNA_CROWLEY || !lorna->IsAlive()
                    || lorna->GetMapId() != player->GetMapId() || !lorna->IsInPhase(player))
                    m_lornaGUID = ObjectGuid::Empty;
                else
                    m_isLornaNear = player->GetDistance(lorna) < 10.0f;
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 && creature->IsSummon() ? new npc_mountain_horse_36555AI(creature) : nullptr;
    }
};

// 36540
class npc_mountain_horse_36540 : public CreatureScript
{
public:
    npc_mountain_horse_36540() : CreatureScript("npc_mountain_horse_36540") { }

    enum eNpc
    {
        EVENT_CHECK_HEALTH_AND_LORNA            = 901
    };

    struct npc_mountain_horse_36540AI : public ScriptedAI
    {
        npc_mountain_horse_36540AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_lornaGUID;
        float m_dist;
        float m_angle;
        float m_size;
        Position m_oldPosition;
        bool m_lornaIsNear;
        bool m_creditGiven;

        void Reset() override
        {
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
            m_lornaGUID = ObjectGuid::Empty;
            m_lornaIsNear = false;
            m_creditGiven = false;
        }

        bool IsAtLorna(Player* player) const
        {
            Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID);
            return player && player->GetMapId() == 654 && me->GetMapId() == 654
                && me->IsInPhase(player) && lorna && lorna->GetEntry() == NPC_LORNA_CROWLEY
                && lorna->IsAlive() && lorna->GetMapId() == player->GetMapId()
                && lorna->IsInPhase(player) && player->GetDistance(lorna) < 7.0f;
        }

        void PassengerBoarded(Unit* passenger, int8 /*seatId*/, bool apply) override
        {
            Player* player = passenger ? passenger->ToPlayer() : nullptr;
            if (!player)
                return;

            if (apply)
            {
                if (!player->IsAlive() || me->GetMapId() != 654
                    || player->GetMapId() != me->GetMapId() || !me->IsInPhase(player)
                    || player->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE
                    || (!m_playerGUID.IsEmpty() && m_playerGUID != player->GetGUID()) || m_creditGiven)
                {
                    player->ExitVehicle();
                    return;
                }

                m_playerGUID = player->GetGUID();
                m_lornaIsNear = false;
                me->SetMaxHealth(250);
                m_events.RescheduleEvent(EVENT_CHECK_HEALTH_AND_LORNA, 1s);
            }
            else if (m_playerGUID == player->GetGUID())
            {
                m_events.Reset();
                if (!m_creditGiven && IsAtLorna(player) && player->IsAlive()
                    && player->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) == QUEST_STATUS_INCOMPLETE)
                {
                    m_creditGiven = true;
                    player->KilledMonsterCredit(36560);
                    me->DespawnOrUnsummon(1s);
                }
                m_playerGUID = ObjectGuid::Empty;
                m_lornaIsNear = false;
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_HEALTH_AND_LORNA:
                    {
                        if (m_playerGUID.IsEmpty() || m_creditGiven)
                            return;

                        Player* owner = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                        if (!owner || !owner->IsAlive() || owner->GetMapId() != me->GetMapId()
                            || !me->IsInPhase(owner)
                            || owner->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE)
                        {
                            if (owner)
                                owner->ExitVehicle();
                            m_playerGUID = ObjectGuid::Empty;
                            m_lornaIsNear = false;
                            m_events.Reset();
                            return;
                        }

                        m_lornaIsNear = false;
                        me->SetHealth(me->GetMaxHealth());

                        if (!m_lornaGUID.IsEmpty())
                        {
                            Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID);
                            if (!lorna || !lorna->IsAlive() || lorna->GetEntry() != NPC_LORNA_CROWLEY
                                || !lorna->IsInPhase(owner))
                                m_lornaGUID = ObjectGuid::Empty;
                        }
                        if (!m_lornaGUID)
                            if (Creature* lorna = me->FindNearestCreature(NPC_LORNA_CROWLEY, 100.0f))
                                m_lornaGUID = lorna->GetGUID();

                        m_lornaIsNear = IsAtLorna(owner);
                        if (m_lornaIsNear)
                            owner->ExitVehicle();

                        if (!m_playerGUID.IsEmpty() && !m_creditGiven)
                            m_events.ScheduleEvent(EVENT_CHECK_HEALTH_AND_LORNA, 1s);
                        break;
                    }
                }
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_mountain_horse_36540AI(creature);
    }
};

// 68903
class spell_round_up_horse_68903 : public SpellScriptLoader
{
public:
    spell_round_up_horse_68903() : SpellScriptLoader("spell_round_up_horse_68903") { }

    class spell_round_up_horse_68903_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_round_up_horse_68903_SpellScript);

        bool Validate(SpellInfo const* /*spellInfo*/) override
        {
            return ValidateSpellInfo({ 68903 });
        }

        SpellCastResult CheckTarget()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Creature* horse = GetExplTargetUnit() ? GetExplTargetUnit()->ToCreature() : nullptr;
            if (!player || !player->IsAlive() || !horse || horse->GetEntry() != 36540 || !horse->IsAlive()
                || player->GetMapId() != 654 || horse->GetMapId() != player->GetMapId() || !horse->IsInPhase(player)
                || horse->GetVehicleBase()
                || player->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE)
                return SPELL_FAILED_BAD_TARGETS;
            return SPELL_CAST_OK;
        }

        void HandleEffectDummy(SpellEffIndex /*effIndex*/)
        {
            if (!GetHitUnit() || !GetCaster() || !GetHitUnit()->ToCreature() || GetHitUnit()->GetEntry() != 36540
                || !GetCaster()->ToPlayer() || GetCaster()->ToPlayer()->GetQuestStatus(QUEST_THE_HUNGRY_ETTIN) != QUEST_STATUS_INCOMPLETE)
                return;

            Player* player = GetCaster()->ToPlayer();
            Creature* horse = GetHitUnit()->ToCreature();
            if (!player->IsAlive() || !horse->IsAlive() || player->GetMapId() != 654
                || horse->GetMapId() != player->GetMapId() || !horse->IsInPhase(player) || horse->GetVehicleBase())
                return;
            horse->DespawnOrUnsummon();
        }

        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(spell_round_up_horse_68903_SpellScript::CheckTarget);
            OnEffectHitTarget += SpellEffectFn(spell_round_up_horse_68903_SpellScript::HandleEffectDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_round_up_horse_68903_SpellScript();
    }
};

// 36452
class npc_gwen_armstead_36452 : public CreatureScript
{
public:
    npc_gwen_armstead_36452() : CreatureScript("npc_gwen_armstead_36452") { }

    bool OnQuestAccept(Player* player, Creature* /*creature*/, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_TO_GREYMANE_MANOR)
        {
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_07);
            player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08, player);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_10);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_12);
            player->CastSpell(player, SPELL_FORCECAST_SUMMON_SWIFT_MOUNTAIN_HORSE);
        }
        return true;
    }
};

// 196399
class go_gate_196399 : public GameObjectScript
{
public:
    go_gate_196399() : GameObjectScript("go_gate_196399") { }

    struct go_gate_196399AI : public GameObjectAI
    {
        go_gate_196399AI(GameObject* go) : GameObjectAI(go) { }

        EventMap m_events;
        std::list<ObjectGuid> cList;
        bool m_isUsed;

        void Reset() override
        {
            m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
            m_isUsed = false;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_PLAYER_NEAR:
                    {
                        cList.clear();
                        std::list<Creature*> c1;
                        go->GetCreatureListWithEntryInGrid(c1, NPC_SWIFT_MOUNTAIN_HORSE, 20.0f);

                        for (auto horse : c1)
                            if (Unit* p1 = horse->GetOwner())
                                if (Player* player = p1->ToPlayer())
                                    if (player->GetQuestStatus(QUEST_TO_GREYMANE_MANOR) == QUEST_STATUS_INCOMPLETE
                                        || player->GetQuestStatus(QUEST_TO_GREYMANE_MANOR) == QUEST_STATUS_COMPLETE)
                                        cList.push_back(horse->GetGUID());

                        m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
                        break;
                    }
                    case EVENT_COOLDOWN_00:
                    {
                        m_isUsed = false;
                        cList.clear();
                        go->ResetDoorOrButton();
                        break;
                    }
                }
            }

            if (!m_isUsed)
                for (auto guid : cList)
                    if (Creature* horse = ObjectAccessor::GetCreature(*go, guid))
                        if (horse->GetDistance(go) < 10.0f)
                        {
                            go->UseDoorOrButton(5000);
                            m_isUsed = true;
                            m_events.ScheduleEvent(EVENT_COOLDOWN_00, 5s);
                        }
        }
    };

    GameObjectAI* GetAI(GameObject* go) const override
    {
        return new go_gate_196399AI(go);
    }
};

// Phase 183 (16384)

// 196401
class go_gate_196401 : public GameObjectScript
{
public:
    go_gate_196401() : GameObjectScript("go_gate_196401") { }

    struct go_gate_196401AI : public GameObjectAI
    {
        go_gate_196401AI(GameObject* go) : GameObjectAI(go) { }

        EventMap m_events;
        std::list<ObjectGuid> cList;
        bool m_isUsed;

        void Reset() override
        {
            m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
            m_isUsed = false;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_PLAYER_NEAR:
                    {
                        cList.clear();
                        std::list<Creature*> c1 = FindHorseNear();

                        for (auto mount : c1)
                            if (Player* player = GetPlayer(mount))
                                if (player->GetQuestStatus(QUEST_TO_GREYMANE_MANOR) == QUEST_STATUS_INCOMPLETE
                                    || player->GetQuestStatus(QUEST_TO_GREYMANE_MANOR) == QUEST_STATUS_COMPLETE
                                    || player->GetQuestStatus(QUEST_EXODUS) == QUEST_STATUS_COMPLETE)
                                    cList.push_back(mount->GetGUID());

                        m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
                        break;
                    }
                    case EVENT_COOLDOWN_00:
                    {
                        m_isUsed = false;
                        go->ResetDoorOrButton();
                        break;
                    }
                }
            }

            if (!m_isUsed)
                for (auto guid : cList)
                    if (Creature* horse = ObjectAccessor::GetCreature(*go, guid))
                        if (horse->GetDistance(go) < 14.0f)
                        {
                            go->UseDoorOrButton(5000);
                            m_isUsed = true;
                            m_events.ScheduleEvent(EVENT_COOLDOWN_00, 6s);
                        }
        }

        std::list<Creature*> FindHorseNear()
        {
            std::list<Creature*> cList;
            GetCreatureListWithEntryInGrid(cList, go, NPC_SWIFT_MOUNTAIN_HORSE, 20.0f);
            GetCreatureListWithEntryInGrid(cList, go, NPC_HARNESS_43336, 20.0f);
            return cList;
        }

        Player* GetPlayer(Unit* mount)
        {
            if (Unit* unit = mount->GetCharmerOrOwner())
                if (Player* player = unit->ToPlayer())
                return player;
            if (Player* player = ObjectAccessor::GetPlayer(*go, mount->GetAI()->GetGUID(PLAYER_GUID)))
                return player;

            return nullptr;
        }
    };

    GameObjectAI* GetAI(GameObject* go) const override
    {
        return new go_gate_196401AI(go);
    }
};

// 36741
class npc_swift_mountain_horse_36741 : public CreatureScript
{
public:
    npc_swift_mountain_horse_36741() : CreatureScript("npc_swift_mountain_horse_36741") { }

    enum eNpc
    {
        WAYPOINT_ID                             = 3674101
    };

    struct npc_swift_mountain_horse_36741AI : public ScriptedAI
    {
        npc_swift_mountain_horse_36741AI(Creature* creature) : ScriptedAI(creature), m_playerGUID(ObjectGuid::Empty) { }

        ObjectGuid m_playerGUID;
        uint32 m_lifetime = 0;
        bool m_boarded = false;
        bool m_arrived = false;

        void Reset() override
        {
            me->SetReactState(REACT_PASSIVE);
        }

        static bool HasActiveQuest(Player* player)
        {
            if (!player || !player->IsAlive() || player->GetMapId() != 654)
                return false;
            QuestStatus status = player->GetQuestStatus(QUEST_TO_GREYMANE_MANOR);
            //14465 has no objectives and may be COMPLETE immediately on acceptance.
            return status == QUEST_STATUS_INCOMPLETE || status == QUEST_STATUS_COMPLETE;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!HasActiveQuest(player))
            {
                me->DespawnOrUnsummon();
                return;
            }
            m_playerGUID = player->GetGUID();
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type != WAYPOINT_MOTION_TYPE || id != 28 || !m_boarded || m_arrived)
                return;
            // The audited28-point route ends here, not at the old point11.
            m_arrived = true;
            if (Vehicle* vehicle = me->GetVehicleKit())
                vehicle->RemoveAllPassengers();
            me->DespawnOrUnsummon(1s);
        }

        void PassengerBoarded(Unit* passenger, int8 seatId, bool apply) override
        {
            Player* player = passenger ? passenger->ToPlayer() : nullptr;
            if (apply)
            {
                if (m_boarded && player && seatId == 0 && player->GetGUID() == m_playerGUID)
                    return;
                if (!HasActiveQuest(player) || seatId != 0 || player->GetGUID() != m_playerGUID || m_boarded)
                {
                    if (passenger)
                        passenger->ExitVehicle();
                    return;
                }
                m_boarded = true;
                player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08, player);
                player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09, player);
                me->CastSpell(player, SPELL_FORCECAST_UPDATE_ZONE_AURAS, true);
                me->GetMotionMaster()->MovePath(WAYPOINT_ID, false);
            }
            else if (player && player->GetGUID() == m_playerGUID)
            {
                m_boarded = false;
                me->DespawnOrUnsummon(1s);
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_lifetime += diff;
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            if (m_lifetime >= 360000 || !HasActiveQuest(player)
                || (m_boarded && player->GetVehicleBase() != me))
                me->DespawnOrUnsummon();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_swift_mountain_horse_36741AI(creature);
    }
};

// 36606
class npc_queen_mia_greymane_36606 : public CreatureScript
{
public:
    npc_queen_mia_greymane_36606() : CreatureScript("npc_queen_mia_greymane_36606") { }

    bool OnQuestAccept(Player* player, Creature* /*creature*/, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_THE_KINGS_OBSERVATORY)
        {
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_06);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_07);
            player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08, player);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_10);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11);
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_12);
        }

        return true;
    }

    bool OnQuestReward(Player* player, Creature* /*creature*/, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == QUEST_TO_GREYMANE_MANOR)
            player->CastSpell(player, SPELL_UPDATE_BIND_TO_GREYMANE_MANOR);

        return false;
    }
};

// 36743
class npc_king_genn_greymane_36743 : public CreatureScript
{
public:
    npc_king_genn_greymane_36743() : CreatureScript("npc_king_genn_greymane_36743") { }

    bool OnQuestReward(Player* player, Creature* creature, Quest const* quest, uint32 /*opt*/) override
    {
        switch (quest->GetQuestId())
        {
            case QUEST_THE_KINGS_OBSERVATORY:
            {
                creature->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                creature->AI()->DoAction(EVENT_CHANGE_PHASE);
                break;
            }
            case QUEST_ALAS_GILNEAS:
            {
                player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08);
                player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11, player);
                creature->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                creature->AI()->DoAction(EVENT_START_VIDEO);
                break;
            }
        }

        return false;
    }

    struct npc_king_genn_greymane_36743AI : public ScriptedAI
    {
        npc_king_genn_greymane_36743AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;

        void Reset() override
        {
            m_playerGUID = ObjectGuid::Empty;
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            switch (id)
            {
                case PLAYER_GUID:
                {
                    m_playerGUID = guid;
                    break;
                }
            }
        }

        void DoAction(int32 param) override
        {
            switch (param)
            {
                case EVENT_CHANGE_PHASE:
                {
                    m_events.RescheduleEvent(EVENT_CHANGE_PHASE, 4s);
                    break;
                }
                case EVENT_START_VIDEO:
                {
                    m_events.RescheduleEvent(EVENT_START_VIDEO, 1s);
                    break;
                }
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_VIDEO:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            player->SendCinematicStart(167);
                            player->PlayDirectSound(23539);
                        }
                        break;
                    }
                    case 1:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_08);
                            player->AddAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11, player);
                        }
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_king_genn_greymane_36743AI(creature);
    }
};

// after cataclysm earthquake : phase 186 (131072), WorldMap 679 and TerrainSwap 656
// the ride has additional phase 194

// 44928: the parked carriage is an accessory of the persistent harness.
class npc_stagecoach_carriage_44928 : public CreatureScript
{
public:
    npc_stagecoach_carriage_44928() : CreatureScript("npc_stagecoach_carriage_44928") { }

    static void BeginJourney(Player* player, Creature* creature)
    {
        if (player->GetMapId() != 654 || !player->IsAlive()
            || player->GetQuestStatus(QUEST_EXODUS) != QUEST_STATUS_COMPLETE
            || player->GetVehicleBase() || player->GetDistance(creature) > 5.0f
            || player->GetSummonedCreatureByEntry(NPC_HARNESS_43336))
            return;

        player->CastSpell(player, SPELL_PHASE_QUEST_ZONE_SPECIFIC_19, true);
        if (!player->SummonCreature(NPC_HARNESS_43336, creature->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, 450000, 0, true))
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
    }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        BeginJourney(player, creature);
        return true;
    }

    struct npc_parked_carriageAI : public ScriptedAI
    {
        npc_parked_carriageAI(Creature* creature) : ScriptedAI(creature) { }
        void PassengerBoarded(Unit* passenger, int8, bool apply) override
        {
            // Vehicle::Install sets SPELLCLICK for the free player seat.
            // Native right-click may therefore board the parked vehicle
            // instead of sending gossip. Exit it first, then start the same
            // private journey, after its pending join has completed.
            if (apply)
                if (Player* player = passenger->ToPlayer())
                {
                    player->ExitVehicle();
                    BeginJourney(player, me);
                }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 ? new npc_parked_carriageAI(creature) : nullptr;
    }
};

// 43336: one bounded, owner-only journey over the captured 33-point route.
class npc_harness_43336 : public CreatureScript
{
public:
    npc_harness_43336() : CreatureScript("npc_harness_43336") { }

    struct npc_harness_43336AI : public ScriptedAI
    {
        npc_harness_43336AI(Creature* creature) : ScriptedAI(creature), m_summons(me) { }

        EventMap m_events;
        SummonList m_summons;
        ObjectGuid m_playerGUID;
        ObjectGuid m_carriageGUID;
        uint32 m_lifetime = 0;
        bool m_started = false;
        bool m_arrived = false;
        bool m_finished = false;
        bool m_boardRequested = false;

        void Reset() override
        {
            m_events.Reset();
            me->setActive(true);
            me->SetReactState(REACT_PASSIVE);
            if (!m_playerGUID.IsEmpty())
                Cleanup();
        }

        void Cleanup()
        {
            if (m_finished)
                return;
            m_finished = true; // ExitVehicle can re-enter PassengerBoarded.
            m_events.Reset();
            if (Player* player = ObjectAccessor::FindPlayer(m_playerGUID))
            {
                if (Creature* car = ObjectAccessor::GetCreature(*me, m_carriageGUID))
                    if (player->GetVehicleBase() == car)
                        player->ExitVehicle();
                player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
            }
            if (Creature* car = ObjectAccessor::GetCreature(*me, m_carriageGUID))
                car->AI()->DoAction(EVENT_DESPAWN_PART_00);
            m_summons.DespawnAll();
            me->DespawnOrUnsummon(1s);
        }

        void TryBoard()
        {
            if (m_boardRequested || m_finished || m_playerGUID.IsEmpty())
                return;
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            Creature* car = ObjectAccessor::GetCreature(*me, m_carriageGUID);
            if (!player || !player->IsAlive() || player->GetMapId() != me->GetMapId()
                || !me->InSamePhase(player->GetPhaseShift())
                || player->GetQuestStatus(QUEST_EXODUS) != QUEST_STATUS_COMPLETE
                || !player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19)
                || (car && (!car->IsAlive() || car->GetMapId() != me->GetMapId()
                    || !me->InSamePhase(car->GetPhaseShift()))))
            {
                Cleanup();
                return;
            }
            // The native vehicle installer can create the accessory before or
            // after IsSummonedBy. Wait until its own boarding has completed.
            if (!player || !car || car->GetVehicleBase() != me || !car->GetVehicleKit())
                return;
            m_boardRequested = true;
            car->AI()->SetGUID(m_playerGUID, PLAYER_GUID);
            car->AI()->DoAction(EVENT_ENTER_VEHICLE);
        }

        void DoAction(int32 action) override
        {
            if (action == EVENT_DESPAWN_PART_00)
                Cleanup();
            else if (action == EVENT_START_MOVEMENT && !m_started && !m_finished)
            {
                m_started = true;
                m_events.RescheduleEvent(EVENT_START_MOVEMENT, 3s);
            }
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            return id == PLAYER_GUID ? m_playerGUID : ObjectGuid::Empty;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (m_finished || !m_playerGUID.IsEmpty())
                return;
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || me->GetMapId() != 654
                || player->GetMapId() != me->GetMapId() || !me->InSamePhase(player->GetPhaseShift())
                || player->GetQuestStatus(QUEST_EXODUS) != QUEST_STATUS_COMPLETE
                || !player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19))
            {
                if (player)
                    player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
                Cleanup();
                return;
            }
            m_playerGUID = player->GetGUID();
            TryBoard();
        }

        void JustSummoned(Creature* summon) override
        {
            if (m_finished)
            {
                summon->DespawnOrUnsummon();
                return;
            }
            if (summon->GetEntry() == NPC_CARRIAGE_43337 && !m_carriageGUID.IsEmpty()
                && m_carriageGUID != summon->GetGUID())
            {
                summon->DespawnOrUnsummon();
                return;
            }
            m_summons.Summon(summon);
            if (summon->GetEntry() == NPC_CARRIAGE_43337)
            {
                m_carriageGUID = summon->GetGUID();
                summon->AI()->SetGUID(me->GetGUID(), NPC_HARNESS_43336);
                TryBoard();
            }
        }

        void SummonedCreatureDespawn(Creature* summon) override
        {
            m_summons.Despawn(summon);
            if (summon->GetGUID() == m_carriageGUID && !m_finished)
                Cleanup();
        }

        void PassengerBoarded(Unit* passenger, int8, bool apply) override
        {
            // Harness seats are reserved for horses and the carriage. Before
            // asynchronous accessories finish joining, native SPELLCLICK may
            // briefly expose them; never let a player replace an accessory.
            if (apply && passenger->ToPlayer())
                passenger->ExitVehicle();
        }

        void JustDied(Unit*) override { Cleanup(); }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type != WAYPOINT_MOTION_TYPE || !m_started || m_finished)
                return;
            if (Creature* car = ObjectAccessor::GetCreature(*me, m_carriageGUID))
            {
                if (id == 24)
                    car->AI()->DoAction(EVENT_SAY_ATTACK);
                else if (id == 30 && !m_arrived)
                {
                    m_arrived = true;
                    car->AI()->DoAction(EVENT_EXIT_VEHICLE);
                    if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
                }
            }
            if (id == 33)
                Cleanup();
        }

        void UpdateAI(uint32 diff) override
        {
            if (m_finished)
                return;
            m_lifetime += diff;
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || m_lifetime >= 450000
                || (!m_arrived && (player->GetQuestStatus(QUEST_EXODUS) != QUEST_STATUS_COMPLETE
                    || !me->InSamePhase(player->GetPhaseShift())
                    || !player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19))))
            {
                Cleanup();
                return;
            }
            TryBoard();
            if (!m_started && m_lifetime >= 10000)
            {
                Cleanup();
                return;
            }
            // After the planned stop the owner can reward the quest while the
            // carriage drives away. An earlier dismount cancels the journey.
            if (m_started && !m_arrived)
            {
                Creature* car = ObjectAccessor::GetCreature(*me, m_carriageGUID);
                if (!car || player->GetVehicleBase() != car)
                {
                    Cleanup();
                    return;
                }
            }
            m_events.Update(diff);
            while (uint32 eventId = m_events.ExecuteEvent())
                if (eventId == EVENT_START_MOVEMENT)
                    me->GetMotionMaster()->MovePath(4492801, false);
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_harness_43336AI(creature);
    }
};

// 43337: carriage seat1 belongs exclusively to the journey's player.
class npc_stagecoach_carriage_43337 : public CreatureScript
{
public:
    npc_stagecoach_carriage_43337() : CreatureScript("npc_stagecoach_carriage_43337") { }

    struct npc_stagecoach_carriage_43337AI : public ScriptedAI
    {
        npc_stagecoach_carriage_43337AI(Creature* creature) : ScriptedAI(creature), m_summons(me) { }
        SummonList m_summons;
        ObjectGuid m_playerGUID;
        ObjectGuid m_lornaGUID;
        ObjectGuid m_harnessGUID;
        bool m_boarded = false;
        bool m_exiting = false;
        bool m_finished = false;

        void Reset() override
        {
            me->setActive(true);
            me->SetReactState(REACT_PASSIVE);
            if (!m_playerGUID.IsEmpty())
                CancelJourney();
        }

        void CancelJourney()
        {
            if (Creature* harness = ObjectAccessor::GetCreature(*me, m_harnessGUID))
                harness->AI()->DoAction(EVENT_DESPAWN_PART_00);
            else
                DoAction(EVENT_DESPAWN_PART_00);
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (m_finished || !m_harnessGUID.IsEmpty())
                return;
            if (Creature* harness = summoner ? summoner->ToCreature() : nullptr)
                if (harness->GetEntry() == NPC_HARNESS_43336 && harness->IsAlive()
                    && harness->GetMapId() == me->GetMapId() && me->InSamePhase(harness->GetPhaseShift()))
                    m_harnessGUID = harness->GetGUID();
        }

        void JustSummoned(Creature* summon) override
        {
            if (m_finished)
            {
                summon->DespawnOrUnsummon();
                return;
            }
            m_summons.Summon(summon);
            if (summon->GetEntry() == NPC_LORNA_CRAWLEY)
                m_lornaGUID = summon->GetGUID();
        }

        void SummonedCreatureDespawn(Creature* summon) override { m_summons.Despawn(summon); }
        void JustDied(Unit*) override { CancelJourney(); }

        void PassengerBoarded(Unit* passenger, int8 seatId, bool apply) override
        {
            Player* player = passenger ? passenger->ToPlayer() : nullptr;
            if (!player)
                return;
            if (apply)
            {
                if (m_finished || player->GetGUID() != m_playerGUID || seatId != 1
                    || !player->IsAlive() || player->GetMapId() != me->GetMapId()
                    || !me->InSamePhase(player->GetPhaseShift())
                    || player->GetQuestStatus(QUEST_EXODUS) != QUEST_STATUS_COMPLETE)
                {
                    player->ExitVehicle();
                    return;
                }
                if (!m_boarded)
                {
                    m_boarded = true;
                    if (Creature* harness = ObjectAccessor::GetCreature(*me, m_harnessGUID))
                        harness->AI()->DoAction(EVENT_START_MOVEMENT);
                }
            }
            else if (player->GetGUID() == m_playerGUID && m_boarded && !m_exiting && !m_finished)
                CancelJourney();
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            if (m_finished || guid.IsEmpty())
                return;
            if (id == PLAYER_GUID && (m_playerGUID.IsEmpty() || m_playerGUID == guid))
                m_playerGUID = guid;
            else if (id == NPC_HARNESS_43336 && (m_harnessGUID.IsEmpty() || m_harnessGUID == guid))
                m_harnessGUID = guid;
        }

        void DoAction(int32 action) override
        {
            if (action == EVENT_DESPAWN_PART_00 && !m_finished)
            {
                m_finished = true;
                m_exiting = true;
                if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                    if (player->GetVehicleBase() == me)
                        player->ExitVehicle();
                m_summons.DespawnAll();
                me->DespawnOrUnsummon(1s);
            }
            else if (action == EVENT_SAY_ATTACK)
            {
                if (Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID))
                    lorna->AI()->Talk(0);
            }
            else if (action == EVENT_EXIT_VEHICLE)
            {
                m_exiting = true;
                if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                    if (player->GetVehicleBase() == me)
                        player->ExitVehicle();
            }
            else if (action == EVENT_ENTER_VEHICLE && !m_finished && !m_boarded)
            {
                if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                    if (me->GetVehicleKit() && me->GetVehicleKit()->HasEmptySeat(1)
                        && !player->GetVehicleBase() && player->IsAlive()
                        && player->GetMapId() == me->GetMapId() && me->InSamePhase(player->GetPhaseShift())
                        && player->GetQuestStatus(QUEST_EXODUS) == QUEST_STATUS_COMPLETE)
                        // Explicit seat1, preserving the native ride spell.
                        player->CastCustomSpell(SPELL_RIDE_VEHICLE_72764, SPELLVALUE_BASE_POINT0, 2, me, true);
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_stagecoach_carriage_43337AI(creature);
    }
};

class player_gilneas_carriage_recovery : public PlayerScript
{
public:
    player_gilneas_carriage_recovery() : PlayerScript("player_gilneas_carriage_recovery") { }
    void OnLogout(Player* player) override
    {
        if (player->GetMapId() != 654)
            return;
        if (Creature* harness = player->GetSummonedCreatureByEntry(NPC_HARNESS_43336))
            harness->AI()->DoAction(EVENT_DESPAWN_PART_00);
        player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
    }

    void OnLogin(Player* player, bool) override
    {
        // A temporary vehicle cannot survive a server restart. Remove only
        // its journey aura; normal story phases and quest state are untouched.
        if (player->GetMapId() == 654 && !player->GetVehicleBase()
            && player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19)
            && !player->GetSummonedCreatureByEntry(NPC_HARNESS_43336))
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
    }
};

// 196412
class go_kings_gate_196412 : public GameObjectScript
{
public:
    go_kings_gate_196412() : GameObjectScript("go_kings_gate_196412") { }

    struct go_kings_gate_196412AI : public GameObjectAI
    {
        go_kings_gate_196412AI(GameObject* go) : GameObjectAI(go) { }

        EventMap m_events;
        std::list<ObjectGuid> cList;
        bool m_isUsed;

        void Reset() override
        {
            m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
            m_isUsed = false;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_PLAYER_NEAR:
                    {
                        cList.clear();
                        std::list<Creature*> c1 = FindHorseNear();
                        for (auto mount : c1)
                            if (Player* player = GetPlayer(mount))
                                if (player->GetQuestStatus(QUEST_EXODUS) == QUEST_STATUS_COMPLETE)
                                    cList.push_back(mount->GetGUID());

                        m_events.RescheduleEvent(EVENT_CHECK_PLAYER_NEAR, 1s);
                        break;
                    }
                    case EVENT_COOLDOWN_00:
                    {
                        m_isUsed = false;
                        go->ResetDoorOrButton();
                        break;
                    }
                }
            }

            if (!m_isUsed)
                for (auto guid : cList)
                    if (Creature* horse = ObjectAccessor::GetCreature(*go, guid))
                        if (horse->GetDistance(go) < 14.0f)
                        {
                            go->UseDoorOrButton(5000);
                            m_isUsed = true;
                            m_events.ScheduleEvent(EVENT_COOLDOWN_00, 6s);
                        }
        }

        std::list<Creature*> FindHorseNear()
        {
            std::list<Creature*> cList;
            GetCreatureListWithEntryInGrid(cList, go, NPC_HARNESS_43336, 20.0f);
            return cList;
        }

        Player* GetPlayer(Unit* mount)
        {
            if (Unit* unit = mount->GetCharmerOrOwner())
                if (Player* player = unit->ToPlayer())
                    return player;
            if (Player* player = ObjectAccessor::GetPlayer(*go, mount->GetAI()->GetGUID(PLAYER_GUID)))
                return player;

            return nullptr;
        }
    };

    GameObjectAI* GetAI(GameObject* go) const override
    {
        return new go_kings_gate_196412AI(go);
    }
};

// 38762
class npc_ogre_ambusher_38762 : public CreatureScript
{
public:
    npc_ogre_ambusher_38762() : CreatureScript("npc_ogre_ambusher_38762") { }

    struct npc_ogre_ambusher_38762AI : public ScriptedAI
    {
        npc_ogre_ambusher_38762AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        bool m_cast_cooldown;

        void Reset() override
        {
            m_cast_cooldown = false;
            me->SetReactState(REACT_PASSIVE);
        }

        void MoveInLineOfSight(Unit* who) override
        {
            if (!m_cast_cooldown)
                if (who->ToPlayer() || who->getFaction() == 2203 || who->getFaction() == 2163)
                    if (me->GetDistance(who) < 60.0f)
                    {
                        me->SetFacingToObject(who);
                        if (urand(0, 100) < 30)
                        {
                            me->CastSpell(who, SPELL_THROW_BOULDER, true);
                            m_cast_cooldown = true;
                            m_events.ScheduleEvent(EVENT_COOLDOWN_00, 2s + 500ms, 3s + 500ms);
                        }
                    }
        }

        void AttackStart(Unit* who) override
        {
            DoStartNoMovement(who);
        }

        void EnterCombat(Unit* /*victim*/) override { }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_COOLDOWN_00:
                    {
                        m_cast_cooldown = false;
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_ogre_ambusher_38762AI(creature);
    }
};

// 37065
class npc_prince_liam_greymane_37065 : public CreatureScript
{
public:
    npc_prince_liam_greymane_37065() : CreatureScript("npc_prince_liam_greymane_37065") { }

    enum eNpc
    {
        MOVEMENT_KOROTH                         = 2515531
    };

    bool OnQuestReward(Player* player, Creature* creature, Quest const* quest, uint32 /*opt*/) override
    {
        switch (quest->GetQuestId())
        {
            case QUEST_EXODUS:
            {
                player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_19);
                break;
            }
            case QUEST_INTRODUCTIONS_ARE_IN_ORDER:
            {
                if (Creature* koroth = creature->FindNearestCreature(NPC_KOROTH, 50.0f))
                {
                    player->AddAura(SPELL_GENERIC_QUEST_INVISIBLE_DETECTION_10, player);
                    koroth->SetSpeed(MOVE_RUN, 1.3f);
                    koroth->SetReactState(REACT_AGGRESSIVE);
                    koroth->GetMotionMaster()->MovePath(MOVEMENT_KOROTH, false);
                    creature->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                    creature->AI()->SetGUID(koroth->GetGUID(), koroth->GetEntry());
                    creature->AI()->DoAction(1);
                }
                break;
            }
        }

        return false;
    }

    bool OnQuestAccept(Player* player, Creature* /*creature*/, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_STORMGLEN)
            player->RemoveAura(SPELL_GENERIC_QUEST_INVISIBLE_DETECTION_10);
            return true;
    }

    struct npc_prince_liam_greymane_37065AI : public ScriptedAI
    {
        npc_prince_liam_greymane_37065AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_korothGUID;

        void Reset() override
        {
            m_korothGUID = ObjectGuid::Empty;
            m_playerGUID = ObjectGuid::Empty;
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            switch (id)
            {
                case PLAYER_GUID:
                    m_playerGUID = guid;
                    break;
                case NPC_KOROTH:
                    m_korothGUID = guid;
                    break;
            }
        }

        void DoAction(int32 param) override
        {
            switch (param)
            {
                case 1:
                    m_events.ScheduleEvent(EVENT_TALK_PART_00, 2s);
                    break;
            }
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type == POINT_MOTION_TYPE)
                switch (id)
                {
                    case 1020:
                    {
                        m_events.ScheduleEvent(EVENT_TALK_PART_01, 1s);
                        break;
                    }
                }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_TALK_PART_00:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* koroth = ObjectAccessor::GetCreature(*me, m_korothGUID))
                            {
                                koroth->AI()->Talk(0, player);
                                Talk(0, player);
                            }

                        me->GetMotionMaster()->MovePoint(1020, -2192.868f, 1808.405f, 12.55306f);

                        break;
                    }
                    case EVENT_TALK_PART_01:
                    {
                        me->CastSpell(me, 70511, true);
                        m_events.ScheduleEvent(EVENT_TALK_PART_02, 1s);
                        break;
                    }
                    case EVENT_TALK_PART_02:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(1, player);

                        m_events.ScheduleEvent(EVENT_TALK_PART_03, 3s);
                        break;
                    }
                    case EVENT_TALK_PART_03:
                    {
                        me->GetMotionMaster()->MoveTargetedHome();
                        m_events.ScheduleEvent(EVENT_TALK_PART_04, 10s);
                        break;
                    }
                    case EVENT_TALK_PART_04:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* asther = me->FindNearestCreature(37806, 50.0f))
                                asther->AI()->Talk(0, player);

                        m_events.ScheduleEvent(EVENT_TALK_PART_05, 5s);
                        break;
                    }
                    case EVENT_TALK_PART_05:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            player->RemoveAura(SPELL_GENERIC_QUEST_INVISIBLE_DETECTION_10);
                        if (Creature* koroth = ObjectAccessor::GetCreature(*me, m_korothGUID))
                            koroth->GetMotionMaster()->MoveTargetedHome();
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_prince_liam_greymane_37065AI(creature);
    }
};

// 37067
class npc_crash_survivor_37067 : public CreatureScript
{
public:
    npc_crash_survivor_37067() : CreatureScript("npc_crash_survivor_37067") { }

    struct npc_crash_survivor_37067AI : public ScriptedAI
    {
        npc_crash_survivor_37067AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;

        void Reset() override
        {
            me->SetReactState(REACT_DEFENSIVE);
            m_events.RescheduleEvent(EVENT_CHECK_FOR_CREATURE, 1s);
        }

        void AttackStart(Unit* target) override
        {
            AttackStartNoMove(target);
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            if (attacker->GetEntry() == 37078)
                damage = 0;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_FOR_CREATURE:
                    {
                        if (!me->IsInCombat())
                            if (Creature* croc = me->FindNearestCreature(37078, 4.0f))
                            {
                                me->HandleEmoteCommand(EMOTE_ONESHOT_NONE);
                                me->SetFacingToObject(croc);
                                // Both defensive actors need a victim; zero scripted
                                // damage must not be relied on to aggro the crocodile.
                                if (!croc->IsInCombat() && croc->IsAlive() && me->IsInPhase(croc)
                                    && me->Attack(croc, true))
                                    croc->AI()->AttackStart(me);
                            }

                        m_events.ScheduleEvent(EVENT_CHECK_FOR_CREATURE, 1s);
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_crash_survivor_37067AI(creature);
    }
};

// 37078
class npc_swamp_crocolisk_37078 : public CreatureScript
{
public:
    npc_swamp_crocolisk_37078() : CreatureScript("npc_swamp_crocolisk_37078") { }

    struct npc_swamp_crocolisk_37078AI : public ScriptedAI
    {
        npc_swamp_crocolisk_37078AI(Creature* creature) : ScriptedAI(creature) { }

        void Reset() override
        {
            me->SetReactState(REACT_DEFENSIVE);
        }

        void AttackStart(Unit* target) override
        {
            if (target->GetEntry() == 37067)
                AttackStartNoMove(target);
            else if (me->Attack(target, true))
                me->GetMotionMaster()->MoveChase(target);
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            if (attacker->GetEntry() == 37067)
                damage = 0;
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_swamp_crocolisk_37078AI(creature);
    }
};

// 201594
class go_koroths_banner_201594 : public GameObjectScript
{
public:
    go_koroths_banner_201594() : GameObjectScript("go_koroths_banner_201594") { }

    struct go_koroths_banner_201594AI : public GameObjectAI
    {
        go_koroths_banner_201594AI(GameObject* go) : GameObjectAI(go) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_korothGUID;

        void Reset() override
        {
            m_playerGUID = ObjectGuid::Empty;
            m_korothGUID = ObjectGuid::Empty;
        }

        void OnStateChanged(uint32 /*state*/, Unit* unit) override
        {
            if (unit)
                if (Creature* koroth = go->FindNearestCreature(36294, 50.0f))
                    if (Player* player = unit->ToPlayer())
                    {
                        m_playerGUID = player->GetGUID();
                        m_korothGUID = koroth->GetGUID();
                        m_events.RescheduleEvent(EVENT_TALK_PART_00, 1s);
                    }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_TALK_PART_00:
                    {
                        if (Creature* koroth = ObjectAccessor::GetCreature(*go, m_korothGUID))
                            if (Player* player = ObjectAccessor::GetPlayer(*go, m_playerGUID))
                                koroth->AI()->Talk(0, player);

                        m_events.ScheduleEvent(EVENT_TALK_PART_01, 6s);
                        break;
                    }
                    case EVENT_TALK_PART_01:
                    {
                        if (Creature* koroth = ObjectAccessor::GetCreature(*go, m_korothGUID))
                            if (Player* player = ObjectAccessor::GetPlayer(*go, m_playerGUID))
                                koroth->AI()->Talk(1, player);
                        break;
                    }
                }
            }
        }
    };

    GameObjectAI* GetAI(GameObject* go) const override
    {
        return new go_koroths_banner_201594AI(go);
    }
};

// 6687
class at_the_blackwald_6687 : public AreaTriggerScript
{
public:
    at_the_blackwald_6687() : AreaTriggerScript("at_the_blackwald_6687") { }

    bool OnTrigger(Player* player, const AreaTriggerEntry* /*at*/, bool /*enter*/) override
    {
        if (player->GetQuestStatus(QUEST_LOSING_YOUR_TAIL) == QUEST_STATUS_INCOMPLETE)
            if (!player->FindNearestCreature(NPC_DARK_SCOUT, 50.0f))
                player->CastSpell(player, SPELL_FREEZING_TRAP_EFFECT, true);

        return false;
    }
};

// 37953
class npc_dark_scout_37953 : public CreatureScript
{
public:
    npc_dark_scout_37953() : CreatureScript("npc_dark_scout_37953") { }

    enum eNpc
    {
        TALK_EASY                               = 0,
        TALK_HOW                                = 1,
        TALK_DO                                 = 2
    };

    struct npc_dark_scout_37953AI : public ScriptedAI
    {
        npc_dark_scout_37953AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;

        void Reset() override
        {
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (Player* player = summoner->ToPlayer())
            {
                m_playerGUID = player->GetGUID();
                me->GetMotionMaster()->Clear();
                me->SetFacingToObject(player);
                me->AI()->Talk(TALK_EASY);
                m_events.ScheduleEvent(EVENT_TALK_START, 5s);
                m_events.ScheduleEvent(EVENT_CHECK_PLAYER, 1s);
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_CHECK_PLAYER:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (player->GetQuestStatus(QUEST_LOSING_YOUR_TAIL) == QUEST_STATUS_INCOMPLETE)
                                if (player->GetDistance2d(me) < 30.0f)
                                {
                                    if (!me->IsInCombat())
                                        m_events.ScheduleEvent(EVENT_MELEE_ATTACK, 500ms);

                                    m_events.ScheduleEvent(EVENT_CHECK_PLAYER, 1s);
                                    break;
                                }

                        me->DespawnOrUnsummon(100ms);
                        break;
                    }
                    case EVENT_TALK_START:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(TALK_DO, player);

                        m_events.ScheduleEvent(EVENT_SHOOT, 7s + 500ms);
                        m_events.ScheduleEvent(EVENT_CHECK_AURA, 250ms);
                        break;
                    }
                    case EVENT_SHOOT:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            m_events.CancelEvent(EVENT_CHECK_AURA);
                            me->CastSpell(player, SPELL_AIMED_SHOOT);
                            me->GetMotionMaster()->Clear();
                            me->SetWalk(true);
                            me->SetSpeed(MOVE_WALK, 1.0f);
                            me->GetMotionMaster()->MoveChase(player);
                            me->Attack(player, true);
                        }
                        break;
                    }
                    case EVENT_CHECK_AURA:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (player->HasAura(SPELL_FREEZING_TRAP_EFFECT))
                            {
                                m_events.ScheduleEvent(EVENT_CHECK_AURA, 250);
                                break;
                            }

                        m_events.CancelEvent(EVENT_SHOOT);
                        Talk(TALK_HOW);
                        m_events.ScheduleEvent(EVENT_MELEE_ATTACK, 1s + 500ms);
                        break;
                    }
                    case EVENT_MELEE_ATTACK:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (!player->IsInCombat())
                                if (player->GetDistance2d(me) < 30.0f)
                                {
                                    me->GetMotionMaster()->Clear();
                                    me->SetWalk(true);
                                    me->SetSpeed(MOVE_WALK, 1.0f);
                                    me->GetMotionMaster()->MoveChase(player);
                                    me->Attack(player, true);
                                }

                        m_events.ScheduleEvent(EVENT_MELEE_ATTACK, 1s + 500ms);
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_dark_scout_37953AI(creature);
    }
};

// quest_24616
class npc_trigger_quest_24616 : public CreatureScript
{
public:
    npc_trigger_quest_24616() : CreatureScript("npc_trigger_quest_24616") { }

    struct npc_trigger_quest_24616AI : public ScriptedAI
    {
        npc_trigger_quest_24616AI(Creature* creature) : ScriptedAI(creature) { }

        void Reset() override
        {
            mui_timerAllowSummon = urand(3000, 5000);
            allowSummon = false;
            playerGUID = ObjectGuid::Empty;
        }

        void MoveInLineOfSight(Unit* who) override
        {
            if (who->GetTypeId() != TYPEID_PLAYER)
                return;

            if (who->ToPlayer()->GetQuestStatus(24616) != QUEST_STATUS_INCOMPLETE || me->FindNearestCreature(37953, 100, false) != NULL)
                return;

            if (me->IsWithinDistInMap(who, 20.0f))
            {
                allowSummon = true;
                playerGUID = who->GetGUID();
            }
        }

        void UpdateAI(uint32 diff) override
        {
            if (!allowSummon)
                return;

            if (mui_timerAllowSummon <= diff)
            {
                if (Player *player = ObjectAccessor::GetPlayer(*me, playerGUID))
                    if (me->FindNearestCreature(37953, 100) == NULL)
                        me->CastSpell(player, 70794, true);
                allowSummon = false;
                playerGUID = ObjectGuid::Empty;
                mui_timerAllowSummon = urand(3000, 5000);
            }
            else
                mui_timerAllowSummon -= diff;
        }

    private:
        uint32 mui_timerAllowSummon;
        bool allowSummon;
        ObjectGuid playerGUID;
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_trigger_quest_24616AI(creature);
    }
};

// 49944
class item_belysras_talisman_49944 : public ItemScript
{
public:
    item_belysras_talisman_49944() : ItemScript("item_belysras_talisman_49944") { }

    bool OnUse(Player* player, Item* /*item*/, SpellCastTargets const& /*targets*/, ObjectGuid /*castId*/) override
    {
        if (player->GetQuestStatus(QUEST_LOSING_YOUR_TAIL) == QUEST_STATUS_INCOMPLETE)
            if (player->HasAura(SPELL_FREEZING_TRAP_EFFECT))
                player->RemoveAura(SPELL_FREEZING_TRAP_EFFECT);

        return false;
    }
};

// 38195
class npc_tobias_mistmantle_38051 : public CreatureScript
{
public:
    npc_tobias_mistmantle_38051() : CreatureScript("npc_tobias_mistmantle_38051") { }

    struct npc_tobias_mistmantle_38051AI : public ScriptedAI
    {
        npc_tobias_mistmantle_38051AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_dariusGUID;

        void Reset() override
        {
            m_events.Reset();
            m_dariusGUID = ObjectGuid::Empty;

            if (Creature* darius = me->FindNearestCreature(NPC_LORD_DARIUS_CROWLEY, 50.0f))
                m_dariusGUID = darius->GetGUID();

            m_events.ScheduleEvent(EVENT_START_ANIM, 250ms);
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type == POINT_MOTION_TYPE)
            {
                if (id == 1001)
                {
                    me->HandleEmoteCommand(EMOTE_ONESHOT_KNEEL);
                    m_events.ScheduleEvent(EVENT_START_TALK, 250ms);
                }
                else if (id == 1002)
                    me->DespawnOrUnsummon();
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_ANIM:
                    {
                        me->GetMotionMaster()->MovePoint(1001, -2068.833252f, 1277.579468f, -85.201454f, true);
                        break;
                    }
                    case EVENT_START_TALK:
                    {
                        Talk(0);

                        if (Creature* darius = ObjectAccessor::GetCreature(*me, m_dariusGUID))
                            darius->SetFacingToObject(me);

                        m_events.ScheduleEvent(EVENT_START_TALK + 1, 5s);
                        break;
                    }
                    case EVENT_START_TALK + 1:
                    {
                        if (Creature* darius = ObjectAccessor::GetCreature(*me, m_dariusGUID))
                            darius->AI()->Talk(1);

                        m_events.ScheduleEvent(EVENT_START_TALK + 2, 5s);
                        break;
                    }
                    case EVENT_START_TALK + 2:
                    {
                        Talk(1);
                        m_events.ScheduleEvent(EVENT_START_TALK + 3, 5s);
                        break;
                    }
                    case EVENT_START_TALK + 3:
                    {
                        me->HandleEmoteCommand(EMOTE_STATE_NONE);
                        me->GetMotionMaster()->MovePoint(1002, -2069.574951f, 1305.952393f, -83.195412f, true);
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_tobias_mistmantle_38051AI(creature);
    }
};

// Source: audited2018_10_12_00_world_duskhaven_part3.sql, tracker positions105080-105087.
static Position const TaldorenTrackerPositions[] =
{
    { -2133.54f, 1615.31f, -43.5836f, 0.752862f },
    { -2109.32f, 1616.10f, -42.6374f, 2.402210f },
    { -2112.86f, 1611.64f, -42.9334f, 2.331520f },
    { -2119.90f, 1610.75f, -43.5323f, 3.140480f },
    { -2129.60f, 1609.58f, -43.5793f, 4.593470f },
    { -2141.55f, 1618.05f, -43.5221f, 1.059170f },
    { -2145.55f, 1630.15f, -42.7947f, 0.0695731f },
    { -2131.07f, 1612.27f, -43.5848f, 0.796060f }
};

class npc_gilneas_taldoren_tracker : public CreatureScript
{
public:
    npc_gilneas_taldoren_tracker() : CreatureScript("npc_gilneas_taldoren_tracker") { }
    struct ai : public ScriptedAI
    {
        ai(Creature* creature) : ScriptedAI(creature) { }
        ObjectGuid m_ownerGUID = ObjectGuid::Empty;
        EventMap m_events;
        void Reset() override
        {
            m_events.Reset();
            // Evade resets combat events, but must retain the personal summon owner.
            if (!m_ownerGUID.IsEmpty())
            {
                m_events.ScheduleEvent(1, 1s);
                m_events.ScheduleEvent(2, 3s);
            }
            me->SetReactState(REACT_DEFENSIVE);
        }
        void IsSummonedBy(Unit* summoner) override
        {
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || player->GetMapId() != 654 || player->GetQuestStatus(24646) != QUEST_STATUS_INCOMPLETE)
            {
                me->DespawnOrUnsummon();
                return;
            }
            m_ownerGUID = player->GetGUID();
            m_events.Reset();
            m_events.ScheduleEvent(1, 1s);
            m_events.ScheduleEvent(2, 3s);
        }
        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);
            while (uint32 event = m_events.ExecuteEvent())
            {
                Player* player = ObjectAccessor::GetPlayer(*me, m_ownerGUID);
                if (!player || !player->IsAlive() || !me->IsInPhase(player)
                    || player->GetQuestStatus(24646) != QUEST_STATUS_INCOMPLETE)
                {
                    me->DespawnOrUnsummon();
                    return;
                }
                if (event == 1)
                    m_events.ScheduleEvent(1, 1s);
                else if (event == 2)
                {
                    if (me->GetVictim())
                        me->CastSpell(me, 71019, false); // native War Stomp
                    m_events.ScheduleEvent(2, 30s);
                }
            }
            if (UpdateVictim())
                DoMeleeAttackIfReady();
        }
    };
    CreatureAI* GetAI(Creature* creature) const override { return new ai(creature); }
};

class spell_gilneas_horn_of_taldoren : public SpellScriptLoader
{
public:
    spell_gilneas_horn_of_taldoren() : SpellScriptLoader("spell_gilneas_horn_of_taldoren") { }
    class script : public SpellScript
    {
        PrepareSpellScript(script);
        bool Validate(SpellInfo const* /*info*/) override { return ValidateSpellInfo({ 71019 }); }
        SpellCastResult CheckTarget()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || player->GetQuestStatus(24646) != QUEST_STATUS_INCOMPLETE
                || player->GetExactDist(-2118.81f, 1630.49f, -41.6281f) > 80.0f
                || player->GetSummonedCreatureByEntry(38027))
                return SPELL_FAILED_BAD_TARGETS;
            CreatureTemplate const* tracker = sObjectMgr->GetCreatureTemplate(38027);
            if (!tracker || tracker->faction != 2207
                || tracker->ScriptID != sObjectMgr->GetScriptId("npc_gilneas_taldoren_tracker"))
                return SPELL_FAILED_BAD_TARGETS;
            return SPELL_CAST_OK;
        }
        void HandleHorn(SpellEffIndex index)
        {
            PreventHitDefaultEffect(index); // replaces the otherwise unimplemented event23338
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || CheckTarget() != SPELL_CAST_OK)
                return;
            std::list<Creature*> rangers;
            GetCreatureListWithEntryInGrid(rangers, player, 38022, 80.0f);
            rangers.remove_if([player](Creature* ranger)
            {
                if (!ranger->IsAlive() || !ranger->IsInPhase(player) || !ranger->IsHostileTo(player))
                    return true;
                // Never take an encounter away from another player's group.
                if (Unit* victim = ranger->GetVictim())
                {
                    if (Creature* creature = victim->ToCreature())
                        if (TempSummon* summon = creature->ToTempSummon())
                            if (summon->GetEntry() == 38027 && summon->GetSummonerGUID() != player->GetGUID())
                                return true;
                    if (Player* owner = victim->GetCharmerOrOwnerPlayerOrPlayerItself())
                        return owner != player;
                }
                return false;
            });
            if (rangers.empty())
                return;
            std::vector<Creature*> allies;
            for (Position const& position : TaldorenTrackerPositions)
                if (Creature* tracker = player->SummonCreature(38027, position, TEMPSUMMON_TIMED_DESPAWN, 45000))
                    allies.push_back(tracker);
            if (allies.empty())
                return;
            size_t next = 0;
            for (Creature* ranger : rangers)
            {
                Creature* tracker = allies[next++ % allies.size()];
                tracker->AI()->AttackStart(ranger);
                ranger->AddThreat(tracker, 1000.0f);
                ranger->AI()->AttackStart(tracker);
            }
        }
        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(script::CheckTarget);
            OnEffectHitTarget += SpellEffectFn(script::HandleHorn, EFFECT_0, SPELL_EFFECT_SEND_EVENT);
        }
    };
    SpellScript* GetSpellScript() const override { return new script(); }
};

// Half-Burnt Torch: scare the tunnel vermin, never substitute a kill credit.
class spell_gilneas_half_burnt_torch : public SpellScriptLoader
{
public:
    spell_gilneas_half_burnt_torch() : SpellScriptLoader("spell_gilneas_half_burnt_torch") { }
    class script : public SpellScript
    {
        PrepareSpellScript(script);
        void HandleTorch(SpellEffIndex /*index*/)
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            Creature* vermin = GetHitUnit() ? GetHitUnit()->ToCreature() : nullptr;
            if (!player || player->GetMapId() != 654 || !vermin || !vermin->IsAlive()
                || player->GetQuestStatus(24678) != QUEST_STATUS_INCOMPLETE)
                return;
            switch (vermin->GetEntry())
            {
                case 37889: // Graveyard Rat
                case 37891: // Underground Spider
                case 37892: // Putrescent Maggot
                    vermin->AttackStop();
                    vermin->CombatStop(true);
                    vermin->GetMotionMaster()->MoveFleeing(player, 5000);
                    break;
                default:
                    break;
            }
        }
        void Register() override
        {
            OnEffectHitTarget += SpellEffectFn(script::HandleTorch, EFFECT_0, SPELL_EFFECT_DUMMY);
        }
    };
    SpellScript* GetSpellScript() const override { return new script(); }
};

// Walden's quest attack contains a persistent drunkenness operation, not an aura.
// Preserve its native damage/stun, but do not persist alcohol on the quest player.
class spell_gilneas_walden_brandy : public SpellScriptLoader
{
public:
    spell_gilneas_walden_brandy() : SpellScriptLoader("spell_gilneas_walden_brandy") { }
    class script : public SpellScript
    {
        PrepareSpellScript(script);
        void HandleInebriate(SpellEffIndex index)
        {
            Unit* caster = GetCaster();
            Player* player = GetHitUnit() ? GetHitUnit()->ToPlayer() : nullptr;
            if (caster && caster->GetEntry() == 37733 && caster->GetMapId() == 654 && player
                && player->GetQuestStatus(QUEST_BETRAYAL_AT_TEMPESTS_REACH) == QUEST_STATUS_INCOMPLETE)
                PreventHitDefaultEffect(index);
        }
        void Register() override
        {
            OnEffectHitTarget += SpellEffectFn(script::HandleInebriate, EFFECT_2, SPELL_EFFECT_INEBRIATE);
        }
    };
    SpellScript* GetSpellScript() const override { return new script(); }
};

// Godfrey owns his movement callback. No path is fabricated for this scene.
class npc_gilneas_godfrey_departure : public CreatureScript
{
public:
    npc_gilneas_godfrey_departure() : CreatureScript("npc_gilneas_godfrey_departure") { }
    struct ai : public ScriptedAI
    {
        ai(Creature* creature) : ScriptedAI(creature) { }
        ObjectGuid m_gennGUID;
        uint32 m_elapsed = 0;
        bool m_running = false;
        bool m_finished = false;
        bool m_reportedMissingPath = false;

        uint32 PathId() const
        {
            auto id = me->GetSpawnId();
            return id <= std::numeric_limits<uint32>::max() ? static_cast<uint32>(id) : 0;
        }

        bool HasDeparturePath() const
        {
            WaypointPath const* path = sWaypointMgr->GetPath(PathId());
            return PathId() && path && path->nodes.size() > 1 && path->nodes.back().id == 4
                && std::all_of(path->nodes.begin(), path->nodes.end(), [](WaypointNode const& node)
                {
                    return std::isfinite(node.x) && std::isfinite(node.y) && std::isfinite(node.z);
                });
        }

        uint32 GetData(uint32 id) const override
        {
            return id == 1 && (!m_gennGUID.IsEmpty() || m_finished);
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            if (id == 37876 && !GetData(1))
                m_gennGUID = guid;
        }

        void NotifyGenn()
        {
            if (Creature* genn = ObjectAccessor::GetCreature(*me, m_gennGUID))
                if (genn->GetEntry() == 37876 && genn->GetMapId() == 654
                    && sObjectMgr->GetScriptId("npc_king_genn_greymane_37876")
                    && genn->GetScriptId() == sObjectMgr->GetScriptId("npc_king_genn_greymane_37876"))
                    genn->AI()->DoAction(2);
        }

        void Cancel()
        {
            if (m_running)
            {
                me->GetMotionMaster()->Clear();
                me->GetMotionMaster()->MoveIdle();
                me->StopMoving();
            }
            m_running = false;
            m_elapsed = 0;
            NotifyGenn();
            m_gennGUID = ObjectGuid::Empty;
        }

        void Reset() override
        {
            Cancel();
            m_finished = false;
        }

        void JustDied(Unit*) override
        {
            Cancel();
            m_finished = true;
        }

        void DoAction(int32 action) override
        {
            if (action == 2)
            {
                Cancel();
                return;
            }
            if (action != 1 || m_running || m_finished || m_gennGUID.IsEmpty())
                return;
            if (!HasDeparturePath())
            {
                if (!m_reportedMissingPath)
                {
                    TC_LOG_ERROR("sql.sql", "Gilneas Godfrey37875 departure path %u is absent or incomplete; movement skipped", PathId());
                    m_reportedMissingPath = true;
                }
                Cancel();
                return;
            }
            m_running = true;
            me->GetMotionMaster()->MovePath(PathId(), false);
            // Waypoint movement controls the spline. The scene must not leave
            // a persistent NPC with manually disabled gravity.
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (!m_running || type != WAYPOINT_MOTION_TYPE || id != 4)
                return;
            m_running = false;
            m_finished = true;
            NotifyGenn();
            m_gennGUID = ObjectGuid::Empty;
            me->DespawnOrUnsummon(5s);
        }

        void UpdateAI(uint32 diff) override
        {
            if (!m_gennGUID.IsEmpty())
            {
                m_elapsed += diff;
                Creature* genn = ObjectAccessor::GetCreature(*me, m_gennGUID);
                if (!genn || !genn->IsAlive() || genn->GetMapId() != 654
                    || genn->GetEntry() != 37876
                    || !sObjectMgr->GetScriptId("npc_king_genn_greymane_37876")
                    || genn->GetScriptId() != sObjectMgr->GetScriptId("npc_king_genn_greymane_37876")
                    || !me->InSamePhase(genn->GetPhaseShift()) || m_elapsed >= 60000)
                {
                    Cancel();
                    return;
                }
            }
            if (UpdateVictim())
                DoMeleeAttackIfReady();
        }
    };
    CreatureAI* GetAI(Creature* creature) const override
    {
        return creature->GetMapId() == 654 && !creature->IsSummon() ? new ai(creature) : nullptr;
    }
};

// 37876
class npc_king_genn_greymane_37876 : public CreatureScript
{
public:
    npc_king_genn_greymane_37876() : CreatureScript("npc_king_genn_greymane_37876") { }

    bool OnQuestReward(Player* player, Creature* creature, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == QUEST_BETRAYAL_AT_TEMPESTS_REACH)
        {
            player->CastSpell(player, SPELL_FORCE_REACTION_1);
            player->RemoveAura(SPELL_STEALTH_70456);
            creature->AI()->DoAction(1);
        }

        return false;
    }

    struct npc_king_genn_greymane_37876AI : public ScriptedAI
    {
        npc_king_genn_greymane_37876AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_godfreyGUID;
        bool m_sceneStarted = false;

        void Reset() override
        {
            if (m_sceneStarted)
                if (Creature* godfrey = ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                    if (godfrey->GetScriptId() == sObjectMgr->GetScriptId("npc_gilneas_godfrey_departure"))
                        godfrey->AI()->DoAction(2);
            m_events.Reset();
            m_sceneStarted = false;
            m_godfreyGUID = ObjectGuid::Empty;

            if (Creature* godfrey = me->FindNearestCreature(NPC_LORD_GODFREY, 20.0f))
                m_godfreyGUID = godfrey->GetGUID();
        }

        void DamageTaken(Unit* attacker, uint32& damage) override
        {
            // Protect the questgiver from ambient NPC combat, not player-controlled units.
            if (me->GetMapId() == 654 && attacker && attacker->ToCreature()
                && !attacker->GetCharmerOrOwnerPlayerOrPlayerItself())
                damage = 0;
        }

        void DoAction(int32 param) override
        {
            if (param == 2)
            {
                m_events.Reset();
                m_sceneStarted = false;
                return;
            }
            if (param != 1 || m_sceneStarted || me->GetMapId() != 654 || me->GetEntry() != 37876)
                return;
            uint32 scriptId = sObjectMgr->GetScriptId("npc_gilneas_godfrey_departure");
            Creature* godfrey = me->FindNearestCreature(NPC_LORD_GODFREY, 20.0f);
            if (!scriptId || !godfrey || !godfrey->IsAlive()
                || godfrey->GetMapId() != 654 || godfrey->IsSummon()
                || !me->InSamePhase(godfrey->GetPhaseShift())
                || godfrey->GetScriptId() != scriptId
                || godfrey->AI()->GetData(1))
                return;
            m_godfreyGUID = godfrey->GetGUID();
            godfrey->AI()->SetGUID(me->GetGUID(), 37876);
            m_sceneStarted = true;
            m_events.ScheduleEvent(EVENT_START_ANIM, 100ms);
        }

        void UpdateAI(uint32 diff) override
        {
            if (m_sceneStarted && !ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                DoAction(2);
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_ANIM:
                    {
                        if (ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                            m_events.ScheduleEvent(EVENT_START_ANIM + 1, 100ms);
                        break;
                    }
                    case EVENT_START_ANIM + 1:
                    {
                        Talk(0);
                        m_events.ScheduleEvent(EVENT_START_ANIM + 2, 5s);
                        break;
                    }
                    case EVENT_START_ANIM + 2:
                    {
                        if (Creature* godfrey = ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                            if (sCreatureTextMgr->TextExist(NPC_LORD_GODFREY, 0))
                                godfrey->AI()->Talk(0);

                        m_events.ScheduleEvent(EVENT_START_ANIM + 3, 3s);
                        break;
                    }
                    case EVENT_START_ANIM + 3:
                    {
                        if (Creature* godfrey = ObjectAccessor::GetCreature(*me, m_godfreyGUID))
                        {
                            godfrey->AI()->DoAction(1);
                        }
                        else
                            DoAction(2);

                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_king_genn_greymane_37876AI(creature);
    }
};

// 38764
class npc_lord_hewell_38764 : public CreatureScript
{
public:
    npc_lord_hewell_38764() : CreatureScript("npc_lord_hewell_38764") { }

    bool OnGossipSelect(Player* player, Creature* /*creature*/, uint32 /*sender*/, uint32 /*action*/) override
    {
        if (player->GetQuestStatus(QUEST_FLANK_THE_FORSAKEN) == QUEST_STATUS_COMPLETE)
            player->CastSpell(player, 72773);

        return false;
    }
};

// 38765
class npc_stout_mountain_horse_38765 : public CreatureScript
{
public:
    npc_stout_mountain_horse_38765() : CreatureScript("npc_stout_mountain_horse_38765") { }

    enum eNpc
    {
        PATH_ID                                 = 3876500
    };

    struct npc_stout_mountain_horse_38765AI : public ScriptedAI
    {
        npc_stout_mountain_horse_38765AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;

        void Reset() override
        {
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (summoner->IsPlayer())
            {
                m_playerGUID = summoner->GetGUID();
                m_events.ScheduleEvent(EVENT_START_WAYPOINTS, 1s + 500ms);
            }
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type == WAYPOINT_MOTION_TYPE)
            {
                switch (id)
                {
                    case 41:
                    {
                        m_events.ScheduleEvent(EVENT_STOP_WAYPOINTS, 1s);
                        break;
                    }
                }
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_WAYPOINTS:
                    {
                        me->GetMotionMaster()->MovePath(PATH_ID, false);
                        break;
                    }
                    case EVENT_STOP_WAYPOINTS:
                    {
                        me->CastSpell(me, SPELL_DANS_EJECT_ALL_PASSENGERS);
                        me->DespawnOrUnsummon(3s);

                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            if (player->HasAura(SPELL_FORCE_REACTION_1))
                                player->RemoveAura(SPELL_FORCE_REACTION_1);

                            if (player->HasAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09))
                                player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_09);
                        }
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_stout_mountain_horse_38765AI(creature);
    }
};

// 37783
class npc_lorna_crowley_37783 : public CreatureScript
{
public:
    npc_lorna_crowley_37783() : CreatureScript("npc_lorna_crowley_37783") { }

    bool OnQuestReward(Player* player, Creature* /*creature*/, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == QUEST_PUSH_THEM_OUT)
        {
            player->RemoveAura(SPELL_PHASE_QUEST_ZONE_SPECIFIC_11);
            player->CastSpell(player, SPELL_PHASE_QUEST_ZONE_SPECIFIC_12, true);
        }

        return false;
    }
};

// 37694
class npc_enslaved_villager_37694 : public CreatureScript
{
public:
    npc_enslaved_villager_37694() : CreatureScript("npc_enslaved_villager_37694") { }

    struct npc_enslaved_villager_37694AI : public ScriptedAI
    {
        npc_enslaved_villager_37694AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_ballGUID;
        bool m_sceneStarted;

        void Reset() override
        {
            m_events.Reset();
            m_sceneStarted = false;
            m_playerGUID = ObjectGuid::Empty;
            m_ballGUID = ObjectGuid::Empty;
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            return id == PLAYER_GUID ? m_playerGUID : ObjectGuid::Empty;
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            if (m_sceneStarted)
                return;

            switch (id)
            {
                case PLAYER_GUID:
                    m_playerGUID = guid;
                    break;
                case GO_BALL_AND_CHAIN:
                    m_ballGUID = guid;
                    break;
            }
        }

        void DoAction(int32 param) override
        {
            switch (param)
            {
                case EVENT_START_ANIM:
                {
                    if (m_sceneStarted || m_playerGUID.IsEmpty() || m_ballGUID.IsEmpty())
                        return;
                    Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                    GameObject* ball = ObjectAccessor::GetGameObject(*me, m_ballGUID);
                    if (!player || !player->IsAlive() || !ball || ball->GetEntry() != GO_BALL_AND_CHAIN
                        || me->GetDistance(ball) > 5.0f
                        || (player->GetQuestStatus(QUEST_LIBERATION_DAY) != QUEST_STATUS_INCOMPLETE
                            && player->GetQuestStatus(QUEST_LIBERATION_DAY) != QUEST_STATUS_COMPLETE))
                    {
                        m_playerGUID = ObjectGuid::Empty;
                        m_ballGUID = ObjectGuid::Empty;
                        return;
                    }
                    // GO use supplies the native objective credit and loot-state visibility.
                    // Never destroy a shared GO for every nearby player from this AI.
                    m_sceneStarted = true;
                    m_events.ScheduleEvent(EVENT_START_ANIM, 1s);
                    break;
                }
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_ANIM:
                    {
                        me->HandleEmoteCommand(EMOTE_STATE_NONE);

                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        {
                            me->SetFacingToObject(player);
                            Talk(0, player);
                        }

                        m_events.ScheduleEvent(EVENT_TALK_PART_00, 3s);
                        break;
                    }
                    case EVENT_TALK_PART_00:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            me->GetMotionMaster()->MoveFleeing(player, 7000);

                        m_events.ScheduleEvent(EVENT_TALK_PART_01, 6s);
                        break;
                    }
                    case EVENT_TALK_PART_01:
                        me->DespawnOrUnsummon(10ms, 300s);
                        break;
                }
            }

            if (!UpdateVictim())
                return;
            else
                DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_enslaved_villager_37694AI(creature);
    }
};

// 201775
class go_ball_and_chain_201775 : public GameObjectScript
{
public:
    go_ball_and_chain_201775() : GameObjectScript("go_ball_and_chain_201775") { }

    void OnLootStateChanged(GameObject* go, uint32 state, Unit* unit) override
    {
        if (state == GO_ACTIVATED && unit)
            if (Player* player = unit->ToPlayer())
                if (player->GetQuestStatus(QUEST_LIBERATION_DAY) == QUEST_STATUS_INCOMPLETE || player->GetQuestStatus(QUEST_LIBERATION_DAY) == QUEST_STATUS_COMPLETE)
                    if (Creature* villager = go->FindNearestCreature(NPC_ENSLAVED_VILLAGER, 5.0f))
                    {
                        if (!villager->AI()->GetGUID(PLAYER_GUID).IsEmpty())
                            return; // The active shared scene retains its original owner.
                        villager->AI()->SetGUID(go->GetGUID(), go->GetEntry());
                        villager->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                        villager->AI()->DoAction(EVENT_START_ANIM);
                    }
    }
};

// from here phase 262144 is active.. battle for gilneas in zone_gilneas_city3

void AddSC_zone_gilneas_duskhaven()
{
    new spell_gilneas_walden_brandy();
    new spell_gilneas_half_burnt_torch();
    new npc_gilneas_taldoren_tracker();
    new spell_gilneas_horn_of_taldoren();
    new npc_slain_watchman_36205();
    new npc_krennan_aranas_36331();
    new npc_king_genn_greymane_36332();
    new player_gilneas_stocks_recovery();
    new npc_gwen_armstead_34571();
    new go_mandragore_196394();
    new npc_horrid_abomination_36231();
    new spell_cast_keg_69094();
    new npc_cynthia_36267();
    new npc_james_36268();
    new npc_ashley_36269();
    new npc_forsaken_catapult_36283();
    new spell_launch_68659();
    new spell_fire_boulder_68591();
    new spell_launch_96185();
    new npc_mastiff_36409();
    new spell_gilneas_leader_of_the_pack();
    new npc_mastiff_36405();
    new npc_lord_godfrey_36290();
    new npc_drowning_watchman_36440();
    new spell_rescue_drowning_watchman_68735();
    new npc_gilneas_grandma_scene();
    new npc_chance_36459();
    new npc_gilneas_lucius_the_cruel();
    new npc_forsaken_castaway_36488();
    new npc_mountain_horse_36555();
    new npc_mountain_horse_36540();
    new spell_round_up_horse_68903();
    new npc_gwen_armstead_36452();
    new go_gate_196399();
    new go_gate_196401();
    new npc_swift_mountain_horse_36741();
    new npc_queen_mia_greymane_36606();
    new npc_king_genn_greymane_36743();
    new player_gilneas_carriage_recovery();
    new npc_stagecoach_carriage_44928();
    new npc_harness_43336();
    new npc_stagecoach_carriage_43337();
    new go_kings_gate_196412();
    new npc_ogre_ambusher_38762();
    new npc_prince_liam_greymane_37065();
    new npc_crash_survivor_37067();
    new npc_swamp_crocolisk_37078();
    new go_koroths_banner_201594();
    new at_the_blackwald_6687();
    new npc_dark_scout_37953();
    new npc_trigger_quest_24616();
    new item_belysras_talisman_49944();
    new npc_tobias_mistmantle_38051();
    new npc_gilneas_godfrey_departure();
    new npc_king_genn_greymane_37876();
    new npc_lord_hewell_38764();
    new npc_stout_mountain_horse_38765();
    new npc_lorna_crowley_37783();
    new npc_enslaved_villager_37694();
    new go_ball_and_chain_201775();
};
