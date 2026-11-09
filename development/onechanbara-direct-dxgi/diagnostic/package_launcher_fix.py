"""Replace only the launcher and validation notes in the known diagnostic ZIP."""
from pathlib import Path
import argparse, hashlib, json, struct, zipfile

BASE_SHA = '11a69c0b1862168b3b96cacd00ddf96f3a02159467f1195a1223808ebfaf3539'
RUNTIME_SHA = '653b2fa6fa15b72e30a21da8b2ae13d89b15236740951f1218b250094248e28e'
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base_zip', type=Path)
    ap.add_argument('build_directory', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    assert sha(args.base_zip.read_bytes()) == BASE_SHA, 'Unexpected base package'
    with zipfile.ZipFile(args.base_zip) as z:
        assert z.testzip() is None
        files = {n: z.read(n) for n in z.namelist()}
    original = dict(files)
    assert sha(files['runtime/xenia_onechanbara.exe']) == RUNTIME_SHA
    exe = (args.build_directory / 'Onechanbara_Diagnostics.exe').read_bytes()
    offset = struct.unpack_from('<I', exe, 0x3c)[0]
    assert exe[offset:offset + 4] == b'PE\0\0'
    assert struct.unpack_from('<H', exe, offset + 4)[0] == 0x8664
    assert b'asInvoker' in exe
    build = json.loads((args.build_directory / 'launcher-build.json').read_text(encoding='utf-8-sig'))
    tests = json.loads((args.build_directory / 'Windows-test-results.json').read_text(encoding='utf-8-sig'))
    assert build['sha256'] == sha(exe)
    assert tests['passed'] > 0 and tests['success'] is True
    assert tests['actual_windows_netframework_execution'] is True
    assert tests['actual_production_launcher_lifecycle_with_mock_runtime'] is True
    assert tests['launcher_sha256'] == sha(exe)
    files['Onechanbara_Diagnostics.exe'] = exe
    files['Windows-test-results.json'] = json.dumps(tests, ensure_ascii=False, indent=2).encode('utf-8')
    validation = json.loads(files['validation.json'])
    previous = {k: validation.pop(k) for k in ['launcher_sha256', 'launcher_checks', 'launcher_layout', 'launcher_structure']}
    validation['previous_launcher_validation'] = previous
    validation['launcher_sha256'] = sha(exe)
    validation['launcher_revision'] = 'json-encoding-fix'
    validation['launcher_build'] = build
    validation['windows_launcher_tests'] = tests
    validation['runtime_unchanged_from_previous_package'] = True
    validation['physical_windows_game_test'] = False
    files['validation.json'] = json.dumps(validation, ensure_ascii=False, indent=2).encode('utf-8')
    notes = ('실행 오류 수정 — 2026-11-09\n'
             '기존 설치 기록의 UTF-8 BOM(인코딩 표시)을 올바르게 읽도록 수정했습니다.\n'
             '기존 설치 기록을 다시 만들거나 게임을 재설치할 필요가 없습니다.\n'
             'Windows .NET Framework에서 배포 EXE의 기록 읽기와 실행·종료 흐름을 검사했습니다.\n'
             '상세 결과와 실제 게임 화면 검증의 한계는 Windows-test-results.json에 기록했습니다.\n'
             '제니아 런타임은 직전 진단본과 바이트 단위로 동일합니다.\n\n')
    files['먼저읽기.txt'] = notes.encode('utf-8') + files['먼저읽기.txt']
    files['검토결과.txt'] = notes.encode('utf-8') + files['검토결과.txt']
    for name in original:
        if name.startswith('runtime/'):
            assert files[name] == original[name]
    files.pop('SHA256SUMS.txt')
    files['SHA256SUMS.txt'] = ''.join(sha(data) + '  ' + name + '\n' for name, data in sorted(files.items())).encode('utf-8')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in files.items(): z.writestr(name, data)
    with zipfile.ZipFile(args.output) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(files)
        for name, data in files.items(): assert z.read(name) == data
    report = {'path': str(args.output.resolve()), 'bytes': args.output.stat().st_size,
              'sha256': sha(args.output.read_bytes()), 'launcher_sha256': sha(exe),
              'runtime_sha256': RUNTIME_SHA, 'runtime_unchanged': True,
              'windows_launcher_tests_passed': tests['passed'], 'actual_gpu_test': False}
    args.output.with_suffix('.validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
