from pathlib import Path
import hashlib,json,struct,zipfile,subprocess

exe=Path('build/bin/Windows/Release/xenia_canary.exe')
data=exe.read_bytes()
assert len(data)>100000, 'Executable too small'
offset=struct.unpack_from('<I',data,0x3c)[0]
assert data[:2]==b'MZ' and data[offset:offset+4]==b'PE\0\0'
assert struct.unpack_from('<H',data,offset+4)[0]==0x8664, 'Not AMD64'
assert b'vulkan_direct_dxgi' in data, 'New display option missing'
assert b'Onechanbara direct DXGI output' in data, 'New display implementation missing'
assert b'shared image copy' in data, 'Shared image copy implementation missing'
assert b'Onechanbara diagnostic CPU' in data, 'CPU diagnostics missing'
assert b'Onechanbara GPU output' in data, 'GPU diagnostics missing'
assert b'onechanbara_guest_output' in data, 'Scheduling selector missing'
assert b'diagnostic-output-1' in data, 'Diagnostic protocol marker missing'
assert b'external-acquire-1' in data, 'External acquire synchronization marker missing'
from verify_sources import verify_sources
verify_sources(Path.cwd())
assert b'NvAPI_DRS' not in data, 'Unexpected profile-management implementation'
out=Path('../runtime-output');out.mkdir(exist_ok=True)
metadata={'version':'1.7','base':'b083312b8b18e07e6e410b82104191f126722794',
          'display_revision':'diagnostic-output-1','sync_revision':'external-acquire-1','windows_build':True,'architecture':'AMD64','gpu_play_test':False,
          'exe_bytes':len(data),'exe_sha256':hashlib.sha256(data).hexdigest()}
with zipfile.ZipFile(out/'Onechanbara_DirectDXGI_Runtime_v1.7.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    z.writestr('xenia_onechanbara.exe',data)
    z.write('LICENSE','Xenia-LICENSE.txt')
    z.write('src/xenia/ui/vulkan/onechanbara_display/vendor/LICENSE','Display-Interop-LICENSE.txt')
    z.writestr('build.json',json.dumps(metadata,indent=2))
metadata['archive_sha256']=hashlib.sha256((out/'Onechanbara_DirectDXGI_Runtime_v1.7.zip').read_bytes()).hexdigest()
(out/'build.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps(metadata))
