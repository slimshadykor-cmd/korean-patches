import sys,json,struct
sys.path.insert(0,'.')
from check_save import *
from unicorn import UC_HOOK_CODE
Z=json.loads(Path('settings_analysis/build.json').read_text())['symbols']
count=0
for live in [False,True]:
 for mode in [0,1]:
  for bits in range(8):
   u=cpu();ptr=BASE if live else 0x1700000;dst=0x1800000
   u.mem_write(ptr+SIZE-12,b'NGBSTRM1'+struct.pack('<HH',bits,bits^0xffff));put(u,S['STORM_MODE'],mode)
   u.reg_write(UC_X86_REG_EDI,ptr);u.reg_write(UC_X86_REG_ESI,dst);u.mem_write(dst,b'Q'*0x78)
   call(u,Z['preview_mode']);v=bytes(u.mem_read(dst,0x78));assert v[:0x75]==b'Q'*0x75;assert v[0x75:]==bytes([mode if live else bits&1])+b'SM';count+=1
for bad in [bytes(12),b'NGBSTRM1'+struct.pack('<HH',8,0xfff7),b'NGBSTRM1'+bytes(4)]:
 u=cpu();u.mem_write(0x1700000+SIZE-12,bad);u.reg_write(UC_X86_REG_EDI,0x1700000);u.reg_write(UC_X86_REG_ESI,0x1800000);call(u,Z['preview_mode']);assert u.mem_read(0x1800075,1)==b'\2';count+=1
render=[]
for language in [0,1]:
 for mode in [0,1,2]:
  for y in [-200,0,200]:
   u=cpu();u.mem_write(0x229f20,b'\xc3');p=0x1800000;u.mem_write(p+0x1c,b'\1');u.mem_write(p+0x75,bytes([mode])+b'SM');put(u,0xdb9890,language)
   captured=[]
   def hook(u,a,n,d):
    if a==0x1e6d30:
     sp=u.reg_read(UC_X86_REG_ESP);desc=get(u,sp+4);captured.append(bytes(u.mem_read(desc,0x54)));u.reg_write(UC_X86_REG_EIP,get(u,sp));u.reg_write(UC_X86_REG_ESP,sp+4)
   u.hook_add(UC_HOOK_CODE,hook);u.mem_write(STACK,struct.pack('<III',STOP,p,0x3f000000));u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EAX,y&0xffffffff);u.emu_start(Z['slot_draw'],STOP,count=100000)
   assert u.reg_read(UC_X86_REG_EIP)==STOP and u.reg_read(UC_X86_REG_ESP)==STACK+4
   assert len(captured)==1
   desc=captured[0];assert struct.unpack_from('<hh',desc,0x44)==(164,y+143)
   label=('unknown' if mode==2 else 'storm' if mode else 'black')+('_ko' if language==0 else '_en');assert struct.unpack_from('<I',desc,0x10)[0]==Z[label]
   assert struct.unpack_from('<I',desc,0x14)[0]==0x3f000000
   render.append(dict(language=language,mode=mode,y=y))
for status in [-1,-3,-4,-5,-6,-7,0]:
 u=cpu();u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EBP,status&0xffffffff);put(u,STACK+0x328,0xdb9380);put(u,STACK+0x32c,0x508);put(u,STACK+0x318,0x1234);run(u,0x30fe6a,0x30fe71)
 assert get(u,Z['last_profile_status'])==status&0xffffffff;assert u.reg_read(UC_X86_REG_EBP)==status&0xffffffff
for code in [0,-1,-3,-4,-5,-6,-7,0x100,0x80000005,0x1234abcd]:
 u=cpu();put(u,Z['last_profile_status'],0xfffffffa);u.reg_write(UC_X86_REG_EBX,code&0xffffffff);u.reg_write(UC_X86_REG_ESP,STACK);run(u,0x168937,0x168941)
 assert bytes(u.mem_read(Z['en_digit'],8)).decode()==f'{code&0xffffffff:08X}'
 assert bytes(u.mem_read(Z['en_read'],8))==b'FFFFFFFA'
 assert bytes(u.mem_read(Z['warning_digits'],16)).decode('cp932')==''.join(chr(ord(c)+0xfee0) for c in f'{code&0xffffffff:08X}')
 assert u.reg_read(UC_X86_REG_EBX)==0x100 and u.reg_read(UC_X86_REG_EBP)==1
report=dict(warning_entry_cases=10,preview_cases=count,label_draw_descriptor_cases=len(render),settings_error_cases=7,scope='Actual x86 metadata/hooks; native text descriptor construction. GPU and xemu not run. Error warning retained; no settings recovery claimed.')
Path('settings_analysis/verification.json').write_text(json.dumps(report,indent=2));print(report)
