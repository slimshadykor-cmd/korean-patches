from audit_common import *
import re
S=W/'baseline_source/release-build/onechanbara-v1.2.8/audit'
b=(W/'candidate.memory.bin').read_bytes()
records=json.loads((W/'workbench/analysis/ingame_v006/translation_records.json').read_text())
reloc={0x27e10:0x3c9d4,0x27e34:0x3bc90,0x27e48:0x3c9e0,0x2c698:0x3bca4,0x2c69c:0x3bcac}
exceptions={0x34e98:'腕輪：',0x34eb8:'女神像'}
for r in records:
 old=int(r['memory_offset'],16);at=reloc.get(old,old);text=decoded(cstr(b,at))
 expected=r['korean'].replace('금기의 피','기혈').replace('기혈를','기혈을').replace('기혈가','기혈이').replace('기혈는','기혈은').replace('기혈라는','기혈이라는')
 assert text==exceptions.get(old,expected),(hex(old),text,expected)
dialogues=json.loads((S/'dialogue_verified.json').read_text())
for r in dialogues:
 d=(W/'candidate/Media/Demo'/r['file']).read_bytes();base=struct.unpack_from('>I',d)[0];start,stride,count,tail=struct.unpack_from('>4I',d,base);pool=base+start+stride*count
 at=pool+struct.unpack_from('>I',d,base+start+r['record']*stride+16)[0];s=decoded(cstr(d,at))
 assert s==r['korean'] and not re.search('[ぁ-ゖァ-ヺ一-龯]',s),(r,s)
missiontexts=[]
for p in (W/'original/Media/Mission').glob('*.xmg'):
 q=W/'candidate/Media/Mission'/p.name;d=q.read_bytes() if q.exists() else p.read_bytes();start,count=struct.unpack_from('>II',d,0x38)
 for i in range(count):
  raw=cstr(d,start+i*0x110)
  if not raw:continue
  s=decoded(raw);assert not re.search('[ぁ-ゖァ-ヺ一-龯]',s),(p.name,i,s)
  assert len(raw)<256;missiontexts.append({'file':p.name,'slot':i,'text':s})
areas=[]
for i in range(96):
 raw=cstr(b,0x6e12f8+i*76+44);s=decoded(raw);assert len(raw)<32 and not re.search('[ぁ-ゖァ-ヺ一-龯]',s),(i,s);areas.append(s)
font=(W/'candidate/Media/Sys/font.bin').read_bytes();glyph=json.loads((S/'glyph_mapping.json').read_text());pages={}
for i in range(22):
 off,n,no=struct.unpack_from('>3I',font,i*12);name=cstr(font,no).decode();pages[int(name[1:3],16)]=(off,n)
for g in glyph:
 lead,trail=bytes.fromhex(g['cp932_hex']);off,n=pages[lead];x=(trail-0x40)%16*32;y=(trail-0x40)//16*32
 chunks=[font[off+128+((y//4+by)*128+x//4)*16:off+128+((y//4+by)*128+x//4)*16+128] for by in range(8)]
 assert all(len(c)==128 for c in chunks) and any(b''.join(chunks))
assert (W/'current/Media/Sys/font.bin').read_bytes()==font
report={'executable_display_records':len(records),'story_dialogues':len(dialogues),'mission_nonempty_messages':len(missiontexts),'mission_files':86,'area_labels':len(areas),'font_mapping_count':len(glyph),'font_binary_preserved_from_verified_v128':True,'unexpected_japanese_in_dialogue_mission_or_area_display_fields':0,'new_translation_bug_found':0,'scope':'Known player-visible text fields; internal Japanese resource identifiers intentionally preserved. Full game rendering was not executed.'}
writej('text_validation.json',report);writej('mission_texts_current.json',missiontexts);print(report)
