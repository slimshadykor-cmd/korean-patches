from pathlib import Path
import json,hashlib,zipfile,gzip
sha=lambda b:hashlib.sha256(b).hexdigest()
def assemble(base_path,payload_path,manifest_path,out_path):
 root=Path(manifest_path).parent;m=json.loads(Path(manifest_path).read_text());assert sha(Path(base_path).read_bytes())==m['base_sha256'];assert sha(Path(payload_path).read_bytes())==m['payload_sha256']
 with zipfile.ZipFile(base_path) as b,zipfile.ZipFile(payload_path) as p,zipfile.ZipFile(out_path,'w') as out:
  original=json.loads(b.read('NGB_Korean_Patch_v1.8/ngb_native11/assets/build_plan.json'))
  def decode(v):
   kind,data=v
   if kind=='ref':
    x=original
    for k in data:x=x[k]
    return x
   if kind=='dict':return {k:decode(x) for k,x in data}
   if kind=='list':return [decode(x) for x in data]
   assert kind=='value';return data
  plan=json.dumps(decode(json.loads(gzip.decompress((root/'plan_delta.json.gz').read_bytes()))),ensure_ascii=False,indent=2).encode()
  for r in m['files']:
   assert '..' not in Path(r['name']).parts and not r['name'].startswith('/')
   data=plan if r['source']=='plan' else (b if r['source']=='base' else p).read(r['entry']);assert sha(data)==r['sha256'],r['name']
   i=zipfile.ZipInfo(r['name'],tuple(r['info']['date_time']))
   for k,v in r['info'].items():
    if k=='date_time':continue
    setattr(i,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
   out.writestr(i,data,compress_type=i.compress_type,compresslevel=6)
 assert sha(Path(out_path).read_bytes())==m['output_sha256']
 with zipfile.ZipFile(out_path) as z:assert z.testzip() is None
 return m['output_sha256']
if __name__=='__main__':
 import sys
 print(assemble(*sys.argv[1:]))
