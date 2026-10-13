/*
 * Copyright (C) 2017-2018 AshamaneProject <https://github.com/AshamaneProject>
 * Copyright (C) 2011-2016 ArkCORE <http://www.arkania.net/>
 * Copyright (C) 2008-2014 TrinityCore <http://www.trinitycore.org/>
 * Copyright (C) 2005-2009 MaNGOS <http://getmangos.com/>
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

#include "Creature.h"
#include "Map.h"
#include "Unit.h"
#include "ScriptedCreature.h"
#include "ScriptedEscortAI.h"
#include "ScriptedFollowerAI.h"
#include "Vehicle.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "CreatureGroups.h"
#include "Player.h"
#include "PhasingHandler.h"
#include "MotionMaster.h"
#include "Transport.h"
#include "TransportMgr.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "ScriptMgr.h"
#include "SpellScript.h"
#include "zone_gilneas.h"
#include "WaypointManager.h"
#include "QuestDef.h"
#include "TemporarySummon.h"
#include "Log.h"
#include <cmath>

enum eBattleForGilneas
{
    QUEST_HUNT_FOR_SYLVANAS             = 24902,
    QUEST_RUTTHERAN                     = 14434,
    QUEST_ENDGAME                       = 26706,

    NPC_FORSAKEN_CROSSBOWMAN            = 38210,
    NPC_LORNA_CROWLEY                   = 38426,
    NPC_DARK_RANGER_ELITE               = 38464,
    NPC_LADY_SYLVANAS_WINDRUNNER        = 38469,
    NPC_TOBIAS_MISTMANTLE               = 38507,
    NPC_LADY_SYLVANAS_WINDRUNNER_38530  = 38530,
    NPC_GENERAL_WARHOWL                 = 38533,
    NPC_HIGH_EXECUTOR_CRENSHAW          = 38537,
    NPC_KRENNAN_ARANAS                  = 38553,
    NPC_FORSAKEN_GENERAL                = 38617,
    NPC_FORSAKEN_SERGANT                = 38618,
    NPC_GUNSHIP_GRUNT                   = 42141,
    NPC_LORNA_CRAWLEY_43566             = 43566,
    NPC_WORGEN_WARRIOR                  = 43651,
    NPC_GILNEAN_SHARPSHOOTER            = 43703,
    NPC_HIPPOGRYPH                      = 43747,
    NPC_TOBIAS_MISTMANTLE_43749         = 43749,
    NPC_GILNEAS_VEHICLE_ROPE            = 43793,

    GO_WORGEN_GUNSHIP                   = 203428,
    GO_ROPE                             = 204428,

    SPELL_GILNEAS_MILITIA_SHOOT         = 6660,
    SPELL_CLEAVE                        = 15496,
    SPELL_FOR_GILNEAS                   = 81790,
};

// Walking candidate from pinned JadeCore SQL; all points/segments verified against map 654 mmaps.
// See docs/audit-data/gilneas-tobias-source-audit.json; source timings/credits are not imported.
Position const TobiasWalkingRoute[] =
{
    {-1654.68f, 1603.6f, 23.131f, 0.98f},
    {-1664.22f, 1615.85f, 20.49f, 2.19f},
    {-1632.82f, 1621.85f, 20.49f, 0.18f},
    {-1589.17f, 1607.13f, 21.6f, 5.97f},
    {-1569.75f, 1631.44f, 20.589f, 5.77f},
    {-1490.2f, 1577.88f, 20.486f, 5.65f},
    {-1504.73f, 1577.0f, 20.486f, 3.18f},
    {-1529.4f, 1576.88f, 26.68f, 3.14f},
    {-1545.55f, 1571.63f, 29.2f, 4.02f},
    {-1594.87f, 1524.96f, 29.235f, 3.87f},
    {-1614.23f, 1537.65f, 29.3f, 5.5f},
};

// 38507
class npc_tobias_mistmantle_38507 : public CreatureScript
{
public:
    npc_tobias_mistmantle_38507() : CreatureScript("npc_tobias_mistmantle_38507") { }

    enum eNpc
    {
        EVENT_MOVEMENT_START_PATH_1 = 301,
        EVENT_MOVEMENT_START_PATH_2,
        EVENT_MOVEMENT_START_PATH_3,
        EVENT_MOVEMENT_START_PATH_4,
        EVENT_MOVEMENT_START_PATH_5,
        EVENT_MOVEMENT_START_PATH_6,
        EVENT_MOVEMENT_START_SYLVANAS_AI,
        EVENT_WAIT_FOR_PLAYER_1,
        EVENT_WAIT_FOR_PLAYER_2,
        EVENT_WAIT_FOR_PLAYER_3,
        EVENT_WAIT_FOR_PLAYER_4,
        EVENT_WAIT_FOR_OUTSIDE_EVENT,
        EVENT_WAIT_FOR_OUTSIDE_EVENT1,
        EVENT_MOVE_NATIVE_POINT,
    };

    struct npc_tobias_mistmantle_38507AI : public ScriptedAI
    {
        npc_tobias_mistmantle_38507AI(Creature* pCreature) : ScriptedAI(pCreature) { }

        EventMap m_events;
        ObjectGuid   m_playerGUID;
        ObjectGuid   m_sylvanasGUID;
        ObjectGuid   m_warhowlGUID;
        ObjectGuid   m_crenshawGUID;
        uint32   m_eventPhase = 0;
        uint32   m_lifetime = 0;
        bool     m_stopped = false;
        bool     m_walkingRoute = false;
        bool     m_walkMoving = false;
        bool     m_sceneActorsSpawned = false;
        uint32   m_walkPoint = 0;
        uint32   m_nativePath = 0;
        uint32   m_nativePoint = 0;
        bool     m_nativeMoving = false;

        void Reset() override
        {
            me->SetReactState(REACT_PASSIVE);
            if (!m_playerGUID.IsEmpty())
            {
                StopScene();
                return;
            }
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
            m_eventPhase = 0;
            m_sylvanasGUID = ObjectGuid::Empty;
            m_warhowlGUID = ObjectGuid::Empty;
            m_crenshawGUID = ObjectGuid::Empty;
        }

        void AttackStart(Unit* /*who*/) override { }
        void MoveInLineOfSight(Unit* /*who*/) override { }
        bool CanAIAttack(Unit const* /*who*/) const override { return false; }
        void EnterEvadeMode(EvadeReason /*reason*/) override { }
        void DamageTaken(Unit* /*attacker*/, uint32& damage) override { damage = 0; }

        bool HasScenePaths() const
        {
            uint32 const endpoints[] = {1, 1, 3, 5, 23};
            for (uint32 i = 0; i < 5; ++i)
            {
                WaypointPath const* path = sWaypointMgr->GetPath(3850701 + i);
                // MovementInform receives a vector index; all expected stops
                // must exist as contiguous points in these native zero-based paths.
                if (!path || path->nodes.size() != endpoints[i] + 1)
                    return false;
                uint32 index = 0;
                for (WaypointNode const& node : path->nodes)
                {
                    if (node.id != index++ || !std::isfinite(node.x)
                        || !std::isfinite(node.y) || !std::isfinite(node.z))
                        return false;
                }
            }
            return true;
        }

        void StopScene()
        {
            if (m_stopped)
                return;
            m_stopped = true;
            m_events.Reset();
            me->GetMotionMaster()->Clear();
            for (ObjectGuid guid : {m_sylvanasGUID, m_warhowlGUID, m_crenshawGUID})
                if (Creature* actor = ObjectAccessor::GetCreature(*me, guid))
                    actor->DespawnOrUnsummon();
            me->DespawnOrUnsummon();
        }

        void JustDied(Unit*) override
        {
            StopScene();
        }

        bool UpdateSceneOwner(uint32 diff)
        {
            if (m_stopped || m_playerGUID.IsEmpty())
                return false;
            // WorldObject::SummonCreature applies its requested type AFTER IsSummonedBy.
            // Reassert the owned scene lifetime before TempSummon::Update checks its timer.
            if (TempSummon* summon = me->ToTempSummon())
                summon->SetTempSummonType(TEMPSUMMON_MANUAL_DESPAWN);
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            uint32 const lifetimeLimit = m_sceneActorsSpawned ? 180000 : 900000;
            if (m_lifetime >= lifetimeLimit || diff >= lifetimeLimit - m_lifetime || !player || !player->IsAlive()
                || player->GetMapId() != me->GetMapId() || !me->IsInPhase(player)
                || (player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_INCOMPLETE
                    && player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_COMPLETE))
            {
                TC_LOG_ERROR("scripts", "Gilneas 24902: Tobias stopped: lifetime=%u limit=%u ownerPresent=%u ownerAlive=%u sameMap=%u samePhase=%u questStatus=%u stage=%u", m_lifetime, lifetimeLimit, uint32(player != nullptr), uint32(player && player->IsAlive()), uint32(player && player->GetMapId() == me->GetMapId()), uint32(player && me->IsInPhase(player)), player ? uint32(player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS)) : 0, m_eventPhase);
                StopScene();
                return false;
            }
            m_lifetime += diff;
            return true;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (m_stopped || !m_playerGUID.IsEmpty())
                return;
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || me->GetMapId() != 654
                || player->GetMapId() != me->GetMapId() || !me->IsInPhase(player)
                || (player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_INCOMPLETE
                    && player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_COMPLETE))
            {
                StopScene();
                return;
            }
            m_walkingRoute = !HasScenePaths();
            // Use the owner-checked AI timeout; an independent delayed despawn
            // would still fire after the route hands off to the final scene.
            if (TempSummon* summon = me->ToTempSummon())
            {
                summon->SetTempSummonType(TEMPSUMMON_MANUAL_DESPAWN);

            }
            me->setActive(true);
            me->SetSpeedRate(MOVE_RUN, 1.0f);
            m_playerGUID = player->GetGUID();
            m_eventPhase = 1;
            m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_1, 3000);
        }

        void StartWalkingPoint()
        {
            if (m_stopped || m_walkMoving || m_walkPoint >= sizeof(TobiasWalkingRoute) / sizeof(TobiasWalkingRoute[0]))
                return;
            if (!IsPlayerNear(20.0f))
            {
                m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_1, 1000);
                return;
            }
            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
            {
                if (m_walkPoint == 0)
                    Talk(0, player);
                else if (m_walkPoint == 3)
                    Talk(1, player);
                else if (m_walkPoint == 6)
                    Talk(2, player);
                else if (m_walkPoint == 10)
                    Talk(3, player);
            }
            m_walkMoving = true;
            me->SetWalk(false);
            me->GetMotionMaster()->MovePoint(3000 + m_walkPoint, TobiasWalkingRoute[m_walkPoint]);
        }

        void StartNativePath(uint32 pathId)
        {
            m_nativePath = pathId;
            m_nativePoint = 0;
            m_nativeMoving = false;
            MoveNativePoint();
        }

        void MoveNativePoint()
        {
            if (m_stopped || m_nativeMoving || !m_nativePath)
                return;
            WaypointPath const* path = sWaypointMgr->GetPath(m_nativePath);
            uint32 const exitPoints = m_nativePath == 3850701 ? 3 : 0;
            if (!path || m_nativePoint >= exitPoints + path->nodes.size())
            {
                StopScene();
                return;
            }
            if (!IsPlayerNear(20.0f))
            {
                m_events.RescheduleEvent(EVENT_MOVE_NATIVE_POINT, 1000);
                return;
            }
            // Follow the audited door approach before the native moat-jump route.
            // MovePoint generates a navmesh path instead of drawing through walls.
            Position destination;
            if (m_nativePoint < exitPoints)
                destination = TobiasWalkingRoute[m_nativePoint];
            else
            {
                WaypointNode const& node = path->nodes[m_nativePoint - exitPoints];
                destination.Relocate(node.x, node.y, node.z, node.orientation);
            }
            m_nativeMoving = true;
            me->SetWalk(false);
            me->GetMotionMaster()->MovePoint(4000 + (m_nativePath - 3850701) * 100 + m_nativePoint, destination);
        }

        void JustSummoned(Creature* summon) override
        {
            summon->SetWalk(true);
            switch (summon->GetEntry())
            {
                case NPC_LADY_SYLVANAS_WINDRUNNER_38530:
                    m_sylvanasGUID = summon->GetGUID();
                    me->SetFacingToObject(summon);
                    summon->AI()->SetGUID(me->GetGUID(), me->GetEntry());
                    summon->AI()->SetGUID(m_playerGUID, PLAYER_GUID);
                    summon->GetMotionMaster()->MovePoint(2005, -1600.11f, 1518.04f, 29.24f);
                    break;
                case NPC_GENERAL_WARHOWL:
                    m_warhowlGUID = summon->GetGUID();
                    summon->GetMotionMaster()->MovePoint(2006, -1593.35f, 1531.32f, 29.24f);
                    break;
                case NPC_HIGH_EXECUTOR_CRENSHAW:
                    m_crenshawGUID = summon->GetGUID();
                    summon->GetMotionMaster()->MovePoint(2007, -1587.55f, 1519.32f, 29.24f);
                    break;
            }
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (m_stopped || m_playerGUID.IsEmpty())
                return;
            if (!m_walkingRoute && type == POINT_MOTION_TYPE && m_nativePath)
            {
                uint32 const expected = 4000 + (m_nativePath - 3850701) * 100 + m_nativePoint;
                if (!m_nativeMoving || id != expected)
                    return;
                WaypointPath const* path = sWaypointMgr->GetPath(m_nativePath);
                uint32 const exitPoints = m_nativePath == 3850701 ? 3 : 0;
                if (!path || m_nativePoint >= exitPoints + path->nodes.size())
                {
                    StopScene();
                    return;
                }
                m_nativeMoving = false;
                uint32 const arrived = m_nativePoint++;
                if (m_nativePoint < exitPoints + path->nodes.size())
                    m_events.RescheduleEvent(EVENT_MOVE_NATIVE_POINT, 10);
                else
                    m_nativePath = 0;
                // Preserve the original per-point dialogue, pauses and jump handoffs.
                if (arrived >= exitPoints)
                    MovementInform(WAYPOINT_MOTION_TYPE, arrived - exitPoints);
                return;
            }
            if (m_walkingRoute && type == POINT_MOTION_TYPE)
            {
                if (!m_walkMoving || id != 3000 + m_walkPoint)
                    return;
                m_walkMoving = false;
                ++m_walkPoint;
                if (m_walkPoint < sizeof(TobiasWalkingRoute) / sizeof(TobiasWalkingRoute[0]))
                    m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_1, 1000);
                else
                {
                    // Retain the native hiding jump and subsequent Sylvanas dialogue.
                    m_eventPhase = 5;
                    me->GetMotionMaster()->MoveJump(-1614.5f, 1533.9f, 27.26f, 0.0f, 20.0f, 5.0f, 2004);
                }
                return;
            }
            switch (type)
            {
                case WAYPOINT_MOTION_TYPE:
                {
                    if (m_eventPhase == 1 && id == 0)
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(0, player);
                    }
                    else if (m_eventPhase == 1 && id == 1)
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_PATH_1, 1000);
                    else if (m_eventPhase == 2 && id == 0)
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(1, player);
                    }
                    else if (m_eventPhase == 2 && id == 1)
                        m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_2, 1000); // on open gate
                    else if (m_eventPhase == 3 && id == 3)
                        m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_3, 1000); // on wall 1
                    else if (m_eventPhase == 4 && id == 5)
                        m_events.RescheduleEvent(EVENT_WAIT_FOR_OUTSIDE_EVENT, 1000);
                    else if (m_eventPhase == 5 && id == 23)
                        m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_4, 1000); // inside water
                    break;
                }
                case EFFECT_MOTION_TYPE: // jump
                {
                    if (m_eventPhase == 1 && id == 2001)
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_PATH_2, 1000);
                    else if (m_eventPhase == 3 && id == 2003)
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_PATH_4, 1000);
                    else if (m_eventPhase == 5 && id == 2004)
                    {
                        me->SetFacingTo(5.6f);
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_PATH_6, 10);
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_SYLVANAS_AI, 1000);
                    }
                    break;
                }
            }
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            switch (id)
            {
                case NPC_TOBIAS_MISTMANTLE:
                    return me->GetGUID();
                case NPC_LADY_SYLVANAS_WINDRUNNER_38530:
                    return m_sylvanasGUID;
                case NPC_GENERAL_WARHOWL:
                    return m_warhowlGUID;
                case NPC_HIGH_EXECUTOR_CRENSHAW:
                    return m_crenshawGUID;
                case PLAYER_GUID:
                    return m_playerGUID;
            }
            return ObjectGuid::Empty;
        }

        void UpdateAI(uint32 diff) override
        {
            if (!UpdateSceneOwner(diff))
                return;
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_MOVE_NATIVE_POINT:
                    {
                        MoveNativePoint();
                        break;
                    }
                    case EVENT_WAIT_FOR_PLAYER_1:
                    {
                        if (m_walkingRoute)
                        {
                            StartWalkingPoint();
                            break;
                        }
                        if (IsPlayerNear(20.0f))
                            StartNativePath(3850701);
                        else
                            m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_1, 1000);
                        break;
                    }
                    case EVENT_MOVEMENT_START_PATH_1:
                    {
                        me->GetMotionMaster()->MoveJump(-1601.925f, 1607.654f, 20.11606f, 0.0f, 20.0f, 20.0f, 2001);
                        break;
                    }
                    case EVENT_MOVEMENT_START_PATH_2:
                    {
                        m_eventPhase = 2;
                        StartNativePath(3850702);
                        break;
                    }
                    case EVENT_WAIT_FOR_PLAYER_2:
                    {
                        if (IsPlayerNear(8.0f))
                        {
                            m_eventPhase = 3;
                            StartNativePath(3850703);
                        }
                        else
                            m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_2, 1000);
                        break;
                    }
                    case EVENT_WAIT_FOR_PLAYER_3:
                    {
                        if (IsPlayerNear(8.0f))
                            me->GetMotionMaster()->MoveJump(-1548.65f, 1618.41f, 23.1788f, 0.0f, 20.0f, 5.0f, 2003);
                        else
                            m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_3, 1000);
                        break;
                    }
                    case EVENT_MOVEMENT_START_PATH_4:
                    {
                        m_eventPhase = 4;
                        StartNativePath(3850704);
                        break;
                    }
                    case EVENT_WAIT_FOR_OUTSIDE_EVENT:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            if (Creature* general = me->FindNearestCreature(NPC_FORSAKEN_GENERAL, 25.0f))
                                general->AI()->Talk(0, player);
                        m_events.RescheduleEvent(EVENT_WAIT_FOR_OUTSIDE_EVENT1, 6000);
                        break;
                    }
                    case EVENT_WAIT_FOR_OUTSIDE_EVENT1:
                    {
                        if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                            Talk(2, player);
                        m_events.RescheduleEvent(EVENT_MOVEMENT_START_PATH_5, 6000);
                        break;
                    }
                    case EVENT_MOVEMENT_START_PATH_5:
                    {
                        m_eventPhase = 5;
                        StartNativePath(3850705);
                        break;
                    }
                    case EVENT_WAIT_FOR_PLAYER_4:
                    {
                        if (IsPlayerNear(8.0f))
                        {
                            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                                Talk(3, player);
                            me->GetMotionMaster()->MoveJump(-1614.5f, 1533.9f, 27.26f, 0.0f, 20.0f, 5.0f, 2004);
                        }
                        else
                            m_events.RescheduleEvent(EVENT_WAIT_FOR_PLAYER_4, 1000);
                        break;
                    }
                    case EVENT_MOVEMENT_START_PATH_6:
                    {
                        me->SetSwim(true);
                        me->GetMotionMaster()->MovePoint(2008, -1613.95f, 1536.012f, 27.4f);
                        break;
                    }
                    case EVENT_MOVEMENT_START_SYLVANAS_AI:
                    {
                        if (m_sceneActorsSpawned)
                            break;
                        m_sceneActorsSpawned = true;
                        // there are several summon spell, but all have the summoner position as spawnpoint.. 72476, 72239, 72236, 72238, 72245
                        if (!me->SummonCreature(NPC_GENERAL_WARHOWL, -1566.053f, 1557.191f, 29.36808f, 4.273f, TEMPSUMMON_TIMED_DESPAWN, 180000))
                        {
                            StopScene();
                            break;
                        }
                        if (!me->SummonCreature(NPC_LADY_SYLVANAS_WINDRUNNER_38530, -1567.477f, 1554.569f, 29.36808f, 0.88f, TEMPSUMMON_TIMED_DESPAWN, 180000))
                        {
                            StopScene();
                            break;
                        }
                        if (!me->SummonCreature(NPC_HIGH_EXECUTOR_CRENSHAW, -1566.795f, 1555.300f, 29.36808f, 3.275f, TEMPSUMMON_TIMED_DESPAWN, 180000))
                        {
                            StopScene();
                            break;
                        }
                        m_lifetime = 0; // Give the complete conversation its own three-minute budget.
                        break;
                    }
                }
            }

            // This guide observes the scene; combat must never interrupt his escort.
        }

        bool IsPlayerNear(float range)
        {
            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                if (player->GetDistance2d(me) < range)
                    return true;
            return false;
        }
    };

    CreatureAI* GetAI(Creature* pCreature) const override
    {
        if (!pCreature->IsSummon() || pCreature->GetMapId() != 654)
            return nullptr;
        return new npc_tobias_mistmantle_38507AI(pCreature);
    }
};

