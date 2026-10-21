"""Execute actual original and patched PowerPC routines; mock external OS calls only."""
from pathlib import Path
import sys,struct,json,itertools
R=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(R/'deps/python'))
from unicorn import Uc,UC_ARCH_PPC,UC_MODE_64,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,UC_TLB_VIRTUAL
from unicorn.ppc_const import *
ENTRY=0x824ecd68;STATE=0x87356f60;STACK=0x71020000;BUFFER=0x72000100;STOP=0x73000000;BASE=0x82000000
ORIG=(R/'current.memory.bin').read_bytes();PATCH=(R/'candidate.memory.bin').read_bytes()
APIS={0x8250e6e8:'read',0x824e1188:'poll',0x824db478:'close',0x824dbfd0:'last_error',0x824dc308:'exit_thread',0x824dd320:'memory_query',0x824dd300:'memory_protect'}
def scenario(patched,start_state=0,ready_tick=0,read_ok=True,last_error=0,protect=False,wait_failure=False):
 u=Uc(UC_ARCH_PPC,UC_MODE_64|UC_MODE_BIG_ENDIAN);u.ctl_set_tlb_mode(UC_TLB_VIRTUAL);u.reg_write(UC_PPC_REG_MSR,0)
 mem=PATCH if patched else ORIG
 pages={a&~4095 for a in [ENTRY,0x82666900,0x826454c8,STATE,0x873570ac,0x82706f90,*APIS]}
 for a in pages:
  u.mem_map(a,4096);off=a-BASE
  if 0<=off<len(mem):u.mem_write(a,mem[off:off+4096])
 u.mem_map(STACK-0x10000,0x20000);u.mem_map(BUFFER&~4095,4096);u.mem_map(STOP,4096)
 def w(a,v):u.mem_write(a,struct.pack('>I',v&0xffffffff))
 def r(a):return struct.unpack('>I',u.mem_read(a,4))[0]
 w(STATE,start_state);w(0x82706f90,0x1110);w(0x873570ac,128)
 nonvol={getattr(sys.modules['unicorn.ppc_const'],'UC_PPC_REG_'+str(i)):0xabcdef0000000000+i for i in range(14,32)}
 for reg,value in nonvol.items():u.reg_write(reg,value)
 u.reg_write(UC_PPC_REG_CR,0x12345678)
 events=[];tick=0;counts=[];body=0;aborted=False;trace=[]
 def hook(uc,pc,size,_):
  nonlocal body,aborted
  trace.append((hex(pc),hex(uc.reg_read(UC_PPC_REG_LR)),hex(uc.reg_read(UC_PPC_REG_12)),hex(uc.reg_read(UC_PPC_REG_1)),bytes(uc.mem_read(STACK-8,4)).hex()))
  if pc==ENTRY+4:body+=1
  if pc not in APIS:return
  name=APIS[pc];args=[uc.reg_read(getattr(sys.modules['unicorn.ppc_const'],'UC_PPC_REG_'+str(i)))&0xffffffff for i in range(3,8)]
  if name=='read':
   assert args[0]==0x1110 and args[1]==BUFFER and args[2]==128
   if read_ok and tick>=ready_tick:uc.mem_write(BUFFER,bytes(range(128)))
   ret=int(read_ok)
  elif name=='poll':
   assert args[:3]==[0x1110,0,0],args # same original zero-timeout, non-alertable poll
   ret=0xffffffff if wait_failure else (0 if tick>=ready_tick else 0x102)
   if ret==0:uc.mem_write(BUFFER,bytes(range(128)))
  elif name=='close':assert args[0]==0x1110;ret=1
  elif name=='last_error':ret=last_error
  elif name=='exit_thread':aborted=True;events.append((name,args[0]));uc.emu_stop();return
  elif name=='memory_query':assert args[0]==BUFFER;ret=0x400 if protect else 0
  elif name=='memory_protect':assert args[:3]==[BUFFER,128,4];ret=1
  events.append((name,tuple(args[:3]) if name=='poll' else args[0]))
  # Volatile register destruction ensures the wrapper follows the actual ABI.
  for i in [0,4,5,6,7,8,9,10,11,12]:uc.reg_write(getattr(sys.modules['unicorn.ppc_const'],'UC_PPC_REG_'+str(i)),0xfee10000+i)
  uc.reg_write(UC_PPC_REG_3,ret);uc.reg_write(UC_PPC_REG_PC,uc.reg_read(UC_PPC_REG_LR))
 u.hook_add(UC_HOOK_CODE,hook)
 result=None
 for tick in range(12):
  event_start=len(events)
  body=0;u.reg_write(UC_PPC_REG_1,STACK);u.reg_write(UC_PPC_REG_3,BUFFER);u.reg_write(UC_PPC_REG_LR,STOP)
  try:u.emu_start(ENTRY,STOP,count=1500)
  except Exception as e:raise RuntimeError((patched,start_state,ready_tick,read_ok,last_error,protect,wait_failure,hex(u.reg_read(UC_PPC_REG_PC)),trace[-60:])) from e
  counts.append(body)
  if aborted:break
  assert u.reg_read(UC_PPC_REG_PC)==STOP,'instruction limit / bad return'
  assert u.reg_read(UC_PPC_REG_1)==STACK,'stack mismatch'
  for reg,value in nonvol.items():assert u.reg_read(reg)==value,('nonvolatile register',reg)
  assert u.reg_read(UC_PPC_REG_CR)&0x00fff000==0x00345000,'nonvolatile condition fields'
  assert sum(e[0]=='read' for e in events[event_start:])<=1,'repeated pending/failed read within one invocation'
  assert sum(e[0]=='poll' for e in events[event_start:])<=1,'busy polling within one invocation'
  result=u.reg_read(UC_PPC_REG_3)&0xffffffff
  assert body<=(4 if patched else 1)
  if result==1:
   assert start_state==3 or tick>=ready_tick,'completion before data readiness'
   break
 return {'state':r(STATE),'return':result,'aborted':aborted,'events':events,'calls':counts,'buffer':bytes(u.mem_read(BUFFER,128)).hex(),'outer_calls':len(counts),'handle':r(0x82706f90)}
