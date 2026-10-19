from pathlib import Path
import json,struct
W=Path(__file__).resolve().parent; A=W.parent/'audit_identifiers_20261019'
mapping={bytes.fromhex(r['cp932_hex']):r['korean'] for r in json.loads((A/'v126/audit/glyph_mapping.json').read_text())}
for r in json.loads((A/'previous_audit/evidence/font_alias_validation.json').read_text())['verified_aliases']: mapping.setdefault(bytes.fromhex(r['cp932_hex']),r['korean'])
def decode(b):
 out='';i=0
 while i<len(b):
  n=2 if 0x81<=b[i]<=0x9f or 0xe0<=b[i]<=0xfc else 1;v=b[i:i+n];out+=mapping.get(v,v.decode('cp932',errors='replace'));i+=n
 return out
if __name__=='__main__':
 rows=[]
 for p in sorted((A/'mission/Media/Mission').glob('*.xmg')):
  o=p.read_bytes();q=A/'current/Media/Mission'/p.name;c=q.read_bytes() if q.exists() else o
  start,count=struct.unpack_from('>II',o,0x38)
  for i in range(count):
   at=start+i*0x110;raw=c[at:at+256].split(b'\0')[0];old=o[at:at+256].split(b'\0')[0]
   if raw:rows.append(dict(file=p.name,record=i,original=old.decode('cp932',errors='replace'),current=decode(raw),raw=raw.hex()))
 (W/'mission_review.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 (W/'mission_review.txt').write_text('\n'.join(f"{i} {r['file']}/{r['record']}\n{r['original']}\n{r['current'].replace(chr(0x3000),' ')}\n" for i,r in enumerate(rows)))
 print('mission messages',len(rows),'files',len(list((A/'mission/Media/Mission').glob('*.xmg'))))
 x=json.load(open(W.parent/'other_patch_compare_20261019/attribution_independent_comparison.json'))
 (W/'xex_review.txt').write_text('\n'.join(f"{r['index']} {r['offset']}\n{r['original']}\n{r['ours']}\n" for r in x))
