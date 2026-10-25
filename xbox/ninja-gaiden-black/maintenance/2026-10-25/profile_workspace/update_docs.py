from pathlib import Path
import json
R=Path('publish_settings');O=R/'upload';r=json.loads((R/'receipt.json').read_text())
header='''## 2026년 10월 25일 — v1.8 설정 불러오기 경고 수정

- 저장 후 게임을 다시 실행할 때 나타나던 **설정 불러오기 경고**에 대응해, 설정을 읽는 작업 메모리 처리를 수정했습니다.
- 같은 슬롯에 **폭풍 → 블랙 / 블랙 → 폭풍**으로 바꾸어 저장하는 경우와 연속 덮어쓰기의 저장·복원을 코드 실행으로 검사했습니다.
- 이번 수정본은 **사용자 xemu 실행에서 정상 작동 확인**을 받았습니다.
- 기존 블랙/폭풍 모드 저장·복원, 목록의 모드 표시와 검·소용돌이 마크, 아무 버튼 컷신 넘기기와 한글화를 함께 포함합니다.

**버전과 다운로드 링크는 v1.8 그대로입니다.** 이전 ZIP을 받으셨다면 다시 받아 새 폴더에 압축을 풀고, 지원 원본 또는 기존 한글 ISO에 적용해 주세요. xemu를 완전히 종료한 뒤 새 ISO로 부팅하여 기존 게임 내 세이브를 불러오시면 됩니다. **HDD 교체·세이브 삭제·Python 설치는 필요 없습니다.**

설정 파일의 내용·서명 검사와 원래 오류 판정은 유지합니다. 코드 검사에서는 정상 파일과 손상 파일을 구분하고, 작업 메모리 할당 실패·주소 조건 불일치 및 양방향·연속 모드 덮어쓰기를 확인했습니다. 사용자 환경에서 경고를 일으킨 세부 메모리 상태까지 확정한 것은 아니며, 이번 확인은 전 난이도·전 챕터·모든 환경의 완주 검수를 뜻하지 않습니다.

모드 기록이 없는 이전 세이브는 ‘교차의 법’ 소지 시 폭풍으로 복원합니다. 기록·비전서가 모두 없으면 ‘미확인’ 표시 후 블랙으로 불러오며, 유효한 모드 기록을 우선합니다.

'''
for source,target in [('README.md','README.md'),('RELEASE_NOTES.md','RELEASE_NOTES.md')]:
 s=(R/'prior'/source).read_text();a=s.index('## 2026년');b=s.index('**[v1.8 폭풍 다운로드]',a) if source=='README.md' else s.index('**비행선 보고서',a)
 s=s[:a]+header+s[b:]
 s=s.replace('배포 ZIP: **62,861,980바이트**',f"배포 ZIP: **{r['bytes']:,}바이트**").replace('558f55599302f9403faa1da290e35f3e3e1a711ee3d6aea103cfbda3405c9da8',r['sha256'])
 s=s.replace('폭풍 표시가 없는 기존 저장은 블랙으로 읽으므로 **폭풍은 새 게임과 새 저장 슬롯으로 시작**해 주세요.','유효한 모드 기록을 우선하며, 기록이 없는 이전 저장의 복원 기준은 위 안내를 참고해 주세요. 폭풍을 새로 시작하려면 새 게임에서 선택해 주세요.')
 s=s.replace('v1.8의 실제 Windows GUI 실행·xemu 화면·실기와 모든 진행 분기는 미검증이며,','v1.8의 전체 Windows GUI·xemu 화면·실기와 모든 진행 분기까지 검증한 것은 아니며,')
 (O/target).write_text(s)
pub=(R/'prior/publish.py').read_text().replace("OLD='ee36ae347ad2287cc74e0efee3ad00f380ecb9164f2def8f0c91b0dd740f7cf6'","OLD='558f55599302f9403faa1da290e35f3e3e1a711ee3d6aea103cfbda3405c9da8'").replace("NEW='558f55599302f9403faa1da290e35f3e3e1a711ee3d6aea103cfbda3405c9da8'",f"NEW='{r['sha256']}'").replace('?revision=save-mode-marks-','?revision=settings-workspace-20261025-')
(O/'publish.py').write_text(pub)
print('docs ready',r['sha256'])
