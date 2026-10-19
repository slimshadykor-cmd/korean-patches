from pathlib import Path
import sys,io,zipfile,gzip,struct,json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;A=W.parent/'audit_identifiers_20261019'
sys.path.insert(0,str(A));from audit_common import delta,sha,memory
P=W/'package';D=W/'deliverables';S=W/'source';C=W/'changed'
for p in [P/'payload',D,S,C,W/'audit']:p.mkdir(parents=True,exist_ok=True)
oldrelease=A/'input/Onechanbara_ISO_Korean_v1.2.7_Release.zip'
assert sha(oldrelease.read_bytes())=='453114a5ff3cd9c17b5090fa6923ceab611aade09c0d9d6e8138c973cc86dd65'
with zipfile.ZipFile(oldrelease) as z:(W/'baseline/v127.exe').write_bytes(z.read('Onechanbara_ISO_Korean_v1.2.7.exe'))
with zipfile.ZipFile(A/'package.zip') as z:
 rows={r[0]:r for l in z.read('manifest.tsv').decode().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
 for name in z.namelist():
  if name!='manifest.tsv':(P/name).write_bytes(z.read(name))
base125=W/'baseline/v125_release.zip'
assert sha(base125.read_bytes())=='d0774300d87384b906749b405e4730af1bdcbc4fc47b292b168f0aea1f9093e3'
with zipfile.ZipFile(base125) as z:(W/'baseline/v125.exe').write_bytes(z.read('Onechanbara_ISO_Korean_v1.2.5.exe'))
with zipfile.ZipFile(W/'baseline/v125.exe') as z:
 rows125={r[0]:r for l in z.read('manifest.tsv').decode().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
 row=rows125['Media/Menu/title2d.cat'];title=delta((A/'original/Media/Menu/title2d.cat').read_bytes(),z.read('payload/'+row[4]));assert sha(title)==row[2]
 (W/'baseline/title_v125.cat').write_bytes(title)
off,capacity=struct.unpack_from('>II',title,0)
im=Image.open(io.BytesIO(title[off:off+capacity]));im.load();im=im.convert('RGB');assert im.size==(1280,720)
f=ImageFont.truetype(str(W/'dependencies/NotoSansCJKkr-Regular.otf'),21);d=ImageDraw.Draw(im);label='v1.2.8';bbox=d.textbbox((0,0),label,font=f,stroke_width=2)
d.text((194,684-bbox[1]),label,font=f,fill=(239,249,248),stroke_width=2,stroke_fill=(12,21,25))
for quality in range(98,89,-1):
 buf=io.BytesIO();im.save(buf,format='JPEG',quality=quality,subsampling=0,optimize=True);jpeg=buf.getvalue()
 if len(jpeg)<=capacity:break
assert len(jpeg)<=capacity
out=bytearray(title);out[off:off+capacity]=jpeg+bytes(capacity-len(jpeg))
assert out[:off]==title[:off] and out[off+capacity:]==title[off+capacity:] and len(out)==len(title)
(C/'title2d.cat').write_bytes(out);(W/'Onechanbara_v1.2.8_Title.jpg').write_bytes(jpeg)
shutil.copyfile(A/'candidate/default.xex',C/'default.xex')
for rel in ['default.xex','Media/Menu/title2d.cat']:
 row=rows[rel];target=(C/Path(rel).name).read_bytes();assert len(target)==int(row[1])
 if rel=='default.xex':
  previous=gzip.decompress((P/'payload'/row[4]).read_bytes());magic,n,count,at,length=struct.unpack_from('<4sIIII',previous)
  assert magic==b'OPD1' and n==len(target) and count==1 and len(previous)==20+length
  public=(A/'current/default.xex').read_bytes();assert target[:at]==public[:at] and target[at+length:]==public[at+length:]
  packed=previous[:20]+target[at:at+length]
 else:packed=struct.pack('<4sIIII',b'OPD1',len(target),1,0,len(target))+target
 (P/'payload'/row[4]).write_bytes(gzip.compress(packed,compresslevel=9,mtime=0))
 row[3]=','.join(dict.fromkeys(row[3].split(',')+[row[2]]));row[2]=sha(target)
 assert delta((A/'original'/rel).read_bytes(),(P/'payload'/row[4]).read_bytes())==target
 assert delta((A/'current'/rel).read_bytes(),(P/'payload'/row[4]).read_bytes())==target
(P/'manifest.tsv').write_text('# path\tresult_size\tresult_sha256\taccepted_original_sha256\tpayload\tmode\trequired\n'+'\n'.join('\t'.join(r) for r in rows.values())+'\n')
assert len(rows)==158 and len({r[4] for r in rows.values()})==140
for name in ['IsoCore.cs','Standalone.cs','Program.cs','CoreCli.cs','StandaloneCli.cs']:
 t=(W/'baseline/source'/name).read_text()
 if name=='Program.cs':t=t.replace('v1.2.7','v1.2.8').replace('v1.2.2~v1.2.6','v1.2.2~v1.2.7')
 (S/name).write_text(t)
for name in ['IsoCore.cs','Standalone.cs']:assert (S/name).read_bytes()==(W/'baseline/source'/name).read_bytes()
with zipfile.ZipFile(W/'payload.zip','w',zipfile.ZIP_STORED) as z:
 for p in [P/'manifest.tsv']+[P/'payload'/n for n in sorted({r[4] for r in rows.values()})]:
  inf=zipfile.ZipInfo(p.relative_to(P).as_posix(),date_time=(2026,10,19,0,0,0));inf.external_attr=0o644<<16;z.writestr(inf,p.read_bytes())
SDK=W/'dependencies/sdk';REF=W/'dependencies/net48/build/.NETFramework/v4.8';resource='/resource:'+str(W/'payload.zip')+',OnechanbaraPackage.zip'
common=[str(SDK/'dotnet'),str(SDK/'sdk/8.0.100/Roslyn/bincore/csc.dll'),'/nologo','/noconfig','/nostdlib+','/optimize+','/deterministic+']
exe=D/'Onechanbara_ISO_Korean_v1.2.8.exe'
cmd=common+['/target:winexe','/platform:x64','/out:'+str(exe),resource]+['/reference:'+str(REF/x) for x in ['mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll']]+[str(S/f) for f in ['IsoCore.cs','Standalone.cs','Program.cs']]
subprocess.run(cmd,check=True)
refs=['/reference:'+str(p) for p in sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.0/ref/net8.0').glob('*.dll'))]
for cli,files,embedded in [('CoreCli',['IsoCore.cs','CoreCli.cs'],False),('StandaloneCli',['IsoCore.cs','Standalone.cs','StandaloneCli.cs'],True)]:
 cmd=common+['/target:exe','/out:'+str(W/f'{cli}.dll')]+refs+[str(S/f) for f in files]
 if embedded:cmd.append(resource)
 subprocess.run(cmd,check=True)
 (W/f'{cli}.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.0'}}}))
with zipfile.ZipFile(exe) as z:
 assert z.testzip() is None
 for name in z.namelist():assert z.read(name)==(P/name).read_bytes()
oldmem=memory((A/'current/default.xex').read_bytes());newmem=memory((C/'default.xex').read_bytes())
diff=[i for i,(a,b) in enumerate(zip(oldmem,newmem)) if a!=b];assert diff==list(range(0x34e98,0x34e9e))
report={'version':'1.2.8','modified_assets':['default.xex','Media/Menu/title2d.cat'],'logical_xex_changed_bytes':len(diff),'logical_xex_changed_offset':'0x34e98','restored_original_internal_prefix':'腕輪：','existing_translations_preserved':True,'title_size':list(im.size),'title_jpeg_quality':quality,'title_other_entries_unchanged':True,'patcher_core_unchanged':True,'manifest_paths':158,'exe_bytes':exe.stat().st_size,'exe_sha256':sha(exe.read_bytes()),'actual_xenia_gameplay_tested':False}
(W/'audit/build_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report,flush=True)
