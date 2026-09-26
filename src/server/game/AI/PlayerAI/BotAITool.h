/*
 * This file is part of the DestinyCore Project. See AUTHORS file for Copyright information
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

#ifndef _BOT_AI_TOOL_H
#define _BOT_AI_TOOL_H

#include "ScriptSystem.h"
#include "PlayerAI.h"
#include "Player.h"

#define ARENA_PLAYER_BOT_AURA 80849
#define ARENA_WARRIOR_BOT_AURA 80850
#define ARENA_PALADIN_BOT_AURA 80851
#define ARENA_ROGUE_BOT_AURA 80852
#define ARENA_HUNTER_BOT_AURA 80853
#define ARENA_SHAMAN_BOT_AURA 80854
#define ARENA_MAGE_BOT_AURA 80855
#define ARENA_WARLOCK_BOT_AURA 80856
#define ARENA_PRIEST_BOT_AURA 80857
#define ARENA_DRUID_BOT_AURA 80858

#define BOTAI_UPDATE_TICK 500

#define BOTAI_MAXTARGET_TICKTIME 30000
#define BOTAI_FIELDTELEPORT_DISTANCE 80
#define BOTAI_SEARCH_RANGE 32
#define BOTAI_RANGESPELL_DISTANCE 28
#define BOTAI_TOTEMRANGE 18
#define BOTAI_FLEE_JUDGE 14

#define NEEDFLEE_CHECKRANGE 10

enum ShamanTotemPattern
{
    ShamanTP_None = 0,
    ShamanTP_Normal = 1,
    ShamanTP_Flee = 2,
    ShamanTP_Heal = 3,
    ShamanTP_Melee = 4,
    ShamanTP_Range = 5
};

enum BOTAI_WORKTYPE
{
    AIWT_TANK,
    AIWT_MELEE,
    AIWT_RANGE,
    AIWT_HEAL,
    AIWT_ALL
};

struct SpellEntry;
class Player;
class Group;
class BotBGAIMovement;

class TC_GAME_API BotUtility
{
public:
    static float BattlegroundScoreRate;
    static float DungeonBotDamageModify;
    static float DungeonBotEndureModify;
    static bool BotCanForceRevive;
    static bool BotCanSettingToMaster;
    static int32 BotCritTakenAddion;
    static bool ControllSpellDiminishing;
    static bool ControllSpellFromDmgBreak;
    static bool DownBotArenaTeam;
    static bool ArenaIsHell;
    static uint32 BotArenaTeamTactics;
    static bool DisableDKQuest;

public:
    static SpellEntry* BuildNewArenaSpellEntry();
    static void ModifySpecialSpells();
    //static void BuildNewArenaHellSpells(SpellInfoMap& spellMap);
    static void AddArenaBotSpellsByPlayer(Player* player);
    static void RemoveArenaBotSpellsByPlayer(Player* player);
    static bool SpellHasReady(Player* player, uint32 spellID);
    static uint32 GetFirstNumberByString(std::string text);
    static std::string BuildItemLinkText(const ItemTemplate* pItemTemplate);
    static void UpdatePlayerBotRoll(Player* player);
    static Item* FindItemFromAllBag(Player* player, uint32 entry, bool destroy = false);
    static Item* FindItemFromAllBag(Player* player, uint32 entry, uint8& bag, uint8& index);
    static bool DestroyItemFromAllBag(Player* player, Item* pItem);
    static Item* StoreNewItemByEntry(Player* player, uint32 entry, int32 count = 1);
    static uint32 FindMaxRankSpellByExist(Player* player, uint32 spellID);
    static uint32 FindPetMaxRankSpellByExist(Player* player, uint32 spellID);
    static void PlayerBotTogglePVP(Player* player, bool pvp);
    static Position FindRadiusByNearDistance(Unit* pTargetUnit, float range, Unit* pRefUnit);
    static Position FindRadiusByFarDistance(Unit* pTargetUnit, float range, Unit* pRefUnit);
    static bool FindFirstCollisionPosition(Unit* pTargetUnit, float range, Unit* pRefUnit, Position& outPos);
    static void TryTeleportPlayerPet(Player* player, bool force = false);
};

class TC_GAME_API BotAITeleport
{
public:
    BotAITeleport(Player* self) : me(self), m_Teleporting(false), m_MapId(self->GetMapId()), m_TeleportStep(0)
    {
    }
    ~BotAITeleport() {}

    void SetTeleport(Position& telePos);
    void SetTeleport(uint32 mapID, Position& telePos);
    void SetTeleport(Player* pTarget, float offset = NEEDFLEE_CHECKRANGE);
    void ClearTeleport();
    void Update(uint32 diff, BotBGAIMovement* pMovement);
    bool CanMovement() { return !m_Teleporting; }
    void UpdateMapID() { if (me) m_MapId = me->GetMapId(); }

private:
    Player* me;
    bool m_Teleporting;
    Position m_TeleportPositon;
    uint32 m_MapId;
    uint32 m_TeleportStep;
};

class TC_GAME_API BotAIStoped
{
public:
    BotAIStoped(Player* self) : me(self), m_updateTick(0), m_SyncTick(0)
    {
        if (me)
        {
            m_lastPosition = me->GetPosition();
        }
    }
    ~BotAIStoped() {}

    void UpdatePosition(uint32 diff);

private:
    bool HasDifference(Position& pos1, Position& pos2);
    void SyncPosition(Position pos, uint32 opcode);

private:
    Player* me;
    int32 m_updateTick;
    Position m_lastPosition;
    uint32 m_SyncTick;
};

class TC_GAME_API BotAIHorrorState
{
public:
    BotAIHorrorState(Player* self) : me(self), m_CurHorrorPos(self->GetPosition()) {}
    ~BotAIHorrorState() {}

    void UpdateHorror(uint32 diff, BotBGAIMovement* movement);

    Position GetNewHorrorPos();
    static Position GetNewHorrorPosByRange(Player* player, float distance);
    Position FindNewHorrorPos(BotBGAIMovement* movement);

private:
    Player* me;
    Position m_CurHorrorPos;
};

struct PotionInfo
{
    uint32 level;
    uint32 potionEntry;

    PotionInfo(uint32 lv, uint32 entry) : level(lv), potionEntry(entry)
    {
    }
};

class TC_GAME_API BotAIUsePotion
{
    typedef std::list<PotionInfo> POTION_LIST;
public:
    BotAIUsePotion(Player* self);
    ~BotAIUsePotion() {}

    bool TryUsePotion();

private:
    bool TryUseLifeVial();
    bool TryUseManaVial();
    Item* FindLifeVial();
    Item* FindManaVial();

private:
    Player* me;
    bool m_NeedMana;
    POTION_LIST m_LifeVials;
    POTION_LIST m_ManaVials;
};

class TC_GAME_API BotAIFastAid
{
    typedef std::list<PotionInfo> AID_LIST;
public:
    BotAIFastAid(Player* self);
    ~BotAIFastAid() {}

    void CheckPlayerFastAid();
    bool TryDoingFastAidForMe();

private:
    uint32 GetFastAidSpell();
    bool CanFastAidByTarget(Player* target);

private:
    Player* me;
    uint32 m_NoAidBuff;
    AID_LIST m_FastAids;
};

class TC_GAME_API BotAIFlee
{
    struct PVEFleePosition
    {
        Position fleePosition;
        uint32 enemyCount;
        float byMeDist;
        float byMasterDist;
        PVEFleePosition() : enemyCount(0), byMeDist(0), byMasterDist(0)
        {

        }
        bool operator < (const PVEFleePosition& fleePos)
        {
            return byMeDist > fleePos.byMeDist;
        }
    };

public:
    BotAIFlee(Player* self) : me(self), m_FleeTarget(NULL), m_FleeTick(0), m_cruxTime(0) {}
    ~BotAIFlee() {}

    void Clear() { if (m_FleeTarget) { delete m_FleeTarget; m_FleeTarget = NULL; } m_FleeTick = 0; m_cruxTime = 0; }
    bool Fleeing() { return m_FleeTarget != NULL; }
    void UpdateFleeMovementByPVE(Unit* pMaster, Unit* pRefUnit, BotBGAIMovement* pMovement);
    void UpdateFleeMovementByPVP(Unit* pRefUnit, BotBGAIMovement* pMovement);
    void UpdateFleeMovementByPosition(Unit* pRefUnit, Position centerPos, float maxPosDist, BotBGAIMovement* pMovement);
    float CalcMaxFleeDistance(Unit* pRefUnit);
    void AddCruxFlee(uint32 durTime, Unit* pRefUnit, BotBGAIMovement* pMovement);

private:
    bool CanFleeToTargetPlayer(Player* player);
    bool SearchPVEFleePosition(Unit* pMaster, Unit* pRefUnit, Position& fleePos);
    void SearchCreatureListFromRange(Position centerPos, std::list<Creature*>& nearCreatures, float range);
    Position CalculateFlee(float dist, float angle, Unit* pRefUnit, float& outDistance);

private:
    Player* me;
    Position* m_FleeTarget;
    uint32 m_FleeTick;
    uint32 m_cruxTime;
};

class TC_GAME_API BotAINeedFleeAura
{
public:
    BotAINeedFleeAura(Player* self) : me(self)
    {
        m_NeedFleeAuras.push_back(46924);
    }
    ~BotAINeedFleeAura() {}

    void AddFleeAura(uint32 aura);
    bool TargetHasFleeAura() { return TargetHasFleeAura(me->GetSelectedPlayer()); };
    bool TargetHasFleeAura(ObjectGuid targetGUID) { return TargetHasFleeAura(ObjectAccessor::FindPlayer(targetGUID)); };
    bool TargetHasFleeAura(Unit* pTarget);

    Player* me;
    std::list<uint32> m_NeedFleeAuras;
};

class TC_GAME_API BotAIRecordCastSpell
{
    struct CastedSpell
    {
        CastedSpell() {}
        CastedSpell(ObjectGuid guid)
        {
            castTarget = guid;
        }
        ObjectGuid castTarget;
        std::map<uint32, uint32> castRecords;
    };
    typedef std::map<ObjectGuid, CastedSpell> AIRECORDS;

public:
    BotAIRecordCastSpell(Player* self) : me(self) {}
    ~BotAIRecordCastSpell() {}

    void ClearRecordSpell() { m_Records.clear(); }
    void RecordCastSpellTick(Unit* pTarget, uint32 spellID);
    bool MatchCastRecord(Unit* pTarget, uint32 spellID, uint32 tickGap);

private:
    Player* me;
    AIRECORDS m_Records;
};

class TC_GAME_API BotAIGroupLeader
{
public:
    BotAIGroupLeader(Player* self) : me(self) {}
    ~BotAIGroupLeader() {}

    void ProcessGroupLeader();

private:
    Player* me;
};

class TC_GAME_API BotAIMovetoUseGO
{
public:
    BotAIMovetoUseGO(Player* self) : me(self), m_UseGO(ObjectGuid::Empty), m_RiteSpellID(0) {}
    ~BotAIMovetoUseGO() {}

    bool CanCastSummonRite();
    bool CastingSummonRite() { return m_RiteSpellID != 0; }
    void ClearUseGO() { m_UseGO = ObjectGuid::Empty; m_RiteSpellID = 0; }
    void StartSummonRite(uint32 spellID);
    bool SetNeedMovetoUseGO(ObjectGuid& guid);
    bool ProcessMovetoUseGO(BotBGAIMovement* pMovement);

private:
    Player* me;
    ObjectGuid m_UseGO;
    uint32 m_RiteSpellID;
};

#endif // !_BOT_AI_TOOL_H