// 38530
class npc_lady_sylvanas_windrunner_38530 : public CreatureScript
{
public:
    npc_lady_sylvanas_windrunner_38530() : CreatureScript("npc_lady_sylvanas_windrunner_38530") { }

    enum eNpc
    {
        EVENT_START_TALK = 401,
        EVENT_TALK_2,
        EVENT_TALK_3,
        EVENT_TALK_4,
        EVENT_TALK_5,
        EVENT_TALK_6,
        EVENT_TALK_7,
        EVENT_TALK_8,
        EVENT_END,
        EVENT_DESPAWN_WARHOWL,
        EVENT_DESPAWN,
    };

    struct npc_lady_sylvanas_windrunner_38530AI : public ScriptedAI
    {
        npc_lady_sylvanas_windrunner_38530AI(Creature* pCreature) : ScriptedAI(pCreature) { }

        EventMap m_events;
        bool m_dialogueStarted = false;
        bool m_completionHandled = false;
        ObjectGuid   m_playerGUID;
        ObjectGuid   m_tobiasGUID;
        ObjectGuid   m_sylvanasGUID;
        ObjectGuid   m_warhowlGUID;
        ObjectGuid   m_crenshawGUID;

        void Reset() override
        {
            m_events.Reset();
            m_dialogueStarted = false;
            m_completionHandled = false;
            m_playerGUID = ObjectGuid::Empty;
            m_tobiasGUID = ObjectGuid::Empty;
            m_sylvanasGUID = ObjectGuid::Empty;
            m_warhowlGUID = ObjectGuid::Empty;
            m_crenshawGUID = ObjectGuid::Empty;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (summoner->GetEntry() == NPC_TOBIAS_MISTMANTLE)
                m_tobiasGUID = summoner->GetGUID();
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type == POINT_MOTION_TYPE)
                if (id == 2005)
                {
                    if (m_dialogueStarted)
                        return;
                    m_dialogueStarted = true;
                    me->SetFacingTo(5.6f);
                    m_events.ScheduleEvent(EVENT_START_TALK, 1000);
                }
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            switch (id)
            {
                case PLAYER_GUID:
                    m_playerGUID = guid;
                    break;
                case NPC_TOBIAS_MISTMANTLE:
                    m_tobiasGUID = guid;
                    break;
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_START_TALK:
                    {
                        if (Creature* tobias = ObjectAccessor::GetCreature(*me, m_tobiasGUID))
                        {
                            m_playerGUID = tobias->AI()->GetGUID(PLAYER_GUID);
                            m_warhowlGUID = tobias->AI()->GetGUID(NPC_GENERAL_WARHOWL);
                            m_crenshawGUID = tobias->AI()->GetGUID(NPC_HIGH_EXECUTOR_CRENSHAW);
                        }
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            warhowl->AI()->Talk(0);
                        m_events.ScheduleEvent(EVENT_TALK_2, 10000);
                        break;
                    }
                    case EVENT_TALK_2:
                    {
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            me->SetFacingToObject(warhowl);
                        Talk(0);
                        m_events.ScheduleEvent(EVENT_TALK_3, 8000);
                        break;
                    }
                    case EVENT_TALK_3:
                    {
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            warhowl->AI()->Talk(1);
                        m_events.ScheduleEvent(EVENT_TALK_4, 11000);
                        break;
                    }
                    case EVENT_TALK_4:
                    {
                        Talk(1);
                        m_events.ScheduleEvent(EVENT_TALK_5, 14000);
                        break;
                    }
                    case EVENT_TALK_5:
                    {
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            warhowl->AI()->Talk(2);
                        m_events.ScheduleEvent(EVENT_TALK_6, 8000);
                        break;
                    }
                    case EVENT_TALK_6:
                    {
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            warhowl->GetMotionMaster()->MovePoint(2010, -1566.053f, 1557.191f, 29.36808f);
                        Talk(2);
                        m_events.ScheduleEvent(EVENT_DESPAWN_WARHOWL, 8000);
                        m_events.ScheduleEvent(EVENT_TALK_7, 5000);
                        break;
                    }
                    case EVENT_TALK_7:
                    {
                        if (Creature* crenshaw = ObjectAccessor::GetCreature(*me, m_crenshawGUID))
                        {
                            crenshaw->AI()->Talk(0);
                            me->SetFacingToObject(crenshaw);
                        }
                        m_events.ScheduleEvent(EVENT_TALK_8, 10000);
                        break;
                    }
                    case EVENT_TALK_8:
                    {
                        Talk(3);
                        m_events.ScheduleEvent(EVENT_END, 8000);
                        break;
                    }
                    case EVENT_END:
                    {
                        if (m_completionHandled)
                            break;
                        Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                        if (!player || !player->IsAlive() || !me->IsInPhase(player)
                            || player->GetMapId() != me->GetMapId())
                            break;
                        if (player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_INCOMPLETE
                            && player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_COMPLETE)
                            break;
                        if (player->GetDistance2d(me) > 50.0f)
                        {
                            m_events.RescheduleEvent(EVENT_END, 1000);
                            break;
                        }
                        Creature* tobias = ObjectAccessor::GetCreature(*me, m_tobiasGUID);
                        if (!tobias || !tobias->IsAlive() || tobias->GetEntry() != NPC_TOBIAS_MISTMANTLE
                            || tobias->GetMapId() != me->GetMapId() || !tobias->IsInPhase(player)
                            || tobias->AI()->GetGUID(PLAYER_GUID) != m_playerGUID)
                        {
                            TC_LOG_ERROR("scripts", "Gilneas 24902: final dialogue cannot credit its owner because Tobias is absent, invalid or owned by another player.");
                            break;
                        }
                        player->AreaExploredOrEventHappens(QUEST_HUNT_FOR_SYLVANAS);
                        player->KilledMonsterCredit(38530);
                        if (player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS) != QUEST_STATUS_COMPLETE)
                        {
                            TC_LOG_ERROR("scripts", "Gilneas 24902: final dialogue finished but event credit failed; questStatus=%u. Scene departure cancelled.", uint32(player->GetQuestStatus(QUEST_HUNT_FOR_SYLVANAS)));
                            break;
                        }
                        m_completionHandled = true;
                        if (Creature* crenshaw = ObjectAccessor::GetCreature(*me, m_crenshawGUID))
                            crenshaw->GetMotionMaster()->MovePoint(2010, -1566.053f, 1557.191f, 29.36808f);
                        me->GetMotionMaster()->MovePoint(2010, -1566.053f, 1557.191f, 29.36808f);
                        m_events.ScheduleEvent(EVENT_DESPAWN, 8000);
                        break;
                    }
                    case EVENT_DESPAWN_WARHOWL:
                    {
                        if (Creature* warhowl = ObjectAccessor::GetCreature(*me, m_warhowlGUID))
                            warhowl->DespawnOrUnsummon(10);
                        break;
                    }
                    case EVENT_DESPAWN:
                    {
                        if (Creature* crenshaw = ObjectAccessor::GetCreature(*me, m_crenshawGUID))
                            crenshaw->DespawnOrUnsummon(10);
                        if (Creature* tobias = ObjectAccessor::GetCreature(*me, m_tobiasGUID))
                            tobias->DespawnOrUnsummon(10);
                        me->DespawnOrUnsummon(10);
                        break;
                    }
                }
            }

            if (!UpdateVictim())
                return;

            DoMeleeAttackIfReady();
        }
    };

    CreatureAI* GetAI(Creature* pCreature) const override
    {
        return new npc_lady_sylvanas_windrunner_38530AI(pCreature);
    }
};

