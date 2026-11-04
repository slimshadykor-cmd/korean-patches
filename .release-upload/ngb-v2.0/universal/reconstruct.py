"""Reconstruct the reviewed ZIP from the prior release and exact entry deltas."""
import base64,hashlib,json,struct,zlib,zipfile,io
import copy

def compress(data):
 c=zlib.compressobj(9,zlib.DEFLATED,-15);return c.compress(data)+c.flush()

def reconstruct(source,encoded):
 r=json.loads(zlib.decompress(base64.b64decode(encoded)))
 assert hashlib.sha256(source).hexdigest()==r['source_sha256'],'Previous ZIP differs'
 blocks=[];manifest={};manifest_index=None
 for i,x in enumerate(r['blocks']):
  if x[0]=='copy':data=source[x[1]:x[1]+x[2]]
  elif x[0]=='data':data=base64.b64decode(x[1])
  elif x[0]=='manifest':manifest_index=i;data=b''
  elif x[0]=='plan':
   with zipfile.ZipFile(io.BytesIO(source)) as z:plan=json.loads(z.read(x[1]))
   patch=r['plan_update']
   previous=copy.deepcopy(plan['boot_repairs'][patch['repair_template_index']])
   previous['previous_xbe_sha256']=patch['new_repair_hash'];previous['reason']=patch['new_repair_reason']
   plan['boot_repairs'].append(previous)
   for k,v in patch['replace'].items():plan[k]=v
   for index,value in patch['universal_change_updates']:plan['universal']['changes'][index]=value
   plan['universal']['output_sha256']=patch['new_repair_hash']
   next(a for a in plan['archives'] if a['path']=='demo.afs')['version_member']=patch['demo_version_member']
   data=compress(json.dumps(plan,ensure_ascii=False,indent=2).encode())
  else:raise ValueError(x[0])
  blocks.append(data)
  if i%2 and x[0]!='manifest':
   h=blocks[i-1];name_len,extra=struct.unpack_from('<HH',h,26);name=h[30:30+name_len].decode('utf-8');method=struct.unpack_from('<H',h,8)[0]
   raw=zlib.decompress(data,-15) if method==8 else data
   manifest[name.split('/',1)[1]]={'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 assert manifest_index is not None
 blocks[manifest_index]=compress(json.dumps(manifest,ensure_ascii=False,indent=2).encode())
 out=b''.join(blocks);assert len(out)==r['output_size'] and hashlib.sha256(out).hexdigest()==r['output_sha256'],'Reconstructed ZIP differs'
 with zipfile.ZipFile(io.BytesIO(out)) as z:assert z.testzip() is None
 return out
