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

#include "PlayerCombatModifiersAI.h"
#include "WaypointManager.h"
#include "Map.h"
#include "WorldSession.h"
#include "PlayerGameplayUtility.h"
#include "MapManager.h"
#include "MotionMaster.h"
#include "WaypointMovementGenerator.h"

void PlayerCombatModifiersAI::DamageDealt(Unit* victim, uint32& damage, DamageEffectType damageType)
{
	if (!victim || !me->IsInWorld() || damage == 0)
		return;

	if (me->InBattleground())
	{
	}
	else if (me->GetMap()->IsDungeon())
	{
        damage = uint32(float(damage) * PlayerGameplayUtility::DungeonPlayerDamageMultiplier);
	}
}

void PlayerCombatModifiersAI::DamageEndure(Unit* attacker, uint32& damage, DamageEffectType damageType)
{
	if (!attacker || !me->IsInWorld() || damage == 0)
		return;

	if (me->InBattleground())
	{
	}
	else if (me->GetMap()->IsDungeon())
	{
        damage = uint32(float(damage) * (1.0f / PlayerGameplayUtility::DungeonPlayerDamageDivisor));
	}
}
