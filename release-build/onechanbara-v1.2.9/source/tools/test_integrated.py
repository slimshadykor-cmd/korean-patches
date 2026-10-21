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
rows=manifest((P/'manifest.tsv').read_bytes());oldrows=manifest((W/'baseline_package/manifest.tsv').read_bytes())
assert all(set(oldrows[k][3].split(','))<=set(r[3].split(',')) for k,r in rows.items())
original={p.relative_to(W/'original').as_posix():p.read_bytes() for p in (W/'original').rglob('*') if p.is_file()}
expected={};current={};movies=[]
for rel,row in rows.items():
 raw=(P/'payload'/row[4]).read_bytes();oldraw=(W/'baseline_package/payload'/row[4]).read_bytes()
 if '/Movie/' in rel or '/DMovie' in rel:
  assert raw==oldraw;original[rel]=raw;movies.append(rel)
 else:assert rel in original and sha(original[rel]) in row[3].split(',')
 expected[rel]=delta(original[rel],raw) if row[5]=='delta' else raw
 current[rel]=delta(original[rel],oldraw) if row[5]=='delta' else oldraw
 assert sha(expected[rel])==row[2] and sha(current[rel])==oldrows[rel][2]
 if rel not in ['default.xex','Media/Menu/title2d.cat']:assert row==oldrows[rel] and raw==oldraw
original['untouched.bin']=b'UNCHANGED INPUT SENTINEL\0'*100
DOTNET=W/'deps/sdk/dotnet';EXE=W/'deliverables/Onechanbara_ISO_Korean_v1.2.9.exe';tests=[];rejections=[]
with tempfile.TemporaryDirectory(prefix='integrated-check-',dir=W) as tmp:
 tmp=Path(tmp);temp=tmp/'temp';temp.mkdir();env=dict(os.environ,TMPDIR=str(temp))
 def run(src,dst,ok=True,contains=None):
  p=subprocess.run([str(DOTNET),str(W/'ShippingDriver.dll'),str(EXE),str(src),str(dst)],capture_output=True,text=True,env=env)
  assert (p.returncode==0)==ok,(p.stdout[-2000:],p.stderr)
  if contains:assert contains in p.stderr,p.stderr
  assert not list(temp.glob('OnechanbaraPatch_*')) and not Path(str(dst)+'.partial').exists(), {'temp':[(str(q),len(list(q.rglob('*')))) for q in temp.glob('OnechanbaraPatch_*')], 'partial':Path(str(dst)+'.partial').exists(), 'stdout':p.stdout[-1000:], 'stderr':p.stderr}
  return p
 for version,base in [('original',0),('v125',0xfb20),('v128',0x20600),('Test01-JP',0x2080000),('Test01-KOR',0xfd90000)]:
  files=dict(original)
  if version=='v125':
   with zipfile.ZipFile(W/'v125.exe') as z:
    for rel,row in manifest(z.read('manifest.tsv')).items():
     raw=z.read('payload/'+row[4]);files[rel]=delta(original[rel],raw) if row[5]=='delta' else raw;assert sha(files[rel])==row[2]
  elif version in ['v128','Test01-KOR']:files.update(current)
  if version.startswith('Test01'):files['default.xex']=(W/('jp_test01.xex' if version=='Test01-JP' else 'kor128_test01.xex')).read_bytes()
  for rel,row in rows.items():assert sha(files[rel])==row[2] or sha(files[rel]) in row[3].split(','),(version,rel)
  src=tmp/'input.iso';dst=tmp/'output.iso';create_iso(src,files,base);before=digest(src);run(src,dst);assert digest(src)==before
  entries=read_entries(dst,base);assert set(entries)==set(files)
  with dst.open('rb') as f:
   for rel,data in files.items():
    off,n=entries[rel];f.seek(off);assert f.read(n)==expected.get(rel,data),(version,rel)
  tests.append({'input':version,'base':hex(base),'all_158_targets_byte_exact':True,'unrelated_assets_and_input_preserved':True,'shipping_exe_core_executed':True,'temp_cleaned':True});print(tests[-1],flush=True)
  if version=='v128':
   run(dst,tmp/'repeat.iso',False,'이미');assert not (tmp/'repeat.iso').exists();rejections.append('already-patched')
   keep=digest(dst);run(src,dst,False,'출력 파일');assert digest(dst)==keep;rejections.append('existing-output')
   run(src,src,False,'출력 파일');assert digest(src)==before;rejections.append('input-equals-output')
   off,n=read_entries(src,base)['default.xex']
   with src.open('r+b') as f:f.seek(off+64);f.write(b'BAD!')
   damaged=digest(src);run(src,tmp/'bad.iso',False,'지원하는 일본판');assert digest(src)==damaged and not (tmp/'bad.iso').exists();rejections.append('unknown-xex')
  src.unlink();dst.unlink()
 # Missing required assets and invalid directory metadata fail before output creation.
 small=tmp/'invalid.iso';small.write_bytes(b'not-an-iso');run(small,tmp/'invalid-out.iso',False,'ISO 구조');rejections.append('invalid-iso')
report={'tests':tests,'rejections':rejections,'manifest_paths':len(rows),'unchanged_movie_paths':len(movies),'older_accepted_hashes_retained':True,'actual_shipping_exe_managed_core_executed':True,'windows_gui_runtime_tested':False,'actual_xenia_gameplay_tested_by_assistant':False,'fixture':'Synthetic XDVDFS with supplied original nonvideo assets and real v125/v128/Test01 files. Video payloads are already Korean. This is not execution of a full original retail ISO.'}
(W/'audit/iso_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report,flush=True)