// 38540
class npc_captured_riding_bat_38540 : public CreatureScript
{
public:
    npc_captured_riding_bat_38540() : CreatureScript("npc_captured_riding_bat_38540") { }

    struct npc_captured_riding_bat_38540AI : public ScriptedAI
    {
        npc_captured_riding_bat_38540AI(Creature* creature) : ScriptedAI(creature), m_playerGUID(ObjectGuid::Empty) { }

        ObjectGuid m_playerGUID;
        uint32 m_lifetime = 0;
        uint8 m_flightState = 0; //0 waiting,1 circuit,3 return,4 landed
        bool m_boarded = false;
        uint32 m_nextBoardAttempt = 500;

        void OnCharmed(bool /*apply*/) override { } // Keep the scripted flight AI for the vehicle owner.
        void AttackStart(Unit* /*who*/) override { }
        void EnterCombat(Unit* /*who*/) override { }
        void EnterEvadeMode(EvadeReason /*reason*/) override { }
        void Reset() override { me->SetReactState(REACT_PASSIVE); }
        ObjectGuid GetGUID(int32 id) const override
        {
            return id == PLAYER_GUID ? m_playerGUID : ObjectGuid::Empty;
        }

        bool HasFlightPaths() const
        {
            uint32 const paths[] = {3854001, 3854003};
            uint32 const endpoints[] = {60, 14};
            for (uint32 i = 0; i < 2; ++i)
            {
                WaypointPath const* path = sWaypointMgr->GetPath(paths[i]);
                if (!path || path->nodes.size() < 2 || path->nodes.back().id != endpoints[i])
                    return false;
                uint32 previousId = 0;
                bool first = true;
                for (WaypointNode const& node : path->nodes)
                {
                    if (!std::isfinite(node.x) || !std::isfinite(node.y) || !std::isfinite(node.z)
                        || (!first && node.id <= previousId))
                        return false;
                    previousId = node.id;
                    first = false;
                }
            }
            return true;
        }

        void IsSummonedBy(Unit* summoner) override
        {
            if (!m_playerGUID.IsEmpty())
                return;
            Player* player = summoner ? summoner->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || me->GetMapId() != 654 || player->GetMapId() != 654
                || !me->IsInPhase(player)
                || player->GetQuestStatus(24920) != QUEST_STATUS_INCOMPLETE)
            {
                me->DespawnOrUnsummon();
                return;
            }
            if (!HasFlightPaths())
            {
                TC_LOG_ERROR("sql.sql", "Gilneas quest24920: invalid bat flight/return paths3854001/3854003; boarding skipped");
                me->DespawnOrUnsummon();
                return;
            }
            if (!me->GetVehicleKit())
            {
                TC_LOG_ERROR("sql.sql", "Gilneas quest24920: bat38540 has no vehicle kit; check VehicleId641");
                me->DespawnOrUnsummon();
                return;
            }
            m_playerGUID = player->GetGUID();
            me->setActive(true);
            // Boarding casts another spell; wait until the summon cast has finished.
        }

        void DoAction(int32 action) override
        {
            if (action != 1 || m_flightState != 1 || !m_boarded)
                return;
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            if (!player || !player->IsAlive() || player->GetVehicleBase() != me)
                return;
            m_flightState = 3;
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MovePath(3854003, false);
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type != WAYPOINT_MOTION_TYPE || !m_boarded)
                return;
            // Callbacks carry zero-based indices: SQL point60/14 is index59/13.
            if ((m_flightState == 1 && id == 59) || (m_flightState == 3 && id == 13))
            {
                m_flightState = 4;
                me->SetDisableGravity(false);
                if (Vehicle* vehicle = me->GetVehicleKit())
                    vehicle->RemoveAllPassengers();
                m_boarded = false;
                me->DespawnOrUnsummon(100ms);
            }
        }

        void PassengerBoarded(Unit* passenger, int8 seatId, bool apply) override
        {
            Player* player = passenger ? passenger->ToPlayer() : nullptr;
            if (apply)
            {
                if (m_boarded && player && seatId == 0 && player->GetGUID() == m_playerGUID)
                    return;
                if (!player || !player->IsAlive() || seatId != 0 || m_boarded
                    || player->GetGUID() != m_playerGUID || player->GetMapId() != 654
                    || !me->IsInPhase(player) || !HasFlightPaths()
                    || player->GetQuestStatus(24920) != QUEST_STATUS_INCOMPLETE)
                {
                    if (passenger)
                        passenger->ExitVehicle();
                    return;
                }
                m_boarded = true;
                m_flightState = 1;
                me->SetCanFly(true);
                me->SetDisableGravity(true);
                me->SetSpeedRate(MOVE_FLIGHT, 2.0f);
                me->GetMotionMaster()->MovePath(3854001, false);
            }
            else if (player && player->GetGUID() == m_playerGUID)
            {
                m_boarded = false;
                me->DespawnOrUnsummon(100ms);
            }
        }

        void UpdateAI(uint32 diff) override
        {
            // The summon factory can overwrite the type after IsSummonedBy.
            if (!m_playerGUID.IsEmpty())
                if (TempSummon* summon = me->ToTempSummon())
                    summon->SetTempSummonType(TEMPSUMMON_MANUAL_DESPAWN);
            m_lifetime += diff;
            if (m_lifetime >= 10000 && m_flightState == 0)
            {
                TC_LOG_ERROR("scripts", "Gilneas quest24920: personal bat boarding timed out after ten seconds; check vehicle641 seat0 and ride spell46598");
                me->DespawnOrUnsummon();
                return;
            }
            Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || (m_boarded && player->GetVehicleBase() != me))
            {
                me->DespawnOrUnsummon();
                return;
            }
            if (m_flightState == 0 && !m_boarded && m_lifetime >= m_nextBoardAttempt)
            {
                if (player->GetVehicleBase() && player->GetVehicleBase() != me)
                {
                    me->DespawnOrUnsummon();
                    return;
                }
                if (player->GetQuestStatus(24920) != QUEST_STATUS_INCOMPLETE
                    || !me->IsInPhase(player) || !HasFlightPaths())
                {
                    me->DespawnOrUnsummon();
                    return;
                }
                m_nextBoardAttempt = m_lifetime + 1000;
                if (!player->GetVehicleBase())
                    player->EnterVehicle(me, 0);
            }
            QuestStatus status = player->GetQuestStatus(24920);
            if (m_lifetime >= 900000 || !me->InSamePhase(player->GetPhaseShift())
                || (status != QUEST_STATUS_INCOMPLETE && status != QUEST_STATUS_COMPLETE))
                DoAction(1); // Abandon returns a living rider along the real route.
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_captured_riding_bat_38540AI(creature);
    }
};

