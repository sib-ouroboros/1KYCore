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

#ifndef __AIWAYPOINTSMGR_H__
#define __AIWAYPOINTSMGR_H__

#include "Log.h"
#include "Common.h"
#include "SharedDefines.h"
#include "DatabaseEnv.h"
#include "Position.h"
#include <map>

struct AIWaypoint
{
	uint32 entry;
	uint32 mapID;
	float posX;
	float posY;
	float posZ;

    AIWaypoint(uint32 id, uint32 map, float x, float y, float z) :
        entry(id), mapID(map), posX(x), posY(y), posZ(z)
	{
	}

	Position GetPosition()
	{
		Position pos;
		pos.m_positionX = posX;
		pos.m_positionY = posY;
		pos.m_positionZ = posZ;
		return pos;
	}

};

class TC_GAME_API AIWaypointsMgr
{
public:
    typedef std::map<uint32, AIWaypoint> AIWPMap;

public:
	static AIWaypointsMgr* instance();

    void LoadAIWaypoints();
    AIWaypoint* FindAIWaypoint(uint32 entry);

private:
	AIWPMap m_AIWaypointMap;
};

#define sAIWPMgr AIWaypointsMgr::instance()

#endif // __AIWAYPOINTSMGR_H__
