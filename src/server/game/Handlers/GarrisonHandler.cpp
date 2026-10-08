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

#include "WorldSession.h"
#include "WodGarrison.h"
#include "Creature.h"
#include "ClassHall.h"
#include "GarrisonAI.h"
#include "GarrisonMgr.h"
#include "GarrisonPackets.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Creature.h"
#include "SpellMgr.h"
#include "SpellInfo.h"

#include <algorithm>

void WorldSession::HandleGetGarrisonInfo(WorldPackets::Garrison::GetGarrisonInfo& /*getGarrisonInfo*/)
{
    _player->SendGarrisonInfo();
}

void WorldSession::HandleGarrisonPurchaseBuilding(WorldPackets::Garrison::GarrisonPurchaseBuilding& garrisonPurchaseBuilding)
{
    if (!_player->GetNPCIfCanInteractWith(garrisonPurchaseBuilding.NpcGUID, UNIT_NPC_FLAG_GARRISON_ARCHITECT))
        return;

    if (Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_GARRISON))
        garrison->ToWodGarrison()->PlaceBuilding(garrisonPurchaseBuilding.PlotInstanceID, garrisonPurchaseBuilding.BuildingID);
}

void WorldSession::HandleGarrisonCancelConstruction(WorldPackets::Garrison::GarrisonCancelConstruction& garrisonCancelConstruction)
{
    if (!_player->GetNPCIfCanInteractWith(garrisonCancelConstruction.NpcGUID, UNIT_NPC_FLAG_GARRISON_ARCHITECT))
        return;

    if (Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_GARRISON))
        garrison->ToWodGarrison()->CancelBuildingConstruction(garrisonCancelConstruction.PlotInstanceID);
}

void WorldSession::HandleGarrisonCheckUpgradeable(WorldPackets::Garrison::GarrisonCheckUpgradeable& /*garrisonCheckUpgradeable*/)
{
    bool canUpgrade = false;
    if (Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_GARRISON))
        canUpgrade = garrison->ToWodGarrison()->CanUpgrade(false);

    SendPacket(WorldPackets::Garrison::GarrisonCheckUpgradeableResult(canUpgrade).Write());
}

void WorldSession::HandleGarrisonUpgrade(WorldPackets::Garrison::GarrisonUpgrade& garrisonUpgrade)
{
    if (!_player->GetNPCIfCanInteractWith(garrisonUpgrade.NpcGUID, UNIT_NPC_FLAG_GARRISON_ARCHITECT))
        return;

    if (Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_GARRISON))
    {
        /*bool result = */garrison->ToWodGarrison()->Upgrade();
        //SendPacket(WorldPackets::Garrison::GarrisonUpgradeResult().Write());
    }
}

void WorldSession::HandleGarrisonRequestBlueprintAndSpecializationData(WorldPackets::Garrison::GarrisonRequestBlueprintAndSpecializationData& /*garrisonRequestBlueprintAndSpecializationData*/)
{
    _player->SendGarrisonBlueprintAndSpecializationData();
}

void WorldSession::HandleGarrisonGetBuildingLandmarks(WorldPackets::Garrison::GarrisonGetBuildingLandmarks& /*garrisonGetBuildingLandmarks*/)
{
    if (Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_GARRISON))
        garrison->ToWodGarrison()->SendBuildingLandmarks(_player);
}

