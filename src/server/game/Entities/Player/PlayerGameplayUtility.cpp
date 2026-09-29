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

#include "PlayerGameplayUtility.h"
#include "Item.h"
#include "Bag.h"
#include "ObjectMgr.h"
#include "ItemEnchantmentMgr.h"

float PlayerGameplayUtility::BattlegroundScoreRate = 1.0f;
float PlayerGameplayUtility::DungeonPlayerDamageMultiplier = 1.0f;
float PlayerGameplayUtility::DungeonPlayerDamageDivisor = 1.0f;

Item* PlayerGameplayUtility::FindItemFromAllBag(Player* player, uint32 entry, bool destroy)
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

Item* PlayerGameplayUtility::StoreNewItemByEntry(Player* player, uint32 entry, int32 count)
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
