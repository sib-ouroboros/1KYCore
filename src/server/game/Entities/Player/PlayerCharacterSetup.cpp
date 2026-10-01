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

#include "PlayerCharacterSetup.h"
#include "ObjectMgr.h"
#include "Pet.h"
#include "WorldSession.h"
#include "OnlineMgr.h"
#include "MapManager.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "Bag.h"
#include <Spell.h>
#include "DB2Stores.h"
#include "Random.h"

uint32 PlayerCharacterSetup::classesTrainersGUID[MAX_CLASSES][2];
std::set<ClassTalentEntry> PlayerCharacterSetup::classesTalents[MAX_CLASSES][3] = { std::set<ClassTalentEntry>() };
std::map<uint32, ItemsForLevel> PlayerCharacterSetup::classesEquips[MAX_CLASSES][InventoryType::INVTYPE_RELIC+1] = { std::map<uint32, ItemsForLevel>() };
std::list<uint32> PlayerCharacterSetup::classesCommonSpells[MAX_CLASSES] = { std::list<uint32>() };
std::vector<uint32> PlayerCharacterSetup::normalMountSpells = std::vector<uint32>();
std::vector<uint32> PlayerCharacterSetup::fastMountSpells = std::vector<uint32>();
std::set<uint32> PlayerCharacterSetup::specialFlyingMountSpells = std::set<uint32>();

bool ItemsForLevel::IsTenacityItem(const ItemTemplate* itemTemplate)
{
	if (!itemTemplate || itemTemplate->ExtendedData->ItemLevel < 240)
		return false;
	for (uint32 i = 0; i < MAX_ITEM_PROTO_STATS; i++)
	{
		auto type = itemTemplate->ExtendedData->StatModifierBonusStat[i];
		if (type == ItemModType::ITEM_MOD_CRIT_TAKEN_RATING ||
			type == ItemModType::ITEM_MOD_RESILIENCE_RATING)
		{
			if (itemTemplate->GetQuality() < ItemQualities::ITEM_QUALITY_EPIC)
				continue;
			if (type >= 40)
				return true;
			if (itemTemplate->GetInventoryType() == InventoryType::INVTYPE_THROWN ||
				itemTemplate->GetInventoryType() == InventoryType::INVTYPE_RANGED ||
				itemTemplate->GetInventoryType() == InventoryType::INVTYPE_RANGEDRIGHT)
			{
				if (type >= 20)
					return true;
			}
			if (itemTemplate->GetInventoryType() == InventoryType::INVTYPE_TRINKET)
				return true;
		}
	}
	return false;
}

void ItemsForLevel::AddItem(const ItemTemplate* pItem)
{
	if (!pItem || pItem->ExtendedData->AllowableClass == 0)
		return;
	if (IsTenacityItem(pItem))
	{
		bool exist = false;
        for (LevelItems::iterator itItem = m_TenacityItems.begin(); itItem != m_TenacityItems.end(); itItem++)
		{
			if ((*itItem) == pItem)
			{
				exist = true;
				break;
			}
		}
		if (!exist)
		{
			m_TenacityItems.push_back(pItem);
			return;
		}
	}
	bool exist = false;
    for (LevelItems::iterator itItem = m_Items.begin(); itItem != m_Items.end(); itItem++)
	{
		if ((*itItem) == pItem)
		{
			exist = true;
			break;
		}
	}
	if (!exist)
		m_Items.push_back(pItem);
}

const ItemTemplate* ItemsForLevel::RandomItem()
{
	if (m_Items.size() <= 0)
		return NULL;
	uint32 index = irand(0, m_Items.size() - 1);
	return m_Items[index];
}

const ItemTemplate* ItemsForLevel::RandomTenacityItem()
{
	if (m_TenacityItems.size() <= 0)
		return NULL;
	uint32 index = irand(0, m_TenacityItems.size() - 1);
	return m_TenacityItems[index];
}

bool ClassTalentEntry::operator < (const ClassTalentEntry &tal) const
{
    if (!talentEntry || !tal.talentEntry)
        return false;

    if (talentEntry->TierID == tal.talentEntry->TierID)
    {
        return talentEntry->ColumnIndex < tal.talentEntry->ColumnIndex;
    }
    else
    {
        return talentEntry->TierID < tal.talentEntry->TierID;
    }
}

bool PlayerCharacterSetup::IsEquipByClasses(uint32 cls, const ItemTemplate* itemTemplate)
{
	if (!itemTemplate || itemTemplate->ExtendedData->AllowableClass == 0)
		return false;

	// OBJETS RESERVES A UNE RACE.
	//
	// MESURE : tous les bots accumulaient neuf a seize refus de code 10
	// -- EQUIP_ERR_CANT_EQUIP_EVER -- et il leur manquait toujours les
	// memes emplacements. CanUseItem rend ce code quand AllowableClass ou
	// AllowableRace ne correspond pas. La classe etait deja filtree juste
	// en dessous ; la race, jamais.
	//
	// Le reservoir est construit par CLASSE, pas par personnage : il ne
	// peut pas savoir a quelle race servira l objet. On ecarte donc tout ce
	// qui est reserve a une race quelconque. Le reservoir compte plus de
	// dix-huit mille pieces par classe : la perte est negligeable, et elle
	// garantit que tout ce qui en sort est reellement portable.
	if (itemTemplate->ExtendedData->AllowableRace != -1)
		return false;
	if (itemTemplate->ExtendedData->AllowableClass > 0)
	{
		if (!(itemTemplate->ExtendedData->AllowableClass & (1 << (cls - 1))))
			return false;
	}
	// =================================================================
	// SPECIALISATION_ARMURE
	//
	// SIGNALE EN JEU : sur une escorte de deux paladins, un habille et un
	// nu. Meme classe, meme niveau, meme reservoir.
	//
	// MESURE (sonde EQUIPDBG) : les bots nus accumulaient seize a dix-sept
	// refus de code 39 -- EQUIP_ERR_CLIENT_LOCKED_OUT -- la ou les habilles
	// n en avaient aucun.
	//
	// Player::CanEquipItem impose une regle que ce filtre ignorait : passe
	// le niveau 40, un guerrier, un paladin ou un chevalier de la mort ne
	// peut porter QUE des plaques ; un chasseur ou un chaman, QUE des
	// mailles ; un voleur ou un druide, QUE du cuir ; un mage, un pretre ou
	// un demoniste, QUE du tissu.
	//
	// Ici on ne regardait que AllowableClass, bien plus permissif -- un
	// paladin « peut » porter du tissu au sens du drapeau de l objet. Le
	// reservoir melangeait donc les quatre types, la pioche etait aleatoire,
	// et chaque piece du mauvais type repartait en refus silencieux. D ou
	// deux paladins identiques aux sorts opposes : l un avait tire assez de
	// plaques, l autre non.
	//
	// On applique la meme regle que le core, a l identique -- meme plage de
	// sous-classes, meme exemption de la cape.
	// =================================================================
	if (itemTemplate->GetClass() == ITEM_CLASS_ARMOR &&
		itemTemplate->GetSubClass() > ITEM_SUBCLASS_ARMOR_MISCELLANEOUS &&
		itemTemplate->GetSubClass() < ITEM_SUBCLASS_ARMOR_COSMETIC &&
		itemTemplate->GetInventoryType() != INVTYPE_CLOAK)
	{
		uint32 sousClasseAttendue = 0;
		switch (cls)
		{
		case CLASS_WARRIOR:
		case CLASS_PALADIN:
		case CLASS_DEATH_KNIGHT:
			sousClasseAttendue = ITEM_SUBCLASS_ARMOR_PLATE;
			break;
		case CLASS_HUNTER:
		case CLASS_SHAMAN:
			sousClasseAttendue = ITEM_SUBCLASS_ARMOR_MAIL;
			break;
		case CLASS_ROGUE:
		case CLASS_DRUID:
		case CLASS_MONK:
		case CLASS_DEMON_HUNTER:
			sousClasseAttendue = ITEM_SUBCLASS_ARMOR_LEATHER;
			break;
		case CLASS_MAGE:
		case CLASS_PRIEST:
		case CLASS_WARLOCK:
			sousClasseAttendue = ITEM_SUBCLASS_ARMOR_CLOTH;
			break;
		default:
			break;
		}

		// Le reservoir sert des bots de niveau 10 au minimum et se consulte
		// par niveau ; on retient la regle du haut niveau, la seule qui vaille
		// pour un mercenaire mis au niveau de son employeur.
		if (sousClasseAttendue && itemTemplate->GetSubClass() != sousClasseAttendue)
			return false;
	}

	if (cls == 1 || cls == 6 || cls == 3 || cls == 4)
	{
		if (!IsOnlyPhysicsAttributeEquip(itemTemplate, (cls == 3) ? false : true))
			return false;
	}
    // Weapon proficiency and specialization are checked for the actual player at selection.
    // Legacy class lists excluded Legion weapons (including Frost one-handers and druid polearms).
    if (itemTemplate->GetClass() == ITEM_CLASS_WEAPON)
        return true;
	if (IsCommonEquip(itemTemplate))
		return true;
	switch (cls)
	{
	case 1:
		return IsWarriorEquip(itemTemplate);
	case 2:
		return IsPaladinEquip(itemTemplate);
	case 3:
		return IsHunterEquip(itemTemplate);
	case 4:
		return IsRogueEquip(itemTemplate);
	case 5:
		return IsPriestEquip(itemTemplate);
	case 6:
		return IsDeathKightEquip(itemTemplate);
	case 7:
		return IsShamanEquip(itemTemplate);
	case 8:
		return IsMageEquip(itemTemplate);
	case 9:
		return IsWarlockEquip(itemTemplate);
    case CLASS_MONK:
    case CLASS_DEMON_HUNTER:
        return itemTemplate->GetClass() == ITEM_CLASS_ARMOR;
	case 11:
		return IsDruidEquip(itemTemplate);
	default:
		return false;
	}
	return false;
}




