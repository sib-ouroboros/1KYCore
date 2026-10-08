/*
 * Copyright (C) 2008-2018 TrinityCore <https://www.trinitycore.org/>
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

#include "ScriptMgr.h"
#include "Conversation.h"
#include "Creature.h"
#include <vector>

namespace
{
struct CampaignActorBinding
{
    uint32 ConversationId;
    uint8 Idx;
    uint32 CreatureEntry;
};

// Source conversation_creature GUIDs are unused by its implementation.
// Retain its creator-relative, phase-aware nearest-creature lookup instead.
CampaignActorBinding const CampaignActorBindings[] = {
    {1821,0,98102},
    {1823,0,98102},
    {1832,0,105333},
    {2017,0,106001},
    {2023,0,106001},
    {2211,0,42465},
    {2300,0,94138},
    {2381,0,107979},
    {2937,0,98008},
    {2938,0,103832},
    {2939,0,103778},
    {2940,0,98013},
    {2941,0,106091},
    {2942,0,106093},
    {2943,0,107025},
    {2944,0,104329},
    {3187,0,107806},
    {3572,0,112959},
    {3575,0,102594},
    {3597,0,113299},
    {3597,1,109102},
    {3642,0,99997},
    {3771,0,113419},
    {3772,0,93453},
    {3786,0,113481},
    {3787,0,108975},
    {3788,0,93555},
    {3791,0,106521},
    {3792,0,106519},
    {3793,0,106524},
    {3794,0,106518},
    {3795,0,106649},
    {3796,0,106517},
    {4110,0,116448},
    {4110,1,116414},
    {4593,0,115883},
    {4597,0,116880},
    {3914,0,118242},
    {3914,1,110489},
    {4204,0,116880},
    {1841,0,105464},
    {2778,0,109000}
};

class conversation_campaign_nearest_actors : public ConversationScript
{
public:
    conversation_campaign_nearest_actors() : ConversationScript("conversation_campaign_nearest_actors") { }

    void OnConversationCreate(Conversation* conversation, Unit* creator) override
    {
        if (!conversation || !creator)
            return;

        struct Actor { uint8 Idx; ObjectGuid Guid; };
        std::vector<Actor> actors;
        for (CampaignActorBinding const& binding : CampaignActorBindings)
        {
            if (binding.ConversationId != conversation->GetEntry())
                continue;
            Creature* creature = creator->FindNearestCreature(binding.CreatureEntry, creator->GetVisibilityRange());
            if (!creature)
                return; // Native Create rejects the missing actor; never substitute another entry.
            actors.push_back({binding.Idx, creature->GetGUID()});
        }
        // Publish only after every source actor has been found, including unused slots.
        for (Actor const& actor : actors)
            conversation->AddActor(actor.Guid, actor.Idx);
    }
};
}

void AddSC_conversation_scripts()
{
    new conversation_campaign_nearest_actors();
}
