from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent
workspace = root.parent.parent
base = workspace / 'non_nv/dependencies/xenia-canary-b083312b8'
patch = workspace / 'non_nv/regression_2145/before/xenia-direct-dxgi.patch'
spec = importlib.util.spec_from_file_location('gpu_transform', root / 'transform.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(dir=root) as temp:
    out = Path(temp)
    for line in patch.read_text().splitlines():
        if line.startswith('+++ b/'):
            rel = line[6:]
            src = base / rel
            if src.is_file():
                dest = out / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dest)
    subprocess.run(['git', 'apply', '--whitespace=nowarn', str(patch)], cwd=out, check=True)
    files = {str(p.relative_to(out)): p.read_text() for p in out.rglob('*') if p.is_file()}
    cc = 'src/xenia/ui/vulkan/vulkan_presenter.cc'
    before = files[cc]
    module.apply(files)
    after = files[cc]
    for token in ('vkQueueWaitIdle', 'AwaitAllSubmissions',
                  'AwaitSubmissionAndUpdateCompleted', 'vkQueueSubmit',
                  'AcquireFenceAndSubmit'):
        assert before.count(token) == after.count(token), token
    assert after.index('gpu_output_timing.Submitted(gpu_timing_slot)') > after.index('if (submit_result != VK_SUCCESS)')

binary = root / 'test_gpu_timing'
subprocess.run(['g++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
    '-Wno-missing-field-initializers', '-I'+str(root/'test_stubs'),
    '-I'+str(workspace/'non_nv/dependencies/Vulkan-Headers-1.3.296/include'),
    str(root/'test_gpu_timing.cc'), '-o', str(binary)], check=True)
subprocess.run([str(binary)], check=True)
report = {'exact_paced_patch_applies': True, 'source_transform_applies': True,
    'no_new_wait_or_submit_calls': True, 'gpu_probe_api_protocol_mock_test': True,
    'physical_gpu_test': False, 'scope': 'Vulkan final output GPU interval; may include semaphore stalls',
    'engine_busy_time': False, 'd3d12_copy_gpu_time': False, 'guest_render_gpu_time': False}
(root/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
