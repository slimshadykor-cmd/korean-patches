from pathlib import Path
import json,zipfile,hashlib,shutil
W=Path(__file__).resolve().parent;D=W/'deliverables';B=W/'publication/release-build/onechanbara-v1.2.8';B.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
readme='''오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.2.8
한글화 슬림쉐이디

[2026-10-19 대사 수정본]
기존 v1.2.8과 파일명·버전·다운로드 주소를 유지한 교체본입니다.
이전에 v1.2.8을 받으셨다면 ZIP을 다시 받고, 기존 한글판 ISO에 한 번 적용해 주세요.
대사 21구간의 잘못 표시되는 글자와 어색한 표현을 수정했습니다.
예: "퇴 갖고 싶어서" → "널 갖고 싶어서", "피에 꼬주린" → "피에 굶주린"
누락된 한글 글자 14개를 보완했습니다.
게임 메인 화면의 버전 표시는 v1.2.8로 유지합니다.
패치 프로그램 제목에서 "10/19 대사 수정"을 확인할 수 있습니다.

[기존 v1.2.8 수정]
팔찌를 다른 아이템으로 잘못 분류하던 공통 판별 오류를 수정했습니다.
게임 내부에서 사용하는 팔찌 식별값을 원본으로 복구했습니다.
v1.2.7의 여신상 수정과 이전 한글화가 모두 포함된 누적 패치입니다.
메인 화면에서 v1.2.8을 확인할 수 있습니다.

[준비물]
- 일본판 원본 ISO 또는 정식 v1.2.2~v1.2.8 한글판 ISO
- 위 지원 한글판에 별도 여신상 수정 1(GoddessFix1)을 적용한 ISO도 지원
- Windows 64비트, .NET Framework 4.8
- 새 ISO를 저장할 여유 공간과 약 500MB의 임시 공간

[적용 방법]
1. 제니아에서 게임을 종료하고 이 ZIP을 원하는 폴더에 풉니다.
2. Onechanbara_ISO_Korean_v1.2.8.exe를 실행합니다.
3. ISO 선택 버튼을 누르고 원본 또는 지원되는 기존 한글판 ISO를 선택합니다.
4. 새 ISO의 저장 위치와 이름을 지정합니다.
5. 완료 후 Xenia에서 새로 생성된 ISO를 직접 불러옵니다.

게임 ISO 자체를 압축 해제할 필요는 없습니다.
입력 ISO는 보존되며 새 ISO가 생성됩니다. 기존 파일에는 덮어쓰지 않습니다.
이전 패치를 순서대로 다시 적용할 필요 없이 이번 패치를 한 번 적용하면 됩니다.
게임이나 Xenia를 자동 실행하지 않습니다.

[누적 내용]
장소명·모드명, 대사와 화자 이름, 메뉴·미션 안내, 꾸미기 설명 및 뷰 모드,
영상 자막, 엔딩 첫 화면, 대사 출력 및 열쇠 사용 확인 문구 수정을 포함합니다.
간단한 영어 표기와 배경 간판·장식 글씨, 제작진 실명은 원문을 유지합니다.

[검수 범위]
미션 86개와 공통 아이템·오브젝트 식별값, 표시 문자열을 대조했습니다.
팔찌 오분류를 게임의 실제 판별 명령으로 재현하고 수정 결과를 확인했습니다.
제공된 원본 자료와 이전 한글판 자료로 구성한 ISO 구조에서 패치 결과와 자료 보존을 검사했습니다.
이번 통합판의 제니아 실제 플레이 및 엔딩까지의 통과 검수는 완료하지 않았습니다.

[원본 ISO 기준 해시]
MD5: a1c8c272378c3ac0bae34c61ff0fc0aa
SHA-1: 13cfb703350719c4e22cfd83100d100e94cb661f
위 값은 패치 전 일본판 원본 ISO의 기준값입니다.
패치 적용 후 생성된 ISO는 다른 값을 가집니다.

게임 ISO, Xenia, 세이브 파일, 트레이너 및 테스트용 도구는 포함하지 않습니다.
'''
hashes='일본판 원본 ISO 기준 해시\n\nMD5: a1c8c272378c3ac0bae34c61ff0fc0aa\nSHA-1: 13cfb703350719c4e22cfd83100d100e94cb661f\n\n패치 전 원본 ISO의 기준값입니다. 패치 ZIP이나 패치 후 ISO의 해시가 아닙니다.\n'
for name,t in [('먼저읽기.txt',readme),('원본ISO_해시.txt',hashes)]:
 (D/name).write_bytes(t.replace('\n','\r\n').encode('utf-8-sig'));shutil.copyfile(D/name,B/name)
