"""Publish only the reviewed NGB v1.7 public package to its dedicated release."""
from pathlib import Path
import hashlib,json,os,subprocess,time,urllib.request,urllib.error
from reassemble_release import assemble

ROOT=Path(__file__).resolve().parent
REPO='slimshadykor-cmd/korean-patches';TAG='ngb-v1.7'
API='https://api.github.com/repos/'+REPO
EXPECTED='f1ac09bd2e9de9da1c0e383943a152b637a6d6dda9b96c9f0dcd9e2f6483ea72'
def sha(b):return hashlib.sha256(b).hexdigest()
def api(path,data=None,method='GET'):
    headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    body=None if data is None else json.dumps(data).encode()
    if body is not None:headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request(API+path,body,headers,method=method),timeout=90) as r:return json.load(r)

def main():
    assert os.environ['GITHUB_REPOSITORY']==REPO
    base=ROOT/'base-v1.6.zip'
    urllib.request.urlretrieve('https://github.com/'+REPO+'/releases/download/ngb-v1.6/NGB_Korean_Patch_v1.6.zip',base)
    parts=sorted(ROOT.glob('payload.part*'));assert len(parts)==26
    payload=ROOT/'payload.zip'
    with payload.open('wb') as f:
        for part in parts:f.write(part.read_bytes())
    out=ROOT/'NGB_Korean_Patch_v1.7.zip'
    assert assemble(base,payload,ROOT/'manifest.json',out)==EXPECTED
    try:
        release=api('/releases/tags/'+TAG)
        raise RuntimeError('Release tag already exists; refusing to replace existing publication')
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
    body=(ROOT/'RELEASE_NOTES.md').read_text()
    release=api('/releases',dict(tag_name=TAG,target_commitish=os.environ['GITHUB_SHA'],
        name='닌자가이덴 블랙 한글패치 v1.7 폭풍',body=body,draft=True,prerelease=False,make_latest='false'),'POST')
    assets=[out,ROOT/'SHA256SUMS.txt',ROOT/'ORIGINAL_HASHES.txt']
    subprocess.run(['gh','release','upload',TAG,*map(str,assets),'--repo',REPO],check=True)
    uploaded=api('/releases/'+str(release['id'])+'/assets')
    by_name={a['name']:a for a in uploaded}
    assert set(by_name)=={p.name for p in assets}
    for p in assets:
        assert by_name[p.name]['size']==p.stat().st_size
        assert by_name[p.name]['digest']=='sha256:'+sha(p.read_bytes())
    api('/releases/'+str(release['id']),dict(draft=False,make_latest='false'),'PATCH')
    # Verify the link a visitor will use without sending authentication.
    url='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+out.name
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url,timeout=120) as r:download=r.read()
            assert sha(download)==EXPECTED and len(download)==out.stat().st_size
            print(json.dumps(dict(public_url='https://github.com/'+REPO+'/releases/tag/'+TAG,
                anonymous_download_sha256=sha(download),bytes=len(download),status='PASS')))
            return
        except urllib.error.HTTPError as e:
            if e.code!=404 or attempt==5:raise
            time.sleep(5)
    raise RuntimeError('Anonymous download verification incomplete')
if __name__=='__main__':main()
