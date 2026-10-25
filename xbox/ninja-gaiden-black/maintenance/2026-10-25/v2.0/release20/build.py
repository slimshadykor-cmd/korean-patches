from pathlib import Path
import json,hashlib,zipfile,base64,struct,sys,copy,gzip
from PIL import ImageFont,ImageDraw,Image
R=Path('release20'); sha=lambda b:hashlib.sha256(b).hexdigest();src=Path('save_crash_fix/package/NGB_Korean_Patch_v1.8.zip');pre='NGB_Korean_Patch_v1.8/';newpre='NGB_Korean_Patch_v2.0/'
sys.path.insert(0,str(R.resolve()));from title import b,sw,dataoff,pal,im
# Only replace the existing version-number rectangle, preserving all credit/copyright art.
mask=Image.new('L',(45,22));d=ImageDraw.Draw(mask);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',16);d.text((1,-1),'v2.0',font=font,fill=255)
nb=bytearray(b)
for y in range(22):
 for x in range(45):
  alpha=mask.getpixel((x,y));ix=min(range(256),key=lambda i:(pal[i][3]-alpha)**2+((pal[i][0]-255)**2+(pal[i][1]-255)**2+(pal[i][2]-255)**2)*alpha/255)
  nb[dataoff+sw(x+122,y+26)]=ix
