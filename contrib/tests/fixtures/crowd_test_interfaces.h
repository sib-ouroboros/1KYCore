#pragma once
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>
using uint32=std::uint32_t; using int32=std::int32_t;
#define TC_GAME_API
#define TC_LOG_DEBUG(...) ((void)0)
constexpr float CONTACT_DISTANCE=0.5f;
enum {TYPEID_UNIT,TYPEID_PLAYER};
enum MovementGeneratorType {CHASE_MOTION_TYPE,FOLLOW_MOTION_TYPE,POINT_MOTION_TYPE};
enum {UNIT_STATE_NOT_MOVE=1,UNIT_STATE_FLEEING=2,UNIT_STATE_CONFUSED=4,UNIT_STATE_CHASE_MOVE=8,UNIT_STATE_CHASE=16,UNIT_STATE_FOLLOW=32,UNIT_STATE_FOLLOW_MOVE=64};
enum {MOVE_RUN,MOVE_WALK,MOVE_SWIM,RATE_TARGET_POS_RECALCULATION_RANGE};
enum {CONFIG_CROWD_SEPARATION_ENABLE,CONFIG_CROWD_SEPARATION_PADDING,CONFIG_CROWD_SEPARATION_INTERVAL,CONFIG_CROWD_SEPARATION_MAX_NEIGHBORS};
namespace G3D {struct Vector3 {float x=0,y=0,z=0;};}
namespace Trinity {inline bool IsValidMapCoord(float x,float y,float z){return std::isfinite(x)&&std::isfinite(y)&&std::isfinite(z)&&std::fabs(x)<17000&&std::fabs(y)<17000;}}
struct ObjectGuid {uint32 value=0;bool IsEmpty()const{return !value;}uint32 GetCounter()const{return value;}std::string ToString()const{return std::to_string(value);}bool operator<(ObjectGuid b)const{return value<b.value;}bool operator==(ObjectGuid b)const{return value==b.value;}bool operator!=(ObjectGuid b)const{return value!=b.value;}};
struct MotionMaster {MovementGeneratorType type=CHASE_MOTION_TYPE;MovementGeneratorType GetCurrentMovementGeneratorType()const{return type;}};
struct MoveSpline {bool finalized=true,onTransport=false;G3D::Vector3 end;bool Finalized()const{return finalized;}G3D::Vector3 const& FinalDestination()const{return end;}};
struct TransportBase {void CalculatePassengerPosition(float&,float&,float&) {}};
struct Creature; struct Unit;
inline std::vector<Creature*> grid;
inline uint32 gridVisits=0,pathCalls=0,launches=0;
struct Unit {
 virtual ~Unit()=default;
 float x=0,y=0,z=0,size=1.5f,orientation=0;uint32 guid=1,phase=1,map=1,state=0,type=TYPEID_UNIT;
 bool inworld=true,alive=true,pet=false,controlled=false,fly=false,water=false,underwater=false,boss=false,worldboss=false,vehicle=false,transport=false,casting=false,los=true,walking=false,accessible=true,focusing=false,unreachable=false;
 ObjectGuid ownerGuid;Unit* victim=nullptr;MotionMaster motion;MoveSpline spline;MoveSpline* movespline=&spline;
 Creature* ToCreature();bool IsInWorld()const{return inworld;}bool IsAlive()const{return alive;}bool IsPet()const{return pet;}bool IsControlledByPlayer()const{return controlled;}ObjectGuid GetCharmerOrOwnerGUID()const{return ownerGuid;}ObjectGuid GetOwnerGUID()const{return ownerGuid;}
 void* GetVehicle()const{return vehicle?(void*)this:nullptr;}void* GetVehicleKit()const{return GetVehicle();}TransportBase* GetDirectTransport()const{return transport?(TransportBase*)this:nullptr;}
 bool CanFly()const{return fly;}bool CanWalk()const{return true;}bool CanSwim()const{return water;}bool IsInWater()const{return water;}bool IsUnderWater()const{return underwater;}bool IsDungeonBoss()const{return boss;}bool isWorldBoss()const{return worldboss;}
 bool IsInMap(Unit const* u)const{return map==u->map;}bool IsInPhase(Unit const* u)const{return phase==u->phase;}Unit* GetVictim()const{return victim;}bool HasUnitState(uint32 mask)const{return state&mask;}bool IsMovementPreventedByCasting()const{return casting;}
 MotionMaster* GetMotionMaster(){return &motion;}float GetObjectSize()const{return size;}float GetCombatReach()const{return size;}float GetMeleeRange(Unit const* u)const{return std::max(5.f,size+u->size+4.f/3.f);}
 float GetPositionX()const{return x;}float GetPositionY()const{return y;}float GetPositionZ()const{return z;}float GetAngle(Unit const* u)const{return std::atan2(u->y-y,u->x-x);}ObjectGuid GetGUID()const{return {guid};}uint32 GetEntry()const{return 123;}
 bool IsWithinLOS(float,float,float)const{return los;}bool IsWithinLOSInMap(Unit const* u)const{return los&&u->los;}void UpdateAllowedPositionZ(float,float,float& pz)const;
 void GetCreatureListInGrid(std::vector<Creature*>& out,float radius)const;
 uint32 GetTypeId()const{return type;}bool isInAccessiblePlaceFor(Creature*)const{return accessible;}bool IsInCombat()const{return victim!=nullptr;}bool IsFocusing(void*,bool)const{return focusing;}
 bool IsWithinDistInMap(Unit const* u,float dist)const{float dx=x-u->x,dy=y-u->y,dz=z-u->z;dist+=size+u->size;return dx*dx+dy*dy+dz*dz<dist*dist;}
 bool IsWithinDist2d(float px,float py,float dist)const{dist+=size;return (x-px)*(x-px)+(y-py)*(y-py)<dist*dist;}
 bool IsWithinDist3d(float px,float py,float pz,float dist)const{dist+=size;return (x-px)*(x-px)+(y-py)*(y-py)+(z-pz)*(z-pz)<dist*dist;}
 void GetContactPoint(Unit const* u,float& px,float& py,float& pz)const{float a=GetAngle(u),r=size+u->size+CONTACT_DISTANCE;px=x+r*std::cos(a);py=y+r*std::sin(a);pz=z;}
 void GetClosePoint(float& px,float& py,float& pz,float s,float d,float a)const{float r=size+s+d;px=x+r*std::cos(a+orientation);py=y+r*std::sin(a+orientation);pz=z;}
 void SetCannotReachTarget(bool value){unreachable=value;}void AddUnitState(uint32 s){state|=s;}void ClearUnitState(uint32 s){state&=~s;}bool IsStopped()const{return spline.finalized;}void StopMoving(){spline.finalized=true;}
 bool IsWithinMeleeRange(Unit const* u)const{float d=GetMeleeRange(u);return (x-u->x)*(x-u->x)+(y-u->y)*(y-u->y)+(z-u->z)*(z-u->z)<=d*d;}
 void Attack(Unit* u,bool){victim=u;}bool HasInArc(float,Unit*)const{return true;}void SetInFront(Unit*){}void SetWalk(bool w){walking=w;}bool IsWalking()const{return walking;}void UpdateSpeed(int){}
};
struct CreatureAI {void MovementInform(MovementGeneratorType,uint32){}};
struct Creature:Unit {CreatureAI ai;CreatureAI* AI(){return &ai;}};
inline Creature* Unit::ToCreature(){return static_cast<Creature*>(this);}
struct Player:Unit {Player(){type=TYPEID_PLAYER;}};
inline float geometryZ=0;inline bool overrideZ=false;
inline void Unit::UpdateAllowedPositionZ(float,float,float& pz)const{if(overrideZ)pz=geometryZ;}
inline void Unit::GetCreatureListInGrid(std::vector<Creature*>& out,float radius)const {++gridVisits;for(auto c:grid){float dx=c->x-x,dy=c->y-y;if(dx*dx+dy*dy<(radius+c->size)*(radius+c->size))out.push_back(c);}}
enum {PATHFIND_NORMAL=1,PATHFIND_SHORTCUT=2,PATHFIND_INCOMPLETE=4,PATHFIND_NOPATH=8,PATHFIND_NOT_USING_PATH=16,PATHFIND_SHORT=32};
inline unsigned pathType=PATHFIND_NORMAL;inline bool blockPaths=false;inline float endpointError=0;inline bool blockPositive=false;
struct PathGenerator {G3D::Vector3 end,actual;std::vector<G3D::Vector3> points;explicit PathGenerator(Unit*){}bool CalculatePath(float x,float y,float z,bool=false){++pathCalls;end={x,y,z};actual={x+endpointError,y,z};points={actual};return !blockPaths&&!(blockPositive&&y>0.0f);}unsigned GetPathType()const{return pathType;}G3D::Vector3 const& GetActualEndPosition()const{return actual;}G3D::Vector3 GetEndPosition()const{return end;}auto const& GetPath()const{return points;}};
struct World {bool enabled=true;float padding=.2f;uint32 interval=500,maxNeighbors=64;bool getBoolConfig(int)const{return enabled;}float getFloatConfig(int)const{return padding;}uint32 getIntConfig(int c)const{return c==CONFIG_CROWD_SEPARATION_INTERVAL?interval:maxNeighbors;}float getRate(int)const{return 1.5f;}};
inline World world;inline World* sWorld=&world;
template<class T,class D>struct MovementGeneratorMedium {virtual ~MovementGeneratorMedium()=default;virtual MovementGeneratorType GetMovementGeneratorType()const=0;virtual void unitSpeedChanged(){}};
struct FollowerReference {Unit* target=nullptr;void link(Unit* t,void*){target=t;}bool isValid()const{return target!=nullptr;}Unit* operator->()const{return target;}Unit* getTarget()const{return target;}};
struct TimeTrackerSmall {int remaining;explicit TimeTrackerSmall(int t):remaining(t){}void Update(uint32 d){remaining-=int(d);}bool Passed()const{return remaining<=0;}void Reset(int t){remaining=t;}};
namespace Movement {struct MoveSplineInit {Unit* owner;explicit MoveSplineInit(Unit* u):owner(u){}void MovebyPath(std::vector<G3D::Vector3> const& p){owner->spline.end=p.back();}void SetWalk(bool){}void SetFacing(Unit*){}void Launch(){++launches;owner->spline.finalized=false;}};}
