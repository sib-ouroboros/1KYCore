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

#ifndef SC_BOTFOLLOWERAI_H
#define SC_BOTFOLLOWERAI_H

#include "ScriptSystem.h"
#include "PlayerAI.h"
#include "Pathfinding.h"
#include "BotAITool.h"

class TC_GAME_API BotMovementAI : public PlayerAI
{
public:
    explicit BotMovementAI(Player* player) : PlayerAI(player) { }

    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType damageType) override;
    void DamageEndure(Unit* attacker, uint32& damage, DamageEffectType damageType);
    void UpdateAI(uint32 /*diff*/) override { }
};

#endif // SC_BOTFOLLOWERAI_H
