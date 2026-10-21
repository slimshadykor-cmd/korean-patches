from pathlib import Path
import sys,struct,gzip,hashlib,json,shutil,zipfile,importlib.util
R=Path(__file__).resolve().parent
I=R/'inputs/Onechanbara vorteX 일본판 한글화'
S=R/'baseline_source/release-build/onechanbara-v1.2.8'
for d in ['tools','audit','original','current','candidate','source','deliverables']:(R/d).mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def delta(b,p):
 d=gzip.decompress(p);magic,size,n=struct.unpack_from('<4sII',d);assert magic==b'OPD1' and len(b)==size
 out=bytearray(b);pos=12
 for _ in range(n):
  at,z=struct.unpack_from('<II',d,pos);pos+=8;assert at+z<=size;out[at:at+z]=d[pos:pos+z];pos+=z
 assert pos==len(d);return bytes(out)
for src,dst in [('media_original','Media'),('demo_original/Demo','Media/Demo'),('mission_original/Media/Mission','Media/Mission'),('story_original/Media/Story','Media/Story')]:
 shutil.copytree(R/'recovered'/src,R/'original'/dst,dirs_exist_ok=True)
shutil.copyfile(I/'default.xex',R/'original/default.xex')
rows={r[0]:r for l in (R/'baseline_package/manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
verified=[]
for rel,row in rows.items():
 p=R/'original'/rel
 if not p.exists():
  assert '/Movie/' in rel or '/DMovie' in rel,rel
  continue
 b=p.read_bytes();assert sha(b) in row[3].split(','),rel
 raw=(R/'baseline_package/payload'/row[4]).read_bytes();out=delta(b,raw) if row[5]=='delta' else raw
 assert len(out)==int(row[1]) and sha(out)==row[2],rel
 q=R/'current'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(out);verified.append(rel)
shutil.copytree(R/'current',R/'candidate',dirs_exist_ok=True)
src=(R/'loading_test01/dev/build_candidate.py').read_text().replace("R=Path(__file__).parent;A=R.parent/'loading_analysis_20261021';BASE", "R=Path(__file__).resolve().parent.parent;A=R;BASE").replace("A/'recovered/analysis/source/xex_module.cc'","A/'workbench/analysis/source/xex_module.cc'")
src=src.replace("A/'inputs/Onechanbara vorteX 일본판 한글화/default.xex'","R/'original/default.xex'").replace("R/'baseline_v128.xex'","R/'current/default.xex'")
(R/'tools/loading_candidate.py').write_text(src)
spec=importlib.util.spec_from_file_location('loading_candidate',R/'tools/loading_candidate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.main()
assert sha((R/'kor128_test01.xex').read_bytes())=='1d5ca57194a51bf60eee37f9612f30f275381c85c480b5210a0d0e5895e4573c'
shutil.copyfile(R/'kor128_test01.xex',R/'candidate/default.xex')
for name in ['original','current','candidate']:
 b=(R/name/'default.xex').read_bytes();mem,fmt=m.unpack(b);assert m.repack(b,mem,fmt)==b;(R/(name+'.memory.bin')).write_bytes(mem)
common=(R/'recovered/identifier_evidence/audit_common.py').read_text().replace('W=Path(__file__).resolve().parent','W=Path(__file__).resolve().parent.parent').replace("OUT=W/'evidence'","OUT=W/'audit'").replace("W/'v126/audit/glyph_mapping.json'","W/'baseline_source/release-build/onechanbara-v1.2.8/audit/glyph_mapping.json'")
common=common.replace("def glyphs():return", "def glyphs():return")
(R/'tools/audit_common.py').write_text(common)
(R/'audit/recovery_validation.json').write_text(json.dumps({'baseline_release_sha256':sha((I/'Onechanbara_ISO_Korean_v1.2.8_Release.zip').read_bytes()),'nonvideo_assets_reconstructed_and_hash_verified':verified,'candidate_exactly_matches_user_tested_loading_code':True},indent=2))
print('Reconstructed',len(verified),'assets; exact user-tested candidate recovered.')
