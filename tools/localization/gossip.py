"""Direct gossip locale import with verified menu/option/NPC/action binding.

Donor GossipData.cpp loads locale (MenuID, ID) into MAKE_PAIR32; its base
uses (MenuID, OptionIndex). Target locale PK omits Locale: preserve foreign rows.
Broadcast-backed fields deliberately belong to the separate hotfix route.
"""
from collections import Counter,defaultdict
from localize import get,column,digest
from text_checks import quality,CYRILLIC
from sql_dump import DumpError

def analyse_gossip(target,source,sha):
    names=('gossip_menu_option','gossip_menu_option_locale')
    if any(n not in target or n not in source for n in names):
        return [],[],{'unavailable_tables':1}
    bt,tt=map(target.get,names);bs,sl=map(source.get,names)
    if tt.primary!=['MenuId','OptionIndex']:
        raise DumpError('Unsupported gossip locale PK')
    for table,cols in ((tt,('MenuId','OptionIndex','Locale','OptionText','BoxText')),
                       (sl,('MenuID','ID','Locale','OptionText','BoxText'))):
        for c in cols:column(table,c)
    owners=defaultdict(list)
    npc_t=target['creature_template'];npc_s=source['creature_template'];wdb=source['creature_template_wdb']
    for key,row in npc_t.rows.items():
        src=npc_s.rows.get(key);name=wdb.rows.get(key)
        if src and name and get(npc_t,row,'gossip_menu_id')==get(npc_s,src,'gossip_menu_id') and get(npc_t,row,'name')==get(wdb,name,'Name1'):
            owners[get(npc_t,row,'gossip_menu_id')].append((key,row))
    donor_locale=defaultdict(list)
    for row in sl.rows.values():donor_locale[(get(sl,row,'MenuID'),get(sl,row,'ID'))].append(row)
    out=[];changes=[];counts=Counter()
    for key,base in sorted(bt.rows.items()):
        sb=bs.rows.get(key);loc=tt.rows.get(key);lr=donor_locale.get(key,[])
        action=target['gossip_menu_option_action'].rows.get(key)
        box=target['gossip_menu_option_box'].rows.get(key)
        foreign=loc and get(tt,loc,'Locale')!='ruRU'
        semantic=bool(sb and owners.get(key[0]))
        guards=[{'table':'gossip_menu_option','key':{'MenuId':key[0],'OptionIndex':key[1]},'fields':dict(base)}]
        if semantic:
            semantic=all(get(bt,base,a)==get(bs,sb,b) for a,b in (('OptionType','OptionType'),('OptionNpcFlag','OptionNpcflag'),('OptionIcon','OptionNPC')))
            semantic=semantic and get(bs,sb,'OptionNpcflag2')=='0' and get(bs,sb,'BoxCurrency')=='0'
            for a,b in (('ActionMenuId','ActionMenuID'),('ActionPoiId','ActionPoiID')):
                semantic=semantic and (action[a] if action else '0')==get(bs,sb,b)
            owner_key,owner=sorted(owners[key[0]])[0]
            guards.append({'table':'creature_template','key':{'entry':owner_key[0]},'fields':{'gossip_menu_id':key[0],'name':get(npc_t,owner,'name')}})
        for name,row in (('gossip_menu_option_action',action),('gossip_menu_option_box',box)):
            guards.append({'table':name,'key':{'MenuId':key[0],'OptionIndex':key[1]},'fields':dict(row or {}),'absent':row is None})
        for field in ('OptionText','BoxText'):
            original=get(bt,base,field) if field=='OptionText' else (box['BoxText'] if box else '')
            if not original:counts['empty_english_excluded']+=1;continue
            counts['english_fields_in_current_db']+=1
            current=get(tt,loc,field) if loc and not foreign else None
            donor=lr[0] if len(lr)==1 else None
            proposal=get(sl,donor,field) if donor else None
            english=get(bs,sb,field) if sb else None
            status='manual_review';reason='ambiguous/missing owner, locale or transition'
            if current and current.strip() and current!=original:
                status='existing_translation_conflict';reason='preserve existing nonempty text'
                counts['existing_cyrillic' if CYRILLIC.search(current) else 'existing_nonempty_unreviewed']+=1
            elif foreign:reason='native PK already belongs to another locale; preserve it'
            elif not donor or not sb:status='insufficient_data';reason='missing corresponding donor locale/base'
            elif semantic and original==english:
                broadcast=get(bt,base,'OptionBroadcastTextId') if field=='OptionText' else (box['BoxBroadcastTextId'] if box else '0')
                same_box=field!='BoxText' or all((box[a] if box else '0')==get(bs,sb,a) for a in ('BoxCoded','BoxMoney'))
                if broadcast!='0' or get(bs,sb,field.replace('Text','BroadcastTextID'))!='0':reason='BroadcastText priority; separate hotfix route'
                elif not same_box:reason='confirmation metadata differs'
                elif key in bt.duplicates or key in tt.duplicates or key in bs.duplicates or tuple(donor[c] for c in sl.primary) in sl.duplicates:reason='duplicate dump key'
                elif (problem:=quality(original,proposal,tt.limits.get(field))):status='invalid_source';reason=problem
                else:
                    status='automatic';reason='exact English; same NPC, menu option and transition; no BroadcastText'
                    counts['accepted_fields']+=1
                    changes.append({'category':'gossip','table':'gossip_menu_option_locale','key':{'MenuId':key[0],'OptionIndex':key[1],'Locale':'ruRU'},'field':field,'before':current,'after':proposal,'row_before':loc,'seed':{},'guards':guards,'source':{'table':'gossip_menu_option_locale','field':field,'key':{c:donor[c] for c in sl.primary},'dump_sha256':sha,'row_sha256':digest(donor),'english_sha256':digest(english),'proposal_sha256':digest(proposal)}})
            out.append({'category':'gossip','table':'gossip_menu_option_locale','key':list(key),'field':field,'english':original,'donor_english':english,'current':current,'proposal':proposal,'status':status,'reason':reason,'source_sha256':sha,'current_hash':digest(current),'proposal_hash':digest(proposal)})
    for key in sorted(set(donor_locale)-set(bt.rows)):
        out.append({'category':'gossip','table':names[1],'key':list(key),'field':None,'english':None,'donor_english':None,'current':None,'proposal':None,'status':'entity_absent','reason':'no target base option','source_sha256':sha,'current_hash':digest(None),'proposal_hash':digest(None)})
    counts['remaining_fields']=counts['english_fields_in_current_db']-counts['existing_cyrillic']-counts['existing_nonempty_unreviewed']-counts['accepted_fields']
    return out,changes,dict(sorted(counts.items()))
