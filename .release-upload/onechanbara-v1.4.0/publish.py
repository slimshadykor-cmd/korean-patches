from pathlib import Path
import os,sys,json,gzip,zipfile,hashlib,struct,io,urllib.request,subprocess,re
Q=Path(__file__).resolve().parent;REPO='slimshadykor-cmd/korean-patches';TAG='onechanbara-v1.4.0';API='https://api.github.com/repos/'+REPO
sha=lambda b:hashlib.sha256(b).hexdigest()
def aes(key,data,dec=False):
 cmd=['openssl','enc','-aes-128-cbc','-K',key.hex(),'-iv','00'*16,'-nopad']
 if dec:cmd.append('-d')
 return subprocess.run(cmd,input=data,capture_output=True,check=True).stdout
def patch_xex(x,delta):
 assert sha(x)==delta['old_sha256'];off=struct.unpack_from('>I',x,8)[0];sec=struct.unpack_from('>I',x,16)[0]
 h=dict(struct.unpack_from('>II',x,24+i*8) for i in range(struct.unpack_from('>I',x,20)[0]));size,en,co=struct.unpack_from('>IHH',x,h[0x3ff]);assert (en,co)==(1,1)
 blocks=[struct.unpack_from('>II',x,h[0x3ff]+8+i*8) for i in range((size-8)//8)]
 key=aes(bytes.fromhex('20b185a59d28fdc340583fbb0896bf91'),x[sec+0x150:sec+0x160],True)
 raw=aes(key,x[off:],True);memory=bytearray();p=0
 for n,z in blocks:memory+=raw[p:p+n]+bytes(z);p+=n
 for at,v in delta['memory']:v=bytes.fromhex(v);memory[at:at+len(v)]=v
 data=[];p=0
 for n,z in blocks:
  data.append(memory[p:p+n]);assert not any(memory[p+n:p+n+z]);p+=n+z
 header=bytearray(x[:off])
 for at,v in delta['header']:v=bytes.fromhex(v);header[at:at+len(v)]=v
 result=bytes(header)+aes(key,b''.join(data));assert sha(result)==delta['new_sha256'];return result
def assemble(base_path=None):
 m=json.loads((Q/'recipe.json').read_text());base=Path(base_path) if base_path else Q/'baseline.zip'
 if not base_path:urllib.request.urlretrieve(m['base_url'],base)
 assert sha(base.read_bytes())==m['base_sha256']
 assert sha((Q/'literals.zip').read_bytes())==m['literals_sha256']
 with zipfile.ZipFile(base) as outer:oldexe=outer.read('Onechanbara_ISO_Korean_v1.3.0.exe')
 with zipfile.ZipFile(io.BytesIO(oldexe)) as old,zipfile.ZipFile(Q/'literals.zip') as literal:
  raw=gzip.decompress(old.read('payload/default.xex.opd.gz'));magic,n,count,at,k=struct.unpack_from('<4sIIII',raw);assert magic==b'OPD1' and count==1 and at==0 and n==k
  newx=patch_xex(raw[20:],json.loads((Q/'game-code-delta.json').read_text()))
  newdelta=gzip.compress(struct.pack('<4sIIII',b'OPD1',len(newx),1,0,len(newx))+newx,9,mtime=0)
  # Python 3.13+ normalizes the gzip OS byte to 255; the tested Linux build
  # uses 3. Preserve its exact header independently of the runner's Python.
  newdelta=newdelta[:9]+b'\x03'+newdelta[10:]
  buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w',zipfile.ZIP_STORED) as payload:
   for e in m['entries']:
    name=e['name'];data=newdelta if name=='payload/default.xex.opd.gz' else (literal.read(name) if name in literal.namelist() else old.read(name))
    assert sha(data)==e['sha256'],name
    info=zipfile.ZipInfo(name,tuple(e['date_time']))
    for field in ['compress_type','external_attr','create_system']:setattr(info,field,e[field])
    payload.writestr(info,data)
  exe=literal.read('exe-prefix.bin')+buffer.getvalue()+literal.read('exe-suffix.bin');assert sha(exe)==m['exe_sha256']
  result=Q/m['release']['name']
  with zipfile.ZipFile(result,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for name,data in [('Onechanbara_ISO_Korean_v1.4.0.exe',exe),('먼저읽기.txt',literal.read('먼저읽기.txt')),('원본ISO_해시.txt',literal.read('원본ISO_해시.txt'))]:
    i=zipfile.ZipInfo(name,(2026,11,6,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;z.writestr(i,data,compresslevel=6)
  assert sha(result.read_bytes())==m['release']['sha256']
  with zipfile.ZipFile(result) as z:assert z.testzip() is None
 return result,m
def api(path,data=None,method=None):
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 req=urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),headers,method=method or ('GET' if data is None else 'POST'))
 with urllib.request.urlopen(req,timeout=120) as f:return json.load(f)
def publish():
 assert os.environ['GITHUB_REPOSITORY']==REPO
 result,m=assemble();rels=api('/releases?per_page=100');rel=next((r for r in rels if r['tag_name']==TAG),None);body=(Q/'RELEASE_NOTES.md').read_text()
 if rel is None:rel=api('/releases',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'오네찬바라 볼텍스 한글패치 v1.4.0 — 로딩 대폭 개선','body':body,'draft':True,'prerelease':False})
 for path in [result,Q/'SHA256SUMS-v1.4.0.txt']:
  subprocess.run(['gh','release','upload',TAG,str(path),'--repo',REPO,'--clobber'],check=True)
 check=api('/releases/'+str(rel['id']));asset=next(a for a in check['assets'] if a['name']==result.name);assert asset['digest']=='sha256:'+m['release']['sha256'] and asset['size']==m['release']['size']
 api('/releases/'+str(rel['id']),{'body':body,'name':'오네찬바라 볼텍스 한글패치 v1.4.0 — 로딩 대폭 개선','draft':False,'make_latest':'true'},'PATCH')
 with urllib.request.urlopen(asset['browser_download_url'],timeout=180) as f:assert sha(f.read())==m['release']['sha256']
 url='https://github.com/'+REPO+'/releases/tag/'+TAG
 notice='<!-- latest-patch-navigation:start -->\n> **최신 패치: [오네찬바라 볼텍스 v1.4.0 다운로드·설치 안내]('+url+')**\n>\n> 로딩 개선을 통합한 새 버전입니다. 기존 한글판 ISO에도 적용할 수 있습니다.\n> [게임별 최신 안내](https://github.com/'+REPO+'/tree/main/xbox360/onechanbara)\n<!-- latest-patch-navigation:end -->'
 updated=[]
 for old in rels:
  if old['draft'] or not old['tag_name'].startswith('onechanbara-') or old['tag_name']==TAG:continue
  oldbody=old.get('body') or ''
  oldbody=re.sub(r'<!-- latest-patch-navigation:start -->.*?<!-- latest-patch-navigation:end -->\s*(?:---\s*)?','',oldbody,flags=re.S)
  newbody=notice+'\n\n---\n\n'+oldbody
  api('/releases/'+str(old['id']),{'body':newbody},'PATCH');assert api('/releases/'+str(old['id']))['body']==newbody;updated.append(old['tag_name'])
 print(json.dumps({'status':'PASS','url':url,'asset_url':asset['browser_download_url'],'sha256':m['release']['sha256'],'previous_notices':updated,'old_assets_preserved':True}),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1:
  result,m=assemble(sys.argv[1]);print('LOCAL_RECONSTRUCTION_PASS',m['release']['sha256'],flush=True)
 else:publish()
