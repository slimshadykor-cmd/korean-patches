from pathlib import Path
import zipfile,io,struct,json,gzip,hashlib,numpy as np,shutil
W=Path(__file__).resolve().parent;B=W/'publication/release-build/onechanbara-v1.2.9';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(W/'baseline.exe').read_bytes();new=(W/'deliverables/Onechanbara_ISO_Korean_v1.2.9.exe').read_bytes()
oz=zipfile.ZipFile(io.BytesIO(old));nz=zipfile.ZipFile(io.BytesIO(new));commands=[];literals=bytearray();cursor=0

def literal(b):
 if b:commands.append(['literal',len(literals),len(b)]);literals.extend(b)
def copy(at,n):
 if n:commands.append(['copy',at,n])
def data_at(b,e):
 at=e.header_offset;assert b[at:at+4]==b'PK\x03\x04';n,x=struct.unpack_from('<HH',b,at+26);return at+30+n+x
for e in nz.infolist():
 oe=oz.getinfo(e.filename);assert e.compress_type==oe.compress_type==zipfile.ZIP_STORED;na=data_at(new,e);oa=data_at(old,oe)
 literal(new[cursor:na]);a=old[oa:oa+oe.file_size];b=new[na:na+e.file_size]
 if len(a)==len(b) and len(a)>=1024:
  same=np.frombuffer(a,dtype='u1')==np.frombuffer(b,dtype='u1');edges=np.flatnonzero(np.diff(np.concatenate(([False],same,[False])).astype('i1')));pos=0
  for start,end in zip(edges[::2],edges[1::2]):
   start=int(start);end=int(end)
   if end-start<1024:continue
   literal(b[pos:start]);copy(oa+start,end-start);pos=end
  literal(b[pos:]);cursor=na+len(b);continue
 n=min(len(a),len(b));diff=np.flatnonzero(np.frombuffer(a[:n],dtype='u1')!=np.frombuffer(b[:n],dtype='u1'));prefix=int(diff[0]) if len(diff) else n;suffix=0
 if prefix<len(b) and prefix<len(a):
  limit=n-prefix;diff=np.flatnonzero(np.frombuffer(a[-limit:][::-1],dtype='u1')!=np.frombuffer(b[-limit:][::-1],dtype='u1'));suffix=int(diff[0]) if len(diff) else limit
 copy(oa,prefix);literal(b[prefix:len(b)-suffix if suffix else len(b)])
 if suffix:copy(oa+len(a)-suffix,suffix)
 cursor=na+len(b)
literal(new[cursor:]);compressed=gzip.compress(literals,compresslevel=9,mtime=0);parts=[]
for i,at in enumerate(range(0,len(compressed),131072)):
 name=f'release-literals.part{i:03}';(B/name).write_bytes(compressed[at:at+131072]);parts.append(name)
meta=json.loads((W/'audit/release_validation.json').read_text())
recipe={'format':'verified-exe-copy-literal-v1','baseline_release_url':'https://github.com/slimshadykor-cmd/korean-patches/releases/download/onechanbara-v1.2.8/Onechanbara_ISO_Korean_v1.2.8_Release.zip','baseline_release_sha256':'12bf37abcf391a6d0476cd986d7008ae32bd06efccb613d8b95c7a1a6c1a8b84','baseline_exe':'Onechanbara_ISO_Korean_v1.2.8.exe','baseline_exe_sha256':sha(old),'result_exe':'Onechanbara_ISO_Korean_v1.2.9.exe','result_exe_sha256':sha(new),'result_exe_size':len(new),'literals_sha256':sha(literals),'compressed_literals_sha256':sha(compressed),'literal_parts':parts,'commands':commands,'inner_manifest_sha256':sha((W/'package/manifest.tsv').read_bytes()),'public_files':meta['release_files'],'release_sha256':meta['release_sha256']}
assert sum(c[2] for c in commands)==len(new)
reconstructed=bytearray()
for kind,at,n in commands:reconstructed.extend((old if kind=='copy' else literals)[at:at+n])
assert reconstructed==new
(B/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False))

script=(W/'baseline_source/release-build/onechanbara-v1.2.8/build_release.py').read_text().replace('v1.2.8','v1.2.9').replace('v1.2.7','v1.2.8').replace('baseline-v127','baseline-v128').replace('(2026,10,19,0,0,0)','(2026,10,21,0,0,0)')
(B/'build_release.py').write_text(script)
shutil.copytree(W/'source',B/'source',dirs_exist_ok=True)
shutil.copytree(W/'tools',B/'source/tools',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for f in ['bootstrap.py','prepare_audits.py','build_integrated.py','finish_release.py','create_recipe.py']:shutil.copyfile(W/f,B/'source'/f)
shutil.copytree(W/'audit',B/'audit',dirs_exist_ok=True)
print({'literal_bytes':len(compressed),'parts':len(parts),'baseline_bytes_reused':sum(n for kind,at,n in commands if kind=='copy'),'exact_reconstruction':True})