class spell_gilneas_captured_bat_summon : public SpellScriptLoader
{
public:
    spell_gilneas_captured_bat_summon() : SpellScriptLoader("spell_gilneas_captured_bat_summon") { }
    class script : public SpellScript
    {
        PrepareSpellScript(script);
        SpellCastResult CheckBat()
        {
            Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
            if (!player || !player->IsAlive() || player->GetMapId() != 654
                || player->GetQuestStatus(24920) != QUEST_STATUS_INCOMPLETE
                || player->GetSummonedCreatureByEntry(38540) || player->GetVehicleBase())
                return SPELL_FAILED_BAD_TARGETS;
            Creature* source = player->FindNearestCreature(38615, 15.0f);
            return source && source->InSamePhase(player->GetPhaseShift()) ? SPELL_CAST_OK : SPELL_FAILED_BAD_TARGETS;
        }
        void Register() override
        {
            OnCheckCast += SpellCheckCastFn(script::CheckBat);
        }
    };
    SpellScript* GetSpellScript() const override { return new script(); }
};

// 72849
class spell_fly_back_72849 : public SpellScriptLoader
{
public:
    spell_fly_back_72849() : SpellScriptLoader("spell_fly_back_72849") { }

    class spell_fly_back_72849_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_fly_back_72849_SpellScript);

        void HandleDummy(SpellEffIndex /*effindex*/)
        {
            Unit* caster = GetCaster();
            if (!caster)
                return;
            Creature* bat = caster->ToCreature();
            if (Player* player = caster->ToPlayer())
            {
                Unit* vehicle = player->GetVehicleBase();
                bat = vehicle ? vehicle->ToCreature() : nullptr;
                if (!bat || bat->AI()->GetGUID(PLAYER_GUID) != player->GetGUID())
                    return;
            }
            if (bat && bat->GetEntry() == 38540 && bat->GetMapId() == 654)
                bat->AI()->DoAction(1);
        }

        void Register() override
        {
            OnEffectHitTarget += SpellEffectFn(spell_fly_back_72849_SpellScript::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_fly_back_72849_SpellScript();
    }
};

// 72247
class spell_iron_bomb_72247 : public SpellScriptLoader
{
public:
    spell_iron_bomb_72247() : SpellScriptLoader("spell_iron_bomb_72247") { }

    class IsFriendly
    {
    public:
        IsFriendly(Unit* caster) : _caster(caster) { }

        bool operator()(WorldObject* object) const
        {
            if (Unit* unit = object->ToUnit())
                return _caster->IsFriendlyTo(unit);
            return true;
        }

    private:
        Unit* _caster;
    };

    class spell_iron_bomb_72247_SpellScript : public SpellScript
    {
        PrepareSpellScript(spell_iron_bomb_72247_SpellScript);

        void FilterTargets(std::list<WorldObject*>& targets)
        {
            targets.remove_if(IsFriendly(GetCaster()));
        }

        void Register() override
        {
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_iron_bomb_72247_SpellScript::FilterTargets, EFFECT_0, TARGET_UNIT_DEST_AREA_ENTRY);
        }
    };

    SpellScript* GetSpellScript() const override
    {
        return new spell_iron_bomb_72247_SpellScript();
    }
};

// the endgame is in phase 191

enum eEndGame
{
    ACTION_EVENT_ID_25663 = 25663, // leave the ship
    ACTION_EVENT_ID_25664 = 25664, // ship start movening
    ACTION_EVENT_ID_25670 = 25670, // ship spawn
    ACTION_EVENT_ID_25727 = 25727, // ship on destroy

    EVENT_MAKE_SHOWFIGHT = 301,
    EVENT_START_SHOWFIGHT,
    EVENT_FLOOR_IS_ONE_REMAIN,
    EVENT_FLOOR_IS_CLEAN,
    EVENT_START_ROPE_PART,
};

// 43749
class npc_tobias_mistmantle_43749 : public CreatureScript
{
public:
    npc_tobias_mistmantle_43749() : CreatureScript("npc_tobias_mistmantle_43749") { }

    struct npc_tobias_mistmantle_43749AI : public ScriptedAI
    {
        npc_tobias_mistmantle_43749AI(Creature* creature) : ScriptedAI(creature) { Initialize(); }

        EventMap m_events;
        ObjectGuid   m_gunshipGUID;
        uint32   m_gunshipEventId;
        bool m_boardingAllowed = false;
        uint32 m_readinessReportCooldown = 0;
        std::list<ObjectGuid> m_hippoList;

        void Initialize()
        {
            m_gunshipGUID = ObjectGuid::Empty;
            m_gunshipEventId = 0;
            m_events.ScheduleEvent(EVENT_INIT_TARGET, 1000);
        }

        uint32 GetData(uint32 id) const override
        {
            if (id != QUEST_ENDGAME || !m_boardingAllowed)
                return 0;
            GameObject* ship = ObjectAccessor::GetGameObject(*me, m_gunshipGUID);
            return ship && ship->AI() && ship->AI()->GetData(QUEST_ENDGAME) ? 1 : 0;
        }

        void DoAction(int32 param) override
        {
            switch (param)
            {
            case ACTION_EVENT_ID_25670: // arrival at the three-minute boarding stop
                m_events.Reset();
                m_events.RescheduleEvent(EVENT_INIT_TARGET, 1000);
                m_events.RescheduleEvent(EVENT_TALK_PART_00, 10);
                break;
            case ACTION_EVENT_ID_25663:
            case ACTION_EVENT_ID_25664:
            case ACTION_EVENT_ID_25727:
                m_events.Reset();
                m_events.RescheduleEvent(EVENT_INIT_TARGET, 1000);
                m_events.RescheduleEvent(EVENT_TALK_PART_02, 10);
                break;
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_readinessReportCooldown = diff >= m_readinessReportCooldown ? 0 : m_readinessReportCooldown - diff;
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_INIT_TARGET:
                {
                    if (!m_gunshipGUID)
                        FindWorgenGunshipWorldwide();

                    if (GameObject* ship = ObjectAccessor::GetGameObject(*me, m_gunshipGUID))
                    {
                        m_gunshipGUID = ship->GetGUID();
                        ship->AI()->SetGUID(me->GetGUID(), me->GetEntry());
                        bool ready = CheckPlayerForQuest() && CheckIsGunshipReady();
                        SetHippoSpellClick(ready);
                        if (ready != m_boardingAllowed)
                        {
                            m_boardingAllowed = ready;
                            Talk(ready ? 1 : 0);
                        }
                    }
                    m_events.ScheduleEvent(EVENT_INIT_TARGET, 1000);
                    break;
                }
                case EVENT_TALK_PART_02:
                case EVENT_TALK_PART_03:
                case EVENT_TALK_PART_04:
                {
                    Talk(0);
                    SetHippoSpellClick(false);
                    break;
                }
                case EVENT_TALK_PART_00:
                {
                    if (CheckPlayerForQuest() && CheckIsGunshipReady())
                    {
                        SetHippoSpellClick(true);
                        Talk(1);
                    }
                    else
                    {
                        SetHippoSpellClick(false);
                        Talk(0);
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

        void FindNearestHippogryphs()
        {
            m_hippoList.clear();
            std::list<Creature*> hippoList = me->FindNearestCreatures(NPC_HIPPOGRYPH, 25.0f);
            for (std::list<Creature*>::iterator itr = hippoList.begin(); itr != hippoList.end(); ++itr)
                m_hippoList.push_back((*itr)->GetGUID());
        }

        void SetHippoSpellClick(bool value)
        {
            // Respawned birds can have new runtime GUIDs; refresh for every departure window.
            FindNearestHippogryphs();

            for (std::list<ObjectGuid>::iterator itr = m_hippoList.begin(); itr != m_hippoList.end(); ++itr)
                if (Creature* hippo = ObjectAccessor::GetCreature(*me, (*itr)))
                {
                    if (value)
                        hippo->SetFlag(UNIT_NPC_FLAGS, UNIT_NPC_FLAG_SPELLCLICK);
                    else
                        hippo->RemoveFlag(UNIT_NPC_FLAGS, UNIT_NPC_FLAG_SPELLCLICK);
                }
        }

        bool CheckPlayerForQuest()
        {
            std::list<Player*> playerList = me->SelectNearestPlayers(25.0f);
            for (std::list<Player*>::iterator itr = playerList.begin(); itr != playerList.end(); ++itr)
                if ((*itr)->GetQuestStatus(QUEST_ENDGAME) == QUEST_STATUS_INCOMPLETE)
                    return true;
            return false;
        }

        class GunshipSearchWorker
        {
        public:
            GunshipSearchWorker(ObjectGuid* gunshipGuid) : m_gunshipGuid(gunshipGuid) { }

            void Visit(std::unordered_map<ObjectGuid, GameObject*>& gameObjectMap)
            {
                for (auto const& p : gameObjectMap)
                    if (p.second->IsInWorld() && p.second->GetEntry() == GO_WORGEN_GUNSHIP)
                        *m_gunshipGuid = p.first;
            }

            template<class T>
            void Visit(std::unordered_map<ObjectGuid, T*>&) { }
        private:
            ObjectGuid* m_gunshipGuid;
        };

        void FindWorgenGunshipWorldwide()
        {
            GunshipSearchWorker worker(&m_gunshipGUID);
            TypeContainerVisitor<GunshipSearchWorker, MapStoredObjectTypesContainer> visitor(worker);
            visitor.Visit(me->GetMap()->GetObjectsStore());
        }

        bool CheckIsGunshipReady()
        {
            GameObject* ship = ObjectAccessor::GetGameObject(*me, m_gunshipGUID);
            Transport* transport = ship ? ship->ToTransport() : nullptr;
            if (!transport || transport->GetMapId() != 654 || !ship->AI()
                || !ship->AI()->GetData(QUEST_ENDGAME))
            {
                if (!m_readinessReportCooldown)
                {
                    TC_LOG_INFO("scripts", "Gilneas26706 readiness: ship=%u boarding_window=%u map=%u position=(%.2f,%.2f,%.2f) timer=%u period=%u; waiting for rendezvous",
                        uint32(transport != nullptr), uint32(ship && ship->AI() && ship->AI()->GetData(QUEST_ENDGAME)),
                        transport ? transport->GetMapId() : 0, transport ? transport->GetPositionX() : 0.0f,
                        transport ? transport->GetPositionY() : 0.0f, transport ? transport->GetPositionZ() : 0.0f,
                        transport ? transport->GetTimer() : 0, transport ? transport->GetTransportPeriod() : 0);
                    if (transport)
                        for (KeyFrame const& frame : transport->GetKeyFrames())
                            if (frame.Node->ArrivalEventID == ACTION_EVENT_ID_25670)
                                TC_LOG_INFO("scripts", "Gilneas26706 dock frame: arrival_ms=%u departure_ms=%u map=%u position=(%.2f,%.2f,%.2f)",
                                    frame.ArriveTime, frame.DepartureTime, uint32(frame.Node->ContinentID),
                                    frame.Node->Loc.X, frame.Node->Loc.Y, frame.Node->Loc.Z);
                    m_readinessReportCooldown = 30000;
                }
                return false;
            }

            // Transport passenger loading follows grid activation. The harbor NPC can
            // register after arrival, or before the distant ship grid has been visited.
            transport->GetMap()->LoadGrid(transport->GetPositionX(), transport->GetPositionY());
            if (transport->GetStaticPassengers().empty())
                transport->LoadStaticPassengers();

            uint32 lorna = 0, warriors = 0, shooters = 0, grunts = 0, anchors = 0, ropes = 0;
            for (WorldObject* passenger : transport->GetStaticPassengers())
            {
                if (Creature* npc = passenger->ToCreature())
                {
                    if (npc->GetTransport() != transport
                        || (!npc->IsAlive() && npc->GetEntry() != NPC_GUNSHIP_GRUNT))
                        continue;
                    switch (npc->GetEntry())
                    {
                        case NPC_LORNA_CRAWLEY_43566: if (npc->IsAIEnabled && npc->AI()) ++lorna; break;
                        case NPC_WORGEN_WARRIOR: ++warriors; break;
                        case NPC_GILNEAN_SHARPSHOOTER: ++shooters; break;
                        case NPC_GUNSHIP_GRUNT: ++grunts; break;
                        case NPC_GILNEAS_VEHICLE_ROPE: ++anchors; break;
                    }
                }
                else if (GameObject* object = passenger->ToGameObject())
                    if (object->GetEntry() == GO_ROPE && object->GetTransport() == transport)
                        ++ropes;
            }
            bool ready = lorna == 1 && warriors >= 4 && shooters >= 4 && grunts >= 22
                && anchors >= 15 && ropes >= 2;
            if (!m_readinessReportCooldown)
            {
                TC_LOG_INFO("scripts", "Gilneas26706 readiness: Lorna=%u warriors=%u shooters=%u grunts=%u rope_anchors=%u ropes=%u ready=%u",
                    lorna, warriors, shooters, grunts, anchors, ropes, uint32(ready));
                m_readinessReportCooldown = 30000;
            }
            return ready;
        }

    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_tobias_mistmantle_43749AI(creature);
    }
};

// Spellclick must not bypass the ship window, even when a stale client cursor remains.
class spell_gilneas_endgame_hippogryph : public SpellScript
{
    PrepareSpellScript(spell_gilneas_endgame_hippogryph);

    SpellCastResult CheckBoarding()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || !player->IsAlive() || player->GetMapId() != 654
            || player->GetVehicleBase()
            || player->GetQuestStatus(QUEST_ENDGAME) != QUEST_STATUS_INCOMPLETE)
            return SPELL_FAILED_BAD_TARGETS;
        Creature* tobias = player->FindNearestCreature(NPC_TOBIAS_MISTMANTLE_43749, 25.0f);
        if (!tobias || !tobias->IsAIEnabled || !tobias->AI()
            || !tobias->AI()->GetData(QUEST_ENDGAME))
            return SPELL_FAILED_NOT_READY;
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_gilneas_endgame_hippogryph::CheckBoarding);
    }
};

// 43751
class npc_hippogryph_43751 : public CreatureScript
{
public:
    npc_hippogryph_43751() : CreatureScript("npc_hippogryph_43751") { }

