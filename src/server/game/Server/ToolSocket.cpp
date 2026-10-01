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
#include "PlayerGameplayUtility.h"
#include "Map.h"
#include "ToolSocket.h"
#include "BigNumber.h"
#include "Opcodes.h"
#include "SharedDefines.h"
#include "World.h"
#include "AccountMgr.h"
#include "OnlineMgr.h"
#include "ToolSocketMgr.h"
#include "Config.h"
#include "AccountMgr.h"


#include <memory>
#include <cmath>
#include <limits>
#include <fstream>
#include <boost/algorithm/string.hpp>

using boost::asio::ip::tcp;

ToolSocket* ToolSocket::g_Tool = NULL;
std::mutex ToolSocket::_commandLock;

ToolSocket::ToolSocket(tcp::socket&& socket)
	: Socket(std::move(socket)), _authed(false)
{
}

ToolSocket::~ToolSocket()
{
	if (this == ToolSocket::g_Tool)
	{
		ToolSocket::g_Tool = NULL;
		TC_LOG_ERROR("ToolSocket", "Release tool socket, set g_Tool to null.");
	}
}

void ToolSocket::Start()
{
	std::string ip_address = GetRemoteIpAddress().to_string();
    LoginDatabasePreparedStatement* stmt = LoginDatabase.GetPreparedStatement(LOGIN_SEL_TOOL_IPBIND);
	stmt->setString(0, ip_address);

	PreparedQueryResult result = LoginDatabase.Query(stmt);
	if (result && (ToolSocket::g_Tool == NULL))
	{
		ToolSocket::g_Tool = this;
		_authed = true;
		LoadConfigure();
		AsyncRead();
	}
	else
	{
	 
		DelayedCloseSocket();
		return;
	}
}

bool ToolSocket::Update()
{
	{
        std::unique_lock<std::mutex> sessionGuard(_commandLock);
		while (_bufferQueue.size())
		{
            QueuePacket(std::move(_bufferQueue.front()));
            _bufferQueue.pop();
		}
	}

	if (!BaseSocket::Update())
		return false;

	return true;
}

namespace
{
bool IsValidToolCommand(Json::Value const& info)
{
    if (info.type() != Json::objectValue || !info["entry"].isString())
        return false;
    auto integer = [&info](char const* key, int minimum, int maximum)
    {
        Json::Value const& value = info[key];
        if (!value.isInt() && !value.isUInt())
            return false;
        // This bundled JsonCpp version throws at UINT >= INT_MAX in asInt().
        double number = value.asDouble();
        return number >= minimum && number <= maximum &&
            (!value.isUInt() || number < std::numeric_limits<int>::max());
    };
    auto number = [&info](char const* key)
    {
        Json::Value const& value = info[key];
        return (value.isInt() || value.isUInt() || value.isDouble()) && std::isfinite(value.asDouble());
    };
    std::string const entry = info["entry"].asString();
    if (entry == "heartbeat")
        return true;
    if (entry == "player_acc")
    {
        Json::Value const& after = info["after"];
        // This bundled JsonCpp parses values near UINT_MAX as doubles.
        bool const validCursor = after.isNull() || after.isUInt() ||
            (after.isInt() && after.asInt() >= 0) ||
            (after.isDouble() && std::isfinite(after.asDouble()) && after.asDouble() >= 0 &&
                after.asDouble() <= std::numeric_limits<uint32>::max() &&
                std::floor(after.asDouble()) == after.asDouble());
        return validCursor && (info["limit"].isNull() || integer("limit", 1, 100));
    }
    if (entry == "player_change_status")
        return integer("guid", 1, std::numeric_limits<int>::max());
    if (entry == "player_specialization")
        return integer("guid", 1, std::numeric_limits<int>::max()) &&
            (integer("talent", 0, MAX_SPECIALIZATIONS - 1) ||
                integer("talent", PLAYER_SPECIALIZATION_KEEP, PLAYER_SPECIALIZATION_KEEP));
    if (entry == "authorization")
        return info["authorization"].isString();
    if (entry == "create_acc")
        return info["cmdName"].isString() && info["cmdPass"].isString();
    if (entry == "xp_reward")
        return info["reward"].isBool() || integer("reward", 0, 1);
    if (entry == "bg_scorerate")
        return number("scorerate");
    if (entry == "set_security")
        return integer("accid", 1, std::numeric_limits<int>::max()) && integer("security", 0, 4);
    if (entry == "player_change")
        return integer("guid", 1, std::numeric_limits<int>::max()) && integer("minlv", 20, 110) &&
            integer("maxlv", 20, 110) && info["maxlv"].asInt() >= info["minlv"].asInt() &&
            (info["talent"].isNull() || integer("talent", 0, MAX_SPECIALIZATIONS - 1) ||
                integer("talent", PLAYER_SPECIALIZATION_KEEP, PLAYER_SPECIALIZATION_KEEP));
    if (entry == "pve_maxlevel")
        return integer("max_level", 0, 6);
    if (entry == "pve_maxdungeon")
        return integer("maxdungeon", 0, std::numeric_limits<int>::max());
    if (entry == "pve_addion")
        return number("addion") && number("endure");
    return false;
}
}