void PlayerCharacterSetup::ClearUnknowMount(Player* player)
{
	for (uint32 mountID : normalMountSpells)
	{
		if (player->HasAura(mountID))
			player->RemoveOwnedAura(mountID, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	}
	for (uint32 mountID : fastMountSpells)
	{
		if (player->HasAura(mountID))
			player->RemoveOwnedAura(mountID, ObjectGuid::Empty, 0, AURA_REMOVE_BY_CANCEL);
	}
	if (player->IsMounted())// && AURA_EFFECT_HANDLE_REAL
	{
		player->Dismount();
		player->RemoveAurasByType(SPELL_AURA_MOUNTED);
	}
}

uint32 PlayerCharacterSetup::CheckMaxLevel(uint32 level)
{
	uint32 worldMaxLevel = sWorld->getIntConfig(CONFIG_MAX_PLAYER_LEVEL);
	if (level > worldMaxLevel)
	{
		level = worldMaxLevel;
	}
	if (level == 0)
		level = 1;
	return level;
}

bool PlayerCharacterSetup::IsSpecialFlyingMountAura(uint32 aura)
{
	if (!aura)
		return false;
    return specialFlyingMountSpells.find(aura) != specialFlyingMountSpells.end();
}

bool PlayerCharacterSetup::IsOnlyPhysicsAttributeEquip(const ItemTemplate* itemTemplate, bool coverIntellect)
{
	if (!itemTemplate->HasStats())
		return false;
	for (uint32 i = 0; i < MAX_ITEM_PROTO_STATS; i++)
	{
		auto type = itemTemplate->ExtendedData->StatModifierBonusStat[i];
		switch (type)
		{
		case ItemModType::ITEM_MOD_MANA:
		case ItemModType::ITEM_MOD_SPIRIT:
		case ItemModType::ITEM_MOD_HIT_SPELL_RATING:
		case ItemModType::ITEM_MOD_CRIT_SPELL_RATING:
		case ItemModType::ITEM_MOD_HIT_TAKEN_SPELL_RATING:
		case ItemModType::ITEM_MOD_CRIT_TAKEN_SPELL_RATING:
		case ItemModType::ITEM_MOD_HASTE_SPELL_RATING:
		case ItemModType::ITEM_MOD_SPELL_HEALING_DONE:
		case ItemModType::ITEM_MOD_SPELL_DAMAGE_DONE:
		case ItemModType::ITEM_MOD_MANA_REGENERATION:
		case ItemModType::ITEM_MOD_SPELL_POWER:
		case ItemModType::ITEM_MOD_SPELL_PENETRATION:
			return false;
		case ItemModType::ITEM_MOD_INTELLECT:
			if (coverIntellect)
				return false;
		}
	}
	return true;
}







//bool PlayerCharacterSetup::MatchEquipmentSlotsByWeapon(EquipmentSlots slot, InventoryType iType)
//{
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_MAINHAND)
//		return (iType == InventoryType::INVTYPE_2HWEAPON || iType == InventoryType::INVTYPE_WEAPON || iType == InventoryType::INVTYPE_WEAPONMAINHAND);
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_OFFHAND)
//		return (iType == InventoryType::INVTYPE_WEAPON || iType == InventoryType::INVTYPE_WEAPONOFFHAND);
//
//	return false;
//}
//
//bool PlayerCharacterSetup::MatchEquipmentSlotsByArmor(EquipmentSlots slot, InventoryType iType)
//{
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_BODY)
//		return (iType == InventoryType::INVTYPE_BODY || iType == InventoryType::INVTYPE_ROBE);
//	if (slot >= EquipmentSlots::EQUIPMENT_SLOT_HEAD && slot <= EquipmentSlots::EQUIPMENT_SLOT_HANDS)
//		return (uint8(iType) - 1 == slot);
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_FINGER1 || slot == EquipmentSlots::EQUIPMENT_SLOT_FINGER2)
//		return (iType == InventoryType::INVTYPE_FINGER);
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_TRINKET1 || slot == EquipmentSlots::EQUIPMENT_SLOT_TRINKET2)
//		return (iType == InventoryType::INVTYPE_TRINKET);
//	if (slot == EquipmentSlots::EQUIPMENT_SLOT_BACK)
//		return (iType == InventoryType::INVTYPE_CLOAK);
//	return false;
//}
//
//bool PlayerCharacterSetup::MatchRangeEquipmentSlots(uint32 cls, const ItemTemplate* itemTemplate)
//{
//	return false;
//}

bool PlayerCharacterSetup::IsCommonEquip(const ItemTemplate* itemTemplate)
{
	switch (itemTemplate->GetInventoryType())
	{
	case INVTYPE_NECK:
	case INVTYPE_CLOAK:
	case INVTYPE_FINGER:
	case INVTYPE_TRINKET:
		return true;
	default:
		break;
	}
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR /*&& itemTemplate->GetSubClass() == ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC */&& itemTemplate->GetInventoryType() == INVTYPE_TRINKET)
		return true;
	return false;
}


