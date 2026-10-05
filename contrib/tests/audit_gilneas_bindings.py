#!/usr/bin/env python3
"""Read-only Gilneas registration/binding audit; never infer entries from class suffixes.

Snapshot input uses creature_template/gameobject_template/spell_script_names and optional
creature/gameobject arrays (JSON dictionaries with ScriptName and entry/id/guid fields).
--require-all is deliberately optional: missing bindings require a behavior audit first.
"""
import argparse,json,re
from pathlib import Path
from test_gilneas_quests import method
ROOT=Path(__file__).resolve().parents[2]

def registered_scripts():
 result=[]
 for name in ('duskhaven','gilneas_city2','gilneas_city3'):
  path=ROOT/'src/server/scripts/EasternKingdoms/Gilneas'/('zone_'+name+'.cpp')
  text=path.read_text('utf8');loader='AddSC_zone_gilneas_duskhaven' if name=='duskhaven' else 'AddSC_zone_'+name
  body=method(text,'void '+loader+'()');registered=set(re.findall(r'new\s+(\w+)\s*\(',body))
  definitions=list(re.finditer(r'class\s+(\w+)\s*:\s*public\s+(CreatureScript|GameObjectScript|SpellScriptLoader)',text))
  for i,m in enumerate(definitions):
   segment=text[m.end():definitions[i+1].start() if i+1<len(definitions) else len(text)]
   constructor=re.search(m[2]+r'\s*\(\s*"([^"\n]+)"\s*\)',segment)
   if not constructor:raise ValueError('Missing literal ScriptName for '+m[1])
   result.append({'file':path.name,'class':m[1],'kind':m[2],'script':constructor[1],'registered':m[1] in registered})
 return result

def audit(snapshot):
 report=[]
 for definition in registered_scripts():
  tables={'CreatureScript':('creature_template','creature'),'GameObjectScript':('gameobject_template','gameobject'),'SpellScriptLoader':('spell_script_names',)}[definition['kind']]
  bindings=[]
  for table in tables:
   for row in snapshot.get(table,[]):
    if row.get('ScriptName')==definition['script']:
     bindings.append({'table':table,'key':row.get('entry',row.get('spell_id',row.get('guid'))),'AIName':row.get('AIName')})
  report.append(dict(definition,bindings=bindings,status='BOUND' if definition['registered'] and bindings else 'MISSING_BINDING' if definition['registered'] else 'NOT_REGISTERED'))
 return report

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--snapshot',type=Path);parser.add_argument('--require-all',action='store_true');args=parser.parse_args()
 if not args.snapshot:
  scripts=registered_scripts();assert all(s['registered'] for s in scripts),'Unregistered C++ class';print(json.dumps(scripts,indent=2));return
 report=audit(json.loads(args.snapshot.read_text('utf8')));print(json.dumps(report,indent=2))
 if args.require_all and any(r['status']!='BOUND' for r in report):raise SystemExit(1)
if __name__=='__main__':main()
