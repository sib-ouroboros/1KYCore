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

#ifndef __PLAYERBOTMGR_H__
#define __PLAYERBOTMGR_H__

 //#include <chrono>

#include "Log.h"
#include "Common.h"
#include "SharedDefines.h"
#include "DatabaseEnv.h"
#include "Timer.h"
//#include "Callback.h"
#include "PlayerBotSession.h"
#include "BotAITool.h"
#include "LFGMgr.h"
//#include "ArenaTeamMgr.h"
#include "Containers.h"

class ObjectGuid;
struct BotGlobleSchedule;
class PlayerBotSession;

struct PlayerBotCharBaseInfo
{
    uint64 guid;
    uint32 account;
    std::string name;
    uint16 race;
    uint16 profession;
    uint16 gender;
    uint16 level;

    PlayerBotCharBaseInfo()
    {
        guid = 0;
        account = 0;
        race = profession = gender = level = 0;
    }
    PlayerBotCharBaseInfo(uint64 id, uint32 acc, const std::string& na, uint16 ra, uint16 pro, uint16 gen, uint16 lv) :
        guid(id), account(acc), name(na), race(ra), profession(pro), gender(gen), level(lv)
    {
    }

    std::string GetNameANDClassesText();

    TeamId GetCamp()
    {
        if (race == 1 || race == 3 || race == 4 || race == 7 || race == 11)
        {
            return TeamId::TEAM_ALLIANCE;
        }
        if (race == 2 || race == 5 || race == 6 || race == 8 || race == 10)
        {
            return TeamId::TEAM_HORDE;
        }
        return TeamId::TEAM_NEUTRAL;
    }
};

struct PlayerBotBaseInfo
{
    static PlayerBotCharBaseInfo empty;
    bool isAccountInfo;
    uint32 id;
    std::string username;
    uint32 battlenetAccountId;
    std::string pass;
    using CharInfoMap = std::map<uint64, PlayerBotCharBaseInfo>;
    CharInfoMap characters;
    std::queue<WorldPacket> needCreateBots;

    PlayerBotBaseInfo(uint32 uid, const char* name, std::string& pa, bool isAcc, uint32 bnetId) :
        isAccountInfo(isAcc), id(uid), pass(pa), battlenetAccountId(bnetId)
    {
        characters.clear();
        username = name;
    }

    bool MatchRaceByFuction(bool fuction, uint16 race)
    {
        if (fuction)
        {
            if (race == 1 || race == 3 || race == 4 || race == 7 || race == 11)
            {
                return true;
            }
        }
        else
        {
            if (race == 2 || race == 5 || race == 6 || race == 8 || race == 10)
            {
                return true;
            }
        }
        return false;
    }
    bool ExistClass(bool fuction, uint16 prof)
    {
#ifdef INCOMPLETE_BOT
        if (prof != 1 && prof != 5 && prof != 9)
            return false;
#endif
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (it->second.profession == prof)
            {
                uint16 race = it->second.race;
                if (MatchRaceByFuction(fuction, race))
                    return true;
            }
        }
        return false;
    }

    PlayerBotCharBaseInfo& GetRandomCharacterByFuction(bool faction)
    {
        if (characters.size() <= 0)
        {
            return empty;
        }
#ifdef INCOMPLETE_BOT
        for (int i = 0; i < 20; i++)
#else
        for (int i = 0; i < 5; i++)
#endif
        {
            // SylvaniaCore: correction racine du crash #56 - avec un seul perso sur le
            // compte, characters.size()/2 - 1 = -1 => irand(0,-1) => ASSERT max >= min
            int32 maxSelect = int32(characters.size()) / 2 - 1;
            if (maxSelect < 0)
                maxSelect = 0;
            int16 select = int16(irand(0, maxSelect));
            for (CharInfoMap::iterator it = characters.begin();
                it != characters.end();
                it++)
            {
#ifdef INCOMPLETE_BOT
                if (it->second.profession != 1 && it->second.profession != 5 && it->second.profession != 9)
                    continue;
#endif
                if (MatchRaceByFuction(faction, it->second.race))
                {
                    if (select <= 0)
                        return it->second;
                    else
                        --select;
                }
            }
        }
        return characters.begin()->second;
    }

    std::vector<uint32> GetNoArenaTeamCharacterIDsByFuction(bool faction, ArenaGroupTypes type)
    {
        std::vector<uint32> outIDs;
        if (characters.size() <= 0)
        {
            return outIDs;
        }
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
#ifdef INCOMPLETE_BOT
            if (it->second.profession != 1 && it->second.profession != 5 && it->second.profession != 9)
                continue;
#endif
            if (MatchRaceByFuction(faction, it->second.race))
            {
                //if (sArenaTeamMgr->ExistArenaTeamByType(ObjectGuid(uint64(it->second.guid)), type))
                //	continue;
                outIDs.push_back(it->second.guid);
            }
        }
        Trinity::Containers::RandomShuffle(outIDs);
        //unsigned seed = std::chrono::system_clock::now().time_since_epoch().count();
        //std::shuffle(outIDs.begin(), outIDs.end(), std::default_random_engine(time(NULL)));
        return outIDs;
    }

    PlayerBotCharBaseInfo& GetCharacter(bool faction, uint32 prof)
    {
        if (characters.size() <= 0)
            return empty;
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (!MatchRaceByFuction(faction, it->second.race))
                continue;
            if (it->second.profession == prof)
                return it->second;
        }
        return empty;
    }

    bool ExistCharacterByGUID(ObjectGuid& guid)
    {
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (it->second.guid == guid.GetCounter())
                return true;
        }
        return false;
    }

    TeamId GetTeamIDByChar(ObjectGuid& guid)
    {
        uint32 id = guid.GetCounter();
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (it->second.guid != id)
                continue;
            return it->second.GetCamp();
        }
        return TeamId::TEAM_NEUTRAL;
    }

    std::string GetCharNameANDClassesText(ObjectGuid& guid)
    {
        uint32 id = guid.GetCounter();
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (it->second.guid != id)
                continue;
            return it->second.GetNameANDClassesText();
        }
        return "";
    }

    bool RemoveCharacterByGUID(ObjectGuid& guid)
    {
        uint32 id = guid.GetCounter();
        for (CharInfoMap::iterator it = characters.begin();
            it != characters.end();
            it++)
        {
            if (it->second.guid != id)
                continue;
            characters.erase(it);
            return true;
        }
        return false;
    }
};

