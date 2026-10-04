#!/usr/bin/env python3
"""Analyse trusted MySQL dumps and generate optional ruRU CAS patches; never execute SQL."""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys
from sql_dump import DumpError,Table,read_dump
from rules import RULES,HOTFIX_RULES,POI_RULES,selected_tables,projection
from text_checks import CYRILLIC,quality,csv_cell


VERSION='1'
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def column(table,name):
    found=[c for c in table.columns if c.lower()==name.lower()]
    if len(found)!=1:raise DumpError('Required column missing or ambiguous: '+name)
    return found[0]


def get(table,row,name):
    return row.get(column(table,name))


def index(table,keys):
    result=defaultdict(list)
    for row in table.rows.values():result[tuple(get(table,row,k) for k in keys)].append(row)
    return result


def dataset(path,sha,cache=None,rules=RULES):
    # JSON cache is data only. Its checksum and projection/tool sources are part
    # of its identity; no pickle and no code execution on cache reads.
    fingerprint=digest({'version':VERSION,'tables':sorted(selected_tables(rules)),'projection':{k:sorted(v) for k,v in projection(rules).items()},'reader_sha256':hashlib.sha256(Path(__file__).with_name('sql_dump.py').read_bytes()).hexdigest()})
    with Path(path).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=sha:raise DumpError('Input checksum mismatch: '+str(path))
    cache_path=Path(cache)/(sha+'-'+fingerprint+'.json') if cache else None
    if cache_path and cache_path.exists():
        doc=json.loads(cache_path.read_text('utf8'))
        if digest(doc['tables'])!=doc['digest']:raise DumpError('Corrupt dataset cache')
        return {name:Table(info['columns'],info['primary'],info['definition'],{tuple(k):v for k,v in info['rows']},{tuple(k) for k in info['duplicates']},info['limits'],info['defaults']) for name,info in doc['tables'].items()}
    tables,_=read_dump(path,selected_tables(rules),sha,projection(rules))
    if cache_path:
        data={n:{'columns':t.columns,'primary':t.primary,'definition':t.definition,'rows':[[list(k),v] for k,v in t.rows.items()],'duplicates':sorted(t.duplicates),'limits':t.limits,'defaults':t.defaults} for n,t in tables.items()}
        cache_path.parent.mkdir(parents=True,exist_ok=True)
        cache_path.write_text(json.dumps({'tables':data,'digest':digest(data)},ensure_ascii=False),encoding='utf8')
    return tables


def validate_rule(rule,target,source):
    for name in (rule.target,rule.base_target):
        if name not in target:raise DumpError('Missing target table '+name)
    for name in (rule.source,rule.base_source):
        if name not in source:return False
    for t,keys,fields in ((target[rule.target],rule.keys_target,[f[0] for f in rule.fields]),(source[rule.source],rule.keys_source,[f[1] for f in rule.fields]),(target[rule.base_target],rule.base_keys_target,[f[2] for f in rule.fields]+[f[0] for f in rule.identity]),(source[rule.base_source],rule.base_keys_source,[f[3] for f in rule.fields]+[f[1] for f in rule.identity])):
        for name in keys+tuple(fields):column(t,name)
    locale=target[rule.target]
    expected={column(locale,k) for k in rule.keys_target}
    if rule.locale:expected.add(column(locale,rule.locale))
    if set(locale.primary)!=expected:raise DumpError('Unsupported target locale primary key: '+rule.target)
    return True


def parent_identity(quest_id,target,source):
    tt,st=target['quest_template'],source['quest_template']
    a=tt.rows.get((quest_id,));b=st.rows.get((quest_id,))
    if not a or not b:return False
    return all(get(tt,a,k)==get(st,b,k) for k in ('LogTitle','QuestType','QuestSortID'))


