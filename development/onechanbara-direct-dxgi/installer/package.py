from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parent
release=R/'release';runtime=R/'runtime'
exe=release/'Onechanbara_Korean_v1.7.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((runtime/'build.json').read_text())
assert sha(runtime/'xenia_onechanbara.exe')==meta['exe_sha256']
assert meta.get('display_revision')=='paced-output-1', 'Wrong display runtime revision'
readme='''오네찬바라 볼텍스 한글패치 v1.7 — 직접 화면 출력 통합본
한글화 슬림쉐이디

기존 v1.7 ISO를 이미 만드셨다면
1. 압축을 풀고 Onechanbara_Korean_v1.7.exe를 실행합니다.
2. [기존 v1.7 ISO — 바로가기 연결]을 누릅니다.
3. 사용 중인 v1.7 한글 ISO와 기존 xenia_canary.exe를 선택합니다.
4. 바탕화면의 [오네찬바라] 바로가기로 실행합니다.
ISO를 다시 만들 필요는 없습니다.
직전 직접 DXGI판을 설치하셨더라도 같은 버튼으로 연결하면 전용 실행파일을 갱신합니다.

이번 수정 내용 — 내부 출력 식별자 paced-output-1
게임 화면을 출력 스레드에서 직접 전달하도록 수정했습니다.
게임 플레이 중에는 표시 버퍼를 16ms 안에 받지 못했다고 바로 프레임을
포기하지 않고 기다립니다. 수직동기화는 유지하고 UI 창 처리에는 짧은 대기를 씁니다.
화면 전달 단계별 CPU 소요 시간과 전달 함수의 성공 횟수를 매초 한 줄로 기록합니다.
이는 GPU 실행 시간이나 실제 표시 FPS가 아니며, last_run.json에는 실행파일 해시도 남깁니다.
이번 영상의 23~37 FPS 저하 원인이 모두 밝혀진 것은 아닙니다.
실제 게임 성능과 동작 표현이 해결됐는지는 검증되지 않은 수정 후보입니다.

원본 또는 지원하는 이전 한글 ISO라면
[한글패치 적용 — 새 ISO 만들기]로 새 v1.7 ISO를 만드세요.
입력 ISO는 보존됩니다. 한글화·로딩 개선 데이터는 기존 통합본과 동일합니다.

이번 실행 방식
Vulkan/FSI로 게임을 그리고 제니아 자체에서 DXGI 화면 출력을 처리합니다.
게임 시작·종료 때 NVIDIA 프로필을 만들거나 변경하거나 제거하지 않습니다.
바탕화면 바로가기는 일반 권한의 실행파일을 시작합니다. 실행 시 PowerShell과
관리자 권한을 요청하는 NVIDIA 동기화 도구를 거치지 않습니다.
설치 과정에서만 내부 설치 스크립트를 일반 권한으로 실행합니다.

전용 파일 위치
기존 제니아 폴더\\config\\OnechanbaraDirect
기본 제니아 실행파일과 공용 TOML은 교체하지 않습니다.
프로필·저장 데이터는 기존 content 위치를 사용합니다.
기존 전용 설정과 게임 캐시를 읽어 새 전용 폴더에 적용합니다.
기존 바로가기가 있었다면 새 전용 폴더의 [이전 실행 바로가기.lnk]에 보관합니다.

오류 기록
전용 폴더\\logs\\xenia.log
전용 폴더\\logs\\last_run.json

확인 범위
수정한 제니아 전체의 Windows 64비트 빌드, 실행파일 구조, 설치/실패 복구 및
한글패치 데이터 보존을 검사했습니다. 제작 환경에는 실제 Windows GPU가 없어
게임 화면·화면 갈라짐·프레임 성능은 직접 확인하지 못했습니다.
이전에 잘 작동한 NVIDIA 임시 프로필 방식과 성능이 같다고 보장하지 않습니다.

기반 소스
https://github.com/xenia-canary/xenia-canary/tree/b083312b8b18e07e6e410b82104191f126722794
https://github.com/slimshadykor-cmd/korean-patches/tree/development/onechanbara-direct-dxgi-v1.7/development/onechanbara-direct-dxgi
'''
(release/'먼저읽기.txt').write_text(readme,encoding='utf-8-sig')
(release/'SHA256SUMS.txt').write_text(sha(exe)+'  '+exe.name+'\n'+meta['exe_sha256']+'  [내장] xenia_onechanbara.exe\n',encoding='utf-8-sig')
target=release/'Onechanbara_Korean_DirectDXGI_v1.7.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in [exe,release/'먼저읽기.txt',release/'SHA256SUMS.txt']:z.write(p,p.name)
 for p in runtime.iterdir():
  if p.name.endswith('LICENSE.txt') or p.name=='build.json':z.write(p,'licenses/'+p.name)
 for name in ['install-validation.json','shipping-validation.json']:
  p=R/name
  assert p.is_file(), 'Missing validation: '+name
  z.write(p,'validation/'+name)
 for name in ['copy-protocol-validation.json','metrics-validation.json','pacing-validation.json','revision-notes.txt']:
  z.write(R.parent/'non_nv/regression_204149'/name,'validation/'+name)
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print(json.dumps({'path':str(target),'bytes':target.stat().st_size,'sha256':sha(target),'native_gpu_test':False},indent=2))