bool PlayerCharacterSetup::IsWarriorEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_DAGGER:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
			if (itemTemplate->GetBaseRequiredLevel() >= 40)
				return false;
			break;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_PROJECTILE)
	{
		if (itemTemplate->GetSubClass() == ItemSubclassProjectile::ITEM_SUBCLASS_ARROW || itemTemplate->GetSubClass() == ItemSubclassProjectile::ITEM_SUBCLASS_BULLET)
			return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsPaladinEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_DAGGER:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
			if (itemTemplate->GetBaseRequiredLevel() >= 40)
				return false;
			break;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsDeathKightEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_DAGGER:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
			return false;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
			if (itemTemplate->GetBaseRequiredLevel() >= 40)
				return false;
			break;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsRogueEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsDruidEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsHunterEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_DAGGER:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
			if (itemTemplate->GetBaseRequiredLevel() >= 40)
				return false;
			break;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
			if (itemTemplate->GetBaseRequiredLevel() < 40)
				return false;
			break;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_PROJECTILE)
	{
		if (itemTemplate->GetSubClass() == ItemSubclassProjectile::ITEM_SUBCLASS_ARROW || itemTemplate->GetSubClass() == ItemSubclassProjectile::ITEM_SUBCLASS_BULLET)
			return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsShamanEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_STAFF:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_DAGGER:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_WAND:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MISC:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_CLOTH:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
			if (itemTemplate->GetBaseRequiredLevel() >= 40)
				return false;
			break;
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
			if (itemTemplate->GetBaseRequiredLevel() < 40)
				return false;
			break;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsMageEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsWarlockEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		default:
			break;
		}
		return true;
	}

	return false;
}

bool PlayerCharacterSetup::IsPriestEquip(const ItemTemplate* itemTemplate)
{
	if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_WEAPON)
	{
		switch (itemTemplate->GetSubClass())
		{
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_obsolete:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_AXE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MACE2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SWORD2:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_BOW:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_GUN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_CROSSBOW:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FIST:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_THROWN:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_POLEARM:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_SPEAR:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_EXOTIC2:
		//case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_MISC:
		case ItemSubclassWeapon::ITEM_SUBCLASS_WEAPON_FISHING_POLE:
			return false;
		default:
			break;
		}
		return true;
	}
	else if (itemTemplate->GetClass() == ItemClass::ITEM_CLASS_ARMOR)
	{
		switch (itemTemplate->GetSubClass())
		{
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LEATHER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_MAIL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_PLATE:
		//case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_BUCKLER:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SHIELD:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_LIBRAM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_IDOL:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_TOTEM:
		case ItemSubclassArmor::ITEM_SUBCLASS_ARMOR_SIGIL:
			return false;
		default:
			break;
		}
		return true;
	}

	return false;
}



uint32 PlayerCharacterSetup::FindPlayerTalentType(Player* player)
{
    // OnlineMgr uses an unsigned byte with 0xFF for an unknown specialization.
    constexpr uint32 unknownSpecialization = 0xFF;
    if (!player)
        return unknownSpecialization;

    ChrSpecializationEntry const* specialization = sChrSpecializationStore.LookupEntry(player->GetSpecializationId());
    if (!specialization || specialization->IsPetSpecialization() ||
        specialization->ClassID != player->getClass() ||
        specialization->OrderIndex < 0 || specialization->OrderIndex >= MAX_SPECIALIZATIONS)
        return unknownSpecialization;

    return uint32(specialization->OrderIndex);
}