void ToolSocket::ProcessToolCmd()
{
    std::unique_lock<std::mutex> sessionGuard(_commandLock);
	while (_processCmd.size())
	{
        Json::Value jsonCmd = _processCmd.front();
        _processCmd.pop();
        std::string entry = "invalid_command";
        try
        {
            if (jsonCmd.type() == Json::objectValue && jsonCmd["entry"].isString())
                entry = jsonCmd["entry"].asString();
            if (!IsValidToolCommand(jsonCmd))
            {
                SendNormalResult(entry, false);
                continue;
            }
            if (entry == "heartbeat")
                CmdHeartbeat(jsonCmd);
            else if (entry == "authorization")
                CmdAuthorization(jsonCmd);
            else if (entry == "xp_reward")
                CmdBGXPReward(jsonCmd);
            else if (entry == "bg_scorerate")
                CmdBGScoreRate(jsonCmd);
            else if (entry == "create_acc")
                CmdCreateAccount(jsonCmd);
            else if (entry == "player_acc")
                CmdPlayerAccount(jsonCmd);
            else if (entry == "set_security")
                CmdAccountSecurity(jsonCmd);
            else if (entry == "player_change")
                CmdPlayerChange(jsonCmd);
            else if (entry == "player_specialization")
                CmdPlayerSpecialization(jsonCmd);
            else if (entry == "player_change_status")
                CmdPlayerChangeStatus(jsonCmd);
            else if (entry == "pve_maxlevel")
                CmdPVEMaxLevel(jsonCmd);
            else if (entry == "pve_maxdungeon")
                CmdPVEMaxDungeon(jsonCmd);
            else if (entry == "pve_addion")
                CmdPVEAddion(jsonCmd);
            else
            {
                TC_LOG_ERROR("ToolSocket", "Can`t find tool opcode case by entry : %s.", entry.c_str());
                SendNormalResult(entry, false);
            }
        }
        catch (std::exception const&)
        {
            TC_LOG_ERROR("ToolSocket", "Rejected invalid tool command");
            SendNormalResult(entry, false);
        }
	}
}

void ToolSocket::OnClose()
{
}

void ToolSocket::ReadHandler()
{
    if (!IsOpen() || !_authed)
        return;
    MessageBuffer& packet = GetReadBuffer();
    while (packet.GetActiveSize() >= sizeof(uint16))
    {
        uint16 size = 0;
        memcpy(&size, packet.GetReadPointer(), sizeof(size));
        if (size > 1024)
        {
            _authed = false;
            DelayedCloseSocket();
            return;
        }
        if (packet.GetActiveSize() < sizeof(size) + size)
            break; // Leave the header and partial payload for the next TCP read.
        packet.ReadCompleted(sizeof(size));
        if (!size)
            continue;
        std::string command(reinterpret_cast<char const*>(packet.GetReadPointer()), size);
        packet.ReadCompleted(size);
        if (!command.empty() && command.back() == '\0')
            command.pop_back(); // Legacy clients include a trailing NUL in their frame size.
        if (command.find('\0') != std::string::npos)
        {
            _authed = false;
            DelayedCloseSocket();
            return;
        }
        ProcessCmd(std::move(command));
    }
    AsyncRead();
}

