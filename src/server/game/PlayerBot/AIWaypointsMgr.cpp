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

#include "AIWaypointsMgr.h"
#include "Timer.h"

AIWaypointsMgr::AIWaypointsMgr():
m_lastAIWPEntry(0)
{
}

AIWaypointsMgr::~AIWaypointsMgr()
{
	for (AIWPMap::iterator itAIWP = m_AIWaypointMap.begin();
		itAIWP != m_AIWaypointMap.end();
		itAIWP++)
	{
		delete itAIWP->second;
	}
	m_AIWaypointMap.clear();
}

AIWaypointsMgr* AIWaypointsMgr::instance()
{
	static AIWaypointsMgr instance;
	return &instance;
}

bool AIWaypointsMgr::LoadAIWaypoints()
{
	uint32 oldMSTime = getMSTime();

	m_lastAIWPEntry = 0;
	for (AIWPMap::iterator itAIWP = m_AIWaypointMap.begin();
		itAIWP != m_AIWaypointMap.end();
		itAIWP++)
	{
		delete itAIWP->second;
	}
	m_AIWaypointMap.clear();

	QueryResult curIncrementResult = WorldDatabase.Query("SELECT `AUTO_INCREMENT` FROM information_schema.`TABLES` WHERE `TABLE_NAME`='aiwaypoints'");
	if (curIncrementResult)
	{
		Field* fields = curIncrementResult->Fetch();
		uint32 curIncr = fields[0].GetUInt32();
		m_lastAIWPEntry = curIncr;
	}
	else
	{
		//TC_LOG_INFO("server.loading", ">> Load aiwaypoints AUTO_INCREMENT error!!!");
		return false;
	}

    WorldDatabasePreparedStatement* stmt = WorldDatabase.GetPreparedStatement(WORLD_SEL_ALL_AIWAYPOINTS);
	PreparedQueryResult result = WorldDatabase.Query(stmt);
	if (result)
	{
		do
		{
			Field* fields = result->Fetch();
			uint32 entry = fields[0].GetUInt32();
			uint32 map = fields[1].GetUInt32();
			float x = fields[2].GetFloat();
			float y = fields[3].GetFloat();
			float z = fields[4].GetFloat();
			std::string link = fields[5].GetString();
			std::string desc = fields[6].GetString();
			AIWaypoint* aiwp = new AIWaypoint(entry, map, x, y, z, link, desc);
			if (m_AIWaypointMap.find(entry) == m_AIWaypointMap.end())
				m_AIWaypointMap[entry] = aiwp;
			else
			{
				delete aiwp;
			}
			if (m_lastAIWPEntry < aiwp->entry)
				m_lastAIWPEntry = aiwp->entry;
		}
		while (result->NextRow());

		//for (AIWPMap::iterator itAIWP = m_AIWaypointMap.begin();
		//	itAIWP != m_AIWaypointMap.end();
		//	itAIWP++)
		//{
		//	itAIWP->second->ProcessLinkInfo(this);
		//}
	}

	//TC_LOG_INFO("server.loading", ">> Loaded %u ai way points %u ms", m_AIWaypointMap.size(), GetMSTimeDiffToNow(oldMSTime));
	return true;
}

AIWaypoint* AIWaypointsMgr::FindAIWaypoint(uint32 entry)
{
	AIWPMap::iterator itMap = m_AIWaypointMap.find(entry);
	if (itMap == m_AIWaypointMap.end())
		return NULL;
	return itMap->second;
}
