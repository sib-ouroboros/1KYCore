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

#include "PlayerBotSession.h"
#include "Player.h"
#include "BattlegroundMgr.h"
#include "LFGMgr.h"
#include "CharacterPackets.h"
#include "MovementPackets.h"
#include "DB2Structure.h"
#include "LFGPackets.h"
#include "LFGPacketsCommon.h"
#include "PetitionPackets.h"

PlayerBotSession::PlayerBotSession(uint32 id, std::string& name, uint32 battlenetAccountId, AccountTypes sec, uint8 expansion, time_t mute_time, LocaleConstant locale, uint32 recruiter, bool isARecruiter, std::string&& battlenetAccountName) :
m_LastCastTime(CAST_SCHEDULE_TICK),
m_NoWorldTick(0),
m_AccountBot(false),

WorldSession(id, std::string(name), battlenetAccountId, nullptr, SEC_PLAYER, 6, 0, "Wn64", LOCALE_deDE, 0, false, std::string(battlenetAccountName))
{
    SetAddress("DestinyCore");
}

bool PlayerBotSession::IsBotSession()
{
	return true;
}

bool PlayerBotSession::Update(uint32 diff, PacketFilter& updater)
{
	bool updateResult = WorldSession::Update(diff, updater);
	ProcessNoWorld(diff);
	m_LastCastTime -= diff;
	if (m_LastCastTime <= 0)
	{
		//std::lock_guard<std::mutex> lock(m_optQueueLock);
		CastSchedule(CAST_SCHEDULE_TICK);
		m_LastCastTime = CAST_SCHEDULE_TICK;
	}
	return updateResult;
}

void PlayerBotSession::PushScheduleToQueue(BotGlobleSchedule& schedule)
{
	//std::lock_guard<std::mutex> lock(m_optQueueLock);
	for (BotSchedules::iterator itSc = m_Schedules.begin(); itSc != m_Schedules.end(); itSc++)
	{
		if ((*itSc).bbgType == schedule.bbgType)
			return;
	}

	m_Schedules.push_back(schedule);
}

void PlayerBotSession::RemoveScheduleByType(BotGlobleScheduleType eType)
{
	for (BotSchedules::iterator itSc = m_Schedules.begin(); itSc != m_Schedules.end(); itSc++)
	{
		if ((*itSc).bbgType == eType)
		{
			m_Schedules.erase(itSc);
			return;
		}
	}
}

bool PlayerBotSession::HasScheduleByType(BotGlobleScheduleType eType)
{
	for (BotSchedules::iterator itSc = m_Schedules.begin(); itSc != m_Schedules.end(); itSc++)
	{
		if ((*itSc).bbgType == eType)
		{
			return true;
		}
	}
	return false;
}

bool PlayerBotSession::HasSchedules()
{
	return m_Schedules.size() > 0;
}

bool PlayerBotSession::IsAccountBotSession()
{
	return m_AccountBot;
}

bool PlayerBotSession::PlayerIsReady()
{
	Player* player = GetPlayer();
	if (!player)
		return true;
	if (!player->IsSettingFinish())
		return false;

	return true;
}

void PlayerBotSession::ProcessNoWorld(uint32 diff)
{
    if (PlayerLoading())
        return;
    Player* player = GetPlayer();
    if (!player)
        return;

    // Un client reel confirme le changement de monde par MSG_MOVE_WORLDPORT_ACK ;
    // sans cette simulation, un bot en jeu vise par .tele reste bloque sur le semaphore.
    if (player->IsBeingTeleportedFar())
    {
        HandleMoveWorldportAck();
        m_NoWorldTick = 500;
        return;
    }

    // idem pour un teleport proche (meme map) : un client reel repond CMSG_MOVE_TELEPORT_ACK
    if (player->IsBeingTeleportedNear())
    {
        WorldPacket data(CMSG_MOVE_TELEPORT_ACK);
        WorldPackets::Movement::MoveTeleportAck ack(std::move(data));
        ack.MoverGUID = player->GetGUID();
        HandleMoveTeleportAck(ack);
        m_NoWorldTick = 500;
        return;
    }

    if (player->IsInWorld())
    {
        m_NoWorldTick = 0;
        return;
    }

    if (m_NoWorldTick == 0)
    {
        m_NoWorldTick = 2000;
        return;
    }
    m_NoWorldTick -= int32(diff);
    if (m_NoWorldTick > 0)
        return;

    HandleMoveWorldportAck();
    m_NoWorldTick = 500;
}

