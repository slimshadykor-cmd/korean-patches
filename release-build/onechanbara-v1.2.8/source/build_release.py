from pathlib import Path
import zipfile,shutil,subprocess,json
W=Path(__file__).resolve().parent;R=W.parent/'release_v128';P=W/'package';S=W/'source';D=W/'deliverables';S.mkdir(exist_ok=True);D.mkdir(exist_ok=True)
for n in ['dependencies','baseline']:
 if not (W/n).exists():(W/n).symlink_to(R/n,target_is_directory=True)
shutil.copytree(R/'source',S,dirs_exist_ok=True)
s=(S/'Program.cs').read_text().replace('v1.2.2~v1.2.7','v1.2.2~v1.2.8').replace('ISO 한글패치 v1.2.8','ISO 한글패치 v1.2.8 (10/19 대사 수정)')
(S/'Program.cs').write_text(s)
with zipfile.ZipFile(W/'payload.zip','w',zipfile.ZIP_STORED) as z:
 rows=[l.split('\t') for l in (P/'manifest.tsv').read_text().splitlines() if l and not l.startswith('#')]
 for p in [P/'manifest.tsv']+[P/'payload'/n for n in sorted({r[4] for r in rows})]:
  inf=zipfile.ZipInfo(p.relative_to(P).as_posix(),date_time=(2026,10,19,0,0,0));inf.external_attr=0o644<<16;z.writestr(inf,p.read_bytes())
SDK=W/'dependencies/sdk';REF=W/'dependencies/net48/build/.NETFramework/v4.8';res='/resource:'+str(W/'payload.zip')+',OnechanbaraPackage.zip'
common=[str(SDK/'dotnet'),str(SDK/'sdk/8.0.100/Roslyn/bincore/csc.dll'),'/nologo','/noconfig','/nostdlib+','/optimize+','/deterministic+']
cmd=common+['/target:winexe','/platform:x64','/out:'+str(D/'Onechanbara_ISO_Korean_v1.2.8.exe'),res]+['/reference:'+str(REF/x) for x in ['mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll']]+[str(S/f) for f in ['IsoCore.cs','Standalone.cs','Program.cs']];subprocess.run(cmd,check=True)
refs=['/reference:'+str(p) for p in sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.0/ref/net8.0').glob('*.dll'))]
for cli,files,embedded in [('CoreCli',['IsoCore.cs','CoreCli.cs'],False),('StandaloneCli',['IsoCore.cs','Standalone.cs','StandaloneCli.cs'],True)]:
 cmd=common+['/target:exe','/out:'+str(W/f'{cli}.dll')]+refs+[str(S/f) for f in files]
 if embedded:cmd.append(res)
 subprocess.run(cmd,check=True);(W/f'{cli}.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.0'}}}))
with zipfile.ZipFile(D/'Onechanbara_ISO_Korean_v1.2.8.exe') as z:
 assert z.testzip() is None
 for n in z.namelist():assert z.read(n)==(P/n).read_bytes()
print('Windows GUI and test harness compiled; embedded package verified')
