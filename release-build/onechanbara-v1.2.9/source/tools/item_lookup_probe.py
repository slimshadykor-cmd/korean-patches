from audit_common import *
import unicorn as u
from unicorn.ppc_const import *
orig=(W/'original.memory.bin').read_bytes();rows=[]
for i in range(35):
 ident,key,label,desc=struct.unpack_from('>4I',orig,0x6e4860+i*16)
 rows.append((ident,cstr(orig,key-0x82000000),label,desc))
report=[]
for version in ['original','current','candidate']:
 b=(W/(version+'.memory.bin')).read_bytes();uc=u.Uc(u.UC_ARCH_PPC,u.UC_MODE_64|u.UC_MODE_BIG_ENDIAN);uc.ctl_set_tlb_mode(u.UC_TLB_VIRTUAL);uc.reg_write(UC_PPC_REG_MSR,0)
 uc.mem_map(0x82000000,(len(b)+4095)&~4095);uc.mem_write(0x82000000,b);uc.mem_map(0x90000000,0x20000);uc.mem_map(0x91000000,4096)
 for ident,key,label,desc in rows:
  results=[]
  for address,expected in [(0x82293d70,ident),(0x82293de0,label),(0x82293e58,desc)]:
   uc.mem_write(0x91000000,key+b'\0');uc.reg_write(UC_PPC_REG_1,0x90010000);uc.reg_write(UC_PPC_REG_3,0);uc.reg_write(UC_PPC_REG_4,0x91000000);uc.reg_write(UC_PPC_REG_LR,0x90001000)
   uc.emu_start(address,0x90001000,count=100000)
   actual=(uc.reg_read(UC_PPC_REG_3)&0xffffffff);assert actual==expected,(version,key,hex(address),hex(actual),hex(expected));results.append(actual)
  report.append({'version':version,'key':key.decode('cp932'),'id':ident,'display_pointer':hex(results[1]),'display_text':cstr(b,label-0x82000000).decode('cp932') if version=='original' else decoded(cstr(b,label-0x82000000)),'description_pointer':hex(results[2]),'passed':True})
writej('item_lookup_machinecode_probe.json',{'method':'Run original PPC ID/name/description lookup functions against 35 original keys for original, public v1.2.8, and local candidate memories; 315 actual function calls. This is not full gameplay.','tests':315,'results':report})
print('315 key-ID/name/description machine-code lookups passed; candidate display labels match v1.2.8.')
