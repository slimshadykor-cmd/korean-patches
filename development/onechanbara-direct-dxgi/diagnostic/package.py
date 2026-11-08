"""Package the verified comparison runtime without replacing the recovery ZIP."""
from pathlib import Path
import hashlib,json,struct,zipfile

R=Path(__file__).resolve().parent
source='5895522ba3fc918e7bcc3ad7cfc0acc1dae49a26'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((R/'runtime/build.json').read_text())
assert meta['version']=='1.7' and meta['display_revision']=='diagnostic-output-1'
assert meta['source_commit']==source and meta['windows_build'] is True
assert meta['gpu_play_test'] is False
assert sha(R/'runtime/xenia_onechanbara.exe')==meta['exe_sha256']
launcher=R/'launcher/Onechanbara_Diagnostics.exe'
launcher_meta=json.loads((R/'launcher/launcher-build.json').read_text())
assert sha(launcher)==launcher_meta['sha256']
data=launcher.read_bytes();offset=struct.unpack_from('<I',data,0x3c)[0]
assert data[offset:offset+4]==b'PE\0\0' and struct.unpack_from('<H',data,offset+4)[0]==0x8664
assert b'asInvoker' in data
core=json.loads((R/'launcher/test-results.json').read_text())
assert core['passed']==62
validation={
 'version':'1.7','revision':'diagnostic-output-1','stable_patch':False,
 'source_commit':source,'runtime':meta,'launcher_sha256':sha(launcher),
 'source':json.loads((R/'source-validation.json').read_text()),
 'launcher_checks':core['passed'],
 'launcher_layout':json.loads((R/'launcher/layout-test-results.json').read_text()),
 'launcher_structure':json.loads((R/'launcher/verification.json').read_text()),
 'copy_protocol':json.loads((R/'protocol_tests/copy-protocol-validation.json').read_text()),
 'scheduling':json.loads((R/'protocol_tests/pacing-validation.json').read_text()),
 'gpu_probe_protocol':json.loads((R/'gpu_metrics/validation.json').read_text()),
 'physical_windows_game_test':False,
 'hair_regression_fixed':False,
 'performance_improvement_verified':False,
 'unchanged_originals_policy':'No common config, shortcut, original runtime, ISO or NVIDIA profile writes. Game saves still use original content.'}
(R/'validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False))
files={
 'Onechanbara_Diagnostics.exe':launcher,
 '먼저읽기.txt':R/'먼저읽기.txt',
 '검토결과.txt':R/'검토결과.txt',
 'validation.json':R/'validation.json',
 'runtime/xenia_onechanbara.exe':R/'runtime/xenia_onechanbara.exe',
 'runtime/build.json':R/'runtime/build.json',
 'runtime/Xenia-LICENSE.txt':R/'runtime/Xenia-LICENSE.txt',
 'runtime/Display-Interop-LICENSE.txt':R/'runtime/Display-Interop-LICENSE.txt'}
sums=''.join(sha(p)+'  '+n+'\n' for n,p in sorted(files.items()))
(R/'SHA256SUMS.txt').write_text(sums)
files['SHA256SUMS.txt']=R/'SHA256SUMS.txt'
release=R/'release';release.mkdir(exist_ok=True)
out=release/'Onechanbara_Diagnostics_v1.7.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,path in files.items():z.write(path,name)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None and set(z.namelist())==set(files)
 for name,path in files.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha(path)
report={'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out),'entries':len(files),'runtime_sha256':meta['exe_sha256'],'launcher_sha256':sha(launcher),'source_commit':source,'actual_gpu_test':False}
(R/'package-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