public=['Onechanbara_ISO_Korean_v1.2.8.exe','먼저읽기.txt','원본ISO_해시.txt'];release=D/'Onechanbara_ISO_Korean_v1.2.8_Release.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in public:
  inf=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));inf.compress_type=zipfile.ZIP_DEFLATED;inf.external_attr=0o644<<16;z.writestr(inf,(D/name).read_bytes(),compresslevel=6)
with zipfile.ZipFile(release) as z:assert z.testzip() is None and z.namelist()==public
notes='''오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.2.8

## 2026-10-19 대사 수정본

기존 v1.2.8의 ZIP 파일명과 다운로드 주소를 유지한 수정본입니다. 이전 v1.2.8 사용자는 ZIP을 다시 받고 기존 한글판 ISO에 한 번 적용해 주세요.

- 대사 21구간의 잘못 표시되는 글자와 어색한 문구를 수정했습니다.
- `퇴 갖고 싶어서` → `널 갖고 싶어서`, `피에 꼬주린` → `피에 굶주린` 등.
- 누락된 한글 글자 14개를 추가하고 기존 글자 776개를 보존했습니다.
- 패치 프로그램 제목에서 `10/19 대사 수정`을 확인할 수 있습니다. 게임 메인 화면의 버전은 v1.2.8로 유지합니다.

## 기존 v1.2.8 변경 사항

- 팔찌를 다른 아이템으로 잘못 분류하던 공통 판별 오류를 수정했습니다.
- v1.2.7의 여신상 수정과 이전 한글화·영상 자막을 모두 포함합니다.
- 메인 화면에서 v1.2.8을 확인할 수 있습니다.

## 다운로드 및 적용

아래 `Onechanbara_ISO_Korean_v1.2.8_Release.zip`을 받으세요. 패치 EXE와 사용 안내문, 원본 ISO 해시 안내가 들어 있습니다.

일본판 원본 ISO 또는 정식 v1.2.2~v1.2.8 한글판 ISO에 적용할 수 있습니다. 지원 한글판에 별도 여신상 수정 1(GoddessFix1)을 적용한 ISO도 지원합니다. Windows 64비트와 .NET Framework 4.8이 필요합니다.

ZIP을 푼 뒤 패치 EXE에서 ISO를 선택하면 새 한글판 ISO를 만듭니다. 게임 ISO를 압축 해제할 필요는 없습니다. 입력 ISO는 보존되며 이전 패치를 순서대로 적용할 필요도 없습니다. 완료 후 Xenia에서 새 ISO를 직접 불러오세요.

## 검수 범위

미션 86개의 안내문 55구간, 이야기 대사 411구간, 실행 파일 표시문 1,053곳, 메뉴 표시문 1,423곳의 글자 대응을 검사했습니다. 대사의 원문을 대조해 확인된 21구간을 수정했습니다. 공통 아이템·오브젝트 식별값은 기존 v1.2.8과 동일합니다. 팔찌 오분류를 게임의 실제 판별 명령으로 재현하고 수정 결과를 확인했습니다. 제공된 원본·기존 한글판 자료를 사용한 ISO 구조에서 패치 결과와 자료 보존을 검사했습니다. 이번 통합판으로 제니아에서 엔딩까지 직접 플레이한 검수는 완료하지 않았습니다.

## 원본 ISO 기준 해시

| 항목 | 값 |
| --- | --- |
| MD5 | `a1c8c272378c3ac0bae34c61ff0fc0aa` |
| SHA-1 | `13cfb703350719c4e22cfd83100d100e94cb661f` |

패치 전 일본판 원본 ISO 기준입니다. 간단한 영어 표기, 배경 간판·장식 글씨와 제작진 실명은 원문을 유지합니다. 게임 ISO, Xenia, 세이브, 트레이너 및 테스트용 도구는 포함하지 않습니다.
'''
(B/'release-notes.md').write_text(notes)
meta={'version':'1.2.8','release_bytes':release.stat().st_size,'release_sha256':sha(release.read_bytes()),'exe_sha256':sha((D/public[0]).read_bytes()),'actual_xenia_gameplay_tested':False,'release_files':public,'test_and_trainer_assets_excluded':True}
(W/'audit/release_validation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(meta,flush=True)
