"""Replace only the v2.1 assets on the existing release after exact verification."""
from pathlib import Path
import sys,os,json,hashlib,urllib.request,urllib.parse,base64,time
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'universal'))
from reconstruct import reconstruct
REPO='slimshadykor-cmd/korean-patches';API='https://api.github.com/repos/'+REPO;TAG='ngb-v2.0';NAME='NGB_Korean_Patch_v2.1.zip'
OLD='7187793812d562495272b3f4c4f6ffdc3732b6eb9d4eec1493856745c67bb1f3';NEW='6aaa28e6f28f288ca22480c7e009966c32331ea4f522f13637ac0a083b6f17c9';V20='192bb7941aee3d5a0fc18a2aace770e5080d20ffdeb2c31de99d7d5530f89235'
MARK='아래는 보존한 v2.0 설치·기능·검증 기록입니다.'
sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path,data=None,method=None):
 req=urllib.request.Request(API+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=120) as f:
  b=f.read();return json.loads(b) if b else None
def download(url):
 with urllib.request.urlopen(url,timeout=180) as f:return f.read()
def upload(rel,name,payload,mime):
 url=rel['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(name)
 req=urllib.request.Request(url,data=payload,method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':mime})
 with urllib.request.urlopen(req,timeout=240) as f:r=json.load(f)
 assert r['digest']=='sha256:'+sha(payload);return r
def swap(rel,name,payload,mime,label,expected_old=None):
 assets=api('/releases/'+str(rel['id']))['assets'];old=next((a for a in assets if a['name']==name),None)
 digest='sha256:'+sha(payload)
 if old and old.get('digest')==digest:return old
 if expected_old is not None:assert old and old.get('digest')=='sha256:'+expected_old,'Concurrent asset change'
 staging=name+'.uploading';backup=name+'.previous'
 assert not any(a['name'] in (staging,backup) for a in assets),'Prior interrupted replacement requires review'
 staged=upload(rel,staging,payload,mime)
 # The previous asset stays available until the full new upload has been verified.
 if old:api('/releases/assets/'+str(old['id']),{'name':backup},'PATCH')
 try:new=api('/releases/assets/'+str(staged['id']),{'name':name,'label':label},'PATCH')
 except Exception:
  if old:api('/releases/assets/'+str(old['id']),{'name':name},'PATCH')
  raise
 assert new['digest']==digest
 assert sha(download(new['browser_download_url']+'?verify='+sha(payload)[:16]))==sha(payload)
 if old:api('/releases/assets/'+str(old['id']),method='DELETE')
 return new

def main():
 rel=api('/releases/tags/'+TAG);assert rel['html_url']=='https://github.com/'+REPO+'/releases/tag/'+TAG
 preserved={a['id']:(a['name'],a.get('digest')) for a in rel['assets'] if a['name'] not in (NAME,'SHA256SUMS-v2.1.txt')}
 assert next(a for a in rel['assets'] if a['name']=='NGB_Korean_Patch_v2.0.zip')['digest']=='sha256:'+V20
 old=next(a for a in rel['assets'] if a['name']==NAME)
 if old['digest']=='sha256:'+NEW:
  out=download(old['browser_download_url']+'?verify='+NEW[:16]);assert sha(out)==NEW
 else:
  assert old['digest']=='sha256:'+OLD
  source=download(old['browser_download_url']+'?verify='+OLD[:16]);encoded=''.join(p.read_text() for p in sorted((ROOT/'universal').glob('recipe-*.txt')));out=reconstruct(source,encoded)
 assert sha(out)==NEW and len(out)==70822467
 prefix=(ROOT/'universal/notes_prefix.md').read_text();assert rel['body'].count(MARK)==1
 notes=prefix+MARK+rel['body'].split(MARK,1)[1]
 readme=api('/contents/xbox/ninja-gaiden-black/README.md?ref=main');body=base64.b64decode(readme['content']).decode();assert body.count(MARK)==1
 newreadme=prefix+MARK+body.split(MARK,1)[1]
 asset=swap(rel,NAME,out,'application/zip','v2.1 — 공용 패처 · 제목 위치 보완',expected_old=OLD if old['digest']!='sha256:'+NEW else None)
 sums=(NEW+'  '+NAME+'\n').encode();swap(rel,'SHA256SUMS-v2.1.txt',sums,'text/plain; charset=utf-8','v2.1 공용 수정본 SHA-256')
 api('/releases/'+str(rel['id']),{'name':'닌자가이덴 블랙 한글패치 v2.1 / v2.0','body':notes},'PATCH')
 if body!=newreadme:api('/contents/xbox/ninja-gaiden-black/README.md',{'message':'Document NGB v2.1 title alignment and warning region behavior','branch':'main','sha':readme['sha'],'content':base64.b64encode(newreadme.encode()).decode()},'PUT')
 final=api('/releases/tags/'+TAG);assert final['body']==notes
 actual={a['id']:(a['name'],a.get('digest')) for a in final['assets'] if a['name'] not in (NAME,'SHA256SUMS-v2.1.txt')};assert actual==preserved
 assert next(a for a in final['assets'] if a['name']==NAME)['digest']=='sha256:'+NEW
 print(json.dumps({'status':'PASS','release_url':final['html_url'],'sha256':NEW,'v2.0_and_other_assets_preserved':True,'public_download_verified':True}))
if __name__=='__main__':main()