void PlayerCharacterSetup::Initialize()
{
	for (int i = 0; i < MAX_CLASSES; i++)
	{
		classesTrainersGUID[i][0] = 0;
		classesTrainersGUID[i][1] = 0;

		for (int j = 0; j < 3; j++)
			classesTalents[i][j].clear();

		for (int j = 0; j <= InventoryType::INVTYPE_RELIC; j++)
			classesEquips[i][j].clear();

		classesCommonSpells[i].clear();
	}
	normalMountSpells.clear();
	fastMountSpells.clear();
    specialFlyingMountSpells.clear();

	classesTrainersGUID[Classes::CLASS_WARRIOR][0] = 5113;
	classesTrainersGUID[Classes::CLASS_WARRIOR][1] = 4593;

	classesTrainersGUID[Classes::CLASS_PALADIN][0] = 5147;
	classesTrainersGUID[Classes::CLASS_PALADIN][1] = 23128;

	classesTrainersGUID[Classes::CLASS_DEATH_KNIGHT][0] = 28474;
	classesTrainersGUID[Classes::CLASS_DEATH_KNIGHT][1] = 28474;

	classesTrainersGUID[Classes::CLASS_ROGUE][0] = 5165;
	classesTrainersGUID[Classes::CLASS_ROGUE][1] = 4584;

	classesTrainersGUID[Classes::CLASS_DRUID][0] = 4217;
	classesTrainersGUID[Classes::CLASS_DRUID][1] = 3034;

	classesTrainersGUID[Classes::CLASS_HUNTER][0] = 5115;
	classesTrainersGUID[Classes::CLASS_HUNTER][1] = 3352;

	classesTrainersGUID[Classes::CLASS_SHAMAN][0] = 20407;
	classesTrainersGUID[Classes::CLASS_SHAMAN][1] = 3344;

	classesTrainersGUID[Classes::CLASS_MAGE][0] = 5146;
	classesTrainersGUID[Classes::CLASS_MAGE][1] = 4566;

	classesTrainersGUID[Classes::CLASS_WARLOCK][0] = 5172;
	classesTrainersGUID[Classes::CLASS_WARLOCK][1] = 4563;

	classesTrainersGUID[Classes::CLASS_PRIEST][0] = 5141;
	classesTrainersGUID[Classes::CLASS_PRIEST][1] = 4606;

	for (uint32 talentId = 0; talentId < sTalentStore.GetNumRows(); ++talentId)
	{
		TalentEntry const* talentInfo = sTalentStore.LookupEntry(talentId);

		if (!talentInfo)
			continue;

		//TalentTabEntry const* talentTabInfo = sTalentTabStore.LookupEntry(talentInfo->TalentTab);

		//if (!talentTabInfo || talentTabInfo->tabpage < 0 || talentTabInfo->tabpage > 2)
		//	continue;
		//if ((talentTabInfo->GetClass()Mask & CLASSMASK_ALL_PLAYABLE) == 0)
		//	continue;
		//for (uint32 cls = 1; cls < MAX_CLASSES; ++cls)
		//{
		//	if (talentTabInfo->GetClass()Mask & (1 << (cls - 1)))
		//	{
        //		ClassTalentPage& talentPage = classesTalents[cls][talentTabInfo->tabpage];
        //		talentPage.insert(ClassTalentEntry(cls, talentTabInfo->tabpage, talentInfo));
		//	}
		//}
	}

	ItemTemplateContainer const* its = sObjectMgr->GetItemTemplateStore();
	for (ItemTemplateContainer::const_iterator itr = its->begin(); itr != its->end(); ++itr)
	{
		const ItemTemplate& item = itr->second;
		if (item.GetRequiredSkill() > 0 /*|| item.RequiredSpell > 0*/)// || item.AllowableRace != -1)
			continue;
		//if (item.RequiredReputationFaction != 0 || item.Area != 0 || item.Map != 0)
		//	continue;
		//if (item.Class != ItemClass::ITEM_CLASS_WEAPON && item.Class != ItemClass::ITEM_CLASS_ARMOR && item.Class != ItemClass::ITEM_CLASS_PROJECTILE)
		//	continue;
		
	//hxsd
		//if (item.ItemId	>=56806)
		//	continue;
		
		//if (item.Flags2 > 0)
		//	continue;
		if (item.GetBaseRequiredLevel() <= 0 || item.ExtendedData->InventoryType <= InventoryType::INVTYPE_NON_EQUIP || item.ExtendedData->InventoryType > InventoryType::INVTYPE_RELIC)
			continue;
		if (item.GetBaseRequiredLevel() < 20 && item.GetQuality() <= 1 && item.ExtendedData->InventoryType != InventoryType::INVTYPE_AMMO)
			continue;
		for (int i = 1; i < MAX_CLASSES; i++)
		{
			if (!IsEquipByClasses(i, &item))
				continue;
			//uint32 classMask = 1 << (i - 1);
			//if (item.AllowableClass & classMask)
			{
				InventoryType iType = InventoryType((item.ExtendedData->InventoryType == InventoryType::INVTYPE_ROBE) ? (InventoryType::INVTYPE_CHEST) : item.ExtendedData->InventoryType);
                EquipmentByLevel& equips = classesEquips[i][iType];
                EquipmentByLevel::iterator itEquip = equips.find(item.GetBaseRequiredLevel());
				ItemsForLevel& forLevel = (itEquip == equips.end()) ? equips[item.GetBaseRequiredLevel()] : itEquip->second;
				forLevel.AddItem(&item);
			}
		}
	}

	classesCommonSpells[1].push_back(33388);
	classesCommonSpells[1].push_back(33391);
	classesCommonSpells[1].push_back(196);
	classesCommonSpells[1].push_back(197);
	classesCommonSpells[1].push_back(201);
	classesCommonSpells[1].push_back(202);
	classesCommonSpells[1].push_back(198);
	classesCommonSpells[1].push_back(199);
	classesCommonSpells[1].push_back(264);
	classesCommonSpells[1].push_back(5011);
	classesCommonSpells[1].push_back(266);
	classesCommonSpells[1].push_back(200);
	classesCommonSpells[1].push_back(2567);
	classesCommonSpells[1].push_back(71);
	classesCommonSpells[1].push_back(355);
	classesCommonSpells[1].push_back(2458);
	classesCommonSpells[1].push_back(7386);

	classesCommonSpells[2].push_back(33388);
	classesCommonSpells[2].push_back(33391);
	classesCommonSpells[2].push_back(201);
	classesCommonSpells[2].push_back(202);
	classesCommonSpells[2].push_back(198);
	classesCommonSpells[2].push_back(199);
	classesCommonSpells[2].push_back(200);
	classesCommonSpells[2].push_back(7328);

	classesCommonSpells[3].push_back(33388);
	classesCommonSpells[3].push_back(33391);
	classesCommonSpells[3].push_back(1515);
	classesCommonSpells[3].push_back(6991);
	classesCommonSpells[3].push_back(883);
	classesCommonSpells[3].push_back(982);
	classesCommonSpells[3].push_back(2641);
	classesCommonSpells[3].push_back(197);
	classesCommonSpells[3].push_back(202);
	classesCommonSpells[3].push_back(200);
	classesCommonSpells[3].push_back(264);
	classesCommonSpells[3].push_back(5011);
	classesCommonSpells[3].push_back(266);

	classesCommonSpells[4].push_back(33388);
	classesCommonSpells[4].push_back(33391);
	classesCommonSpells[4].push_back(196);
	classesCommonSpells[4].push_back(201);
	classesCommonSpells[4].push_back(198);
	classesCommonSpells[4].push_back(1180);
	classesCommonSpells[4].push_back(15590);
	classesCommonSpells[4].push_back(2567);

	classesCommonSpells[5].push_back(33388);
	classesCommonSpells[5].push_back(33391);
	classesCommonSpells[5].push_back(1180);
	classesCommonSpells[5].push_back(5009);
	classesCommonSpells[5].push_back(227);
	classesCommonSpells[5].push_back(198);

	classesCommonSpells[6].push_back(33388);
	classesCommonSpells[6].push_back(33391);
	classesCommonSpells[6].push_back(197);
	classesCommonSpells[6].push_back(202);
	classesCommonSpells[6].push_back(199);
	classesCommonSpells[6].push_back(200);

	classesCommonSpells[7].push_back(33388);
	classesCommonSpells[7].push_back(33391);
	classesCommonSpells[7].push_back(196);
	classesCommonSpells[7].push_back(197);
	classesCommonSpells[7].push_back(198);
	classesCommonSpells[7].push_back(199);

	classesCommonSpells[8].push_back(33388);
	classesCommonSpells[8].push_back(33391);
	classesCommonSpells[8].push_back(1180);
	classesCommonSpells[8].push_back(5009);
	classesCommonSpells[8].push_back(227);
	classesCommonSpells[8].push_back(201);

	classesCommonSpells[9].push_back(33388);
	classesCommonSpells[9].push_back(33391);
	classesCommonSpells[9].push_back(1180);
	classesCommonSpells[9].push_back(5009);
	classesCommonSpells[9].push_back(227);
	classesCommonSpells[9].push_back(201);
	classesCommonSpells[9].push_back(712);
	classesCommonSpells[9].push_back(697);
	classesCommonSpells[9].push_back(691);

	classesCommonSpells[11].push_back(33388);
	classesCommonSpells[11].push_back(33391);
	classesCommonSpells[11].push_back(1180);
	classesCommonSpells[11].push_back(227);
	classesCommonSpells[11].push_back(198);
	classesCommonSpells[11].push_back(199);

	normalMountSpells.push_back(6777);
	fastMountSpells.push_back(23240);
	fastMountSpells.push_back(22717);
	fastMountSpells.push_back(22720);
	fastMountSpells.push_back(22719);
	fastMountSpells.push_back(22723);
	fastMountSpells.push_back(48027);
	fastMountSpells.push_back(42777);
	fastMountSpells.push_back(74918);
	fastMountSpells.push_back(73313);
	fastMountSpells.push_back(51412);
	fastMountSpells.push_back(65644);
	fastMountSpells.push_back(64659);
	fastMountSpells.push_back(65646);
	fastMountSpells.push_back(66091);
	fastMountSpells.push_back(65641);
	fastMountSpells.push_back(68188);
	fastMountSpells.push_back(66090);
	fastMountSpells.push_back(41252);
	fastMountSpells.push_back(68057);

    specialFlyingMountSpells.insert(69395);
    specialFlyingMountSpells.insert(67336);
    specialFlyingMountSpells.insert(65439);
    specialFlyingMountSpells.insert(32345);
    specialFlyingMountSpells.insert(46199);
    specialFlyingMountSpells.insert(75596);
}

bool PlayerCharacterSetup::BindingPlayerHomePosition(Player* player)
{
	if (!player || !player->IsInWorld() || player->GetMap()->IsDungeon())
		return false;
	if (!MapManager::IsValidMapCoord(player->GetMapId(), player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(), player->GetOrientation()))
		return false;

	uint32 bindspell = 3286;

	// send spell for homebinding (3286)
	player->CastSpell(player, bindspell, true);
	return true;
}

PlayerCharacterSetup::PlayerCharacterSetup(Player* player) :
m_Finish(true),
m_TenacitySetting(false),
m_ResetStep(0),
m_Player(player),
m_ActiveTalentType(PLAYER_SPECIALIZATION_KEEP)
{
}

PlayerCharacterSetup::~PlayerCharacterSetup()
{
}


uint32 PlayerCharacterSetup::GetTalentType()
{

    return FindPlayerTalentType(m_Player);
}

bool PlayerCharacterSetup::ResetPlayerToLevel(uint32 level, uint32 talent, bool tenacity)
{
    if (!m_Player || !m_Finish)
        return false;

    // Validate before changing level or starting the reset pipeline.
    ChrSpecializationEntry const* spec = talent == PLAYER_SPECIALIZATION_KEEP
        ? sChrSpecializationStore.LookupEntry(m_Player->GetSpecializationId())
        : (talent < MAX_SPECIALIZATIONS
            ? sDB2Manager.GetChrSpecializationByIndex(m_Player->getClass(), talent) : nullptr);
    if (!spec || spec->IsPetSpecialization() || spec->ClassID != m_Player->getClass() ||
        spec->OrderIndex < 0 || spec->OrderIndex >= MAX_SPECIALIZATIONS)
        return false;

    m_ActiveTalentType = spec->OrderIndex;
    m_TargetLevel = level;
    m_SetupFailures = 0;
	m_ResetStep = 0;
	m_Finish = false;
	m_TenacitySetting = tenacity;
	return true;
}


