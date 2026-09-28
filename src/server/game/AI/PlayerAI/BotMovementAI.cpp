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

#include "BotMovementAI.h"
#include "WaypointManager.h"
#include "Pathfinding.h"
#include "WorldSession.h"
#include "BotAITool.h"
#include "MapManager.h"
#include "MotionMaster.h"
#include "WaypointMovementGenerator.h"

void BotMovementAI::DamageDealt(Unit* victim, uint32& damage, DamageEffectType damageType)
{
	if (!victim || !me->IsInWorld() || damage == 0)
		return;

	if (me->InBattleground())
	{
		//Player* vicPlayer = victim->ToPlayer();
		//if (!vicPlayer)
		//	return;
		//int32 meCP = me->GetEquipCombatPower();
		//int32 vicCP = vicPlayer->GetEquipCombatPower();
		//int32 cpGap = meCP - vicCP;
		//if (cpGap == 0)
		//	return;
		//float addion = 0;
		//if (cpGap > 0 && meCP > 0)
		//{
		//	addion = float(cpGap) / float(meCP);
		//	addion = 1.0f - addion;
		//}
		//else if (cpGap < 0 && vicCP > 0)
		//{
		//	addion = float(cpGap * (-1.0f)) / float(vicCP);
		//	addion += 1.0f;
		//}
		//if (addion <= 0)
		//	return;
		//float result = float(damage);
		//switch (damageType)
		//{
		//case DamageEffectType::DIRECT_DAMAGE:
		//case DamageEffectType::SPELL_DIRECT_DAMAGE:
		//case DamageEffectType::DOT:
		//	result *= addion;
		//	break;
		//default:
		//	return;
		//}
		//damage = uint32(result);
	}
	else if (me->GetMap()->IsDungeon())
	{
		damage = uint32(float(damage) * BotUtility::DungeonBotDamageModify);
	}
}

void BotMovementAI::DamageEndure(Unit* attacker, uint32& damage, DamageEffectType damageType)
{
	if (!attacker || !me->IsInWorld() || damage == 0)
		return;

	if (me->InBattleground())
	{
		//Player* attPlayer = attacker->ToPlayer();
		//if (!attPlayer)
		//	return;
		//int32 meCP = me->GetEquipCombatPower();
		//int32 attCP = attPlayer->GetEquipCombatPower();
		//int32 cpGap = attCP - meCP;
		//if (cpGap == 0)
		//	return;
		//float addion = 0;
		//if (cpGap > 0)
		//{
		//	addion = float(cpGap) / float(attPlayer->GetEquipCombatPower());
		//	addion = 1.0f - addion;
		//}
		//else
		//{
		//	addion = float(cpGap * (-1.0f)) / float(me->GetEquipCombatPower());
		//	addion += 1.0f;
		//}
		//if (addion <= 0)
		//	return;
		//float result = float(damage);
		//switch (damageType)
		//{
		//case DamageEffectType::DIRECT_DAMAGE:
		//case DamageEffectType::SPELL_DIRECT_DAMAGE:
		//case DamageEffectType::DOT:
		//	result *= addion;
		//	break;
		//default:
		//	return;
		//}
		//damage = uint32(result);
	}
	else if (me->GetMap()->IsDungeon())
	{
		damage = uint32(float(damage) * (1.0f / BotUtility::DungeonBotEndureModify));
	}
}
