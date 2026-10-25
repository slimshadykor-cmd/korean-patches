import os
MODE=int(os.environ.get("NGB_TEST_MODE","1"))
exec(open('settings_analysis/profile_probe.py').read().split("u.mem_write(STACK")[0])
from unicorn import UC_HOOK_CODE
heap=[0x1800000]; disk=[b'']; sig=[b'']; calls=[]
def hook(u,a,n,d):
 sp=u.reg_read(UC_X86_REG_ESP)
 def arg(i):return get(u,sp+4+i*4)
 def ret(v=0,pop=0):u.reg_write(UC_X86_REG_EAX,v&0xffffffff);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,get(u,sp))
 if a in [0x3347e0,0x379c29]:ret(u.reg_read(UC_X86_REG_EAX))
 elif a==0x310740:ret(0x12345678)
 elif a==0x310550:
  import hashlib
  u.mem_write(arg(3),hashlib.sha1(bytes(u.mem_read(arg(0),arg(1)))).digest());ret(1)
 elif a==0x329105:u.mem_write(arg(4),b'U:\\1\\\0');ret(0,24)
 elif a==0x36f436:
  p=heap[0];heap[0]+=(arg(0)+255)&~255;ret(p)
 elif a==0x36f43b:ret(u.reg_read(UC_X86_REG_EAX))
 elif a==0x32a3a0:ret(123,28)
 elif a==0x32a772:ret(arg(1),16)
 elif a==0x32a6ee:ret(1,4)
 elif a==0x32af30:ret(1,4)
 elif a==0x32a618:
  disk[0]=bytes(u.mem_read(arg(1),arg(2)));put(u,arg(3),arg(2));ret(1,20)
 elif a==0x32a95b:put(u,arg(1),len(disk[0]));put(u,arg(1)+4,0);ret(1,8)
 elif a==0x32a52b:u.mem_write(arg(1),disk[0]);put(u,arg(3),len(disk[0]));ret(1,20)
 elif a>=0x320000 and a<0x3e0000:
  print('unexpected',hex(a));u.emu_stop()


def fresh():
 global u
 u=cpu();heap[0]=0x1800000
 for a in [0x3347e0,0x379c29,0x310740,0x310550,0x329105,0x36f436,0x36f43b,0x32a3a0,0x32a772,0x32a6ee,0x32af30,0x32a618,0x32a95b,0x32a52b]:u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 u.mem_write(0x1701000,b'1\0\0\0')
def write(mode,seq):
 put(u,S['STORM_MODE'],mode);put(u,BASE+0x100,seq)
 u.reg_write(UC_X86_REG_ECX,0);u.mem_write(STACK,struct.pack('<7I',STOP,0,0x1701000,BASE,SIZE,0,0));u.reg_write(UC_X86_REG_ESP,STACK)
 u.emu_start(0x30f650,STOP,count=20000000)
 assert u.reg_read(UC_X86_REG_EIP)==STOP and u.reg_read(UC_X86_REG_EAX)==0
 return bytes(u.mem_read(BASE,SIZE))
def read(expected,mode):
 fresh();put(u,S['STORM_MODE'],1-mode)
 u.reg_write(UC_X86_REG_ECX,0);u.reg_write(UC_X86_REG_EDX,0);u.mem_write(STACK,struct.pack('<5I',STOP,0x1701000,BASE,SIZE,0));u.reg_write(UC_X86_REG_ESP,STACK)
 u.emu_start(0x310050,STOP,count=20000000)
 assert u.reg_read(UC_X86_REG_EIP)==STOP and u.reg_read(UC_X86_REG_EAX)==0
 assert get(u,S['STORM_MODE'])==mode
 assert bytes(u.mem_read(BASE,SIZE))==expected
 put(u,0xdb9e9c,0x1708000);u.mem_write(0x1708002,b'\1');u.mem_write(0x47a55c,b'\0\0');u.mem_write(0xdba04e,struct.pack('<H',1));u.reg_write(UC_X86_REG_EDI,0x4b4e50);u.reg_write(UC_X86_REG_EDX,3);u.reg_write(UC_X86_REG_EBX,5)
 u.mem_write(STACK,struct.pack('<II',STOP,14));u.reg_write(UC_X86_REG_ESP,STACK);u.emu_start(0xe040ba,STOP,count=100000)
 assert u.reg_read(UC_X86_REG_EBX)==(13 if mode else 5)
results=[]
for seq in [(0,0),(0,1),(1,0),(1,1),(1,0,1),(0,1,0)]:
 fresh();disk[0]=b''
 for i,mode in enumerate(seq):
  expected=write(mode,i+1);read(expected,mode)
 results.append({'sequence':seq,'result':'PASS'})
Path('profile_fix/cross_modes.json').write_text(json.dumps({'cases':results,'scope':'Native save serializer/reader/internal allocator, fresh CPU after each overwrite; host file operations and Xbox signing mocked. Not xemu playback.'},indent=2));print(results)
