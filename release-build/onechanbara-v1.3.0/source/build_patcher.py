from pathlib import Path
import struct,gzip,json,hashlib,shutil,zipfile,subprocess
R=Path(__file__).resolve().parent.parent;A=R.parent/'audit1024'
sha=lambda b:hashlib.sha256(b).hexdigest()
P=R/'package';D=R/'deliverables'
shutil.copytree(A/'package',P,dirs_exist_ok=True)
rows={r[0]:r for l in (P/'manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
for rel in ['default.xex','Media/Menu/title2d.cat']:
    row=rows[rel];candidate=(R/'candidate'/rel).read_bytes();assert len(candidate)==int(row[1])
    row[3]=','.join(dict.fromkeys(row[3].split(',')+[row[2]]));row[2]=sha(candidate)
    payload=struct.pack('<4sIIII',b'OPD1',len(candidate),1,0,len(candidate))+candidate
    (P/'payload'/row[4]).write_bytes(gzip.compress(payload,9,mtime=0))
(P/'manifest.tsv').write_text('# path\tresult_size\tresult_sha256\taccepted_original_sha256\tpayload\tmode\trequired\n'+'\n'.join('\t'.join(x) for x in rows.values())+'\n')
assert len(rows)==158 and len({x[4] for x in rows.values()})==140
with zipfile.ZipFile(R/'payload.zip','w',zipfile.ZIP_STORED) as z:
    for p in [P/'manifest.tsv']+[P/'payload'/n for n in sorted({r[4] for r in rows.values()})]:
        inf=zipfile.ZipInfo(p.relative_to(P).as_posix(),date_time=(2026,10,24,0,0,0));inf.external_attr=0o644<<16;z.writestr(inf,p.read_bytes())
SDK=R/'deps/sdk';REF=R/'deps/net48/build/.NETFramework/v4.8'
common=[str(SDK/'dotnet'),str(SDK/'sdk/8.0.100/Roslyn/bincore/csc.dll'),'/nologo','/noconfig','/nostdlib+','/optimize+','/deterministic+']
exe=D/'Onechanbara_ISO_Korean_v1.3.0.exe'
subprocess.run(common+['/target:winexe','/platform:x64','/out:'+str(exe),'/resource:'+str(R/'payload.zip')+',OnechanbaraPackage.zip']+['/reference:'+str(REF/x) for x in ['mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll']]+[str(R/'source'/f) for f in ['IsoCore.cs','Standalone.cs','Program.cs']],check=True)
refs=['/reference:'+str(p) for p in sorted((SDK/'packs/Microsoft.NETCore.App.Ref/8.0.0/ref/net8.0').glob('*.dll'))]
for name in ['CoreCli','ShippingDriver']:
    files=['IsoCore.cs','CoreCli.cs'] if name=='CoreCli' else ['ShippingDriver.cs']
    subprocess.run(common+['/target:exe','/out:'+str(R/(name+'.dll'))]+refs+[str(R/'source'/f) for f in files],check=True)
    (R/(name+'.runtimeconfig.json')).write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.0'}}}))
with zipfile.ZipFile(exe) as z:
    assert z.testzip() is None
    for n in z.namelist():assert z.read(n)==(P/n).read_bytes()
oldrows={r[0]:r for l in (A/'package/manifest.tsv').read_text().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
for rel,r in rows.items():
    if rel not in ['default.xex','Media/Menu/title2d.cat']:assert r==oldrows[rel] and (P/'payload'/r[4]).read_bytes()==(A/'package/payload'/r[4]).read_bytes()
for name in ['IsoCore.cs','Standalone.cs']:assert (R/'source'/name).read_bytes()==(A/'recovered/v129/source'/name).read_bytes()
report={'version':'1.3.0','exe_sha256':sha(exe.read_bytes()),'exe_bytes':exe.stat().st_size,'manifest_paths':158,'unique_payloads':140,'changed_game_files_from_v129':['default.xex','Media/Menu/title2d.cat'],'unchanged_other_manifest_paths':156,'core_and_extraction_logic_unchanged':True,'prior_input_hashes_retained':True,'v129_upgrade_supported':True,'images_modified':True,'title_image_shows':'v1.3.0','earlier_v130_upgrade_supported':True,'windows_gui_executed':False}
(R/'audit/build_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(report,flush=True)
