"""Promote the exact low-memory candidate into the sole common v2.0 download."""
from pathlib import Path
import argparse, gzip, hashlib, json, os, subprocess, urllib.request, zipfile

R = Path(__file__).resolve().parent
REPO = 'slimshadykor-cmd/korean-patches'
API = 'https://api.github.com/repos/'+REPO
TAG = 'ngb-v2.0'
NAME = 'NGB_Korean_Patch_v2.0.zip'
OLD = {
    NAME: (674655538, 'sha256:9d272fc640eb560289150bd6ab44f8d1d8499ccacef6c449e06839b798677ab4'),
    'SHA256SUMS.txt': (674655696, 'sha256:7aac2cc07273311c35be015c46a530e14ff825107b51e0ed80c4d2d224fa0036'),
    'NGB_Korean_Patch_v2.0_hakuX.zip': (675085039, 'sha256:c168b1a891823ac29bfc247a249fdf596f7d8c1607c8f721147c315e0f33a062'),
    'SHA256SUMS_hakuX.txt': (675085143, 'sha256:174c851fb717a469e047a64f79d832945aca49d47a8bbc94a9102de68236c37c'),
}
sha = lambda b:hashlib.sha256(b).hexdigest()

def api(path, data=None, method=None):
    headers = {'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
    request = urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),headers,method=method or ('GET' if data is None else 'POST'))
    with urllib.request.urlopen(request,timeout=120) as response:
        content = response.read()
        return json.loads(content) if content else None

def download_hash(url):
    digest = hashlib.sha256()
    with urllib.request.urlopen(url,timeout=180) as response:
        while True:
            block = response.read(1024*1024)
            if not block: break
            digest.update(block)
    return digest.hexdigest()

def assemble(base):
    m = json.loads(gzip.decompress((R/'manifest.json.gz').read_bytes()))
    if base is None:
        base = R/'base.zip'
        urllib.request.urlretrieve(m['base_url'],base)
    assert sha(base.read_bytes()) == m['base_sha256'], 'Wrong candidate ZIP'
    assert sha((R/'payload.zip').read_bytes()) == m['payload_sha256']
    with zipfile.ZipFile(base) as b, zipfile.ZipFile(R/'payload.zip') as p, zipfile.ZipFile(R/NAME,'w') as z:
        original = json.loads(b.read('NGB_Korean_Patch_v2.0_hakuX/ngb_native11/assets/build_plan.json'))
        def decode(value):
            kind, data = value
            if kind == 'ref':
                out = original
                for k in data: out = out[k]
                return out
            if kind == 'dict': return {k:decode(v) for k,v in data.items()}
            if kind == 'list': return [decode(v) for v in data]
            assert kind == 'value'
            return data
        new = decode(json.loads(gzip.decompress((R/'plan_delta.json.gz').read_bytes())))
        for key in ['xbe','boot_repairs','archives','root_patches']: assert new[key] == original[key], key
        assert new['xbe']['output_sha256'] == 'c04e774df621566c60cbfb929a675ca4f375074205366c16e947bb858b66c97c'
        plan = json.dumps(new,ensure_ascii=False,indent=2).encode()
        for e in m['files']:
            data = plan if e['source'] == 'plan' else (b if e['source'] == 'base' else p).read(e['entry'])
            assert sha(data) == e['sha256'], e['name']
            info = zipfile.ZipInfo(e['name'],tuple(e['info']['date_time']))
            for k,v in e['info'].items():
                if k != 'date_time': setattr(info,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
            z.writestr(info,data,compress_type=info.compress_type,compresslevel=6)
    assert sha((R/NAME).read_bytes()) == m['output_sha256'], 'Reconstructed ZIP differs'
    assert (R/'SHA256SUMS.txt').read_text() == m['output_sha256']+'  '+NAME+'\n'
    with zipfile.ZipFile(R/NAME) as z: assert z.testzip() is None
    return m

def publish(m):
    assert os.environ['GITHUB_REPOSITORY'] == REPO
    rel = api('/releases/tags/'+TAG)
    assert rel['id'] == 423298286
    notes = (R/'RELEASE_NOTES.md').read_text()
    assert sha(rel['body'].encode()) == m['release_body_before_sha256'] or rel['body'] == notes, 'Concurrent release edit'
    assets = {a['name']:a for a in rel['assets']}
    assert set(assets) <= set(OLD), 'Unexpected release asset: inspect before publishing'
    wanted = {NAME:'sha256:'+m['output_sha256'],'SHA256SUMS.txt':'sha256:'+sha((R/'SHA256SUMS.txt').read_bytes())}
    for name,a in assets.items():
        assert (a['id'],a['digest']) == OLD[name] or (name in wanted and a['digest'] == wanted[name]), 'Concurrent asset edit: '+name
    for name,label in [(NAME,'공용 v2.0 — 선택 화면 메모리 개선'),('SHA256SUMS.txt','공용 v2.0 SHA-256')]:
        if name not in assets or assets[name]['digest'] != wanted[name]:
            subprocess.run(['gh','release','upload',TAG,str(R/name)+'#'+label,'--clobber','--repo',REPO],check=True)
    updated = api('/releases/'+str(rel['id']))
    for name,digest in wanted.items():
        a = next(a for a in updated['assets'] if a['name'] == name)
        assert a['digest'] == digest
        assert download_hash(a['browser_download_url']+'?verify=unified-'+m['output_sha256'][:12]) == digest.removeprefix('sha256:'), name
    assert updated['body'] == rel['body'], 'Concurrent release edit before description update'
    api('/releases/'+str(rel['id']),{'body':notes},'PATCH')
    # Remove only the separate candidate assets after the common public download is verified.
    current = api('/releases/'+str(rel['id']))
    assert current['body'] == notes
    for name in ['NGB_Korean_Patch_v2.0_hakuX.zip','SHA256SUMS_hakuX.txt']:
        candidates = [a for a in current['assets'] if a['name'] == name]
        if candidates:
            a = candidates[0]
            assert (a['id'],a['digest']) == OLD[name]
            api('/releases/assets/'+str(a['id']),method='DELETE')
    final = api('/releases/'+str(rel['id']))
    assert final['body'] == notes
    assert {a['name']:a['digest'] for a in final['assets']} == wanted
    print(json.dumps({'status':'PASS','package_sha256':m['output_sha256'],'game_executable_sha256':'c04e774df621566c60cbfb929a675ca4f375074205366c16e947bb858b66c97c','public_download_verified':True,'separate_hakux_assets_removed':True,'single_common_package':True,'release':final['html_url']},ensure_ascii=False))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--assemble-only',action='store_true')
    parser.add_argument('--base',type=Path)
    args = parser.parse_args()
    manifest = assemble(args.base)
    if args.assemble_only: print('PASS: exact low-memory candidate promoted; byte-identical common ZIP reconstructed')
    else: publish(manifest)