def page_chain(key,target,source):
    tt,st=target['page_text'],source['page_text'];seen=set()
    while key!='0':
        if key in seen:return False
        seen.add(key);a=tt.rows.get((key,));b=st.rows.get((key,))
        if not a or not b:return False
        if any(get(tt,a,k)!=get(st,b,k) for k in ('Text','NextPageID')):return False
        key=get(tt,a,'NextPageID')
    return True


def analyse(target,source,source_sha,rules=RULES):
    records=[];changes=[];coverage={}
    for rule in rules:
        available=validate_rule(rule,target,source)
        tt=target[rule.target];bt=target[rule.base_target]
        targets=index(bt,rule.base_keys_target);locals_t=index(tt,rule.keys_target)
        if available:
            sl=source[rule.source];bs=source[rule.base_source]
            locals_s=index(sl,rule.keys_source);sources=index(bs,rule.base_keys_source)
        totals=Counter()
        for key,variants in sorted(targets.items()):
            local=locals_t.get(key,[])
            target_row=local[0] if len(local)==1 else None
            base=variants[0]
            for dest,donor,english_dest,english_source in rule.fields:
                original=get(bt,base,english_dest)
                if not original:totals['empty_english_excluded']+=1;continue
                totals['english_fields_in_current_db']+=1
                current=get(tt,target_row,dest) if target_row else None
                status='insufficient_data';reason='donor table missing';proposal=None;english_donor=None;donor_row=None
                if available:
                    sr=locals_s.get(key,[]);br=sources.get(key,[])
                    if len(sr)==1:
                        proposal=get(sl,sr[0],donor);donor_row=sr[0]
                    if len(br)==1:english_donor=get(bs,br[0],english_source)
                if current is not None and current.strip() and current!=original:
                    status='existing_translation_conflict';reason='preserve existing nonempty text (Cyrillic is not a quality verdict)'
                    totals['existing_cyrillic' if CYRILLIC.search(current) else 'existing_nonempty_unreviewed']+=1
                elif available:
                    srows=locals_s.get(key,[]);bases=sources.get(key,[])
                    if len(srows)!=1 or len(bases)!=1 or len(variants)!=1 or len(local)>1:
                        reason='missing or ambiguous locale/base row';status='manual_review' if srows or len(variants)>1 else 'insufficient_data'
                    else:
                        donor_row=srows[0];source_base=bases[0]
                        proposal=get(sl,donor_row,donor);english_donor=get(bs,source_base,english_source)
                        source_key=tuple(donor_row[c] for c in sl.primary)
                        base_source_key=tuple(source_base[c] for c in bs.primary)
                        target_key=tuple(target_row[c] for c in tt.primary) if target_row else None
                        identity=all(get(bt,base,a)==get(bs,source_base,b) for a,b in rule.identity)
                        if rule.category in ('rewards','requests'):
                            identity=identity and parent_identity(key[0],target,source)
                        if rule.category=='objectives':
                            identity=identity and parent_identity(get(bt,base,'QuestID'),target,source)
                            identity=identity and get(sl,donor_row,'QuestId')==get(bs,source_base,'QuestID') and get(sl,donor_row,'StorageIndex')==get(bs,source_base,'StorageIndex')
                        if rule.category=='pages':identity=identity and page_chain(key[0],target,source)
                        if source_key in sl.duplicates or base_source_key in bs.duplicates or target_key in tt.duplicates:
                            status='manual_review';reason='duplicate dump key'
                        elif original!=english_donor or not identity:
                            status='manual_review';reason='English field or semantic identity differs'
                        elif (problem:=quality(original,proposal,tt.limits.get(column(tt,dest)),rule.mode)):
                            status='invalid_source';reason=problem
                        else:
                            status='automatic';reason='exact English field and semantic identity; '+('documented exact English copy' if current==original else 'empty target field')
                            totals['accepted_fields']+=1
                            guard_fields={column(bt,english_dest):original}
                            guard_fields.update({column(bt,a):get(bt,base,a) for a,b in rule.identity})
                            guards=[{'table':rule.base_target,'key':{column(bt,k):key[i] for i,k in enumerate(rule.base_keys_target)},'fields':guard_fields}]
                            if rule.category in ('rewards','requests','objectives'):
                                qid=get(bt,base,'QuestID') if rule.category=='objectives' else key[0]
                                qb=target['quest_template'];q=qb.rows[(qid,)]
                                guards.append({'table':'quest_template','key':{'ID':qid},'fields':{column(qb,k):get(qb,q,k) for k in ('LogTitle','QuestType','QuestSortID')}})
                            if rule.category=='pages':
                                next_id=get(bt,base,'NextPageID');seen=set()
                                while next_id!='0' and next_id not in seen:
                                    seen.add(next_id);p=bt.rows[(next_id,)]
                                    guards.append({'table':'page_text','key':{'ID':next_id},'fields':{k:get(bt,p,k) for k in ('Text','NextPageID')}});next_id=get(bt,p,'NextPageID')
                            seeds={}
                            if rule.category=='objectives':seeds={column(tt,'QuestId'):get(bt,base,'QuestID'),column(tt,'StorageIndex'):get(bt,base,'StorageIndex')}
                            locale_key={column(tt,k):key[i] for i,k in enumerate(rule.keys_target)}
                            if rule.locale:locale_key[column(tt,rule.locale)]='ruRU'
                            changes.append({'category':rule.category,'table':rule.target,'key':locale_key,'field':column(tt,dest),'before':current,'after':proposal,'row_before':target_row,'seed':seeds,'guards':guards,'source':{'table':rule.source,'field':column(sl,donor),'key':dict(zip(sl.primary,source_key)),'dump_sha256':source_sha,'row_sha256':digest(donor_row),'english_sha256':digest(english_donor),'proposal_sha256':digest(proposal)}})
                records.append({'category':rule.category,'table':rule.target,'key':list(key),'field':dest,'english':original,'donor_english':english_donor,'current':current,'proposal':proposal,'status':status,'reason':reason,'source_sha256':source_sha,'current_hash':digest(current),'proposal_hash':digest(proposal)})
        # Donor-only entities are recorded separately; never add gameplay entities.
        if available:
            for key in sorted(set(locals_s)-set(targets)):
                records.append({'category':rule.category,'table':rule.target,'key':list(key),'field':None,'english':None,'donor_english':None,'current':None,'proposal':None,'status':'entity_absent','reason':'no target base entity','source_sha256':source_sha,'current_hash':digest(None),'proposal_hash':digest(None)})
        totals['remaining_fields']=totals['english_fields_in_current_db']-totals['existing_cyrillic']-totals['existing_nonempty_unreviewed']-totals['accepted_fields']
        coverage[rule.category]=dict(sorted(totals.items()))
    return records,changes,coverage


