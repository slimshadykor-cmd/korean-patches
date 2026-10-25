from pathlib import Path
import os,json,zipfile,gzip,hashlib,urllib.request,subprocess,copy
R=Path(__file__).parent;REPO='slimshadykor-cmd/korean-patches';API='https://api.github.com/repos/'+REPO;TAG='ngb-v2.0';NAME='NGB_Korean_Patch_v2.0.zip';sha=lambda b:hashlib.sha256(b).hexdigest()
def api(path,data=None,method=None):
 h={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 with urllib.request.urlopen(urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),h,method=method or ('GET' if data is None else 'POST')),timeout=120) as f:return json.load(f)
def assemble():
 m=json.loads(gzip.decompress((R/'manifest.json.gz').read_bytes()));base=R/'base.zip';urllib.request.urlretrieve('https://github.com/'+REPO+'/releases/download/ngb-v1.8/NGB_Korean_Patch_v1.8.zip',base);assert sha(base.read_bytes())==m['base_sha256']
 assert sha((R/'payload.zip').read_bytes())==m['payload_sha256']
 with zipfile.ZipFile(base) as b,zipfile.ZipFile(R/'payload.zip') as p,zipfile.ZipFile(R/NAME,'w') as z:
  original=json.loads(b.read('NGB_Korean_Patch_v1.8/ngb_native11/assets/build_plan.json'))
  def dec(v):
   kind,data=v
   if kind=='ref':
    o=original
    for k in data:o=o[k]
    return o
   if kind=='dict':return {k:dec(x) for k,x in data}
   if kind=='list':return [dec(x) for x in data]
   assert kind=='value';return data
  plan=json.dumps(dec(json.loads(gzip.decompress((R/'plan_delta.json.gz').read_bytes()))),ensure_ascii=False,indent=2).encode()
  for e in m['files']:
   data=plan if e['source']=='plan' else (b if e['source']=='base' else p).read(e['entry']);assert sha(data)==e['sha256'],e['name'];i=zipfile.ZipInfo(e['name'],tuple(e['info']['date_time']))
   for k,v in e['info'].items():
    if k!='date_time':setattr(i,k,bytes.fromhex(v) if k in ['extra','comment'] else v)
   z.writestr(i,data,compress_type=i.compress_type,compresslevel=6)
 assert sha((R/NAME).read_bytes())==m['output_sha256']
 with zipfile.ZipFile(R/NAME) as z:assert z.testzip() is None
 return m
if __name__=='__main__':
 assert os.environ['GITHUB_REPOSITORY']==REPO
 m=assemble();releases=api('/releases?per_page=100');old=[r for r in releases if r['tag_name'].startswith('ngb-') and r['tag_name']!=TAG]
 rel=next((r for r in releases if r['tag_name']==TAG),None)
 body=(R/'RELEASE_NOTES.md').read_text()
 if rel is None:rel=api('/releases',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'닌자가이덴 블랙 한글패치 v2.0 폭풍','body':body,'draft':True,'prerelease':False})
 for f in [R/NAME,R/'SHA256SUMS.txt']:
  subprocess.run(['gh','release','upload',TAG,str(f),'--repo',REPO,'--clobber'],check=True)
 after=api('/releases/'+str(rel['id']));asset=next(a for a in after['assets'] if a['name']==NAME);assert asset['digest']=='sha256:'+m['output_sha256']
 api('/releases/'+str(rel['id']),{'body':body,'draft':False,'make_latest':'true'},'PATCH')
 url='https://github.com/'+REPO+'/releases/download/'+TAG+'/'+NAME
 with urllib.request.urlopen(url+'?verify=v20',timeout=180) as f:assert sha(f.read())==m['output_sha256']
 # Replace obsolete release bodies: no old download/version navigation links remain.
 results=[]
 for r in old:
  notice=f"# 이전 버전 {r['tag_name'].removeprefix('ngb-')} 안내\n\n이 버전의 배포 안내는 v2.0으로 통합되었습니다.\n\n**[닌자가이덴 블랙 v2.0 다운로드·업데이트 안내](https://github.com/{REPO}/releases/tag/{TAG})**\n\n이후 수정도 같은 v2.0 페이지에서 파일과 수정 날짜를 갱신합니다. 기존 버전의 설치 안내·다운로드 링크는 혼동을 줄이기 위해 정리했습니다.\n\n날짜별 누적 변경 내용은 v2.0 페이지에서 확인해 주세요. 기존 게임 내 저장은 유지되며 지원하는 원본 또는 기존 한글 ISO에 적용할 수 있습니다.\n"
  api('/releases/'+str(r['id']),{'body':notice},'PATCH');verify=api('/releases/'+str(r['id']));assert verify['body']==notice;results.append(r['tag_name'])
 print(json.dumps({'status':'PASS','release':url,'sha256':m['output_sha256'],'previous_notices':results,'old_assets_preserved':True}))
