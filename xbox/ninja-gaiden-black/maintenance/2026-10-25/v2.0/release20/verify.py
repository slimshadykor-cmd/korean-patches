from pathlib import Path
import json,zipfile,hashlib,sys,struct,tempfile
R=Path('release20');P=R/'extracted/NGB_Korean_Patch_v2.0';sys.path.insert(0,str((P/'ngb_native11').resolve()));import patch_iso as I
sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((P/'ngb_native11/assets/build_plan.json').read_text());target=(R/'fixed.xbe').read_bytes();rows=[]
for f in ['original.xbe','profile_fix/test6.xbe','save_probe/test7.xbe','save_probe8/test8.xbe','save_fix9/test9.xbe','crash_analysis/memory_fix.xbe','ui_audit/memory_fix.xbe','save_crash_fix/fixed.xbe','release20/fixed.xbe']:
 b=Path(f).read_bytes();h=sha(b);cs=plan['xbe']['changes'] if h==plan['xbe']['source_sha256'] else [] if h==sha(target) else next(r['changes'] for r in plan['boot_repairs'] if r['previous_xbe_sha256']==h)
 import base64
 out=bytearray(b)
 for c in cs:v=base64.b64decode(c['data']);out[c['offset']:c['offset']+len(v)]=v
 out=out[:plan['xbe']['output_length']];assert bytes(out)==target;I.validate_xbe(out);rows.append(f)
# Real sprite, synthetic AFS container; only version rectangle changes.
a=next(a for a in plan['archives'] if a['path']=='demo.afs');sp=a['version_member'];b=(P/'ngb_native11/assets/members/demo.afs/demo.spr').read_bytes();n=1;buf=bytearray(2048);buf[:4]=b'AFS\0';struct.pack_into('<I',buf,4,n);struct.pack_into('<II',buf,8,2048,len(b));buf+=b;buf+=b'\0'*(-len(buf)%2048);off=len(buf);names=bytearray(48);names[:8]=b'demo.spr';struct.pack_into('<I',names,44,len(b));buf+=names;buf+=b'\0'*(-len(buf)%2048);struct.pack_into('<II',buf,16,off,48);buf=bytes(buf)
entry={'index':0,'name':'demo.spr','offset':2048,'size':len(b)};spec={'path':'demo.afs','entries':[entry],'members':[next(m for m in a['members'] if m['name']=='demo.spr')],'output_sha256':sha(buf),'version_member':sp}
new=I.rebuild_archive(buf,spec,P/'ngb_native11');assert new!=buf;assert I.version_member(new,spec,False)==buf;assert I.archive_digest(new,spec)==sha(buf);assert I.rebuild_archive(new,spec,P/'ngb_native11')==new
bad=bytearray(new);bad[1000]^=1
try:I.rebuild_archive(bytes(bad),spec,P/'ngb_native11')
except ValueError:pass
else:raise AssertionError('tamper accepted')
# Native packaged patcher execution including archive transform, XISO/raw and original/old/new XBE.
import subprocess
F=R/'fixtures';F.mkdir(exist_ok=True);mini=json.loads(json.dumps(plan));mini['archives']=[spec];mini['root_patches']=[];(F/'package/assets/members/demo.afs').mkdir(parents=True,exist_ok=True);(F/'package/assets/members/demo.afs/demo.spr').write_bytes(b);(F/'package/assets/build_plan.json').write_text(json.dumps(mini));cases=[]
for f,arc in [('original.xbe',buf),('save_crash_fix/fixed.xbe',buf),('release20/fixed.xbe',new)]:
 for base in [0,405798912]:
  source=F/'input.iso';output=F/'output.iso';output.unlink(missing_ok=True);xbe=Path(f).read_bytes();d=bytearray(2048);d[:20]=b'MICROSOFT*XBOX*MEDIA';struct.pack_into('<II',d,20,33,56)
  rec1=struct.pack('<HHIIBB',0,7,34,len(xbe),0,11)+b'default.xbe';pos2=34+(len(xbe)+2047)//2048;rec2=struct.pack('<HHIIBB',0,0,pos2,len(arc),0,8)+b'demo.afs'
  with source.open('wb') as out:out.seek(base+65536);out.write(d);out.write(rec1+b'\0'*(28-len(rec1))+rec2);out.seek(base+34*2048);out.write(xbe);out.seek(base+pos2*2048);out.write(arc);out.write(b'\0'*(-out.tell()%2048))
  r=subprocess.run([sys.executable,str(P/'ngb_native11/patch_iso.py'),'--source',str(source),'--output',str(output),'--package',str(F/'package')],capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
  with output.open('rb') as out:base2,files=I.root_files(out);assert base2==0;assert I.get(out,files['default.xbe'])==target;assert I.get(out,files['demo.afs'])==new
  cases.append([f,base]);source.unlink();output.unlink()
manifest=json.loads((P/'FILE_HASHES.json').read_text())
for f,h in manifest.items():assert sha((P/f).read_bytes())==h,f
with zipfile.ZipFile(R/'NGB_Korean_Patch_v2.0.zip') as z:assert z.testzip() is None
report={'status':'PASS','supported_xbe_inputs':rows,'actual_patcher_iso_cases':cases,'files_hash_checked':len(manifest),'version_member_roundtrip_and_tamper_check':True,'scope':'Real sprite in synthetic AFS/ISO; no complete original game ISO or xemu execution. Earlier runtime regressions reused; executable changes only cache generation stamp and section digest.'};(R/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
