from pathlib import Path
import json,struct,gzip,zipfile,hashlib,io
from Crypto.Cipher import AES
W=Path(__file__).resolve().parent.parent
INPUT=W/'input'/'Onechanbara vorteX 일본판 한글화'
OUT=W/'audit';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def delta(b,p):
 d=gzip.decompress(p);magic,size,n=struct.unpack_from('<4sII',d);assert magic==b'OPD1' and len(b)==size
 out=bytearray(b);pos=12
 for _ in range(n):
  at,z=struct.unpack_from('<II',d,pos);pos+=8;assert at+z<=size;out[at:at+z]=d[pos:pos+z];pos+=z
 assert pos==len(d)
 return bytes(out)
def memory(xex):
 _,_,header,_,security,num=struct.unpack_from('>6I',xex)
 headers=dict(struct.unpack_from('>II',xex,24+i*8) for i in range(num));fmt=headers[0x3ff]
 size,enc,comp=struct.unpack_from('>IHH',xex,fmt);assert (enc,comp)==(1,1)
 key=AES.new(bytes.fromhex('20b185a59d28fdc340583fbb0896bf91'),AES.MODE_CBC,bytes(16)).decrypt(xex[security+0x150:security+0x160])
 plain=AES.new(key,AES.MODE_CBC,bytes(16)).decrypt(xex[header:]);out=bytearray();pos=0
 for i in range((size-8)//8):
  n,z=struct.unpack_from('>II',xex,fmt+8+i*8);out+=plain[pos:pos+n]+bytes(z);pos+=n
 assert pos==len(plain)
 return bytes(out)
def cstr(b,at):return b[at:b.index(0,at)]
def runs(indices):
 result=[]
 for i in indices:
  if result and i==result[-1][1]:result[-1][1]+=1
  else:result.append([int(i),int(i)+1])
 return result
def package():return zipfile.ZipFile(W/'package.zip')
def manifest():
 with package() as z:s=z.read('manifest.tsv').decode('utf-8-sig')
 return {r[0]:r for line in s.splitlines() if line and not line.startswith('#') for r in [line.split('\t')]}
def glyphs():return {bytes.fromhex(r['cp932_hex']):r['korean'] for r in json.loads((W/'baseline_source/release-build/onechanbara-v1.2.8/audit/glyph_mapping.json').read_text())}
def decoded(b):
 mapping=glyphs();out=[];i=0
 while i<len(b):
  n=2 if 0x81<=b[i]<=0x9f or 0xe0<=b[i]<=0xfc else 1;v=b[i:i+n];out.append(mapping.get(v,v.decode('cp932',errors='replace')));i+=n
 return ''.join(out)
