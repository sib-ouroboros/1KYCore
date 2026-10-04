/* NPC melee combat positioning; GPL-2.0-or-later, like the movement core. */
#include "CombatSlot.h"
#include "Creature.h"
#include "Unit.h"
#include "World.h"
#include "ObjectPosSelector.h"
#include "PathGenerator.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "Log.h"
#include <algorithm>
#include <cmath>
#include <vector>

namespace
{
    constexpr float VerticalTolerance = 2.0f;
    constexpr unsigned MaxCandidates = 8;
    struct Occupant { float x, y, z, size; };
    float RelativeAngle(float angle)
    {
        return std::remainder(angle, 2.0f * float(M_PI));
    }
    bool GroundCreature(Creature* creature)
    {
        return creature->IsInWorld() && creature->IsAlive() &&
            !creature->IsPet() && !creature->IsControlledByPlayer() &&
            creature->GetCharmerOrOwnerGUID().IsEmpty() && !creature->GetVehicle() &&
            !creature->GetVehicleKit() && !creature->GetDirectTransport() &&
            !creature->CanFly() && !creature->IsInWater() && !creature->IsUnderWater() &&
            !creature->IsDungeonBoss() && !creature->isWorldBoss();
    }
    bool Clear(float x, float y, float z, float size, std::vector<Occupant> const& occupants)
    {
        for (Occupant const& other : occupants)
        {
            if (std::fabs(z - other.z) > VerticalTolerance)
                continue;
            float dx = x - other.x, dy = y - other.y;
            float distance = size + other.size;
            if (dx * dx + dy * dy < distance * distance - 0.0001f)
                return false;
        }
        return true;
    }
}

bool CombatSlots::IsEligible(Creature* owner, Unit* target)
{
    return sWorld->getBoolConfig(CONFIG_CROWD_SEPARATION_ENABLE) && GroundCreature(owner) &&
        target && target->IsInWorld() && target->IsAlive() && owner->IsInMap(target) &&
        owner->IsInPhase(target) && owner->GetVictim() == target && !target->GetDirectTransport() &&
        !owner->HasUnitState(UNIT_STATE_NOT_MOVE | UNIT_STATE_FLEEING | UNIT_STATE_CONFUSED) &&
        !owner->IsMovementPreventedByCasting() &&
        owner->GetMotionMaster()->GetCurrentMovementGeneratorType() == CHASE_MOTION_TYPE;
}

