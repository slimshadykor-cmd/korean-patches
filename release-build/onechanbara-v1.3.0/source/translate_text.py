"""Translate only the 107 independently confirmed Unicode display records."""
from pathlib import Path
import json,struct,re,hashlib,sys
R=Path(__file__).resolve().parent.parent
A=R.parent/'audit1024'
sys.path.insert(0,str(A/'tools'))
from xex_codec import unpack,repack
sha=lambda b:hashlib.sha256(b).hexdigest()
baseline=(A/'current/default.xex').read_bytes()
assert sha(baseline)=='1d5ca57194a51bf60eee37f9612f30f275381c85c480b5210a0d0e5895e4573c'
old,fmt=unpack(baseline);new=bytearray(old);ranges=[];changes=[]
wide=[(0x33e90,'コスチューム名を入力してください。','의상 이름을 입력해 주세요.'),
 (0x3916c,'コスチュームデータ','의상 데이터'),(0x39180,'ゲームデータ','게임 데이터'),
 (0x391a4,'エラーファイル','오류 파일')]
for at,jp,ko in wide:
    raw=jp.encode('utf-16-be')+b'\0\0';b=ko.encode('utf-16-be')+b'\0\0'
    assert old[at:at+len(raw)]==raw and len(b)<=len(raw)
    new[at:at+len(raw)]=b+bytes(len(raw)-len(b));ranges.append((at,at+len(raw)))
    changes.append({'encoding':'UTF-16BE','offset':hex(at),'original':jp,'korean':ko,'slot_bytes':len(raw)})

tr={0x8000:'오네찬바라 vorteX',0x7f00:'게임 종류',0x7f01:'랭크 매치',0x7f02:'플레이어 매치',
 0x4:'카우보이 모자와 수영복 차림의 아름다운 여검사 아야가 좀비를 상대로 칼을 휘두르는 통쾌한 액션 게임. 더욱 빠르고 화려해진 액션으로 좀비를 베어 쓰러뜨리세요! 적의 피를 뒤집어쓸수록 차오르는 오염 게이지와 게이지가 MAX에 도달하면 발동하는 폭주 시스템도 건재합니다. 아야와 사키의 외모도 더욱 다양하게 꾸밀 수 있습니다. 의상과 머리색은 물론, 이번에는 눈과 입술 색까지 변경할 수 있습니다! 호평받은 시스템은 그대로 살리고 통쾌함을 한층 높인 『오네찬바라 vorteX』. 전작보다 더욱 아름다워진 아야와 사키에 새로운 캐릭터까지 합류하며, "기혈"을 둘러싼 이야기는 절정으로 치닫습니다.',
 0x6:'액션',0xd:'스토리 모드',0xe:'서바이벌 모드',0x13:'난이도 {c3},\r\n챕터 {p0x10000007}까지 진행 중.',
 0x67:'챕터 {p0x10000001} 플레이 중.\r\n「{c0}」: Lv{p0x10000002}',
 0x68:'챕터 {p0x10000001} 플레이 중.\r\n2인 동시 플레이 중.',
 0x69:'챕터 {p0x10000001} 플레이 중.\r\n「{c0}」: Lv{p0x10000002}',
 0x6a:'챕터 {p0x10000001} 플레이 중.\r\n2인 동시 플레이 중.',
 0x6b:'스테이지 {p0x10000003}-{p0x10000004} 플레이 중.\r\n「{c0}」: Lv{p0x10000002}',
 0x6c:'스테이지 {p0x10000003}-{p0x10000004} 플레이 중.\r\n2인 동시 플레이 중.',
 0x6d:'연습 모드 플레이 중.\r\n「{c0}」: Lv{p0x10000002}',
 0x6e:'퀘스트 모드 확인 중.\r\n퀘스트 {p0x10000005}개 달성.',
 0x6f:'꾸미기 모드 이용 중.\r\n꾸미기 부품 {p0x10000006}개 획득.',
 0x70:'감상 모드 이용 중.\r\n「{c2}」 감상 중.',0x7b:'아야',0x7c:'사키',0x7d:'안나'}
core={x['string_id']:x for x in json.loads((A/'results/common_string_table.json').read_text())}
for i in range(20):
    name=core[149+i]['current']
    tr[0x16+i*2]=f'퀘스트 칭호: 『{name}』 획득'
    tr[0x17+i*2]=f'퀘스트 No.{i+1} 『{name}』(Lv1~3)를 달성했습니다.'
    tr[0x4c+i]=f'퀘스트 No.{i+1} 『{name}』(Lv1~3)를 달성하세요.'
