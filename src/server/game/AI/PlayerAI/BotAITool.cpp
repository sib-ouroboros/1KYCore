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

#include "DB2Structure.h"
#include "BotAITool.h"
#include "Pet.h"
#include "PlayerBotSession.h"
#include "Map.h"
#include "Group.h"
#include "Language.h"
#include "SpellAuras.h"
#include "SpellMgr.h"
#include "WorldSession.h"
#include "SpellHistory.h"
#include "Item.h"
#include "Bag.h"
#include "MotionMaster.h"
#include <cmath>

float BotUtility::BattlegroundScoreRate = 1.0f;
float BotUtility::DungeonBotDamageModify = 1.0f;
float BotUtility::DungeonBotEndureModify = 1.0f;
bool BotUtility::BotCanForceRevive = false;
bool BotUtility::BotCanSettingToMaster = true;
int32 BotUtility::BotCritTakenAddion = 1;
bool BotUtility::ControllSpellDiminishing = true;
bool BotUtility::ControllSpellFromDmgBreak = true;
bool BotUtility::DownBotArenaTeam = false;
bool BotUtility::ArenaIsHell = false;
uint32 BotUtility::BotArenaTeamTactics = 1;
bool BotUtility::DisableDKQuest = false;

SpellEntry* BotUtility::BuildNewArenaSpellEntry()
{
	const SpellEntry* pSpellEntry = sSpellStore.LookupEntry(72221);
	if (!pSpellEntry || true)
		return NULL;

	SpellEntry* newSpellEntry = new SpellEntry(*pSpellEntry);
	newSpellEntry->ID = ARENA_PLAYER_BOT_AURA;
	/*SpellEffectEntry* Effect[] = {newSpellEntry->GetSpellEffect0(0), newSpellEntry->GetSpellEffect0(1), newSpellEntry->GetSpellEffect0(2)};
	Effect[0]->Effect = 6;
	Effect[1]->Effect = 6;
	Effect[2]->Effect = 6;
    Effect[0]->EffectDieSides = 1;
    Effect[1]->EffectDieSides = 1;
    Effect[2]->EffectDieSides = 1;
    Effect[0]->EffectBasePoints = 25;
    Effect[1]->EffectBasePoints = 15;
    Effect[2]->EffectBasePoints = -24;
    Effect[0]->EffectAura = 79;
    Effect[1]->EffectAura = 65;
    Effect[2]->EffectAura = 87;
    Effect[0]->EffectMiscValue[0] = 127;
    Effect[1]->EffectMiscValue[0] = 127;
    Effect[2]->EffectMiscValue[0] = 127;
    Effect[0]->EffectMiscValue[1] = 127;
    Effect[1]->EffectMiscValue[1] = 127;
    Effect[2]->EffectMiscValue[1] = 127;
	//newSpellEntry->Attributes &= ~(SpellAttr0::SPELL_ATTR0_CANT_CANCEL);
	//newSpellEntry->Attributes &= ~(SpellAttr0::SPELL_ATTR0_HIDE_IN_COMBAT_LOG);
	//newSpellEntry->Attributes |= SpellAttr0::SPELL_ATTR0_PASSIVE;
	//newSpellEntry->AttributesEx4 |= SpellAttr4::SPELL_ATTR4_USABLE_IN_ARENA;*/

	return newSpellEntry;
}

void BotUtility::ModifySpecialSpells()
{
    // Spell ID 8690 = Hearthstone
    if (SpellInfo const* pSpellEntry = sSpellMgr->GetSpellInfo(8690))
	{
        // CastTimeEntry and CategoryRecoveryTime are non-const members, so we cast away constness
        SpellInfo* spell = const_cast<SpellInfo*>(pSpellEntry);

        // Set cast time to entry ID 6 from SpellCastTimes.dbc
        spell->CastTimeEntry = sSpellCastTimesStore.LookupEntry(6);

        // Set category recovery time to 30 seconds
        spell->CategoryRecoveryTime = 30000;
	}
}

