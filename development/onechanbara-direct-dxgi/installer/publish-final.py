"""Package the verified Windows installer and update existing release pages."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent / 'release'
REPO = 'slimshadykor-cmd/korean-patches'
TAG = 'onechanbara-v1.4.0'
PAGE = f'https://github.com/{REPO}/releases/tag/{TAG}'
ASSET = 'Onechanbara_Korean_DirectDXGI_v1.7.zip'
URL = f'https://github.com/{REPO}/releases/download/{TAG}/{ASSET}'

def gh(*args, body=None):
    return subprocess.check_output(
        ['gh', *args], input=None if body is None else json.dumps(body).encode('utf-8')
    ).decode('utf-8')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def update_body(release, block, marker):
    endpoint = f"repos/{REPO}/releases/{release['id']}"
    before = json.loads(gh('api', endpoint))['body'] or ''
    pattern = f'<!-- {marker}:start -->.*?<!-- {marker}:end -->'
    after = re.sub(pattern, lambda _: block, before, count=1, flags=re.S) if re.search(pattern, before, re.S) else block + '\n\n' + before
    if before != after:
        actual = json.loads(gh('api', endpoint, '-X', 'PATCH', '--input', '-', body={'body': after}))
        if actual['body'] != after:
            raise RuntimeError(f"Release notes verification failed for {release['tag_name']}")

def main():
    exe = ROOT / 'Onechanbara_Korean_v1.7.exe'
    checks = Path(__file__).with_name('install-validation.json')
    readme = """오네찬바라 볼텍스 일본판 한글패치 v1.7 · Xenia 직접 화면 출력
한글화 슬림쉐이디

압축을 풀고 Onechanbara_Korean_v1.7.exe를 실행합니다.
일본판 원본 또는 지원하는 한글 ISO에 한글패치를 적용합니다.
이미 v1.7 한글 ISO가 있다면 기존 ISO 실행 연결 버튼을 이용하세요.
설치 시 기존 xenia_canary.exe를 선택하고 바탕화면의 오네찬바라 바로가기로 실행합니다.
바로가기에 사용자 플레이에서 확인한 화면 출력 방식을 적용했습니다.

새 설치에는 기존 Xenia와 content 폴더의 프로필 및 저장 데이터가 필요합니다.
빈 캐시 검증 전에는 content와 일본판 원본 ISO를 백업하세요.
다른 게임의 공용 캐시는 보존하고, 오네찬바라 전용 캐시와
공용 캐시 안에 남아 있는 445007D2 항목만 따로 옮기세요.
첫 실행과 같은 구간을 두 번째로 실행했을 때의 프레임을 비교하세요.

실행파일의 Windows 빌드와 설치 검사를 수행했습니다.
앞선 사용자 플레이에서 사키 뒷머리 윤곽 문제가 재현되지 않았습니다.
이 통합 설치본의 빈 캐시 실게임 테스트는 예정되어 있습니다.
"""
    path = ROOT / ASSET
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as package:
        package.write(exe, exe.name)
        package.writestr('먼저읽기.txt', readme.encode('utf-8-sig'))
        package.writestr('SHA256SUMS.txt', f'{digest(exe)}  {exe.name}\n')
        package.write(checks, 'validation/install-validation.json')
        package.write(ROOT / 'original/원본ISO_해시.txt', '원본ISO_해시.txt')
        for name in ('Xenia-LICENSE.txt', 'Display-Interop-LICENSE.txt', 'build.json'):
            package.write(ROOT / 'runtime' / name, 'licenses/' + name)
    with zipfile.ZipFile(path) as package:
        if package.testzip() is not None:
            raise RuntimeError('Corrupt release ZIP')
    sha = digest(path)
    if os.environ.get('GITHUB_REPOSITORY') != REPO or not os.environ.get('GH_TOKEN'):
        raise RuntimeError('Release publication requires the authorized repository workflow')
    releases = json.loads(gh('api', f'repos/{REPO}/releases?per_page=100'))
    current = next(r for r in releases if r['tag_name'] == TAG and not r['draft'])
    existing = next((a for a in current['assets'] if a['name'] == ASSET), None)
    if existing is None:
        gh('release', 'upload', TAG, str(path), '--repo', REPO)
    elif existing.get('digest') != 'sha256:' + sha:
        raise RuntimeError('Final asset name is already in use by a different file')
    after = json.loads(gh('api', f"repos/{REPO}/releases/{current['id']}"))
    asset = next(a for a in after['assets'] if a['name'] == ASSET)
    if asset.get('digest') != 'sha256:' + sha or asset['size'] != path.stat().st_size:
        raise RuntimeError('Published asset does not match the verified ZIP')
    block = f"""<!-- direct-dxgi-v17:start -->
## v1.7 최종 통합판 · Xenia 화면 동기화

**[최종 통합판 ZIP 다운로드]({URL})**

한글패치 설치 후 바탕화면의 오네찬바라 바로가기로 실행하세요.
기존 v1.7 한글 ISO는 설치기의 실행 연결 버튼으로 등록할 수 있습니다.
검증에서 사용한 화면 출력 방식을 바로가기에 적용했습니다.

기존 일반 Xenia의 프로필 및 세이브 위치인 `content`를 사용합니다.
사용자 플레이에서 사키 뒷머리 윤곽 문제가 재현되지 않았습니다. 빈 캐시에서의 통합판 플레이 확인은 예정되어 있습니다.

SHA-256 `{sha}`

아래는 이전 v1.7 배포 파일과 변경 기록입니다.
<!-- direct-dxgi-v17:end -->"""
    update_body(current, block, 'direct-dxgi-v17')
    previous = [r for r in releases if r['tag_name'].startswith('onechanbara-') and r['tag_name'] != TAG and not r['draft']]
    banner = f"""<!-- latest-patch-navigation:start -->
> **[최신 오네찬바라 볼텍스 한글패치 v1.7 최종 통합판]({PAGE})**
> 설치 후 바탕화면 바로가기로 실행할 수 있습니다.
<!-- latest-patch-navigation:end -->"""
    for release in previous:
        update_body(release, banner, 'latest-patch-navigation')
    print(json.dumps({'download': URL, 'sha256': sha, 'size': path.stat().st_size,
                      'previous_releases_updated': [r['tag_name'] for r in previous]}, ensure_ascii=True))

if __name__ == '__main__':
    main()
