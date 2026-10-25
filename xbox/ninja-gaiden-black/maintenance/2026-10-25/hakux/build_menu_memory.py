"""Split the unchanged full XPR into two screen-specific allocations.
Code and tiny headers occupy proven zero tail padding in the embedded XPR.
No image bytes, virtual image size, save code or gameplay logic are changed.
"""
import struct,sys,hashlib,json,subprocess
from pathlib import Path
sys.path.insert(0,'hakux_audit')
from xbe_inspect import b,at,n,sh,sections
root=Path('hakux_audit')
xpr=b[at(0xe04a00):at(0xe04a00)+0xf2800]
sizes=[0x80400,0x480,0x20400,0x20400,0x20400,0x10400]
sources=[0xe05200+struct.unpack_from('<I',xpr,0xa8+i*32)[0] for i in range(6)]
def header(indices):
    total=0x800+sum(sizes[i] for i in indices)
    h=bytearray(struct.pack('<5I',0x30525058,total,0x800,0x80000000,6*24))
    h+=xpr[20:0xa4]
    cursor=0
    for i in indices:
        t=bytearray(xpr[0xa4+i*32:0xc4+i*32])
        struct.pack_into('<I',t,4,cursor)
        struct.pack_into('<I',t,24,cursor+sizes[i]-0x400)
        h+=t;cursor+=sizes[i]
    h+=b'\xff'*4
    return bytes(h),total
ch,cs=header([0,1]);co,cos=header([2,3,4])
(root/'chooser_header.bin').write_bytes(ch);(root/'costume_header.bin').write_bytes(co)
start,end=0xef6a80,0xef7200
assert b[at(start):at(start)+end-start]==bytes(end-start)
defs={'CHOOSER_SIZE':cs,'COSTUME_SIZE':cos}|{f'TEX{i}_SOURCE':sources[i] for i in range(5)}
args=['as','--32']
for k,v in defs.items():args+=['--defsym',f'{k}={v}']
subprocess.run(args+[str(root/'menu_memory.S'),'-o',str(root/'menu_memory.o')],check=True)
subprocess.run(['ld','-m','elf_i386','-Ttext',hex(start),'-e','ensure_chooser',str(root/'menu_memory.o'),'-o',str(root/'menu_memory.elf')],check=True)
subprocess.run(['objcopy','-O','binary',str(root/'menu_memory.elf'),str(root/'menu_memory.bin')],check=True)
symbols={l.split()[2]:int(l.split()[0],16) for l in subprocess.check_output(['nm','-n',str(root/'menu_memory.elf')],text=True).splitlines() if len(l.split())==3}
code=(root/'menu_memory.bin').read_bytes();assert len(code)<=end-start
out=bytearray(b);allowed=set(range(at(start),at(start)+len(code)));out[at(start):at(start)+len(code)]=code
hooks=[]
def patch(a,data,reason):
    off=at(a);old=b[off:off+len(data)];out[off:off+len(data)]=data;allowed.update(range(off,off+len(data)))
    hooks.append(dict(address=hex(a),old=old.hex(),new=data.hex(),reason=reason))
patch(0xe0459a,b'\xe9'+struct.pack('<i',symbols['ensure_chooser']-0xe0459a-5)+b'\x90\x90','compact chooser loader')
patch(0xef7ae5,b'\xe8'+struct.pack('<i',symbols['ensure_costumes']-0xef7ae5-5),'compact costume loader')
patch(0xe049a8,bytes(4),'private resource parser must not clear global slots')
for i in range(n):
    entry=sh+i*56;raw,size=struct.unpack_from('<II',out,entry+12)
    out[entry+36:entry+56]=hashlib.sha1(struct.pack('<I',size)+out[raw:raw+size]).digest()
    allowed.update(range(entry+36,entry+56))
assert len(out)==len(b)
assert all(i in allowed for i,(x,y) in enumerate(zip(b,out)) if x!=y)
for i in range(6):
    p=at(sources[i]);assert out[p:p+sizes[i]]==b[p:p+sizes[i]],i
assert out[0x10c:0x110]==b[0x10c:0x110]
(root/'menu_memory_candidate.xbe').write_bytes(out)
report=dict(scope=__doc__,base_sha256=hashlib.sha256(b).hexdigest(),sha256=hashlib.sha256(out).hexdigest(),
            code_va=hex(start),code_bytes=len(code),symbols=symbols,hooks=hooks,
            chooser_bytes=cs,chooser_pages=(cs+4095)//4096,costume_bytes=cos,costume_pages=(cos+4095)//4096,
            embedded_art_sha256=hashlib.sha256(b''.join(b[at(sources[i]):at(sources[i])+sizes[i]] for i in range(6))).hexdigest(),
            image_size_unchanged=True,all_six_art_payloads_unchanged=True,hakux_verified=False,public_changed=False)
(root/'menu_memory_build.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
