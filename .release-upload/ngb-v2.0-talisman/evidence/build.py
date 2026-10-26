"""Promote the user-confirmed talisman patch; keep its game output identical."""
from pathlib import Path
import ast, copy, hashlib, json, os, zipfile

R = Path(__file__).resolve().parent
W = R.parent
SRC = W/'deliverables/NGB_v2.0_Talisman_Equip_Test1.zip'
OUT = R/'NGB_Korean_Patch_v2.0.zip'
PRE = 'NGB_v2.0_Talisman_Equip_Test1/'
POST = 'NGB_Korean_Patch_v2.0/'
sha = lambda b:hashlib.sha256(b).hexdigest()
assert sha(SRC.read_bytes()) == '5aba66019452bcfbe5e721003635364553285cae9f383caada362ea436280719'
TARGET = '1ed80090b4b2872dbd1d896ae7571eaa0ff660672f09c5dbbe2d1745ec1d8b88'
assert sha((W/'candidate.xbe').read_bytes()) == TARGET
REPORT = {'date':'2026-10-26','source':'User confirmation in this conversation','statement':'아까 테스트한 수정본이 잘되는 것을 확인했고 공용 v2.0 교체를 요청함','scope':'Talisman equipment candidate reported working; individual test cases and emulator version were not specified','all_chapters_confirmed':False}
NOTE = '2026-10-26 / v2.0 갱신: 폭풍 모드의 부활 부적을 게임 내 아이템 메뉴에서 A 버튼으로 장착·해제할 수 있도록 개선. 상태·버튼 그림 표시 및 게임 저장을 통한 설정 유지. 제작자 테스트 확인 후 동일 수정본을 정식 공용 패치에 반영.'
README = '''닌자가이덴 블랙 한글패치 v2.0 폭풍
한글화·제작: 슬림쉐이디
2026.10.26 부활 부적 장착·해제 개선

[설치]
1. ZIP 전체를 새 폴더에 압축 해제합니다.
2. NGB_Korean_Patch.exe를 실행합니다.
3. 지원하는 원본 또는 기존 한글 ISO/XISO를 선택합니다.
4. [새 한글 XISO 만들기] 버튼을 누릅니다.
5. 에뮬레이터를 완전히 종료한 뒤 새 NGB_Korean_v2.0.xiso.iso로 부팅합니다.
   같은 출력 이름이 이미 있으면 숫자가 붙습니다. 입력 ISO는 유지합니다.
   이전 실행 상태 스냅샷 대신 게임 내 세이브를 사용하세요.

Windows 10/11 64비트용이며 Python 별도 설치는 필요 없습니다.
일반 ISO와 XISO를 자동 판별합니다. 이전 패치를 순서대로 설치할 필요 없습니다.
지원되는 기존 v2.0 및 부활 부적 확인용 수정본에도 적용할 수 있습니다.
기존 게임 내 세이브를 유지합니다. HDD 교체·삭제나 별도 세이브 패치는 필요 없습니다.

[이번 갱신 — 폭풍 모드의 부활 부적]
부활 부적을 가진 상태에서 게임 내 아이템 메뉴를 열고 부활 부적을 선택합니다.
오른쪽 아래에 현재 상태와 A 버튼 그림이 표시됩니다.
  장착 중 → A 버튼으로 해제
  해제 중 → A 버튼으로 장착
장착하면 원래 조건에서 자동 부활하며, 해제하면 소지하고 있어도 자동 사용하지 않습니다.
장착·해제 조작만으로 부적 수량은 줄어들지 않습니다.
변경한 상태를 유지하려면 게임을 저장하세요.
새 게임 시작 전 자동 사용 선택은 최초 설정이며, 플레이 중 다시 바꿀 수 있습니다.
블랙 모드는 원래 자동 사용 방식을 유지합니다.

[확인 및 기존 기능]
제작자가 이번 부활 부적 수정본을 테스트하여 정상 작동을 확인했습니다.
정식판의 게임 코드는 확인한 수정본과 동일합니다.
메뉴·부활 처리와 저장·읽기 코드를 CPU 검사하고, 패치 적용과 ZIP 무결성을 확인했습니다.
CPU 검사의 OS 파일·화면 처리는 시험용 대체이며, 전 환경·전 챕터 완주 확인을 뜻하지 않습니다.
기존 한글화, 블랙/폭풍 선택, 저장 관련 수정과 선택 화면 메모리 개선을 함께 포함합니다.
카메라 설정 관련 추가 변경은 이번 갱신에 포함하지 않았습니다.

[지원 대상]
Ninja Gaiden Black Japan/Korea (En,Ja)의 지원되는 원본·기존 한글 이미지.
USA/Europe·임의 수정본까지 지원하는 것은 아닙니다.
제작 원본 MD5: 9e09ba06bab10c53b8460f4c43b98b18
제작 원본 SHA-1: 8581d5d0e2f90dcbcb63bd94bcb958a764f6d3a5
ISO/XISO 재포장 시 전체 해시가 달라질 수 있으며 내부 자료로 호환성을 검사합니다.

공용 패치에는 게임 ISO·BIOS·HDD·세이브·개인용 상시 무적을 포함하지 않습니다.
에뮬레이터 버전과 설정·환경에 따라 동작이 달라질 수 있습니다.

[다운로드·업데이트]
https://github.com/slimshadykor-cmd/korean-patches/releases/tag/ngb-v2.0
버전명과 주소는 v2.0으로 유지하며 수정 날짜와 파일을 갱신합니다.
번역 오류 제보는 기존 v2.0 안내 게시글 댓글 한곳으로 부탁드립니다.
'''
with zipfile.ZipFile(SRC) as z:
    original = json.loads(z.read(PRE+'ngb_native11/assets/build_plan.json'))
    plan = copy.deepcopy(original)
    assert plan['xbe']['output_sha256'] == TARGET
    evidence = plan.pop('talisman_equipment_test')
    plan['revision'] = 'v2.0 talisman equipment update 2026-10-26'
    plan['talisman_equipment_update'] = {'date':'2026-10-26','public_release':True,'candidate_build_evidence':evidence,'runtime_user_report':REPORT,'game_executable_unchanged_from_confirmed_candidate':True}
    plan['validation_scope'] = 'User confirmed the talisman candidate works. Native CPU and package evidence retained. Full game/environment verification is not claimed.'
    for repair in plan['boot_repairs']:
        if repair.get('reason') == 'Storm talisman equipment toggle, private test 1.':
            repair['reason'] = 'Storm talisman equipment toggle, public v2.0 update 2026-10-26.'
    for k in ['xbe','archives','root_patches']:
        assert plan[k] == original[k]
    assert [(v['previous_xbe_sha256'],v['changes']) for v in plan['boot_repairs']] == [(v['previous_xbe_sha256'],v['changes']) for v in original['boot_repairs']]
    gui = z.read(PRE+'ngb_native11/patch_gui.py').decode()
    gui = gui.replace("VERSION = '2.0 부활 부적 확인용 1'", "VERSION = '2.0'")
    gui = gui.replace('부활 부적 장착·해제 확인용','부활 부적 장착·해제 개선')
    gui = gui.replace('NGB_Korean_v2.0_Talisman_Test1','NGB_Korean_v2.0')
    assert 'Test1' not in gui and '확인용' not in gui and "VERSION = '2.0'" in gui
    ast.parse(gui)
    changelog = z.read(PRE+'CHANGELOG_KO.txt').decode('utf-8-sig').rstrip()+'\n\n'+NOTE+'\n'
    validation = {'date':'2026-10-26','release':'2.0','packaging_only_promotion':True,'game_executable_sha256':TARGET,'all_game_patch_operations_identical_to_confirmed_candidate':True,'runtime_user_report':REPORT,'historical_candidate_cpu_evidence':json.loads(z.read(PRE+'VALIDATION.json')),'candidate_package_verification':json.loads((W/'package_verification.json').read_text())}
    replacements = {'ngb_native11/assets/build_plan.json':json.dumps(plan,ensure_ascii=False,indent=2).encode(),'ngb_native11/patch_gui.py':gui.encode(),'README_KO.txt':README.encode('utf-8-sig'),'CHANGELOG_KO.txt':changelog.encode(),'VALIDATION.json':json.dumps(validation,ensure_ascii=False,indent=2).encode()}
    manifest = {}; changed = []
    with zipfile.ZipFile(OUT.with_suffix('.partial'),'w',zipfile.ZIP_DEFLATED,compresslevel=6) as q:
        for info in z.infolist():
            rel = info.filename.removeprefix(PRE)
            if rel == 'FILE_HASHES.json':continue
            old = z.read(info); data = replacements.pop(rel,old)
            ni = copy.copy(info); ni.filename = POST+rel
            q.writestr(ni,data)
            if data != old:changed.append(rel)
            if not info.is_dir():manifest[rel] = sha(data)
        assert not replacements
        q.writestr(POST+'FILE_HASHES.json',json.dumps(manifest,indent=2))
    os.replace(OUT.with_suffix('.partial'),OUT)
    with zipfile.ZipFile(OUT) as q:
        assert q.testzip() is None
        for rel,h in manifest.items():assert sha(q.read(POST+rel)) == h,rel
        assert not any(n.lower().endswith(('.iso','.xbe','.qcow2')) or Path(n).name.lower() in ['save000.dat','system.dat'] for n in q.namelist())
        assert not any('Talisman_Test1' in n or 'Equip_Test1' in n for n in q.namelist())
        q.extractall(R/'extracted')
