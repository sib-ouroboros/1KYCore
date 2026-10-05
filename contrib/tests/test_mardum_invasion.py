#!/usr/bin/env python3
"""Compile actual Mardum departure handlers against isolated entity fixtures.

Checks ownership, phases, ordering and path rejection; not client visuals or
real Mardum geometry. Run with --no-sanitizers on toolchains without ASan.
"""
from pathlib import Path
import argparse,os,subprocess,tempfile

def method(source,marker):
 start=source.index(marker);opening=source.index('{',start);end=opening+1;depth=1
 while depth:
  depth+=(source[end]=='{')-(source[end]=='}');end+=1
 return source[start:end]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--no-sanitizers',action='store_true');args=parser.parse_args()
 root=Path(__file__).resolve().parents[2]
 source=(root/'src/server/scripts/BrokenIsles/DemonHunterZones/zone_mardum.cpp').read_text('utf8')
 block=source[source.index('struct MardumInvasionSpawn'):source.index('class go_mardum_legion_banner_1 :')]
 abandon=method(source,'    void OnQuestAbandon(Player* player, Quest const* quest)')
 complete=method(source,'    void OnSceneComplete(Player* player, uint32 /*sceneInstanceID*/')
 prefix=r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <list>
#include <map>
#include <stdexcept>
#include <vector>
using uint32=std::uint32_t;using uint8=std::uint8_t;using ObjectGuid=int;
constexpr uint32 QUEST_INVASION_BEGIN=40077;
REAL_QUEST_STATUS
constexpr uint32 CLASS_DEMON_HUNTER=12,SPELL_PHASE_MARDUM_WELCOME=59073,SPELL_PHASE_171=59074;
constexpr uint32 TEMPSUMMON_TIMED_DESPAWN=1,REACT_PASSIVE=0,UNIT_NPC_FLAGS=0,UNIT_FIELD_FLAGS=1;
constexpr uint32 UNIT_NPC_FLAG_QUESTGIVER=2,UNIT_NPC_FLAG_GOSSIP=1,UNIT_FLAG_IMMUNE_TO_PC=256,UNIT_FLAG_IMMUNE_TO_NPC=512;
constexpr uint32 PATHFIND_NORMAL=1,PATHFIND_SHORTCUT=2,PATHFIND_INCOMPLETE=4,PATHFIND_NOPATH=8,PATHFIND_NOT_USING_PATH=16;
struct Position{float x,y,z,o;float GetPositionX()const{return x;}float GetPositionY()const{return y;}float GetPositionZ()const{return z;}};
struct Player;struct Creature;struct TempSummon;struct CreatureAI;struct Quest;
unsigned smartAccepts=0;
using LocaleConstant=int;constexpr int GENDER_FEMALE=1;
struct FakePacket{bool chat=false;int value=0,locale=0,type=0;};
struct Session{int GetSessionDbLocaleIndex(){return 2;}};
struct CreatureTextEntry{int id=0,type=12,lang=0,sound=0,BroadcastTextId=0,emote=0;};
using CreatureTextMap=std::map<int,std::map<int,std::vector<CreatureTextEntry>>>;
struct TextMgr{
 CreatureTextMap texts;
 TextMgr(){texts[93011][0]={{0,12,0,55248,0,0}};texts[93011][1]={{0,12,0,55246,0,0}};texts[98292][0]={{0,12,0,55284,0,0}};}
 CreatureTextMap const& GetTextMap(){return texts;}
 std::string GetLocalizedChatString(int entry,int,int group,int,int locale){if(locale!=2)throw std::runtime_error("wrong locale");return std::to_string(entry*10+group);}
} textMgr;
#define sCreatureTextMgr (&textMgr)
struct BroadcastTextEntry{uint32 SoundEntriesID[2]={0,0};};
struct BroadcastStore{BroadcastTextEntry* LookupEntry(int){return nullptr;}} sBroadcastTextStore;
namespace WorldPackets{
 namespace Chat{struct Chat{FakePacket packet;void Initialize(int type,int,Creature*,Player*,std::string text,int,std::string,int locale){packet={true,std::stoi(text),locale,type};}FakePacket* Write(){return &packet;}};}
 namespace Misc{struct PlaySound{FakePacket packet;PlaySound(int,int sound):packet{false,sound,0,0}{}FakePacket* Write(){return &packet;}};}
}
struct Spline{bool finalized=false;bool Finalized(){return finalized;}};
struct Motion{int idles=0;void MoveIdle(){++idles;}};
struct Creature{
 int entry=0,map=1481,guid=0;Position position{1179.57f,3202.61f,51.4265f,0};
 bool removed=false,active=false,walking=true,initOK=true;int react=1;uint32 flags[2]={3,0};
 int pathType=PATHFIND_NORMAL;bool pathOK=true;std::vector<int> path{1,2};unsigned launches=0;int launchResult=1000;
 CreatureAI* ai=nullptr;Spline spline;Spline* movespline=&spline;Motion motion;
 virtual ~Creature();virtual TempSummon* ToTempSummon(){return nullptr;}
 int GetEntry(){return entry;}int GetGUID(){return guid;}int getGender(){return 0;}void HandleEmoteCommand(int){}bool IsInMap(Player*);bool IsWithinDistInMap(Player*,float);
 float GetDistance(Position const& p){return std::hypot(position.x-p.x,position.y-p.y);}
 void DespawnOrUnsummon(){removed=true;}void SetFacingToObject(Player*){}
 void SetWalk(bool value){walking=value;}Motion* GetMotionMaster(){return &motion;}
 void SetReactState(int v){react=v;}void RemoveFlag(int f,uint32 v){flags[f]&=~v;}void SetFlag(int f,uint32 v){flags[f]|=v;}
 void setActive(bool v){active=v;}bool AIM_Initialize(CreatureAI*);CreatureAI* AI(){return ai;}
};
struct CreatureAI{
 Creature* me;explicit CreatureAI(Creature* c):me(c){}virtual ~CreatureAI()=default;
 virtual uint32 GetData(uint32)const{return 0;}virtual void UpdateAI(uint32){}
};
struct ScriptedAI:CreatureAI{using CreatureAI::CreatureAI;void Talk(int,Player*);};
struct SmartAI:ScriptedAI{using ScriptedAI::ScriptedAI;virtual void sQuestAccept(Player*,Quest const*){++smartAccepts;}};
Creature::~Creature(){delete ai;}
bool Creature::AIM_Initialize(CreatureAI* v){if(!initOK)return false;delete ai;ai=v;return true;}
struct TempSummon:Creature{int owner=0;bool personal=false;uint32 lifetime=0;TempSummon* ToTempSummon()override{return this;}int GetSummonerGUID(){return owner;}};
struct Player{
 int guid=1,map=1481,klass=CLASS_DEMON_HUNTER,status=QUEST_STATUS_INCOMPLETE;bool near=true;
 bool welcome=true,phase171=true;unsigned summons=0,failAt=99;
 std::vector<TempSummon*> actors;std::vector<int> lines,sounds;int lastLocale=0,lastType=0;Session session;
 Session* GetSession(){return &session;}
 void SendDirectMessage(FakePacket* packet){if(packet->chat){lines.push_back(packet->value);lastLocale=packet->locale;lastType=packet->type;}else sounds.push_back(packet->value);}
 int GetGUID(){return guid;}int GetMapId(){return map;}int getClass(){return klass;}int GetQuestStatus(uint32){return status;}
 void RemoveAurasDueToSpell(uint32 id){if(id==SPELL_PHASE_MARDUM_WELCOME)welcome=false;if(id==SPELL_PHASE_171)phase171=false;}
 void AddAura(uint32 id){if(id==SPELL_PHASE_MARDUM_WELCOME)welcome=true;}
 void GetCreatureListWithEntryInGrid(std::list<Creature*>&,int,float);
 TempSummon* SummonCreature(uint32 entry,Position const& pos,uint32,uint32 lifetime,uint32,bool personal);
};
std::vector<Creature*> world;std::map<int,Player*> players;
bool Creature::IsInMap(Player* p){return map==p->map;}
bool Creature::IsWithinDistInMap(Player* p,float){return IsInMap(p)&&p->near;}
void ScriptedAI::Talk(int id,Player* p){p->lines.push_back(me->entry*10+id);}
void Player::GetCreatureListWithEntryInGrid(std::list<Creature*>& out,int entry,float){for(auto* c:world)if(c->entry==entry&&!c->removed)out.push_back(c);}
TempSummon* Player::SummonCreature(uint32 entry,Position const& pos,uint32,uint32 lifetime,uint32,bool personal){
 if(summons++==failAt)return nullptr;
 auto* c=new TempSummon;c->entry=entry;c->owner=guid;c->position=pos;c->map=map;c->personal=personal;c->lifetime=lifetime;
 c->ai=new ScriptedAI(c);actors.push_back(c);world.push_back(c);return c;
}
namespace ObjectAccessor{Player* GetPlayer(Creature&,int guid){auto it=players.find(guid);return it==players.end()?nullptr:it->second;}}
struct PathGenerator{Creature* c;explicit PathGenerator(Creature* c):c(c){}bool CalculatePath(float,float,float){return c->pathOK;}int GetPathType(){return c->pathType;}std::vector<int>const& GetPath(){return c->path;}};
namespace Movement{struct MoveSplineInit{Creature* c;explicit MoveSplineInit(Creature*c):c(c){}void MovebyPath(std::vector<int>const&){}void SetWalk(bool){}int Launch(){++c->launches;c->spline.finalized=false;return c->launchResult;}};}
unsigned errors=0;
#define TC_LOG_ERROR(...) (++errors)
struct Quest{uint32 id=QUEST_INVASION_BEGIN;uint32 GetQuestId()const{return id;}};
struct CreatureScript{explicit CreatureScript(char const*){}virtual ~CreatureScript()=default;virtual CreatureAI* GetAI(Creature*)const{return nullptr;}virtual bool OnQuestAccept(Player*,Creature*,Quest const*){return true;}};
struct SceneTemplate{};
void require(bool v,char const* msg){if(!v)throw std::runtime_error(msg);}
'''
 suffix=r'''
