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

#include "Chat.h"
#include "CustomTalkMenu.h"
#include "Player.h"
#include "RBAC.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

class customutility_commandscript : public CommandScript
{
public:
    customutility_commandscript() : CommandScript("customutility_commandscript") { }

    std::vector<ChatCommand> GetCommands() const override
    {
        static std::vector<ChatCommand> commandTable =
        {
            { "resetgossip", rbac::RBAC_PREM_COMMAND_RESETCUSTOMGOSSIP, true, &HandleResetGossipCommand, "" },
            { "displaymodel", rbac::RBAC_PREM_COMMAND_RESETCUSTOMGOSSIP, true, &HandleDisplayModelCommand, "" },
        };

        return commandTable;
    }

    static bool HandleResetGossipCommand(ChatHandler* handler, const char* args)
    {
        sCustomTalkMenu->Initialize();
        Player* player = handler->GetSession()->GetPlayer();
        player->Whisper(std::string("Success reset gossip menu!"), Language::LANG_COMMON, player);
        return true;
    }

    static bool HandleDisplayModelCommand(ChatHandler* handler, const char* args)
    {
        char* idStr = strtok((char*)args, " ");
        char* sizeStr = strtok(NULL, " ");
        if (!idStr)
            return false;
        uint32 id = (uint32)atoi(idStr);
        float size = sizeStr ? (float)atof(sizeStr) : 1.0f;
        Player* player = handler->GetSession()->GetPlayer();
        if (id == 0)
        {
            player->DeMorph();
            player->SetObjectScale(1.0f);
        }
        else
        {
            player->SetDisplayId(id);
            player->SetObjectScale(size);
        }
        return true;
    }
};

void AddSC_customutility_commandscript()
{
    new customutility_commandscript();
}
