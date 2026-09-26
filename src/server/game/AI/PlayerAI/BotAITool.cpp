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
#include "BotBGAIMovement.h"
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

void BotAITeleport::SetTeleport(Position& telePos)
{
	if (m_Teleporting)
		return;
	UpdateMapID();
	m_TeleportPositon = telePos;
	m_Teleporting = true;
	m_TeleportStep = 1;
}

void BotAITeleport::SetTeleport(uint32 mapID, Position& telePos)
{
	if (m_Teleporting)
		return;
	
	m_MapId = mapID;
	m_TeleportPositon = telePos;
	m_Teleporting = true;
	m_TeleportStep = 1;
}

void BotAITeleport::SetTeleport(Player* pTarget, float offset)
{
	if (m_Teleporting)
		return;
	if (!pTarget || !pTarget->GetMap() || !pTarget->IsInWorld() || me->InBattlegroundQueue() || me->InBattleground())
		return;

	Position pos = pTarget->GetPosition();
	float x = pos.GetPositionX() + ((offset != 0) ? frand(offset * (-1), offset) : 0);
	float y = pos.GetPositionY() + ((offset != 0) ? frand(offset * (-1), offset) : 0);
	float z = pos.GetPositionZ();
	pTarget->GetMap()->GetHeight(pTarget->GetPhaseShift(), x, y, z);

	me->CombatStop(true);
	m_TeleportPositon = Position(x, y, z, pos.GetOrientation());
	m_MapId = pTarget->GetMapId();
	m_Teleporting = true;
	m_TeleportStep = 1;
}

void BotAITeleport::ClearTeleport()
{
	m_TeleportPositon.m_positionX = m_TeleportPositon.m_positionY = m_TeleportPositon.m_positionZ = 0;
	m_Teleporting = false;
	UpdateMapID();
	m_TeleportStep = 0;
}

void BotAITeleport::Update(uint32 diff, BotBGAIMovement* pMovement)
{
	if (!m_Teleporting || !pMovement)
		return;
	if (me->isMoving())
	{
		pMovement->ClearMovement();
		me->GetMotionMaster()->Clear();
		//me->StopMoving();
		//return;
	}
	if (me->IsCanDelayTeleport() || me->IsHasDelayedTeleport())
		return;
	if (m_TeleportStep > 0)//m_TeleportPositon.m_positionZ != 0)
	{
		if (m_TeleportStep == 1)
		{
			float x = m_TeleportPositon.GetPositionX();
			float y = m_TeleportPositon.GetPositionY();
			float z = m_TeleportPositon.GetPositionZ();
			if (!me->TeleportTo(m_MapId, x, y, z, me->GetOrientation()))
			{
				ClearTeleport();
				return;
			}
			m_TeleportStep = 2;
			if (me->GetMapId() != m_MapId)
			{
				WorldSession* pSession = me->GetSession();
				if (pSession)
					pSession->HandleMoveWorldportAck();
				m_TeleportStep = 3;
			}
		}
		else if (m_TeleportStep == 2)
		{
			me->UpdatePosition(m_TeleportPositon, true);
			WorldSession* pSession = me->GetSession();
            WorldPacket opcode2(CMSG_MOVE_TELEPORT_ACK);
            WorldPackets::Movement::MoveTeleportAck pakcet(std::move(opcode2));
            pakcet.MoverGUID = me->GetGUID();
			pSession->HandleMoveTeleportAck(pakcet);
			m_TeleportStep = 3;
		}
		else if (m_TeleportStep == 3)
		{
			// =====================================================
			// SylvaniaCore : envoi mort retire.
			//
			// Le bloc supprime ici diffusait un paquet portant
			// l'opcode CLIENT CMSG_MOVE_FALL_LAND. WorldSession le
			// REFUSE systematiquement -- « Prevented sending of
			// opcode 14841 with non existing handler » -- et ecrit
			// une ligne d'ERREUR a chaque tentative. Signale par un
			// utilisateur de SylvaniaCore : des milliers de lignes
			// par match de champ de bataille.
			//
			// Il n'accomplissait donc rien. La reconstruction de
			// l'objet ci-dessous, ajoutee precedemment pour pallier
			// son inefficacite, reste seule en charge du travail.
			// =====================================================
			me->CombatStop(true);
			me->SetSelection(ObjectGuid::Empty);
			// SylvaniaCore : le paquet diffuse ci-dessus porte un opcode CLIENT
			// (CMSG_MOVE_FALL_LAND), que les clients voisins ne savent pas lire.
			// Resultat : le bot avait bien change de place cote serveur - positions
			// identiques en base - mais restait affiche a son ancien emplacement,
			// jusqu au prochain passage hors puis dans le champ de vision. On force
			// donc la reconstruction de l objet chez les joueurs alentour.
			me->DestroyForNearbyPlayers();
			me->UpdateObjectVisibility(true);
			// mod-playerbots (PlayerbotAI::HandleTeleportAck) vide le MotionMaster
			// et arrete le mouvement a chaque acquittement de teleport. Sans cela,
			// le generateur de suivi encore en place fait repartir le bot depuis
			// l ancienne trajectoire.
			me->GetMotionMaster()->Clear(true);
			me->StopMoving();
			m_TeleportPositon.m_positionX = m_TeleportPositon.m_positionY = m_TeleportPositon.m_positionZ = 0;
			m_TeleportStep = 0;
		}
	}
	else
		m_Teleporting = false;
}

