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

#ifndef TRINITY_PLAYER_CHARACTER_SETUP_H
#define TRINITY_PLAYER_CHARACTER_SETUP_H

#include "Log.h"
#include "Common.h"
#include "SharedDefines.h"
#include "DatabaseEnv.h"
#include "Player.h"
#include "ItemTemplate.h"

typedef std::vector<const ItemTemplate*> LevelItems;
class TC_GAME_API ItemsForLevel
{
public:
	static bool IsTenacityItem(const ItemTemplate* itemTemplate);

public:
	ItemsForLevel() {}
	void AddItem(const ItemTemplate* pItem);
	const ItemTemplate* RandomItem();
	const ItemTemplate* RandomTenacityItem();

    LevelItems m_Items;
    LevelItems m_TenacityItems;
};

struct TalentEntry;
class TC_GAME_API ClassTalentEntry
{
public:
    ClassTalentEntry(uint32 cls, uint32 index, const TalentEntry* entry) :
		prof(cls), pageIndex(index), talentEntry(entry)
	{
	}

    bool operator < (const ClassTalentEntry &tal) const;

public:
	uint32 prof;
	uint32 pageIndex;
	const TalentEntry* talentEntry;
};

class TC_GAME_API PlayerCharacterSetup
{
public:
	typedef std::set<uint32> SetEntrys;
    typedef std::set<ClassTalentEntry> ClassTalentPage;
    typedef std::map<uint32, ItemsForLevel> EquipmentByLevel;
    typedef std::list<Item*> PendingEquipment;
    typedef std::list<uint32> ClassCommonSpells;
    typedef std::vector<uint32> MountSpellIds;

	static void Initialize();
	static bool BindingPlayerHomePosition(Player* player);
	static uint32 FindPlayerTalentType(Player* player);
	static bool MatchEquipmentSlot(uint8 pos, const ItemTemplate* itemTemplate);
	static uint32 GetItemLevelByAI(const ItemTemplate* item);
	static void ClearUnknowMount(Player* player);
	static uint32 CheckMaxLevel(uint32 level);
    static bool IsSpecialFlyingMountAura(uint32 aura);

private:
	//static bool MatchEquipmentSlotsByWeapon(EquipmentSlots slot, InventoryType iType);
	//static bool MatchEquipmentSlotsByArmor(EquipmentSlots slot, InventoryType iType);
	//static bool MatchRangeEquipmentSlots(uint32 cls, const ItemTemplate* itemTemplate);
	static bool IsCommonEquip(const ItemTemplate* itemTemplate);
	static bool IsTrinketEquip(const ItemTemplate* itemTemplate);
	static bool IsWarriorEquip(const ItemTemplate* itemTemplate);
	static bool IsPaladinEquip(const ItemTemplate* itemTemplate);
	static bool IsDeathKightEquip(const ItemTemplate* itemTemplate);
	static bool IsRogueEquip(const ItemTemplate* itemTemplate);
	static bool IsDruidEquip(const ItemTemplate* itemTemplate);
	static bool IsHunterEquip(const ItemTemplate* itemTemplate);
	static bool IsShamanEquip(const ItemTemplate* itemTemplate);
	static bool IsMageEquip(const ItemTemplate* itemTemplate);
	static bool IsWarlockEquip(const ItemTemplate* itemTemplate);
	static bool IsPriestEquip(const ItemTemplate* itemTemplate);
	static bool IsEquipByClasses(uint32 cls, const ItemTemplate* itemTemplate);
	static bool IsEquipByClsAndTal(uint32 cls, uint32 tal, const ItemTemplate* itemTemplate, int32 rndPropID);
	static bool IsOnlyPhysicsAttributeEquip(const ItemTemplate* itemTemplate, bool coverIntellect);
	static bool IsOnlyMagicAttributeEquip(const ItemTemplate* itemTemplate);
	static bool IsTankAttributeEquip(const ItemTemplate* itemTemplate);
	static bool IsOnlyPhysicsRandomAttributeByEquip(std::list<uint32>& enchants, bool coverIntellect);
	static bool IsOnlyMagicRandomAttributeByEquip(std::list<uint32>& enchants);
	static bool IsTankRandomAttributeByEquip(std::list<uint32>& enchants);
	static void GetRandomPropEnchantments(int32 rndPropID, std::list<uint32>& enchants);

public:
    PlayerCharacterSetup(Player* player);
    ~PlayerCharacterSetup();

	bool EquipIsTidiness();
	bool CheckNeedTenacityFlush();
	uint32 UpdateTalentType();
	uint32 GetTalentType();
	bool IsFinish() { return m_Finish; }
	bool ResetPlayerToLevel(uint32 level, uint32 talent, bool tenacity = false);
	uint32 SwitchPlayerTalent(uint32 talent);
	void SupplementAmmo();
	void UpdateReset();
	void ViderLesSacs();
	void LearnSpells();
	void ActivateSpecialization();
	void LearnTalents();
	bool EquipItem(Item* pItem);

private:
	void RemoveSpells();
	void LearnCommonSpells();
	void CheckInventroy();
	void AddEquipFromAll();
	void UpequipFromAll();
	void SupplementOtherItems();

	bool IsTenacityEquipSlot(uint8 slot);
	void AddOnceEquip(const ItemTemplate* item);
	const ItemTemplate* GetRandomAmmoByType(ItemSubclassProjectile ammoType, uint32 startLV);
	const ItemTemplate* GetRandomItemFromLoopLV(uint32 prof, InventoryType iType, uint32 startLV, const ItemTemplate* filter = 0);
	void RandomWeaponByWarrior();
	void RandomWeaponByPaladin();
	void RandomWeaponByDeathKight();
	void RandomWeaponByRogue();
	void RandomWeaponByDruid();
	void RandomWeaponByHunter();
	void RandomWeaponByShaman();
	void RandomWeaponByMage();
	void RandomWeaponByWarlock();
	void RandomWeaponByPriest();

	void SupplementItemByWarrior();
	void SupplementItemByPaladin();

private:
	bool m_Finish;
	bool m_TenacitySetting;
	uint32 m_ResetStep;
	Player* m_Player;
    PendingEquipment m_NeedEquips;
	uint32 m_ActiveTalentType;

	static uint32 classesTrainersGUID[MAX_CLASSES][2];
    static ClassTalentPage classesTalents[MAX_CLASSES][3];
    static EquipmentByLevel classesEquips[MAX_CLASSES][InventoryType::INVTYPE_RELIC+1];
    static ClassCommonSpells classesCommonSpells[MAX_CLASSES];
    static MountSpellIds normalMountSpells;
    static MountSpellIds fastMountSpells;
    static SetEntrys specialFlyingMountSpells;
};

#endif // TRINITY_PLAYER_CHARACTER_SETUP_H