void PlayerBotSession::CastSchedule(uint32 diff)
{
	if (m_Schedules.empty())
		return;
	bool result = false;
	BotGlobleSchedule& schedule = *m_Schedules.begin();
	schedule.processTick += diff;
	if (schedule.processTick > 60000 * 3)
	{
		m_Schedules.erase(m_Schedules.begin());
		return;
	}
	if (!PlayerIsReady())
		return;
	switch (schedule.bbgType)
	{
	case BGSType_Online:
		result = ProcessOnline(schedule);
		break;
	case BGSType_Online_GUID:
		result = ProcessOnlineByGUID(schedule);
		TC_LOG_ERROR("server.worldserver", "QA-BOTLOG: ProcessOnlineByGUID resultat=%d", (int)result); // QA-BOTLOG
		break;
	case BGSType_Offline:
		result = ProcessOffline(schedule);
		break;
	case BGSType_Settting:
		result = ProcessSetting(schedule);
		break;
	case BGSType_OfferPetitionSign:
		result = ProcessOfferPetitionSign(schedule);
		break;
	default:
		result = true;
		break;
	}
	if (result)
	{
		m_Schedules.erase(m_Schedules.begin());
	}
}

bool PlayerBotSession::ProcessOnline(BotGlobleSchedule& schedule)
{
    if (schedule.parameter1 <= 0)
        return true;
    if (PlayerLoading())
        return false;
    if (GetPlayer())
        return true;
    PlayerBotBaseInfo* pInfo = sPlayerBotMgr->GetPlayerBotAccountInfo(GetAccountId());
    if (!pInfo)
    {
        pInfo = sPlayerBotMgr->GetAccountBotAccountInfo(GetAccountId());
        if (!pInfo)
        {
            ClearAllSchedule();
            return false;
        }
    }

    bool fuction = true;
    if (schedule.parameter1 > 1)
        fuction = false;
    PlayerBotCharBaseInfo& charInfo = (schedule.parameter2 == 0) ? pInfo->GetRandomCharacterByFuction(fuction) : pInfo->GetCharacter(fuction, schedule.parameter2);
    if (charInfo.guid == 0)
        return true;

    WorldPacket _worldPacket(CMSG_PLAYER_LOGIN);
    WorldPackets::Character::PlayerLogin cmd(std::move(_worldPacket));
    cmd.Guid = ObjectGuid::Create<HighGuid::Player>(charInfo.guid);
    cmd.FarClip = 0.0f;
    HandlePlayerLoginOpcode(cmd);
    HandleContinuePlayerLogin();
    return false;
}

bool PlayerBotSession::ProcessOnlineByGUID(BotGlobleSchedule& schedule)
{
    if (schedule.playerGUID <= 0)
        return true;
    if (PlayerLoading())
        return false;
    if (GetPlayer())
        return true;

    WorldPacket _worldPacket(CMSG_PLAYER_LOGIN);
    WorldPackets::Character::PlayerLogin cmd(std::move(_worldPacket));
    cmd.Guid = schedule.playerGUID;
    cmd.FarClip = 0.0f;
    HandlePlayerLoginOpcode(cmd);
	HandleContinuePlayerLogin();
	return false;
}

bool PlayerBotSession::ProcessOffline(BotGlobleSchedule& schedule)
{
	if (PlayerLoading())
		return false;
	Player* player = GetPlayer();
	if (!player)
		return true;
	if (schedule.scheduleState > 0)
		return false;
    WorldPackets::Character::LogoutRequest logoutReq(time(NULL) - 18);
	//LogoutPlayer(false);
	schedule.scheduleState = 1;
	return false;
}