void ToolSocket::LoadConfigure()
{
#ifdef INCOMPLETE_BOT
	return;
#endif
/*	std::fstream _file;
	_file.open("pve.cfg", std::ios::in);
	if (!_file)
		return;
	FILE* pFile = fopen("pve.cfg", "r");
	if (!pFile)
		return;
	fseek(pFile, 0, SEEK_END);
	int size = ftell(pFile);
	if (size <= 0)
	{
		fclose(pFile);
		return;
	}
	char* infos = new char[size + 1];
	memset(infos, 0, size + 1);
	fseek(pFile, 0, SEEK_SET);
	fread(infos, size, 1, pFile);
	fclose(pFile);

	std::string cfgString(infos);
*/
	Json::Reader jsonReader;
	Json::Value jsonValue;
	/*if (!jsonReader.parse(cfgString, jsonValue))
	{
		TC_LOG_ERROR("ToolSocket", "Parse configure string error. text is %s", cfgString.c_str());
		return;
	}*/
	TC_LOG_ERROR("ToolSocket", "load Gtools\n");
	Json::Value jsonScoreRate = sConfigMgr->GetFloatDefault("bgscorerate", 1.0f);

		float bgScoreReate =  sConfigMgr->GetFloatDefault("bgscorerate", 1.0f);
		if (bgScoreReate < 0.2f)
			bgScoreReate = 0.2f;
		if (bgScoreReate > 8.0f)
			bgScoreReate = 8.0f;
        PlayerGameplayUtility::BattlegroundScoreRate = bgScoreReate;

Json::Value jsonMaxLevel = sConfigMgr->GetIntDefault("max_level", 6);
		int maxLevel = sConfigMgr->GetIntDefault("max_level", 6);
		if (maxLevel >= 0 && maxLevel < 7)
		{
			uint32 realLevel = 110;
			switch (maxLevel)
			{
			case 0:
				realLevel = 60;
				break;
			case 1:
				realLevel = 70;
				break;
			case 2:
				realLevel = 80;
				break;
			case 3:
				realLevel = 85;
				break;
			case 4:
				realLevel = 90;
				break;
			case 5:
				realLevel = 100;
				break;
			case 6:
				realLevel = 110;
				break;
			}
			sWorld->setIntConfig(CONFIG_MAX_PLAYER_LEVEL, realLevel);
		}

Json::Value jsonMaxDungeon = sConfigMgr->GetIntDefault("maxdungeon", 0);
		int maxDungeon = sConfigMgr->GetIntDefault("maxdungeon", 0);
        InstanceMap::AllowFortyPlayers = (maxDungeon != 0) ? true : false;

Json::Value jsonAddion = sConfigMgr->GetFloatDefault("addion", 1.0f);
		float modifyAddion = sConfigMgr->GetFloatDefault("addion", 1.0f);
		if (modifyAddion < 0.5f)
			modifyAddion = 0.5f;
		if (modifyAddion > 15.0f)
			modifyAddion = 15.0f;
        PlayerGameplayUtility::DungeonPlayerDamageMultiplier = modifyAddion;

Json::Value jsonEndure = sConfigMgr->GetFloatDefault("endure", 1.0f);
		modifyAddion = sConfigMgr->GetFloatDefault("endure", 1.0f);
		if (modifyAddion < 0.5f)
			modifyAddion = 0.5f;
		if (modifyAddion > 15.0f)
			modifyAddion = 15.0f;
        PlayerGameplayUtility::DungeonPlayerDamageDivisor = modifyAddion;
}

void ToolSocket::ProcessCmd(std::string cmdString)
{
	Json::Reader jsonReader;
	Json::Value jsonValue;
	if (!jsonReader.parse(cmdString, jsonValue))
	{
        TC_LOG_ERROR("ToolSocket", "Invalid JSON in tool command");
		return;
	}
    std::unique_lock<std::mutex> sessionGuard(_commandLock);
	_processCmd.push(jsonValue);
	//std::unique_lock<std::mutex> sessionGuard(_consoleLock, std::defer_lock);
	//sessionGuard.lock();
	//sWorld->QueueCliCommand(new CliCommandHolder(this, cmdString.c_str(), &CommandPrint, &CommandFinished));
}

