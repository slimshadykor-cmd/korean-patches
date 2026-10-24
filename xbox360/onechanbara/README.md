[← Xbox 360 한글패치 목록](../README.md)

# 오네찬바라 볼텍스 ~기혈을 잇는 자들~ 한글패치 v1.3.0

한글화: **슬림쉐이디**

## 이번 변경

- 코스튬 이름 입력 안내·저장 데이터 명칭 4개를 한글화했습니다.
- 도전과제 제목·설명, 활동 상태, 게임 소개 등의 시스템 정보 103항목을 한글화했습니다.
- 기존 한글화와 대사·여신상·팔찌 수정, **v1.2.9 로딩 개선**을 모두 포함합니다.
- 도전과제 ID와 이벤트·오브젝트 식별값, 저장 처리 및 로딩 코드는 유지합니다.

**패치 프로그램과 파일명에서 v1.3.0을 확인해 주세요.** 이번에는 이미지 수정을 제외하여 게임 타이틀 화면에는 **v1.2.9**가 그대로 표시됩니다.

## 다운로드

[**Onechanbara_ISO_Korean_v1.3.0_Release.zip 받기**](https://github.com/slimshadykor-cmd/korean-patches/releases/download/onechanbara-v1.3.0/Onechanbara_ISO_Korean_v1.3.0_Release.zip)

ZIP에는 패치 EXE, 사용 안내문, 원본 ISO 해시 안내만 들어 있습니다.

## 적용 방법

1. 게임을 종료하고 배포 ZIP을 풉니다.
2. `Onechanbara_ISO_Korean_v1.3.0.exe`를 실행합니다.
3. 일본판 원본 또는 지원되는 기존 한글판 ISO를 선택합니다.
4. 새 ISO의 저장 위치와 이름을 지정합니다.
5. 완료 후 지정한 위치의 새 ISO를 Xenia에서 직접 불러옵니다.

게임 ISO 자체를 압축 해제할 필요는 없습니다. 입력 ISO를 보존하고 새 파일을 만듭니다. 이전 패치를 순서대로 적용할 필요 없이 이번 패치를 한 번 적용하면 됩니다.

일본판 원본, 정식 v1.2.2~v1.2.9 한글판, 기존 지원 GoddessFix1·Loading Test01 적용판을 지원합니다. Windows 64비트와 .NET Framework 4.8, 새 ISO 저장 공간 및 약 500MB의 임시 공간이 필요합니다.

## 검사 범위

미번역 107항목을 수정한 뒤 실행 파일에서 재추출해 대조했습니다. 문자열 길이·참조, 도전과제 27개의 연결, 입력·저장 관련 실제 명령을 검사했고, 원본과 v1.2.9 자료로 구성한 ISO 구조에 배포 EXE를 적용하여 158개 대상과 입력 보존을 확인했습니다. 모든 챕터·난이도·특수 상황을 Xenia에서 직접 플레이한 검수는 아닙니다.

도전과제·활동 상태 등 시스템 정보의 표시 지원은 실행 환경에 따라 다릅니다. 이미지·영상과 기존 게임 내 문구는 유지했습니다. 간단한 영어 표기도 유지합니다.

## 원본 ISO 기준 해시

| 항목 | 값 |
| --- | --- |
| MD5 | `a1c8c272378c3ac0bae34c61ff0fc0aa` |
| SHA-1 | `13cfb703350719c4e22cfd83100d100e94cb661f` |

패치 전 일본판 원본 ISO의 기준값입니다. 게임 ISO·Xenia·세이브·트레이너·테스트 도구는 포함하지 않습니다.

[항상 최신 안내](https://github.com/slimshadykor-cmd/korean-patches/tree/main/xbox360/onechanbara) · [이전 v1.2.9 배포](https://github.com/slimshadykor-cmd/korean-patches/releases/tag/onechanbara-v1.2.9)
