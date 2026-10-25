"""Native compact menu parse/release/retry and screen switching.
540 KiB total allocation budget from the reporter log is modeled; actual
physical-page compaction, GPU/FEX and Android execution are not reproduced.
"""
import sys,struct,json,hashlib,itertools,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
W=ROOT/'storm_save_audit/recovery/work9'
os.chdir(W);sys.path.insert(0,str(W));sys.argv=[sys.argv[0],str(ROOT/'hakux_audit/menu_memory_candidate.xbe')]
from check_save import *
from unicorn import UC_HOOK_CODE
sy=json.loads((ROOT/'hakux_audit/menu_memory_build.json').read_text())['symbols']
rows=[]
for mode in [0,1]:
 u=cpu();put(u,0x3d83c8,0x1600000);setstate(u,(mode,1,0))
 registry=bytes((i*13+29)%256 for i in range(0x516*8));u.mem_write(0x8dbb28,registry)
 live={};allocs=[];frees=[];fail=[False];peak=[0]
 def hook(u,a,n,d):
  sp=u.reg_read(UC_X86_REG_ESP)
  def ret(v=0,pop=0):
   u.reg_write(UC_X86_REG_EAX,v);u.reg_write(UC_X86_REG_ESP,sp+4+pop);u.reg_write(UC_X86_REG_EIP,get(u,sp))
  if a==0x32bd3e:
   size=get(u,sp+4);rounded=(size+4095)&~4095
   assert get(u,sp+8)==0xb6800000
   if fail[0] or sum(live.values())+rounded>540*1024:ret(0,8);return
   p=0x1800000+(len(allocs)%5)*0x100000;assert p not in live
   u.mem_write(p,bytes(rounded));live[p]=rounded;allocs.append((p,size));peak[0]=max(peak[0],sum(live.values()));ret(p,8)
  elif a==0x32bdde:
   p=get(u,sp+4);assert p in live;del live[p];frees.append(p);ret(0,8)
  elif a==0x3caa10:ret(0,8)
 for a in [0x32bd3e,0x32bdde,0x3caa10]:u.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
 def check_empty():
  assert not live and get(u,0xe049e8)==0 and get(u,0xe0498c)==0
  assert bytes(u.mem_read(0x8dbb28,len(registry)))==registry
 def release():call(u,0xf40df2);check_empty()
 for label,count in [('chooser',2),('costumes',3)]:
  entry=sy['ensure_'+label]
  fail[0]=True;call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==0;check_empty()
  fail[0]=False;call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==1
  assert get(u,0xe049e4)==count
  before=len(allocs);call(u,entry);assert len(allocs)==before
  release()
  # Corrupt each native resource header in turn, including partial parse paths.
  template=sy['chooser_header' if label=='chooser' else 'costume_header']
  for index in range(count):
   a=template+20+6*24+index*32;old=get(u,a);put(u,a,0xffffffff)
   call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==0;check_empty()
   put(u,a,old);call(u,entry);assert u.reg_read(UC_X86_REG_EAX)==1
   release()
  rows.append(dict(mode=mode,client=label,allocation_failure_retry=True,partial_parse_failures=count,passed=True))
 # Switch directly as well as through the real scene teardown hook.
 for cycle in range(12):
  for label in ['chooser','costumes']:
   call(u,sy['ensure_'+label]);assert u.reg_read(UC_X86_REG_EAX)==1
   assert len(live)==1
   assert bytes(u.mem_read(0x8dbb28,len(registry)))==registry
  regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP]
  values=[0x2000000+i*16 for i in range(len(regs))]
  for k,v in zip(regs,values):u.reg_write(k,v)
  xmm=0x1234567890abcdefabcdef0123456789;u.reg_write(UC_X86_REG_XMM3,xmm)
  u.reg_write(UC_X86_REG_ESP,STACK);u.mem_write(0xdb9888,b'\x0c')
  run(u,0x21a9b0,0x21a9b7)
  assert [u.reg_read(k) for k in regs]==values and u.reg_read(UC_X86_REG_XMM3)==xmm
  assert state(u)==(mode,1,0);check_empty()
  before=len(frees);run(u,0x21a9b0,0x21a9b7);assert len(frees)==before
 rows.append(dict(mode=mode,kind='screen switch + scene release',cycles=12,peak_pages=peak[0]//4096,passed=True))
report=dict(scope=__doc__,sha256=hashlib.sha256(b).hexdigest(),cases=rows,status='PASS')
(ROOT/'hakux_audit/menu_lifetime_results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