//void ToolSocket::CommandPrint(void* callbackArg, const char* text)
//{
//	TC_LOG_ERROR("ToolSocket", "Process command result %s", text);
//}
//
//void ToolSocket::CommandFinished(void* callbackArg, bool success)
//{
//	std::string text = success ? "success" : "error";
//	uint16 size = text.size() + 1;
//	MessageBuffer* retMsg = new MessageBuffer(2 + size);
//	retMsg->Write(&size, 2);
//	retMsg->Write(text.c_str(), size);
//	retMsg->WriteCompleted(2 + size);
//	((ToolSocket*)callbackArg)->SendPacket(retMsg);
//}

void ToolSocket::SendNormalResult(std::string entry, bool result)
{
	Json::Value test;
	test["entry"] = entry;
	test["result"] = result ? "success" : "error";
	SendResult(test.toStyledString());
}

void ToolSocket::SendResult(std::string result)
{
    if (result.empty() || !IsOpen())
        return;
    if (result.size() >= std::numeric_limits<uint16>::max())
    {
        TC_LOG_ERROR("ToolSocket", "Tool response exceeds the 16-bit protocol length");
        DelayedCloseSocket();
        return;
    }
    uint16 size = static_cast<uint16>(result.size() + 1);
    MessageBuffer message(sizeof(size) + size);
    message.Write(&size, sizeof(size));
    message.Write(result.c_str(), size); // Write already advances the buffer position.
    SendPacket(std::move(message));
}

void ToolSocket::SendPacket(MessageBuffer&& packet)
{
    if (IsOpen())
        _bufferQueue.push(std::move(packet));
}

void ToolSocket::CmdHeartbeat(Json::Value& info)
{
	SendNormalResult("heartbeat", true);
}

void ToolSocket::CmdAuthorization(Json::Value& info)
{
	std::string authorization = info["authorization"].asString();
	SendNormalResult("authorization", authorization.empty());
}

void ToolSocket::CmdBGXPReward(Json::Value& info)
{
	bool can = info["reward"].asBool();
	sWorld->setBoolConfig(CONFIG_BG_XP_FOR_KILL, can);
	SendNormalResult("xp_reward", true);
}

void ToolSocket::CmdBGScoreRate(Json::Value& info)
{
	float rate = info["scorerate"].asDouble();
	if (rate < 0.2f)
		rate = 0.2f;
	if (rate > 8.0f)
		rate = 8.0f;
    PlayerGameplayUtility::BattlegroundScoreRate = rate;
	SendNormalResult("bg_scorerate", true);
}

void ToolSocket::CmdCreateAccount(Json::Value& info)
{
	std::string name = info["cmdName"].asString();
	std::string pass = info["cmdPass"].asString();
    bool isBotAcc = OnlineMgr::IsLegacyBotAccountName(name);
	if (isBotAcc || name.empty() || pass.empty())
	{
		Json::Value test;
		test["entry"] = "create_acc";
		test["result"] = "error";
		SendResult(test.toStyledString());
		return;
	}

	bool createResult = false;
	createResult = sAccountMgr->CreateAccount(name, pass, "") == AccountOpResult::AOR_OK;
	if (createResult)
	{
        Utf8ToUpperOnlyLatin(name);
        sOnlineMgr->AddNewAccount(AccountMgr::GetId(name), name);
	}
	SendNormalResult("create_acc", createResult);
}

void ToolSocket::CmdPlayerAccount(Json::Value& info)
{
    uint32 after = info["after"].isNull() ? 0 : info["after"].asUInt();
    uint32 limit = info["limit"].isNull() ? 99 : info["limit"].asUInt();
    SendResult(sOnlineMgr->SerializerPlayerAccount(after, limit));
}

void ToolSocket::CmdAccountSecurity(Json::Value& info)
{
	int accID = info["accid"].asInt();
	int secu = info["security"].asInt();
	bool succ = sOnlineMgr->SetAccountSecurity(accID, secu);
	SendNormalResult("set_security", succ);
}

