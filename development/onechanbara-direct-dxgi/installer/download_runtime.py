"""Fetch a successful pinned development build and verify its runtime hashes."""
from pathlib import Path
import hashlib, json, sys, urllib.request, zipfile, tempfile, re

revision = sys.argv[1]
assert re.fullmatch(r'[0-9a-f]{40}', revision)
expected_source = 'bb56f39c5725a646358cca1e465128965387f001'
base = ('https://raw.githubusercontent.com/slimshadykor-cmd/korean-patches/'
        + revision + '/development/onechanbara-direct-dxgi/runtime/')
out = Path(__file__).resolve().parent / 'runtime'
out.mkdir(exist_ok=True)
with urllib.request.urlopen(base + 'build.json', timeout=60) as response:
    metadata_bytes = response.read()
metadata = json.loads(metadata_bytes)
assert metadata['source_commit'] == expected_source
assert metadata['display_revision'] == 'paced-output-1'
assert metadata['windows_build'] and metadata['architecture'] == 'AMD64'
assert metadata['gpu_play_test'] is False
name = 'Onechanbara_DirectDXGI_Runtime_v1.7.zip'
with tempfile.TemporaryDirectory(prefix='ocb-runtime-download-') as temp:
    archive = Path(temp) / name
    with urllib.request.urlopen(base + name, timeout=120) as response:
        with archive.open('wb') as target:
            while block := response.read(1024 * 1024):
                target.write(block)
    data = archive.read_bytes()
    assert hashlib.sha256(data).hexdigest() == metadata['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {'xenia_onechanbara.exe', 'Xenia-LICENSE.txt',
                                    'Display-Interop-LICENSE.txt', 'build.json'}
        assert z.testzip() is None
        exe = z.read('xenia_onechanbara.exe')
        assert len(exe) == metadata['exe_bytes']
        assert hashlib.sha256(exe).hexdigest() == metadata['exe_sha256']
        assert b'paced-output-1' in exe and b'Onechanbara display stats' in exe
        assert b'NvAPI_DRS' not in exe
        for filename in z.namelist():
            if filename != 'build.json':
                (out / filename).write_bytes(z.read(filename))
    (out / name).write_bytes(data)
    (out / 'build.json').write_bytes(metadata_bytes)
print(json.dumps({'verified_runtime': metadata, 'artifact_commit': revision}))
