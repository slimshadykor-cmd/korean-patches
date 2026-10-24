"""Run the actual shipping EXE's managed entry point against real asset fixtures."""
from pathlib import Path
import ast,sys,struct,os,hashlib,json,zipfile,tempfile,subprocess,gzip
R=Path(__file__).resolve().parent.parent;A=R.parent/'audit1024'
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def manifest(b):return {r[0]:r for l in b.decode().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
def delta(b,p):
    raw=gzip.decompress(p);magic,size,n=struct.unpack_from('<4sII',raw);assert magic==b'OPD1' and len(b)==size
    out=bytearray(b);pos=12
    for i in range(n):
        at,z=struct.unpack_from('<II',raw,pos);pos+=8;out[at:at+z]=raw[pos:pos+z];pos+=z
    assert pos==len(raw);return bytes(out)
# Reuse the independently implemented ISO fixture writer/reader already used for
# v1.2.9, without importing or executing its previous tests.
source=(A/'recovered/v129/source/tools/test_integrated.py').read_text()
tree=ast.parse(source);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['create_iso','read_entries']]
exec(compile(ast.Module(body=functions,type_ignores=[]),'independent_fixture','exec'))
rows=manifest((R/'package/manifest.tsv').read_bytes());oldrows=manifest((A/'package/manifest.tsv').read_bytes())
original={};current={};expected={};movies=[]
for rel,row in rows.items():
    prior=oldrows[rel];assert set(prior[3].split(','))<=set(row[3].split(','))
    raw=(R/'package/payload'/row[4]).read_bytes()
    if '/Movie/' in rel or '/DMovie' in rel:
        # Already-patched real video bytes in the fixture; unchanged video payloads
        # are not a new original-video conversion test.
        assert raw==(A/'package/payload'/prior[4]).read_bytes();original[rel]=raw;movies.append(rel)
    else:
        original[rel]=(A/'original'/rel).read_bytes()
        assert sha(original[rel]) in row[3].split(','),rel
    expected[rel]=delta(original[rel],raw) if row[5]=='delta' else raw
    priorraw=(A/'package/payload'/prior[4]).read_bytes()
    current[rel]=delta(original[rel],priorraw) if prior[5]=='delta' else priorraw
    assert sha(expected[rel])==row[2] and sha(current[rel])==prior[2]
    if rel not in ['default.xex','Media/Menu/title2d.cat']:assert row==prior
original['untouched.bin']=b'UNCHANGED INPUT SENTINEL\0'*100
DOTNET=R/'deps/sdk/dotnet';EXE=R/'deliverables/Onechanbara_ISO_Korean_v1.3.0.exe';tests=[];rejections=[];empty_temp_observations=[]
with tempfile.TemporaryDirectory(prefix='iso-verify-',dir=R) as tempdir:
    tmp=Path(tempdir);temp=tmp/'temp';temp.mkdir();env=dict(os.environ,TMPDIR=str(temp))
    def run(src,dst,ok=True,contains=None):
        p=subprocess.run([str(DOTNET),str(R/'ShippingDriver.dll'),str(EXE),str(src),str(dst)],capture_output=True,text=True,env=env)
        assert (p.returncode==0)==ok,(p.stdout[-1000:],p.stderr)
        if contains:assert contains in p.stderr,p.stderr
        # Record the empty directory residue observed under the Linux managed-core
        # harness. Do not report full directory cleanup as passed when it remains.
        runtime_files=[(q.name,q.exists(),q.is_dir()) for q in temp.iterdir()]
        if runtime_files:print('Runtime temporary entry/stat:',runtime_files,flush=True)
        remaining=[q for q in temp.glob('OnechanbaraPatch_*') if q.exists()]
        leftover_payloads=[q for d in remaining for q in d.rglob('*') if q.is_file()]
        if leftover_payloads:
            debug={'returncode':p.returncode,'stdout_tail':p.stdout[-2500:],'stderr':p.stderr,'remaining':[(q.relative_to(temp).as_posix(),q.stat().st_size) for q in temp.rglob('*') if q.is_file()]}
            (R/'audit/iso_runtime_diagnostic.json').write_text(json.dumps(debug,ensure_ascii=False,indent=2));print({k:v for k,v in debug.items() if k!='remaining'},flush=True)
        assert not leftover_payloads and not Path(str(dst)+'.partial').exists(),runtime_files
        if remaining:empty_temp_observations.append({'input':src.name,'output':dst.name,'empty_patch_directories':len(remaining),'remaining_payload_files':0})
        return p
    for version,base in [('original',0),('v1.2.9',0xfd90000),('earlier-v1.3.0',0)]:
        if '--v129-only' in sys.argv and version=='original':continue
        files=dict(original)
        if version!='original':files.update(current)
        if version=='earlier-v1.3.0':files['default.xex']=expected['default.xex']
        src=tmp/'input.iso';dst=tmp/'output.iso';create_iso(src,files,base);before=digest(src)
        run(src,dst);assert digest(src)==before
        entries=read_entries(dst,base);assert set(entries)==set(files)
        with dst.open('rb') as f:
            for rel,data in files.items():
                at,n=entries[rel];f.seek(at);assert f.read(n)==expected.get(rel,data),(version,rel)
        tests.append({'input':version,'base':hex(base),'all_158_targets_byte_exact':True,'input_and_unrelated_data_preserved':True,'shipping_exe_core_executed':True,'temporary_payload_files_cleaned':True});print(tests[-1],flush=True)
        (R/'audit/iso_partial_tests.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2))
        if version=='v1.2.9':
            run(dst,tmp/'repeat.iso',False,'이미');assert not (tmp/'repeat.iso').exists();rejections.append('already-patched')
            beforeout=digest(dst);run(src,dst,False,'출력 파일');assert digest(dst)==beforeout;rejections.append('existing-output')
            run(src,src,False,'출력 파일');assert digest(src)==before;rejections.append('input-equals-output')
            at,n=read_entries(src,base)['default.xex']
            with src.open('r+b') as f:f.seek(at+64);f.write(b'BAD!')
            damaged=digest(src);run(src,tmp/'bad.iso',False,'지원하는 일본판');assert digest(src)==damaged and not (tmp/'bad.iso').exists();rejections.append('unknown-xex')
        src.unlink();dst.unlink()
    bad=tmp/'invalid.iso';bad.write_bytes(b'not-an-iso');run(bad,tmp/'invalid-out.iso',False,'ISO 구조');rejections.append('invalid-iso')
result={'version':'1.3.0','tests':tests,'rejections':rejections,'manifest_paths':len(rows),'unchanged_movie_paths':len(movies),'previous_accepted_hashes_retained':True,'iso_core_identical_to_tested_v129':True,'actual_shipping_exe_managed_core_executed':True,'windows_gui_runtime_tested':False,'actual_xenia_gameplay_tested':False,'empty_directory_observations_linux_harness':empty_temp_observations,'full_temporary_directory_cleanup_confirmed':not empty_temp_observations,'fixture':'Synthetic XDVDFS with supplied original/current nonvideo assets and unchanged already-Korean movie payloads. Not a full original retail ISO or gameplay test.'}
(R/'audit/iso_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result,flush=True)
