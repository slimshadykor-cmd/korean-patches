from pathlib import Path
import json,zipfile,hashlib,shutil
R=Path(__file__).resolve().parent;D=R/'deliverables';B=R/'publication/release-build/onechanbara-v1.2.9';B.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
readme='''오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.2.9
한글화 슬림쉐이디

[v1.2.9 변경 내용]
기존 한글화와 10/19 대사 수정, 여신상·팔찌 판별 수정을 모두 포함한 정식 누적 패치입니다.
파일 읽기 단계 사이의 불필요한 대기를 줄이는 로딩 개선을 통합했습니다.
별도 로딩 시험 패치를 추가로 적용할 필요는 없습니다.
게임 메인 화면 왼쪽 하단에서 v1.2.9를 확인할 수 있습니다.

로딩 개선본의 사용자 플레이 확인에서는 약 1분 걸리던 구간이 약 30~35초로 줄었다는 결과가 있었습니다.
이는 한 환경에서의 체감 측정이며, PC·제니아 버전·장소에 따라 차이가 있습니다.
전투 속도, 프레임 제한, 게임 내 제한시간 설정은 변경하지 않습니다.

[준비물]
- 일본판 원본 ISO 또는 정식 v1.2.2~v1.2.8 한글판 ISO
- 지원 한글판에 여신상 수정 1(GoddessFix1)을 적용한 ISO도 지원
- Loading Test01을 적용한 일본판 원본/10월 19일 수정 v1.2.8 ISO도 지원
- Windows 64비트, .NET Framework 4.8
- 새 ISO를 저장할 여유 공간과 약 500MB의 임시 공간

[적용 방법]
1. 제니아에서 게임을 종료하고 이 ZIP을 원하는 폴더에 풉니다.
2. Onechanbara_ISO_Korean_v1.2.9.exe를 실행합니다.
3. ISO 선택 버튼을 누르고 원본 또는 지원되는 기존 ISO를 선택합니다.
4. 새 ISO의 저장 위치와 이름을 지정합니다.
5. 완료 후 Xenia에서 새로 생성된 ISO를 직접 불러옵니다.

게임 ISO 자체를 압축 해제할 필요는 없습니다.
입력 ISO는 보존되며 새 ISO가 생성됩니다. 기존 파일에는 덮어쓰지 않습니다.
이전 패치를 순서대로 적용할 필요 없이 이번 패치를 한 번 적용하면 됩니다.
게임이나 Xenia를 자동 실행하지 않으며, 별도 실행기나 외부 자막 도구는 필요하지 않습니다.

[포함 내용]
장소명·모드명, 대사와 화자 이름, 메뉴·미션 안내, 꾸미기 설명 및 뷰 모드,
영상 자막, 엔딩 첫 화면, 대사 출력 및 열쇠 사용 확인 문구 수정을 포함합니다.
간단한 영어 표기와 배경 간판·장식 글씨, 제작진 실명은 원문을 유지합니다.

[검수 범위]
미션 86개, 대사 411구간, 실행 파일 문구 1,053곳, 메뉴 문구 1,423곳,
장소명 96개와 내부 식별값 142개를 자료 및 코드 수준에서 다시 검사했습니다.
이번 검사 범위에서 새로 확인된 한글 오류는 없었습니다.
로딩 처리 192개 조건과 아이템·오브젝트·장소 판별 함수를 검사했습니다.
원본 및 지원 한글판 자료로 구성한 ISO 구조에서 적용 결과와 입력 보존을 확인했습니다.
이는 제니아에서 전 미션을 직접 플레이한 검수를 의미하지 않습니다.

[원본 ISO 기준 해시]
MD5: a1c8c272378c3ac0bae34c61ff0fc0aa
SHA-1: 13cfb703350719c4e22cfd83100d100e94cb661f
패치 전 일본판 원본 ISO 기준입니다. 패치 후 생성된 ISO의 값은 달라집니다.

게임 ISO, Xenia, 세이브 파일, 트레이너 및 테스트용 도구는 포함하지 않습니다.

최신 안내: https://github.com/slimshadykor-cmd/korean-patches/tree/main/xbox360/onechanbara
'''
hashes='일본판 원본 ISO 기준 해시\n\nMD5: a1c8c272378c3ac0bae34c61ff0fc0aa\nSHA-1: 13cfb703350719c4e22cfd83100d100e94cb661f\n\n패치 전 원본 ISO 기준입니다. 패치 ZIP이나 패치 후 ISO의 해시가 아닙니다.\n'
for name,s in [('먼저읽기.txt',readme),('원본ISO_해시.txt',hashes)]:
 (D/name).write_bytes(s.replace('\n','\r\n').encode('utf-8-sig'));shutil.copyfile(D/name,B/name)
public=['Onechanbara_ISO_Korean_v1.2.9.exe','먼저읽기.txt','원본ISO_해시.txt'];release=D/'Onechanbara_ISO_Korean_v1.2.9_Release.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in public:
  inf=zipfile.ZipInfo(name,date_time=(2026,10,21,0,0,0));inf.compress_type=zipfile.ZIP_DEFLATED;inf.external_attr=0o644<<16;z.writestr(inf,(D/name).read_bytes(),compresslevel=6)
