from pathlib import Path
import json,hashlib,base64,zipfile,gzip,copy,shutil,sys
R=Path('publish_settings');O=R/'upload';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
name='NGB_Korean_Patch_v1.8';pre=name+'/'
base_path=R/'base-v1.8.zip';old=Path('mark_release/final.xbe').read_bytes();new=Path('profile_fix/test6.xbe').read_bytes()
assert sha(base_path.read_bytes())=='558f55599302f9403faa1da290e35f3e3e1a711ee3d6aea103cfbda3405c9da8'
assert sha(new)=='1b06de256086d7a6fd900046145833becb2eb129b7113ac85e7a69913a7d8576'
def diff(a,b):
 out=[];i=0
 while i<len(b):
  if i<len(a) and a[i]==b[i]:i+=1;continue
  st=i
  while i<len(b) and (i>=len(a) or a[i]!=b[i]):i+=1
  out.append({'offset':st,'data':base64.b64encode(b[st:i]).decode()})
 return out
def apply(b,cs):
 b=bytearray(b)
 for c in cs:
  d=base64.b64decode(c['data']);b[c['offset']:c['offset']+len(d)]=d
 return bytes(b[:len(new)])
with zipfile.ZipFile(base_path) as z:
 original=json.loads(z.read(pre+'ngb_native11/assets/build_plan.json'));plan=copy.deepcopy(original);cs=diff(old,new)
 plan['xbe']['changes']+=cs;plan['xbe']['output_sha256']=sha(new);plan['xbe']['output_length']=len(new)
 for r in plan['boot_repairs']:r['changes']+=cs
 plan['boot_repairs'].append({'previous_xbe_sha256':sha(old),'changes':cs,'reason':'2026-10-25 settings read workspace fix'})
 plan['profile_workspace_release']={'date':'2026-10-25','scope':'system.dat reads only','reserved_bytes':16384,'native_validation_preserved':True,'xemu_confirmation':'User confirmed TEST6 works on 2026-10-25; not a full playthrough'}
 assert apply(Path('original.xbe').read_bytes(),plan['xbe']['changes'])==new
 for b in [old,Path('test5.xbe').read_bytes()]:assert apply(b,next(r['changes'] for r in plan['boot_repairs'] if r['previous_xbe_sha256']==sha(b)))==new
 assert plan['archives']==original['archives'] and plan['root_patches']==original['root_patches']
 plan['private_personal_build']=False
 plan['save_mode_release']['settings_error_fixed']=True
 plan['save_mode_release']['settings_workspace_user_confirmed']='2026-10-25 TEST6'
 plan['cutscene_skip_test']['actual_gameplay_verified']=True
 plan_bytes=json.dumps(plan,ensure_ascii=False,indent=2).encode()
 def encode(v,o,path):
  if v==o:return ['ref',path]
  if isinstance(v,dict):return ['dict',[[k,encode(x,o.get(k) if isinstance(o,dict) else None,path+[k])] for k,x in v.items()]]
  if isinstance(v,list):return ['list',[encode(x,o[i] if isinstance(o,list) and i<len(o) else None,path+[i]) for i,x in enumerate(v)]]
  return ['value',v]
 (O/'plan_delta.json.gz').write_bytes(gzip.compress(json.dumps(encode(plan,original,[]),ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
 validation=json.loads(z.read(pre+'VALIDATION.json'))
 validation['settings_read_20261025']={k:json.loads(Path(v).read_text()) for k,v in {'build':'profile_fix/build.json','native_before':'profile_fix/before_native.json','native_after':'profile_fix/fixed_native.json','cross_modes':'profile_fix/cross_modes.json','scope':'profile_fix/scope.json','core':'save_check.json'}.items()}
 validation['settings_read_20261025']['user_confirmation']={'date':'2026-10-25','message':'아니야 내가 확인했어 / 잘되는거','scope':'TEST6 user xemu confirmation; not all modes/chapters/hardware'}
 readme='''닌자가이덴 블랙 한글패치 v1.8 폭풍 — 2026년 10월 25일 수정본

이번 수정
- 저장 후 다시 실행할 때 나타나던 설정 불러오기 경고를 해결하기 위해 설정 읽기 작업 메모리 처리를 보완했습니다.
- 같은 슬롯에 블랙/폭풍을 바꾸어 저장하는 경우와 연속 덮어쓰기의 저장·복원을 검사했습니다.
- 수정본은 사용자 xemu 실행에서 정상 작동 확인을 받았습니다.
- 기존 모드 저장·복원, 블랙/폭풍 표시와 마크, 아무 버튼 컷신 넘기기 및 한글화를 포함합니다.

사용 방법
1. ZIP 전체를 새 폴더에 압축 해제합니다.
2. NGB_Korean_Patch.exe를 실행하고 지원 원본 또는 기존 한글 ISO를 선택합니다.
3. 새 한글 XISO 만들기를 누릅니다.
4. xemu를 완전히 종료한 뒤 새 *_Korean_v1.8.xiso.iso로 부팅합니다.
5. 기존 게임 내 세이브를 불러옵니다. 이전 에뮬레이터 스냅샷은 사용하지 않습니다.

버전·다운로드 링크는 v1.8 그대로입니다. 이전 ZIP 이용자는 다시 받아 적용해 주세요.
일반 ISO/XISO는 자동 처리합니다. Python 설치·HDD 교체·세이브 삭제는 필요 없습니다.
공용 패치에는 게임 ISO·BIOS·HDD·세이브·개인용 무적 치트가 없습니다.
Windows 10/11 64비트 / Japan-Korea (En,Ja)판용입니다.
원본과 지원 이전 패치의 내부 데이터로 호환성을 확인합니다. 모든 지역판·임의 수정본 지원은 아닙니다.

모드 기록이 없는 이전 세이브는 교차의 법 소지 시 폭풍으로 복원합니다.
기록·비전서가 모두 없으면 미확인 표시 후 블랙으로 불러오며, 유효한 모드 기록을 우선합니다.
이미 지나친 첫 닌자에게서 놓친 비전서를 자동 지급하는 수정은 아닙니다.

확인 범위
설정 읽기의 정상·할당 실패·주소 조건 불일치, 손상 파일 오류 유지, 양방향·연속 모드 덮어쓰기와 복원을 코드 실행으로 검사했습니다.
파일 입출력과 Xbox 서명은 모의 처리입니다. 사용자 xemu 정상 작동 확인은 별도입니다.
전 난이도·전 챕터 완주 또는 모든 환경·실기 검증을 뜻하지 않습니다.
게임 데이터 내용·서명 검사는 유지합니다. 이번 변경은 설정 읽기 경로에 한정됩니다.

원본 참고 해시(사용자 제공)
MD5: 9e09ba06bab10c53b8460f4c43b98b18
SHA-1: 8581d5d0e2f90dcbcb63bd94bcb958a764f6d3a5
ISO/XISO 재구성 시 전체 해시는 달라질 수 있습니다.

다운로드와 상세 설명:
https://github.com/slimshadykor-cmd/korean-patches/releases/tag/ngb-v1.8
한글화·제작: 슬림쉐이디
'''
 gui=z.read(pre+'ngb_native11/patch_gui.py').decode()
 assert 'Save_TEST' not in gui
 gui=gui.replace('v1.8 폭풍 · 새 게임에서 블랙/폭풍 선택 · ISO/XISO 자동 처리','v1.8 폭풍 · 2026.10.25 설정 읽기 수정 · ISO/XISO 자동 처리')
 changes={'README_KO.txt':readme.encode(),'VALIDATION.json':json.dumps(validation,ensure_ascii=False,indent=2).encode(),'ngb_native11/patch_gui.py':gui.encode(),'ngb_native11/assets/build_plan.json':plan_bytes}
 out=Path('deliverables')/(name+'.zip');files=[]
 with zipfile.ZipFile(out,'w') as target,zipfile.ZipFile(O/'payload.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as payload:
  for info in z.infolist():
   rel=info.filename.removeprefix(pre);data=changes.get(rel,z.read(info.filename));ni=copy.copy(info)
   if rel in changes:ni.date_time=(2026,10,25,5,0,0)
   target.writestr(ni,data,compress_type=ni.compress_type,compresslevel=6)
   source='plan' if rel=='ngb_native11/assets/build_plan.json' else 'payload' if rel in changes else 'base'
   if source=='payload':payload.writestr(info.filename,data)
   fields={k:getattr(ni,k) for k in ['date_time','compress_type','comment','extra','create_system','create_version','extract_version','flag_bits','volume','internal_attr','external_attr']}
   for k in ['comment','extra']:fields[k]=fields[k].hex()
   files.append({'name':info.filename,'entry':info.filename,'source':source,'sha256':sha(data),'info':fields})
 with zipfile.ZipFile(out) as q:assert q.testzip() is None
 manifest={'base_sha256':sha(base_path.read_bytes()),'payload_sha256':sha((O/'payload.zip').read_bytes()),'output_sha256':sha(out.read_bytes()),'files':files}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False))
 (O/'manifest.json.gz').write_bytes(gzip.compress((O/'manifest.json').read_bytes(),mtime=0))
 shutil.copyfile(R/'prior/assemble.py',O/'assemble.py')
 sys.path.insert(0,str(O));from assemble import assemble
 assert assemble(base_path,O/'payload.zip',O/'manifest.json',R/'reassembled.zip')==manifest['output_sha256']
 (O/'SHA256SUMS.txt').write_text(manifest['output_sha256']+'  '+name+'.zip\n')
 receipt={'path':str(out),'sha256':manifest['output_sha256'],'bytes':out.stat().st_size,'xbe_sha256':sha(new),'unchanged_zip_entries':len(files)-len(changes),'changed_entries':list(changes),'user_xemu_confirmed':True,'full_playthrough_confirmed':False}
 (R/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2));print(json.dumps(receipt,ensure_ascii=False))