def main():
 results=[]
 for state,ready,read_ok,error,protect,waitfail in itertools.product([0,1,2,3,4,0xffffffff],[0,3],[False,True],[0,5],[False,True],[False,True]):
  kw=dict(start_state=state,ready_tick=ready,read_ok=read_ok,last_error=error,protect=protect,wait_failure=waitfail)
  old=scenario(False,**kw);new=scenario(True,**kw)
  for k in ['state','aborted','buffer','handle']+([] if old['aborted'] else ['return']):assert old[k]==new[k],(kw,k,old[k],new[k])
  # A permanently failing read can be retried once per outer call in either routine.
  trace0=[e for e in old['events'] if e[0]!='poll'];trace1=[e for e in new['events'] if e[0]!='poll']
  if not read_ok:
   trace0=[k for k,g in itertools.groupby(trace0)];trace1=[k for k,g in itertools.groupby(trace1)]
  assert trace0==trace1,(kw,trace0,trace1)
  results.append({'case':kw,'original_calls':old['outer_calls'],'test_calls':new['outer_calls'],'max_inner_calls':max(new['calls'])})
 fast0=scenario(False);fast1=scenario(True)
 assert fast0['outer_calls']==4 and fast1['outer_calls']==1
 report={'engine':'Unicorn 2.1.4 PPC64 default POWER10, MSR=0, virtual TLB; actual instructions including ld/std, only external APIs mocked','tested_cases':len(results),'original_and_test_final_results_match':True,'nonblocking_wait_arguments_preserved':True,'nonvolatile_registers_and_stack_preserved':True,'ready_immediately_original_outer_calls':4,'ready_immediately_test_outer_calls':1,'max_steps':4,'actual_xenia_or_wall_time_test':False,'cases':results}
 (R/'audit/ppc_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
