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

#include "PlayerBotMgr.h"
#include "World.h"
#include "DB2Stores.h"
#include "Player.h"
#include "BattlegroundMgr.h"
#include "OnlineMgr.h"
#include "Group.h"
#include "SocialMgr.h"
#include "LFGMgr.h"
#include "Config.h"
#include "AccountMgr.h"
#include "BattlenetAccountMgr.h"
#include "CharacterPackets.h"
#include "MotionMaster.h"
#include <boost/algorithm/string.hpp>
#include <algorithm>
 //#include <boost/format.hpp>

PlayerBotCharBaseInfo PlayerBotBaseInfo::empty;
std::mutex PlayerBotMgr::g_uniqueLock;

std::string PlayerBotCharBaseInfo::GetNameANDClassesText()
{
    //std::string clsName;
    uint32 clsEntry = 620000;
    switch (profession)
    {
    case 1:
        //clsName = "  战  士 : ";
        clsEntry += 1;
        break;
    case 2:
        //clsName = "  圣骑士 : ";
        clsEntry += 2;
        break;
    case 3:
        //clsName = "  猎  人 : ";
        clsEntry += 3;
        break;
    case 4:
        //clsName = "  盗  贼 : ";
        clsEntry += 4;
        break;
    case 5:
        //clsName = "  牧  师 : ";
        clsEntry += 5;
        break;
    case 6:
        //clsName = "  死  骑 : ";
        clsEntry += 6;
        break;
    case 7:
        //clsName = "  萨  满 : ";
        clsEntry += 7;
        break;
    case 8:
        //clsName = "  法  师 : ";
        clsEntry += 8;
        break;
    case 9:
        //clsName = "  术  士 : ";
        clsEntry += 9;
        break;
    case 11:
        //clsName = "  德鲁伊 : ";
        clsEntry += 10;
        break;
    }
    std::string clsText = sObjectMgr->GetTrinityStringForDBCLocale(clsEntry);
    //consoleToUtf8(clsName, clsText);
    return clsText + name;
}

PlayerBotMgr::PlayerBotMgr() :
    m_LastBotAccountIndex(0)
{
#ifndef NON_SINGLE_GAME
#endif
}

PlayerBotMgr::~PlayerBotMgr()
{
    ClearBaseInfo();
}

PlayerBotMgr* PlayerBotMgr::instance()
{
    static PlayerBotMgr instance;
    return &instance;
}


bool PlayerBotMgr::IsBotAccuntName(std::string name)
{
    if (name.size() < 10)
        return false;
    std::string head = name.substr(0, 9);
    if (head != "playerbot")
        return false;
    std::string numText = name.substr(9);
    int num = atoi(numText.c_str());
    return num > 0;
}

PlayerBotBaseInfo* PlayerBotMgr::GetPlayerBotAccountInfo(uint32 guid)
{
    std::map<uint32, PlayerBotBaseInfo*>::iterator it = m_idPlayerBotBase.find(guid);
    if (it == m_idPlayerBotBase.end())
        return NULL;
    return it->second;
}

PlayerBotBaseInfo* PlayerBotMgr::GetAccountBotAccountInfo(uint32 guid)
{
    std::map<uint32, PlayerBotBaseInfo*>::iterator it = m_idAccountBotBase.find(guid);
    if (it == m_idAccountBotBase.end())
        return NULL;
    return it->second;
}

void PlayerBotMgr::ClearBaseInfo()
{
    for (std::map<uint32, PlayerBotBaseInfo*>::iterator it = m_idPlayerBotBase.begin();
        it != m_idPlayerBotBase.end();
        it++)
    {
        delete it->second;
    }
    m_idPlayerBotBase.clear();
    for (std::map<uint32, PlayerBotBaseInfo*>::iterator it = m_idAccountBotBase.begin();
        it != m_idAccountBotBase.end();
        it++)
    {
        delete it->second;
    }
    m_idAccountBotBase.clear();
}

void PlayerBotMgr::UpdateLastAccountIndex(std::string& username)
{
    //std::unique_lock<std::mutex> sessionGuard(PlayerBotMgr::g_uniqueLock);
    if (username.empty())
        return;
    std::string querySql = "SELECT id FROM account WHERE username='" + username + "'";
    QueryResult result = LoginDatabase.Query(querySql.c_str());
    if (result)
    {
        Field* fields = result->Fetch();
        if (fields)
        {
            uint32 id = fields[0].GetUInt32();
            m_LastBotAccountIndex = id;
        }
    }
}

void PlayerBotMgr::DestroyBotMail(uint32 guid)
{
    char sql[256] = { 0 };
    snprintf(sql, 255, "DELETE FROM mail WHERE receiver = %d", guid);
    CharacterDatabase.Execute(sql);
    //memset(sql, 0, 256);
    //snprintf(sql, 255, "DELETE FROM mail_items WHERE receiver = %d", guid);
    //CharacterDatabase.Execute(sql);
    CharacterDatabasePreparedStatement* stmt = CharacterDatabase.GetPreparedStatement(CHAR_DEL_MAIL_ITEMS);
    stmt->setUInt32(0, guid);
    CharacterDatabase.Execute(stmt);
}