void BotAIStoped::UpdatePosition(uint32 diff)
{
	//if (me->HasUnitState(UNIT_STATE_CASTING))
	//	return;
	Position currentPos = me->GetPosition();
	if (HasDifference(m_lastPosition, currentPos))
	{
		//SyncPosition(currentPos, MSG_MOVE_START_FORWARD);
		me->UpdatePosition(currentPos);
		m_lastPosition = currentPos;
		m_updateTick = 0;
	}
	//else
	//{
	//	m_updateTick += diff;
	//	if (m_updateTick >= BOTAI_UPDATE_TICK * 2)
	//	{
	//		SyncPosition(currentPos, MSG_MOVE_STOP);
	//		m_updateTick = 0;
	//		m_lastPosition = currentPos;
	//		me->StopMoving();
	//	}
	//}
}

bool BotAIStoped::HasDifference(Position& pos1, Position& pos2)
{
	float posGap = 0.2f;
	if ((pos1.GetVector3() - pos2.GetVector3()).length() > posGap)
		return true;
	if (fabsf(pos1.GetOrientation() - pos2.GetOrientation()) > posGap)
		return true;
	return false;
}

void BotAIStoped::SyncPosition(Position pos, uint32 opcode)
{
	//if (m_SyncTick < 3)
	//{
	//	++m_SyncTick;
	//	return;
	//}
	//m_SyncTick = 0;
	if (me->IsFlying())
		return;

	WorldSession* pSession = me->GetSession();
	MovementInfo movementInfo;
	movementInfo.flags = (opcode == CMSG_MOVE_START_FORWARD) ? MovementFlags(MOVEMENTFLAG_FORWARD) : 0;
	movementInfo.pos = pos;
	movementInfo.time = getMSTime(); // +(opcode == MSG_MOVE_START_FORWARD) ? BOTAI_UPDATE_TICK : 0;
	movementInfo.guid = me->GetGUID();
	//movementInfo.fall.fallTime = me->m_movementInfo.fall.fallTime;
	WorldPacket data(opcode);
	data << me->GetGUID();
	data << movementInfo;
	me->SendMessageToSet(&data, me);
}

void BotAIHorrorState::UpdateHorror(uint32 diff, BotBGAIMovement* movement)
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
		if (movement && 0)
			m_CurHorrorPos = FindNewHorrorPos(movement);
		else
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