void PlayerCharacterSetup::SupplementAmmo()
{
	
}

bool PlayerCharacterSetup::ChangeSpecialization(uint32 talent)
{
    if (!m_Player || !m_Finish)
        return false;
    ChrSpecializationEntry const* spec = talent == PLAYER_SPECIALIZATION_KEEP
        ? sChrSpecializationStore.LookupEntry(m_Player->GetSpecializationId())
        : (talent < MAX_SPECIALIZATIONS
            ? sDB2Manager.GetChrSpecializationByIndex(m_Player->getClass(), talent) : nullptr);
    if (!spec || spec->IsPetSpecialization() || spec->ClassID != m_Player->getClass() ||
        spec->OrderIndex < 0 || spec->OrderIndex >= MAX_SPECIALIZATIONS)
        return false;
    m_Player->ActivateTalentGroup(spec);
    if (m_Player->GetSpecializationId() != spec->ID)
        return false;
    m_Player->SendTalentsInfoData();
    m_Player->SaveToDB();
    if (WorldSession* session = m_Player->GetSession())
        sOnlineMgr->CharaterState(session->GetAccountId(), uint32(m_Player->GetGUID()),
            m_Player->getLevel(), FindPlayerTalentType(m_Player));
    return true;
}

void PlayerCharacterSetup::UpdateReset()
{
	if (m_Finish)
		return;

    if (WorldSession* session = m_Player->GetSession())
        sOnlineMgr->SetCharacterOperation(session->GetAccountId(), uint32(m_Player->GetGUID()),
            "preparation", "running", m_SetupFailures);
	if (m_Player->IsInCombat())
		m_Player->CombatStop(true);
    // Finish on this player update: no session packet or autosave can split the steps.
    while (m_ResetStep < 14)
    {
	switch (m_ResetStep)
	{
    case 0:
        if (m_Player->getLevel() != m_TargetLevel)
        {
            m_Player->GiveLevel(m_TargetLevel);
            m_Player->SetUInt32Value(PLAYER_XP, 0);
        }
		ActivateSpecialization();
		++m_ResetStep;
		break;
	case 1:
		m_Player->ResetTalents(true);
		++m_ResetStep;
		break;
	case 2:
		LearnTalents();
		++m_ResetStep;
		break;
	case 3:
		RemoveSpells();
		++m_ResetStep;
		break;
	case 4:
		LearnCommonSpells();
		++m_ResetStep;
		break;
	case 5:
		LearnSpells();
		++m_ResetStep;
		break;
    case 6:
        // Preserve all existing inventory; report insufficient space instead of deleting items.
        ++m_ResetStep;
        break;
	case 7:
		CheckInventroy();
		++m_ResetStep;
		break;
	case 8:
		AddEquipFromAll();
		++m_ResetStep;
		break;
	case 9:
		UpequipFromAll();
		++m_ResetStep;
		break;
	case 10:
		SupplementOtherItems();
		++m_ResetStep;
		break;
	case 11:
        m_Player->SendTalentsInfoData();
		++m_ResetStep;
		break;
	case 12:
		++m_ResetStep;
		break;
	case 13:
        PlayerCharacterSetup::ClearUnknowMount(m_Player);
		m_Player->SetFullHealth();
		m_Player->UpdateSkillsForLevel();
		m_Player->UpdateAllStats();
        m_Finish = true; // Allow the final transaction through the save guard.
        m_Player->SaveToDB();
        if (WorldSession* session = m_Player->GetSession())
        {
            sOnlineMgr->CharaterState(session->GetAccountId(), uint32(m_Player->GetGUID()),
                m_Player->getLevel(), FindPlayerTalentType(m_Player));
            sOnlineMgr->SetCharacterOperation(session->GetAccountId(), uint32(m_Player->GetGUID()),
                "preparation", m_SetupFailures ? "completed_with_warnings" : "completed", m_SetupFailures);
        }
		++m_ResetStep;
		break;
	}

    }
	m_Finish = (m_ResetStep >= 14);
	if (m_Finish)
		m_TenacitySetting = false;
}

// Bascule le bot sur la specialisation demandee par le re-level, en passant par
// le chemin officiel du core. Une version precedente ecrivait
// PLAYER_FIELD_CURRENT_SPEC_ID a la main en plein re-level et provoquait un
// debordement de pile : ActivateTalentGroup fait le travail complet, y compris
// InitTalentForLevel, les boutons d action, la puissance et les auras de forme.
void PlayerCharacterSetup::ActivateSpecialization()
{
	if (!m_Player)
		return;

    // KEEP was resolved at reset start; index 3 is the fourth druid specialization.
    if (m_ActiveTalentType >= MAX_SPECIALIZATIONS)
		return;

	uint8 const playerClass = m_Player->getClass();
	for (uint32 i = 0; i < sChrSpecializationStore.GetNumRows(); ++i)
	{
		ChrSpecializationEntry const* spec = sChrSpecializationStore.LookupEntry(i);
		if (!spec || spec->ClassID != int8(playerClass) || spec->IsPetSpecialization())
			continue;
		if (uint32(spec->OrderIndex) != m_ActiveTalentType)
			continue;

		// ActivateTalentGroup ne fait rien si la specialisation est deja active.
		m_Player->ActivateTalentGroup(spec);
		return;
	}
}

void PlayerCharacterSetup::LearnTalents()
{
	// SylvaniaCore : cette fonction etait un corps vide alors que l etape
	// precedente du re-level appelle ResetTalents(true). Les bots repartaient
	// donc au combat sans un seul talent, soit sept rangs manquants a 110.
	//
	// Version volontairement minimale : on apprend les talents de la
	// specialisation deja portee par le personnage, rien d autre. Une premiere
	// version basculait aussi la specialisation en cours de re-level et
	// provoquait un debordement de pile.
	if (!m_Player)
		return;

	uint8 const playerClass = m_Player->getClass();
	uint32 const specId = m_Player->GetPrimarySpecialization();
	uint32 const tiers = m_Player->CalculateTalentsTiers();
	uint8 const talentGroup = m_Player->GetActiveTalentGroup();

	for (uint32 tier = 0; tier < tiers; ++tier)
	{
		std::vector<TalentEntry const*> candidates;
		for (uint32 column = 0; column < MAX_TALENT_COLUMNS; ++column)
		{
			for (TalentEntry const* talent : sDB2Manager.GetTalentsByPosition(playerClass, tier, column))
			{
				if (!talent || !talent->SpellID)
					continue;
				if (talent->SpecID && specId && talent->SpecID != specId)
					continue;
				if (m_Player->HasTalent(talent->ID, talentGroup) || m_Player->HasSpell(talent->SpellID))
					continue;
				candidates.push_back(talent);
			}
		}

		if (candidates.empty())
			continue;

		TalentEntry const* picked = candidates[urand(0, uint32(candidates.size()) - 1)];
		if (m_Player->AddTalent(picked, talentGroup, true))
			m_Player->LearnSpell(picked->SpellID, false);
	}
}

void PlayerCharacterSetup::LearnCommonSpells()
{
	uint8 cls = m_Player->getClass();
	if (cls <= 0 || cls >= 12 || cls == 10)
		return;
    ClassCommonSpells& commonSpells = classesCommonSpells[cls];
    for (ClassCommonSpells::iterator itSpell = commonSpells.begin();
		itSpell != commonSpells.end();
		itSpell++)
	{
		uint32 spellID = *itSpell;
		if (m_Player->HasSpell(spellID))
			continue;
		m_Player->LearnSpell(spellID, false);
	}

    for (MountSpellIds::iterator itMount = normalMountSpells.begin();
		itMount != normalMountSpells.end();
		itMount++)
	{
		uint32 spellID = *itMount;
		if (m_Player->HasSpell(spellID))
			continue;
		m_Player->LearnSpell(spellID, false);
	}

}

