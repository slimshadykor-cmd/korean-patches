from pathlib import Path
import struct,subprocess,json,hashlib,sys
sys.path.insert(0,'.')
from inspect_xbe import *
sys.path.insert(0,'candidate/NGB_CutsceneSkip_TEST1/ngb_native11')
from xbe_guard import finalize_build
s=sections[-1];va=(s['va']+s['size']+15)&~15
subprocess.run(['as','--32','profile_fix/read.S','-o','profile_fix/read.o'],check=True)
subprocess.run(['ld','-m','elf_i386','-Ttext',hex(va),'-e','profile_workspace_gate','profile_fix/read.o','-o','profile_fix/read.elf'],check=True)
subprocess.run(['objcopy','-O','binary','profile_fix/read.elf','profile_fix/read.bin'],check=True)
sy={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output(['nm','-n','profile_fix/read.elf'],text=True).splitlines() if len(l.split())==3}
out=bytearray(b);fo=s['fo']+va-s['va'];out.extend(bytes(fo-len(out)));out.extend(Path('profile_fix/read.bin').read_bytes())
site=at(0x30fce0);assert b[site:site+6]==bytes.fromhex('81ec0c030000');out[site:site+6]=b'\xe9'+struct.pack('<i',sy['profile_workspace_gate']-0x30fce5)+b'\x90'
hdr=table-base+(n-1)*56;size=len(out)-s['fo']
for off in [8,16]:struct.pack_into('<I',out,hdr+off,size)
struct.pack_into('<I',out,0x10c,((s['va']+size+4095)&~4095)-base)
out=bytes(finalize_build(out,Path('original.xbe').read_bytes()));Path('profile_fix/test6.xbe').write_bytes(out)
allowed=set(range(site,site+6))|set(range(hdr+8,hdr+12))|set(range(hdr+16,hdr+20))|set(range(0x10c,0x110))
for i in range(n):allowed.update(range(table-base+i*56+36,table-base+i*56+56))
diff={i for i,(x,y) in enumerate(zip(b,out)) if x!=y};assert diff<=allowed
report={'symbols':sy,'base_sha256':hashlib.sha256(b).hexdigest(),'sha256':hashlib.sha256(out).hexdigest(),'bytes':len(out),'preserved':'save write, actual mode restoration, menu marks, cutscene skip and all translations unchanged','scope':'Only default system settings read workspace; native parsing/checksum/error behavior retained'}
Path('profile_fix/build.json').write_text(json.dumps(report,indent=2));print(report)