Position BotAIHorrorState::FindNewHorrorPos(BotBGAIMovement* movement)
{
	float moveMaxDistance = 0;
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos = me->GetPosition();
	float maxDist = 0.0f;
	std::list<Position> allPosition;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	{
		for (float dist = 0.1f; dist <= 1.0f; dist += 0.1f)
		{
			float distX = me->GetPositionX() + (moveMaxDistance*dist) * std::cos(angle);
			float distY = me->GetPositionY() + (moveMaxDistance*dist) * std::sin(angle);
			float distZ = me->GetPositionZ();
			//distZ = me->GetMap()->GetHeight(me->GetPhaseMask(), distX, distY, distZ);
			Position pos = me->GetPosition();
			if (!movement->SimulationMovementTo(distX, distY, distZ, pos))
				break;
			allPosition.push_back(pos);
		}
	}
	if (allPosition.empty())
		return GetNewHorrorPos();
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

BotAIUsePotion::BotAIUsePotion(Player* self) :
me(self),
m_NeedMana(true)
{
	uint8 cls = me->getClass();
	if (cls == 1 || cls == 4)
		m_NeedMana = false;

	m_LifeVials.push_back(PotionInfo(70, 33447));
	m_LifeVials.push_back(PotionInfo(55, 22829));
	m_LifeVials.push_back(PotionInfo(45, 13446));
	m_LifeVials.push_back(PotionInfo(35, 3928));
	m_LifeVials.push_back(PotionInfo(21, 1710));
	m_LifeVials.push_back(PotionInfo(12, 929));
	m_LifeVials.push_back(PotionInfo(3, 858));
	m_LifeVials.push_back(PotionInfo(1, 118));

	m_ManaVials.push_back(PotionInfo(70, 33448));
	m_ManaVials.push_back(PotionInfo(55, 22832));
	m_ManaVials.push_back(PotionInfo(49, 13444));
	m_ManaVials.push_back(PotionInfo(41, 13443));
	m_ManaVials.push_back(PotionInfo(31, 6149));
	m_ManaVials.push_back(PotionInfo(22, 3827));
	m_ManaVials.push_back(PotionInfo(14, 3385));
	m_ManaVials.push_back(PotionInfo(5, 2455));
}

bool BotAIUsePotion::TryUsePotion()
{
	if (!me->IsInCombat() || me->IsMounted() || me->HasUnitState(UNIT_STATE_CASTING))
		return false;
	if (!m_NeedMana)
	{
		float healPct = me->GetHealthPct();
		if (healPct < 65)
		{
			return TryUseLifeVial();
		}
	}
	else if (me->InBattleground())
	{
		float manaPer = (float)me->GetPower(POWER_MANA) / (float)me->GetMaxPower(POWER_MANA);
		if (manaPer * 100 < 15)
		{
			return TryUseManaVial();
		}
		else if (me->GetHealthPct() < 60)
		{
			return TryUseLifeVial();
		}
	}
	else
	{
		float healPct = me->GetHealthPct();
		if (healPct < 30)
		{
			return TryUseLifeVial();
		}
		else
		{
			float per = (float)me->GetPower(POWER_MANA) / (float)me->GetMaxPower(POWER_MANA);
			float manaPct = per * 100;
			if (manaPct < 75)
				return TryUseManaVial();
		}
	}
	return false;
}

bool BotAIUsePotion::TryUseLifeVial()
{
	Item* pItem = FindLifeVial();

	if (!pItem)
		return false;

	SpellCastTargets targets;
	targets.SetTargetMask(0);

    // Fallback misc array for server-side cast (Bots don't have a client)
    int32 dummyMisc[2] = { 0, 0 };

	if (me->CastItemUseSpell(pItem, targets, ObjectGuid::Empty, dummyMisc))
		return true;
	return false;
}

bool BotAIUsePotion::TryUseManaVial()
{
	Item* pItem = FindManaVial();

	if (!pItem)
		return false;

	SpellCastTargets targets;
	targets.SetTargetMask(0);

    // Fallback misc array for server-side cast (Bots don't have a client)
    int32 dummyMisc[2] = { 0, 0 };

	if (me->CastItemUseSpell(pItem, targets, ObjectGuid::Empty, dummyMisc))
		return true;
	return false;
}

Item* BotAIUsePotion::FindLifeVial()
{
	uint32 level = me->getLevel();
	uint32 entry = 0;
	for (PotionInfo& info : m_LifeVials)
	{
		if (info.level <= level)
		{
			entry = info.potionEntry;
			break;
		}
	}
	if (entry == 0)
		return NULL;
	Item* pItem = BotUtility::FindItemFromAllBag(me, entry);
	if (!pItem)
		pItem = BotUtility::StoreNewItemByEntry(me, entry, 5);
	return pItem;
}

Item* BotAIUsePotion::FindManaVial()
{
	uint32 level = me->getLevel();
	uint32 entry = 0;
	for (PotionInfo& info : m_ManaVials)
	{
		if (info.level <= level)
		{
			entry = info.potionEntry;
			break;
		}
	}
	if (entry == 0)
		return NULL;
	Item* pItem = BotUtility::FindItemFromAllBag(me, entry);
	if (!pItem)
		pItem = BotUtility::StoreNewItemByEntry(me, entry, 5);
	return pItem;
}

BotAIFastAid::BotAIFastAid(Player* self) :
me(self),
m_NoAidBuff(11196)
{
	m_FastAids.push_back(PotionInfo(71, 45544));
	m_FastAids.push_back(PotionInfo(61, 45543));
	m_FastAids.push_back(PotionInfo(51, 27030));
	m_FastAids.push_back(PotionInfo(41, 18608));
	m_FastAids.push_back(PotionInfo(31, 10838));
	m_FastAids.push_back(PotionInfo(21, 7926));
	m_FastAids.push_back(PotionInfo(11, 3267));
	m_FastAids.push_back(PotionInfo(1, 746));
}

void BotAIFastAid::CheckPlayerFastAid()
{
	uint8 level = me->getLevel();
	for (PotionInfo& info : m_FastAids)
	{
		if (level >= info.level)
		{
			if (!me->HasSpell(info.potionEntry))
				me->LearnSpell(info.potionEntry, false);
		}
		else
		{
			if (me->HasSpell(info.potionEntry))
				me->RemoveSpell(info.potionEntry, false, false);
		}
	}
}

bool BotAIFastAid::TryDoingFastAidForMe()
{
	if (!CanFastAidByTarget(me))
		return false;
	uint32 fastAidSpellID = GetFastAidSpell();
	if (fastAidSpellID == 0)
		return false;
	SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(fastAidSpellID);
	if (!spellInfo)
		return false;
	me->StopMoving();
	me->GetMotionMaster()->Clear();
    Spell* spell = new Spell(me, spellInfo, TriggerCastFlags::TRIGGERED_NONE, ObjectGuid::Empty);
	spell->m_CastItem = NULL;
	SpellCastTargets targets;
	targets.SetUnitTarget(me);
	auto castResult = spell->prepare(&targets);
	if (castResult != SpellCastResult::SPELL_CAST_OK)
		return false;
	return true;
}

uint32 BotAIFastAid::GetFastAidSpell()
{
	uint8 level = me->getLevel();
	for (PotionInfo& info : m_FastAids)
	{
		if (level >= info.level)
		{
			if (me->HasSpell(info.potionEntry))
				return info.potionEntry;
		}
	}
	return 0;
}

bool BotAIFastAid::CanFastAidByTarget(Player* target)
{
	if (!target || !target->IsInWorld() || !target->IsAlive() || target->IsMounted() || target->HasAura(m_NoAidBuff))
		return false;
	if (me != target && me->IsValidAttackTarget(target))
		return false;
	if (!me->IsAlive() || me->HasUnitState(UNIT_STATE_CASTING) || target->GetHealthPct() > 75)
		return false;
	if ((me->HasAuraWithMechanic(1 << Mechanics::MECHANIC_CHARM)) || (me->HasAuraWithMechanic(1 << Mechanics::MECHANIC_FEAR)) ||
		(me->HasAuraWithMechanic(1 << Mechanics::MECHANIC_HORROR)) || (me->HasAuraWithMechanic(1 << Mechanics::MECHANIC_POLYMORPH)))
		return false;

	std::list<Player*> nearPlayer;
	target->GetPlayerListInGrid(nearPlayer, BOTAI_RANGESPELL_DISTANCE);
	for (Player* player : nearPlayer)
	{
		if (player->GetTeamId() == target->GetTeamId())
			continue;
		if (!player->IsValidAttackTarget(target))
			continue;
		if (player->GetTarget() != target->GetGUID())
			continue;
		return false;
	}
	NearCreatureList nearCreature;
	Trinity::AllWorldObjectsInRange checker(target, BOTAI_RANGESPELL_DISTANCE);
	Trinity::CreatureListSearcher<Trinity::AllWorldObjectsInRange> searcher(target, nearCreature, checker);
	//target->VisitNearbyGridObject(BOTAI_RANGESPELL_DISTANCE, searcher);
	for (Creature* pCreature : nearCreature)
	{
		if (pCreature->IsTotem())
			continue;
		if (!pCreature->IsValidAttackTarget(target))
			continue;
		if (pCreature->GetTarget() != target->GetGUID())
			continue;
		return false;
	}
	return true;
}

void BotAIFlee::UpdateFleeMovementByPVE(Unit* pMaster, Unit* pRefUnit, BotBGAIMovement* pMovement)
{
	if (!pMovement || !pRefUnit)
		return;
	if (m_FleeTick > 16 || me->IsFlying())
	{
		Clear();
		return;
	}
	if (m_cruxTime > 0)
	{
		uint32 curTick = getMSTime();
		if (!Fleeing() || m_cruxTime < curTick)
		{
			Clear();
			return;
		}
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
	}
	else if (Fleeing())
	{
		float fleeDistance = (m_FleeTarget->GetVector3() - me->GetVector3()).length();
		if (fleeDistance < 2.0f || fleeDistance > BOTAI_RANGESPELL_DISTANCE)
		{
			Clear();
			float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
			if (fleeDistance < CalcMaxFleeDistance(pRefUnit))
			{
				Position targetPos;
				if (!SearchPVEFleePosition(pMaster, pRefUnit, targetPos))
				{
					Clear();
					return;
				}
				m_FleeTarget = new Position(targetPos);
				pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
				++m_FleeTick;
			}
		}
		else
		{
			pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
			++m_FleeTick;
		}
	}
	else if (pRefUnit)
	{
		Position targetPos;
		if(!SearchPVEFleePosition(pMaster, pRefUnit, targetPos))
		{
			Clear();
			return;
		}
		m_FleeTarget = new Position(targetPos);
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
		++m_FleeTick;
	}
}

void BotAIFlee::UpdateFleeMovementByPVP(Unit* pRefUnit, BotBGAIMovement* pMovement)
{
	if (!pMovement)
		return;
	if (m_FleeTick > 16 || me->IsFlying())
	{
		Clear();
		return;
	}
	if (m_cruxTime > 0)
	{
		uint32 curTick = getMSTime();
		if (!Fleeing() || m_cruxTime < curTick)
		{
			Clear();
			return;
		}
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
	}
	else if (Fleeing())
	{
		float fleeDistance = (m_FleeTarget->GetVector3() - me->GetVector3()).length();
		if (fleeDistance < 2.0f || fleeDistance > BOTAI_RANGESPELL_DISTANCE)
		{
			Clear();
			float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
			if (fleeDistance < CalcMaxFleeDistance(pRefUnit))
			{
				fleeDistance = BOTAI_RANGESPELL_DISTANCE;// -fleeDistance;
				float onceAngle = float(M_PI) * 2.0f / 8.0f;
				Position targetPos;
				float selectAngle = me->GetOrientation() * (-1);
				float maxDist = 0.0f;
				for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
				{
					float dist = 0;
					Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
					if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
						continue;
					if (dist > maxDist)
					{
						maxDist = dist;
						targetPos = pos;
					}
				}
				if (maxDist == 0)
					return;
				m_FleeTarget = new Position(targetPos);
				pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
				++m_FleeTick;
			}
		}
		else
		{
			pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
			++m_FleeTick;
		}
	}
	else if (pRefUnit)
	{
		float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
		if (fleeDistance >= BOTAI_RANGESPELL_DISTANCE)
		{
			Clear();
			return;
		}
		fleeDistance = BOTAI_RANGESPELL_DISTANCE;// -fleeDistance;
		float onceAngle = float(M_PI) * 2.0f / 8.0f;
		Position targetPos;
		float selectAngle = me->GetOrientation() * (-1);
		float maxDist = 0.0f;
		for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
		{
			float dist = 0;
			Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
			if(!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
				continue;
			if (dist > maxDist)
			{
				maxDist = dist;
				targetPos = pos;
			}
		}
		if (maxDist == 0)
		{
			Clear();
			return;
		}
		m_FleeTarget = new Position(targetPos);
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
		++m_FleeTick;
	}
}

void BotAIFlee::UpdateFleeMovementByPosition(Unit* pRefUnit, Position centerPos, float maxPosDist, BotBGAIMovement* pMovement)
{
	if (!pMovement)
		return;
	if (m_FleeTick > 16 || me->IsFlying())
	{
		Clear();
		return;
	}
	if (m_cruxTime > 0)
	{
		uint32 curTick = getMSTime();
		if (!Fleeing() || m_cruxTime < curTick)
		{
			Clear();
			return;
		}
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
	}
	else if (Fleeing())
	{
		float fleeDistance = (m_FleeTarget->GetVector3() - me->GetVector3()).length();
		if (fleeDistance < 2.0f || fleeDistance > BOTAI_RANGESPELL_DISTANCE)
		{
			Clear();
			float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
			if (fleeDistance < CalcMaxFleeDistance(pRefUnit))
			{
				fleeDistance = BOTAI_RANGESPELL_DISTANCE;// -fleeDistance;
				float onceAngle = float(M_PI) * 2.0f / 8.0f;
				Position targetPos;
				float selectAngle = me->GetOrientation() * (-1);
				float maxDist = 0.0f;
				for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
				{
					float dist = 0;
					Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
					if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
						continue;
					if (centerPos.GetExactDist(&pos) >= maxPosDist)
						continue;
					if (dist > maxDist)
					{
						maxDist = dist;
						targetPos = pos;
					}
				}
				if (maxDist == 0)
					return;
				m_FleeTarget = new Position(targetPos);
				pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
				++m_FleeTick;
			}
		}
		else
		{
			pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
			++m_FleeTick;
		}
	}
	else if (pRefUnit)
	{
		float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
		if (fleeDistance >= BOTAI_RANGESPELL_DISTANCE)
		{
			Clear();
			return;
		}
		fleeDistance = BOTAI_RANGESPELL_DISTANCE;// -fleeDistance;
		float onceAngle = float(M_PI) * 2.0f / 8.0f;
		Position targetPos;
		float selectAngle = me->GetOrientation() * (-1);
		float maxDist = 0.0f;
		for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
		{
			float dist = 0;
			Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
			if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
				continue;
			if (centerPos.GetExactDist(&pos) >= maxPosDist)
				continue;
			if (dist > maxDist)
			{
				maxDist = dist;
				targetPos = pos;
			}
		}
		if (maxDist == 0)
		{
			Clear();
			return;
		}
		m_FleeTarget = new Position(targetPos);
		pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
		++m_FleeTick;
	}
}

void BotAIFlee::AddCruxFlee(uint32 durTime, Unit* pRefUnit, BotBGAIMovement* pMovement)
{
	if (!pMovement || !pRefUnit || !durTime)
		return;
	float fleeDistance = pRefUnit->GetObjectSize() + BOTAI_RANGESPELL_DISTANCE;
	float onceAngle = float(M_PI) * 2.0f / 8.0f;
	Position targetPos;
	float selectAngle = me->GetOrientation() * (-1);
	float maxDist = 0.0f;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	{
		float dist = 0;
		Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
		if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
			continue;
		if (dist > maxDist)
		{
			maxDist = dist;
			targetPos = pos;
		}
	}
	if (maxDist == 0)
	{
		return;
	}
	m_FleeTarget = new Position(targetPos);
	pMovement->MovementTo(m_FleeTarget->GetPositionX(), m_FleeTarget->GetPositionY(), m_FleeTarget->GetPositionZ());
	m_cruxTime = getMSTime() + durTime;
}

bool BotAIFlee::CanFleeToTargetPlayer(Player* player)
{
	if (!player)
		return false;
	switch (player->getClass())
	{
	case CLASS_WARRIOR:
	case CLASS_ROGUE:
	case CLASS_DEATH_KNIGHT:
		return false;
	case CLASS_PALADIN:
		return player->FindTalentType() == 0;
	case CLASS_MAGE:
	case CLASS_WARLOCK:
	case CLASS_HUNTER:
	case CLASS_PRIEST:
		return true;
	case CLASS_SHAMAN:
	case CLASS_DRUID:
		return player->FindTalentType() != 1;
	}
	return false;
}

bool BotAIFlee::SearchPVEFleePosition(Unit* pMaster, Unit* pRefUnit, Position& fleePos)
{
	if (!pMaster || !pRefUnit)
		return false;
	float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
	if (fleeDistance >= BOTAI_RANGESPELL_DISTANCE)
	{
		Clear();
		return false;
	}
	if (pRefUnit->GetTarget() != me->GetGUID() && CanFleeToTargetPlayer(pMaster->ToPlayer()))
	{
		float offsetDist = frand(1.0f, 4.0f);
		float angle = frand(0, float(M_PI * 2) - 0.1f);
		Position targetPos;
		pMaster->GetFirstCollisionPosition(offsetDist, angle);
		if (pRefUnit->GetDistance(targetPos) > NEEDFLEE_CHECKRANGE)
		{
			fleePos = targetPos;
			return true;
		}
	}

	fleeDistance = BOTAI_RANGESPELL_DISTANCE;// -fleeDistance;
	uint32 minCount = 100;
	float onceAngle = float(M_PI) * 2.0f / 16.0f;
	std::list<PVEFleePosition> pveFleePoss;
	float maxDist = 0.0f;
	for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	{
		float dist = 0;
		Position pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
		if (dist <= NEEDFLEE_CHECKRANGE)
			continue;
		if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
			continue;
		std::list<Creature*> creatures;
		SearchCreatureListFromRange(pos, creatures, BOTAI_RANGESPELL_DISTANCE);
		uint32 enemys = creatures.size();
		if (enemys > minCount)
			continue;
		minCount = enemys;
		PVEFleePosition pfPos;
		pfPos.fleePosition = pos;
		pfPos.enemyCount = enemys;
		pfPos.byMeDist = dist;
		pfPos.byMasterDist = pMaster->GetDistance(pos);
		pveFleePoss.push_back(pfPos);
	}
	if (pveFleePoss.empty())
	{
		float offsetDist = frand(1.0f, 4.0f);
		float angle = frand(0, float(M_PI * 2) - 0.1f);
		pMaster->GetFirstCollisionPosition(offsetDist, angle);
		return true;
	}

	if (minCount > 0 && CanFleeToTargetPlayer(pMaster->ToPlayer()))
	{
		float offsetDist = frand(1.0f, 4.0f);
		float angle = frand(0, float(M_PI * 2) - 0.1f);
		Position targetPos;
		pMaster->GetFirstCollisionPosition(offsetDist, angle);
		if (pRefUnit->GetDistance(targetPos) > NEEDFLEE_CHECKRANGE)
		{
			fleePos = targetPos;
			return true;
		}
	}

	std::list<PVEFleePosition> minEnemyPoss;
	for (PVEFleePosition& poss : pveFleePoss)
	{
		if (poss.enemyCount > minCount)
			continue;
		minEnemyPoss.push_back(poss);
		if (minEnemyPoss.empty())
			fleePos = poss.fleePosition;
	}
	if (minEnemyPoss.size() == 1)
		return true;
	minEnemyPoss.sort();
	std::vector<PVEFleePosition> smallDistPoss;
	std::vector<PVEFleePosition> bigDistPoss;
	int32 bigCount = int32(float(minEnemyPoss.size()) * 0.4f);
	for (PVEFleePosition& poss : minEnemyPoss)
	{
		if (bigCount > 0)
		{
			bigDistPoss.push_back(poss);
			--bigCount;
		}
		else
			smallDistPoss.push_back(poss);
	}
	std::vector<PVEFleePosition>& useFleePoss = bigDistPoss.empty() ? smallDistPoss : bigDistPoss;
	float nearDist = 999.0f;
	for (PVEFleePosition& poss : useFleePoss)
	{
		if (poss.byMasterDist < nearDist)
		{
			fleePos = poss.fleePosition;
			nearDist = poss.byMasterDist;
		}
	}
	return true;
}

void BotAIFlee::SearchCreatureListFromRange(Position centerPos, std::list<Creature*>& nearCreatures, float range)
{
	std::list<Creature*> nearCreature;
	Trinity::AllWorldObjectsInRange checker(me, BOTAI_RANGESPELL_DISTANCE + range);
	Trinity::CreatureListSearcher<Trinity::AllWorldObjectsInRange> searcher(me, nearCreature, checker);
	//me->VisitNearbyGridObject(range, searcher);
	for (Creature* pCreature : nearCreature)
	{
		if (pCreature->IsPet() || pCreature->IsTotem() || pCreature->getLevel() <= 1)
			continue;
		if (pCreature->GetDistance(centerPos) > range)
			continue;
		if (!me->IsValidAttackTarget(pCreature))
			continue;
		nearCreatures.push_back(pCreature);
	}
}

float BotAIFlee::CalcMaxFleeDistance(Unit* pRefUnit)
{
	return NEEDFLEE_CHECKRANGE - 1;
	//float fleeDistance = me->GetDistance(pRefUnit->GetPosition());
	//if (fleeDistance >= NEEDFLEE_CHECKRANGE)
	//	return NEEDFLEE_CHECKRANGE;
	//fleeDistance = NEEDFLEE_CHECKRANGE;
	//float onceAngle = float(M_PI) * 2.0f / 8.0f;
	//float selectAngle = me->GetOrientation() * (-1);
	//float maxDist = 0.0f;
	//for (float angle = 0.0f; angle < (float(M_PI) * 2.0f); angle += onceAngle)
	//{
	//	float dist = 0;
	//	Position& pos = CalculateFlee(fleeDistance, angle, pRefUnit, dist);
	//	if (!pRefUnit->IsWithinLOS(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ()))
	//		continue;
	//	if (dist > maxDist)
	//	{
	//		maxDist = dist;
	//	}
	//}
	//if (maxDist >= NEEDFLEE_CHECKRANGE)
	//	return NEEDFLEE_CHECKRANGE;
	//return maxDist;
}

Position BotAIFlee::CalculateFlee(float dist, float angle, Unit* pRefUnit, float& outDistance)
{
	Position targetPos;
	me->GetFirstCollisionPosition(dist, angle);
	outDistance = pRefUnit->GetDistance(targetPos);
	return targetPos;
}

void BotAINeedFleeAura::AddFleeAura(uint32 aura)
{
	if (aura == 0)
		return;
	for (uint32 hasAura : m_NeedFleeAuras)
	{
		if (aura == hasAura)
			return;
	}
	m_NeedFleeAuras.push_back(aura);
}

bool BotAINeedFleeAura::TargetHasFleeAura(Unit* pTarget)
{
	if (!pTarget || pTarget == me)
		return false;
	if (me->GetDistance(pTarget->GetPosition()) > NEEDFLEE_CHECKRANGE)
		return false;
	for (uint32 aura : m_NeedFleeAuras)
	{
		if (pTarget->HasAura(aura))
			return true;
	}
	return false;
}

void BotAIRecordCastSpell::RecordCastSpellTick(Unit* pTarget, uint32 spellID)
{
	if (!pTarget || !pTarget->IsAlive() || spellID == 0)
		return;
	if (m_Records.find(pTarget->GetGUID()) == m_Records.end())
	{
		CastedSpell record(pTarget->GetGUID());
		record.castRecords[spellID] = getMSTime();
		m_Records[pTarget->GetGUID()] = record;
	}
	else
	{
		CastedSpell& record = m_Records[pTarget->GetGUID()];
		record.castRecords[spellID] = getMSTime();
	}
}

bool BotAIRecordCastSpell::MatchCastRecord(Unit* pTarget, uint32 spellID, uint32 tickGap)
{
	if (!pTarget || !pTarget->IsAlive() || spellID == 0 || tickGap == 0)
		return false;
	if (m_Records.find(pTarget->GetGUID()) == m_Records.end())
		return true;

	CastedSpell& record = m_Records[pTarget->GetGUID()];
	if (record.castRecords.find(spellID) == record.castRecords.end())
		return true;
	uint32 recordTick = record.castRecords[spellID];
	return (recordTick + tickGap) <= getMSTime();
}

void BotAIGroupLeader::ProcessGroupLeader()
{
	Group* pGroup = me->GetGroup();
	if (!pGroup || !pGroup->IsLeader(me->GetGUID()))
		return;
	Group::MemberSlotList const& memList = pGroup->GetMemberSlots();
	for (Group::MemberSlot const& slot : memList)
	{
		Player* player = ObjectAccessor::FindPlayer(slot.guid);
		if (!player || player->IsPlayerBot())
			continue;
		if (!player->IsAlive() || me->GetMap() != player->GetMap() || !me->IsInWorld() || !player->IsInWorld())
			continue;
		pGroup->ChangeLeader(player->GetGUID());
		pGroup->SendUpdate();
	}
}

bool BotAIMovetoUseGO::CanCastSummonRite()
{
	if (m_RiteSpellID || m_UseGO != ObjectGuid::Empty || me->HasUnitState(UNIT_STATE_CASTING) || !me->IsInWorld())
		return false;
	return true;
}

bool BotAIMovetoUseGO::SetNeedMovetoUseGO(ObjectGuid& guid)
{
	if (guid != ObjectGuid::Empty)
	{
		if (m_RiteSpellID)
			return false;
		if (m_UseGO == ObjectGuid::Empty)
		{
			m_UseGO = guid;
			return true;
		}
	}
	else
	{
		ClearUseGO();
		return true;
	}
	return false;
}

void BotAIMovetoUseGO::StartSummonRite(uint32 spellID)
{
	if (!spellID || m_RiteSpellID)
		return;
	m_RiteSpellID = spellID;
}

bool BotAIMovetoUseGO::ProcessMovetoUseGO(BotBGAIMovement* pMovement)
{
	if (m_RiteSpellID)
	{
		if (!me->HasUnitState(UNIT_STATE_CASTING))
		{
			ClearUseGO();
			return false;
		}
		if (GameObject* go = me->GetGameObject(m_RiteSpellID))
		{
			ClearUseGO();
			uint32 pickCount = 0;
			Group* pGroup = me->GetGroup();
			Group::MemberSlotList const& memList = pGroup->GetMemberSlots();
			for (Group::MemberSlot const& slot : memList)
			{
				Player* player = ObjectAccessor::FindPlayer(slot.guid);
				if (!player || !player->IsPlayerBot() || !player->IsAlive() || me->GetMap() != player->GetMap() || !player->IsInWorld())
					continue;
				if (player == me || player->IsInCombat() || player->HasUnitState(UNIT_STATE_CASTING))
					continue;
				if (me->GetDistance(player->GetPosition()) > BOTAI_RANGESPELL_DISTANCE)
					continue;
                if (BotBGAI* pAI = dynamic_cast<BotBGAI*>(player->GetAI()))
				{
					if (pAI->SetMovetoUseGOTarget(go->GetGUID()))
					{
						pAI->Dismount();
						++pickCount;
						if (pickCount >= 3)
							return true;
					}
				}
			}
		}
		return true;
	}

	if (m_UseGO == ObjectGuid::Empty)
		return false;
	if (!pMovement || me->HasUnitState(UNIT_STATE_CASTING) || !me->IsInWorld())
		return true;
	Map* pMap = me->GetMap();
	if (!pMap)
	{
		ClearUseGO();
		return false;
	}
	if (GameObject* pGO = pMap->GetGameObject(m_UseGO))
	{
		float dist = me->GetDistance(pGO->GetPosition());
		if (dist < 1.5f)
		{
			if (me->m_unitMovedByMe != me)
			{
				if (!(me->IsOnVehicle(me->m_unitMovedByMe) || me->IsMounted()) && !pGO->GetGOInfo()->IsUsableMounted())
				{
					ClearUseGO();
					return false;
				}
			}
			pMovement->ClearMovement();
			pGO->Use(me);
			ClearUseGO();
		}
		//else if (dist > BOTAI_RANGESPELL_DISTANCE)
		//{
		//	ClearUseGO();
		//	return false;
		//}
		else
		{
			pMovement->MovementTo(m_UseGO, 1.0f);
		}
	}
	else
	{
		ClearUseGO();
		return false;
	}
	return true;
}