void WorldSession::HandleGarrisonOpenMissionNpc(WorldPackets::Garrison::GarrisonOpenMissionNpcClient& garrisonOpenMissionNpcClient)
{
    if (!_player->GetNPCIfCanInteractWith(garrisonOpenMissionNpcClient.NpcGUID, UNIT_NPC_FLAG_GARRISON_MISSION_NPC))
        return;

    GarrisonType garType = GARRISON_TYPE_CLASS_HALL; // Todo : differenciate depending of NPC
    switch (garrisonOpenMissionNpcClient.NpcGUID.GetEntry())
    {
    case 81546://ALLIANCE
    case 84224:
    case 84698:
    case 80432://HORDE 
    case 86031:
    case 85805:
        garType = GARRISON_TYPE_GARRISON;
        break;
    default:
        garType = GARRISON_TYPE_CLASS_HALL;
        break;
    }
    Garrison const* garrison = _player->GetGarrison(garType);

    if (!garrison)
        return;

    if (garType == GARRISON_TYPE_CLASS_HALL)
    {
        // quetes deja en cours avant ce correctif : leur mission n avait jamais ete posee
        _player->AddQuestGarrisonMissions();

        // La table de commandement d un domaine de classe (ex. Р’В« Scouting Map Р’В» 102669 du
        // Pavillon du Traqueur, que la quete 42523 fait utiliser pour lancer une mission)
        // ouvre la fenetre des MISSIONS. Le core envoyait SMSG_SHOW_ADVENTURE_MAP, la carte
        // de choix de zone : une carte s affichait sans rien de cliquable (Blez, 30/09/2026).
        // Le champ lu Р’В« GarrTypeID Р’В» est en realite le type de sujet demande par le client
        // Class halls always use follower type 4, including clients requesting type 1.
        WorldPackets::Garrison::GarrisonOpenMissionNpc garrisonOpenMissionNpc;
        garrisonOpenMissionNpc.NpcGUID = garrisonOpenMissionNpcClient.NpcGUID;
        garrisonOpenMissionNpc.FollowerType = int32(FOLLOWER_TYPE_CLASS_HALL);
        SendPacket(garrisonOpenMissionNpc.Write());
    }
    else
    {
        WorldPackets::Garrison::GarrisonOpenMissionNpc garrisonOpenMissionNpc;
        garrisonOpenMissionNpc.NpcGUID = garrisonOpenMissionNpcClient.NpcGUID;
        garrisonOpenMissionNpc.FollowerType = int32(FOLLOWER_TYPE_GARRISON);
        SendPacket(garrisonOpenMissionNpc.Write());
    }
}

void WorldSession::HandleGarrisonRequestScoutingMap(WorldPackets::Garrison::GarrisonRequestScoutingMap& scoutingMap)
{
    WorldPackets::Garrison::GarrisonScoutingMapResult result;
    result.ID = scoutingMap.ID;
    result.Active = true;
    SendPacket(result.Write());
}

void WorldSession::HandleGarrisonStartMission(WorldPackets::Garrison::GarrisonStartMission& startMission)
{
    if (!_player->GetNPCIfCanInteractWith(startMission.NpcGUID, UNIT_NPC_FLAG_GARRISON_MISSION_NPC))
        return;

    GarrMissionEntry const* missionEntry = sGarrMissionStore.LookupEntry(startMission.MissionID);
    if (!missionEntry)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType(missionEntry->GarrTypeID));
    if (!garrison)
        return;

    garrison->StartMission(startMission.MissionID, startMission.Followers);
}

void WorldSession::HandleGarrisonCompleteMission(WorldPackets::Garrison::GarrisonCompleteMission& completeMission)
{
    if (!_player->GetNPCIfCanInteractWith(completeMission.NpcGUID, UNIT_NPC_FLAG_GARRISON_MISSION_NPC))
        return;

    GarrMissionEntry const* missionEntry = sGarrMissionStore.LookupEntry(completeMission.MissionID);
    if (!missionEntry)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType(missionEntry->GarrTypeID));
    if (!garrison)
        return;

    garrison->CompleteMission(completeMission.MissionID);
}

void WorldSession::HandleGarrisonMissionBonusRoll(WorldPackets::Garrison::GarrisonMissionBonusRoll& missionBonusRoll)
{
    if (!_player->GetNPCIfCanInteractWith(missionBonusRoll.NpcGUID, UNIT_NPC_FLAG_GARRISON_MISSION_NPC))
        return;

    GarrMissionEntry const* missionEntry = sGarrMissionStore.LookupEntry(missionBonusRoll.MissionID);
    if (!missionEntry)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType(missionEntry->GarrTypeID));
    if (!garrison)
        return;

    garrison->CalculateMissonBonusRoll(missionBonusRoll.MissionID);
}

void WorldSession::HandleRequestLandingPageShipmentInfoOpcode(WorldPackets::Garrison::GarrisonRequestLandingPageShipmentInfo& /*packet*/)
{
    if (!_player)
        return;

    Garrison* garrison = _player->GetGarrison(GARRISON_TYPE_CLASS_HALL);
    if (!garrison)
        return;

    WorldPackets::Garrison::GarrisonLandingPageShipmentInfo result;
    result.GarrisonType = uint32(garrison->GetType());
    for (auto const& pair : garrison->GetWorkOrders())
    {
        Garrison::WorkOrder const& order = pair.second;
        CharShipmentEntry const* entry = sCharShipmentStore.LookupEntry(order.ShipmentID);
        if (!entry || !order.DatabaseID || order.CompleteTime < order.CreationTime)
            continue;

        WorldPackets::Garrison::GarrisonShipment shipment;
        shipment.ShipmentId = order.DatabaseID;
        shipment.ShipmentRecId = order.ShipmentID;
        // GarrFollowerID is a DB2 record ID, not an assigned follower database ID.
        shipment.AssignedFollowerDBID = 0;
        shipment.CreationTime = order.CreationTime;
        shipment.ShipmentDuration = order.CompleteTime - order.CreationTime;
        shipment.BuildingType = 0;
        result.Shipments.push_back(shipment);
    }
    SendPacket(result.Write());
}