void PlayerCharacterSetup::RemoveSpells()
{
	const TrainerSpellData* spellData = sObjectMgr->GetNpcTrainerSpells(classesTrainersGUID[m_Player->getClass()][(m_Player->GetTeamId() == TeamId::TEAM_ALLIANCE) ? 0 : 1]);
	if (!spellData)
		return;
	for (TrainerSpellMap::const_iterator itBTS = spellData->spellList.begin();
		itBTS != spellData->spellList.end();
		itBTS++)
	{
		const TrainerSpell& tSpell = itBTS->second;
		uint32 spellID = tSpell.SpellID;
		if (m_Player->HasSpell(spellID))
		{
			m_Player->RemoveSpell(spellID, false, false);
		}
	}
}

void PlayerCharacterSetup::LearnSpells()
{
	uint8 level = m_Player->getLevel();

	// SylvaniaCore : en 7.3.5 le gros du kit de classe ne s apprend plus chez un
	// dresseur mais s octroie a la montee de niveau et via la specialisation. Se
	// limiter aux donnees de dresseur laissait les bots re-leveles sans sorts
	// d attaque : constate en jeu sur les demonistes 110 du siege, deux sorts de
	// degats sur la duree sur cinq et aucun sort de degats directs sur quatre.
	// Concerne aussi le remplissage des champs de bataille, qui re-level de la
	// meme facon.
	m_Player->LearnDefaultSkills();
	m_Player->LearnSpecializationSpells();
	m_Player->UpdateSkillsToMaxSkillsForLevel();

	const TrainerSpellData* spellData = sObjectMgr->GetNpcTrainerSpells(classesTrainersGUID[m_Player->getClass()][(m_Player->GetTeamId() == TeamId::TEAM_ALLIANCE) ? 0 : 1]);
	if (!spellData)
		return;
	for (TrainerSpellMap::const_iterator itBTS = spellData->spellList.begin();
		itBTS != spellData->spellList.end();
		itBTS++)
	{
		const TrainerSpell& tSpell = itBTS->second;
		uint32 spellID = tSpell.SpellID;
		if (tSpell.ReqLevel > level)
		{
			continue;
		}
		if (m_Player->HasSpell(spellID))
			continue;
		if (tSpell.IsCastable())
		{
			m_Player->CastSpell(m_Player, spellID, true);
            //TC_LOG_WARN("PlayerCharacterSetup", "Player %s Learn spell %d, spell is castable, do cast.", m_Player->GetName().c_str(), spellID);
		}
		else
			m_Player->LearnSpell(spellID, false);
	}
}

void PlayerCharacterSetup::CheckInventroy()
{
    ItemTemplate const* item = sObjectMgr->GetItemTemplate(21876);
    if (!item)
    {
        TC_LOG_ERROR("entities.player", "Character setup: missing bag template 21876");
        ++m_SetupFailures;
        return;
    }
    for (uint8 slot = INVENTORY_SLOT_BAG_START; slot < INVENTORY_SLOT_BAG_END; ++slot)
    {
        if (m_Player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
            continue;
        ItemPosCountVec dest;
        if (m_Player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, item->GetId(), 1) != EQUIP_ERR_OK || dest.empty())
        {
            ++m_SetupFailures;
            return;
        }
        Item* bag = m_Player->StoreNewItem(dest, item->GetId(), true, GenerateItemRandomPropertyId(item->GetId()));
        if (!bag || !EquipItem(bag, slot))
        {
            ++m_SetupFailures;
            return;
        } // Keep the stored bag; do not create more items after a failed equip.
    }
}

void PlayerCharacterSetup::AddEquipFromAll()
{
	m_NeedEquips.clear();
	uint32 level = m_Player->getLevel();
	uint8 prof = m_Player->getClass();
	if (prof <= 0 || prof >= MAX_CLASSES)
		return;
	const ItemTemplate* firstFinger = NULL;
	const ItemTemplate* firstTrinket = NULL;
	for (int i = 0; i < InventoryType::INVTYPE_RELIC; i++)
	{
        //EquipmentByLevel& equips = classesEquips[prof][i];
        //EquipmentByLevel::iterator itEquip = equips.find(level);
		//if (itEquip == equips.end())
		//	continue;
		if (i != InventoryType::INVTYPE_CLOAK && i > InventoryType::INVTYPE_TRINKET)
			continue;
		if (i == InventoryType::INVTYPE_FINGER && !firstFinger)
		{
			const ItemTemplate* item = GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_FINGER, level, firstFinger);
			firstFinger = item;
            AddOnceEquip(item, EQUIPMENT_SLOT_FINGER1);
		}
		else if (i == InventoryType::INVTYPE_TRINKET && !firstTrinket)
		{
            const ItemTemplate* item = GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_TRINKET, level, firstTrinket);
			firstTrinket = item;
            AddOnceEquip(item, EQUIPMENT_SLOT_TRINKET1);
		}
		else
		{
			const ItemTemplate* item = GetRandomItemFromLoopLV(prof, (InventoryType)i, level);
			AddOnceEquip(item);
		}
	}
	if (firstFinger)
        AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_FINGER, level, firstFinger), EQUIPMENT_SLOT_FINGER2);
	if (firstTrinket)
        AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_TRINKET, level, firstTrinket), EQUIPMENT_SLOT_TRINKET2);

    RandomWeaponsForSpecialization();
}

void PlayerCharacterSetup::UpequipFromAll()
{
    for (PendingEquipment::iterator itNeed = m_NeedEquips.begin();
		itNeed != m_NeedEquips.end();
		itNeed++)
	{
        Item* itemInst = m_Player->GetItemByGuid(itNeed->first);
        if (!itemInst || !m_Player->IsInventoryPos(itemInst->GetPos()) || m_Player->IsBankPos(itemInst->GetPos()))
        {
            ++m_SetupFailures;
            continue;
        } // Removed, equipped or banked since the previous reset step.
		if (itemInst->GetTemplate()->GetInventoryType() == InventoryType::INVTYPE_AMMO)
		{
			//m_Player->SetAmmo(itemInst->GetEntry());
		}
        else if (!EquipItem(itemInst, itNeed->second))
            ++m_SetupFailures;
	}
	m_NeedEquips.clear();
}

