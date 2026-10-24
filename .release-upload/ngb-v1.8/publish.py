"""Publish the verified v1.8 artifact, then put its link above the v1.7 body."""
from pathlib import Path
import hashlib,json,os,subprocess,urllib.request,urllib.error,time
from assemble import assemble
ROOT=Path(__file__).resolve().parent
REPO='slimshadykor-cmd/korean-patches';TAG='ngb-v1.8';PREVIOUS='ngb-v1.7'
API='https://api.github.com/repos/'+REPO
EXPECTED='5e1d83671e7fafe1134f71fcead404cb33c7f45395388322b68ffed584be771b'
def sha(b):return hashlib.sha256(b).hexdigest()
def api(path,data=None,method='GET'):
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
 raw=None if data is None else json.dumps(data).encode()
 if raw is not None:headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(API+path,raw,headers,method=method),timeout=90) as r:return json.load(r)
def main():
 assert os.environ['GITHUB_REPOSITORY']==REPO
 base=ROOT/'base-v1.7.zip';urllib.request.urlretrieve('https://github.com/'+REPO+'/releases/download/ngb-v1.7/NGB_Korean_Patch_v1.7.zip',base)
 payload=ROOT/'payload.zip'
 with payload.open('wb') as f:
  for p in sorted(ROOT.glob('payload.part*')):f.write(p.read_bytes())
 out=ROOT/'NGB_Korean_Patch_v1.8.zip';assert assemble(base,payload,ROOT/'manifest.json',out)==EXPECTED
 try:
  release=api('/releases/tags/'+TAG)
  assert release['name']=='닌자가이덴 블랙 한글패치 v1.8 폭풍'
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
  release=api('/releases',dict(tag_name=TAG,target_commitish=os.environ['GITHUB_SHA'],name='닌자가이덴 블랙 한글패치 v1.8 폭풍',body=(ROOT/'RELEASE_NOTES.md').read_text(),draft=True,prerelease=False,make_latest='false'),'POST')
 assets=[out,ROOT/'SHA256SUMS.txt',ROOT/'ORIGINAL_HASHES.txt'];existing={a['name']:a for a in api('/releases/'+str(release['id'])+'/assets')}
 for p in assets:
  if p.name in existing:assert existing[p.name]['digest']=='sha256:'+sha(p.read_bytes())
  else:subprocess.run(['gh','release','upload',TAG,str(p),'--repo',REPO],check=True)
 uploaded={a['name']:a for a in api('/releases/'+str(release['id'])+'/assets')}
 assert set(uploaded)=={p.name for p in assets}
 for p in assets:assert uploaded[p.name]['size']==p.stat().st_size and uploaded[p.name]['digest']=='sha256:'+sha(p.read_bytes())
 if release['draft']:api('/releases/'+str(release['id']),dict(draft=False,make_latest='false'),'PATCH')
 url='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+out.name
 for attempt in range(8):
  try:
   with urllib.request.urlopen(url,timeout=120) as r:download=r.read()
   assert sha(download)==EXPECTED;break
  except urllib.error.HTTPError as e:
   if e.code!=404 or attempt==7:raise
   time.sleep(5)
 previous=api('/releases/tags/'+PREVIOUS);oldbody=previous['body'] or '';notice=(ROOT/'UPGRADE_NOTICE.md').read_text()
 if not oldbody.startswith(notice):
  assert '<!-- NGB_LATEST_VERSION_NOTICE -->' not in oldbody,'Unexpected concurrent upgrade notice; preserve it for review'
  result=api('/releases/'+str(previous['id']),dict(body=notice+oldbody),'PATCH')
  assert result['body']==notice+oldbody
 verified=api('/releases/tags/'+PREVIOUS);assert verified['body'].startswith(notice)
 stable=lambda assets:sorted((a['id'],a['name'],a['size'],a.get('digest'),a['browser_download_url']) for a in assets)
 assert stable(verified['assets'])==stable(previous['assets']),'Previous release assets unexpectedly changed'
 print(json.dumps(dict(status='PASS',release_url='https://github.com/'+REPO+'/releases/tag/'+TAG,anonymous_download_sha256=EXPECTED,previous_release_notice_updated=True,previous_release_assets_preserved=True)))
if __name__=='__main__':main()