def sql_value(value):
    if value is None:return 'NULL'
    if value=='':return "''"
    return 'CONVERT(0x'+str(value).encode('utf8').hex()+' USING utf8mb4)'


def equals(fields,alias=''):
    return ' AND '.join(f"BINARY {alias}`{k}` <=> BINARY {sql_value(v)}" for k,v in fields.items())


def key_equals(fields):
    # Use the native PK index first. BINARY alone can force a full scan for every
    # translated field; retain it as the exact/case-sensitive ownership check.
    native=' AND '.join(f'`{k}` <=> {sql_value(v)}' for k,v in fields.items())
    return native+' AND '+equals(fields)


GUARD='`_1kycore_ru_localization_guard`'
PREAMBLE="SET NAMES utf8mb4;\nCREATE TEMPORARY TABLE IF NOT EXISTS "+GUARD+" (`ok` TINYINT PRIMARY KEY) ENGINE=MEMORY;\nINSERT IGNORE INTO "+GUARD+" VALUES (1);\n"
def refusal(condition):
    return f'INSERT INTO {GUARD} SELECT 1 WHERE {condition};\n'


def schema_guard(name,table):
    cols=','.join(sql_value(c) for c in table.columns)
    lines=[refusal(f"(SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(name)} AND COLUMN_NAME IN ({cols}))<>{len(table.columns)} OR (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(name)})<>{len(table.columns)}")]
    for order,key in enumerate(table.primary,1):
        lines.append(refusal(f"NOT EXISTS (SELECT 1 FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(name)} AND CONSTRAINT_NAME='PRIMARY' AND COLUMN_NAME={sql_value(key)} AND ORDINAL_POSITION={order})"))
    lines.append(refusal(f"(SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(name)} AND CONSTRAINT_NAME='PRIMARY')<>{len(table.primary)}"))
    return ''.join(lines)


