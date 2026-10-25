exec(open('settings_analysis/profile_probe.py').read().split("u.mem_write(STACK")[0])
from unicorn import UC_HOOK_CODE
heap=[0x1800000];disk=[b''];alloc=['aligned'];outer=[];inner=[];frees=[]
def hook(u,a,n,d):
 sp=u.reg_read(UC_X86_REG_ESP)
 def arg(i):return get(u,sp+4+i*4)
 def ret(v=0,pop=0):u.reg_write(UC_X86_REG_EAX,v&0xffffffff);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,get(u,sp))
 if a==0x327e00:inner.append(u.reg_read(UC_X86_REG_ECX));return
 if a==0x3347e0:ret()
 elif a==0x379c29:ret(u.reg_read(UC_X86_REG_EAX))
 elif a==0x310740:ret(0x12345678)
 elif a==0x310550:
  import hashlib
  u.mem_write(arg(3),hashlib.sha1(bytes(u.mem_read(arg(0),arg(1)))).digest());ret(1)
 elif a==0x36f436:
  outer.append(arg(0));ret(0 if alloc[0]=='null' else 0x1800008 if alloc[0]=='misaligned' else 0x1800000)
 elif a==0x36f43b:frees.append(arg(0));ret(u.reg_read(UC_X86_REG_EAX))
 elif a==0x32a3a0:ret(123,28)
 elif a==0x32a772:ret(arg(1),16)
 elif a==0x32a6ee:ret(1,4)
 elif a==0x32af30:ret(1,4)
 elif a==0x32a618:disk[0]=bytes(u.mem_read(arg(1),arg(2)));put(u,arg(3),arg(2));ret(1,20)
 elif a==0x32a95b:put(u,arg(1),len(disk[0]));put(u,arg(1)+4,0);ret(1,8)
 elif a==0x32a52b:u.mem_write(arg(1),disk[0]);put(u,arg(3),len(disk[0]));ret(1,20)
for a in [0x327e00,0x3347e0,0x379c29,0x310740,0x310550,0x36f436,0x36f43b,0x32a3a0,0x32a772,0x32a6ee,0x32af30,0x32a618,0x32a95b,0x32a52b]:u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
# Prepare native arena to write a valid profile. Internal allocation/free is real code.
arena=0x1900000;put(u,arena,arena+0x10);put(u,arena+4,0x44000);put(u,arena+0x10,arena+0x20);put(u,arena+0x14,0);put(u,arena+0x20,arena+0x10);put(u,arena+0x24,0x4400-2);put(u,0xc05fe8,arena)
u.mem_write(0x1701000,b'T:\\system.dat\0');u.mem_write(STACK,struct.pack('<5I',STOP,0x1701000,0xdb9380,0x508,0x1da9e0));u.reg_write(UC_X86_REG_ESP,STACK);u.emu_start(0x30f9d0,STOP,count=10000000)
assert u.reg_read(UC_X86_REG_EIP)==STOP and u.reg_read(UC_X86_REG_EAX)==0;valid=disk[0];profile=bytes(u.mem_read(0xdb9380,0x508))
rows=[];Z=json.load(open('settings_analysis/build.json'))['symbols'];fixed='test6' in sys.argv[1]
for a in ['aligned','misaligned','null']:
 for label,blob in [('valid',valid),('truncated',valid[:-1]),('bad_signature',bytes([valid[0]^1])+valid[1:])]:
  alloc[0]=a;disk[0]=blob;outer.clear();inner.clear();frees.clear();put(u,Z['last_profile_status'],0)
  before=bytes(u.mem_read(BASE,SIZE));u.mem_write(STACK,struct.pack('<8I',STOP,1,0,0xdb9380,0x508,0x1da9e0,0,0));u.reg_write(UC_X86_REG_ESP,STACK);u.emu_start(0x30fce0,STOP,count=10000000)
  assert u.reg_read(UC_X86_REG_EIP)==STOP
  status=u.reg_read(UC_X86_REG_EAX);expected={'valid':0,'truncated':0xfffffffd,'bad_signature':0xfffffffa}[label] if fixed or a=='aligned' else 0xfffffff9
  assert status==expected,(a,label,hex(status),hex(expected))
  assert bytes(u.mem_read(BASE,SIZE))==before
  if label=='valid' and status==0:assert bytes(u.mem_read(0xdb9380,0x508))==profile
  if fixed:assert outer==[] and frees==[]
  rows.append({'allocation':a,'file':label,'status':f'{status:08X}','R':f'{get(u,Z["last_profile_status"]):08X}','outer_allocations':list(outer),'inner_native_allocations':list(inner)})
print(json.dumps(rows,indent=2));Path('profile_fix/'+('fixed' if fixed else 'before')+'_native.json').write_text(json.dumps(rows,indent=2))
