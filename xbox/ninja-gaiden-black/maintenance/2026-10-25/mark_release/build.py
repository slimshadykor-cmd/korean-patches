import sys,struct,subprocess,json,hashlib
from pathlib import Path
sys.path.insert(0,'.')
from inspect_xbe import *
sys.path.insert(0,'candidate/NGB_CutsceneSkip_TEST1/ngb_native11')
from xbe_guard import finalize_build
s=sections[-1];va=(s['va']+s['size']+15)&~15
subprocess.run(['as','--32','mark_release/marks.S','-o','mark_release/marks.o'],check=True)
subprocess.run(['ld','-m','elf_i386','-Ttext',hex(va),'-e','mark_text_gate','mark_release/marks.o','-o','mark_release/marks.elf'],check=True)
subprocess.run(['objcopy','-O','binary','mark_release/marks.elf','mark_release/marks.bin'],check=True)
S={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output(['nm','-n','mark_release/marks.elf'],text=True).splitlines() if len(l.split())==3}
oldsy=json.loads(Path('mark_release/test5_build.json').read_text())['symbols'];start=oldsy['slot_draw'];end=oldsy['profile_read'];hits=[]
for site in range(start,end-4):
 p=at(site)
 if b[p]==0xe8 and site+5+struct.unpack_from('<i',b,p+1)[0]==0x1e6d30:hits.append(site)
assert len(hits)==1
site=hits[0];out=bytearray(b);fo=s['fo']+va-s['va'];out.extend(bytes(fo-len(out)));out.extend(Path('mark_release/marks.bin').read_bytes());out[at(site):at(site)+5]=b'\xe8'+struct.pack('<i',S['mark_text_gate']-site-5)
hdr=table-base+(n-1)*56;size=len(out)-s['fo']
for off in [8,16]:struct.pack_into('<I',out,hdr+off,size)
struct.pack_into('<I',out,0x10c,((s['va']+size+4095)&~4095)-base)
out=bytes(finalize_build(out,Path('original.xbe').read_bytes()));Path('mark_release/final.xbe').write_bytes(out)
allowed=set(range(at(site),at(site)+5))|set(range(hdr+8,hdr+12))|set(range(hdr+16,hdr+20))|set(range(0x10c,0x110))
for i in range(n):allowed.update(range(table-base+i*56+36,table-base+i*56+56))
diff={i for i,(x,y) in enumerate(zip(b,out)) if x!=y};assert diff<=allowed
report={'symbols':S,'hook':hex(site),'sha256':hashlib.sha256(out).hexdigest(),'test5_bytes_changed':len(diff),'preservation':'Only text-draw call, section length/hash/header fields; appended mark renderer. All save/load/mode/skip instructions byte-identical to TEST5.'}
Path('mark_release/build.json').write_text(json.dumps(report,indent=2));print(report)
