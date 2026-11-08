"""Save the build only on the development branch, without publishing a release."""
import os,json,base64,urllib.request
from pathlib import Path

repo=os.environ['BUILD_REPOSITORY']
assert repo=='slimshadykor-cmd/korean-patches'
branch='development/onechanbara-direct-dxgi-v1.7'
source=os.environ['BUILD_SOURCE_SHA']
def api(path,body=None,method=None):
    req=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                 'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},
        method=method)
    with urllib.request.urlopen(req,timeout=120) as r:return json.load(r)
head=api('git/ref/heads/'+branch)['object']['sha']
assert head==source,'Branch moved during build; refusing stale output'
tree=api('git/commits/'+head)['tree']['sha']
entries=[]
out=Path('runtime-output')
for p in sorted(out.iterdir()):
    data=p.read_bytes();assert len(data)<90*1024*1024
    if p.name=='build.json':
        meta=json.loads(data);meta['source_commit']=source;meta['run_url']=os.environ['BUILD_RUN_URL']
        data=(json.dumps(meta,indent=2)+'\n').encode()
    blob=api('git/blobs',{'content':base64.b64encode(data).decode(),'encoding':'base64'})
    entries.append({'path':'development/onechanbara-direct-dxgi/runtime/'+p.name,
                    'mode':'100644','type':'blob','sha':blob['sha']})
newtree=api('git/trees',{'base_tree':tree,'tree':entries})
commit=api('git/commits',{'message':'Build Onechanbara v1.7 direct DXGI Windows runtime',
                        'tree':newtree['sha'],'parents':[head]})
assert api('git/ref/heads/'+branch)['object']['sha']==head,'Branch moved before output commit'
api('git/refs/heads/'+branch,{'sha':commit['sha'],'force':False},'PATCH')
print('Development runtime committed: '+commit['sha'])
