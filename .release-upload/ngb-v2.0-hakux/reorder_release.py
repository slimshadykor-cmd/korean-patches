"""Move the hakuX candidate notes below the complete common v2.0 notes."""
import hashlib,json,os,urllib.request
REPO='slimshadykor-cmd/korean-patches'
API='https://api.github.com/repos/'+REPO
MARK='<!-- hakux-v20-20261025 -->'
COMMON='https://github.com/'+REPO+'/releases/download/ngb-v2.0/NGB_Korean_Patch_v2.0.zip'
HAKU='https://github.com/'+REPO+'/releases/download/ngb-v2.0/NGB_Korean_Patch_v2.0_hakuX.zip'
def reorder(body):
 assert body.count(MARK)==1 and body.count(COMMON)==1 and body.count(HAKU)==1
 start=body.index(MARK)
 if body.index(COMMON)<start:return body
 end=body.index('\n---\n',start)
 candidate=body[start:end].strip()
 common=body[:start].rstrip()+'\n\n'+body[end+len('\n---\n'):].lstrip()
 result=common.rstrip()+'\n\n---\n\n'+candidate+'\n'
 assert result.index(COMMON)<result.index(HAKU)
 assert sorted(x for x in body.splitlines() if x.strip())==sorted(x for x in result.splitlines() if x.strip())
 return result
def api(path,data=None):
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'}
 req=urllib.request.Request(API+path,None if data is None else json.dumps(data).encode(),headers,method='GET' if data is None else 'PATCH')
 with urllib.request.urlopen(req,timeout=90) as f:return json.load(f)
def asset_state(release):
 return sorted((a['id'],a['name'],a['size'],a['digest']) for a in release['assets'])
if __name__=='__main__':
 assert os.environ['GITHUB_REPOSITORY']==REPO
 old=api('/releases/tags/ngb-v2.0');newbody=reorder(old['body'])
 if newbody!=old['body']:
  current=api('/releases/'+str(old['id']))
  assert current['body']==old['body'] and asset_state(current)==asset_state(old),'Concurrent release edit'
  api('/releases/'+str(old['id']),{'body':newbody})
 new=api('/releases/'+str(old['id']))
 assert new['body']==newbody and asset_state(new)==asset_state(old)
 print(json.dumps({'status':'PASS','common_v2_first':True,'all_text_preserved':True,'all_assets_unchanged':True,'body_sha256':hashlib.sha256(newbody.encode()).hexdigest()}))
