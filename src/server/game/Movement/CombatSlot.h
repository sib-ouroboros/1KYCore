/* NPC melee combat positioning; GPL-2.0-or-later, like the movement core. */
#ifndef TRINITY_COMBAT_SLOT_H
#define TRINITY_COMBAT_SLOT_H

#include "Common.h"
class Creature;
class Unit;
class PathGenerator;

// Owned only by a chase generator. No persistent unit pointers or slot locks.
struct CombatSlotState
{
    bool valid = false;
    float angle = 0.0f;
    float targetX = 0.0f, targetY = 0.0f, targetZ = 0.0f;
    uint32 cooldown = 0;
    void Reset() { valid = false; cooldown = 0; }
    void Update(uint32 diff) { cooldown = diff >= cooldown ? 0 : cooldown - diff; }
};

namespace CombatSlots
{
    bool IsEligible(Creature* owner, Unit* target);
    // On success the provided PathGenerator contains the validated path.
    bool Select(Creature* owner, Unit* target, CombatSlotState& state,
        PathGenerator& path, float& x, float& y, float& z);
}
#endif
