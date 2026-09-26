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

class TC_GAME_API BotAIHorrorState
{
public:
    BotAIHorrorState(Player* self) : me(self), m_CurHorrorPos(self->GetPosition()) {}
    ~BotAIHorrorState() {}

    void UpdateHorror(uint32 diff);

    Position GetNewHorrorPos();
    static Position GetNewHorrorPosByRange(Player* player, float distance);

private:
    Player* me;
    Position m_CurHorrorPos;
};

#endif // !_BOT_AI_TOOL_H
