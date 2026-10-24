from pathlib import Path
import json,hashlib,zipfile
sha=lambda b:hashlib.sha256(b).hexdigest()
def assemble(base_path,payload_path,manifest_path,out_path):
 m=json.loads(Path(manifest_path).read_text());assert sha(Path(base_path).read_bytes())==m['base_sha256'];assert sha(Path(payload_path).read_bytes())==m['payload_sha256']
 with zipfile.ZipFile(base_path) as b,zipfile.ZipFile(payload_path) as p,zipfile.ZipFile(out_path,'w') as out:
  for r in m['files']:
   assert '..' not in Path(r['name']).parts and not r['name'].startswith('/')
   data=(b if r['source']=='base' else p).read(r['entry']);assert sha(data)==r['sha256']
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
