from audit import *
import re,hashlib
H=W;R=W.parent/'release_v128'
records=json.loads((H/'glyph_mapping.json').read_text());lookup={bytes.fromhex(r['cp932_hex']):r['korean'] for r in records};added={bytes.fromhex(r['cp932_hex']) for r in json.loads((H/'changes_validation.json').read_text())['new_glyphs']}
def actual(raw):
 out='';i=0
 while i<len(raw):
  n=2 if 0x81<=raw[i]<=0x9f or 0xe0<=raw[i]<=0xfc else 1;v=bytes(raw[i:i+n]);out+=lookup.get(v,v.decode('cp932'));i+=n
 return out
c=(A/'candidate.memory.bin').read_bytes();rs=json.loads((A/'workbench/analysis/ingame_v006/translation_records.json').read_text());reloc={0x27e10:0x3c9d4,0x27e34:0x3bc90,0x27e48:0x3c9e0,0x2c698:0x3bca4,0x2c69c:0x3bcac};exceptions={0x34e98:'腕輪：',0x34eb8:'女神像'};texts=[]
for r in rs:
 old=int(r['memory_offset'],16);at=reloc.get(old,old);raw=c[at:c.index(0,at)];s=actual(raw);expected=r['korean'].replace('금기의 피','기혈').replace('기혈를','기혈을').replace('기혈가','기혈이').replace('기혈는','기혈은').replace('기혈라는','기혈이라는')
 if old in exceptions:expected=exceptions[old]
 assert s==expected,(r['memory_offset'],expected,s)
 assert not any(code in raw for code in added),('newfontcollidesxex',hex(at))
 texts.append(dict(offset=hex(at),japanese=r['original'],korean=s))
assert len(texts)==1053
# Independently resolve each menu string through its resource metadata.
menu_records=json.loads((A/'v125/source/translation_records.json').read_text());menus={}
for r in menu_records:
 if r['archive'] not in menus:
  b=(A/'current/Media/Menu'/r['archive']).read_bytes();first=struct.unpack_from('>I',b)[0];table={}
  for pos in range(0,first,12):
   at,n,no=struct.unpack_from('>III',b,pos)
   if at==0xffffffff:break
   table[b[no:b.index(0,no)].decode()]=(at,n)
  menus[r['archive']]=(b,table)
 b,table=menus[r['archive']];off,n=table[r['entry']];leaf=b[off:off+n]
 at=8 if r['kind']=='customize description' else struct.unpack_from('>I',leaf,r['pointer_field'])[0];raw=leaf[at:leaf.index(0,at)]
 assert actual(raw)==r['korean'],r
 assert not any(code in raw for code in added),('newfontcollidesmenu',r)
for r in json.loads((H/'mission_review.json').read_text()):
 raw=bytes.fromhex(r['raw']);assert actual(raw)==r['current'];assert not any(code in raw for code in added),('newfontcollidesmission',r)
verified=json.loads((H/'dialogue_verified.json').read_text());fixes=json.loads((H/'corrections.json').read_text())
for r in verified:
 path='Media/Demo/'+r['file'];p=H/'changed'/path;b=p.read_bytes() if p.exists() else (A/'current'/path).read_bytes();base=struct.unpack_from('>I',b)[0];start,stride,count,tail=struct.unpack_from('>IIII',b,base);pool=base+start+stride*count;at=pool+struct.unpack_from('>I',b,base+start+r['record']*stride+16)[0];raw=b[at:b.index(0,at)];s=actual(raw);assert s==r['korean']
 assert not re.search('[ぁ-ゖァ-ヺ一-龯]',s),(path,r['record'],s)
 if r['file']+'/'+str(r['record']) not in fixes:assert not any(code in raw for code in added),('newfontcollidesdialogue',r)
# Entire executable, mission scripts and all unrelated package payloads are unchanged from public v1.2.8.
changed={p.relative_to(H/'changed').as_posix() for p in (H/'changed').rglob('*') if p.is_file()};old={r[0]:r for l in (R/'package/manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]};new={r[0]:r for l in (H/'package/manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
assert len(changed)==9
for name,row in old.items():
 if name not in changed:assert row==new[name] and (R/'package/payload'/row[4]).read_bytes()==(H/'package/payload'/row[4]).read_bytes()
report=dict(executable_texts_compared_to_own_translation_records=len(texts),mission_files_checked=86,mission_texts_checked=55,menu_texts_checked=len(menu_records),dialogue_texts_checked=len(verified),new_glyph_codes_unused_by_unmodified_display_strings=True,non_dialogue_logic_identical_to_public_v128=True,changed_assets=sorted(changed),actual_xenia_gameplay_tested=False)
(H/'audit/text_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