bool CombatSlots::Select(Creature* owner, Unit* target, CombatSlotState& state,
    PathGenerator& path, float& x, float& y, float& z)
{
    if (!IsEligible(owner, target))
    {
        state.Reset();
        return false;
    }
    float size = owner->GetObjectSize();
    float radius = target->GetObjectSize() + size + CONTACT_DISTANCE;
    if (!std::isfinite(radius) || !std::isfinite(size) || size <= 0.0f || radius <= 0.0f)
    {
        state.Reset();
        return false;
    }
    float preferred = state.valid ? state.angle : target->GetAngle(owner);
    float padding = sWorld->getFloatConfig(CONFIG_CROWD_SEPARATION_PADDING);
    std::vector<Occupant> occupants;
    bool collect = !state.cooldown;
    if (!collect && !state.valid)
        return false;

    ObjectPosSelector selector(target->GetPositionX(), target->GetPositionY(), size + padding, radius);
    if (collect)
    {
        state.cooldown = sWorld->getIntConfig(CONFIG_CROWD_SEPARATION_INTERVAL);
        std::vector<Creature*> nearby;
        target->GetCreatureListInGrid(nearby, radius + 2.0f * size + padding + 1.0f);
        // Incoming attackers can be close to each other but outside the victim ring.
        std::vector<Creature*> approaching;
        owner->GetCreatureListInGrid(approaching, 2.0f * size + padding + 1.0f);
        nearby.insert(nearby.end(), approaching.begin(), approaching.end());
        // Stable order independent of grid container iteration; spline endpoints act as reservations.
        std::sort(nearby.begin(), nearby.end(), [](Creature* a, Creature* b) { return a->GetGUID() < b->GetGUID(); });
        nearby.erase(std::unique(nearby.begin(), nearby.end()), nearby.end());
        uint32 relevantNeighbors = 0;
        for (Creature* other : nearby)
        {
            if (other == owner || !GroundCreature(other) || other->GetVictim() != target ||
                !owner->IsInMap(other) || !owner->IsInPhase(other) ||
                other->GetMotionMaster()->GetCurrentMovementGeneratorType() != CHASE_MOTION_TYPE)
                continue;
            float otherSize = other->GetObjectSize();
            if (!std::isfinite(otherSize) || otherSize <= 0.0f)
                continue;
            auto add = [&](float ox, float oy, float oz)
            {
                float dx = ox - target->GetPositionX(), dy = oy - target->GetPositionY();
                float dist = std::sqrt(dx * dx + dy * dy);
                if (!std::isfinite(dist) || !std::isfinite(oz) ||
                    std::fabs(oz - target->GetPositionZ()) > VerticalTolerance ||
                    dist > target->GetObjectSize() + otherSize + CONTACT_DISTANCE + 1.0f ||
                    !target->IsWithinLOS(ox, oy, oz))
                    return;
                occupants.push_back({ox, oy, oz, otherSize + padding});
                selector.AddUsedPos(otherSize + padding, RelativeAngle(std::atan2(dy, dx) - preferred), dist);
            };
            auto previousCount = occupants.size();
            add(other->GetPositionX(), other->GetPositionY(), other->GetPositionZ());
            if (!other->movespline->Finalized() && !other->movespline->onTransport)
            {
                auto const& end = other->movespline->FinalDestination();
                add(end.x, end.y, end.z);
            }
            if (occupants.size() != previousCount &&
                ++relevantNeighbors > sWorld->getIntConfig(CONFIG_CROWD_SEPARATION_MAX_NEIGHBORS))
            {
                state.valid = false;
                return false; // Saturation degrades to legacy chase, never blocks combat.
            }
        }
    }

    unsigned attempts = 0;
    auto tryAngle = [&](float angle)
    {
        ++attempts;
        float cx = target->GetPositionX() + radius * std::cos(angle);
        float cy = target->GetPositionY() + radius * std::sin(angle);
        float cz = target->GetPositionZ();
        if (!Trinity::IsValidMapCoord(cx, cy, cz))
            return false;
        owner->UpdateAllowedPositionZ(cx, cy, cz);
        float dz = cz - target->GetPositionZ();
        float melee = owner->GetMeleeRange(target);
        if (!Trinity::IsValidMapCoord(cx, cy, cz) || std::fabs(dz) > VerticalTolerance ||
            radius * radius + dz * dz > melee * melee ||
            !Clear(cx, cy, cz, size, occupants) || !target->IsWithinLOS(cx, cy, cz) ||
            !owner->IsWithinLOS(cx, cy, cz))
            return false;
        if (!path.CalculatePath(cx, cy, cz, false) ||
            !(path.GetPathType() & PATHFIND_NORMAL) ||
            (path.GetPathType() & (PATHFIND_NOPATH | PATHFIND_INCOMPLETE | PATHFIND_SHORTCUT | PATHFIND_NOT_USING_PATH | PATHFIND_SHORT)))
            return false;
        auto const& end = path.GetActualEndPosition();
        float ex = end.x - cx, ey = end.y - cy, ez = end.z - cz;
        float tx = end.x - target->GetPositionX(), ty = end.y - target->GetPositionY();
        float tz = end.z - target->GetPositionZ();
        if (!Trinity::IsValidMapCoord(end.x, end.y, end.z) || std::fabs(tz) > VerticalTolerance ||
            tx * tx + ty * ty + tz * tz > melee * melee || !target->IsWithinLOS(end.x, end.y, end.z) ||
            ex * ex + ey * ey + ez * ez > 0.25f * 0.25f ||
            !Clear(end.x, end.y, end.z, size, occupants))
            return false;
        state.valid = true;
        state.angle = RelativeAngle(angle);
        state.targetX = target->GetPositionX();
        state.targetY = target->GetPositionY();
        state.targetZ = target->GetPositionZ();
        x = cx; y = cy; z = cz;
        return true;
    };

    bool selected = tryAngle(preferred);
    if (!selected && collect)
    {
        selector.InitializeAngle();
        std::vector<float> angles;
        float angle;
        if (selector.FirstAngle(angle))
            angles.push_back(angle);
        // Bound enumeration as well as expensive navmesh checks.
        for (unsigned i = 0; i < 64 && selector.NextAngle(angle); ++i)
            angles.push_back(angle);
        bool preferPositive = (owner->GetGUID().GetCounter() & 1) != 0;
        std::sort(angles.begin(), angles.end(), [preferPositive](float a, float b)
        {
            if (std::fabs(a) != std::fabs(b))
                return std::fabs(a) < std::fabs(b);
            return preferPositive ? a > b : a < b;
        });
        for (float candidate : angles)
        {
            if (attempts >= MaxCandidates)
                break;
            if (tryAngle(preferred + candidate))
            {
                selected = true;
                break;
            }
        }
    }
    if (!selected)
        state.valid = false;
    TC_LOG_DEBUG("movement.crowd", "Crowd owner=%s entry=%u target=%s occupied=%u candidates=%u selected=%u angle=%f",
        owner->GetGUID().ToString().c_str(), owner->GetEntry(), target->GetGUID().ToString().c_str(),
        uint32(occupants.size()), attempts, uint32(selected), state.angle);
    return selected;
}
