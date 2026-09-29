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

#include "ArenaPositionStore.h"

ArenaPositionStore* ArenaPositionStore::instance()
{
    static ArenaPositionStore instance;
    return &instance;
}

void ArenaPositionStore::LoadPositions()
{
    m_ArenaPositions.clear();

    // The bot editor is gone; Dalaran Sewers still reads its configured positions.
    WorldDatabasePreparedStatement* stmt = WorldDatabase.GetPreparedStatement(WORLD_SEL_LEGACY_ARENA_POSITIONS);
    PreparedQueryResult result = WorldDatabase.Query(stmt);
    if (!result)
    {
        TC_LOG_INFO("server.loading", ">> No legacy arena positions loaded from aiwaypoints");
        return;
    }

    do
    {
        Field* fields = result->Fetch();
        uint32 entry = fields[0].GetUInt32();
        uint32 map = fields[1].GetUInt32();
        float x = fields[2].GetFloat();
        float y = fields[3].GetFloat();
        float z = fields[4].GetFloat();
        m_ArenaPositions.emplace(entry, LegacyArenaPosition(entry, map, x, y, z));
    }
    while (result->NextRow());
}

LegacyArenaPosition* ArenaPositionStore::FindPosition(uint32 entry)
{
    auto itr = m_ArenaPositions.find(entry);
    return itr != m_ArenaPositions.end() ? &itr->second : nullptr;
}
