from pathlib import Path
import struct,re,json,hashlib,gzip
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
R=Path(__file__).resolve().parent.parent;A=R;BASE=0x82000000
sha=lambda b:hashlib.sha256(b).hexdigest()
src=(A/'workbench/analysis/source/xex_module.cc').read_text()
keydef=re.search(r'xe_xex2_retail_key\[16\]\s*=\s*\{([^}]+)',src).group(1)
KEY=bytes(int(a,16) for a in re.findall(r'0x([0-9a-fA-F]{2})',keydef))
def aes(key,data,enc=False):
 c=Cipher(algorithms.AES(key),modes.CBC(bytes(16)));t=c.encryptor() if enc else c.decryptor();return t.update(data)+t.finalize()
def unpack(x):
 assert x[:4]==b'XEX2';off,sec=struct.unpack_from('>I',x,8)[0],struct.unpack_from('>I',x,16)[0]
 h=dict(struct.unpack_from('>II',x,24+i*8) for i in range(struct.unpack_from('>I',x,20)[0]));sz,en,co=struct.unpack_from('>IHH',x,h[0x3ff]);assert (en,co)==(1,1)
 blocks=[struct.unpack_from('>II',x,h[0x3ff]+8+8*i) for i in range((sz-8)//8)]
 key=aes(KEY,x[sec+0x150:sec+0x160]);p=aes(key,x[off:]);assert sum(n for n,z in blocks)==len(p)
 m=bytearray();at=0
 for n,z in blocks:m+=p[at:at+n]+bytes(z);at+=n
 return m,(off,blocks,key)
def repack(x,m,fmt):
 off,blocks,key=fmt;at=0;parts=[]
 for n,z in blocks:
  parts.append(m[at:at+n]);assert not any(m[at+n:at+n+z]);at+=n+z
 assert at==len(m)
 return x[:off]+aes(key,b''.join(parts),True)
def branch(at,target,link=False):
 d=target-at;assert d%4==0 and -0x2000000<=d<0x2000000
 return 0x48000000|(d&0x3fffffc)|int(link)
def dform(op,rt,ra,imm):return (op<<26)|(rt<<21)|(ra<<16)|(imm&65535)
def cmpi(ra,imm,unsigned=False):return ((10 if unsigned else 11)<<26)|(6<<23)|(ra<<16)|(imm&65535)
def mr(rt,rs):return (31<<26)|(rs<<21)|(rt<<16)|(rs<<11)|(444<<1)
START=0x82666900;ORIGINAL=0x824ecd68;STATE=0x87356f60
ops=[];labels={};fix=[]
def emit(v):ops.append(v)
def mark(n):labels[n]=START+len(ops)*4
def bc(cond,label):fix.append((len(ops),'bc',cond,label));emit(0)
def b(label,link=False):fix.append((len(ops),'b',link,label));emit(0)
emit(0x7d8802a6) # mflr r12
emit(branch(START+len(ops)*4,0x826454c8,True)) # save r28-r31 and caller LR
emit(dform(37,1,1,-0x90)) # stwu r1,-0x90(r1)
emit(mr(31,3));emit(dform(15,29,0,STATE>>16));emit(dform(24,29,29,STATE&65535));emit(dform(14,30,0,4))
mark('loop');emit(dform(32,28,29,0));emit(mr(3,31));b('original',True)
emit(cmpi(3,1));bc('eq','exit')
emit(dform(14,30,30,-1));emit(cmpi(30,0));bc('eq','exit')
emit(dform(32,11,29,0));emit(cmpi(11,3,True));bc('gt','exit')
emit((31<<26)|(6<<23)|(11<<16)|(28<<11)|(32<<1)) # cmplw cr6,r11,r28
bc('le','exit');b('loop')
mark('exit');emit(dform(14,1,1,0x90));emit(branch(START+len(ops)*4,0x82645518))
mark('original');emit(0x7d8802a6);emit(branch(START+len(ops)*4,ORIGINAL+4))
for i,kind,cond,label in fix:
 at=START+i*4;to=labels[label]
 if kind=='b':ops[i]=branch(at,to,cond)
 else:
  bo,bi={'eq':(12,26),'gt':(12,25),'le':(4,25)}[cond];disp=to-at;assert -32768<=disp<32768
  ops[i]=(16<<26)|(bo<<21)|(bi<<16)|(disp&65532)
code=b''.join(struct.pack('>I',v) for v in ops);assert len(code)<=256
def apply_memory(m):
 out=bytearray(m);assert out[ORIGINAL-BASE:ORIGINAL-BASE+4]==bytes.fromhex('7d8802a6');assert not any(out[START-BASE:START-BASE+len(code)])
 out[ORIGINAL-BASE:ORIGINAL-BASE+4]=struct.pack('>I',branch(ORIGINAL,START));out[START-BASE:START-BASE+len(code)]=code
 pe=struct.unpack_from('<I',out,0x3c)[0];opt=struct.unpack_from('<H',out,pe+20)[0];found=False
 for i in range(struct.unpack_from('<H',out,pe+6)[0]):
  p=pe+24+opt+i*40
  if out[p:p+8].rstrip(b'\0')==b'.text':
   vs,va,rs,raw=struct.unpack_from('<4I',out,p+8);assert BASE+va+vs<=START and START-BASE+len(code)<=va+rs
   struct.pack_into('<I',out,p+8,START-BASE+len(code)-va);found=True
 assert found
 return out
def main():
 (R/'hook.bin').write_bytes(code)
 info={'experiment':'Loading Test 01','max_calls_per_invocation':4,'entry':hex(ORIGINAL),'hook':hex(START),'hook_bytes':len(code),'state':hex(STATE),'trampoline':hex(labels['original']),'targets':[],'actual_xenia_tested':False}
 for name,path in [('jp',R/'original/default.xex'),('kor128',R/'current/default.xex')]:
  x=path.read_bytes();m,fmt=unpack(x);assert repack(x,m,fmt)==x
  out=apply_memory(m);result=repack(x,out,fmt);assert len(result)==len(x) and unpack(result)[0]==out
  changes=[i for i,(a,b) in enumerate(zip(m,out)) if a!=b];allowed=set(range(0x230,0x234))|set(range(ORIGINAL-BASE,ORIGINAL-BASE+4))|set(range(START-BASE,START-BASE+len(code)));assert set(changes)<=allowed
  (R/(name+'_test01.xex')).write_bytes(result);(R/(name+'_test01.memory.bin')).write_bytes(out)
  # XOR is reversible, and only used after exact source/target hash validation.
  delta=bytes(a^b for a,b in zip(x,result));(R/(name+'.xor.gz')).write_bytes(gzip.compress(delta,9,mtime=0))
  info['targets'].append({'name':name,'size':len(x),'input_sha256':sha(x),'output_sha256':sha(result),'logical_changed_bytes':len(changes),'logical_changed_offsets':[hex(i) for i in changes]})
 (R/'audit/candidate.json').write_text(json.dumps(info,indent=2));print(json.dumps({k:v for k,v in info.items() if k!='targets'}));print([(t['name'],t['output_sha256'],t['logical_changed_bytes']) for t in info['targets']])
if __name__=='__main__':main()
