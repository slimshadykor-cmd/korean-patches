from audit import *
import io,hashlib,gzip,shutil
from PIL import Image,ImageFont,ImageDraw
R=W.parent/'release_v128';sha=lambda b:hashlib.sha256(b).hexdigest()
base_records=json.loads((A/'v126/audit/glyph_mapping.json').read_text());aliases=json.loads((W/'font_alias_validation.json').read_text())['verified_aliases']
reverse={bytes.fromhex(r['cp932_hex']):r['korean'] for r in base_records+aliases};mapping={r['korean']:bytes.fromhex(r['cp932_hex']) for r in base_records}
for r in aliases:mapping.setdefault(r['korean'],bytes.fromhex(r['cp932_hex']))
fixes=json.loads((W/'corrections.json').read_text());fixes={k:v.replace(' ','　') for k,v in fixes.items()}
missing=sorted({c for t in fixes.values() for c in t if '\uac00'<=c<='\ud7a3'}-mapping.keys())
font=(A/'current/Media/Sys/font.bin').read_bytes();out=bytearray(font);entries={}
for i in range(22):
 at,n,np=struct.unpack_from('>III',font,i*12);name=font[np:font.index(0,np)].decode();entries[int(name[1:3],16)]=(i,at,n)
# Eligible carriers were absent from original initialized text regions. Also reserve all existing Korean aliases.
eligible=[bytes.fromhex(s) for s in json.loads((A/'workbench/analysis/ingame_v006/eligible_glyphs.json').read_text())]
original=(A/'original.memory.bin').read_bytes()
available=[x for x in eligible if x not in reverse and x[0]>=0x8e and x not in original[0x600:0xaa4b4] and x not in original[0x690000:0x738000]]
assert len(available)>=len(missing)
f=ImageFont.truetype(str(R/'dependencies/NotoSansCJKkr-Regular.otf'),30);allowed=set();added=[]
for char,code in zip(missing,available):
 lead,trail=code;i,at,n=entries[lead];mapping[char]=code;reverse[code]=char
 cell=Image.new('RGBA',(32,32),(255,255,255,0));d=ImageDraw.Draw(cell);a,b,z,h=d.textbbox((0,0),char,font=f);d.text(((32-z+a)//2-a,(32-h+b)//2-b),char,font=f,fill='white')
 buf=io.BytesIO();cell.save(buf,format='DDS',pixel_format='DXT5');data=buf.getvalue()[128:];x=(trail-0x40)%16*32;y=(trail-0x40)//16*32
 for by in range(8):
  off=at+128+((y//4+by)*128+x//4)*16;out[off:off+128]=data[by*128:(by+1)*128];allowed.update(range(off,off+128))
 im=Image.open(io.BytesIO(out[at:at+n])).convert('RGBA');box=im.crop((x,y,x+32,y+32)).getchannel('A').point(lambda a:255 if a>=32 else 0).getbbox();assert box and min(box[:2])>=1 and max(box[2:])<=31
 added.append(dict(korean=char,cp932_hex=code.hex().upper(),atlas=i,x=x,y=y,decoded_ink_bounds=box))
assert len(out)==len(font) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(font,out)))
# Existing game-font cells, including 50 legacy aliases, remain exactly byte-identical.
for code,char in {bytes.fromhex(r['cp932_hex']):r['korean'] for r in base_records+aliases}.items():
 lead,trail=code;i,at,n=entries[lead];x=(trail-0x40)%16*32;y=(trail-0x40)//16*32
 for by in range(8):
  off=at+128+((y//4+by)*128+x//4)*16;assert out[off:off+128]==font[off:off+128]
C=W/'changed';(C/'Media/Sys').mkdir(parents=True,exist_ok=True);(C/'Media/Sys/font.bin').write_bytes(out)
(W/'glyph_mapping.json').write_text(json.dumps(base_records+aliases+added,ensure_ascii=False,indent=2))
def enc(s):return b''.join(mapping[c] if c in mapping else c.encode('cp932') for c in s)
def dec(raw):
 raw=bytes(raw);s='';i=0
 while i<len(raw):
  n=2 if 0x81<=raw[i]<=0x9f or 0xe0<=raw[i]<=0xfc else 1;v=raw[i:i+n];s+=reverse.get(v,v.decode('cp932'));i+=n
 return s
changes=[];verified=[]
for rec in json.loads((A/'evidence/demo_structure_audit.json').read_text()):
 name=rec['file'];b=(A/'current/Media/Demo'/name).read_bytes();new=bytearray(b);lo,hi=map(lambda x:int(x,16),rec['text_pool']);base=struct.unpack_from('>I',b)[0];start,stride,count,tail=struct.unpack_from('>IIII',b,base);texts=[];changed=False
 for row in rec['dialogue_records']:
  at=int(row['current_text_offset'],16);raw=b[at:b.index(0,at)];key=name+'/'+str(row['record']);s=dec(raw)
  if key in fixes:
   target=fixes[key];raw=enc(target);assert dec(raw)==target
   changes.append(dict(file=name,record=row['record'],japanese=row['original'],before=s,after=target));changed=True
  else:target=s
  texts.append((row['record'],raw,target));verified.append(dict(file=name,record=row['record'],japanese=row['original'],korean=target))
 if not changed:continue
 new[lo:hi]=bytes(hi-lo);cursor=lo;shared={}
 for i,raw,target in texts:
  if raw not in shared:
   assert cursor+len(raw)+1<=hi,(name,cursor,len(raw),hi);shared[raw]=cursor;new[cursor:cursor+len(raw)+1]=raw+b'\0';cursor+=len(raw)+1
  struct.pack_into('>I',new,base+start+i*stride+16,shared[raw]-lo)
  pos=lo+struct.unpack_from('>I',new,base+start+i*stride+16)[0];assert dec(new[pos:new.index(0,pos)])==target
 # All archive metadata, speakers, timings, animations and non-dialogue entries unchanged.
 mask=set(range(lo,hi))
 for i,_,_ in texts:mask.update(range(base+start+i*stride+16,base+start+i*stride+20))
 assert len(new)==len(b) and all(a==bb or i in mask for i,(a,bb) in enumerate(zip(b,new)))
 p=C/'Media/Demo'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
assert len(changes)==len(fixes) and len(verified)==411
(W/'dialogue_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));(W/'dialogue_verified.json').write_text(json.dumps(verified,ensure_ascii=False,indent=2))
# Copy the already released package, preserving all unrelated assets including movies.
P=W/'package';shutil.copytree(R/'package',P,dirs_exist_ok=True)
rows={r[0]:r for l in (P/'manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
for p in C.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(C).as_posix();row=rows[rel];data=p.read_bytes();assert len(data)==int(row[1]);oldhash=row[2];row[2]=sha(data);row[3]=','.join(dict.fromkeys(row[3].split(',')+[oldhash]));assert row[5]=='delta'
 # Preserve every previously supported input by retaining all inherited write ranges.
 import numpy as np
 previous=gzip.decompress((R/'package/payload'/row[4]).read_bytes());magic,size,count=struct.unpack_from('<4sII',previous);assert magic==b'OPD1' and size==len(data)
 mask=np.zeros(size,dtype=bool);pos=12
 for _ in range(count):
  off,n=struct.unpack_from('<II',previous,pos);pos+=8;mask[off:off+n]=True;pos+=n
 assert pos==len(previous)
 baseline=(A/'current'/rel).read_bytes();mask|=np.frombuffer(baseline,'u1')!=np.frombuffer(data,'u1')
 edges=np.flatnonzero(np.diff(np.concatenate(([False],mask,[False])).astype('i1')));ranges=list(zip(edges[::2],edges[1::2]));packed=bytearray(struct.pack('<4sII',b'OPD1',len(data),len(ranges)))
 for start,end in ranges:packed.extend(struct.pack('<II',int(start),int(end-start)));packed.extend(data[start:end])
 (P/'payload'/row[4]).write_bytes(gzip.compress(packed,compresslevel=9,mtime=0))
(P/'manifest.tsv').write_text('# path\tresult_size\tresult_sha256\taccepted_original_sha256\tpayload\tmode\trequired\n'+'\n'.join('\t'.join(r) for r in rows.values())+'\n')
report=dict(changed_dialogues=len(changes),changed_demo_files=len({r['file'] for r in changes}),reviewed_dialogues=411,mission_files=86,mission_messages=55,new_glyphs=added,preserved_font_cells=len(base_records)+len(aliases),font_size_unchanged=True,non_dialogue_data_unchanged=True,version='1.2.8',actual_xenia_gameplay_tested=False)
(W/'changes_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
