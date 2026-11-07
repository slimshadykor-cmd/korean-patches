# 오네찬바라 볼텍스 일본판 한글패치 v1.7

**한글화 슬림쉐이디**

기존 일반 Xenia 프로필과 원래 `content` 위치의 세이브·의상·DLC를 직접 사용하는 통합판입니다. 전용 그래픽 설정·캐시·로그는 `config/Onechanbara`에서 관리합니다. 메인 화면·패처·출력 ISO·배포 ZIP의 버전 표기를 **v1.7**로 맞췄습니다.

**[v1.7 통합 패치 ZIP](https://github.com/slimshadykor-cmd/korean-patches/releases/download/onechanbara-v1.4.0/Onechanbara_Korean_v1.7.zip)** · [배포 페이지](https://github.com/slimshadykor-cmd/korean-patches/releases/tag/onechanbara-v1.4.0)

기존 링크를 위해 릴리스 태그 `onechanbara-v1.4.0`을 유지합니다. 실제 배포 버전은 **v1.7**입니다.

## 설치

1. Xenia를 종료하고 ZIP 전체를 새 폴더에 풉니다.
2. **Onechanbara_Korean_v1.7.exe**를 실행해 **한글패치 적용 — 새 ISO 만들기**를 선택합니다.
3. 일본판 원본 또는 지원하는 기존 한글 ISO를 입력으로 선택하고 새 ISO를 저장합니다. 메인 화면의 버전 표시도 새 ISO에서 반영됩니다.
4. 기존 `xenia_canary.exe`를 선택해 실행 연결을 완료하고 바탕화면의 **오네찬바라** 아야 아이콘으로 실행합니다.

이미 v1.7 ISO가 있고 실행 연결만 갱신하려면 **기존 v1.7 ISO — 기존 프로필 사용·바탕화면 바로가기** 버튼을 사용하세요. 이전 전용 폴더에만 있는 세이브·DLC는 자동 이전 대상에서 제외됩니다. 세부 경로와 실행 조건은 ZIP의 **먼저읽기.txt**를 참고하세요.

## 변경과 검증

- 기존 한글화·영상 자막·로딩 개선과 전용 Vulkan/FSI·2x2·VSync 구성을 이어받았습니다.
- 기존 일반 프로필을 사용하도록 실행 연결을 변경하고, 같은 Windows 경로의 슬래시 표기 차이로 발생하던 오류를 수정했습니다.
- 프로필과 설정 보호 자동 검사 26개, 배포 EXE의 ISO 변환, 메인 화면 이미지와 내장 데이터 검사를 통과했습니다. **Windows UI 및 실제 게임 플레이는 미검증**입니다. ZIP의 **검수결과.txt**에 범위를 기록했습니다.

ZIP 크기 **319,350,856바이트**

SHA-256 `bc003bb63403c8e92da32da8c034255287190fd708a5fdbe391a70c30346e734`