bool PlayerBotSession::ProcessSetting(BotGlobleSchedule& schedule)
{
	if (schedule.parameter3 == 0 || schedule.parameter3 > 4)
		schedule.parameter3 = 4;
    if (schedule.parameter2 > 110 || schedule.parameter2 == 0)
        schedule.parameter2 = 110;
	if (schedule.parameter1 > schedule.parameter2)
		schedule.parameter2 = schedule.parameter1;
	if (PlayerLoading())
		return false;
	Player* player = GetPlayer();
	if (!player)
	{
		ClearAllSchedule();
		return false;
	}
	if (!player->IsInWorld() || !player->IsSettingFinish())
		return false;
	if (schedule.scheduleState != 0)
		return true;
	bool needTenacity = (schedule.parameter4 != 0) ? true : false;
	if (needTenacity)
		needTenacity = player->CheckNeedTenacityFlush();
	if (!needTenacity && player->CalculateTalentsTiers() < 10)
	{
		if (player->IsSettingFinish() && player->getLevel() >= schedule.parameter1 && player->getLevel() <= schedule.parameter2)
		{
			// SylvaniaCore : le raccourci ne vaut que si le bot a reellement ses
			// talents. Sans ce controle, un bot deja au bon niveau et a la bonne
			// specialisation sautait tout le re-level et restait avec zero talent,
			// heritage de l epoque ou LearnTalents() etait un corps vide.
			PlayerTalentMap const* talents = player->GetTalentMap(player->GetActiveTalentGroup());
			bool const hasTalents = talents && talents->size() >= player->CalculateTalentsTiers();

			// SIGNALE EN JEU : « Kaerbrus n a meme pas d equipement ».
			// Constate en base : niveau 110, 76 sorts, ZERO piece portee.
			//
			// Ce raccourci evite un re-level complet a un bot deja au bon
			// niveau, avec ses talents et la bonne specialisation. Mais il
			// saute du meme coup les etapes 6 a 10 de UpdateReset(), qui sont
			// justement l habillage. Un mercenaire ayant perdu son equipement
			// -- contrat precedent interrompu, re-level avorte -- ne le
			// retrouvait donc JAMAIS : a chaque embauche, le raccourci
			// concluait que tout allait bien et le renvoyait nu.
			//
			// On verifie donc qu il est reellement habille avant de couper.
			// Dix pieces sur les dix-neuf emplacements : de quoi distinguer un
			// bot equipe d un bot depouille, sans exiger un sans-faute (la
			// seconde babiole et l arme de jet manquent souvent, legitimement).
			uint32 piecesPortees = 0;
			for (uint8 emplacement = EQUIPMENT_SLOT_START; emplacement < EQUIPMENT_SLOT_END; ++emplacement)
				if (player->GetItemByPos(INVENTORY_SLOT_BAG_0, emplacement))
					++piecesPortees;
			bool const correctementEquipe = (piecesPortees >= 10);

			if (hasTalents && correctementEquipe &&
				(schedule.parameter3 >= 4 || (player->FindTalentType() + 1 == schedule.parameter3)))
				return true;
		}
	}

	uint32 flushTalent = (schedule.parameter3 > 0 && schedule.parameter3 < 4) ? schedule.parameter3 - 1 : 3;
	player->ResetPlayerToLevel(schedule.parameter2, flushTalent, needTenacity);
	schedule.scheduleState = 1;
	return false;
}

bool PlayerBotSession::ProcessOfferPetitionSign(BotGlobleSchedule& schedule)
{
	if (PlayerLoading())
		return false;
	if (schedule.parameter1 == 0 && schedule.parameter2 == 0)
		return true;
	Player* player = GetPlayer();
	if (!player)
	{
		ClearAllSchedule();
		return false;
	}

	uint64 signGUID = uint64(schedule.parameter1);
	uint64 highID = uint64(schedule.parameter2) << 32;
	signGUID |= highID;

    WorldPacket packet(CMSG_SIGN_PETITION, 0);
    packet << signGUID;
    packet << uint8(1);
    WorldPackets::Petition::SignPetition signPacket(std::move(packet));
    HandleSignPetition(signPacket);
	return true;
}
