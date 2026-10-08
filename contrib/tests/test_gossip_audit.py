#!/usr/bin/env python3
"""Audit fixtures distinguish proven references from dynamic/default-menu reviews."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('gossip_audit',root/'contrib/tools/gossip_audit.py');tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    types,events,_=tool.enums(root)
    tables={name:[] for name in tool.TABLES}
    def option(menu,index,type_=None):return dict(MenuId=menu,OptionIndex=index,OptionType=types['GOSSIP_OPTION_GOSSIP'] if type_ is None else type_,OptionNpcFlag=1,OptionText='Тест')
    tables['gossip_menu']=[dict(MenuId=10,TextId=1)]
    tables['gossip_menu_option']=[option(10,0),option(10,1),option(10,2,types['GOSSIP_OPTION_MAX']),option(20,0),option(10,3,types['GOSSIP_OPTION_TRAINER']),option(0,0)]
    tables['gossip_menu_option_action']=[dict(MenuId=10,OptionIndex=0,ActionMenuId=20,ActionPoiId=0),dict(MenuId=10,OptionIndex=1,ActionMenuId=99,ActionPoiId=7),dict(MenuId=10,OptionIndex=999,ActionMenuId=0,ActionPoiId=0)]
    tables['creature_template']=[dict(entry=11,name='NPC',AIName='SmartAI',ScriptName='fixture',gossip_menu_id=10,npcflag=17)]
    tables['npc_trainer']=[dict(ID=11,SpellID=1234)];tables['creature_default_trainer']=[dict(CreatureId=11,TrainerId=18)];tables['trainer']=[dict(Id=18)]
    row=dict(entryorguid=11,source_type=0,id=0,link=0,event_type=events['SMART_EVENT_GOSSIP_SELECT'],event_param1=10,event_param2=0,event_phase_mask=0,event_chance=100,event_flags=0,action_type=1,action_param1=0,action_param2=0,target_type=1,target_param1=0,target_param2=0,comment='test')
    tables['smart_scripts']=[row,dict(row,id=1)]
    tables['conditions']=[dict(SourceTypeOrReferenceId=15,SourceGroup=99,SourceEntry=0,SourceId=0,ElseGroup=0,ConditionTypeOrReference=9,ConditionTarget=0,ConditionValue1=1,ConditionValue2=0,ConditionValue3=0,NegativeCondition=0)]
    # C++ lexical coverage is exercised on a small actual file, with real enum headers.
    with tempfile.TemporaryDirectory() as tmp:
        fixture=Path(tmp)
        for path in ['src/server/game/Entities/Creature/GossipDef.h','src/server/game/AI/SmartScripts/SmartScriptMgr.h','src/server/game/Entities/Unit/UnitDefines.h']:
            dest=fixture/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((root/path).read_bytes())
        cpp=fixture/'src/server/scripts/test.cpp';cpp.parent.mkdir(parents=True,exist_ok=True);cpp.write_text('class X:CreatureScript{X():CreatureScript("fixture"){} bool OnGossipSelect(Player* p,uint32 s,uint32 a) override { ClearGossipMenuFor(p); return true; }};','utf8')
        snapshot=dict(tables=tables,basis='Synthetic audit fixtures, not production')
        original=json.dumps(snapshot,sort_keys=True);report=tool.audit(snapshot,fixture)
        assert json.dumps(snapshot,sort_keys=True)==original,'Audit mutated input'
        find=report['findings']
        assert any(x['category']=='BROKEN_ACTION_MENU' and x['ActionMenuId']==20 and x['status']=='REVIEW_REQUIRED' for x in find)
        assert any(x['category']=='BROKEN_ACTION_MENU' and x['ActionMenuId']==99 and x['status']=='CONFIRMED_DATA_ERROR' for x in find)
        assert any(x['category']=='MISSING_TRAINER' and x['status']=='VALID' for x in find),'Legacy trainer0 wrongly marked broken'
        assert any(x['category']=='DUPLICATE_SMART_EVENT' and x['status']=='REVIEW_REQUIRED' for x in find)
        assert any(x['category']=='SMARTAI_CPP_CONFLICT' and x['cpp_files']==['src/server/scripts/test.cpp'] for x in find)
        assert report['counts']['INVALID_OPTION_TYPE']==1 and report['counts']['ORPHAN_OPTION']==1
        assert report['cpp_hook_counts']=={'OnGossipSelect':1}
        saved=tables['npc_trainer'];tables['npc_trainer']=[]
        assert any(x['category']=='MISSING_TRAINER' and x['status']=='REVIEW_REQUIRED' for x in tool.audit(snapshot,fixture)['findings']),'Default trainer must not falsely validate Gossip trainer0'
        tables['npc_trainer']=saved
        incomplete=copy.deepcopy(snapshot);del incomplete['tables']['trainer'];assert not tool.audit(incomplete,fixture)['complete']
        tables['creature_template'] += [dict(entry=i+100,name='default',AIName='',ScriptName='',gossip_menu_id=0,npcflag=0) for i in range(1000)]
        bounded=tool.audit(snapshot,fixture);defaults=[x for x in bounded['findings'] if x['category']=='DEFAULT_MENU_REVIEW']
        assert len(defaults)==1 and defaults[0]['hidden_template_count']==1000 and len(defaults[0]['creature_examples'])==20
    print('PASS: read-only Gossip audit, enum synchronization, missing schema, default trainer/menu, orphan records, bounded NPC reviews and SmartAI/C++ ambiguity')


if __name__=='__main__':main()
