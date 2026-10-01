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

#include "Timer.h"
#include "OnlineMgr.h"
#include "World.h"
#include "WorldSession.h"

#include <boost/algorithm/string.hpp>
#include <cstdlib>

std::mutex OnlineMgr::g_uniqueMgrLock;

Json::Value ToolCharaterInfo::SerializerInfo()
{
	Json::Value result;
	if (guid != 0)
	{
		result["guid"] = guid;
		result["name"] = name;
		result["race"] = race;
		result["profession"] = profession;
		result["level"] = level;
		result["talent"] = talent;
	}
	else
	{
		result["guid"] = 0;
	}
	return result;
}

Json::Value ToolAccountInfo::SerializerInfo()
{
	WorldSession* pSession = sWorld->FindSession(id);
	Json::Value result;
	result["id"] = id;
	result["name"] = username.c_str();
	result["security"] = (pSession) ? uint32(pSession->GetSecurity()) : 0;
	result["charater"] = online.SerializerInfo();
    if (!operation.isNull())
        result["operation"] = operation;
	return result;
}

OnlineMgr::OnlineMgr()
{
}

OnlineMgr::~OnlineMgr()
{
}

OnlineMgr* OnlineMgr::instance()
{
	static OnlineMgr instance;
	return &instance;
}

void OnlineMgr::LoadAccounts()
{
    uint32 oldMSTime = getMSTime();
    QueryResult result = LoginDatabase.Query("SELECT id, username FROM account");
    if (!result)
    {
        TC_LOG_INFO("server.loading", ">> Loaded 0 accounts");
        return;
    }

    uint32 count = 0;
    do
    {
        Field* fields = result->Fetch();
        uint32 accountId = fields[0].GetUInt32();
        std::string name = fields[1].GetString();
        if (AddNewAccount(accountId, name))
            ++count;
    } while (result->NextRow());

    TC_LOG_INFO("server.loading", ">> Loaded %u accounts in %u ms", count, GetMSTimeDiffToNow(oldMSTime));
}

bool OnlineMgr::IsLegacyBotAccountName(std::string const& name)
{
    // Keep the historical classification until legacy data is migrated explicitly.
    std::string lowerName = boost::algorithm::to_lower_copy(name);
    if (lowerName.size() < 10 || lowerName.substr(0, 9) != "playerbot")
        return false;
    return std::atoi(lowerName.substr(9).c_str()) > 0;
}

bool OnlineMgr::IsLegacyBotAccount(uint32 accountId)
{
    std::unique_lock<std::mutex> guard(g_uniqueMgrLock);
    return m_LegacyBotAccounts.find(accountId) != m_LegacyBotAccounts.end();
}

bool OnlineMgr::AddNewAccount(uint32 guid, std::string& name)
{
	if (guid == 0 || name.empty())
		return false;
	std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
    if (IsLegacyBotAccountName(name))
        return m_LegacyBotAccounts.insert(guid).second;
    if (m_OnlinePlayerAcc.find(guid) != m_OnlinePlayerAcc.end())
        return false;
    m_OnlinePlayerAcc[guid] = ToolAccountInfo(guid, name.c_str());
	return true;
}

bool OnlineMgr::CharaterOnline(uint32 accID, uint32 charID, const std::string& charName, uint16 race, uint16 pro, uint16 lv, uint8 talent)
{
	std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
	if (m_OnlinePlayerAcc.find(accID) != m_OnlinePlayerAcc.end())
	{
		ToolAccountInfo& info = m_OnlinePlayerAcc.find(accID)->second;
		if (info.online.guid != 0)
			return false;
		info.online.guid = charID;
		info.online.name = charName;
		info.online.race = race;
		info.online.profession = pro;
		info.online.level = lv;
		info.online.talent = talent;
		return true;
	}
	return false;
}

bool OnlineMgr::CharaterOffline(uint32 accID)
{
	std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
	if (m_OnlinePlayerAcc.find(accID) != m_OnlinePlayerAcc.end())
	{
		ToolAccountInfo& info = m_OnlinePlayerAcc.find(accID)->second;
		if (info.online.guid == 0)
			return false;
		info.online.guid = 0;
		info.online.name.clear();
		info.online.race = 0;
		info.online.profession = 0;
		info.online.level = 0;
		info.online.talent = -1;
		return true;
	}
	return false;
}

