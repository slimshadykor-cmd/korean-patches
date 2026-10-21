from pathlib import Path
import sys,io,zipfile,gzip,struct,json,hashlib,subprocess,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'tools'))
from audit_common import delta,sha
S=R/'baseline_source/release-build/onechanbara-v1.2.8/source';P=R/'package';D=R/'deliverables'
shutil.copytree(R/'baseline_package',P,dirs_exist_ok=True)
rows={r[0]:r for l in (P/'manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
oldzip=R/'inputs/Onechanbara vorteX 일본판 한글화/Onechanbara_ISO_Korean_v1.2.5_Release.zip'
assert sha(oldzip.read_bytes())=='d0774300d87384b906749b405e4730af1bdcbc4fc47b292b168f0aea1f9093e3'
with zipfile.ZipFile(oldzip) as z:(R/'v125.exe').write_bytes(z.read('Onechanbara_ISO_Korean_v1.2.5.exe'))
with zipfile.ZipFile(R/'v125.exe') as z:
 oldrows={r[0]:r for l in z.read('manifest.tsv').decode().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
 row=oldrows['Media/Menu/title2d.cat'];title=delta((R/'original/Media/Menu/title2d.cat').read_bytes(),z.read('payload/'+row[4]));assert sha(title)==row[2]
off,capacity=struct.unpack_from('>II',title);im=Image.open(io.BytesIO(title[off:off+capacity])).convert('RGB');assert im.size==(1280,720)
f=ImageFont.truetype(str(R/'deps/NotoSansCJKkr-Regular.otf'),21);draw=ImageDraw.Draw(im);label='v1.2.9';bbox=draw.textbbox((0,0),label,font=f,stroke_width=2)
draw.text((194,684-bbox[1]),label,font=f,fill=(239,249,248),stroke_width=2,stroke_fill=(12,21,25))
for quality in range(98,89,-1):
 out=io.BytesIO();im.save(out,format='JPEG',quality=quality,subsampling=0,optimize=True);jpeg=out.getvalue()
 if len(jpeg)<=capacity:break
assert len(jpeg)<=capacity
out=bytearray(title);out[off:off+capacity]=jpeg+bytes(capacity-len(jpeg))
assert out[:off]==title[:off] and out[off+capacity:]==title[off+capacity:]
(R/'candidate/Media/Menu/title2d.cat').write_bytes(out)
(D/'Onechanbara_v1.2.9_Title.jpg').write_bytes(jpeg)
changes=['default.xex','Media/Menu/title2d.cat']
for rel in changes:
 row=rows[rel];b=(R/'candidate'/rel).read_bytes();assert len(b)==int(row[1])
 row[3]=','.join(dict.fromkeys(row[3].split(',')+[row[2]]+([sha((R/'jp_test01.xex').read_bytes()),sha((R/'kor128_test01.xex').read_bytes())] if rel=='default.xex' else [])))
 row[2]=sha(b);p=struct.pack('<4sIIII',b'OPD1',len(b),1,0,len(b))+b
 (P/'payload'/row[4]).write_bytes(gzip.compress(p,9,mtime=0))
 for version in ['original','current']:assert delta((R/version/rel).read_bytes(),(P/'payload'/row[4]).read_bytes())==b
(P/'manifest.tsv').write_text('# path\tresult_size\tresult_sha256\taccepted_original_sha256\tpayload\tmode\trequired\n'+'\n'.join('\t'.join(r) for r in rows.values())+'\n')
assert len(rows)==158 and len({r[4] for r in rows.values()})==140
for name in ['IsoCore.cs','Standalone.cs','Program.cs','CoreCli.cs','StandaloneCli.cs']:
 s=(S/name).read_text()
 if name=='Program.cs':
  s=s.replace('v1.2.8 (10/19 대사 수정)','v1.2.9 (로딩 개선 통합)').replace('v1.2.8 적용','v1.2.9 적용').replace('_KOR_v1.2.8.iso','_KOR_v1.2.9.iso').replace('여신상 수정 적용판을 새 v1.2.8로 만듭니다.','Loading Test01 적용판을 v1.2.9로 만듭니다.')
 (R/'source'/name).write_text(s)
assert (R/'source/IsoCore.cs').read_bytes()==(S/'IsoCore.cs').read_bytes()
with zipfile.ZipFile(R/'payload.zip','w',zipfile.ZIP_STORED) as z:
 for p in [P/'manifest.tsv']+[P/'payload'/n for n in sorted({r[4] for r in rows.values()})]:
  inf=zipfile.ZipInfo(p.relative_to(P).as_posix(),date_time=(2026,10,21,0,0,0));inf.external_attr=0o644<<16;z.writestr(inf,p.read_bytes())
SDK=R/'deps/sdk';REF=R/'deps/net48/build/.NETFramework/v4.8';resource='/resource:'+str(R/'payload.zip')+',OnechanbaraPackage.zip'
common=[str(SDK/'dotnet'),str(SDK/'sdk/8.0.100/Roslyn/bincore/csc.dll'),'/nologo','/noconfig','/nostdlib+','/optimize+','/deterministic+']
exe=D/'Onechanbara_ISO_Korean_v1.2.9.exe'
subprocess.run(common+['/target:winexe','/platform:x64','/out:'+str(exe),resource]+['/reference:'+str(REF/x) for x in ['mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll']]+[str(R/'source'/f) for f in ['IsoCore.cs','Standalone.cs','Program.cs']],check=True)
refs=['/reference:'+str(p) for p in sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.0/ref/net8.0').glob('*.dll'))]
driver='''using System;using System.IO;using System.Reflection;class ShippingDriver {static int Main(string[] a){try {var x=Assembly.LoadFile(Path.GetFullPath(a[0]));x.GetType("Standalone",true).GetMethod("Apply").Invoke(null,new object[]{a[1],a[2],new Action<string>(Console.WriteLine)});return 0;}catch(Exception e){Console.Error.WriteLine((e.InnerException??e).ToString());return 1;}}}'''
(R/'source/ShippingDriver.cs').write_text(driver)
for name in ['CoreCli','ShippingDriver']:
 files=['IsoCore.cs','CoreCli.cs'] if name=='CoreCli' else ['ShippingDriver.cs']
 subprocess.run(common+['/target:exe','/out:'+str(R/(name+'.dll'))]+refs+[str(R/'source'/f) for f in files],check=True)
 (R/(name+'.runtimeconfig.json')).write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.0'}}}))
with zipfile.ZipFile(exe) as z:
 assert z.testzip() is None
 for name in z.namelist():assert z.read(name)==(P/name).read_bytes()
report={'version':'1.2.9','changed_assets_from_latest_v128':changes,'other_156_manifest_paths_unchanged':True,'loading_xex_matches_user_tested_build':rows['default.xex'][2],'patcher_core_identical_to_v128':True,'title_size':im.size,'title_jpeg_quality':quality,'manifest_paths':158,'unique_payloads':140,'test01_input_supported':True,'exe_sha256':sha(exe.read_bytes()),'actual_xenia_gameplay_tested_by_assistant':False}
(R/'audit/build_validation.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
