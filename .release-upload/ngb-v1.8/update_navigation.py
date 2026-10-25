import os,json,re,urllib.request
REPO='slimshadykor-cmd/korean-patches'
assert os.environ['GITHUB_REPOSITORY']==REPO
API='https://api.github.com/repos/'+REPO
def api(path,data=None):
 h={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 req=urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),h,method='GET' if data is None else 'PATCH')
 with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
notice="""<!-- NGB_LATEST_VERSION_NOTICE -->
> [!IMPORTANT]
> **최신 수정본: [닌자가이덴 블랙 v1.8 폭풍 안내·다운로드](https://github.com/slimshadykor-cmd/korean-patches/releases/tag/ngb-v1.8)**
>
> **2026년 10월 25일 수정본**에는 설정 불러오기 경고 수정, 블랙/폭풍 모드 저장·복원, 저장 목록의 모드 표시와 마크, 아무 버튼 컷신 넘기기 및 기존 한글화가 포함되어 있습니다.
> 지원 원본 또는 지원되는 기존 한글 ISO에 적용할 수 있습니다. **기존 게임 내 세이브는 그대로 사용하며 HDD 교체·세이브 삭제는 필요 없습니다.**
> **[최신 패치 ZIP 바로 받기](https://github.com/slimshadykor-cmd/korean-patches/releases/download/ngb-v1.8/NGB_Korean_Patch_v1.8.zip)** · **[게임별 최신 안내](https://github.com/slimshadykor-cmd/korean-patches/tree/main/xbox/ninja-gaiden-black)**
> 아래는 해당 이전 버전의 기존 안내입니다.
<!-- /NGB_LATEST_VERSION_NOTICE -->

---

"""
releases=api('/releases?per_page=100')
targets=[r for r in releases if r['tag_name'].startswith('ngb-') and r['tag_name']!='ngb-v1.8']
assert {r['tag_name'] for r in targets}=={'ngb-v1.0','ngb-v1.2','ngb-v1.3','ngb-v1.4','ngb-v1.5','ngb-v1.6','ngb-v1.7'}
results=[]
for r in targets:
 assert not r['immutable']
 body=r['body'] or ''
 body=re.sub(r'\A<!-- (?:latest-patch-navigation:start|NGB_LATEST_VERSION_NOTICE) -->.*?<!-- (?:latest-patch-navigation:end|/NGB_LATEST_VERSION_NOTICE) -->\s*---\s*','',body,count=1,flags=re.S)
 new=notice+body
 latest=api('/releases/'+str(r['id']))
 assert latest['body']==r['body']
 assets=lambda v:{x['name']:(x['id'],x.get('digest')) for x in v['assets']}
 if new!=r['body']:api('/releases/'+str(r['id']),{'body':new})
 after=api('/releases/'+str(r['id']))
 assert after['body']==new and assets(after)==assets(r)
 results.append(r['tag_name'])
print(json.dumps({'status':'PASS','updated_notices':results,'assets_unchanged':True}))
