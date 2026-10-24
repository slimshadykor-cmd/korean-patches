from pathlib import Path
import hashlib,json,os,subprocess,urllib.request,time,gzip
from assemble import assemble
ROOT=Path(__file__).resolve().parent
REPO='slimshadykor-cmd/korean-patches';TAG='ngb-v1.8'
API='https://api.github.com/repos/'+REPO
OLD='55e37a602c0863664f72ba69c0e5186743a343dd013afb9f9e7fc64fe3f4c53f'
NEW='ee36ae347ad2287cc74e0efee3ad00f380ecb9164f2def8f0c91b0dd740f7cf6'
NAME='NGB_Korean_Patch_v1.8.zip'
sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path,data=None,method='GET'):
    headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    raw=None if data is None else json.dumps(data).encode()
    if raw is not None:headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request(API+path,raw,headers,method=method),timeout=90) as r:return json.load(r)
def main():
    assert os.environ['GITHUB_REPOSITORY']==REPO
    release=api('/releases/tags/'+TAG);assert not release['draft'] and not release['immutable']
    assets={x['name']:x for x in release['assets']};assert assets[NAME]['digest'] in ('sha256:'+OLD,'sha256:'+NEW)
    if assets[NAME]['digest']=='sha256:'+NEW:
        body=(ROOT/'RELEASE_NOTES.md').read_text()
        if release['body']!=body:api('/releases/'+str(release['id']),{'body':body},'PATCH')
        after=api('/releases/tags/'+TAG)
        assert after['body']==body
        assert {a['name']:(a['id'],a['digest']) for a in after['assets']}=={n:(a['id'],a['digest']) for n,a in assets.items()}
        print('Release explanation updated; all assets unchanged');return
    base=ROOT/'base-v1.8.zip'
    url='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+NAME
    urllib.request.urlretrieve(url,base);assert sha(base.read_bytes())==OLD
    payload=ROOT/'payload.zip'
    with payload.open('wb') as f:
        for p in sorted(ROOT.glob('payload.part*')):f.write(p.read_bytes())
    (ROOT/'manifest.json').write_bytes(gzip.decompress((ROOT/'manifest.json.gz').read_bytes()))
    out=ROOT/NAME;assert assemble(base,payload,ROOT/'manifest.json',out)==NEW
    latest=api('/releases/tags/'+TAG);assert latest['body']==release['body'];assert next(a for a in latest['assets'] if a['name']==NAME)['digest']=='sha256:'+OLD
    for p in [out,ROOT/'SHA256SUMS.txt']:
        subprocess.run(['gh','release','upload',TAG,str(p),'--repo',REPO,'--clobber'],check=True)
    after=api('/releases/tags/'+TAG);a={x['name']:x for x in after['assets']}
    assert a[NAME]['digest']=='sha256:'+NEW and a[NAME]['size']==out.stat().st_size
    assert a['SHA256SUMS.txt']['digest']=='sha256:'+sha((ROOT/'SHA256SUMS.txt').read_bytes())
    for n,x in assets.items():
        if n not in (NAME,'SHA256SUMS.txt'):assert a[n]['id']==x['id'] and a[n]['digest']==x['digest']
    body=(ROOT/'RELEASE_NOTES.md').read_text();api('/releases/'+str(release['id']),{'body':body},'PATCH')
    assert api('/releases/tags/'+TAG)['body']==body
    for attempt in range(10):
        with urllib.request.urlopen(url+'?revision=storm-pickup-'+str(attempt),timeout=120) as r:download=r.read()
        if sha(download)==NEW:break
        if attempt==9:raise AssertionError('Public download does not match')
        time.sleep(5)
    print(json.dumps(dict(status='PASS',release=release['html_url'],sha256=NEW,body_updated=True,other_assets_preserved=True)))
if __name__=='__main__':main()
