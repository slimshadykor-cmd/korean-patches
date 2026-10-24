import sys,struct,subprocess,json,hashlib
from pathlib import Path
sys.path.insert(0,'.')
from inspect_xbe import *
sys.path.insert(0,'candidate/NGB_CutsceneSkip_TEST1/ngb_native11')
from xbe_guard import finalize_build
p=struct.unpack_from('<I',b,at(0x4284a8))[0];raw=b[at(p):b.index(0,at(p))];a,z=raw.split(b'\n',1)
Path('settings_analysis/ko_prefix.bin').write_bytes(a)
Path('settings_analysis/ko_suffix.bin').write_bytes(b'\n'+z)
s=sections[-1];va=(s['va']+s['size']+15)&~15
subprocess.run(['as','--32','settings_analysis/save_ui.S','-o','settings_analysis/code.o'],check=True)
subprocess.run(['ld','-m','elf_i386','-Ttext',hex(va),'settings_analysis/code.o','-o','settings_analysis/code.elf'],check=True)
subprocess.run(['objcopy','-O','binary','settings_analysis/code.elf','settings_analysis/code.bin'],check=True)
S={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output(['nm','-n','settings_analysis/code.elf'],text=True).splitlines() if len(l.split())==3}
out=bytearray(b);fo=s['fo']+va-s['va'];out.extend(bytes(fo-len(out)));out.extend(Path('settings_analysis/code.bin').read_bytes());changes=[]
for site,label,old,op in [(0x3104dc,'common_read_success','e85f0c0000',0xe8),(0x168937,'warning_enter','bb00010000',0xe9),(0x30f9d0,'common_write','83ec5ca1d8',0xe9),(0xe04323,'restore_mode','e958fdffff',0xe9),(0x179eb4,'preview_mode','c3cccccccc',0xe9),(0x187f3f,'slot_draw','e8dc1f0a00',0xe8),(0x30fe6a,'profile_read','e9e144af00',0xe9)]:
 pos=at(site);actual=b[pos:pos+5].hex()
 if site!=0x30fe6a:assert actual==old,(hex(site),actual)
 else:assert b[pos]==0xe9 and site+5+struct.unpack_from('<i',b,pos+1)[0]==0xe04350
 out[pos:pos+5]=bytes([op])+struct.pack('<i',S[label]-site-5);
 if site==0x30f9d0:out[pos+5:pos+8]=b'\x90'*3
 if site==0x168937:out[pos+5:pos+10]=b'\x90'*5
changes.append(dict(site=hex(site),old=actual,new=out[pos:pos+5].hex()))
for site,label in [(0x4284a8,'ko_warning'),(0x4284ac,'en_warning')]:struct.pack_into('<I',out,at(site),S[label])
hdr=table-base+(n-1)*56;size=len(out)-s['fo'];struct.pack_into('<I',out,hdr+8,size);struct.pack_into('<I',out,hdr+16,size);struct.pack_into('<I',out,0x10c,((s['va']+size+4095)&~4095)-base)
out=bytes(finalize_build(out,Path('original.xbe').read_bytes()));Path('settings_candidate.xbe').write_bytes(out)
Path('settings_analysis/build.json').write_text(json.dumps(dict(symbols=S,changes=changes,sha256=hashlib.sha256(out).hexdigest(),base_sha256=hashlib.sha256(b).hexdigest()),indent=2))
print('Built',len(out),hashlib.sha256(out).hexdigest())
