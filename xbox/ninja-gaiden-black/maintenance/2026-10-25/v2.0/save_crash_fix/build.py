"""Split unchanged gameplay art from the full chooser/costume XPR.

Only compact headers/code are appended. Pixel/palette payloads are copied from
the existing immutable embedded XPR; no new image or translation content.
"""
import sys,struct,json,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,'.')
from inspect_xbe import *
sys.path.insert(0,'candidate/NGB_CutsceneSkip_TEST1/ngb_native11')
from xbe_guard import finalize_build

root=Path('save_crash_fix')
assert hashlib.sha256(b).hexdigest()=='295ab4601e27d161c2dda92c50e70ab1738e990e482252953183a3ab31dcda78'
xpr=b[at(0xe04a00):at(0xe04a00)+0xf2800]
def header(indices,total):
 desc=[];resources=[];offset=0
 for slot,index in enumerate(indices):
  d=bytearray(xpr[20+index*24:44+index*24]);struct.pack_into('<I',d,16,slot);desc.append(d)
  t=bytearray(xpr[0xa4+index*32:0xb8+index*32])
  p=bytearray(xpr[0xb8+index*32:0xc4+index*32])
  pixel=0x80 if index==1 else 0x10000
  struct.pack_into('<I',t,4,offset);struct.pack_into('<I',p,4,offset+pixel)
  resources.extend([t,p]);offset+=pixel+0x400
 data=struct.pack('<5I',0x30525058,total,0x800,0x80000000,len(desc)*24)+b''.join(desc)+b''.join(resources)+bytes.fromhex('ffffffff')
 assert len(data)%4==0 and offset+0x800==total
 return data
for label,indices,total in [('white',[1],0xc80),('scroll',[1,5],0x11080)]:
 (root/(label+'_header.bin')).write_bytes(header(indices,total))
white_source=0xe04a00+0x800+struct.unpack_from('<I',xpr,0xc8)[0]
scroll_source=0xe04a00+0x800+struct.unpack_from('<I',xpr,0x148)[0]
assert xpr[white_source-0xe04a00:white_source-0xe04a00+0x80]==bytes(0x80)
old_symbols=json.loads(Path('ui_audit/memory_fix_build.json').read_text())['symbols']
s=sections[-1];va=(s['va']+s['size']+15)&~15
subprocess.run(['as','--32','--defsym',f'WHITE_SOURCE={white_source}','--defsym',f'SCROLL_SOURCE={scroll_source}','--defsym',f'RELEASE_LARGE={old_symbols["release_menu_art"]}',str(root/'compact_art.S'),'-o',str(root/'compact_art.o')],check=True)
subprocess.run(['ld','-m','elf_i386','-Ttext',hex(va),'-e','ensure_badge',str(root/'compact_art.o'),'-o',str(root/'compact_art.elf')],check=True)
subprocess.run(['objcopy','-O','binary',str(root/'compact_art.elf'),str(root/'compact_art.bin')],check=True)
sy={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output(['nm','-n',str(root/'compact_art.elf')],text=True).splitlines() if len(l.split())==3}
out=bytearray(b);fo=s['fo']+va-s['va'];out.extend(bytes(fo-len(out)));out.extend((root/'compact_art.bin').read_bytes())
allowed=set();hooks=[]
def patch(site,old,new,reason):
 p=at(site);assert b[p:p+len(old)]==old,(hex(site),b[p:p+len(old)].hex(),old.hex());assert len(old)==len(new)
 out[p:p+len(old)]=new;allowed.update(range(p,p+len(old)))
 hooks.append(dict(site=hex(site),old=old.hex(),new=new.hex(),reason=reason))
def branch(site,label,opcode):
 patch(site,b[at(site):at(site)+5],bytes([opcode])+struct.pack('<i',sy[label]-site-5),label)
branch(0xef841a,'ensure_badge',0xe8)
branch(0xef7e76,'ensure_scroll',0xe8)
branch(0x21a9b0,'scene_gate',0xe9)
# The same six sprite descriptors, without depending on the large XPR copy.
patch(0xe04525,bytes.fromhex('03059c49e000'),b'\x05'+struct.pack('<I',0xe04a14)+b'\x90','static sprite descriptors')
for a in [0xe04538,0xe0453f]:patch(a,bytes.fromhex('a19c49e000'),b'\xb8'+struct.pack('<I',0xe04a14),'static sprite descriptors')
patch(0xef8436,struct.pack('<I',0xe049b4),struct.pack('<I',sy['white_record']+56),'badge compatibility resource table')
for site,old,delta in [(0xef7ec3,0xe049b4,0),(0xef7eca,0xe049c4,16),(0xef7ed1,0xe049d4,32)]:
 patch(site,struct.pack('<I',old),struct.pack('<I',sy['scroll_record']+56+delta),'scroll compatibility resource table')
hdr=table-base+(n-1)*56;size=len(out)-s['fo']
for off in [8,16]:struct.pack_into('<I',out,hdr+off,size);allowed.update(range(hdr+off,hdr+off+4))
struct.pack_into('<I',out,0x10c,((s['va']+size+4095)&~4095)-base);allowed.update(range(0x10c,0x110))
for i in range(n):allowed.update(range(table-base+i*56+36,table-base+i*56+56))
out=bytes(finalize_build(out,Path('original.xbe').read_bytes()))
assert all(i in allowed for i,(x,y) in enumerate(zip(b,out)) if x!=y)
(root/'fixed.xbe').write_bytes(out)
report=dict(symbols=sy,hooks=hooks,base_sha256=hashlib.sha256(b).hexdigest(),sha256=hashlib.sha256(out).hexdigest(),bytes=len(out),added_bytes=len(out)-len(b),white_source=hex(white_source),scroll_source=hex(scroll_source),scope=__doc__,xemu_verified=False)
(root/'build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
