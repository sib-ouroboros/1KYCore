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
#include "BotAITool.h"
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
			MessageBuffer* buffer = _bufferQueue.front();
			QueuePacket(std::move(*buffer));
			_bufferQueue.pop();
			delete buffer;
		}
	}

	if (!BaseSocket::Update())
		return false;

	return true;
}

void ToolSocket::ProcessToolCmd()
{
    std::unique_lock<std::mutex> sessionGuard(_commandLock);
	while (_processCmd.size())
	{
		Json::Value& jsonCmd = _processCmd.front();
		std::string entry = jsonCmd["entry"].asString();
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
		_processCmd.pop();
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
	while (packet.GetActiveSize() > 0)
	{
		uint16 size = 0;
		std::size_t readHeaderSize = 2;
		memcpy((void*)&size, packet.GetReadPointer(), readHeaderSize);
		packet.ReadCompleted(readHeaderSize);

		if (size > 0 && size <= 1024 && packet.GetRemainingSpace() >= size)
		{
			char* data = new char[size];
			memcpy(data, packet.GetReadPointer(), size);
			packet.ReadCompleted(size);
			ProcessCmd(data);
		}
		else if (size != 0)
		{
			_authed = false;
			DelayedCloseSocket();
			return;
		}
		else
		{
			packet.ReadCompleted(packet.GetActiveSize());
			break;
		}
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
		BotUtility::BattlegroundScoreRate = bgScoreReate;

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
		BotUtility::DungeonBotDamageModify = modifyAddion;

Json::Value jsonEndure = sConfigMgr->GetFloatDefault("endure", 1.0f);
		modifyAddion = sConfigMgr->GetFloatDefault("endure", 1.0f);
		if (modifyAddion < 0.5f)
			modifyAddion = 0.5f;
		if (modifyAddion > 15.0f)
			modifyAddion = 15.0f;
		BotUtility::DungeonBotEndureModify = modifyAddion;
}

void ToolSocket::ProcessCmd(std::string cmdString)
{
	Json::Reader jsonReader;
	Json::Value jsonValue;
	if (!jsonReader.parse(cmdString, jsonValue))
	{
		TC_LOG_ERROR("ToolSocket", "Parse tool string error. text is %s", cmdString.c_str());
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
	uint16 size = result.size() + 1;
	MessageBuffer* retMsg = new MessageBuffer(2 + size);
	retMsg->Write(&size, 2);
	retMsg->Write(result.c_str(), size);
	retMsg->WriteCompleted(2 + size);
	SendPacket(retMsg);
}

void ToolSocket::SendPacket(MessageBuffer* packet)
{
	if (!IsOpen())
		return;

	_bufferQueue.push(packet);
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
	BotUtility::BattlegroundScoreRate = rate;
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
	SendResult(sOnlineMgr->SerializerPlayerAccount());
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
	if (minlv < 20 || minlv > 110 || maxlv < minlv || maxlv < 20 || maxlv > 110 || talent > 2)
	{
		SendNormalResult("player_change", false);
		return;
	}
	minlv = PlayerBotSetting::CheckMaxLevel(minlv);
	WorldSession* pWorldSession = sWorld->FindSession(guid);
	if (pWorldSession && !pWorldSession->PlayerLoading())
	{
		Player* player = pWorldSession->GetPlayer();
		if (!player || player->InBattlegroundQueue() || player->InBattleground() ||
			player->GetBattleground() || player->IsInCombat())
		{
			SendNormalResult("player_change", false);
			return;
		}
		maxlv = PlayerBotSetting::CheckMaxLevel(maxlv);
		if (maxlv < minlv)
			maxlv = minlv;
		uint32 level = urand(minlv, maxlv);
		bool result = player->ResetPlayerToLevel(level, talent);
		SendNormalResult("player_change", result);
		return;
	}
	SendNormalResult("player_change", false);
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
	BotUtility::DungeonBotDamageModify = modifyAddion;
	BotUtility::DungeonBotEndureModify = modifyEndure;
	SendNormalResult("pve_addion", true);
}
