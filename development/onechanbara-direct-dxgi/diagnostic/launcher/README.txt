오네찬바라 v1.7 출력 경로 비교용 · diagnostic-output-1

Onechanbara_Diagnostics.exe는 .NET Framework 4.8 / Windows x64 비교 실행기입니다.
안정화가 완료된 배포 패치가 아닙니다. 이 실행기는 NVIDIA 프로필/API/레지스트리를 쓰지 않습니다.
원본 EXE·설정·바로가기·캐시·ISO는 읽기만 합니다. 기존 content 저장 위치는 게임이 그대로 사용합니다.
게임의 일반적인 세이브 기록은 기존 위치에 저장됩니다.

배치:
  Onechanbara_Diagnostics.exe
  runtime/xenia_onechanbara.exe
  runtime/build.json (display_revision=diagnostic-output-1, exe_sha256 필수)
압축을 푼 폴더에서 Onechanbara_Diagnostics.exe를 바로 실행할 수 있습니다.
개발용 launcher/하위 배치도 지원하며, 실행기 옆 runtime이 없을 때 상위 runtime을 사용합니다.

기존 install.json은 실행기 폴더/상위/각 상위의 config/OnechanbaraDirect에서 자동 검색합니다.
기존 바탕화면 오네찬바라 바로가기도 읽기만 하여 대상/작업 폴더를 검색합니다. 바로가기는 저장하거나 변경하지 않습니다.
찾지 못하면 실행기에서 기존 전용 install.json 한 파일을 선택할 수 있습니다.
실행 시 관리자 요청이나 PowerShell을 호출하지 않습니다. build.ps1은 개발 빌드용이며 실행에 필요하지 않습니다.

세 모드의 공통값: Vulkan FSI, strict, 내부 2×2, time_scalar=1, vsync=true.
즉시 출력·메일박스·relaxed FIFO 허용값은 세 모드 모두 false입니다.
1: DirectDXGI + 게임 출력 스레드 허용
2: DirectDXGI + 원래 UI 스레드 정책
3: 기존 Vulkan FIFO + 원래 UI 스레드 정책
DirectDXGI에는 UI 출력 대기 16ms / 게임 출력 대기 250ms 차이도 있어 단순 스레드 위치만의 비교는 아닙니다.
기존 Vulkan 경로의 vkAcquireNextImageKHR는 UINT64_MAX 대기를 사용하므로 같은 제한 시간 비교가 아닙니다.

원본 캐시는 처음 한 번 읽어서 검증된 비교용 seed를 만듭니다. 각 모드 첫 실행 때 seed에서 복사합니다.
그 후 각 모드는 자기 캐시를 재사용하며 runmeta의 CacheWasReused와 seed 생성 시각으로 구분합니다.
세 모드를 재실행하면 완전히 동일한 warm cache 상태라는 뜻은 아닙니다.
실행별 설정·로그·종료 코드·해시·모드·캐시 정보를 sessions의 고유 폴더 및 ZIP으로 보관합니다.
같은 실행기 창에서 마친 모든 모드 기록은 results/비교결과_시각_GUID.zip 한 파일로도 자동 묶습니다.
각 실행 종료 후 합본을 새 파일로 만들며 결과 폴더 열기는 가장 최근 합본을 가리킵니다.
ZIP은 자동 업로드하지 않으며 게임 ISO·세이브·캐시는 ZIP에 넣지 않습니다.
게임 종료 요청은 CloseMainWindow만 사용합니다. 강제 종료하지 않습니다.

런타임 SHA256은 배포된 build.json과 비교합니다. 이는 패키지 내부 일치 검사이며 서명 검증은 아닙니다.
ISO는 설치 기록의 크기·수정 시각 및 읽기 공유 잠금으로 확인합니다. 대용량 ISO를 매번 재해시하지 않습니다.
기록에 게임/사용자 경로가 포함될 수 있으므로 ZIP을 외부로 보낼 때는 내용을 확인할 수 있습니다.
Linux에서 빌드 및 파일/설정/실패 처리 테스트를 수행했으며 실제 Windows GUI와 GPU 출력 검증은 별도입니다.