//void BotUtility::BuildNewArenaHellSpells(SpellInfoMap& spellMap)
//{
	
//}

void BotUtility::AddArenaBotSpellsByPlayer(Player* player)
{
	if (!player)
		return;
	if (!player->HasAura(ARENA_PLAYER_BOT_AURA))
	{
		if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_PLAYER_BOT_AURA))
			Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
	}
	if (!BotUtility::ArenaIsHell)
		return;
	switch (player->getClass())
	{
	case Classes::CLASS_WARRIOR:
		if (!player->HasAura(ARENA_WARRIOR_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_WARRIOR_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_PALADIN:
		if (!player->HasAura(ARENA_PALADIN_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_PALADIN_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_ROGUE:
		if (!player->HasAura(ARENA_ROGUE_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_ROGUE_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_DRUID:
		if (!player->HasAura(ARENA_DRUID_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_DRUID_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_HUNTER:
		if (!player->HasAura(ARENA_HUNTER_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_HUNTER_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_SHAMAN:
		if (!player->HasAura(ARENA_SHAMAN_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_SHAMAN_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_MAGE:
		if (!player->HasAura(ARENA_MAGE_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_MAGE_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_WARLOCK:
		if (!player->HasAura(ARENA_WARLOCK_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_WARLOCK_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	case Classes::CLASS_PRIEST:
		if (!player->HasAura(ARENA_PRIEST_BOT_AURA))
		{
			if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(ARENA_PRIEST_BOT_AURA))
				Aura::TryRefreshStackOrCreate(spellInfo, player->GetGUID(), MAX_EFFECT_MASK, player, player);
		}
		break;
	}
}

void BotUtility::RemoveArenaBotSpellsByPlayer(Player* player)
{
	if (!player)
		return;
	if (player->HasAura(ARENA_PLAYER_BOT_AURA))
		player->RemoveOwnedAura(ARENA_PLAYER_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_WARRIOR_BOT_AURA))
		player->RemoveOwnedAura(ARENA_WARRIOR_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_PALADIN_BOT_AURA))
		player->RemoveOwnedAura(ARENA_PALADIN_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_ROGUE_BOT_AURA))
		player->RemoveOwnedAura(ARENA_ROGUE_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_DRUID_BOT_AURA))
		player->RemoveOwnedAura(ARENA_DRUID_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_HUNTER_BOT_AURA))
		player->RemoveOwnedAura(ARENA_HUNTER_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_SHAMAN_BOT_AURA))
		player->RemoveOwnedAura(ARENA_SHAMAN_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_MAGE_BOT_AURA))
		player->RemoveOwnedAura(ARENA_MAGE_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_WARLOCK_BOT_AURA))
		player->RemoveOwnedAura(ARENA_WARLOCK_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	if (player->HasAura(ARENA_PRIEST_BOT_AURA))
		player->RemoveOwnedAura(ARENA_PRIEST_BOT_AURA, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
}

bool BotUtility::SpellHasReady(Player* player, uint32 spellID)
{
    if (!player || spellID == 0)
        return false;
    SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellID);
    if (!spellInfo || spellInfo->IsPassive())
        return false;
    if (player->GetSpellHistory()->HasGlobalCooldown(spellInfo))
        return false;
    if (player->GetSpellHistory()->IsReady(spellInfo))
        return true;
    return false;
}

uint32 BotUtility::GetFirstNumberByString(std::string text)
{
	char numStr[21] = { 0 };
	char* pCur = numStr;
	const char* pText = text.c_str();
	int count = text.size();
	bool start = false;
	for (int i = 0; i < count; ++i)
	{
		char c = pText[i];
		if (c >= '0' && c <= '9')
		{
			start = true;
			*pCur = c;
			++pCur;
		}
		else if (start)
			break;
	}
	return (uint32)atoi(numStr);
}

std::string BotUtility::BuildItemLinkText(const ItemTemplate* pItemTemplate)
{
	if (!pItemTemplate)
		return "";
	std::string text = sObjectMgr->GetTrinityStringForDBCLocale(TrinityStrings::LANG_ITEM_LIST_CHAT);// , LocaleConstant::LOCALE_zhTW);
	return Trinity::StringFormat(text.c_str(), pItemTemplate->BasicData->ID, pItemTemplate->BasicData->ID);
}

void BotUtility::UpdatePlayerBotRoll(Player* player)
{
	if (!player)
		return;
	Group* pGroup = player->GetGroup();
	if (!pGroup)
		return;
	/*Rolls& rolls = pGroup->GetAllRolls();
	for (Rolls::iterator iter = rolls.begin(); iter != rolls.end(); ++iter)
	{
		Roll* roll = (*iter);
		if (!roll->isValid())
			continue;
		if (roll->rolledPlayers.find(player->GetGUID()) != roll->rolledPlayers.end())
			continue;
		if (roll->totalPass > 0 || roll->totalNeed > 0 || roll->totalGreed > 0)
		{
			roll->rolledPlayers.insert(player->GetGUID());
			pGroup->PlayerBotRoll(player, *roll);
			break;
		}
	}*/
}

Item* BotUtility::FindItemFromAllBag(Player* player, uint32 entry, bool destroy)
{
	if (!player || entry == 0)
		return NULL;
	for (uint8 slot = InventoryPackSlots::INVENTORY_SLOT_ITEM_START; slot < InventoryPackSlots::INVENTORY_SLOT_ITEM_END; slot++)
	{
		Item* pItem = player->GetItemByPos(255, slot);
		if (!pItem)
			continue;
		const ItemTemplate* pTemplate = pItem->GetTemplate();
		if (!pTemplate || pTemplate->GetId() != entry)
			continue;
		if (destroy)
		{
			player->DestroyItem(255, slot, true);
			pItem = NULL;
		}
		return pItem;
	}
	for (uint8 i = INVENTORY_SLOT_BAG_START; i < INVENTORY_SLOT_BAG_END; ++i)
	{
		if (Bag* pBag = player->GetBagByPos(i))
		{
			for (uint32 j = 0; j < pBag->GetBagSize(); j++)
			{
				Item* pItem = pBag->GetItemByPos(uint8(j));
				if (!pItem)
					continue;
				const ItemTemplate* pTemplate = pItem->GetTemplate();
				if (!pTemplate || pTemplate->GetId() != entry)
					continue;
				if (destroy)
				{
					player->DestroyItem(255, uint8(j), true);
					pItem = NULL;
				}
				return pItem;
			}
		}
	}
	return NULL;
}

Item* BotUtility::FindItemFromAllBag(Player* player, uint32 entry, uint8& bag, uint8& index)
{
	if (!player || entry == 0)
		return NULL;
	for (uint8 slot = InventoryPackSlots::INVENTORY_SLOT_ITEM_START; slot < InventoryPackSlots::INVENTORY_SLOT_ITEM_END; slot++)
	{
		Item* pItem = player->GetItemByPos(255, slot);
		if (!pItem)
			continue;
		const ItemTemplate* pTemplate = pItem->GetTemplate();
		if (!pTemplate || pTemplate->GetId() != entry)
			continue;
		bag = 255;
		index = slot;
		return pItem;
	}
	for (uint8 i = INVENTORY_SLOT_BAG_START; i < INVENTORY_SLOT_BAG_END; ++i)
	{
		if (Bag* pBag = player->GetBagByPos(i))
		{
			for (uint32 j = 0; j < pBag->GetBagSize(); j++)
			{
				Item* pItem = pBag->GetItemByPos(uint8(j));
				if (!pItem)
					continue;
				const ItemTemplate* pTemplate = pItem->GetTemplate();
				if (!pTemplate || pTemplate->GetId() != entry)
					continue;
				bag = i;
				index = uint8(j);
				return pItem;
			}
		}
	}
	return NULL;
}

bool BotUtility::DestroyItemFromAllBag(Player* player, Item* pItem)
{
	if (!player || !pItem)
		return false;
	for (uint8 slot = InventoryPackSlots::INVENTORY_SLOT_ITEM_START; slot < InventoryPackSlots::INVENTORY_SLOT_ITEM_END; slot++)
	{
		Item* pBagItem = player->GetItemByPos(255, slot);
		if (!pBagItem || pBagItem != pItem)
			continue;
		player->DestroyItem(255, slot, true);
		return true;
	}
	for (uint8 i = INVENTORY_SLOT_BAG_START; i < INVENTORY_SLOT_BAG_END; ++i)
	{
		if (Bag* pBag = player->GetBagByPos(i))
		{
			for (uint32 j = 0; j < pBag->GetBagSize(); j++)
			{
				Item* pBagItem = pBag->GetItemByPos(uint8(j));
				if (!pBagItem || pBagItem != pItem)
					continue;
				player->DestroyItem(255, uint8(j), true);
				return true;
			}
		}
	}
	return false;
}

Item* BotUtility::StoreNewItemByEntry(Player* player, uint32 entry, int32 count)
{
	if (!player || entry == 0 || count == 0)
		return NULL;
	ItemTemplate const* pTemplate = sObjectMgr->GetItemTemplate(entry);
	if (!pTemplate)
		return NULL;
	uint32 noSpaceForCount = 0;
	ItemPosCountVec dest;
	InventoryResult msg = player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, pTemplate->GetId(), count, &noSpaceForCount);
	if (msg != EQUIP_ERR_OK)
		count -= noSpaceForCount;
	if (count <= 0 || dest.empty())
		return NULL;
	Item* itemInst = player->StoreNewItem(dest, pTemplate->GetId(), true, GenerateItemRandomPropertyId(pTemplate->GetId()));
	return itemInst;
}

uint32 BotUtility::FindMaxRankSpellByExist(Player* player, uint32 spellID)
{
	if (spellID == 0)
		return 0;
	uint32 selectSpell = sSpellMgr->GetLastSpellInChain(spellID);
	if (selectSpell == 0)
	{
		if (player->HasSpell(spellID))
			return spellID;
		return 0;
	}
	while (!player->HasSpell(selectSpell))
	{
		selectSpell = sSpellMgr->GetPrevSpellInChain(selectSpell);
		if (selectSpell == 0)
			return 0;
	}
	return selectSpell;
}

void BotUtility::PlayerBotTogglePVP(Player* player, bool pvp)
{
	if (!player || !player->IsPlayerBot())
		return;
	//WorldPacket opcode(1);
	//opcode << uint8(pvp ? 1 : 0);
	//player->GetSession()->HandleTogglePvP(opcode);
}

uint32 BotUtility::FindPetMaxRankSpellByExist(Player* player, uint32 spellID)
{
	if (spellID == 0)
		return 0;
	Pet* pPet = player->GetPet();
	if (!pPet)
		return 0;
	uint32 selectSpell = sSpellMgr->GetLastSpellInChain(spellID);
	if (selectSpell == 0)
	{
		if (pPet->HasSpell(spellID))
			return spellID;
		return 0;
	}
	while (!pPet->HasSpell(selectSpell))
	{
		selectSpell = sSpellMgr->GetPrevSpellInChain(selectSpell);
		if (selectSpell == 0)
			return 0;
	}
	return selectSpell;
}

Position BotUtility::FindRadiusByNearDistance(Unit* pTargetUnit, float range, Unit* pRefUnit)
{
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos;
	//float selectAngle = pTargetUnit->GetOrientation() * (-1);
	float minDist = 999999.0f;
	std::list<Position> allPosition;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	{
		Position pos;
		pRefUnit->GetFirstCollisionPosition(range, angle);
		float dist = pRefUnit->GetDistance(pos);
		if (!pTargetUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
			continue;
		allPosition.push_back(pos);
	}
	if (allPosition.empty())
		return pTargetUnit->GetPosition();
	for (Position pos : allPosition)
	{
		float dist = pTargetUnit->GetDistance(pos);
		if (dist < minDist)
		{
			minDist = dist;
			targetPos = pos;
		}
	}
	return targetPos;
}

Position BotUtility::FindRadiusByFarDistance(Unit* pTargetUnit, float range, Unit* pRefUnit)
{
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos = pTargetUnit->GetPosition();
	//float selectAngle = pTargetUnit->GetOrientation() * (-1);
	float maxDist = 0.0f;
	std::list<Position> allPosition;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	{
		Position pos;
		pRefUnit->GetFirstCollisionPosition(range, angle);
		float dist = pRefUnit->GetDistance(pos);
		if (!pTargetUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
			continue;
		allPosition.push_back(pos);
	}
	if (allPosition.empty())
		return targetPos;
	for (Position pos : allPosition)
	{
		float dist = pTargetUnit->GetDistance(pos);
		if (dist > maxDist)
		{
			maxDist = dist;
			targetPos = pos;
		}
	}
	return targetPos;
}

bool BotUtility::FindFirstCollisionPosition(Unit* pTargetUnit, float range, Unit* pRefUnit, Position& outPos)
{
	if (range < 3.0f || range <= pRefUnit->GetObjectSize() || pRefUnit->GetDistance(pTargetUnit->GetPosition()) >= range)
		return false;
	Map* pMap = pRefUnit->GetMap();
	if (pTargetUnit->GetMap() != pMap)
		return false;
	//G3D::Vector3 refUnitV3 = pRefUnit->GetVector3();
	//G3D::Vector3 tarUnitV3 = pTargetUnit->GetVector3();
	//G3D::Vector3 distV3 = tarUnitV3 - refUnitV3;
	//if (distV3.length() < 1.0f)
	//	return false;
	//G3D::Vector3 dir = distV3.directionOrZero();
	//G3D::Vector3 target = refUnitV3 + dir * range;
	//target.z = pMap->GetHeight(pTargetUnit->GetPhaseMask(), target.x, target.y, target.z);

	//G3D::Vector3 searchPos = target;
	//float once = range * 0.1f;
	//while (!pTargetUnit->IsWithinLOS(searchPos.x, searchPos.y, searchPos.z))
	//{
	//	if (range <= once)
	//		return false;
	//	range -= once;
	//	searchPos = refUnitV3 + dir * range;
	//	searchPos.z = pMap->GetHeight(pTargetUnit->GetPhaseMask(), searchPos.x, searchPos.y, searchPos.z);
	//}

	float once = range * 0.2f;
	std::vector<Position> canPoss;
	for (float angle = 0; angle < (float(M_PI) * 2.0f); angle += float(M_PI_4))
	{
		float calcRange = range;
		float distX = pRefUnit->GetPositionX() + calcRange * std::cos(angle);
		float distY = pRefUnit->GetPositionY() + calcRange * std::sin(angle);
		float distZ = pMap->GetHeight(pTargetUnit->GetPhaseShift(), distX, distY, pRefUnit->GetPositionZ());
		while (!pTargetUnit->IsWithinLOS(distX, distY, distZ))
		{
			if (calcRange <= once)
				break;
			calcRange -= once;
			distX = pRefUnit->GetPositionX() + calcRange * std::cos(angle);
			distY = pRefUnit->GetPositionY() + calcRange * std::sin(angle);
			distZ = pMap->GetHeight(pTargetUnit->GetPhaseShift(), distX, distY, pRefUnit->GetPositionZ());
		}
		if (calcRange >= range * 0.75f)
			canPoss.push_back(Position(distX, distY, distZ, pTargetUnit->GetOrientation()));
	}
	Position calcPos;
	if (!canPoss.empty())
	{
		calcPos = canPoss[urand(0, canPoss.size() - 1)];
		float minDist = 0;
		for (Position pos : canPoss)
		{
			float dist = pTargetUnit->GetDistance(pos);
			if (dist < minDist)
			{
				calcPos = pos;
				minDist = dist;
			}
		}
	}
	else
		return false;

	outPos.m_positionX = calcPos.GetPositionX();
	outPos.m_positionY = calcPos.GetPositionY();
	outPos.m_positionZ = calcPos.GetPositionZ();
	return true;
}

void BotUtility::TryTeleportPlayerPet(Player* player, bool force)
{
	if (!player)
		return;
	Pet* pet = player->GetPet();
	if (!pet)
		return;
	if (!player->IsInWorld() || !pet->IsInWorld() || player->GetMap() != pet->GetMap())
		return;
	if (!force && player->GetDistance(pet->GetPosition()) < (BOTAI_SEARCH_RANGE * 2))
		return;

	if (pet->IsAlive() && pet->IsInCombat())
		pet->CombatStop(true);
	pet->NearTeleportTo(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(), player->GetOrientation());
}

void BotAIHorrorState::UpdateHorror(uint32 diff)
{
	if (!me)
		return;
	//if (me->IsStopped())
	//{
	//	float rndOffset = 40.0f;
	//	float x = me->GetPositionX() + frand(-rndOffset, rndOffset);
	//	float y = me->GetPositionY() + frand(-rndOffset, rndOffset);
	//	float z = me->GetPositionZ();
	//	me->GetMap()->GetHeight(me->GetPhaseMask(), x, y, z);
	//	me->GetMotionMaster()->MoveCharge(x, y, z, me->GetSpeed(UnitMoveType::MOVE_RUN));
	//}
	if (me->GetDistance(m_CurHorrorPos) < 3.0f)
	{
        m_CurHorrorPos = GetNewHorrorPos();
	}
	me->GetMotionMaster()->Clear();
	me->GetMotionMaster()->MovePoint(1, m_CurHorrorPos);
}

Position BotAIHorrorState::GetNewHorrorPos()
{
	std::vector<float> angles;
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos = me->GetPosition();
	float maxDist = 0.0f;
	std::list<Position> allPosition;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
		angles.push_back(angle);
	Trinity::Containers::RandomShuffle(angles);
	for (float angle : angles)
	{
		Position pos;
		me->GetFirstCollisionPosition(BOTAI_SEARCH_RANGE, angle);
		pos.m_positionZ = me->GetMap()->GetHeight(me->GetPhaseShift(), pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ());
		if (me->GetDistance(pos) > (BOTAI_SEARCH_RANGE * 0.8f))
			return pos;
		allPosition.push_back(pos);
	}
	if (allPosition.empty())
		return targetPos;
	for (Position pos : allPosition)
	{
		float dist = me->GetDistance(pos);
		if (dist > maxDist)
		{
			maxDist = dist;
			targetPos = pos;
		}
	}
	return targetPos;
}

Position BotAIHorrorState::GetNewHorrorPosByRange(Player* player, float distance)
{
	if (!player)
		return Position();
	std::vector<float> angles;
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos = player->GetPosition();
	float maxDist = 0.0f;
	std::vector<Position> allPosition;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
		angles.push_back(angle);
	Trinity::Containers::RandomShuffle(angles);
	for (float angle : angles)
	{
		Position pos;
		player->GetFirstCollisionPosition(distance, angle);
		pos.m_positionZ = player->GetMap()->GetHeight(player->GetPhaseShift(), pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ());
		if (player->GetDistance(pos) >(distance * 0.5f))
			allPosition.push_back(pos);
	}
	if (allPosition.empty())
		return targetPos;
	return allPosition[urand(0, allPosition.size() - 1)];
}
