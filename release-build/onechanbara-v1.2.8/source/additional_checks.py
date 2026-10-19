from pathlib import Path
import sys,json,struct
W=Path(__file__).resolve().parent;A=W.parent/'audit_identifiers_20261019';sys.path.insert(0,str(A))
from audit_common import cstr,decoded
import unicorn as u
from unicorn.ppc_const import *
OUT=W/'audit';OUT.mkdir(exist_ok=True)
original=(A/'original.memory.bin').read_bytes();versions={n:(A/(n+'.memory.bin')).read_bytes() for n in ['original','current','candidate']}
def setup(b):
 uc=u.Uc(u.UC_ARCH_PPC,u.UC_MODE_PPC32|u.UC_MODE_BIG_ENDIAN);uc.mem_map(0x82000000,(len(b)+4095)&~4095);uc.mem_write(0x82000000,b);uc.mem_map(0x90000000,0x20000);uc.mem_map(0x91000000,4096)
 return uc
def reset(uc,text):
 uc.mem_write(0x91000000,text+b'\0');uc.reg_write(UC_PPC_REG_1,0x90010000);uc.reg_write(UC_PPC_REG_3,0);uc.reg_write(UC_PPC_REG_4,0);uc.reg_write(UC_PPC_REG_LR,0x90001000)
def filename_stub(uc,address,size,data):
 if address in [0x822948c8,0x822949c0]:uc.reg_write(UC_PPC_REG_3,0x91000000);uc.reg_write(UC_PPC_REG_PC,uc.reg_read(UC_PPC_REG_LR))
areas=[];props=[];creation=[]
filenames=[cstr(original,0x6e12f8+i*76+12) for i in range(96)]
propnames=[cstr(original,0x6e40c0+i*72+8) for i in range(26)]
for version,b in versions.items():
 uc=setup(b);uc.hook_add(u.UC_HOOK_CODE,filename_stub)
 for name in filenames:
  reset(uc,name);uc.emu_start(0x82296e20,0x90001000,count=100000)
  ret=uc.reg_read(UC_PPC_REG_3);expect=0x82000000+0x6e12f8+filenames.index(name)*76+44
  assert ret==expect,(version,name,hex(ret),hex(expect))
  areas.append({'version':version,'filename':name.decode('ascii'),'label_pointer':hex(ret),'label':cstr(b,ret-0x82000000).decode('cp932') if version=='original' else decoded(cstr(b,ret-0x82000000))})
 for name in propnames+[b'unknown-object']:
  for mode,key in [(1,cstr(original,0x34eb0)),(2,cstr(original,0x34eb8))]:
   reset(uc,name);uc.reg_write(UC_PPC_REG_5,mode);uc.emu_start(0x82297090,0x90001000,count=100000)
   ret=uc.reg_read(UC_PPC_REG_3);expect=int(key in name);assert ret==expect,(version,name,mode,ret)
   props.append({'version':version,'object':name.decode('cp932'),'mode':mode,'result':ret,'matches_original':True})
 for i in range(35):
  ident,key,_,_=struct.unpack_from('>4I',original,0x6e4860+i*16);name=cstr(original,key-0x82000000)
  reset(uc,name);uc.reg_write(UC_PPC_REG_30,0x91000000);uc.reg_write(UC_PPC_REG_31,0)
  uc.emu_start(0x82294f04,0x82294f48,count=100000)
  typ=struct.unpack('>I',uc.mem_read(0x90010000+0x90,4))[0];itemid=struct.unpack('>I',uc.mem_read(0x90010000+0x98,4))[0]
  expected=13 if i>=23 else 14
  if version!='current':assert typ==expected and itemid==(ident if i>=23 else 0)
  creation.append({'version':version,'key':name.decode('cp932'),'category':typ,'expected_category':expected,'item_id':itemid,'matches_original':typ==expected})
report={'additional_bug_count':0,'area_lookup_tests':len(areas),'prop_classification_tests':len(props),'item_creation_branch_tests':len(creation),'v127_creation_mismatches':sum(r['version']=='current' and not r['matches_original'] for r in creation),'candidate_creation_mismatches':sum(r['version']=='candidate' and not r['matches_original'] for r in creation),'areas':areas,'props':props,'item_creation':creation,'method':'Original PPC instructions run in Unicorn. Area/object-name getters are stubbed to supplied original lookup strings; classification/search and item category selection execute original instructions. This is function-level emulation, not Xenia gameplay.'}
(OUT/'additional_function_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print({k:v for k,v in report.items() if k not in ['areas','props','item_creation']})
