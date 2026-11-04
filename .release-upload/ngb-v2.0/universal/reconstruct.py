"""Reconstruct the reviewed ZIP from the prior release and exact entry deltas."""
import base64,hashlib,json,struct,zlib,zipfile,io

def plan_update(d):
 d['universal']=d.pop('targets')['xbox360'];d['revision']='v2.1 universal package, no device selection, 2026-11-04'
 d['cache_generation']['method']='Shared v2.1 resource cache generation for all platforms.'
 d['v21_compatibility']={'output':'one identical XBE and game-data result; no user-selected device variants','compatibility_changes':'preserves the previously verified v2.1 XeFu candidate byte-for-byte','intended_platforms':['Original Xbox','Xbox 360 (XeFu)','xemu','hakuX'],'hardware_verified':False,'xemu_current_candidate_playtest':False,'hakux_current_candidate_playtest':False,'validation_file':'audit/verification.json'}
 return json.dumps(d,ensure_ascii=False,indent=2).encode()

def compress(data):
 c=zlib.compressobj(9,zlib.DEFLATED,-15);return c.compress(data)+c.flush()

def reconstruct(source,encoded):
 r=json.loads(zlib.decompress(base64.b64decode(encoded)))
 assert hashlib.sha256(source).hexdigest()==r['source_sha256'],'Previous ZIP differs'
 with zipfile.ZipFile(io.BytesIO(source)) as z:plan=plan_update(json.loads(z.read('NGB_Korean_Patch_v2.1/ngb_native11/assets/build_plan.json')))
 blocks=[];manifest={};manifest_index=None
 for i,x in enumerate(r['blocks']):
  if x[0]=='copy':data=source[x[1]:x[1]+x[2]]
  elif x[0]=='data':data=base64.b64decode(x[1])
  elif x[0]=='plan':data=compress(plan)
  elif x[0]=='manifest':manifest_index=i;data=b''
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