with zipfile.ZipFile(release) as z:assert z.testzip() is None and z.namelist()==public
meta={'version':'1.2.9','release_bytes':release.stat().st_size,'release_sha256':sha(release.read_bytes()),'exe_sha256':sha((D/public[0]).read_bytes()),'release_files':public,'test_and_trainer_assets_excluded':True,'actual_xenia_gameplay_tested_by_assistant':False}
(R/'audit/release_validation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
notes='''# 오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.2.9

한글화: **슬림쉐이디**

## 이번 변경

- 로딩 개선을 기존 한글패치에 통합했습니다. 파일 읽기 단계 사이의 불필요한 대기를 줄였습니다.
- 게임 속도, 프레임 제한, 게임 내 제한시간 설정은 유지합니다.
- 기존 한글화, 10/19 대사 수정, 여신상·팔찌 판별 수정을 모두 포함합니다.
- 메인 화면 왼쪽 하단의 버전은 **v1.2.9**입니다.

로딩 개선본의 사용자 플레이 확인에서는 **약 1분 → 약 30~35초**로 줄었다는 결과가 있었습니다. 한 환경에서의 체감 측정이며, PC·제니아 버전·장소에 따라 효과는 달라집니다.

## 다운로드

[**Onechanbara_ISO_Korean_v1.2.9_Release.zip 받기**](https://github.com/slimshadykor-cmd/korean-patches/releases/download/onechanbara-v1.2.9/Onechanbara_ISO_Korean_v1.2.9_Release.zip)

ZIP에는 패치 EXE, 사용 안내문, 원본 ISO 해시 안내만 들어 있습니다. 게임 ISO·Xenia·세이브·트레이너·테스트 도구는 포함하지 않습니다.

## 적용 방법

1. 제니아에서 게임을 종료하고 배포 ZIP을 풉니다.
2. `Onechanbara_ISO_Korean_v1.2.9.exe`를 실행합니다.
3. 일본판 원본 ISO 또는 지원되는 기존 한글판 ISO를 선택합니다.
4. 새 ISO의 저장 위치를 지정하고 완료를 기다립니다.
5. Xenia에서 새로 만들어진 ISO를 직접 불러옵니다.

게임 ISO 자체를 압축 해제할 필요는 없습니다. 입력 ISO를 보존하고 새 파일을 만듭니다. 이전 패치를 순서대로 적용하거나 별도 로딩 패치를 더 적용할 필요가 없습니다.

지원 입력은 일본판 원본, 정식 v1.2.2~v1.2.8 한글판 및 해당 한글판의 GoddessFix1 적용판입니다. Loading Test01을 적용한 일본판 원본/10월 19일 수정 v1.2.8도 지원합니다. Windows 64비트와 .NET Framework 4.8, 새 ISO를 저장할 공간 및 약 500MB의 임시 공간이 필요합니다.

## 검사 결과

미션 86개, 대사 411구간, 실행 파일 문구 1,053곳, 메뉴 문구 1,423곳, 장소명 96개와 내부 식별값 142개를 재검사했습니다. 이번 자료·코드 검사 범위에서 새 한글 오류는 발견되지 않았습니다. 로딩 처리 192개 조건과 아이템·오브젝트·장소 판별 함수, 원본/기존 한글판 자료를 사용한 ISO 적용 결과도 검사했습니다.

로딩 코드는 사용자가 플레이로 개선을 확인한 시험판과 동일합니다. 이 통합판으로 제니아에서 전 미션을 직접 플레이한 검수는 완료하지 않았습니다.

## 원본 ISO 기준 해시

| 항목 | 값 |
| --- | --- |
| MD5 | `a1c8c272378c3ac0bae34c61ff0fc0aa` |
| SHA-1 | `13cfb703350719c4e22cfd83100d100e94cb661f` |

패치 전 일본판 원본 ISO의 기준값입니다. 간단한 영어 표기, 배경 간판·장식 글씨와 제작진 실명은 원문을 유지합니다.
'''
(B/'release-notes.md').write_text(notes)
landing='[← Xbox 360 한글패치 목록](../README.md)\n\n'+notes+'\n[이전 v1.2.8 배포본](https://github.com/slimshadykor-cmd/korean-patches/releases/tag/onechanbara-v1.2.8)\n'
(R/'publication/onechanbara-README.md').write_text(landing)
forum='''[Xbox 360] 오네찬바라 볼텍스 한글패치 v1.2.9 — 로딩 개선 통합

오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.2.9를 배포합니다.

이번 버전은 기존 한글화와 대사·여신상·팔찌 수정에 로딩 개선을 통합한 누적 패치입니다. 테스트한 환경에서는 약 1분 걸리던 구간이 약 30~35초로 줄었습니다. 체감 측정이며 PC와 제니아 버전, 장소에 따라 차이는 있습니다.

게임 속도와 제한시간 설정은 유지하며, 미션 안내·대사·장소명과 내부 아이템·오브젝트 판별도 다시 점검했습니다.

일본판 원본이나 지원되는 기존 한글판 ISO에 이번 패치를 한 번 적용하시면 됩니다. 로딩 시험판을 적용하신 분도 업데이트할 수 있습니다. 배포 ZIP의 EXE에서 ISO를 선택하면 원본을 보존하고 새 ISO를 만듭니다. 게임 ISO를 압축 해제할 필요는 없습니다. 완료 후 제니아에서 새 ISO를 직접 불러 주세요.

메인 화면 왼쪽 하단에서 v1.2.9를 확인하실 수 있습니다.

다운로드 및 적용 안내:
https://github.com/slimshadykor-cmd/korean-patches/tree/main/xbox360/onechanbara

일본판 원본 ISO 기준 해시
MD5: a1c8c272378c3ac0bae34c61ff0fc0aa
SHA-1: 13cfb703350719c4e22cfd83100d100e94cb661f

플레이 중 문제가 발견되면 미션·장소·상황과 사용 중인 제니아 버전을 함께 알려 주세요.
'''
(D/'Onechanbara_v1.2.9_Forum_Post.txt').write_text(forum)
print(meta,flush=True)
