"""All compact cache failure/retry and mixed scene lifetime paths.
Native parser/unregister/resource wait code; physical alloc/free and terminal
GPU completion modeled. CPU/FPU, shared registry, and mode state are checked.
"""
import sys,struct,json,hashlib,itertools
from pathlib import Path
sys.path.insert(0,'.')
from check_save import *
from unicorn import UC_HOOK_CODE
sy=json.loads(Path('save_crash_fix/build.json').read_text())['symbols']
rows=[]
for mode in [0,1]:
 u=cpu();put(u,0x3d83c8,0x1600000);setstate(u,(mode,1,0))
 registry=bytes((i*13+29)%256 for i in range(0x516*8));u.mem_write(0x8dbb28,registry)
 live={};allocs=[];frees=[];waits=[];fail=[False]
 def hook(u,a,n,d):
  sp=u.reg_read(UC_X86_REG_ESP)
  def ret(v=0,pop=0):
   u.reg_write(UC_X86_REG_EAX,v);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,get(u,sp))
  if a==0x32bd3e:
   size=get(u,sp+4);assert get(u,sp+8)==0xb6800000
   if fail[0]:ret(0,8);return
   p=0x1800000+(len(allocs)%5)*0x100000;assert p not in live
   u.mem_write(p,bytes((size+4095)&~4095));live[p]=size;allocs.append((p,size));ret(p,8)
  elif a==0x32bdde:
   p=get(u,sp+4);assert p in live;del live[p];frees.append(p);ret(0,8)
  elif a==0x3cadf0:waits.append(u.reg_read(UC_X86_REG_EAX))
  elif a==0x3caa10:ret(0,8)
 for a in [0x32bd3e,0x32bdde,0x3cadf0,0x3caa10]:u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def check_empty(rec):
  assert get(u,rec)==0 and get(u,rec+16)==0
  assert bytes(u.mem_read(rec+56,68))==bytes(68)
  assert bytes(u.mem_read(0x8dbb28,len(registry)))==registry
 for label in ['badge','scroll']:
  rec=sy['white_record' if label=='badge' else 'scroll_record'];entry=sy['ensure_'+label]
  fail[0]=True;call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==0;check_empty(rec)
  fail[0]=False;call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==1
  before=len(allocs);call(u,entry);assert len(allocs)==before
  u.reg_write(UC_X86_REG_EAX,rec);call(u,sy['release_compact']);check_empty(rec)
  # Fail the ACTUAL parser's first resource type check, then restore template.
  template=get(u,rec+128);resource=template+20+get(u,rec+136)*24
  value=get(u,resource);put(u,resource,0xffffffff)
  call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==0;check_empty(rec)
  put(u,resource,value);call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==1
  u.reg_write(UC_X86_REG_EAX,rec);call(u,sy['release_compact']);check_empty(rec)
  rows.append(dict(mode=mode,kind='allocation/parser failure and retry',client=label))
 for order in itertools.permutations(['large','badge','scroll']):
  for label in order:
   call(u,0xe0459a if label=='large' else sy['ensure_'+label]);assert u.reg_read(UC_X86_REG_EAX)==1
  # Nonzero fences exercise native resource waits before free.
  ptrs=[get(u,0xe049b4+i*4) for i in range(12)]
  for rec,count in [(sy['white_record'],2),(sy['scroll_record'],4)]:
   ptrs += [get(u,rec+104+i*4) for i in range(count)]
  for p in ptrs:assert p;put(u,p+8,0x1234)
  regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  values=[0x2000000+i*16 for i in range(len(regs))]
  for k,v in zip(regs,values):u.reg_write(k,v)
  xmm=0x1234567890abcdefabcdef0123456789;u.reg_write(UC_X86_REG_XMM3,xmm)
  u.reg_write(UC_X86_REG_EFLAGS,0x246);u.reg_write(UC_X86_REG_ESP,STACK);u.mem_write(0xdb9888,b'\x0c')
  start=len(waits);run(u,0x21a9b0,0x21a9b7)
  assert set(waits[start:])==set(ptrs) and len(waits)-start==18
  assert [u.reg_read(k) for k in regs]==values
  assert u.reg_read(UC_X86_REG_XMM3)==xmm and u.reg_read(UC_X86_REG_ESP)==STACK
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x40
  assert not live and state(u)==(mode,1,0)
  for rec in [sy['white_record'],sy['scroll_record']]:check_empty(rec)
  assert get(u,0xe049e8)==0 and bytes(u.mem_read(0xe049b4,52))==bytes(52)
  before=len(frees);run(u,0x21a9b0,0x21a9b7);assert len(frees)==before
  rows.append(dict(mode=mode,kind='mixed cache full scene release',order=order))
out=dict(status='PASS',sha256=hashlib.sha256(b).hexdigest(),scope=__doc__,cases=rows)
Path('save_crash_fix/lifetime.json').write_text(json.dumps(out,indent=2));print('PASS',len(rows),'cases')