    enum eNpc
    {
        EVENT_MOVE_LAST_POINT=201,
        EVENT_EJECT_ALL_PASSENGER,
        EVENT_JUMP_TO_LORNA,
    };

    struct npc_hippogryph_43751AI : public ScriptedAI
    {
        npc_hippogryph_43751AI(Creature* creature) : ScriptedAI(creature) {}

        EventMap m_events;
        ObjectGuid m_playerGUID;
        ObjectGuid m_lornaGUID;
        float  m_cruiseSpeedRate;
        bool m_boarded = false;
        bool m_finished = false;

        // Retain route and owner state when vehicle boarding charms this creature.
        void OnCharmed(bool /*apply*/) override { }

        void Reset() override
        {
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
            m_lornaGUID = ObjectGuid::Empty;
            m_cruiseSpeedRate = 3.0f;
            m_boarded = false;
            m_finished = false;
            if (Creature* wy = me->FindNearestCreature(43747, 10.0f))
                me->SetOrientation(wy->GetOrientation());
        }

        void SetFlightSpeedRate(float rate)
        {
            // Waypoint splines select run or flight speed from the current movement flags.
            me->SetSpeedRate(MOVE_RUN, rate);
            me->SetSpeedRate(MOVE_FLIGHT, rate);
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (!m_boarded || m_finished)
                return;
            switch (type)
            {
                case WAYPOINT_MOTION_TYPE:
                {
                    if (id == 2)
                        SetFlightSpeedRate(m_cruiseSpeedRate);
                    else if (id == 6)
                        SetFlightSpeedRate(1.0f);
                    else if (id == 7)
                        m_events.ScheduleEvent(EVENT_MOVE_LAST_POINT, 10);
                    break;
                }
                case POINT_MOTION_TYPE:
                {
                    switch (id)
                    {
                    case 1002:
                        m_events.ScheduleEvent(EVENT_JUMP_TO_LORNA, 10);
                        break;
                    }
                }
            } // end switch
        }

        void FinishRide()
        {
            if (m_finished)
                return;
            m_finished = true;
            m_boarded = false;
            m_events.Reset();
            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                if (player->GetVehicleBase() == me)
                    player->ExitVehicle();
            me->DespawnOrUnsummon(100ms);
        }

        void JustDied(Unit* /*killer*/) override { FinishRide(); }

        void PassengerBoarded(Unit* who, int8 /*seatId*/, bool apply) override
        {
            Player* player = who ? who->ToPlayer() : nullptr;
            // Accessory callbacks must not destroy another player's transport.
            if (!player)
                return;
            if (!apply)
            {
                if (player->GetGUID() == m_playerGUID)
                    FinishRide();
                return;
            }
            if (m_finished || !player->IsAlive() || player->GetMapId() != 654
                || me->GetMapId() != 654 || !me->IsInPhase(player)
                || player->GetQuestStatus(QUEST_ENDGAME) != QUEST_STATUS_INCOMPLETE
                || (!m_playerGUID.IsEmpty() && player->GetGUID() != m_playerGUID))
            {
                player->ExitVehicle();
                return;
            }
            if (m_boarded)
                return;
            m_playerGUID = player->GetGUID();
            m_boarded = true;
            m_events.RescheduleEvent(EVENT_MOVEMENT_START, 1000);
        }

        void UpdateAI(uint32 diff) override
        {
            if (m_finished)
                return;
            if (m_boarded)
            {
                Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                if (!player || !player->IsAlive() || player->GetMapId() != 654
                    || !me->IsInPhase(player) || player->GetVehicleBase() != me
                    || player->GetQuestStatus(QUEST_ENDGAME) != QUEST_STATUS_INCOMPLETE)
                {
                    FinishRide();
                    return;
                }
            }
            ScriptedAI::UpdateAI(diff);
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_MOVEMENT_START:
                {
                    me->SetCanFly(true);
                    me->SetDisableGravity(true);
                    SetFlightSpeedRate(2.0f);
                    me->GetMotionMaster()->MovePath(4375101, false);
                    break;
                }
                case EVENT_MOVE_LAST_POINT:
                {
                    FindLornaGuid();
                    if (Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID))
                    {
                        Position pos = lorna->GetPosition();
                        pos.m_positionZ += 15.0f;
                        me->GetMotionMaster()->MovePoint(1002, pos);
                    }
                    break;
                }
                case EVENT_JUMP_TO_LORNA:
                {
                    if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        if (Creature* lorna = ObjectAccessor::GetCreature(*me, m_lornaGUID))
                        {
                            lorna->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                            player->ExitVehicle();
                            lorna->AI()->DoAction(EVENT_TELEPORT_01);
                        }

                    me->DespawnOrUnsummon(100);
                    break;
                }
                }
            }
        }

        void FindLornaGuid()
        {
            if (ObjectAccessor::GetCreature(*me, m_lornaGUID))
                return;

            if (Creature* lorna = me->FindNearestCreature(NPC_LORNA_CRAWLEY_43566, 100.0f))
                m_lornaGUID = lorna->GetGUID();
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_hippogryph_43751AI(creature);
    }
};

// GO 203428
class go_worgen_gunship_203428 : public GameObjectScript
{
public:
    go_worgen_gunship_203428() : GameObjectScript("go_worgen_gunship_203428") { }

    enum eObject
    {
        EVENT_CHECK_POSITIONS = 201,
    };

    struct go_worgen_gunship_203428AI : public GameObjectAI
    {
        go_worgen_gunship_203428AI(GameObject* gameobject) : GameObjectAI(gameobject) { }

        EventMap m_events;
        ObjectGuid   m_tobiasGUID;
        ObjectGuid   m_playerGUID;
        ObjectGuid   m_triggerGUID;
        bool m_boardingWindow = false;

        void Reset() override
        {
            m_tobiasGUID = ObjectGuid::Empty;
            m_playerGUID = ObjectGuid::Empty;
            m_triggerGUID = ObjectGuid::Empty;
            m_events.RescheduleEvent(EVENT_CHECK_POSITIONS, 2500);
        }

        uint32 GetData(uint32 id) const override
        {
            if (id != QUEST_ENDGAME)
                return 0;
            Transport* transport = go->ToTransport();
            if (!transport || !transport->GetTransportPeriod())
                return 0;
            uint32 timer = transport->GetTimer() % transport->GetTransportPeriod();
            for (KeyFrame const& frame : transport->GetKeyFrames())
                if (frame.Node->ArrivalEventID == ACTION_EVENT_ID_25670
                    && timer >= frame.ArriveTime && timer < frame.DepartureTime)
                    // The bird needs about ninety seconds, plus handoff/retry margin.
                    return frame.DepartureTime - timer >= 120000 ? 1 : 0;
            return 0;
        }

        void EventInform(uint32 eventId) override
        {
            if (eventId == ACTION_EVENT_ID_25670)
                m_boardingWindow = true;
            else if (eventId == ACTION_EVENT_ID_25664 || eventId == ACTION_EVENT_ID_25663
                || eventId == ACTION_EVENT_ID_25727)
                m_boardingWindow = false;
            if (Creature* tobias = ObjectAccessor::GetCreature(*go, m_tobiasGUID))
                tobias->AI()->DoAction(eventId);

            if (Creature* trigger = ObjectAccessor::GetCreature(*go, m_triggerGUID))
                trigger->AI()->DoAction(eventId);

            if (eventId == ACTION_EVENT_ID_25727) // ship is on destroy.. we must leave quickly.. or player char is destroyed in database storing..
            {
                WorldLocation wLoc = WorldLocation(654, -1317.54f, 2121.90f, 5.6296f, 0.218f);
                std::list<Player*> pList = go->SelectNearestPlayers(70.0f);
                for (auto player : pList)
                    player->TeleportTo(wLoc);
            }
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            switch (id)
            {
                case NPC_TOBIAS_MISTMANTLE_43749:
                    if (m_tobiasGUID != guid)
                    {
                        m_tobiasGUID = guid;
                        if (Creature* tobias = ObjectAccessor::GetCreature(*go, guid))
                            tobias->AI()->DoAction(GetData(QUEST_ENDGAME) ? ACTION_EVENT_ID_25670 : ACTION_EVENT_ID_25664);
                    }
                    break;
            }
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_CHECK_POSITIONS:
                {
                    if (!m_playerGUID)
                        if (Player* player = go->SelectNearestPlayer(100.0f))
                            m_playerGUID = player->GetGUID();

                    if (!m_triggerGUID)
                        if (Creature* trigger = go->FindNearestCreature(40350, 100.0f))
                            m_triggerGUID = trigger->GetGUID();

                     m_events.ScheduleEvent(EVENT_CHECK_POSITIONS, 2500);
                    break;
                }
                }
            }
        }
    };

    GameObjectAI* GetAI(GameObject* gameobject) const override
    {
        return new go_worgen_gunship_203428AI(gameobject);
    }
};

// 43566
class npc_lorna_crowley_43566 : public CreatureScript
{
public:
    npc_lorna_crowley_43566() : CreatureScript("npc_lorna_crowley_43566") { }

    struct npc_lorna_crowley_43566AI : public ScriptedAI
    {
        npc_lorna_crowley_43566AI(Creature* creature) : ScriptedAI(creature) { Initialize(); }

        EventMap  m_events;
        ObjectGuid    m_bigOrcGUID;
        ObjectGuid    m_playerGUID;
        bool      m_animStarted;
        uint32    m_wp_point;
        std::list<ObjectGuid> pList;
        std::list<ObjectGuid> wList;

        void Initialize()
        {
            m_bigOrcGUID = ObjectGuid::Empty;
            m_playerGUID = ObjectGuid::Empty;
            m_wp_point = 0;
        }