def packages(target,changes,output):
    # A saved/reloaded review plan must yield exactly the same bytes as direct
    # analysis. Canonicalize nested mapping order before composing SQL clauses.
    changes=json.loads(json.dumps(changes,ensure_ascii=False,sort_keys=True))
    grouped=defaultdict(lambda:defaultdict(list))
    for change in changes:grouped[change['category']][tuple(change['key'].values())].append(change)
    manifest=[]
    for category,rows in sorted(grouped.items()):
        rows=list(rows.values())
        for number,start in enumerate(range(0,len(rows),100),1):
            batch=rows[start:start+100];name=f'{category}-{number:03d}';table_name=batch[0][0]['table'];table=target[table_name]
            apply=[f'-- Optional ruRU package {name}; do not put in sql/updates.\n',PREAMBLE,schema_guard(table_name,table)]
            rollback=[f'-- Exact guarded rollback of optional package {name}.\n',PREAMBLE,schema_guard(table_name,table)]
            writes=[];undo=[];evidence=[]
            for fields in batch:
                first=fields[0];key=first['key'];where=key_equals(key);before=first['row_before']
                final=dict(before) if before else dict(table.defaults)|key|first['seed']
                final.update({c['field']:c['after'] for c in fields})
                if before is None and set(final)!=set(table.columns):raise DumpError('Cannot safely seed/rollback required default columns of '+table_name)
                for change in fields:
                    if change['field'] not in table.limits:raise DumpError('Patch destination is not a text field')
                    apply.append(refusal(f"NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(table_name)} AND COLUMN_NAME={sql_value(change['field'])} AND DATA_TYPE IN ('char','varchar','text','mediumtext','longtext'))"))
                    apply.append(refusal(f"NOT EXISTS (SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME={sql_value(table_name)} AND COLUMN_NAME={sql_value(change['field'])} AND CHARACTER_SET_NAME IN ('utf8','utf8mb3','utf8mb4') AND CHARACTER_MAXIMUM_LENGTH>=CHAR_LENGTH({sql_value(change['after'])}) AND CHARACTER_OCTET_LENGTH>=OCTET_LENGTH({sql_value(change['after'])}))"))
                    for guard in change['guards']:
                        condition=f"SELECT 1 FROM `{guard['table']}` WHERE {key_equals(guard['key'])}"
                        if guard.get('absent'):apply.append(refusal(f'EXISTS ({condition})'))
                        else:apply.append(refusal(f"NOT EXISTS ({condition} AND {equals(guard['fields'])})"))
                if before is None:
                    # Native PK equality catches case-insensitive locale collisions
                    # and tables whose PK does not include the locale column.
                    native_key=' AND '.join(f'`{k}` <=> {sql_value(final[k])}' for k in table.primary)
                    apply.append(refusal(f'EXISTS (SELECT 1 FROM `{table_name}` WHERE {native_key} AND NOT ({equals(final)}))'))
                    rollback.append(refusal(f'EXISTS (SELECT 1 FROM `{table_name}` WHERE {native_key} AND NOT ({equals(final)}))'))
                    writes.append(f"INSERT INTO `{table_name}` ({','.join('`'+c+'`' for c in table.columns)}) SELECT {','.join(sql_value(final[c]) for c in table.columns)} WHERE NOT EXISTS (SELECT 1 FROM `{table_name}` WHERE {where});\n")
                    undo.append(f'DELETE FROM `{table_name}` WHERE {where} AND {equals(final)};\n')
                else:
                    apply.append(refusal(f'NOT EXISTS (SELECT 1 FROM `{table_name}` WHERE {where})'))
                    rollback.append(refusal(f'NOT EXISTS (SELECT 1 FROM `{table_name}` WHERE {where})'))
                    for change in fields:
                        either=f"({equals({change['field']:change['before']})}) OR ({equals({change['field']:change['after']})})"
                        apply.append(refusal(f'EXISTS (SELECT 1 FROM `{table_name}` WHERE {where} AND NOT ({either}))'))
                        rollback.append(refusal(f'EXISTS (SELECT 1 FROM `{table_name}` WHERE {where} AND NOT ({either}))'))
                    writes.append(f"UPDATE `{table_name}` SET "+','.join('`'+c['field']+'`='+sql_value(c['after']) for c in fields)+f' WHERE {where};\n')
                    undo.append(f"UPDATE `{table_name}` SET "+','.join('`'+c['field']+'`='+sql_value(c['before']) for c in fields)+f' WHERE {where};\n')
                evidence.append({'key':key,'inserted':before is None,'before':{c['field']:c['before'] for c in fields},'row_after_sha256':digest(final),'after_hashes':{c['field']:digest(c['after']) for c in fields},'sources':[c['source'] for c in fields]})
            # All preflight guards precede permanent writes. Tables may be MyISAM;
            # this is interruption recovery, not a claim of transactional rollback.
            for suffix,parts in (('apply',apply+writes),('rollback',rollback+undo)):
                (output/(name+'.'+suffix+'.sql')).write_text(''.join(parts),encoding='utf8',newline='\n')
            manifest.append({'name':name,'table':table_name,'rows':len(batch),'fields':sum(map(len,batch)),'evidence':evidence,'apply_sha256':hashlib.sha256((output/(name+'.apply.sql')).read_bytes()).hexdigest(),'rollback_sha256':hashlib.sha256((output/(name+'.rollback.sql')).read_bytes()).hexdigest()})
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','target','source-sha256','target-sha256','output'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--cache',help='Optional external data-only JSON cache directory (never commit dumps/cache).')
    parser.add_argument('--database',choices=('world','hotfix','poi'),default='world',help='Separate text allowlists; poi is a supplemental world snapshot.')
    args=parser.parse_args()
    try:
        rules={'world':RULES,'hotfix':HOTFIX_RULES,'poi':POI_RULES}[args.database]
        target=dataset(args.target,args.target_sha256,args.cache,rules);source=dataset(args.source,args.source_sha256,args.cache,rules)
        records,changes,coverage=analyse(target,source,args.source_sha256,rules)
        if args.database=='world':
            from gossip import analyse_gossip
            gr,gc,cv=analyse_gossip(target,source,args.source_sha256)
            records+=gr;changes+=gc;coverage['gossip']=cv
        output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
        patch_dir=output/'packages';patch_dir.mkdir(exist_ok=True)
        if any(patch_dir.iterdir()):raise DumpError('Package output directory must be empty; avoid stale files')
        manifest=packages(target,changes,patch_dir)
        (output/'candidates.json').write_text(json.dumps(records,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
        with (output/'candidates.csv').open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(records[0]) if records else [])
            writer.writeheader()
            for row in records:writer.writerow({k:csv_cell(json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v) for k,v in row.items()})
        summary={'source_sha256':args.source_sha256,'target_sha256':args.target_sha256,'coverage':coverage,'classifications':dict(sorted(Counter(r['status'] for r in records).items())),'accepted_fields':len(changes),'packages':len(manifest),'scope':'Current DB English text fields with target entities; in-game accessibility and translation linguistics not proven.'}
        (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
        (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
    except (DumpError,UnicodeError,OSError,ValueError) as error:
        parser.exit(1,'ERROR: '+str(error)+'\n')


if __name__=='__main__':main()
