import sys,json,itertools
from pathlib import Path
sys.path.insert(0,'.')
from check_save import *
sym=json.load(open('profile_fix/build.json'))['symbols'];cases=0
for typ,buf,size,validator,work,worksize in itertools.product([0,1],[BASE,0xdb9380],[SIZE,0x508],[0,0x1da9e0],[0,0x1900000],[0,0x44000]):
 u=cpu();args=[typ,0,buf,size,validator,work,worksize];u.mem_write(STACK,struct.pack('<8I',STOP,*args));u.reg_write(UC_X86_REG_ESP,STACK);run(u,0x30fce0,0x30fce6)
 got=list(struct.unpack('<7I',u.mem_read(STACK+4,28)));expected=args.copy()
 if typ==1 and buf==0xdb9380 and size==0x508 and validator==0x1da9e0 and work==0:expected[5:]=[sym['profile_workspace'],0x4000]
 assert got==expected and u.reg_read(UC_X86_REG_ESP)==STACK-0x30c
 cases+=1
Path('profile_fix/scope.json').write_text(json.dumps({'cases':cases,'result':'PASS','condition':'Only default work buffer for exact system settings target; provided work buffers and other read targets unchanged'},indent=2));print(cases,'scope cases passed')
