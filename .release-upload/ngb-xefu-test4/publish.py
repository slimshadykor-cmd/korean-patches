"""Reconstruct the already-verified Test4 ZIP exactly, then publish that asset only."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,subprocess,urllib.request,zipfile
R=Path(__file__).resolve().parent;REPO='slimshadykor-cmd/korean-patches';TAG='ngb-v2.0';NAME='NGB_Xbox360_XeFu_Test4.zip';API='https://api.github.com/repos/'+REPO
sha=lambda b:hashlib.sha256(b).hexdigest()
def assemble(base=None):
 m=json.loads(gzip.decompress((R/'manifest.json.gz').read_bytes()))
 if base is None:
  base=R/'base.zip';urllib.request.urlretrieve(m['base_url'],base)
 assert sha(Path(base).read_bytes())==m['base_sha256'],'Base release hash mismatch'
 assert sha((R/'payload.zip').read_bytes())==m['payload_sha256'],'Payload hash mismatch'
 with zipfile.ZipFile(base) as b,zipfile.ZipFile(R/'payload.zip') as p,zipfile.ZipFile(R/NAME,'w') as z:
  for e in m['files']:
   assert e['name'].startswith('NGB_Xbox360_XeFu_Test4/') and '..' not in Path(e['name']).parts
   data=(b if e['source']=='base' else p).read(e['entry']);assert sha(data)==e['sha256'],e['name']
   i=zipfile.ZipInfo(e['name'],tuple(e['info']['date_time']))
   for k,v in e['info'].items():
    if k!='date_time':setattr(i,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
   z.writestr(i,data,compress_type=i.compress_type,compresslevel=9)
 result=R/NAME;assert result.stat().st_size==m['output_size'];assert sha(result.read_bytes())==m['output_sha256'],'Rebuilt ZIP differs from tested ZIP'
 with zipfile.ZipFile(result) as z:assert z.testzip() is None
 return m,result
def api(path,data=None,method=None):
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 request=urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),headers,method=method or ('GET' if data is None else 'POST'))
 with urllib.request.urlopen(request,timeout=120) as f:return json.load(f)
def publish(m,result):
 assert os.environ.get('GITHUB_REPOSITORY')==REPO
 rel=api('/releases/tags/'+TAG);assert not rel['draft'];before_asset_ids={a['id'] for a in rel['assets']}
 existing=next((a for a in rel['assets'] if a['name']==NAME),None)
 if existing is None:subprocess.run(['gh','release','upload',TAG,str(result),'--repo',REPO],check=True)
 else:assert existing.get('digest')=='sha256:'+m['output_sha256'],'Refusing to replace a different existing Test4 asset'
 after=api('/releases/'+str(rel['id']));asset=next(a for a in after['assets'] if a['name']==NAME);assert asset['digest']=='sha256:'+m['output_sha256']
 assert before_asset_ids<={a['id'] for a in after['assets']},'Existing release assets changed'
 with urllib.request.urlopen(asset['browser_download_url']+'?verify='+m['output_sha256'][:16],timeout=180) as f:assert sha(f.read())==m['output_sha256'],'Public download hash mismatch'
 body=after['body'];new=(R/'section.txt').read_text();old_heading='## 2026-11-04 Xbox 360 로고 멈춤 대응 수정본 — Test3';new_heading='## 2026-11-04 Xbox 360 호환 수정본 — XeFu Test4'
 start=body.find(old_heading)
 if start<0:start=body.find(new_heading)
 end=body.find('## 2026-10-26 추가 수정',start);assert start>=0 and end>start,'Release boundaries changed; notes not modified'
 updated=body[:start]+new+body[end:];api('/releases/'+str(rel['id']),{'body':updated},'PATCH');check=api('/releases/'+str(rel['id']));assert check['body']==updated
 print(json.dumps({'status':'PASS','asset_url':asset['browser_download_url'],'release_url':rel['html_url'],'sha256':m['output_sha256'],'size':asset['size'],'existing_assets_preserved':True,'public_download_hash_verified':True}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path);p.add_argument('--publish',action='store_true');a=p.parse_args();m,result=assemble(a.base)
 if a.publish:publish(m,result)
 else:print(json.dumps({'assembly':'PASS','sha256':m['output_sha256'],'size':result.stat().st_size}))
