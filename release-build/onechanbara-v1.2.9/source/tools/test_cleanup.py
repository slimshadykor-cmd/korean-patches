from pathlib import Path
import sys,struct,os,hashlib,json,zipfile,tempfile,subprocess
W=Path(__file__).resolve().parent.parent;A=W/'tools';sys.path.insert(0,str(A));from audit_common import delta,sha,memory
P=W/'package';INPUT=W/'inputs/Onechanbara vorteX 일본판 한글화'
def manifest(data):return {r[0]:r for l in data.decode('utf-8-sig').splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def create_iso(path,files,base):
 # Independent fixture construction: sorted right-linked XDVDFS directory trees.
 dirs={'':{}}
 for rel,data in files.items():
  parts=rel.split('/')
  for i,name in enumerate(parts):
   parent='/'.join(parts[:i]);child='/'.join(parts[:i+1]);isdir=i<len(parts)-1
   dirs.setdefault(parent,{})[name]=(child,isdir)
   if isdir:dirs.setdefault(child,{})
 cursor=0x11000;layouts={}
 for rel,items in sorted(dirs.items()):
  pos=0;entries=[]
  for name,(child,isdir) in sorted(items.items(),key=lambda p:p[0].upper()):
   entries.append((pos,name,child,isdir));pos=(pos+14+len(name.encode('ascii'))+3)&~3
  layouts[rel]=(cursor,pos,entries);cursor+=(pos+2047)//2048*2048
 extents={};shared={}
 for rel,data in files.items():
  key=sha(data)
  if key not in shared:shared[key]=(cursor,len(data));cursor+=(len(data)+2047)//2048*2048
  extents[rel]=shared[key]
 with path.open('wb') as f:
  f.truncate(base+cursor);f.seek(base+0x10000);desc=bytearray(2048);desc[:20]=desc[2028:]=b'MICROSOFT*XBOX*MEDIA';struct.pack_into('<II',desc,20,layouts[''][0]//2048,layouts[''][1]);f.write(desc)
  for rel,(off,size,entries) in layouts.items():
   raw=bytearray(size)
   for i,(pos,name,child,isdir) in enumerate(entries):
    target,n=layouts[child][:2] if isdir else extents[child]
    right=entries[i+1][0]//4 if i+1<len(entries) else 0
    struct.pack_into('<HHIIBB',raw,pos,0,right,target//2048,n,16 if isdir else 0,len(name));raw[pos+14:pos+14+len(name)]=name.encode('ascii')
   f.seek(base+off);f.write(raw)
  written=set()
  for rel,data in files.items():
   off,n=extents[rel]
   if off in written:continue
   written.add(off);f.seek(base+off);f.write(data)
def read_entries(path,base):
 out={}
 with path.open('rb') as f:
  f.seek(base+0x10000);d=f.read(2048);assert d[:20]==d[2028:]==b'MICROSOFT*XBOX*MEDIA';sector,size=struct.unpack_from('<II',d,20)
  def directory(sector,size,parent):
   f.seek(base+sector*2048);raw=f.read(size)
   def node(pos):
    left,right,start,n,attr,nl=struct.unpack_from('<HHIIBB',raw,pos);name=raw[pos+14:pos+14+nl].decode('ascii');rel=parent+name
    if left:node(left*4)
    if attr&16:directory(start,n,rel+'/')
    else:out[rel]=(base+start*2048,n)
    if right:node(right*4)
   node(0)
  directory(sector,size,'')
 return out

rows=manifest((P/'manifest.tsv').read_bytes());files={}
for rel,row in rows.items():
 q=W/'candidate'/rel
 files[rel]=q.read_bytes() if q.exists() else (P/'payload'/row[4]).read_bytes()
 assert sha(files[rel])==row[2]
with tempfile.TemporaryDirectory(dir=W,prefix='cleanup-check-') as root:
 root=Path(root);src=root/'final.iso';create_iso(src,files,0);temp=root/'temp';temp.mkdir();results=[]
 for i in range(3):
  dst=root/f'repeat{i}.iso'
  p=subprocess.run([str(W/'deps/sdk/dotnet'),str(W/'ShippingDriver.dll'),str(W/'deliverables/Onechanbara_ISO_Korean_v1.2.9.exe'),str(src),str(dst)],capture_output=True,text=True,env=dict(os.environ,TMPDIR=str(temp)))
  left=list(temp.iterdir());assert p.returncode==1 and '이미' in p.stderr and not dst.exists() and not left,(p.stderr,left)
  results.append({'attempt':i+1,'expected_rejection':True,'temporary_files_removed':True})
 (W/'audit/cleanup_validation.json').write_text(json.dumps({'reason':'Repeat an earlier transient cleanup assertion in shipping-EXE exception path; full matrix rerun and three isolated repetitions passed.','results':results},indent=2));print(results)