for i,difficulty in enumerate(['NORMAL','HARD','VIOLENT','BERSERK']):
    tr[0x3e+i*2]=f'스토리 모드: {difficulty} 난이도 클리어'
    tr[0x3f+i*2]=f'{difficulty} 난이도로 스토리 모드를 클리어했습니다.'
    tr[0x60+i]=f'{difficulty} 난이도로 스토리 모드를 클리어하세요.'
for i,name in enumerate(['아야','사키','안나']):
    tr[0x46+i*2]=f'{name}: 특전 모두 획득'
    tr[0x47+i*2]=f'캐릭터 「{name}」의 특전을 모두 획득했습니다.'
    tr[0x64+i]=f'캐릭터 「{name}」의 특전을 모두 획득하세요.'
expected=json.loads((A/'results/confirmed_untranslated_text.json').read_text())
assert set(tr)=={int(x['id'],16) for x in expected} and len(tr)==103
assert all(not re.search('[ぁ-ゖァ-ヺ一-龯ｦ-ﾝ]',s) for s in tr.values())

base=0x5370000
magic,ver,cap,used,freecap,freeused=struct.unpack_from('>6I',old,base)
freebase=base+24+cap*18;data=freebase+freecap*8
assert (cap,used,freecap,freeused)==(40,40,21,1)
target=[]
for i in range(used):
    at=base+24+i*18;ns,ident,off,size=struct.unpack_from('>HQII',old,at)
    if ns==3:target.append((at,ident,off,size))
assert len(target)==1
entry,lang,offset,capacity=target[0];start=data+offset
assert (lang,start,capacity)==(2,0x5370aba,9113)
magic,version,declared,count=struct.unpack_from('>4sIIH',old,start)
assert (magic,version,declared,count)==(b'XSTR',1,9109,128)
p=start+14;body=bytearray();strings=[]
for i in range(count):
    sid,n=struct.unpack_from('>HH',old,p);p+=4;jp=bytes(old[p:p+n]).decode('utf-8');p+=n
    ko=tr.get(sid,jp);b=ko.encode('utf-8');assert len(b)<=65535
    assert re.findall(r'\{[^{}]*\}',jp)==re.findall(r'\{[^{}]*\}',ko)
    body+=struct.pack('>HH',sid,len(b))+b;strings.append({'id':hex(sid),'original':jp,'korean':ko,'modified':sid in tr})
    if sid in tr:changes.append({'encoding':'UTF-8','string_id':hex(sid),'original':jp,'korean':ko})
assert p==start+capacity
size=14+len(body);assert size<capacity
# Match the existing XSTR size convention (entry size minus four), retaining all
# outer resource offsets. Return the unused suffix to the existing XDBF free list.
payload=struct.pack('>4sIIH',b'XSTR',version,size-4,count)+body
new[start:start+capacity]=payload+bytes(capacity-size);ranges.append((start,start+capacity))
struct.pack_into('>I',new,entry+14,size);ranges.append((entry+14,entry+18))
struct.pack_into('>I',new,base+20,freeused+1);ranges.append((base+20,base+24))
assert old[freebase+freeused*8:freebase+(freeused+1)*8]==bytes(8)
struct.pack_into('>II',new,freebase+freeused*8,offset+size,capacity-size)
ranges.append((freebase+freeused*8,freebase+(freeused+1)*8))
assert len(changes)==107
changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
assert all(any(a<=i<z for a,z in ranges) for i in changed)
result=repack(baseline,new,fmt);check,_=unpack(result);assert check==new and len(result)==len(baseline)
(R/'candidate/default.xex').write_bytes(result);(R/'candidate.memory.bin').write_bytes(new)
(R/'audit/translations.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
(R/'audit/xstr_strings.json').write_text(json.dumps(strings,ensure_ascii=False,indent=2))
report={'version':'1.3.0','baseline_xex_sha256':sha(baseline),'result_xex_sha256':sha(result),'translated_records':len(changes),'utf16_records':4,'utf8_records':103,'xstr_original_bytes':capacity,'xstr_result_bytes':size,'freed_bytes':capacity-size,'string_ids_and_placeholders_preserved':True,'resource_offsets_preserved':True,'permitted_logical_ranges':ranges,'changed_logical_bytes':len(changed),'images_modified':False,'loading_code_modified':False,'actual_xenia_gameplay_tested':False}
(R/'audit/translation_build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report)
