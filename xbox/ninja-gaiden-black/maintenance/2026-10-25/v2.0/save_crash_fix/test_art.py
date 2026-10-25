"""Native sprite geometry and list lifecycle, modeled physical allocations/GPU.
Run on old and new XBE; compare coordinate/color/UV outputs and pixel/palette
contents independently of their allocation addresses. Native costume textures
0x750..0x754 are absent from this synthetic scene; custom art is exercised.
Not live xemu rendering.
"""
import sys,json,struct,hashlib
from pathlib import Path
sys.path.insert(0,'.')
from check_save import *
from unicorn import UC_HOOK_CODE

report=[]
for width in [640,853]:
 for lang in [0,1]:
  for client in ['chooser_black','chooser_storm']+['costume_'+str(i) for i in range(8)]+['scroll','badge_black','badge_storm']:
   u=cpu();put(u,0x3d83c8,0x1600000);put(u,0x977680,width);put(u,0x977684,480);put(u,0xdb9890,lang);setstate(u,(1,0,0))
   registry=bytes((i*17+23)%256 for i in range(0x516*8));u.mem_write(0x8dbb28,registry)
   put(u,0x43b490,1);put(u,0x8f7df4,0x8e2d50);put(u,0x8f7df0,0x8dfd50);put(u,0x8f7df8,0x300)
   head=0x1700000;put(u,head,head);put(u,head+4,head);put(u,0xc0cf14,head);put(u,0xc0cf18,0)
   allocations=[];frees=[];geometry=[];payloads={};active_heap={head};next_heap=[0x1710000]
   def hook(u,a,n,d):
    sp=u.reg_read(UC_X86_REG_ESP)
    def ret(value=0,pop=0):
     u.reg_write(UC_X86_REG_EAX,value);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,get(u,sp))
    if a==0x32bd3e:
     size=get(u,sp+4);p=0x1800000+len(allocations)*0x100000;u.mem_write(p,bytes((size+4095)&~4095));allocations.append(dict(pointer=p,size=size));ret(p,8)
    elif a==0x32bdde:frees.append(get(u,sp+4));ret(0,8)
    elif a==0x3caa10:ret(0,8)
    elif a==0x36e168:
     assert get(u,sp+4)==12;p=next_heap[0];next_heap[0]+=16;active_heap.add(p);ret(p)
    elif a==0x36e163:
     p=get(u,sp+4);assert p in active_heap,hex(p);active_heap.remove(p);ret()
    elif a==0x1e6d30:ret()
    elif a==0x2213a0:
     i=get(u,0x8f7dfc)-1;meta=bytes(u.mem_read(0x8dfd50+i*16,16));tex,pal=struct.unpack_from('<II',meta)
     vertices=bytes(u.mem_read(0x8e2d50+i*0x70,0x70));geometry.append(hashlib.sha256(vertices+meta[8:]).hexdigest())
     # Native registration resolves texture/palette data into physical addresses.
     data=get(u,tex+4);palette=get(u,pal+4) if pal else 0
     fmt=get(u,tex+12);pixels=1<<(((fmt>>20)&15)+((fmt>>24)&15))
     payload=bytes(u.mem_read(data,max(0x80,pixels)))+(bytes(u.mem_read(palette,0x400)) if pal else b'')
     payloads[str(fmt)]=hashlib.sha256(payload).hexdigest()
   for a in [0x32bd3e,0x32bdde,0x3caa10,0x36e168,0x36e163,0x1e6d30,0x2213a0]:u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
   for cycle in range(2):
    put(u,0x8f7dfc,0)
    if client.startswith('chooser'):
     put(u,0xe044ec,int(client.endswith('storm')));call(u,0xe0457a)
    elif client.startswith('costume'):
     obj=0x1650000;put(u,obj+0x1c,int(client.split('_')[1]));put(u,STACK+4,obj);call(u,0xef7ab0)
    elif client=='scroll':
     desc=0x1650000
     from inspect_xbe import at
     msg=b[at(0xef76bc):].split(b'\0')[0].split(b'\x0c')[lang]
     u.mem_write(0x1660000,msg+b'\0');put(u,desc+0x10,0x1660000);put(u,STACK+4,desc);call(u,0xef7e18)
    else:
     frame=0x1660000;obj=0x1650000;put(u,frame+8,obj);put(u,frame+12,0x3f800000);put(u,frame-4,0)
     u.mem_write(obj+0x75,bytes([int(client.endswith('storm'))]));u.reg_write(UC_X86_REG_EBP,frame);put(u,STACK+4,0x1640000);call(u,0xef83b0)
    assert bytes(u.mem_read(0x8dbb28,len(registry)))==registry,client
    assert geometry or client in ['costume_1','costume_2','costume_3'],client
    put(u,STACK+4,0xc0cf10);call(u,0x2228e0)
    u.reg_write(UC_X86_REG_ESI,0xc0cf10);call(u,0x2228a0);assert len(active_heap)==1
    # Native full-scene teardown site; stop before original remaining teardown.
    u.reg_write(UC_X86_REG_ESP,STACK);run(u,0x21a9b0,0x21a9b7)
    assert bytes(u.mem_read(0x8dbb28,len(registry)))==registry
    assert len(frees)==len(allocations)==cycle+1,(client,allocations,frees)
   report.append(dict(client=client,width=width,language=lang,allocations=[x['size'] for x in allocations],geometry=geometry,payloads=payloads))
out=dict(scope=__doc__,sha256=hashlib.sha256(b).hexdigest(),cases=report)
path=Path(sys.argv[2]);path.write_text(json.dumps(out,indent=2));print('PASS',len(report),'client cases; report',path)