nb=bytes(nb);delta=[{'offset':i,'before':a,'after':c} for i,(a,c) in enumerate(zip(b,nb)) if a!=c];allowed={dataoff+sw(x,y) for y in range(26,48) for x in range(122,167)};assert all(x['offset'] in allowed for x in delta)
preview=im.copy();preview.putdata([pal[nb[dataoff+sw(x,y)]] for y in range(64) for x in range(512)]);preview.resize((1024,128)).save(R/'title_after.png')
(R/'title_delta.json').write_text(json.dumps({'source_sha256':sha(b),'output_sha256':sha(nb),'changes':delta},indent=2))
# Refresh only the on-disc resource cache generation, with XBE section hashes finalized.
sys.argv=['build','save_crash_fix/fixed.xbe'];sys.path.insert(0,'.');import inspect_xbe as X
sys.path.insert(0,'candidate/NGB_CutsceneSkip_TEST1/ngb_native11');from xbe_guard import finalize_build
old=Path('save_crash_fix/fixed.xbe').read_bytes();out=bytearray(old);stamp=0x4b200025;struct.pack_into('<I',out,X.at(0x425b7c),stamp);out=bytes(finalize_build(out,Path('original.xbe').read_bytes()));(R/'fixed.xbe').write_bytes(out)
cs=[{'offset':i,'data':base64.b64encode(bytes([v])).decode()} for i,v in enumerate(out) if old[i]!=v]
with zipfile.ZipFile(src) as z:
 p=json.loads(z.read(pre+'ngb_native11/assets/build_plan.json'));p['xbe']['changes']+=cs;p['xbe']['output_sha256']=sha(out)
 for r in p['boot_repairs']:r['changes']+=cs
 p['boot_repairs'].append({'previous_xbe_sha256':sha(old),'changes':cs,'reason':'v2.0 resource version stamp only'})
 p['release_version']='2.0';p['revision']='v2.0 cumulative public release 2026-10-25';p['title_version']['text']='v2.0 폭풍';p['cache_generation']['stamp']=hex(stamp)
 p['cache_generation']['method']='Dedicated v2.0 cache invalidation stamp; game code unchanged except stamp and section digest.'
 a=next(x for x in p['archives'] if x['path']=='demo.afs');a['version_member']={'name':'demo.spr',**json.loads((R/'title_delta.json').read_text())}
 for key in ['save_workspace_fix','menu_memory_fix','button_sprite_fix','gameplay_art_memory_fix']:
  if key in p:p[key]['public_release']=True
 p['gameplay_art_memory_fix']['user_xemu_confirmation']='2026-10-25 user confirmed delivered memory-fix build operates normally; v2.0 changes cache/version display only.'
 gui=z.read(pre+'ngb_native11/patch_gui.py').decode().replace('v1.8','v2.0').replace('2026.10.25 저장 화면 메모리 수정','2026.10.25 통합 업데이트')
 patch=z.read(pre+'ngb_native11/patch_iso.py').decode().replace('v1.8','v2.0')
 helper='''def version_member(data, a, forward):
    spec=a.get('version_member')
    if not spec:return data
    entries=current_entries(data,a['entries']);e=next(e for e in entries if e['name']==spec['name'])
    member=data[e['offset']:e['offset']+e['size']];h=sha(member)
    if h not in (spec['source_sha256'],spec['output_sha256']):
        if forward:raise ValueError('버전 표시 원본 검사 실패')
        return data
    wanted=spec['output_sha256'] if forward else spec['source_sha256']
    if h==wanted:return data
    buf=bytearray(member)
    for c in spec['changes']:
        before,after=(c['before'],c['after']) if forward else (c['after'],c['before'])
        if buf[c['offset']]!=before:raise ValueError('버전 표시 범위 검사 실패')
        buf[c['offset']]=after
    if sha(buf)!=wanted:raise ValueError('버전 표시 결과 검사 실패')
    result=bytearray(data);result[e['offset']:e['offset']+e['size']]=buf
    return bytes(result)

def archive_digest(data,a):
    return sha(version_member(data,a,False))

'''
 patch=patch.replace('def rebuild_archive(old,a,package):\n    if sha(old)==a[\'output_sha256\']:return old',helper+"def rebuild_archive(old,a,package):\n    old=version_member(old,a,False)\n    if sha(old)==a['output_sha256']:return version_member(old,a,True)")
 patch=patch.replace('    return new\n\ndef patch_root','    return version_member(new,a,True)\n\ndef patch_root')
 patch=patch.replace("if sha(get(result,after[name]))!=wanted:","if (sha(get(result,after[name])) if name=='default.xbe' or name in root_patches else archive_digest(get(result,after[name]),next(a for a in plan['archives'] if a['path']==name)))!=wanted:")
 assert 'return version_member(new,a,True)' in patch
 validation={'date':'2026-10-25','base_xbe_sha256':sha(old),'output_xbe_sha256':sha(out),'game_code_preserved_except_resource_generation':True,'title_changed_pixels':len(delta),'user_confirmed_base_memory_fix':True,'full_playthrough_verified':False}
 repl={'ngb_native11/assets/build_plan.json':json.dumps(p,ensure_ascii=False,indent=2).encode(),'ngb_native11/patch_gui.py':gui.encode(),'ngb_native11/patch_iso.py':patch.encode(),'README_KO.txt':(R/'README_KO.txt').read_bytes(),'VALIDATION.json':json.dumps(validation,ensure_ascii=False,indent=2).encode(),'CHANGELOG_KO.txt':(R/'CHANGELOG_KO.txt').read_bytes()}
 hashes={};dst=R/'NGB_Korean_Patch_v2.0.zip'
 with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as q:
  for info in z.infolist():
   rel=info.filename.removeprefix(pre)
   if rel=='FILE_HASHES.json':continue
   data=repl.pop(rel,z.read(info.filename));ni=copy.copy(info);ni.filename=newpre+rel;q.writestr(ni,data)
   if not info.is_dir():hashes[rel]=sha(data)
  for rel,data in repl.items():q.writestr(newpre+rel,data);hashes[rel]=sha(data)
  q.writestr(newpre+'FILE_HASHES.json',json.dumps(hashes,indent=2))
 with zipfile.ZipFile(dst) as q:assert q.testzip() is None;q.extractall(R/'extracted')
(R/'receipt.json').write_text(json.dumps({'zip_sha256':sha(dst.read_bytes()),'bytes':dst.stat().st_size,'xbe_sha256':sha(out),'manifest_files':len(hashes),'title_changed_pixels':len(delta)},indent=2));print((R/'receipt.json').read_text())