receipt = {'path':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT.read_bytes()),'xbe_sha256':TARGET,'manifest_files':len(manifest),'changed_files':changed,'all_game_data_and_patch_operations_unchanged_from_confirmed_candidate':True,'runtime_user_report':REPORT}
(R/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
(R/'SHA256SUMS.txt').write_text(receipt['sha256']+'  '+OUT.name+'\n')
(R/'README_KO.txt').write_text(README,encoding='utf-8-sig')
before = json.loads((R/'release_before.json').read_text())
body = before['body']
body = body.replace('2026-10-25 선택 화면 메모리 개선 통합본','2026-10-26 부활 부적 장착·해제 개선')
addition = '''## 2026-10-26 추가 수정

- **폭풍 모드에서 부활 부적을 게임 중 장착·해제할 수 있습니다.** 아이템 메뉴에서 부활 부적을 선택하고 **A 버튼**을 누르세요. 상태와 패드 버튼 그림이 함께 표시됩니다.
- 시작할 때 자동 사용을 껐더라도 게임 중 다시 켤 수 있습니다. 장착·해제만으로 부적은 소모되지 않으며, **변경 후 게임을 저장하면 해당 세이브에 설정이 유지됩니다.**
- 블랙 모드는 기존 자동 사용 방식을 유지합니다. 기존 한글화·저장 수정·선택 화면 메모리 개선도 포함합니다.
- 제작자가 이번 수정본을 테스트하여 정상 작동을 확인한 뒤, **동일한 게임 코드를 정식 공용 패치로 반영**했습니다. 파일명·버전·다운로드 주소는 기존 v2.0 그대로입니다.

'''
body = body.replace('## 이번 수정\n\n',addition+'## 기존 v2.0 주요 수정\n\n',1)
body = body.replace('## 확인 범위\n\n','## 확인 범위\n\n이번 부활 부적 수정본은 제작자가 정상 작동을 확인했습니다. 정식판은 확인한 수정본과 동일한 게임 코드를 사용하며, 배포용 표시와 안내문을 정리했습니다. 메뉴·부활 처리, 블랙/폭풍 교차 저장을 포함한 네이티브 CPU 검사와 지원 실행파일 11종·합성 ISO/XISO 10가지 패치 적용 검사를 통과했습니다. 실제 플레이 확인 범위를 모든 난이도·챕터·환경으로 확대하지 않습니다.\n\n',1)
body = body.replace('이번 선택 화면 수정본의 xemu 실제 플레이 확인은 아직 별도로 받지 못했으며, 이를 모든 환경·전 챕터의 확인으로 확대하지 않습니다.','당시 선택 화면 수정은 hakuX 제보 범위로 기록했으며, 이를 모든 환경·전 챕터의 확인으로 확대하지 않습니다.')
old_asset = next(a for a in before['assets'] if a['name']==OUT.name)
body = body.replace(f"배포 ZIP: **{old_asset['size']:,}바이트**",f"배포 ZIP: **{receipt['bytes']:,}바이트**").replace(old_asset['digest'].removeprefix('sha256:'),receipt['sha256'])
tail = '앞으로 버전명은 v2.0으로 유지하며 같은 릴리스에서 파일·수정 날짜를 갱신합니다.'
assert body.count(tail) == 1
body = body.replace(tail,NOTE+'\n\n'+tail)
(R/'RELEASE_NOTES.md').write_text(body)
(R/'CHANGELOG_KO.txt').write_text(body.split('## 날짜별 누적 변경 요약\n\n',1)[1])
print(json.dumps(receipt,ensure_ascii=False,indent=2))