        void Reset() override
        {
            me->SetReactState(REACT_DEFENSIVE);
            m_animStarted = false;
            me->AddAura(SPELL_FOR_GILNEAS, me);
            SetRopeSelectableFlag(false);
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1000);
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage) override
        {
            damage = 0;
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

        bool CanJoinEscape(Player* player) const
        {
            return player && player->IsAlive() && me->GetMapId() == 654
                && player->GetMapId() == me->GetMapId() && me->IsInPhase(player)
                && me->GetTransport() && player->GetTransport() == me->GetTransport()
                && !player->GetVehicleBase()
                && player->GetQuestStatus(QUEST_ENDGAME) == QUEST_STATUS_INCOMPLETE;
        }

        void DoAction(int32 param) override
        {
            switch (param)
            {
                case EVENT_TELEPORT_01:
                {
                    if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                        if (!me->GetTransGUID().IsEmpty())
                        {
                            pList.push_back(player->GetGUID());
                            if (!m_animStarted)
                            {
                                m_animStarted = true;
                                m_events.RescheduleEvent(EVENT_ANIMATION_START, 100);
                            }
                        }
                    break;
                }
            }
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (type == WAYPOINT_MOTION_TYPE)
                switch (m_wp_point)
                {
                    case 1:
                    {
                        if (id == 4)
                            m_events.ScheduleEvent(EVENT_TALK_PART_01, 1000);
                        break;
                    }
                    case 2:
                    {
                        if (id == 10)
                            m_events.ScheduleEvent(EVENT_TALK_PART_04, 1000);
                        break;
                    }
                    case 3:
                    {
                        if (id == 2)
                            m_events.ScheduleEvent(EVENT_TALK_PART_05, 1000);
                        break;
                    }
                    case 4:
                    {
                        if (id == 2)
                            m_events.ScheduleEvent(EVENT_TALK_PART_06, 1000);
                        break;
                    }
                    case 5:
                    {
                        if (id == 2)
                            m_events.ScheduleEvent(EVENT_TALK_PART_07, 1000);
                        break;
                    }
                    case 6:
                    {
                        if (id == 1)
                            m_events.ScheduleEvent(EVENT_TALK_PART_09, 1000);
                        break;
                    }
                    case 7:
                    {
                        if (id == 1)
                            m_events.ScheduleEvent(EVENT_TALK_PART_10, 1000);
                        break;
                    }
                }
        }

        void EnterEvadeMode(EvadeReason /*reason*/) override
        {
            me->CombatStop(true);
            me->SetReactState(REACT_DEFENSIVE);

            if (me->GetTransport())
                me->SetTransportHomePosition(me->GetTransport()->GetPosition());
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            if (m_animStarted && pList.size())
                for (auto guid : pList)
                    if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                    {
                        if (me->GetTransport())
                        {
                            Position pos = me->GetTransport()->GetPosition();
                            player->MovePosition(pos, 0, 0);
                        }
                        pList.remove(guid);
                        break;
                    }

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_CHECK_ATTACK:
                {
                    if (!me->IsInCombat())
                        if (Creature* target = me->FindNearestCreatureOnTransportInFloor(42141, 30.0f, 3.0f))
                        {
                            if (me->GetTransport())
                            {
                                float dist = me->GetTransOffset().GetExactDist2d(&target->GetTransOffset());
                                if (dist < 5.0f)
                                {
                                    me->CastSpell(target, 15496, true);
                                    me->Attack(target, true);
                                }
                                else
                                {
                                    me->CastSpell(target, 31942, true);
                                    m_events.ScheduleEvent(EVENT_CAST_COOLDOWN, 2000);
                                }
                            }
                        }

                    m_events.ScheduleEvent(EVENT_CHECK_ATTACK, urand(1500, 1600));
                    break;
                }
                case EVENT_CAST_COOLDOWN:
                {
                    me->CombatStop(true);
                    break;
                }
                case EVENT_ANIMATION_START:
                {
                    Talk(0);
                    m_events.RescheduleEvent(EVENT_FLOOR_IS_ONE_REMAIN, 3000);
                    break;
                }
                case EVENT_FLOOR_IS_ONE_REMAIN:
                {
                    uint32 count = CountGruntOnThisFloorZ(86.0f, 15.0f);
                    if (count < 2)
                    {
                        Talk(1);
                        m_events.ScheduleEvent(EVENT_FLOOR_IS_CLEAN, 5000);
                    }
                    else
                        m_events.ScheduleEvent(EVENT_FLOOR_IS_ONE_REMAIN, 1000);

                    break;
                }
                case EVENT_FLOOR_IS_CLEAN:
                {
                    uint32 count = CountGruntOnThisFloorZ(86.0f, 15.0f);
                    if (!count)
                    {
                        Talk(2);
                        m_events.ScheduleEvent(EVENT_START_ROPE_PART, 7000);
                    }
                    else
                        m_events.ScheduleEvent(EVENT_FLOOR_IS_CLEAN, 1000);
                    break;
                }
                case EVENT_START_ROPE_PART:
                {
                    SetRopeSelectableFlag(true);
                    std::vector<Creature*> friendsList = FindFriendlyCreatureList();
                    std::vector<Creature*> jumpTargetList = FindJumpTargetPositions(34.0f);
                    for (auto source : friendsList)
                        if (Creature* target = FindBestJumpTarget(source, 34.0f, jumpTargetList))
                        {
                            source->SetTransportHomePosition(target->GetTransOffset());
                            source->JumpTo(target, 0.4f);
                        }

                    m_events.ScheduleEvent(EVENT_WAIT_TO_MOVE, 8000);
                    break;
                }
                case EVENT_WAIT_TO_MOVE:
                {
                    uint32 count = CountGruntOnThisFloorZ(34.0f, 3.0f);
                    if (count)
                    {
                        m_events.ScheduleEvent(EVENT_WAIT_TO_MOVE, 1000);
                        break;
                    }

                    if (IsPlayerInRange(15.0f))
                        m_events.ScheduleEvent(EVENT_TALK_PART_00, 1000); // EVENT_MOVE_ATTACK
                    else
                        m_events.ScheduleEvent(EVENT_WAIT_TO_MOVE, 1000);
                    break;
                }
                case EVENT_TALK_PART_00: // lorna goes to captain and talk..
                {
                    m_wp_point = 1;
                    me->GetMotionMaster()->MovePath(4356601, false);
                    break;
                }
                case EVENT_TALK_PART_01:
                {
                    Talk(3);
                    m_events.ScheduleEvent(EVENT_TALK_PART_02, 10000);
                    break;
                }
                case EVENT_TALK_PART_02:
                {
                    Talk(4);
                    m_events.ScheduleEvent(EVENT_TALK_PART_03, 2000);
                    break;
                }
                case EVENT_TALK_PART_03: // walk downstair, to first grunt there
                {
                    if (IsPlayerInRange(50.0f))
                    {
                        m_wp_point = 2;
                        me->GetMotionMaster()->MovePath(4356602, false);
                    }
                    else
                        m_events.ScheduleEvent(EVENT_TALK_PART_03, 1000);
                    break;
                }
                case EVENT_TALK_PART_04: // fight to grunt on stair
                {
                    if (me->IsInCombat() || IsPlayerInCombat())
                        m_events.ScheduleEvent(EVENT_TALK_PART_04, 1000); // repeat 04 while grunt near or self in combat
                    else
                    {
                        if (IsPlayerInRange(15.0f))
                        {
                            m_wp_point = 3;
                            me->GetMotionMaster()->MovePath(4356603, false); // else walk to next position, grunt outsite floor
                        }
                        else
                            m_events.ScheduleEvent(EVENT_TALK_PART_04, 1000);
                    }
                    break;
                }
                case EVENT_TALK_PART_05: // fight to gunt outside stair
                {
                    if (me->IsInCombat() || IsPlayerInCombat())
                        m_events.ScheduleEvent(EVENT_TALK_PART_05, 1000); // repeat 05 while grunt near or self in combat
                    else
                    {
                        if (IsPlayerInRange(15.0f))
                        {
                            m_wp_point = 4;
                            me->GetMotionMaster()->MovePath(4356604, false); // else walk to middle of ship..
                        }
                        else
                            m_events.ScheduleEvent(EVENT_TALK_PART_05, 1000);
                    }
                    break;
                }
                case EVENT_TALK_PART_06: // fight to gunt inside ship
                {
                    if (me->IsInCombat() || IsPlayerInCombat())
                        m_events.ScheduleEvent(EVENT_TALK_PART_06, 1000); // repeat 06 while grunt near or self in combat
                    else
                    {
                        if (IsPlayerInRange(15.0f))
                        {
                            m_wp_point = 5;
                            me->GetMotionMaster()->MovePath(4356605, false); // else walk to machine room..
                        }
                        else
                            m_events.ScheduleEvent(EVENT_TALK_PART_06, 1000);
                    }
                    break;
                }
                case EVENT_TALK_PART_07: // fight inside machine room
                {
                    if (me->IsInCombat() || IsPlayerInCombat() || !IsPlayerInRange(20.0f))
                    {
                        m_events.ScheduleEvent(EVENT_TALK_PART_07, 1000); // repeat 06 while grunt near or self in combat
                    }
                    else
                        m_events.ScheduleEvent(EVENT_TALK_PART_08, 1000);
                    break;
                }
                case EVENT_TALK_PART_08: // the machine room is clean..
                {
                    m_wp_point = 6;
                    me->GetMotionMaster()->MovePath(4356606, false); // we go to spawn gunpowder position..
                    break;
                }
                case EVENT_TALK_PART_09: // spawn 3 gunpowder's
                {
                    if (Transport* trans = me->GetTransport())
                    {
                        if (ObjectGuid::LowType guid = me->GetMap()->GenerateLowGuid<HighGuid::GameObject>())
                        {
                            GameObjectData& data = sObjectMgr->NewGOData(guid);
                            data.id = 204458;
                            data.posX = 53.6417f;
                            data.posY = -0.00663333f;
                            data.posZ = 10.4467f;
                            data.orientation = 2.010638f;
                            if (GameObject* go = trans->CreateGOPassenger(guid, &data))
                            {
                                go->SetObjectScale(2.0f);
                                sObjectMgr->AddGameobjectToGrid(guid, &data);
                            }
                            else
                                TC_LOG_ERROR("scripts", "Gilneas 26706: failed to create gunpowder 204458 on transport");
                        }
                        if (ObjectGuid::LowType guid = me->GetMap()->GenerateLowGuid<HighGuid::GameObject>())
                        {
                            GameObjectData& data = sObjectMgr->NewGOData(guid);
                            data.id = 204458;
                            data.posX = 53.6808f;
                            data.posY = -2.18513f;
                            data.posZ = 10.4467f;
                            data.orientation = 2.010638f;
                            if (GameObject* go = trans->CreateGOPassenger(guid, &data))
                            {
                                go->SetObjectScale(2.0f);
                                sObjectMgr->AddGameobjectToGrid(guid, &data);
                            }
                            else
                                TC_LOG_ERROR("scripts", "Gilneas 26706: failed to create gunpowder 204458 on transport");
                        }
                        //
                        if (ObjectGuid::LowType guid = me->GetMap()->GenerateLowGuid<HighGuid::GameObject>())
                        {
                            GameObjectData& data = sObjectMgr->NewGOData(guid);
                            data.id = 204458;
                            data.posX = 53.1084f;
                            data.posY = 2.12947f;
                            data.posZ = 10.4467f;
                            data.orientation = 2.010638f;
                            if (GameObject* go = trans->CreateGOPassenger(guid, &data))
                            {
                                go->SetObjectScale(2.0f);
                                sObjectMgr->AddGameobjectToGrid(guid, &data);
                            }
                            else
                                TC_LOG_ERROR("scripts", "Gilneas 26706: failed to create gunpowder 204458 on transport");
                        }
                    }
                    Talk(5);
                    m_wp_point = 7;
                    me->GetMotionMaster()->MovePath(4356607, false); // go back to door.. and wait for orc..
                    m_events.ScheduleEvent(EVENT_SPAWN_OBJECT, 200);
                    break;
                }
                case EVENT_SPAWN_OBJECT: // spawn orc and let him walk to us..
                {
                    if (Transport* trans = me->GetTransport())
                        if (ObjectGuid::LowType guid = me->GetMap()->GenerateLowGuid<HighGuid::Creature>())
                        {
                            CreatureData& data = sObjectMgr->NewOrExistCreatureData(guid);
                            data.id = 43567;
                            data.posX = -47.758198f;
                            data.posY = -11.800224f;
                            data.posZ = 13.089049f;
                            data.orientation = 0.549271f;
                            Creature* npc = trans->CreateNPCPassenger(guid, &data);
                            if (!npc)
                            {
                                m_bigOrcGUID = ObjectGuid::Empty;
                                TC_LOG_ERROR("scripts", "Gilneas 26706: failed to create orc 43567; encounter cannot start");
                                break;
                            }
                            sObjectMgr->AddCreatureToGrid(guid, &data);
                            m_bigOrcGUID = npc->GetGUID();
                        }
                    m_events.ScheduleEvent(EVENT_MOVE_PART2, 200);
                    break;
                }
                case EVENT_MOVE_PART2:
                {
                    if (Creature* orc = ObjectAccessor::GetCreature(*me, m_bigOrcGUID))
                    {
                        orc->SetSpeed(MOVE_WALK, 1.4f);
                        orc->GetMotionMaster()->MovePath(4356701, false);
                    }
                    break;
                }
                case EVENT_TALK_PART_10: // finish talk on door position
                {
                    Talk(6); // What a big orc
                    m_events.ScheduleEvent(EVENT_WAIT_FOR_ACTION_00, 4000);
                    break;
                }
                case EVENT_WAIT_FOR_ACTION_00: // wait that orc comes near..
                {
                    if (Creature* orc = ObjectAccessor::GetCreature(*me, m_bigOrcGUID))
                    {
                        Position posA = me->GetTransOffset();
                        Position posB = orc->GetTransOffset();
                        if (posA.GetExactDist(&posB) < 15.0f)
                            m_events.ScheduleEvent(EVENT_TALK_PART_11, 1000);
                        else
                            m_events.ScheduleEvent(EVENT_WAIT_FOR_ACTION_00, 1000);
                    }
                    break;
                }
                case EVENT_TALK_PART_11: // and fight
                {
                    Creature* orc = me->FindNearestCreature(43567, 40.0f);
                    if (orc)
                    {
                        if (me->GetDistance(orc) > 5.0)
                            me->CastSpell(orc, 50092, true);
                        else
                        {
                            me->CastSpell(orc, 15496, true);
                            orc->Attack(me, true);
                        }
                    }

                    if (orc)
                        m_events.ScheduleEvent(EVENT_TALK_PART_11, urand(1100, 1300)); // repeat 11 while orc living
                    else
                        m_events.ScheduleEvent(EVENT_TALK_PART_12, 1000);
                    break;
                }
                case EVENT_TALK_PART_12: // big orc is death..
                {
                    me->PlayDirectSound(23498);
                    m_events.ScheduleEvent(EVENT_TALK_PART_13, 4000);
                    break;
                }
                case EVENT_TALK_PART_13: //
                {
                    Talk(7);
                    m_events.ScheduleEvent(EVENT_TALK_PART_14, 2000);
                    break;
                }
                // the spell 81780 should now start next: visual fleeing from the gunship with new spawned whyvern..
                // but the triggered spell 95869 is visual damaged.. missing additional phase aura??
                case EVENT_TALK_PART_14: //
                {
                    wList.clear();
                    std::list<Player*> pList = me->SelectNearestPlayers(100.0f);
                    for (auto player : pList)
                    {
                        if (!CanJoinEscape(player))
                            continue;
                        if (Transport* trans = me->GetTransport())
                            if (ObjectGuid::LowType guid = me->GetMap()->GenerateLowGuid<HighGuid::GameObject>())
                            {
                                CreatureData& data = sObjectMgr->NewOrExistCreatureData(guid);
                                data.id = 43713;
                                data.posX = player->GetTransOffset().GetPositionX();
                                data.posY = player->GetTransOffset().GetPositionY();
                                data.posZ = player->GetTransOffset().GetPositionZ();
                                data.orientation = player->GetTransOffset().GetOrientation();
                                Creature* npc = trans->CreateNPCPassenger(guid, &data);
                                if (!npc)
                                {
                                    TC_LOG_ERROR("scripts", "Gilneas26706: failed to create escape wyvern43713; passenger skipped");
                                    continue;
                                }
                                PhasingHandler::InheritPhaseShift(npc, player);
                                sObjectMgr->AddCreatureToGrid(guid, &data);
                                npc->AI()->SetGUID(player->GetGUID(), PLAYER_GUID);
                                wList.push_back(npc->GetGUID());
                            }
                    }
                    m_events.ScheduleEvent(EVENT_TALK_PART_15, 200);
                    break;
                }
                case EVENT_TALK_PART_15:
                {
                    for (auto guid : wList)
                        if (Creature* wyvern = ObjectAccessor::GetCreature(*me, guid))
                        {
                            ObjectGuid ownerGUID = wyvern->AI()->GetGUID(PLAYER_GUID);
                            if (Player* player = ObjectAccessor::GetPlayer(*me, ownerGUID))
                                if (CanJoinEscape(player) && wyvern->IsInPhase(player))
                                    player->EnterVehicle(wyvern, 0);
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

 // ############################

        Creature* FindBestJumpTarget(Creature* source, float floorZ, std::vector<Creature*> tList)
        {
            Position posS = source->GetTransOffset();
            float dist = 100.0f;
            Creature* rTarget = nullptr;
            for (auto target : tList)
            {
                Position posT = target->GetTransOffset();
                if (fabs(posT.GetPositionZ() - floorZ) < 4.0f)
                {
                    float d1 = posS.GetExactDist2d(&posT);
                    if (d1 < dist)
                    {
                        dist = d1;
                        rTarget = target;
                    }
                }
            }
            return rTarget;
        }

        void SetGruntReactStateOnThisFloor(float floorZ, float range, ReactStates react)
        {
            std::list<Creature*> cList = me->FindNearestCreatures(NPC_GUNSHIP_GRUNT, range);
            for (auto grunt : cList)
                if (grunt->IsAlive())
                    if (fabs(grunt->GetTransOffset().GetPositionZ() - floorZ) < 3.0f)
                        grunt->SetReactState(react);
        }

        Creature* FindTargetOnThisFloor(Creature* source, float range)
        {
            std::list<Creature*> cList = me->FindNearestCreatures(NPC_GUNSHIP_GRUNT, range);
            for (auto grunt : cList)
                if (grunt->IsAlive())
                    if (fabs(source->GetTransOffset().GetPositionZ() - grunt->GetTransOffset().GetPositionZ()) < 3.0f)
                    {
                        return grunt;
                    }
            return nullptr;
        }

        bool IsSceneParticipant(Player* player) const
        {
            return player && player->IsAlive() && me->GetMapId() == 654
                && player->GetMapId() == me->GetMapId() && me->IsInPhase(player)
                && me->GetTransport() && player->GetTransport() == me->GetTransport()
                && player->GetQuestStatus(QUEST_ENDGAME) == QUEST_STATUS_INCOMPLETE;
        }

        bool IsPlayerInCombat()
        {
            std::list<Player*> pList = me->SelectNearestPlayers(20.0f);
            for (auto player : pList)
                if (IsSceneParticipant(player) && player->IsInCombat())
                    return true;

            return false;
        }

        bool IsPlayerInRange(float range)
        {
            for (Player* player : me->SelectNearestPlayers(range))
                if (IsSceneParticipant(player))
                    return true;
            return false;
        }

        bool isInSameTranportFloor(Creature* creature)
        {
            float diff = fabs(me->GetTransOffset().GetPositionZ() - creature->GetTransOffset().GetPositionZ());
            return (diff < 5.0f) ? true : false;
        }

        uint32 CountGruntOnThisFloorZ(float posZ, float rangeZ)
        {
            uint32 count = 0;
            std::list<Unit*>m_targetList;
            me->GetAttackableUnitListInRange(m_targetList, 75.0f); // returns only alive
            for (std::list<Unit*>::iterator itr = m_targetList.begin(); itr != m_targetList.end(); ++itr)
            {
                Unit* target = *itr;
                if (target->GetEntry() != NPC_GUNSHIP_GRUNT || !me->GetTransport()
                    || target->GetTransport() != me->GetTransport() || !me->IsInPhase(target))
                    continue;
                Position pos = target->GetTransOffset();
                if (fabs(pos.GetPositionZ() - posZ) < rangeZ)
                    count += 1;
            }

            return count;
        }

        void SetRopeSelectableFlag(bool value)
        {
            std::list<GameObject*> goList = me->FindNearestGameObjects(GO_ROPE, 30.0f); // there are 2 rope on bridge
            for (std::list<GameObject*>::const_iterator itr = goList.begin(); itr != goList.end(); ++itr)
            {
                if (value)
                    (*itr)->RemoveFlag(GAMEOBJECT_FLAGS, GO_FLAG_NOT_SELECTABLE);
                else
                    (*itr)->SetFlag(GAMEOBJECT_FLAGS, GO_FLAG_NOT_SELECTABLE);
            }
        }

        std::vector<Creature*> FindFriendlyCreatureList()
        {
            std::vector<Creature*> rList;
            std::list<Creature*> tList = me->FindAllCreaturesInRange(18.0f);
            for (std::list<Creature*>::iterator itr = tList.begin(); itr != tList.end(); ++itr)
                if (Creature* target = (*itr))
                    if (isInSameTranportFloor(target) && target->IsAlive())
                        rList.push_back(target);

            return rList;
        }

        std::vector<Creature*> FindJumpTargetPositions(float floorZ)
        {
            std::vector<Creature*> rList;
            std::list<Creature*> tList = me->FindNearestCreatures(NPC_GILNEAS_VEHICLE_ROPE, 75.0f);
            for (std::list<Creature*>::iterator itr = tList.begin(); itr != tList.end(); ++itr)
            {
                float diff = fabs((*itr)->GetTransOffset().GetPositionZ() - floorZ);
                if (diff < 5.0f)
                    rList.push_back((*itr));
            }
            return rList;
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_lorna_crowley_43566AI(creature);
    }
};

// 43651
class npc_worgen_warrior_43651 : public CreatureScript
{
public:
    npc_worgen_warrior_43651() : CreatureScript("npc_worgen_warrior_43651") { }

    struct npc_worgen_warrior_43651AI : public ScriptedAI
    {
        npc_worgen_warrior_43651AI(Creature* creature) : ScriptedAI(creature) { Initialize(); }

        EventMap  m_events;

        void Initialize() { }

        void Reset() override
        {
            me->SetReactState(REACT_DEFENSIVE);
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1200);
        }

        void EnterCombat(Unit* /*who*/) override
        {
            me->GetMotionMaster()->MoveIdle();
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage) override
        {
            damage = 0;
        }

        void EnterEvadeMode(EvadeReason /*reason*/) override
        {
            me->CombatStop(true);
            me->SetTransportHomePosition(me->GetTransOffset());
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_CHECK_ATTACK:
                {
                    if (!me->IsInCombat())
                        if (Creature* target = me->FindNearestAttackableCreatureOnTransportInFloor(5, 3))
                        {
                            me->GetMotionMaster()->MoveIdle();
                            me->Attack(target, true);
                        }

                    m_events.ScheduleEvent(EVENT_CHECK_ATTACK, urand(900, 1200));
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
        return new npc_worgen_warrior_43651AI(creature);
    }
};

// 43703
class npc_gilnean_sharpshooter_43703 : public CreatureScript
{
public:
    npc_gilnean_sharpshooter_43703() : CreatureScript("npc_gilnean_sharpshooter_43703") { }

    struct npc_gilnean_sharpshooter_43703AI : public ScriptedAI
    {
        npc_gilnean_sharpshooter_43703AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap    m_events;
        ObjectGuid  m_oldTargetGuid;
        uint32      m_count;

        void Reset() override
        {
            m_oldTargetGuid = ObjectGuid::Empty;
            m_count = 0;
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1000);
            me->SetReactState(REACT_DEFENSIVE);
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage) override
        {
            damage = 0;
        }

        void EnterEvadeMode(EvadeReason /*reason*/) override
        {
            me->CombatStop(false);
            if (me->GetTransOffset().GetPositionZ() < 50.0f)
                me->SetTransportHomePosition(me->GetTransOffset());
            else
                me->GetMotionMaster()->MoveTargetedHome();
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_CHECK_ATTACK:
                {
                    if (!me->IsInCombat())
                    {
                        if (Creature* target = me->FindNearestAttackableCreatureOnTransportInFloor(35, 10))
                        {
                            if (me->GetTransOffset().GetExactDist2d(&target->GetTransOffset()) < 5.0f)
                            {
                                me->GetMotionMaster()->MoveIdle();
                                me->Attack(target, true);
                            }
                            else
                            {
                                Position p = target->GetTransOffset();
                                if (me->IsWithinLOS(p.m_positionX, p.m_positionY, p.m_positionZ))
                                    break;
                                me->CastSpell(target, 50092, true);
                                AttackStartNoMove(target);
                                m_events.ScheduleEvent(EVENT_CAST_COOLDOWN, 2000);
                                /* this is a workaround: sometimes the core make failure in attack.. on attack the core only report 'escape' and none can kill this target..*/
                                bool isEvade = target->HasUnitState(UNIT_STATE_EVADE);
                                if (m_oldTargetGuid == target->GetGUID() && isEvade)
                                {
                                    m_count += 1;
                                    if (m_count > 5)
                                        target->ClearUnitState(UNIT_STATE_EVADE);
                                }
                                else
                                {
                                    m_count = 0;
                                    m_oldTargetGuid = target->GetGUID();
                                }
                            }
                        }
                    }

                    m_events.RescheduleEvent(EVENT_CHECK_ATTACK, urand(1000, 1100));
                    break;
                }
                case EVENT_CAST_COOLDOWN:
                {
                    me->CombatStop(true);
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
        return new npc_gilnean_sharpshooter_43703AI(creature);
    }
};

// 42141
class npc_gunship_grunt_42141 : public CreatureScript
{
public:
    npc_gunship_grunt_42141() : CreatureScript("npc_gunship_grunt_42141") { }

    struct npc_gunship_grunt_42141AI : public ScriptedAI
    {
        npc_gunship_grunt_42141AI(Creature* creature) : ScriptedAI(creature) { }

        EventMap m_events;
        ObjectGuid   m_playerGUID;

        void Reset() override
        {
            m_playerGUID = ObjectGuid::Empty;
            me->SetReactState(REACT_DEFENSIVE);
            m_events.RescheduleEvent(EVENT_CHECK_ATTACK, 1000);
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage) override
        {
            if (!m_playerGUID.IsEmpty())
            {
                //damage *= 2;
            }
            else
                damage = 0;
        }

        void UpdateAI(uint32 diff) override
        {
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_CHECK_ATTACK:
                {
                    if (!me->IsInCombat())
                    {
                        if (Creature* target = me->FindNearestAttackableCreatureOnTransportInFloor(5.0f, 3.0f))
                            me->Attack(target, true);
                    }

                    if (!m_playerGUID)
                        if (Player* player = me->SelectNearestPlayer(75.0f))
                            m_playerGUID = player->GetGUID();

                    m_events.RescheduleEvent(EVENT_CHECK_ATTACK, urand(1000, 1100));
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
        return new npc_gunship_grunt_42141AI(creature);
    }
};

// GO 204428
class go_rope_204428 : public GameObjectScript
{
public:
    go_rope_204428() : GameObjectScript("go_rope_204428") { }

    bool OnGossipHello(Player* player, GameObject* /*go*/) override
    {
        if (Creature* target = FindRandomJumpTargetPosition(player))
            player->JumpTo(target, 0.4f);

        return true;
    }

    Creature* FindRandomJumpTargetPosition(Player* player)
    {
        float zHeight = player->GetPositionZ() - 10.0f;
        std::vector<Creature*> rList;
        std::list<Creature*> tList = player->FindNearestCreatures(NPC_GILNEAS_VEHICLE_ROPE, 50.0f);
        for (std::list<Creature*>::iterator itr = tList.begin(); itr != tList.end(); ++itr)
            if (Creature* target = (*itr))
                if (target->GetPositionZ() < zHeight)
                    rList.push_back(target);

        return (!rList.empty()) ? rList[urand(0, rList.size() - 1)] : nullptr;
    }
};

// 43713
class npc_wyvern_43713 : public CreatureScript
{
public:
    npc_wyvern_43713() : CreatureScript("npc_wyvern_43713") { }

    struct npc_wyvern_43713AI : public ScriptedAI
    {
        npc_wyvern_43713AI(Creature* creature) : ScriptedAI(creature) {}

        EventMap m_events;
        ObjectGuid   m_playerGUID;
        uint32   m_flyPart;
        bool m_boarded = false;
        bool m_arrived = false;
        bool m_stopped = false;

        void TraceEscape(char const* state) const
        {
            TC_LOG_DEBUG("scripts", "Gilneas26706 %s: vehicle=%s owner=%s route=4371301 part=%u boarded=%u arrived=%u",
                state, me->GetGUID().ToString().c_str(), m_playerGUID.ToString().c_str(),
                m_flyPart, uint32(m_boarded), uint32(m_arrived));
        }

        // Retain route and owner state when vehicle boarding charms this creature.
        void OnCharmed(bool /*apply*/) override { }

        void Reset() override
        {
            if (m_boarded || m_stopped)
            {
                CancelFlight();
                return;
            }
            m_events.Reset();
            m_playerGUID = ObjectGuid::Empty;
            m_flyPart = 0;
            m_boarded = false;
            m_arrived = false;
            m_stopped = false;
            TraceEscape("ESCAPE_WAITING");
        }

        void MovementInform(uint32 type, uint32 id) override
        {
            if (m_boarded && !m_stopped && !m_arrived && m_flyPart == 1
                && type == WAYPOINT_MOTION_TYPE && id == 2)
            {
                m_arrived = true;
                TraceEscape("ESCAPE_ARRIVED");
                m_events.ScheduleEvent(EVENT_MOVE_PART1, 200);
            }
        }

        ObjectGuid GetGUID(int32 id) const override
        {
            return id == PLAYER_GUID ? m_playerGUID : ObjectGuid::Empty;
        }

        bool IsEligibleOwner(Player* player) const
        {
            return player && player->GetGUID() == m_playerGUID && player->IsAlive()
                && me->GetMapId() == 654 && player->GetMapId() == 654 && me->IsInPhase(player)
                && player->GetQuestStatus(QUEST_ENDGAME) == QUEST_STATUS_INCOMPLETE;
        }

        void CancelFlight()
        {
            if (m_stopped)
                return;
            m_stopped = true;
            m_boarded = false;
            m_events.Reset();
            TraceEscape("ESCAPE_CANCELLED");
            if (Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID))
                if (player->GetVehicleBase() == me)
                    player->ExitVehicle();
            me->DespawnOrUnsummon(200ms);
        }

        void JustDied(Unit* /*killer*/) override { CancelFlight(); }

        void PassengerBoarded(Unit* who, int8 seatId, bool apply) override
        {
            Player* player = who ? who->ToPlayer() : nullptr;
            if (!player)
                return;
            if (apply)
            {
                if (m_stopped || seatId != 0 || !IsEligibleOwner(player))
                {
                    player->ExitVehicle();
                    return;
                }
                if (!m_boarded)
                {
                    m_boarded = true;
                    TraceEscape("ESCAPE_BOARDED");
                    m_events.RescheduleEvent(EVENT_MOVEMENT_START, 200);
                }
            }
            else if (player->GetGUID() == m_playerGUID && !m_stopped)
            {
                m_boarded = false;
                if (m_arrived && m_flyPart == 1 && IsEligibleOwner(player))
                    m_events.RescheduleEvent(EVENT_MOVE_PART2, 200);
                else
                    CancelFlight();
            }
        }

        void SetGUID(ObjectGuid guid, int32 id) override
        {
            if (id == PLAYER_GUID && m_playerGUID.IsEmpty() && !guid.IsEmpty() && !m_stopped)
            {
                m_playerGUID = guid;
                TraceEscape("ESCAPE_OWNER_BOUND");
            }
        }

        void UpdateAI(uint32 diff) override
        {
            if (m_stopped)
                return;
            if (m_boarded)
            {
                Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                if (!IsEligibleOwner(player) || player->GetVehicleBase() != me)
                {
                    CancelFlight();
                    return;
                }
            }
            ScriptedAI::UpdateAI(diff);
            m_events.Update(diff);

            while (uint32 eventId = m_events.ExecuteEvent())
            {
                switch (eventId)
                {
                case EVENT_MOVEMENT_START:
                {
                    m_flyPart = 1;
                    TraceEscape("ESCAPE_START");
                    me->GetMotionMaster()->MovePath(4371301, false);                    // fly to the open ship gate..
                    break;
                }
                case EVENT_MOVE_PART1:
                {
                    if (ObjectAccessor::GetPlayer(*me, m_playerGUID)) // now we are outside the ship
                        if (Vehicle* wyv = me->GetVehicleKit())
                            wyv->RemoveAllPassengers();                                 // and leave the wyvern

                    break;
                }
                case EVENT_MOVE_PART2:
                {
                    Player* player = ObjectAccessor::GetPlayer(*me, m_playerGUID);
                    if (!m_arrived || m_boarded || m_flyPart != 1 || !IsEligibleOwner(player)
                        || player->GetVehicleBase())
                    {
                        CancelFlight();
                        break;
                    }
                    m_flyPart = 2;
                    m_stopped = true;
                    m_events.Reset();
                    WorldLocation wLoc = WorldLocation(654, -1317.54f, 2121.90f, 5.6296f, 0.218f); // last we teleport to questtaker..
                    TraceEscape("ESCAPE_COMPLETED");
                    player->KilledMonsterCredit(43729);
                    player->TeleportTo(wLoc);
                    me->DespawnOrUnsummon(200);
                    break;
                }
                }
            }
        }
    };

    CreatureAI* GetAI(Creature* creature) const override
    {
        return new npc_wyvern_43713AI(creature);
    }
};

// 43727
class npc_lorna_crowley_43727 : public CreatureScript
{
public:
    npc_lorna_crowley_43727() : CreatureScript("npc_lorna_crowley_43727") { }

    bool OnQuestReward(Player* /*player*/, Creature* creature, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == QUEST_ENDGAME)
        {
            creature->AI()->Talk(0);
        }
        return true;
    }
};

// 36616
class npc_admiral_nightwind_36616 : public CreatureScript
{
public:
    npc_admiral_nightwind_36616() : CreatureScript("npc_admiral_nightwind_36616") { }

    bool OnQuestReward(Player* player, Creature* /*creature*/, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() == QUEST_RUTTHERAN)
        {
            player->RemoveAllAuras();
            player->TeleportTo(1, 8343, 801, 4, 4.19f);
        }
        return true;
    }
};

void AddSC_zone_gilneas_city3()
{
    new npc_tobias_mistmantle_38507();
    new npc_lady_sylvanas_windrunner_38530();
    new npc_captured_riding_bat_38540();
    new spell_gilneas_captured_bat_summon();
    new spell_fly_back_72849();
    new spell_iron_bomb_72247();
    new npc_tobias_mistmantle_43749();
    new npc_hippogryph_43751();
    new spell_gilneas_endgame_hippogryph();
    new go_worgen_gunship_203428();
    new npc_lorna_crowley_43566();
    new npc_worgen_warrior_43651();
    new npc_gilnean_sharpshooter_43703();
    new npc_gunship_grunt_42141();
    new go_rope_204428();
    new npc_wyvern_43713();
    new npc_lorna_crowley_43727();
    new npc_admiral_nightwind_36616();
}