bool OnlineMgr::CharaterState(uint32 accID, uint32 charID, uint16 lv, uint8 talent)
{
	std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
	if (m_OnlinePlayerAcc.find(accID) != m_OnlinePlayerAcc.end())
	{
		ToolAccountInfo& info = m_OnlinePlayerAcc.find(accID)->second;
        if (info.online.guid == 0 || info.online.guid != charID)
			return false;
		info.online.level = lv;
		info.online.talent = talent;
		return true;
	}
	return false;
}

bool OnlineMgr::SetAccountSecurity(uint32 accID, uint8 security)
{
	if (accID==0 || security > 4)
		return false;
	std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
	WorldSession* pSession = sWorld->FindSession(accID);
	if (pSession)
	{
		if (pSession->GetSecurity() == AccountTypes(security))
			return true;
		pSession->SetSecurity(AccountTypes(security));
	}
	char sqlText[128] = { 0 };
	sprintf(sqlText, "SELECT id FROM account_access WHERE id=%d", accID);
	QueryResult result = LoginDatabase.Query(sqlText);
	if (result)
	{
		sprintf(sqlText, "UPDATE account_access SET gmlevel=%d WHERE id=%d", security, accID);
		LoginDatabase.Query(sqlText);
	}
	else
	{
		sprintf(sqlText, "INSERT INTO account_access (id, gmlevel, RealmID) VALUES (%d, %d, -1)", accID, security);
		LoginDatabase.Query(sqlText);
	}
	return true;
}

std::string OnlineMgr::SerializerPlayerAccount(uint32 after, uint32 limit)
{
    std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
    Json::Value data;
    data["entry"] = "player_acc";
    data["result"] = "success";
    data["accounts"] = Json::Value(Json::arrayValue);
    data["total"] = Json::UInt(m_OnlinePlayerAcc.size());
    data["after"] = after;
    if (limit == 0 || limit > 100)
        limit = 99;
    data["limit"] = limit;
    uint32 next = after;
    auto itr = m_OnlinePlayerAcc.upper_bound(after);
    for (uint32 count = 0; itr != m_OnlinePlayerAcc.end() && count < limit; ++count)
    {
        data["accounts"].append(itr->second.SerializerInfo());
        // Reserve room for cursor/status fields and the legacy frame's trailing NUL.
        if (data.toStyledString().size() > 60000)
        {
            data["accounts"].resize(data["accounts"].size() - 1);
            if (count == 0)
            {
                data["result"] = "error";
                data["error"] = "account_too_large";
            }
            break;
        }
        next = itr->first;
        ++itr;
    }
    data["next_after"] = next;
    data["has_more"] = itr != m_OnlinePlayerAcc.end();
    return data.toStyledString();
}

bool OnlineMgr::SetCharacterOperation(uint32 accID, uint32 charID, std::string const& kind,
    std::string const& state, uint32 failures)
{
    std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
    auto itr = m_OnlinePlayerAcc.find(accID);
    if (itr == m_OnlinePlayerAcc.end() || !charID || itr->second.online.guid != charID)
        return false;
    Json::Value& operation = itr->second.operation;
    if (state == "queued" || (kind == "specialization" && state == "running"))
    {
        if (++m_OperationSequence == 0)
            ++m_OperationSequence;
        operation["id"] = m_OperationSequence;
    }
    operation["character_guid"] = charID;
    operation["kind"] = kind;
    operation["state"] = state;
    operation["item_failures"] = failures;
    return true;
}

std::string OnlineMgr::SerializerCharacterOperation(uint32 accID)
{
    std::unique_lock<std::mutex> sessionGuard(OnlineMgr::g_uniqueMgrLock);
    Json::Value data;
    data["entry"] = "player_change_status";
    data["guid"] = accID;
    auto itr = m_OnlinePlayerAcc.find(accID);
    if (itr == m_OnlinePlayerAcc.end())
        data["result"] = "error";
    else
    {
        data["result"] = "success";
        data["operation"] = itr->second.operation;
    }
    return data.toStyledString();
}