void WorldSession::HandleGarrisonAssignFollowerToBuilding(WorldPackets::Garrison::GarrisonAssignFollowerToBuilding& /*packet*/)
{ }

void WorldSession::HandleGarrisonGenerateRecruits(WorldPackets::Garrison::GarrisonGenerateRecruits& generateRecruits)
{
    if (!_player)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType::GARRISON_TYPE_CLASS_HALL);

    if (!garrison)
        return;

    if (Creature* unit = _player->GetNPCIfCanInteractWith(generateRecruits.NpcGUID, 0))
    {
        _player->Whisper(std::string("CMSG_GARRISON_GENERATE_RECRUITS"), Language::LANG_COMMON, _player);
        // if (unit->ToGarrisonNPCAI()) 
        //     unit->ToGarrisonNPCAI()->SendRecruitmentFollowersGenerated(_player, generateRecruits.AbiltyID ? generateRecruits.AbiltyID : generateRecruits.TraitID, 0, generateRecruits.TraitID ? true : false);
    }
}

void WorldSession::HandleGarrisonRecruitFollower(WorldPackets::Garrison::GarrisonRecruitsFollower& garrisonRecruitsFollower)
{
    if (_player == nullptr)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType::GARRISON_TYPE_CLASS_HALL);

    if (!garrison)
        return;

    WorldPackets::Garrison::GarrisonRecruitFollowerResult result;
    std::unordered_map<uint64 /*dbId*/, Garrison::Follower> followers = garrison->GetFollowers();

    if (Creature* unit = _player->GetNPCIfCanInteractWith(garrisonRecruitsFollower.NpcGUID, 0))
    {
        result.resultID = uint32(GarrisonError::GARRISON_SUCCESS);

        for (auto& follower : followers)
        {
            if (follower.second.PacketInfo.GarrFollowerID == garrisonRecruitsFollower.FollowerID)
            {
                result.followers.push_back(follower.second.PacketInfo);
                garrison->AddFollower(garrisonRecruitsFollower.FollowerID);
                //l_Garrison->SetCanRecruitFollower(false);
                //m_Player->SetCharacterWorldState(CharacterWorldStates::GarrisonTavernBoolCanRecruitFollower, 0);
                break;
            }
        }
        SendPacket(result.Write());
    }
}

void WorldSession::HandleGarrisonSetFollowerInactive(WorldPackets::Garrison::GarrisonSetFollowerInactive& garrisonSetFollowerInactive)
{
    if (_player == nullptr)
        return;

    Garrison* garrison = _player->GetGarrison(GarrisonType::GARRISON_TYPE_CLASS_HALL);

    if (!garrison)
        return;

    garrison->ChangeFollowerActivationState(garrisonSetFollowerInactive.followerDBID, !garrisonSetFollowerInactive.desActivate);
}

