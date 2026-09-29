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

#ifndef TRINITY_PLAYER_GAMEPLAY_UTILITY_H
#define TRINITY_PLAYER_GAMEPLAY_UTILITY_H

#include "ScriptSystem.h"
#include "PlayerAI.h"
#include "Player.h"

class TC_GAME_API PlayerGameplayUtility
{
public:
    static float BattlegroundScoreRate;
    static float DungeonPlayerDamageMultiplier;
    static float DungeonPlayerDamageDivisor;

public:
    // Shared inventory helpers still used by ordinary players and custom menus.
    static Item* FindItemFromAllBag(Player* player, uint32 entry, bool destroy = false);
    static Item* StoreNewItemByEntry(Player* player, uint32 entry, int32 count = 1);
};

#endif // !TRINITY_PLAYER_GAMEPLAY_UTILITY_H
