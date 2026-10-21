"""Publish the exact locally verified public v1.6 archive from a hash-checked delta."""
import hashlib,io,json,os,urllib.parse,urllib.request,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent
REPO='slimshadykor-cmd/korean-patches';API='https://api.github.com/repos/'+REPO
TAG='ngb-v1.6';NAME='NGB_Korean_Patch_v1.6.zip'
SHA='3c386160e1d127997f6bd9cc9bb5e85a7d314161ed354f83cc56dfe509a5cdd6';SIZE=50793928
BASE_SHA='3e31105e9748370776542faec3cf5b6bbc63f8ff36d0033300e666a8866a2f78'
sha=lambda b:hashlib.sha256(b).hexdigest()
def request(url,method='GET',data=None,content_type='application/json'):
 if not url.startswith((API+'/', 'https://uploads.github.com/repos/'+REPO+'/')):raise RuntimeError('Unexpected API destination')
 req=urllib.request.Request(url,data=data,method=method,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':content_type,'User-Agent':'ngb-v1.6-publication'})
 with urllib.request.urlopen(req,timeout=180) as res:return json.load(res)
def send(url,method,body):return request(url,method,json.dumps(body).encode())
def check(asset,name,data):
 assert asset['name']==name and asset['size']==len(data) and asset['state']=='uploaded' and asset.get('digest')=='sha256:'+sha(data),name

def main():
 meta=json.loads((R/'payload.json').read_text());payload=b''.join((R/n).read_bytes() for n in meta['parts'])
 assert sha(payload)==meta['sha256'] and len(payload)==meta['bytes']
 with urllib.request.urlopen('https://github.com/'+REPO+'/releases/download/ngb-v1.5/NGB_Korean_Patch_v1.5.zip',timeout=180) as res:base=res.read()
 assert sha(base)==BASE_SHA
 with zipfile.ZipFile(io.BytesIO(payload)) as pack:
  manifest=json.loads(pack.read('zip_manifest.json'));delta=pack.read('delta.zip')
 out=io.BytesIO()
 with zipfile.ZipFile(io.BytesIO(base)) as b,zipfile.ZipFile(io.BytesIO(delta)) as d,zipfile.ZipFile(out,'w') as z:
  for row in manifest:
   info=zipfile.ZipInfo(row['name'],tuple(row['fields']['date_time']))
   for k,v in row['fields'].items():
    if k!='date_time':setattr(info,k,v)
   z.writestr(info,b.read(row['base']) if row['base'] else d.read(row['relative']),compress_type=info.compress_type,compresslevel=9)
 archive=out.getvalue();assert len(archive)==SIZE and sha(archive)==SHA
 with zipfile.ZipFile(io.BytesIO(archive)) as z:assert z.testzip() is None
 print('Exact v1.6 ZIP reconstruction and CRC verified',flush=True)
 files={NAME:archive,'SHA256SUMS.txt':(R/'SHA256SUMS.txt').read_bytes(),'ORIGINAL_HASHES.txt':(R/'ORIGINAL_HASHES.txt').read_bytes()}
 assert files['SHA256SUMS.txt'].decode().strip()==SHA+'  '+NAME
 all_releases=request(API+'/releases?per_page=100');matches=[r for r in all_releases if r['tag_name']==TAG]
 if matches:release=matches[0]
 else:release=send(API+'/releases','POST',{'tag_name':TAG,'target_commitish':os.environ['RELEASE_TARGET'],'name':'닌자가이덴 블랙 한글패치 v1.6 — 한국어·일본어 음성 기본 설정','body':(R/'RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':False})
 assert release['tag_name']==TAG and not release['prerelease']
 url=API+'/releases/'+str(release['id']);existing={a['name']:a for a in release['assets']};assert not set(existing)-set(files)
 for name,data in files.items():
  if name in existing:asset=existing[name]
  else:
   assert release['draft'],'Refusing to alter incomplete public release'
   upload=release['upload_url'].split('{')[0]+'?'+urllib.parse.urlencode({'name':name})
   asset=request(upload,'POST',data,'application/zip' if name.endswith('.zip') else 'text/plain')
  check(asset,name,data);print('Verified remote asset',name,asset['digest'],flush=True)
 release=request(url);assert set(a['name'] for a in release['assets'])==set(files)
 for a in release['assets']:check(a,a['name'],files[a['name']])
 if release['draft']:release=send(url,'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
 assert not release['draft'] and release['published_at'] and release['tag_name']==TAG
 print('PUBLISHED',release['html_url'],flush=True)
 with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('Published '+release['html_url']+'\n\nZIP SHA-256: `'+SHA+'`\n')
if __name__=='__main__':main()