void WorldSession::HandleGarrisonGetShipmentInfo(WorldPackets::Garrison::GarrisonRequestShipmentInfo& request)
{
    if (!_player)
        return;

    Creature* unit = _player->GetNPCIfCanInteractWith(request.NpcGUID, UNIT_NPC_FLAG_SHIPMENT_CRAFTER);
    if (!unit || !_player->IsInGarrison())
        return;

    for (uint32 i = 0; i < sCharShipmentStore.GetNumRows(); ++i)
    {
        CharShipmentEntry const* shipment = sCharShipmentStore.LookupEntry(i);
        if (!shipment || shipment->ShipmentContainerID != unit->GetShipmentContainerID())
            continue;

        CharShipmentContainerEntry const* container = sCharShipmentContainerStore.LookupEntry(shipment->ShipmentContainerID);
        if (!container)
            return;
        Garrison* garrison = _player->GetGarrison(GarrisonType(container->GarrTypeID));
        if (!garrison)
            return;
        uint32 const plotId = garrison->GetClassHallPlotId(unit->GetEntry());
        if (!plotId)
            return;

        auto orders = garrison->GetBuildingWorkOrders(plotId);
        orders.erase(std::remove_if(orders.begin(), orders.end(), [](Garrison::WorkOrder const& order)
        {
            return !order.DatabaseID || order.CompleteTime < order.CreationTime || !sCharShipmentStore.LookupEntry(order.ShipmentID);
        }), orders.end());

        WorldPacket response(SMSG_GET_SHIPMENT_INFO_RESPONSE, 1024);
        response.WriteBit(true);
        response.FlushBits();
        response << uint32(shipment->ID);
        response << uint32(shipment->MaxShipments);
        response << uint32(orders.size());
        response << uint32(plotId);
        for (Garrison::WorkOrder const& order : orders)
        {
            response << uint32(order.ShipmentID);
            response << uint64(order.DatabaseID);
            response << uint64(0);
            response << uint32(order.CreationTime);
            response << uint32(order.CompleteTime - order.CreationTime);
            response << uint32(0);
        }
        SendPacket(&response);
        return;
    }
}


void WorldSession::HandleGarrisonResearchTalent(WorldPackets::Garrison::GarrisonResearchTalent& researchTalent)
{
    printf("HandleGarrisonResearchTalent GarrTalentID=%d \n", researchTalent.GarrTalentID);
    WorldPackets::Garrison::GarrisonResearchTalentResult result;
    result.Result = uint32(GarrisonError::GARRISON_SUCCESS);
    result.GarrTypeId = uint32(GarrisonType::GARRISON_TYPE_CLASS_HALL);
    result.GarrTalentID = researchTalent.GarrTalentID;
    result.StartTime = uint32(2254525440);
    result.Unk1 = uint32(0);
    SendPacket(result.Write());
}

void WorldSession::HandleGarrisonRequestClassSpecCategoryInfo(WorldPackets::Garrison::GarrisonRequestClassSpecCategoryInfo& requestClassSpecCategoryInfo)
{
    WorldPackets::Garrison::GarrisonFollowerCategories result;
    result.GarrFollowerTypeId = requestClassSpecCategoryInfo.GarrFollowerTypeId;
    result.CategoryInfoCount = 0;

    SendPacket(result.Write());
}

void WorldSession::HandleGarrisonCreateShipmentOpcode(WorldPackets::Garrison::GarrisonCreateShipment& request)
{
    if (!_player)
        return;
    Creature* unit = _player->GetNPCIfCanInteractWith(request.NpcGUID, UNIT_NPC_FLAG_SHIPMENT_CRAFTER);
    if (!unit || !_player->IsInGarrison())
        return;

    for (uint32 i = 0; i < sCharShipmentStore.GetNumRows(); ++i)
    {
        CharShipmentEntry const* shipment = sCharShipmentStore.LookupEntry(i);
        if (!shipment || shipment->ShipmentContainerID != unit->GetShipmentContainerID())
            continue;
        CharShipmentContainerEntry const* container = sCharShipmentContainerStore.LookupEntry(shipment->ShipmentContainerID);
        if (!container)
            return;
        Garrison* garrison = _player->GetGarrison(GarrisonType(container->GarrTypeID));
        if (!garrison)
            return;
        uint32 const plotId = garrison->GetClassHallPlotId(unit->GetEntry());
        SpellInfo const* spell = sSpellMgr->GetSpellInfo(shipment->SpellID);
        if (!plotId || !spell)
            return;

        uint32 const pending = garrison->GetWorkOrderCount(plotId);
        if (pending >= shipment->MaxShipments)
            return;
        // Enforce the same queue capacity advertised in the shipment info packet.
        uint32 const count = std::min<uint32>(request.Count ? request.Count : 1, shipment->MaxShipments - pending);
        for (uint32 n = 0; n < count; ++n)
        {
            uint64 const databaseId = garrison->StartWorkOrder(plotId, shipment->ID);
            if (!databaseId)
                return;
            _player->CastSpell(_player, spell, TRIGGERED_FULL_MASK);
            WorldPackets::Garrison::GarrisonCreateShipmentResponse result;
            result.ShipmentID = databaseId;
            result.ShipmentRecID = shipment->ID;
            result.Result = 1;
            SendPacket(result.Write());
        }
        return;
    }
}
