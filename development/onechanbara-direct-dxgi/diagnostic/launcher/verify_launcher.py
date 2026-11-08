from pathlib import Path
import hashlib,json,struct,tomllib

root=Path(__file__).resolve().parent
data=(root/'Onechanbara_Diagnostics.exe').read_bytes()
offset=struct.unpack_from('<I',data,0x3c)[0]
assert data[:2]==b'MZ' and data[offset:offset+4]==b'PE\0\0'
assert struct.unpack_from('<H',data,offset+4)[0]==0x8664
assert struct.unpack_from('<H',data,offset+24+68)[0]==2
assert b'level="asInvoker"' in data and b'level="requireAdministrator"' not in data
build=json.loads((root/'launcher-build.json').read_text(encoding='utf-8-sig'))
assert hashlib.sha256(data).hexdigest()==build['sha256']
source=(root/'DiagnosticLauncher.cs').read_text()+(root/'DiagnosticCore.cs').read_text()
for disallowed in ['NvAPI','Registry.','reg.exe','powershell.exe','pwsh.exe','.Kill(','CreateSymbolicLink','cmd.exe']:
    assert disallowed not in source,disallowed
assert 'CloseMainWindow()' in source and 'FileMode.CreateNew' in source
original=tomllib.loads((root/'../../upload/Onechanbara.config.toml').read_text(encoding='utf-8-sig'))
allowed={('Storage','storage_root'),('Storage','cache_root'),('Storage','content_root'),('Logging','log_file'),('GPU.Debug','trace_gpu_prefix'),('Vulkan','vulkan_allow_present_mode_immediate'),('Vulkan','vulkan_allow_present_mode_mailbox'),('Vulkan','vulkan_allow_present_mode_fifo_relaxed'),('Vulkan','vulkan_direct_dxgi'),('Vulkan','onechanbara_guest_output'),('Display','onechanbara_diagnostics')}
runs=sorted((root/'tests').glob('run_*'),key=lambda p:p.stat().st_mtime)
results=[]
for mode in range(3):
    actual=tomllib.loads((runs[-1]/f'mode_{mode}.toml').read_text())
    changed=[]
    def flatten(d,prefix=''):
        output={}
        for key,value in d.items():
            if isinstance(value,dict): output.update(flatten(value,prefix+key+'.'))
            else: output[(prefix.rstrip('.'),key)]=value
        return output
    before,after=flatten(original),flatten(actual)
    for key,value in before.items():
        if after[key]!=value:
            assert key in allowed,(key,value,after[key])
            changed.append('.'.join(key))
    for key in after.keys()-before.keys(): assert key in allowed,key
    results.append({'mode':mode,'changed_existing_keys':changed,'gameplay_settings_equal':True})
report={'pe_x64_gui':True,'as_invoker':True,'artifact_hash_verified':True,'forbidden_actions_absent_in_launcher_sources':True,'config_diff_checks':results,'native_windows_gui_test':False,'gpu_test':False}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
