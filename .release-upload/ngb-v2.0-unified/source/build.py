"""Promote the reported-working menu-memory build without changing game data."""
from pathlib import Path
import ast,base64,copy,gzip,hashlib,json,os,zipfile
R=Path(__file__).resolve().parent
ROOT=R.parent
SRC=ROOT/'deliverables/NGB_Korean_Patch_v2.0_hakuX.zip'
OUT=R/'NGB_Korean_Patch_v2.0.zip'
PRE='NGB_Korean_Patch_v2.0_hakuX/';POST='NGB_Korean_Patch_v2.0/'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(SRC.read_bytes())=='c168b1a891823ac29bfc247a249fdf596f7d8c1607c8f721147c315e0f33a062'
CONFIRMATION={'date':'2026-10-25','source':'User relayed the hakuX reporter feedback in this conversation','emulator':'hakuX 1.1.0','scope':'New Game works and progression through Chapter 1 reported normal','mode':'not specified','save_and_reload_separately_confirmed':False,'all_chapters_confirmed':False,'xemu_confirmation_of_this_menu_change':False}
NOTE='2026-10-25 / v2.0 추가 갱신: 모드·의상 선택 화면의 메모리 사용 개선을 공용판에 통합. 그림·번역·전투·저장 기능 유지. 제보자가 hakuX에서 새 게임 및 1장까지 정상 진행 확인. 별도 하쿠X 다운로드를 공용 v2.0 하나로 통합.'
README='''닌자가이덴 블랙 한글패치 v2.0 폭풍
한글화·제작: 슬림쉐이디
2026.10.25 선택 화면 메모리 개선 통합본

[설치]
1. ZIP 전체를 새 폴더에 압축 해제합니다.
2. NGB_Korean_Patch.exe를 실행합니다.
3. 지원하는 원본 또는 기존 한글 ISO/XISO를 선택합니다.
4. [새 한글 XISO 만들기] 버튼을 누릅니다.
5. 에뮬레이터를 완전히 종료한 뒤 새 NGB_Korean_v2.0.xiso.iso로 부팅합니다.
   같은 이름이 이미 있으면 숫자가 붙습니다. 입력 ISO는 유지합니다.
   이전 실행 상태 스냅샷 대신 게임 내 세이브를 사용하세요.

Windows 10/11 64비트용이며 Python 별도 설치는 필요 없습니다.
일반 ISO와 XISO를 자동 판별합니다. 이전 패치를 순서대로 설치할 필요 없습니다.
지원되는 기존 v2.0 및 앞서 배포한 하쿠X 수정본에도 적용할 수 있습니다.
기존 게임 내 세이브를 유지합니다. HDD 교체·삭제나 별도 세이브 패치는 필요 없습니다.

[이번 갱신]
새 게임에서 모드·의상을 고를 때 필요한 그림만 준비하도록 개선했습니다.
기존 약 972KiB 할당을 모드 선택 520KiB, 의상 선택 392KiB로 나눕니다.
기존 그림 데이터·화면 배치·번역·블랙/폭풍 전투·저장 코드를 유지합니다.
앞서 별도로 배포한 하쿠X 수정본과 같은 게임 실행파일을 공용 v2.0에 통합했습니다.
앞으로는 NGB_Korean_Patch_v2.0.zip 하나를 받으시면 됩니다.

[구동 확인]
제보자가 hakuX에서 새 게임 및 1장까지 정상 진행했다고 확인했습니다.
이번 선택 화면 수정본의 xemu 실제 플레이 확인은 아직 별도로 받지 못했습니다.
코드·그림 데이터·패치 적용·무결성 검사를 실제 기기 플레이와 구분합니다.
전 난이도·전 챕터·모든 환경의 완주 검수를 의미하지 않습니다.

[지원 대상]
Ninja Gaiden Black Japan/Korea (En,Ja)의 지원되는 원본·기존 한글 이미지.
USA/Europe·임의 수정본까지 지원하는 것은 아닙니다.
제작 원본 MD5: 9e09ba06bab10c53b8460f4c43b98b18
제작 원본 SHA-1: 8581d5d0e2f90dcbcb63bd94bcb958a764f6d3a5
ISO/XISO 재포장 시 전체 해시가 달라질 수 있으며 내부 자료로 호환성을 검사합니다.

게임 ISO·BIOS·HDD·세이브·개인용 상시 무적은 포함하지 않습니다.
블랙/폭풍 선택형 기능과 기존 한글화·수정 사항은 포함합니다.

[다운로드·업데이트]
https://github.com/slimshadykor-cmd/korean-patches/releases/tag/ngb-v2.0
버전명과 주소는 v2.0으로 유지하며 수정 날짜와 파일을 갱신합니다.
번역 오류 제보는 기존 v2.0 안내 게시글 댓글 한곳으로 부탁드립니다.
'''
with zipfile.ZipFile(SRC) as z:
 original=json.loads(z.read(PRE+'ngb_native11/assets/build_plan.json'))
 plan=copy.deepcopy(original)
 assert plan['xbe']['output_sha256']=='c04e774df621566c60cbfb929a675ca4f375074205366c16e947bb858b66c97c'
 plan['revision']='v2.0 unified selection-menu memory update 2026-10-25'
 report=plan.pop('hakux_menu_memory_fix')
 plan['selection_menu_memory_update']={'date':'2026-10-25','public_release':True,'candidate_build_evidence':report,'runtime_user_report':CONFIRMATION,'game_executable_unchanged_from_reported_candidate':True}
 for k in ['xbe','boot_repairs','archives','root_patches']:assert plan[k]==original[k],k
 gui=z.read(PRE+'ngb_native11/patch_gui.py').decode()
 gui=gui.replace("VERSION = '2.0 hakuX 확인용'","VERSION = '2.0'").replace('2026.10.25 hakuX 호환 확인용','2026.10.25 선택 화면 메모리 개선').replace('NGB_Korean_v2.0_hakuX','NGB_Korean_v2.0').replace('새 XISO로 hakuX를 실행해 확인하세요.','새 XISO를 에뮬레이터에서 실행하세요.')
 assert 'haku' not in gui.lower() and '확인용' not in gui
 assert "VERSION = '2.0'" in gui and 'NGB_Korean_v2.0.xiso.iso' in gui
 ast.parse(gui)
 launcher=z.read(PRE+'launch_patch.py').decode().replace('NGB Public release v1.8 폭풍 portable launcher','NGB Public release v2.0 폭풍 portable launcher')
 ast.parse(launcher)
 changelog=z.read(PRE+'CHANGELOG_KO.txt').decode().rstrip()+'\n\n'+NOTE+'\n'
 oldvalidation=json.loads(z.read(PRE+'VALIDATION.json'))
 validation={'date':'2026-10-25','release':'2.0','packaging_only_promotion':True,'game_executable_sha256':plan['xbe']['output_sha256'],'all_game_patch_operations_identical_to_candidate':True,'runtime_user_report':CONFIRMATION,'historical_candidate_cpu_evidence':oldvalidation,'package_validation_reused':json.loads((ROOT/'package_candidate_verification.json').read_text()),'scope':'The tested game executable and all patch operations are unchanged. Only distribution names, metadata, launcher log version, and documentation change; existing runtime tests reused.'}
 replacements={'ngb_native11/assets/build_plan.json':json.dumps(plan,ensure_ascii=False,indent=2).encode(),'ngb_native11/patch_gui.py':gui.encode(),'launch_patch.py':launcher.encode(),'README_KO.txt':README.encode('utf-8-sig'),'CHANGELOG_KO.txt':changelog.encode(),'VALIDATION.json':json.dumps(validation,ensure_ascii=False,indent=2).encode()}
 manifest={};changed=[]
 with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as q:
  for i in z.infolist():
   rel=i.filename.removeprefix(PRE)
   if rel=='FILE_HASHES.json':continue
   old=z.read(i);data=replacements.pop(rel,old);info=copy.copy(i);info.filename=POST+rel
   if data!=old:changed.append(rel)
   q.writestr(info,data)
   if not i.is_dir():manifest[rel]=sha(data)
  assert not replacements
  q.writestr(POST+'FILE_HASHES.json',json.dumps(manifest,indent=2))
 with zipfile.ZipFile(OUT) as q:
  assert q.testzip() is None
  for rel,digest in manifest.items():assert sha(q.read(POST+rel))==digest,rel
  assert not any(n.lower().endswith(('.iso','.xbe','.qcow2')) or Path(n).name in ['save000.dat','system.dat'] for n in q.namelist())
  q.extractall(R/'extracted')
