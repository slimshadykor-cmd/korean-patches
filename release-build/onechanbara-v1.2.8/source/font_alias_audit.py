from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,struct,io,hashlib,collections
W=Path(__file__).resolve().parent;b=(W.parent/'audit_identifiers_20261019/current/Media/Sys/font.bin').read_bytes();known=json.loads((W.parent/'audit_identifiers_20261019/v126/audit/glyph_mapping.json').read_text());cells={};code_hash={}
for i in range(22):
 o,n,no=struct.unpack_from('>3I',b,i*12);name=b[no:b.index(0,no)].decode();lead=int(name[1:3],16)
 for trail in range(0x40,0xfd):
  try:bytes([lead,trail]).decode('cp932')
  except UnicodeError:continue
  x=(trail-0x40)%16*32;y=(trail-0x40)//16*32
  data=b''.join(b[o+128+((y//4+by)*128+x//4)*16:o+128+((y//4+by)*128+x//4)*16+128] for by in range(8));h=hashlib.sha256(data).hexdigest();cells.setdefault(h,[]).append(bytes([lead,trail]).hex().upper());code_hash[bytes([lead,trail]).hex().upper()]=h
font=ImageFont.truetype(str(W.parent/'release_v128/dependencies/NotoSansCJKkr-Regular.otf'),30);matches=[]
for v in range(0xac00,0xd7a4):
 c=chr(v);cell=Image.new('RGBA',(32,32),(255,255,255,0));d=ImageDraw.Draw(cell);a,bb,z,h=d.textbbox((0,0),c,font=font);d.text(((32-z+a)//2-a,(32-h+bb)//2-bb),c,font=font,fill='white');f=io.BytesIO();cell.save(f,format='DDS',pixel_format='DXT5');hh=hashlib.sha256(f.getvalue()[128:]).hexdigest()
 if hh in cells:
  for code in cells[hh]:matches.append({'korean':c,'cp932_hex':code,'verified_by':'exact DXT5 glyph bitmap match'})
knowncodes={r['cp932_hex'].upper():r['korean'] for r in known};new=[r for r in matches if r['cp932_hex'] not in knowncodes];conflicts=[r for r in matches if r['cp932_hex'] in knowncodes and r['korean']!=knowncodes[r['cp932_hex']]]
assert not conflicts
(W/'font_alias_validation.json').write_text(json.dumps({'known_mapping_count':len(known),'bitmap_matches':len(matches),'verified_aliases':new,'conflicts':conflicts},ensure_ascii=False,indent=2));print('known',len(known),'exact matches',len(matches),'additional aliases',len(new),flush=True)