int main(){
 Player a,b;b.guid=2;players[1]=&a;players[2]=&b;
 Creature shared;shared.entry=93011;shared.ai=new ScriptedAI(&shared);world.push_back(&shared);
 Quest quest;npc_kayn_sunfury_welcome handler;
 npc_kayn_sunfury_welcome::WelcomeAI welcomeAI(&shared);welcomeAI.sQuestAccept(&a,&quest);require(smartAccepts==0,"shared acceptance suppressed only for 40077");
 Quest other;other.id=40078;welcomeAI.sQuestAccept(&a,&other);require(smartAccepts==1,"other SmartAI acceptance preserved");
 handler.OnQuestAccept(&a,&shared,&quest);handler.OnQuestAccept(&b,&shared,&quest);
 require(a.actors.size()==6&&b.actors.size()==6,"six allies per player");
 require(!shared.removed&&shared.launches==0&&shared.position.x==1179.57f,"shared giver unchanged");
 require(!a.welcome&&a.phase171,"only welcome phase removed");
 for(auto* c:a.actors){require(c->personal&&c->owner==1&&c->lifetime==60000,"personal before map insertion; finite lifetime");require(c->flags[0]==0&&c->react==REACT_PASSIVE&&c->active,"passive actors without quest menus");}
 auto* kayn=a.actors[0];kayn->ai->UpdateAI(100);require(a.lines==std::vector<int>{930110},"first personal line");require(b.lines.empty()&&b.sounds.empty()&&a.sounds==std::vector<int>{55248}&&a.lastLocale==2&&a.lastType==12,"localized SAY and sound only to owner");
 kayn->ai->UpdateAI(5000);require(a.lines==std::vector<int>({930110,930111})&&kayn->launches==0,"second line before departure");
 a.actors[1]->ai->UpdateAI(10100);require(a.lines.back()==982920,"Korvas shout");
 kayn->ai->UpdateAI(6000);require(kayn->launches==1&&!kayn->removed&&!kayn->walking,"run on complete path");
 kayn->spline.finalized=true;kayn->ai->UpdateAI(1);require(kayn->removed,"cleanup only after arrival");
 CleanupMardumInvasionActors(&a);for(auto*c:a.actors)require(c->removed,"owner cleanup");for(auto*c:b.actors)require(!c->removed,"other player unaffected");
 handler.OnQuestAccept(&a,&shared,&quest);require(a.actors.size()==12,"repeat acceptance allowed");
 auto* c=a.actors.back();c->pathType=PATHFIND_INCOMPLETE;c->ai->UpdateAI(13000);require(c->launches==0&&!c->removed&&errors==1,"incomplete route never forced");
 auto* shortPath=a.actors[6];shortPath->path.resize(1);shortPath->ai->UpdateAI(13000);require(shortPath->launches==0&&!shortPath->removed,"empty spline rejected");
 auto* failedPath=a.actors[7];failedPath->pathOK=false;failedPath->ai->UpdateAI(13000);require(failedPath->launches==0&&!failedPath->removed,"failed calculation rejected");
 auto* failedLaunch=a.actors[8];failedLaunch->launchResult=0;failedLaunch->ai->UpdateAI(13000);require(!failedLaunch->removed,"failed launch not treated as arrival");
 for(int type:{PATHFIND_SHORTCUT,PATHFIND_NOPATH,PATHFIND_NOT_USING_PATH}){auto* x=b.actors[type==2?0:type==8?1:2];x->pathType=type;x->ai->UpdateAI(13000);require(x->launches==0,"unsafe path rejected");}
 a.status=QUEST_STATUS_NONE;c->ai->UpdateAI(1);require(c->removed,"abandon cleanup");
 b.map=1;b.actors[3]->ai->UpdateAI(1);require(b.actors[3]->removed,"map change cleanup");
 b.map=1481;players.erase(2);b.actors[4]->ai->UpdateAI(1);require(b.actors[4]->removed,"logout cleanup");
 players[2]=&b;b.status=QUEST_STATUS_COMPLETE;b.actors[5]->ai->UpdateAI(1);require(b.actors[5]->removed,"banner completion cleanup");
 a.status=QUEST_STATUS_NONE;Lifecycle lifecycle;lifecycle.OnQuestAbandon(&a,&quest);require(a.welcome&&!a.phase171,"abandon restores starting phase");
 a.welcome=false;a.status=QUEST_STATUS_INCOMPLETE;lifecycle.OnSceneComplete(&a,0,nullptr);require(!a.welcome,"late intro callback cannot restore old phase");
 a.status=QUEST_STATUS_NONE;lifecycle.OnSceneComplete(&a,0,nullptr);require(a.welcome,"intro for fresh player");
 a.status=QUEST_STATUS_INCOMPLETE;a.map=1;auto count=a.actors.size();handler.OnQuestAccept(&a,&shared,&quest);require(a.actors.size()==count,"wrong map rejected");
 a.map=1481;a.klass=1;handler.OnQuestAccept(&a,&shared,&quest);require(a.actors.size()==count,"wrong class rejected");
 welcomeAI.sQuestAccept(&a,&quest);require(smartAccepts==2,"wrong class uses original acceptance");
 a.klass=CLASS_DEMON_HUNTER;quest.id=1;handler.OnQuestAccept(&a,&shared,&quest);require(a.actors.size()==count,"other quest unaffected");
 for(auto* x:world)if(x!=&shared)delete x;
 std::cout<<"PASS: actual Mardum handlers; dialogue ordering, personal actors, phases, safe paths, cancellation and multiplayer isolation\n";
}
'''
 # Reject fixture-only field names that do not exist in the actual core.
 updates=(root/'src/server/game/Entities/Object/Updates/UpdateFields.h').read_text('utf8')
 assert '    UNIT_NPC_FLAGS ' in updates
 assert 'UNIT_FIELD_NPC_FLAGS' not in block
 prefix=prefix.replace('REAL_QUEST_STATUS',method((root/'src/server/game/Quests/QuestDef.h').read_text('utf8'),'enum QuestStatus : uint8')+';')
 code=prefix+block+'struct Lifecycle{\n'+abandon.replace(' override','')+'\n'+complete.replace(' override','')+'\n};\n'+suffix
 with tempfile.TemporaryDirectory(prefix='mardum-invasion-') as tmp:
  src=Path(tmp)/'test.cpp';exe=Path(tmp)/('test.exe' if os.name=='nt' else 'test');src.write_text(code,encoding='utf8')
  flags=['-std=c++17','-Wall','-Wextra','-Werror','-g']
  if not args.no_sanitizers:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
  subprocess.run([os.environ.get('CXX','g++'),*flags,str(src),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
