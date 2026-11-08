from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
pairs={}
for n in ['DiagnosticCore.cs','DiagnosticLauncher.cs','AssemblyInfo.cs','app.manifest','build.ps1','README.txt','launcher-build.json','test-results.json','verification.json','test_core.ps1','test_runtime_layout.ps1','layout-test-results.json','verify_launcher.py']:
    if (R/'launcher'/n).exists():pairs['launcher/'+n]=R/'launcher'/n
for n in ['transform.py','ocb_gpu_timing.h','test_gpu_timing.cc','test_transform.py','validation.json','README.txt']:
    pairs['gpu-metrics/'+n]=R/'gpu_metrics'/n
for n in ['add_diagnostics.py','diagnostic_metrics.inc','diagnostic_statistics.h']:
    pairs['source-generation/'+n]=R/'generator/non_nv/integration'/n
for n in ['package.py','download_runtime.py','test_frame_statistics.cc','source-validation.json','먼저읽기.txt','검토결과.txt','validation.json','package-validation.json','checkpoint.json','prepare_publish.py']:
    if (R/n).exists():pairs[n]=R/n
for n in ['test_copy_protocol.py','copy-protocol-validation.json','pacing_test.cc','pacing-validation.json']:
    pairs['protocol-tests/'+n]=R/'protocol_tests'/n
entries=[{'path':'development/onechanbara-direct-dxgi/diagnostic/'+k,'mode':'100644','type':'blob','content':v.read_text()} for k,v in pairs.items()]
assert all('/diagnostic/' in e['path'] for e in entries)
(R/'pending-publish-entries.json').write_text(json.dumps(entries,ensure_ascii=False))
print(json.dumps({'review_and_source_files':len(entries),'workflow_trigger_paths_modified':False,'launcher_sha256':hashlib.sha256((R/'launcher/Onechanbara_Diagnostics.exe').read_bytes()).hexdigest()}))
