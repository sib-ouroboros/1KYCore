#!/usr/bin/env python3
"""Read-only BroadcastText WDC1 layout/ID audit, never exports client resources."""
import argparse,hashlib,json,re,struct
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--dbc',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    metadata=(a.root/'src/server/game/DataStores/DB2Metadata.h').read_text('utf8')
    block=re.search(r'struct BroadcastTextMeta\s*\{(.*?)\n\};',metadata,re.S).group(1)
    m=re.search(r'DB2Meta instance\((-?\d+), (\d+), (0x[0-9A-F]+)',block)
    if int(m[1])!=-1:raise ValueError('Unsupported BroadcastText identity field')
    expected_layout=int(m[3],16);results=[]
    for locale in ('enUS','ruRU'):
        path=a.dbc/locale/'BroadcastText.db2';data=path.read_bytes()
        h=struct.unpack_from('<4s10IHh9I',data)
        names=['signature','records','fields','record_size','string_bytes','table_hash','layout_hash','min_id','max_id','locale_mask','copy_bytes','flags','index_field','total_fields','packed_offset','parent_count','catalog_offset','id_bytes','column_bytes','common_bytes','pallet_bytes','parent_bytes']
        header=dict(zip(names,h));valid=header['signature']==b'WDC1' and header['layout_hash']==expected_layout and not(header['flags']&1)
        row={'locale':locale,'relative_file':locale+'/BroadcastText.db2','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'signature':data[:4].decode('ascii'),'layout_hash':hex(header['layout_hash']),'core_layout_validated':valid,'assurance':'layout/header and ID presence only; no text/voice export'}
        if valid:
            start=84+4*header['fields'];end=start+header['records']*header['record_size']+header['string_bytes'];columns=end+header['id_bytes']+header['copy_bytes']
            if header['id_bytes']!=4*header['records'] or len(data)!=columns+header['column_bytes']+header['common_bytes']+header['pallet_bytes']+header['parent_bytes']:raise ValueError('WDC1 size/identity mismatch')
            ids=set(struct.unpack_from('<'+str(header['records'])+'I',data,end))
            for pos in range(end+header['id_bytes'],columns,8):
                new,old=struct.unpack_from('<II',data,pos)
                if old not in ids:raise ValueError('Missing copy source')
                ids.add(new)
            row.update(identity_count=len(ids),contains_27602=27602 in ids)
        results.append(row)
    a.output.write_text(json.dumps(results,sort_keys=True,indent=2)+'\n',encoding='utf8');print('Audited enUS/ruRU BroadcastText metadata only')
if __name__=='__main__':main()
