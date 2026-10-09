#!/usr/bin/env python3
"""Read-only missing-script manifest; static reachability is not runtime proof."""
import argparse
from collections import defaultdict
import hashlib,json,re
from pathlib import Path


def uncomment(text):
    pattern=r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    return re.sub(pattern,lambda m: re.sub(r'[^\n]',' ',m[0]) if m[0].startswith(('//','/*')) else m[0],text)


def functions(text):
    result=[]
    for m in re.finditer(r'\bvoid\s+(AddSC_\w+|Add\w+Scripts)\s*\(\s*\)\s*\{',text):
        start=m.end();depth=1;end=start
        for token in re.finditer(r'"(?:\\.|[^"\\])*"|[{}]',text[start:]):
            if token[0]=='{':depth+=1
            if token[0]=='}':depth-=1
            if not depth:end=start+token.start();break
        if depth:raise ValueError('Unbalanced loader '+m[1])
        result.append((m[1],m.start(),end,text[start:end]))
    return result


def build(root,log):
    files={};definitions=defaultdict(list);calls=defaultdict(set);by_name=defaultdict(list)
    expected={'CreatureScript':['creature_template','creature'],'GameObjectScript':['gameobject_template','gameobject'],'SpellScriptLoader':['spell_script_names'],'InstanceMapScript':['instance_template'],'ConversationScript':['conversation_template'],'SceneScript':['scene_template'],'QuestScript':['quest_template_addon'],'AreaTriggerScript':['areatrigger_scripts'],'AreaTriggerEntityScript':['areatrigger_template']}
    for path in sorted((root/'src/server/scripts').rglob('*.cpp')):
        # ASCII C++ identifiers are scanned losslessly even in legacy non-UTF8 files.
        rel=path.relative_to(root).as_posix();text=uncomment(path.read_bytes().decode('latin1'));funcs=functions(text);files[rel]=(text,funcs)
        for name,start,end,body in funcs:
            definitions[name].append({'source_file':rel,'line':text.count('\n',0,start)+1})
            calls[name].update(re.findall(r'\b(AddSC_\w+|Add\w+Scripts)\s*\(\s*\)\s*;',body))
        for m in re.finditer(r'\b(\w+Script|SpellScriptLoader)\s*\(\s*"([^"]+)"',text):
            by_name[m[2]].append((rel,m[1],m.start()))
        for m in re.finditer(r'\bRegister(?:SpellScript|AuraScript|SpellAndAuraScriptPair|CreatureAI|GameObjectAI)\s*\(\s*(\w+)',text):
            by_name[m[1]].append((rel,'REGISTRATION_MACRO',m.start()))
    roots={name for name in definitions if not name.startswith('AddSC_') and name.endswith('Scripts')};reachable=set();todo=list(roots)
    while todo:
        name=todo.pop()
        if name in reachable:continue
        reachable.add(name);todo.extend(calls[name]-reachable)
    records=[]
    patterns=[('SCRIPT_CPP_NO_DB',r"Script named '([^']+)' does not have a script name assigned"),('SCRIPT_DB_NO_CPP',r"ScriptName '([^']+)' exists in database, but no core script found")]
    for direction,pattern in patterns:
        for name in sorted(set(re.findall(pattern,log))):
            occurrences=[]
            for rel,kind,pos in by_name[name]:
                text,funcs=files[rel];owners=[f[0] for f in funcs if f[1]<=pos<=f[2]]
                if not owners:
                    classes=list(re.finditer(r'\b(?:class|struct)\s+(\w+)',text[:pos]))
                    if classes:
                        cls=classes[-1][1]
                        owners=[f[0] for f in funcs if re.search(r'\bnew\s+'+re.escape(cls)+r'\b',f[3])]
                occurrences.append({'source_file':rel,'module':rel.split('/')[3],'script_type':kind,'line':text.count('\n',0,pos)+1,'AddSC_loaders':owners,'static_loader_reachable':any(x in reachable for x in owners),'DB_binding_table_expected':expected.get(kind,[]),'binary_registration_verified':False})
            records.append({'script_name':name,'direction':direction,'status':'CONFIRMED_BINDING_BUG' if direction=='SCRIPT_CPP_NO_DB' else 'NEEDS_SOURCE_DATA','classification':'MISSING_DB_BINDING' if direction=='SCRIPT_CPP_NO_DB' else ('NEEDS_DONOR_DATA' if not occurrences else 'LOADER_OR_NAME_REQUIRES_RUNTIME_REVIEW'),'source_occurrences':occurrences,'DB_binding_found_in_logged_runtime':direction=='SCRIPT_DB_NO_CPP','target_entry_spell_map':'NEEDS_SOURCE_DATA','expansion':'Legion' if any(x['module'] in ('BrokenIsles','Argus') for x in occurrences) else 'UNVERIFIED'})
    revision=re.search(r'TrinityCore rev\. ([0-9a-f]+)',log)
    return {'schema_version':1,'log_commit':revision[1] if revision else None,'source_scope':'current checkout, static scan; compilation flags and dynamic binary registration not verified','source_sha256':{rel:hashlib.sha256((root/rel).read_bytes()).hexdigest() for rel in files},'loader_definitions':dict(sorted(definitions.items())),'loader_edges':{k:sorted(v) for k,v in sorted(calls.items())},'uncalled_AddSC_definitions':sorted(set(definitions)-reachable),'calls_without_definition':sorted(reachable-set(definitions)),'scripts':records,'counts':{direction:sum(x['direction']==direction for x in records) for direction,_ in patterns}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--log',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=build(a.root,a.log.read_text('utf-8-sig'));a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(json.dumps(result['counts']))


if __name__=='__main__':main()