bool PlayerCharacterSetup::EquipItem(Item* pItem, uint8 slot)
{
	uint16 dest;
    InventoryResult msg = m_Player->CanEquipItem(slot, dest, pItem, !pItem->IsBag());
	if (msg != EQUIP_ERR_OK)
	{
		return false;
	}

	uint16 src = pItem->GetPos();
	if (dest == src)                                           // prevent equip in same slot, only at cheat
		return false;

	Item* pDstItem = m_Player->GetItemByPos(dest);
	if (!pDstItem)                                         // empty slot, simple case
	{
		m_Player->RemoveItem(pItem->GetBagSlot(), pItem->GetSlot(), true);
		m_Player->EquipItem(dest, pItem, true);
		m_Player->AutoUnequipOffhandIfNeed();
	}
	else                                                    // have currently equipped item, not simple case
	{
		uint8 dstbag = pDstItem->GetBagSlot();
		uint8 dstslot = pDstItem->GetSlot();

		msg = m_Player->CanUnequipItem(dest, !pItem->IsBag());
		if (msg != EQUIP_ERR_OK)
		{
			return false;
		}

		// check dest->src move possibility
		ItemPosCountVec sSrc;
		uint16 eSrc = 0;
		if (m_Player->IsInventoryPos(src))
		{
			msg = m_Player->CanStoreItem(pItem->GetBagSlot(), pItem->GetSlot(), sSrc, pDstItem, true);
			if (msg != EQUIP_ERR_OK)
				msg = m_Player->CanStoreItem(pItem->GetBagSlot(), NULL_SLOT, sSrc, pDstItem, true);
			if (msg != EQUIP_ERR_OK)
				msg = m_Player->CanStoreItem(NULL_BAG, NULL_SLOT, sSrc, pDstItem, true);
		}
		else if (m_Player->IsBankPos(src))
		{
			msg = m_Player->CanBankItem(pItem->GetBagSlot(), pItem->GetSlot(), sSrc, pDstItem, true);
			if (msg != EQUIP_ERR_OK)
				msg = m_Player->CanBankItem(pItem->GetBagSlot(), NULL_SLOT, sSrc, pDstItem, true);
			if (msg != EQUIP_ERR_OK)
				msg = m_Player->CanBankItem(NULL_BAG, NULL_SLOT, sSrc, pDstItem, true);
		}
		else if (m_Player->IsEquipmentPos(src))
		{
			msg = m_Player->CanEquipItem(pItem->GetSlot(), eSrc, pDstItem, true);
			if (msg == EQUIP_ERR_OK)
				msg = m_Player->CanUnequipItem(eSrc, true);
		}

		if (msg != EQUIP_ERR_OK)
		{
			return false;
		}

		// now do moves, remove...
		m_Player->RemoveItem(dstbag, dstslot, false);
		m_Player->RemoveItem(pItem->GetBagSlot(), pItem->GetSlot(), false);

		// add to dest
		m_Player->EquipItem(dest, pItem, true);

		// add to src
		if (m_Player->IsInventoryPos(src))
			m_Player->StoreItem(sSrc, pDstItem, true);
		else if (m_Player->IsBankPos(src))
			m_Player->BankItem(sSrc, pDstItem, true);
		else if (m_Player->IsEquipmentPos(src))
			m_Player->EquipItem(eSrc, pDstItem, true);

		m_Player->AutoUnequipOffhandIfNeed();
	}
	return true;
}

void PlayerCharacterSetup::SupplementOtherItems()
{
	uint8 prof = m_Player->getClass();
	switch (prof)
	{
	case 1:
		SupplementItemByWarrior();
		break;
	case 2:
		SupplementItemByPaladin();
		break;
	}
}

const ItemTemplate* PlayerCharacterSetup::GetRandomAmmoByType(ItemSubclassProjectile iType, uint32 startLV)
{
    EquipmentByLevel& equips = classesEquips[3][InventoryType::INVTYPE_AMMO];
	for (int i = startLV; i > 0; i--)
	{
        EquipmentByLevel::iterator itEquip = equips.find(i);
		if (itEquip == equips.end() || itEquip->second.m_Items.size() <= 0)
			continue;
		for (int j = 0; j < 3; j++)
		{
			const ItemTemplate* item = itEquip->second.RandomItem();
			if (item && item->GetSubClass() == iType)
				return item;
		}
	}
	return NULL;
}

const ItemTemplate* PlayerCharacterSetup::GetRandomItemFromLoopLV(uint32 prof, InventoryType iType, uint32 startLV, const ItemTemplate* filter)
{
    if (!m_Player || prof == 0 || prof >= MAX_CLASSES || iType > INVTYPE_RELIC)
        return nullptr;
    EquipmentByLevel& equips = classesEquips[prof][iType];
    auto select = [this, filter](LevelItems const& items) -> ItemTemplate const*
    {
        ItemTemplate const* selected = nullptr;
        uint32 count = 0;
        for (ItemTemplate const* item : items)
            if (item && item != filter &&
                item->IsUsableBySpecialization(m_Player->GetSpecializationId(), m_Player->getLevel(), false) &&
                m_Player->CanUseItem(item) == EQUIP_ERR_OK)
            {
                // Sample all eligible candidates instead of two possibly incompatible draws.
                if (urand(1, ++count) == 1)
                    selected = item;
            }
        return selected;
    };
    for (uint32 level = startLV; level > 0; --level)
    {
        auto itr = equips.find(level);
        if (itr == equips.end())
            continue;
        if (m_TenacitySetting)
            if (ItemTemplate const* item = select(itr->second.m_TenacityItems))
                return item;
        if (ItemTemplate const* item = select(itr->second.m_Items))
            return item;
    }
    return nullptr;
}

bool PlayerCharacterSetup::IsTenacityEquipSlot(uint8 slot)
{
	switch (EquipmentSlots(slot))
	{
	case EquipmentSlots::EQUIPMENT_SLOT_HEAD:
	case EquipmentSlots::EQUIPMENT_SLOT_NECK:
	case EquipmentSlots::EQUIPMENT_SLOT_SHOULDERS:
	case EquipmentSlots::EQUIPMENT_SLOT_BODY:
	case EquipmentSlots::EQUIPMENT_SLOT_CHEST:
	case EquipmentSlots::EQUIPMENT_SLOT_WAIST:
	case EquipmentSlots::EQUIPMENT_SLOT_LEGS:
	case EquipmentSlots::EQUIPMENT_SLOT_FEET:
	case EquipmentSlots::EQUIPMENT_SLOT_WRISTS:
	case EquipmentSlots::EQUIPMENT_SLOT_HANDS:
	case EquipmentSlots::EQUIPMENT_SLOT_FINGER1:
	case EquipmentSlots::EQUIPMENT_SLOT_FINGER2:
	case EquipmentSlots::EQUIPMENT_SLOT_BACK:
	case EquipmentSlots::EQUIPMENT_SLOT_MAINHAND:
	case EquipmentSlots::EQUIPMENT_SLOT_OFFHAND:
	case EquipmentSlots::EQUIPMENT_SLOT_RANGED:
		return true;
	}
	return false;
}

bool PlayerCharacterSetup::EquipIsTidiness()
{
	uint8 level = m_Player->getLevel();
	uint32 noMatchEquipCount = 0;
	for (uint8 slot = EquipmentSlots::EQUIPMENT_SLOT_HEAD; slot < EquipmentSlots::EQUIPMENT_SLOT_END; slot++)
	{
		Item* pItem = m_Player->GetItemByPos(255, slot);
		if (!pItem)
		{
			++noMatchEquipCount;
			if (level <= 20)
			{
				if (noMatchEquipCount > 10)
					return false;
			}
			else if (noMatchEquipCount >= 5)
				return false;
			continue;
		}
	}
	return true;
}

bool PlayerCharacterSetup::CheckNeedTenacityFlush()
{
	uint32 noMatchEquipCount = 0;
	for (uint8 slot = EquipmentSlots::EQUIPMENT_SLOT_HEAD; slot < EquipmentSlots::EQUIPMENT_SLOT_END; slot++)
	{
		if (!IsTenacityEquipSlot(slot))
			continue;
		//uint16 pos = (255 << 8) | slot;
		//if (m_Player->IsEquipmentPos(pos) || m_Player->IsBagPos(pos))
		//{
		//	InventoryResult msg = m_Player->CanUnequipItem(pos, false);
		//	if (msg != EQUIP_ERR_OK)
		//		continue;
		//}
		Item* pItem = m_Player->GetItemByPos(255, slot);
		if (!pItem)
		{
			++noMatchEquipCount;
			if (noMatchEquipCount > 2)
				return true;
			continue;
		}
		const ItemTemplate* pTemplate = pItem->GetTemplate();
		if (!ItemsForLevel::IsTenacityItem(pTemplate))
		{
			++noMatchEquipCount;
			if (noMatchEquipCount > 2)
				return true;
		}
	}
	return false;
}

