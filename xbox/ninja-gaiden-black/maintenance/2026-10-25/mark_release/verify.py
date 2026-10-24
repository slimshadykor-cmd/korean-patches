import sys,json,struct,hashlib
from pathlib import Path
sys.path.insert(0,'.')
from check_save import *
from unicorn import UC_HOOK_CODE
Z=json.loads(Path('mark_release/test5_build.json').read_text())['symbols'];R=json.loads(Path('mark_release/rects.json').read_text());cases=0
for language in [0,1]:
 for mode in [0,1,2]:
  for y in [-200,0,200]:
   for alpha in [0.,.5,1.]:
    for ready in [True,False]:
     u=cpu();u.mem_write(0x229f20,b'\xc3');p=0x1800000;u.mem_write(p+0x1c,b'\1');u.mem_write(p+0x75,bytes([mode])+b'SM');put(u,0xdb9890,language)
     registry=bytes(range(16));textures=bytes(range(16,32));u.mem_write(0x8dbb28,registry);u.mem_write(0xe049b4,textures)
     put(u,0xe04980+0xc,1);put(u,0x8f7df8,768)
     if not ready:u.mem_write(0xe0459a,b'\x31\xc0\xc3')
     captured=[];texts=[]
     def hook(u,a,n,d):
      if a in [0x1e6d30,0x221340]:
       sp=u.reg_read(UC_X86_REG_ESP)
       if a==0x1e6d30:texts.append(bytes(u.mem_read(get(u,sp+4),0x54)))
       else:
        assert bytes(u.mem_read(0x8dbb28,16))==textures
        captured.append(bytes(u.mem_read(u.reg_read(UC_X86_REG_EDI),0x2c)))
       u.reg_write(UC_X86_REG_EAX,1);u.reg_write(UC_X86_REG_EIP,get(u,sp));u.reg_write(UC_X86_REG_ESP,sp+4)
     u.hook_add(UC_HOOK_CODE,hook);u.mem_write(STACK,struct.pack('<II f',STOP,p,alpha));u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EAX,y&0xffffffff);u.emu_start(Z['slot_draw'],STOP,count=100000)
     assert u.reg_read(UC_X86_REG_EIP)==STOP and u.reg_read(UC_X86_REG_ESP)==STACK+4
     assert bytes(u.mem_read(0x8dbb28,16))==registry
     assert len(texts)==1
     desc=texts[0];assert struct.unpack_from('<hh',desc,0x44)==(164,y+143)
     label=('unknown' if mode==2 else 'storm' if mode else 'black')+('_ko' if language==0 else '_en');assert struct.unpack_from('<I',desc,0x10)[0]==Z[label]
     expected=R['storm' if mode else 'black'] if mode<2 and ready and alpha>0 and y+133>=-20 else []
     assert len(captured)==len(expected)
     for desc,(x,dy,w,h,color) in zip(captured,expected):
      assert struct.unpack_from('<I',desc)[0]==0x7fff
      assert struct.unpack_from('<hhH',desc,4)==(115+x,133+y+dy,0x1ca)
      assert struct.unpack_from('<ff',desc,0x14)==(w,h)
      assert struct.unpack_from('<I',desc,0x28)[0]==(int(alpha*(color>>24))<<24)|(color&0xffffff)
     cases+=1
report={'cases':cases,'game_state_changes':False,'save_code_byte_identical_to_test5':True,'scope':'Native x86 overlay execution and captured draw descriptors. GPU calls mocked; actual xemu mark appearance unverified.'}
Path('mark_release/verification.json').write_text(json.dumps(report,indent=2));print(report)
