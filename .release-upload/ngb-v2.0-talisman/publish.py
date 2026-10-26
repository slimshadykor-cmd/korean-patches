"""Reconstruct and publish the exact user-confirmed v2.0 talisman update."""
from pathlib import Path
import argparse, gzip, hashlib, json, os, shutil, subprocess, urllib.request, zipfile

R = Path(__file__).resolve().parent
REPO = 'slimshadykor-cmd/korean-patches'
API = 'https://api.github.com/repos/'+REPO
TAG = 'ngb-v2.0'
NAME = 'NGB_Korean_Patch_v2.0.zip'
PRE = 'NGB_Korean_Patch_v2.0/'
TARGET_XBE = '1ed80090b4b2872dbd1d896ae7571eaa0ff660672f09c5dbbe2d1745ec1d8b88'
OLD = {NAME:(675216608,'sha256:cf92f7dc22b44f0ff6d76ac688435223de33b47ff4f7124ba321b36e53424464'),'SHA256SUMS.txt':(675216732,'sha256:6270f647ddb9b23075feefea164ee1afff61ef694d5cb18ba31e46acb1119ded')}
sha = lambda b:hashlib.sha256(b).hexdigest()

def api(path,data=None,method=None):
    headers = {'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
    request = urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),headers,method=method or ('GET' if data is None else 'POST'))
    with urllib.request.urlopen(request,timeout=120) as response:
        content = response.read()
        return json.loads(content) if content else None

def download_hash(url):
    h = hashlib.sha256()
    with urllib.request.urlopen(url,timeout=180) as response:
        while True:
            chunk = response.read(1024*1024)
            if not chunk:break
            h.update(chunk)
    return h.hexdigest()

def verify_archive(m):
    assert sha((R/NAME).read_bytes()) == m['output_sha256']
    assert (R/'SHA256SUMS.txt').read_text() == m['output_sha256']+'  '+NAME+'\n'
    with zipfile.ZipFile(R/NAME) as z:
        assert z.testzip() is None
        plan = json.loads(z.read(PRE+'ngb_native11/assets/build_plan.json'))
        assert plan['xbe']['output_sha256'] == TARGET_XBE
        for rel,digest in json.loads(z.read(PRE+'FILE_HASHES.json')).items():
            assert sha(z.read(PRE+rel)) == digest,rel

def assemble(base):
    m = json.loads(gzip.decompress((R/'manifest.json.gz').read_bytes()))
    if base is None:
        base = R/'base.zip'
        urllib.request.urlretrieve(m['base_url']+'?source=talisman-20261026',base)
    base_hash = sha(base.read_bytes())
    if base_hash == m['output_sha256']:
        shutil.copyfile(base,R/NAME)
        verify_archive(m)
        return m
    assert base_hash == m['base_sha256'],'Unexpected base package; no publication attempted'
    assert sha((R/'payload.zip').read_bytes()) == m['payload_sha256']
    with zipfile.ZipFile(base) as b,zipfile.ZipFile(R/'payload.zip') as p,zipfile.ZipFile(R/NAME,'w') as z:
        original = json.loads(b.read(PRE+'ngb_native11/assets/build_plan.json'))
        def decode(value):
            kind,data = value
            if kind == 'ref':
                out = original
                for key in data:out = out[key]
                return out
            if kind == 'dict':return {key:decode(v) for key,v in data.items()}
            if kind == 'list':return [decode(v) for v in data]
            assert kind == 'value'
            return data
        updated = decode(json.loads(gzip.decompress((R/'plan_delta.json.gz').read_bytes())))
        assert updated['xbe']['output_sha256'] == TARGET_XBE
        for key in ['archives','root_patches']:assert updated[key] == original[key]
        plan = json.dumps(updated,ensure_ascii=False,indent=2).encode()
        for e in m['files']:
            data = plan if e['source']=='plan' else (b if e['source']=='base' else p).read(e['entry'])
            assert sha(data) == e['sha256'],e['name']
            info = zipfile.ZipInfo(e['name'],tuple(e['info']['date_time']))
            for key,v in e['info'].items():
                if key!='date_time':setattr(info,key,bytes.fromhex(v) if key in ['extra','comment'] else v)
            z.writestr(info,data,compress_type=info.compress_type,compresslevel=6)
    verify_archive(m)
    return m

def publish(m):
    assert os.environ['GITHUB_REPOSITORY'] == REPO
    rel = api('/releases/tags/'+TAG)
    assert rel['id'] == 423298286 and not rel['draft'] and not rel['prerelease']
    notes = (R/'RELEASE_NOTES.md').read_text()
    assert sha(rel['body'].encode()) == m['release_body_before_sha256'] or rel['body']==notes,'Concurrent release edit'
    assets = {a['name']:a for a in rel['assets']}
    wanted = {NAME:'sha256:'+m['output_sha256'],'SHA256SUMS.txt':'sha256:'+sha((R/'SHA256SUMS.txt').read_bytes())}
    assert set(assets) <= set(OLD),'Unexpected assets; inspect before publication'
    for name,a in assets.items():
        assert (a['id'],a['digest']) == OLD[name] or a['digest']==wanted[name],'Concurrent asset update: '+name
    # Save any asset to be replaced for rollback before touching the release.
    rollback = R/'rollback';rollback.mkdir(exist_ok=True)
    saved = {}
    for name,a in assets.items():
        if a['digest'] != wanted[name]:
            urllib.request.urlretrieve(a['browser_download_url']+'?backup=talisman-20261026',rollback/name)
            assert 'sha256:'+sha((rollback/name).read_bytes()) == a['digest']
            saved[name]=a
    attempted=[]
    try:
        for name,label in [(NAME,'공용 v2.0 — 부활 부적 장착·해제 개선'),('SHA256SUMS.txt','공용 v2.0 SHA-256')]:
            if name not in assets or assets[name]['digest'] != wanted[name]:
                attempted.append(name)
                subprocess.run(['gh','release','upload',TAG,str(R/name)+'#'+label,'--clobber','--repo',REPO],check=True)
        updated = api('/releases/'+str(rel['id']))
        for name,digest in wanted.items():
            a = next(a for a in updated['assets'] if a['name']==name)
            assert a['digest'] == digest
            assert download_hash(a['browser_download_url']+'?verify='+m['output_sha256'][:16]) == digest.removeprefix('sha256:'),name
    except Exception:
        for name in attempted:
            if name in saved:
                subprocess.run(['gh','release','upload',TAG,str(rollback/name)+'#'+(saved[name]['label'] or name),'--clobber','--repo',REPO],check=True)
        raise
    assert updated['body'] == rel['body'],'Concurrent description edit before notes update'
    api('/releases/'+str(rel['id']),{'body':notes},'PATCH')
    final = api('/releases/'+str(rel['id']))
    assert final['body'] == notes
    assert {a['name']:a['digest'] for a in final['assets']} == wanted
    print(json.dumps({'status':'PASS','package_sha256':m['output_sha256'],'game_executable_sha256':TARGET_XBE,'public_download_verified':True,'release':final['html_url'],'same_tag_and_asset_name':True},ensure_ascii=False))

if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--assemble-only',action='store_true');p.add_argument('--base',type=Path);a=p.parse_args()
    manifest=assemble(a.base)
    if a.assemble_only:print('PASS: byte-identical public ZIP reconstructed and all member hashes verified')
    else:publish(manifest)