void PlayerCharacterSetup::AddOnceEquip(const ItemTemplate* item, uint8 slot)
{
    if (!item)
    {
        if (slot != NULL_SLOT)
            ++m_SetupFailures;
        return;
    }
	//m_Player->AddItem(item->GetId(), 1);
	uint32 count = 1;
	if (item->GetClass() == ItemClass::ITEM_CLASS_PROJECTILE && item->GetInventoryType() == InventoryType::INVTYPE_AMMO)
		count = 1000;
	uint32 noSpaceForCount = 0;
	ItemPosCountVec dest;
	InventoryResult msg = m_Player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, item->GetId(), count, &noSpaceForCount);
	if (msg != EQUIP_ERR_OK)
		count -= noSpaceForCount;
    if (count <= 0 || dest.empty())
    {
        ++m_SetupFailures;
        return;
    }
	Item* itemInst = m_Player->StoreNewItem(dest, item->GetId(), true, GenerateItemRandomPropertyId(item->GetId()));
	if (itemInst)
        m_NeedEquips.emplace_back(itemInst->GetGUID(), slot);
    else
        ++m_SetupFailures;
}

void PlayerCharacterSetup::RandomWeaponsForSpecialization()
{
    uint32 const level = m_Player->getLevel();
    uint32 const playerClass = m_Player->getClass();
    auto choose = [this, playerClass, level](InventoryType type, ItemTemplate const* exclude = nullptr)
    {
        return GetRandomItemFromLoopLV(playerClass, type, level, exclude);
    };
    auto oneHand = [&choose](bool offhand, ItemTemplate const* exclude = nullptr)
    {
        ItemTemplate const* item = choose(INVTYPE_WEAPON, exclude);
        return item ? item : choose(offhand ? INVTYPE_WEAPONOFFHAND : INVTYPE_WEAPONMAINHAND, exclude);
    };
    auto dualWield = [this, &choose, &oneHand](bool twoHanded)
    {
        ItemTemplate const* main = twoHanded ? choose(INVTYPE_2HWEAPON) : oneHand(false);
        AddOnceEquip(main, EQUIPMENT_SLOT_MAINHAND);
        if (main && m_Player->CanDualWield())
            AddOnceEquip(twoHanded ? choose(INVTYPE_2HWEAPON, main) : oneHand(true, main), EQUIPMENT_SLOT_OFFHAND);
    };
    switch (m_Player->GetSpecializationId())
    {
        case TALENT_SPEC_WARRIOR_FURY:
            dualWield(m_Player->CanTitanGrip());
            return;
        case TALENT_SPEC_DEATHKNIGHT_FROST:
        case TALENT_SPEC_ROGUE_ASSASSINATION:
        case TALENT_SPEC_ROGUE_COMBAT:
        case TALENT_SPEC_ROGUE_SUBTLETY:
        case TALENT_SPEC_SHAMAN_ENHANCEMENT:
        case TALENT_SPEC_MONK_BATTLEDANCER:
        case TALENT_SPEC_DEMON_HUNTER_HAVOC:
        case TALENT_SPEC_DEMON_HUNTER_VENGEANCE:
            dualWield(false);
            return;
        case TALENT_SPEC_WARRIOR_ARMS:
        case TALENT_SPEC_PALADIN_RETRIBUTION:
        case TALENT_SPEC_DEATHKNIGHT_BLOOD:
        case TALENT_SPEC_DEATHKNIGHT_UNHOLY:
        case TALENT_SPEC_HUNTER_SURVIVAL:
        case TALENT_SPEC_DRUID_CAT:
        case TALENT_SPEC_DRUID_BEAR:
        case TALENT_SPEC_MONK_BREWMASTER:
            AddOnceEquip(choose(INVTYPE_2HWEAPON), EQUIPMENT_SLOT_MAINHAND);
            return;
        case TALENT_SPEC_HUNTER_BEASTMASTER:
        case TALENT_SPEC_HUNTER_MARKSMAN:
        {
            ItemTemplate const* item = choose(INVTYPE_RANGED);
            AddOnceEquip(item ? item : choose(INVTYPE_RANGEDRIGHT), EQUIPMENT_SLOT_MAINHAND);
            return;
        }
        case TALENT_SPEC_WARRIOR_PROTECTION:
        case TALENT_SPEC_PALADIN_HOLY:
        case TALENT_SPEC_PALADIN_PROTECTION:
        case TALENT_SPEC_SHAMAN_ELEMENTAL:
        case TALENT_SPEC_SHAMAN_RESTORATION:
            AddOnceEquip(oneHand(false), EQUIPMENT_SLOT_MAINHAND);
            AddOnceEquip(choose(INVTYPE_SHIELD), EQUIPMENT_SLOT_OFFHAND);
            return;
        case TALENT_SPEC_MAGE_ARCANE:
        case TALENT_SPEC_MAGE_FIRE:
        case TALENT_SPEC_MAGE_FROST:
        case TALENT_SPEC_PRIEST_DISCIPLINE:
        case TALENT_SPEC_PRIEST_HOLY:
        case TALENT_SPEC_PRIEST_SHADOW:
        case TALENT_SPEC_WARLOCK_AFFLICTION:
        case TALENT_SPEC_WARLOCK_DEMONOLOGY:
        case TALENT_SPEC_WARLOCK_DESTRUCTION:
        case TALENT_SPEC_DRUID_BALANCE:
        case TALENT_SPEC_DRUID_RESTORATION:
        case TALENT_SPEC_MONK_MISTWEAVER:
        {
            if (ItemTemplate const* staff = choose(INVTYPE_2HWEAPON))
                AddOnceEquip(staff, EQUIPMENT_SLOT_MAINHAND);
            else
            {
                ItemTemplate const* main = oneHand(false);
                if (!main)
                    main = choose(INVTYPE_RANGEDRIGHT); // Wands occupy the main hand in Legion.
                AddOnceEquip(main, EQUIPMENT_SLOT_MAINHAND);
                if (main)
                    AddOnceEquip(choose(INVTYPE_HOLDABLE), EQUIPMENT_SLOT_OFFHAND);
            }
            return;
        }
        default:
            return;
    }
}

void PlayerCharacterSetup::SupplementItemByWarrior()
{
	uint32 level = m_Player->getLevel();
	uint32 prof = 1;
	switch (m_ActiveTalentType)
	{
	case 0:
	{
		ItemTemplate* item1 = (ItemTemplate*)GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_WEAPON, level);
		if (!item1)
			item1 = (ItemTemplate*)GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_WEAPONMAINHAND, level);
		AddOnceEquip(item1);
		AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_SHIELD, level));
	}
	break;
	case 1:
	{
		AddOnceEquip(GetRandomItemFromLoopLV(1, InventoryType::INVTYPE_2HWEAPON, level));
		AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_SHIELD, level));
	}
	break;
	case 2:
	{
		AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_WEAPON, level));
		AddOnceEquip(GetRandomItemFromLoopLV(1, InventoryType::INVTYPE_2HWEAPON, level));
	}
	break;
	}
	m_NeedEquips.clear();
}

void PlayerCharacterSetup::SupplementItemByPaladin()
{
	uint32 level = m_Player->getLevel();
	uint32 prof = 2;
	switch (m_ActiveTalentType)
	{
	case 0:
	case 1:
	{
		AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_2HWEAPON, level));
	}
	break;
	case 2:
	{
		ItemTemplate* item1 = (ItemTemplate*)GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_WEAPON, level);
		if (!item1)
			item1 = (ItemTemplate*)GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_WEAPONMAINHAND, level);
		AddOnceEquip(item1);
		AddOnceEquip(GetRandomItemFromLoopLV(prof, InventoryType::INVTYPE_SHIELD, level));
	}
	break;
	}
	m_NeedEquips.clear();
}