//using BattlegroundTypeId = uint16;
class TC_GAME_API PlayerBotMgr
{

private:
    PlayerBotMgr();
    ~PlayerBotMgr();

public:
    PlayerBotMgr(PlayerBotMgr const&) = delete;
    PlayerBotMgr(PlayerBotMgr&&) = delete;

    PlayerBotMgr& operator= (PlayerBotMgr const&) = delete;
    PlayerBotMgr& operator= (PlayerBotMgr&&) = delete;

    static PlayerBotMgr* instance();

    bool IsPlayerBot(WorldSession* pSession);
    bool IsBotAccuntName(std::string name);
    void DestroyBotMail(uint32 guid);
    void LoadPlayerBotBaseInfo();
    void AddNewAccountBotBaseInfo(std::string name);
    PlayerBotBaseInfo* GetPlayerBotAccountInfo(uint32 guid);
    PlayerBotBaseInfo* GetAccountBotAccountInfo(uint32 guid);

    void UpdateLastAccountIndex(std::string& username);

    void OnPlayerBotCreate(ObjectGuid const& guid, uint32 accountId, std::string const& name, uint8 gender, uint8 race, uint8 playerClass, uint8 level);
    void OnAccountBotCreate(ObjectGuid const& guid, uint32 accountId, std::string const& name, uint8 gender, uint8 race, uint8 playerClass, uint8 level);
    void OnAccountBotDelete(ObjectGuid& guid, uint32 accountId);
    void OnPlayerBotLogin(WorldSession* pSession, Player* pPlayer);
    void ApplyBotTitle(Player* pPlayer);
    void OnPlayerBotLogout(WorldSession* pSession);
    void LogoutAllGroupPlayerBot(Group* pGroup, bool force);

    std::string GetNameANDClassesText(ObjectGuid& guid);
    int32 m_BotOnlineCount;

private:

    void ClearBaseInfo();
    void LoadCharBaseInfo();
    void LoadSessionPermissionsCallback(PreparedQueryResult result);

    void ClearEmptyNeedPlayer();
    void ClearNeedPlayer(uint32 bgTypeID, uint32 bracketID);

private:
    uint32 m_LastBotAccountIndex;
    std::map<uint32, PlayerBotBaseInfo*> m_idPlayerBotBase;
    std::map<uint32, PlayerBotBaseInfo*> m_idAccountBotBase;

public:
    static std::mutex g_uniqueLock;
};

#define sPlayerBotMgr PlayerBotMgr::instance()

#endif // __PLAYERBOTMGR_H__