void PlayerBotMgr::AddNewAccountBotBaseInfo(std::string name)
{
    std::string upperName = boost::algorithm::to_upper_copy(name);
    std::string sql("SELECT id, username, sha_pass_hash FROM account WHERE `username`='"); sql += upperName + "'";
    QueryResult result = LoginDatabase.Query(sql.c_str());
    if (!result)
        return;
    Field* fields = result->Fetch();
    uint32 id = fields[0].GetUInt32();
    std::string username = fields[1].GetString();
    std::string pass = fields[2].GetString();
    uint32 bnetId = fields[3].GetUInt32();

    if (m_idAccountBotBase.find(id) == m_idAccountBotBase.end())
    {
        PlayerBotBaseInfo* pInfo = new PlayerBotBaseInfo(id, username.c_str(), pass, true, bnetId);
        m_idAccountBotBase[id] = pInfo;
    }
}

void PlayerBotMgr::LoadPlayerBotBaseInfo()
{
    uint32 oldMSTime = getMSTime();

    ClearBaseInfo();
    QueryResult result = LoginDatabase.Query("SELECT id, username, sha_pass_hash, battlenet_account FROM account");
    if (!result)
    {
        TC_LOG_INFO("server.loading", ">> LoadPlayerBot Find 0 account!");
        return;
    }

    do
    {
        Field* fields = result->Fetch();

        uint32 id = fields[0].GetUInt32();
        std::string username = fields[1].GetString();
        std::string pass = fields[2].GetString();
        uint32 bnetId = fields[3].GetUInt32();

        sOnlineMgr->AddNewAccount(id, username); // Real player acc and bot acc all in

        std::string lowerName = boost::algorithm::to_lower_copy(username);
        if (IsBotAccuntName(lowerName))
        {
            if (m_idPlayerBotBase.find(id) == m_idPlayerBotBase.end())
            {
                PlayerBotBaseInfo* pInfo = new PlayerBotBaseInfo(id, username.c_str(), pass, false, bnetId);
                m_idPlayerBotBase[id] = pInfo;
            }
            m_LastBotAccountIndex = id;
        }
        else
        {
            if (m_idAccountBotBase.find(id) == m_idAccountBotBase.end())
            {
                PlayerBotBaseInfo* pInfo = new PlayerBotBaseInfo(id, username.c_str(), pass, true, bnetId);
                m_idAccountBotBase[id] = pInfo;
            }
        }
    } while (result->NextRow());


    if (m_idPlayerBotBase.size() > 0 || m_idAccountBotBase.size() > 0)
        LoadCharBaseInfo();

    TC_LOG_INFO("server.loading", ">> Loaded %u Player bot account base info in %u ms", m_idPlayerBotBase.size(), GetMSTimeDiffToNow(oldMSTime));
}

void PlayerBotMgr::LoadCharBaseInfo()
{
    QueryResult result = CharacterDatabase.Query("SELECT guid, account, name, race, class, gender, level FROM characters");

    if (!result)
    {
        TC_LOG_INFO("server.loading", ">> LoadPlayerBot Find 0 characters!");
        return;
    }

    do
    {
        Field* fields = result->Fetch();

        uint64 guid = fields[0].GetUInt64();
        uint32 accID = fields[1].GetUInt32();
        PlayerBotBaseInfo* pInfo = GetPlayerBotAccountInfo(accID);
        if (pInfo)
        {
            if (pInfo->characters.find(guid) == pInfo->characters.end())
            {
                std::string charName = fields[2].GetString();
                uint16 race = fields[3].GetInt16();
                uint16 pro = fields[4].GetInt16();
                uint16 gender = fields[5].GetInt16();
                uint16 level = fields[6].GetInt16();
                pInfo->characters.emplace(guid, PlayerBotCharBaseInfo{ guid, accID, charName, race, pro, gender, level });
                DestroyBotMail(guid);
            }
        }
        else if (pInfo = GetAccountBotAccountInfo(accID))
        {
            if (pInfo->characters.find(guid) == pInfo->characters.end())
            {
                std::string charName = fields[2].GetString();
                uint16 race = fields[3].GetInt16();
                uint16 pro = fields[4].GetInt16();
                uint16 gender = fields[5].GetInt16();
                uint16 level = fields[6].GetInt16();
                pInfo->characters.emplace(guid, PlayerBotCharBaseInfo{ guid, accID, charName, race, pro, gender, level });
                //DestroyBotMail(guid);
            }
        }
    } while (result->NextRow());
}


void PlayerBotMgr::OnAccountBotCreate(ObjectGuid const& guid, uint32 accountId, std::string const& name, uint8 gender, uint8 race, uint8 playerClass, uint8 level)
{
    PlayerBotBaseInfo* pInfo = GetAccountBotAccountInfo(accountId);
    if (!pInfo)
        return;
    uint32 id = uint32(uint64(guid));
    if (pInfo->characters.find(id) != pInfo->characters.end())
    {
        return;
    }
    pInfo->characters[id] = PlayerBotCharBaseInfo(id, accountId, name, uint16(race), uint16(playerClass), uint16(gender), uint16(level));
}

void PlayerBotMgr::OnAccountBotDelete(ObjectGuid& guid, uint32 accountId)
{
    PlayerBotBaseInfo* pInfo = GetAccountBotAccountInfo(accountId);
    if (!pInfo)
        return;
    pInfo->RemoveCharacterByGUID(guid);
}

std::string PlayerBotMgr::GetNameANDClassesText(ObjectGuid& guid)
{
    for (std::map<uint32, PlayerBotBaseInfo*>::iterator itInfo = m_idPlayerBotBase.begin();
        itInfo != m_idPlayerBotBase.end();
        itInfo++)
    {
        PlayerBotBaseInfo* pInfo = itInfo->second;
        std::string text = pInfo->GetCharNameANDClassesText(guid);
        if (!text.empty())
            return text;
    }
    return "";
}