void ToolSocket::CmdPlayerChange(Json::Value& info)
{
	uint32 guid = info["guid"].asInt();
	uint32 minlv = info["minlv"].asInt();
	uint32 maxlv = info["maxlv"].asInt();
	uint32 talent = info["talent"].asInt();
    if (minlv < 20 || minlv > 110 || maxlv < minlv || maxlv < 20 || maxlv > 110 ||
        (talent >= MAX_SPECIALIZATIONS && talent != PLAYER_SPECIALIZATION_KEEP))
	{
		SendNormalResult("player_change", false);
		return;
	}
    minlv = PlayerCharacterSetup::CheckMaxLevel(minlv);
	WorldSession* pWorldSession = sWorld->FindSession(guid);
	if (pWorldSession && !pWorldSession->PlayerLoading())
	{
		Player* player = pWorldSession->GetPlayer();
        if (!player || !player->IsAlive() || player->IsInFlight() || player->IsBeingTeleported() ||
            player->GetTradeData() || player->InBattlegroundQueue() || player->InBattleground() ||
			player->GetBattleground() || player->IsInCombat())
		{
			SendNormalResult("player_change", false);
			return;
		}
        maxlv = PlayerCharacterSetup::CheckMaxLevel(maxlv);
		if (maxlv < minlv)
			maxlv = minlv;
		uint32 level = urand(minlv, maxlv);
        bool result = player->ResetPlayerToLevel(level, talent);
        if (result)
            sOnlineMgr->SetCharacterOperation(guid, uint32(player->GetGUID()), "preparation", "queued", 0);
        SendNormalResult("player_change", result);
		return;
	}
	SendNormalResult("player_change", false);
}

void ToolSocket::CmdPlayerSpecialization(Json::Value& info)
{
    uint32 const account = info["guid"].asInt();
    WorldSession* session = sWorld->FindSession(account);
    Player* player = session && !session->PlayerLoading() ? session->GetPlayer() : nullptr;
    if (!player || !player->IsAlive() || player->getLevel() < 10 || player->IsInCombat() ||
        player->IsInFlight() || player->IsBeingTeleported() || player->GetTradeData() ||
        player->InBattlegroundQueue() || player->InBattleground() || player->GetBattleground() ||
        player->m_CharacterSetup->HasPendingReset())
    {
        SendNormalResult("player_specialization", false);
        return;
    }
    sOnlineMgr->SetCharacterOperation(account, uint32(player->GetGUID()), "specialization", "running", 0);
    bool success = player->ChangeToolSpecialization(info["talent"].asInt());
    sOnlineMgr->SetCharacterOperation(account, uint32(player->GetGUID()), "specialization",
        success ? "completed" : "rejected", 0);
    SendNormalResult("player_specialization", success);
}

void ToolSocket::CmdPlayerChangeStatus(Json::Value& info)
{
    SendResult(sOnlineMgr->SerializerCharacterOperation(info["guid"].asInt()));
}

void ToolSocket::CmdPVEMaxLevel(Json::Value& info)
{
	uint32 max_level = info["max_level"].asInt();
	if (max_level > 6)
	{
		SendNormalResult("pve_maxlevel", false);
		return;
	}
    uint32 realLevel = 110;
	switch (max_level)
	{
	case 0:
        realLevel = 60;
		break;
	case 1:
        realLevel = 70;
		break;
	case 2:
		realLevel = 80;
		break;
	case 3:
		realLevel = 85;
		break;
    case 4:
        realLevel = 90;
        break;
    case 5:
        realLevel = 100;
        break;
    case 6:
        realLevel = 110;
        break;
	}
	sWorld->setIntConfig(CONFIG_MAX_PLAYER_LEVEL, realLevel);
	SendNormalResult("pve_maxlevel", true);
}

void ToolSocket::CmdPVEMaxDungeon(Json::Value& info)
{
	uint32 max = info["maxdungeon"].asInt();
    InstanceMap::AllowFortyPlayers = (max != 0) ? true : false;
	SendNormalResult("pve_maxdungeon", true);
}

void ToolSocket::CmdPVEAddion(Json::Value& info)
{
	float modifyAddion = (float)info["addion"].asDouble();
	float modifyEndure = (float)info["endure"].asDouble();
	if (modifyAddion < 0.5f)
		modifyAddion = 0.5f;
	if (modifyAddion > 15.0f)
		modifyAddion = 15.0f;
	if (modifyEndure < 0.5f)
		modifyEndure = 0.5f;
	if (modifyEndure > 15.0f)
		modifyEndure = 15.0f;
    PlayerGameplayUtility::DungeonPlayerDamageMultiplier = modifyAddion;
    PlayerGameplayUtility::DungeonPlayerDamageDivisor = modifyEndure;
	SendNormalResult("pve_addion", true);
}
