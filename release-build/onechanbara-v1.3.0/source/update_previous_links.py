"""Add current-release navigation to the seven existing Onechanbara releases."""
from pathlib import Path
import os,json,re,urllib.request
repo='slimshadykor-cmd/korean-patches';api='https://api.github.com/repos/'+repo
token=os.environ['GH_TOKEN']
def request(path,method='GET',payload=None):
    req=urllib.request.Request(api+path,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},data=None if payload is None else json.dumps(payload).encode())
    with urllib.request.urlopen(req) as r:return json.load(r)
new=request('/releases/tags/onechanbara-v1.3.0')
assert not new['draft'] and not new['prerelease']
expected=json.loads((Path(__file__).resolve().parent.parent/'recipe.json').read_text(encoding='utf-8'))
assets=[a for a in new['assets'] if a['name']=='Onechanbara_ISO_Korean_v1.3.0_Release.zip']
assert len(assets)==1 and assets[0]['digest']=='sha256:'+expected['release_sha256']
notice='''<!-- latest-patch-navigation:start -->
> **최신 패치: [오네찬바라 볼텍스 v1.3.0 다운로드·설치 안내](https://github.com/slimshadykor-cmd/korean-patches/releases/tag/onechanbara-v1.3.0)**
>
> 이 글은 이전 버전의 배포 안내입니다. 새로 받으실 분은 위 링크를 이용해 주세요.
> 이후 버전도 확인할 수 있는 **[게임별 최신 안내 페이지](https://github.com/slimshadykor-cmd/korean-patches/tree/main/xbox360/onechanbara)**입니다.
<!-- latest-patch-navigation:end -->'''
updated=[]
for tag in ['onechanbara-v1.2.9','onechanbara-v1.2.8','onechanbara-v1.2.7','onechanbara-v1.2.6','onechanbara-v1.2.5','onechanbara-v1.2.3','onechanbara-v1.2.2']:
    old=request('/releases/tags/'+tag);body=old['body'] or ''
    pattern=r'<!-- latest-patch-navigation:start -->.*?<!-- latest-patch-navigation:end -->'
    if re.search(pattern,body,re.S):body=re.sub(pattern,lambda m:notice,body,count=1,flags=re.S)
    else:body=notice+'\n\n---\n\n'+body
    result=request('/releases/'+str(old['id']),'PATCH',{'body':body})
    assert result['body']==body and result['tag_name']==tag
    updated.append({'tag':tag,'url':result['html_url']})
print(json.dumps({'updated_previous_release_navigation':updated},ensure_ascii=False))
