"""Publish only the separate hakuX candidate asset; preserve the common v2.0 asset."""
from pathlib import Path
import os,json,zipfile,gzip,hashlib,urllib.request,subprocess,argparse
R=Path(__file__).parent
REPO='slimshadykor-cmd/korean-patches';API='https://api.github.com/repos/'+REPO
TAG='ngb-v2.0';NAME='NGB_Korean_Patch_v2.0_hakuX.zip'
COMMON_HASH='sha256:9d272fc640eb560289150bd6ab44f8d1d8499ccacef6c449e06839b798677ab4'
sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path,data=None,method=None):
 h={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 with urllib.request.urlopen(urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),h,method=method or ('GET' if data is None else 'POST')),timeout=120) as f:return json.load(f)
def assemble(base):
 m=json.loads(gzip.decompress((R/'manifest.json.gz').read_bytes()))
 local_validation=base is not None
 if base is None:
  base=R/'base.zip';urllib.request.urlretrieve(m['base_url'],base)
 assert sha(base.read_bytes())==m['local_validation_base_sha256' if local_validation else 'base_sha256']
 assert sha((R/'payload.zip').read_bytes())==m['payload_sha256']
 with zipfile.ZipFile(base) as b,zipfile.ZipFile(R/'payload.zip') as p,zipfile.ZipFile(R/NAME,'w') as z:
  original=json.loads(b.read('NGB_Korean_Patch_v2.0/ngb_native11/assets/build_plan.json'))
  def dec(v):
   kind,data=v
   if kind=='ref':
    o=original
    for k in data:o=o[k]
    return o
   if kind=='dict':return {k:dec(x) for k,x in data.items()}
   if kind=='list':return [dec(x) for x in data]
   assert kind=='value';return data
  plan=json.dumps(dec(json.loads(gzip.decompress((R/'plan_delta.json.gz').read_bytes()))),ensure_ascii=False,indent=2).encode()
  for e in m['files']:
   data=plan if e['source']=='plan' else (b if e['source']=='base' else p).read(e['entry'])
   assert sha(data)==e['sha256'],e['name']
   i=zipfile.ZipInfo(e['name'],tuple(e['info']['date_time']))
   for k,v in e['info'].items():
    if k!='date_time':setattr(i,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
   z.writestr(i,data,compress_type=i.compress_type,compresslevel=6)
 assert sha((R/NAME).read_bytes())==m['output_sha256']
 with zipfile.ZipFile(R/NAME) as z:assert z.testzip() is None
 return m
def publish(m):
 assert os.environ['GITHUB_REPOSITORY']==REPO
 rel=api('/releases/tags/'+TAG)
 common=next(a for a in rel['assets'] if a['name']=='NGB_Korean_Patch_v2.0.zip')
 assert common['digest']==COMMON_HASH
 before={a['name']:(a['id'],a['digest']) for a in rel['assets']}
 assert NAME not in before and 'SHA256SUMS_hakuX.txt' not in before,'Candidate asset already exists; inspect rather than overwrite.'
 for name in [NAME,'SHA256SUMS_hakuX.txt']:
  label='하쿠X v2.0 — 호환 확인용' if name==NAME else '하쿠X v2.0 SHA-256'
  subprocess.run(['gh','release','upload',TAG,str(R/name)+'#'+label,'--repo',REPO],check=True)
 updated=api('/releases/'+str(rel['id']))
 for a in updated['assets']:
  if a['name'] in before:assert (a['id'],a['digest'])==before[a['name']]
 candidate=next(a for a in updated['assets'] if a['name']==NAME)
 assert candidate['digest']=='sha256:'+m['output_sha256']
 assert updated['body']==rel['body'],'Release text changed concurrently; inspect before editing.'
 addition=(R/'RELEASE_ADDITION.md').read_text().strip()
 assert '<!-- hakux-v20-20261025 -->' not in rel['body']
 intro,body=rel['body'].split('\n',1)
 expected=intro+'\n\n'+addition+'\n'+body
 api('/releases/'+str(rel['id']),{'body':expected},'PATCH')
 verify=api('/releases/'+str(rel['id']));assert verify['body']==expected
 for name,(ident,digest) in before.items():
  a=next(a for a in verify['assets'] if a['name']==name);assert (a['id'],a['digest'])==(ident,digest)
 with urllib.request.urlopen(candidate['browser_download_url']+'?verify=hakux-v20',timeout=180) as response:
  h=hashlib.sha256()
  while True:
   block=response.read(1024*1024)
   if not block:break
   h.update(block)
  assert h.hexdigest()==m['output_sha256']
 print(json.dumps({'status':'PASS','candidate_sha256':m['output_sha256'],'public_download_verified':True,'existing_assets_preserved':True,'release':verify['html_url']},ensure_ascii=False))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--assemble-only',action='store_true');parser.add_argument('--base',type=Path);args=parser.parse_args()
 manifest=assemble(args.base)
 if args.assemble_only:print('PASS: byte-identical candidate package reconstructed')
 else:publish(manifest)