receipt={'path':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT.read_bytes()),'xbe_sha256':plan['xbe']['output_sha256'],'manifest_files':len(manifest),'changed_files':changed,'all_game_data_and_patch_operations_unchanged':True,'runtime_user_report':CONFIRMATION}
(R/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
(R/'SHA256SUMS.txt').write_text(receipt['sha256']+'  NGB_Korean_Patch_v2.0.zip\n')
(R/'README_KO.txt').write_text(README)
before=json.loads((R/'release_before.json').read_text())['body']
body=before.split('\n---\n\n<!-- hakux-v20-20261025 -->')[0].rstrip()+'\n'
assert '하쿠X용 패치 v2.0 다운로드' not in body
body=body.replace('2026-10-25 통합본','2026-10-25 선택 화면 메모리 개선 통합본')
body=body.replace('## 이번 수정\n\n','## 이번 수정\n\n- **모드·의상 선택 화면의 메모리 사용 개선을 공용 v2.0에 통합했습니다.** 그림·배치·번역·전투·저장 기능은 그대로 유지합니다.\n- 별도로 배포했던 하쿠X 수정본은 통합했으며, 이제 **NGB_Korean_Patch_v2.0.zip 하나**를 받으시면 됩니다.\n- **제보자가 hakuX에서 새 게임 및 1장까지 정상 진행한 것을 확인했습니다.** 같은 게임 실행파일을 이번 공용판에 반영했습니다.\n')
old='동일한 저장 화면 메모리 수정본에 대해 제작자가 xemu에서 정상 작동을 확인했습니다. v2.0은 해당 전투·저장 코드를 유지하며 시작 화면의 버전 표시와 자원 갱신 표식만 변경했습니다.'
new='이전 공용판의 저장 화면 메모리 수정은 제작자가 xemu에서 확인했습니다. 이번에 통합한 선택 화면 메모리 수정은 **제보자가 hakuX에서 새 게임 및 1장까지 정상 진행했다고 확인**했습니다. 이번 선택 화면 수정본의 xemu 실제 플레이 확인은 아직 별도로 받지 못했으며, 이를 모든 환경·전 챕터의 확인으로 확대하지 않습니다.'
assert old in body;body=body.replace(old,new)
body=body.replace('v2.0에서는 지원 실행파일 9종 변환, 실제 패처의 합성 ISO/XISO 6가지 적용·재적용, 2,724개 파일 해시와 ZIP 무결성을 검사했습니다.','이번 선택 화면 수정에서는 입력 16가지, 그림·배치 대조 52가지, 자원 해제·재시도·반복 전환, 지원 실행파일 10종 변환과 실제 패처의 합성 ISO/XISO 8가지 적용·재적용을 검사했습니다. 공용 통합 과정에서는 동일 실행파일·패치 처리의 기존 검사 결과를 재사용하고, 2,724개 파일 해시와 ZIP 무결성을 확인했습니다.')
body=body.replace('4. xemu를 완전히 종료하고 새 **NGB_Korean_v2.0.xiso.iso**로 부팅합니다.','4. 사용 중인 에뮬레이터를 완전히 종료하고 새 **NGB_Korean_v2.0.xiso.iso**로 부팅합니다.')
body=body.replace('배포 ZIP: **63,075,742바이트**',f"배포 ZIP: **{receipt['bytes']:,}바이트**")
body=body.replace('9d272fc640eb560289150bd6ab44f8d1d8499ccacef6c449e06839b798677ab4',receipt['sha256'])
end='앞으로 버전명은 v2.0으로 유지하며 같은 릴리스에서 파일·수정 날짜를 갱신합니다.'
assert body.count(end)==1;body=body.replace(end,NOTE+'\n\n'+end)
assert '_hakuX.zip' not in body and '호환 확인용' not in body
(R/'RELEASE_NOTES.md').write_text(body)
print(json.dumps(receipt,ensure_ascii=False,indent=2))
