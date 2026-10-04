#include "interfaces.h"
#include "CombatSlot.h"
#include "ObjectPosSelector.h"
#include "TargetedMovementGenerator.h"
#include <chrono>
#include <limits>
#include <stdexcept>
#include <iostream>

void check(bool condition,char const* message){if(!condition)throw std::runtime_error(message);}
void reset(){grid.clear();world=World{};pathType=PATHFIND_NORMAL;blockPaths=false;endpointError=0;blockPositive=false;overrideZ=false;pathCalls=gridVisits=launches=0;}
Creature attacker(Unit& target,uint32 guid,float x=10,float y=0){Creature c;c.guid=guid;c.x=x;c.y=y;c.victim=&target;return c;}
// Unit fixtures contain a self pointer: never rely on copying it.
void bind(Creature& c){c.movespline=&c.spline;}
bool select(Creature& c,Unit& target,CombatSlotState& state,float& x,float& y,float& z){PathGenerator p(&c);return CombatSlots::Select(&c,&target,state,p,x,y,z);}
int main()
{
 try {
    reset();Player target;auto c=attacker(target,2);bind(c);CombatSlotState state;float x=0,y=0,z=0;
    check(select(c,target,state,x,y,z),"unoccupied ring");check(std::fabs(x-3.5f)<.001f&&std::fabs(y)<.001f,"natural approach");
    auto neighbor=attacker(target,3,3.5f);bind(neighbor);grid={&neighbor};state.Reset();
    check(select(c,target,state,x,y,z),"same-side pair");check(std::hypot(x-neighbor.x,y-neighbor.y)>=3.2f-.001f,"size padding");
    float angle=state.angle;state.Update(500);check(select(c,target,state,x,y,z),"stable existing slot");check(std::fabs(state.angle-angle)<.001f,"hysteresis");
    state.Update(500);target.orientation=2;check(select(c,target,state,x,y,z),"turning target");check(std::fabs(state.angle-angle)<.001f,"world angle unaffected");
    reset();target.orientation=0;neighbor.x=10;neighbor.spline.finalized=false;neighbor.spline.end={3.5f,0,0};grid={&neighbor};state.Reset();
    check(select(c,target,state,x,y,z)&&std::fabs(y)>.1f,"spline endpoint reservation");
    for(int exclusion=0;exclusion<8;++exclusion){
        reset();neighbor.x=3.5f;neighbor.spline.finalized=true;neighbor.phase=1;neighbor.map=1;neighbor.alive=neighbor.inworld=true;neighbor.victim=&target;neighbor.z=0;neighbor.pet=false;neighbor.transport=false;
        if(exclusion==0)neighbor.phase=2;
        if(exclusion==1)neighbor.map=2;
        if(exclusion==2)neighbor.alive=false;
        if(exclusion==3)neighbor.inworld=false;
        if(exclusion==4)neighbor.victim=nullptr;
        if(exclusion==5)neighbor.z=-5;
        if(exclusion==6)neighbor.pet=true;
        if(exclusion==7)neighbor.transport=true;
        grid={&neighbor};state.Reset();check(select(c,target,state,x,y,z)&&std::fabs(y)<.001f,"unrelated/vertical exclusion");
    }
    reset();grid={&neighbor};neighbor.transport=false;neighbor.z=0;neighbor.victim=&target;neighbor.inworld=neighbor.alive=true;neighbor.phase=neighbor.map=1;
    blockPositive=true;state.Reset();check(select(c,target,state,x,y,z)&&y<0,"alternative path side");
    for(unsigned flag:{PATHFIND_NOPATH,PATHFIND_INCOMPLETE,PATHFIND_SHORTCUT,PATHFIND_NOT_USING_PATH,PATHFIND_SHORT}){
        reset();pathType=PATHFIND_NORMAL|flag;state.Reset();check(!select(c,target,state,x,y,z),"invalid path flags");check(pathCalls<=8,"bounded paths");
    }
    reset();endpointError=1;state.Reset();check(!select(c,target,state,x,y,z),"navmesh endpoint mismatch");
    reset();overrideZ=true;geometryZ=-5;state.Reset();check(!select(c,target,state,x,y,z),"surface rejection");
    reset();blockPaths=true;state.Reset();check(!select(c,target,state,x,y,z),"blocked ring fallback");
    reset();state.Reset();check(select(c,target,state,x,y,z),"initial cache");
    uint32 visits=gridVisits;target.x=.8f;check(select(c,target,state,x,y,z)&&gridVisits==visits,"cooldown limits scans");target.x=0;
    reset();neighbor.x=3.5f;neighbor.y=0;neighbor.phase=neighbor.map=1;neighbor.z=0;neighbor.victim=&target;neighbor.alive=neighbor.inworld=true;neighbor.transport=false;
    auto second=attacker(target,4,-3.5f);bind(second);grid={&neighbor,&second};world.maxNeighbors=1;state.Reset();
    check(!select(c,target,state,x,y,z),"crowd capacity fallback");
    ChaseMovementGenerator<Creature> saturated(&target,0,0);saturated.DoInitialize(&c);
    check(launches==1&&!c.unreachable&&std::fabs(c.spline.end.x-3.5f)<.001f,"saturation continues legacy chase");
    reset();pathType=PATHFIND_INCOMPLETE;ChaseMovementGenerator<Creature> incomplete(&target,0,0);incomplete.DoInitialize(&c);
    check(launches==1&&!c.unreachable,"helper rejection preserves legacy partial-path policy");
    reset();c.x=3.4f;c.y=0;ChaseMovementGenerator<Creature> alreadyMelee(&target,0,0);alreadyMelee.DoInitialize(&c);
    check(launches==0&&pathCalls==0&&gridVisits==0,"do not shuffle an already touching NPC");c.x=10;
    for(float npcSize:{.1f,6.f}){
        reset();c.size=npcSize;neighbor.size=npcSize;neighbor.x=target.size+npcSize+.5f;neighbor.y=0;grid={&neighbor};state.Reset();
        check(select(c,target,state,x,y,z),"small/large creatures");
        check(std::hypot(x-neighbor.x,y-neighbor.y)>=2*npcSize+.2f-.001f,"scaled spacing");
        check(std::hypot(x-target.x,y-target.y)<=c.GetMeleeRange(&target),"scaled melee radius");
    }
    c.size=neighbor.size=1.5f;
    reset();world.enabled=false;state.Reset();check(!select(c,target,state,x,y,z)&&gridVisits==0&&pathCalls==0,"disabled has no path/grid overhead");
    reset();c.pet=true;check(!CombatSlots::IsEligible(&c,&target),"pet excluded");c.pet=false;c.boss=true;check(!CombatSlots::IsEligible(&c,&target),"boss excluded");c.boss=false;c.fly=true;check(!CombatSlots::IsEligible(&c,&target),"fly excluded");c.fly=false;c.casting=true;check(!CombatSlots::IsEligible(&c,&target),"caster excluded");c.casting=false;
    for(float size:{0.f,-1.f,std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity(),.1f,100.f}){
        ObjectPosSelector selector(0,0,size,size);selector.AddUsedPos(size,0,size);selector.InitializeAngle();float a;
        check(std::isfinite(selector.m_anglestep)&&selector.m_anglestep>0,"selector finite progress");
        for(unsigned i=0;i<1000&&selector.NextAngle(a);++i)check(std::isfinite(a),"finite selector angles");
        check(std::isfinite(selector.GetAngle(ObjectPosSelector::UsedPos(1,size,size))),"finite acos");
    }
    // Actual targeted movement: legacy fallback, disabled, offsets, follow, player,
    // arrivals/Attack, target changes and movement of the victim.
    reset();ChaseMovementGenerator<Creature> chase(&target,0,0);chase.DoInitialize(&c);check(launches==1&&chase.GetCombatSlotState()->valid,"chase integration");
    uint32 before=pathCalls;for(int i=0;i<10;++i)chase.DoUpdate(&c,100);check(pathCalls==before,"stationary target no path churn");
    target.x=2;chase.DoUpdate(&c,100);check(pathCalls>before,"moving target refresh");
    c.x=c.spline.end.x;c.y=c.spline.end.y;c.spline.finalized=true;chase.DoUpdate(&c,100);check(c.GetVictim()==&target&&!c.unreachable,"arrival attacks");
    c.victim=nullptr;chase.DoUpdate(&c,100);check(!chase.GetCombatSlotState()->valid,"lost victim clears slot");chase.DoFinalize(&c);
    reset();target.x=0;c.x=10;c.y=0;c.victim=&target;world.enabled=false;ChaseMovementGenerator<Creature> disabled(&target,0,0);disabled.DoInitialize(&c);
    check(gridVisits==0&&pathCalls==1&&std::fabs(c.spline.end.x-3.5f)<.001f,"disabled legacy endpoint/path");
    reset();blockPaths=true;ChaseMovementGenerator<Creature> blocked(&target,0,0);blocked.DoInitialize(&c);check(c.unreachable&&launches==0,"legacy unreachable behavior");
    reset();ChaseMovementGenerator<Creature> ranged(&target,10,0);ranged.DoInitialize(&c);check(gridVisits==0,"ranged offsets unchanged");
    reset();FollowMovementGenerator<Creature> follow(&target,1,0);follow.DoInitialize(&c);check(gridVisits==0,"follow unchanged");
    reset();Player player;player.x=10;player.victim=&target;ChaseMovementGenerator<Player> playerChase(&target,0,0);playerChase.DoInitialize(&player);check(gridVisits==0,"player chase unchanged");
    std::cout<<"Native helper, selector and chase regression checks passed\n";
    // Synthetic ring saturation benchmark; no real MMAP CPU claims.
    for(unsigned count:{1u,5u,10u,20u,40u,80u}){
        reset();std::vector<Creature> pack(count);std::vector<CombatSlotState> states(count);unsigned accepted=0;
        auto start=std::chrono::steady_clock::now();
        for(unsigned i=0;i<count;++i){pack[i].guid=i+10;pack[i].x=10;pack[i].victim=&target;grid.push_back(&pack[i]);}
        for(unsigned i=0;i<count;++i){if(select(pack[i],target,states[i],x,y,z)){pack[i].spline.end={x,y,z};pack[i].spline.finalized=false;++accepted;}}
        auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();
        check(pathCalls<=count*8,"path bound in packs");
        check(count==1?accepted==1:accepted>=2,"pack not collapsed");
        std::cout<<"pack="<<count<<" selected="<<accepted<<" grid_visits="<<gridVisits<<" path_calls="<<pathCalls<<" helper_us="<<us<<"\n";
    }
 }catch(std::exception const& e){std::cerr<<e.what()<<'\n';return 1;}
}
