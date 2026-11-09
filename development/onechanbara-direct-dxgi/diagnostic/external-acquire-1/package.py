"""Package only the external ownership synchronization candidate.

Preserves the exact Windows-tested BOM-aware launcher. Rejects stale runtimes
and creates a distinct top-level directory, leaving the comparison baseline.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import struct
import zipfile

SOURCE_COMMIT = '8d6b3d2ea51f41e9fd11943a5e6216874c22566f'
RUN_URL = 'https://github.com/slimshadykor-cmd/korean-patches/actions/runs/42626746831'
LAUNCHER_SHA = 'fe93febb207bad63f64e68e3f52bf6ad7132e8d04252ada28c6ba85eabe2d164'
BASE_RUNTIME_SHA = '653b2fa6fa15b72e30a21da8b2ae13d89b15236740951f1218b250094248e28e'
REVISION = 'external-acquire-1'
PREFIX = 'Onechanbara_SyncCheck_v1.7/'
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runtime_zip', type=Path)
    parser.add_argument('runtime_metadata', type=Path)
    parser.add_argument('launcher_build', type=Path)
    parser.add_argument('output_zip', type=Path)
    args = parser.parse_args()
    meta = json.loads(args.runtime_metadata.read_text(encoding='utf-8-sig'))
    assert meta['source_commit'] == SOURCE_COMMIT
    assert meta['run_url'] == RUN_URL
    assert meta['version'] == '1.7' and meta['windows_build'] is True
    assert meta['gpu_play_test'] is False
    assert meta['display_revision'] == 'diagnostic-output-1'
    assert meta['sync_revision'] == REVISION
    assert sha(args.runtime_zip.read_bytes()) == meta['archive_sha256']
    with zipfile.ZipFile(args.runtime_zip) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {'xenia_onechanbara.exe', 'build.json', 'Xenia-LICENSE.txt', 'Display-Interop-LICENSE.txt'}
        runtime = z.read('xenia_onechanbara.exe')
        inner = json.loads(z.read('build.json'))
        assert all(meta[key] == value for key, value in inner.items())
        files = {'runtime/' + name: z.read(name) for name in z.namelist()}
    assert sha(runtime) == meta['exe_sha256'] != BASE_RUNTIME_SHA
    assert len(runtime) == meta['exe_bytes']
    pe = struct.unpack_from('<I', runtime, 0x3c)[0]
    assert runtime[:2] == b'MZ' and runtime[pe:pe+4] == b'PE\0\0'
    assert struct.unpack_from('<H', runtime, pe+4)[0] == 0x8664
    assert b'external-acquire-1' in runtime
    assert b'NvAPI_DRS' not in runtime
    files['runtime/build.json'] = json.dumps(meta, indent=2).encode()
    launcher = (args.launcher_build / 'Onechanbara_Diagnostics.exe').read_bytes()
    assert sha(launcher) == LAUNCHER_SHA
    assert b'asInvoker' in launcher
    files['Onechanbara_Diagnostics.exe'] = launcher
    launcher_tests = json.loads((args.launcher_build / 'Windows-test-results.json').read_text(encoding='utf-8-sig'))
    assert launcher_tests['success'] is True
    assert launcher_tests['launcher_sha256'] == LAUNCHER_SHA
    assert launcher_tests['actual_windows_netframework_execution'] is True
    assert launcher_tests['actual_gpu_gameplay_test'] is False
    files['validation/prior-launcher-Windows-tests.json'] = json.dumps(launcher_tests, indent=2).encode()
    for name in ('copy-protocol-validation.json', 'mutation-validation.json', 'source-checkout-validation.json'):
        files['validation/' + name] = (HERE / name).read_bytes()
    assert json.loads(files['validation/copy-protocol-validation.json'])['passed'] == 51
    assert all(m['rejected'] for m in json.loads(files['validation/mutation-validation.json'])['mutations'])
    files['먼저읽기.txt'] = '''오네찬바라 v1.7 · 화면 동기화 검증본

1. 압축을 별도 폴더에 풀고 Onechanbara_Diagnostics.exe를 실행합니다.
2. 기본으로 선택된 1번 모드에서 「선택한 모드 실행」을 누릅니다.

이번에는 1번 모드만 확인하시면 됩니다. 2·3번 비교를 반복할 필요가 없습니다.
기존 진단 폴더나 Xenia 원본 폴더에 덮어쓰지 마십시오.
설치 기록은 자동으로 찾습니다. 자동 탐색이 안 되면 이전에 사용한
E:\\xenia_canary_windows\\config\\OnechanbaraDirect\\install.json을 선택합니다.
처음 한 번은 기존 셰이더 캐시의 복사본을 준비하며, 이후 재사용합니다.

변경: Vulkan/DXGI 공유 화면을 넘겨받는 작업이 기존 GPU 신호를 제대로
기다리도록 수정했습니다. 새 CPU 대기, 프레임 제한, 추가 fence는 없습니다.
사키 머리카락 문제가 해결되었다고 확정한 패치는 아닙니다.
초반 대화에서 사키 뒷머리 윤곽이 순간적으로 튀는지와 기존 전투 프레임을
같은 조건에서 확인하기 위한 별도 검증본입니다. 실제 GPU 검증은 남아 있습니다.

기존 Windows 검사를 통과한 실행기를 동일한 바이트로 재사용했습니다.
NVIDIA 설정/프로필, 원본 Xenia 실행파일/설정, 게임 ISO/한글패치,
콤보 타이밍/게임 속도/내부 배율은 변경하지 않습니다.
세이브는 이전과 같은 원래 경로를 사용하므로 플레이 중 저장은 그대로 반영됩니다.
게임을 종료하면 실행 기록을 자동 정리합니다. 드라이버 설정을 바꾸지 않으므로
종료 후 NVIDIA 설정을 복구하는 절차도 없습니다.

확인된 범위: Windows 전체 런타임 빌드, 동기화 모의 검사 51개,
두 곳의 이전 잘못된 대기를 각각 복원하면 검사가 실패하는 회귀 검증.
기존 런처의 Windows 검사 기록은 런처 자체에만 해당하며 새 런타임의
실제 게임 실행/그래픽/성능 검증을 의미하지 않습니다.

버전 표기는 1.7입니다. 내부 수정 식별자는 external-acquire-1입니다.
로그의 sync_revision=external-acquire-1로 이번 실행을 구분합니다.
소스: https://github.com/slimshadykor-cmd/korean-patches/tree/8d6b3d2ea51f41e9fd11943a5e6216874c22566f/development/onechanbara-direct-dxgi/source
'''.encode('utf-8-sig')
    report = {
        'version': '1.7', 'sync_revision': REVISION,
        'runtime_source_commit': SOURCE_COMMIT, 'build_url': RUN_URL,
        'runtime_sha256': sha(runtime), 'launcher_sha256': sha(launcher),
        'launcher_reused_byte_for_byte': True,
        'prior_launcher_windows_validation_only': True,
        'sync_contract_mock_checks': 51, 'rejected_old_wait_mutations': 2,
        'native_wait_policy_unchanged': True,
        'shader_translation_unchanged': True,
        'actual_gpu_gameplay_test': False, 'hair_issue_confirmed_fixed': False,
    }
    files['validation/package-validation.json'] = json.dumps(report, indent=2).encode()
    files['SHA256SUMS.txt'] = ''.join(sha(data) + '  ' + name + '\n' for name, data in sorted(files.items())).encode()
    args.output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts
            z.writestr(PREFIX + name, data)
    with zipfile.ZipFile(args.output_zip) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files)
        for name, data in files.items():
            assert z.read(PREFIX + name) == data
    report.update(package_bytes=args.output_zip.stat().st_size,
                  package_sha256=sha(args.output_zip.read_bytes()), entries=len(files))
    args.output_zip.with_suffix('.validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
