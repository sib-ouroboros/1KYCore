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

class TC_GAME_API BotUtility
{
public:
    static float BattlegroundScoreRate;
    static float DungeonBotDamageModify;
    static float DungeonBotEndureModify;
    static bool BotCanForceRevive;
    static bool BotCanSettingToMaster;
    static bool ControllSpellDiminishing;
    static bool ControllSpellFromDmgBreak;
    static bool DownBotArenaTeam;
    static bool ArenaIsHell;
    static uint32 BotArenaTeamTactics;
    static bool DisableDKQuest;

public:
    // Shared inventory helpers still used by ordinary players and custom menus.
    static Item* FindItemFromAllBag(Player* player, uint32 entry, bool destroy = false);
    static Item* StoreNewItemByEntry(Player* player, uint32 entry, int32 count = 1);
};

#endif // !_BOT_AI_TOOL_H
