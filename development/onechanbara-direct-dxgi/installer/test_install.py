from pathlib import Path
import os,tempfile,hashlib,json,subprocess,tomllib,shutil,re
R=Path(__file__).resolve().parent;PS=os.environ.get('OCB_TEST_PWSH','/tmp/onechanbara_pwsh/pwsh');checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def ok(x,msg):
 assert x,msg
 checks.append(msg);print('PASS',msg,flush=True)
with tempfile.TemporaryDirectory(prefix='ocb-direct-install-') as temp:
 T=Path(temp);bundle=T/'bundle';bundle.mkdir()
 (bundle/'xenia_onechanbara.exe').write_bytes(b'fixture Windows emulator, not a usable game executable')
 shutil.copyfile(R/'release/Onechanbara_Launcher.exe',bundle/'Onechanbara_Launcher.exe')
 source=(R/'source/Manage-Onechanbara.ps1').read_text(encoding='utf-8-sig')
 source=re.sub(r"(?m)^\$KnownRuntimeHash='[^']+'",lambda _:"$KnownRuntimeHash='"+h(bundle/'xenia_onechanbara.exe')+"'",source)
 source=re.sub(r"(?m)^\$KnownLauncherHash='[^']+'",lambda _:"$KnownLauncherHash='"+h(bundle/'Onechanbara_Launcher.exe')+"'",source)
 (bundle/'Manage-Onechanbara.ps1').write_text(source,encoding='utf-8-sig')
 def fixture(name,legacy=False):
  p=T/name;p.mkdir();(p/'desktop').mkdir();(p/'config').mkdir()
  (p/'xenia_canary.exe').write_bytes(b'original emulator sentinel')
  (p/'game.iso').write_bytes(b'ISO sentinel')
  (p/'xenia-canary.config.toml').write_text('[GPU]\ngpu="d3d12"\nvsync=false\n')
  (p/'config/another-game.config.toml').write_text('[GPU]\nvsync=false\n')
  uid='E000000000000001'
  for path,value in [(f'content/{uid}/FFFE07D1/00010000/{uid}/Account',b'PROFILE'),(f'content/{uid}/445007D2/00000001/game00',b'SAVE')]:
   f=p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(value)
  if legacy:
   old=p/'config/Onechanbara';old.mkdir();(old/'cache/shaders/shareable').mkdir(parents=True)
   (old/'cache/shaders/shareable/445007D2.bin').write_bytes(b'cached shader sentinel')
   (old/'xconfig.settings').write_bytes(b'xconfig sentinel')
   (old/'patches').mkdir();(old/'patches/own.patch.toml').write_text('title_id="445007D2"\n')
   text=(R/'source/Onechanbara.config.toml').read_text(encoding='utf-8-sig')
   text=text.replace('cache_root = ""','cache_root = '+json.dumps(str(old/'cache'),ensure_ascii=False))
   # Replace the exact profile slot using the existing TOML syntax.
   import re
   text=re.sub(r'(?m)^logged_profile_slot_0_xuid\s*=.*$',f'logged_profile_slot_0_xuid = "{uid}"',text)
   (old/'Onechanbara.config.toml').write_text(text)
   (old/'SyncToggle').mkdir();(old/'SyncToggle/active.lock').write_bytes(b'')
   token='a'*64;entry=str(old/f'SyncToggle/Launcher/{token}/Sync-Toggle.ps1')
   (old/'SyncToggle/installed.json').write_text(json.dumps({'Owner':'Onechanbara.SyncLauncher.1','Build':token,'Entry':entry}))
   (old/'SyncToggle/state.json').write_text('{"Status":"Restored"}')
   (p/'desktop/오네찬바라.lnk').write_text(json.dumps({'Path':str(p/'desktop/오네찬바라.lnk'),'TargetPath':str(p/'Windows/System32/WindowsPowerShell/v1.0/powershell.exe'),'Arguments':'-File "'+entry+'" -Root "'+str(p)+'"','WorkingDirectory':str(old),'IconLocation':'','Description':'','WindowStyle':7}))
  return p
 def snap(p,include_direct=False):return {str(f.relative_to(p)):h(f) for f in p.rglob('*') if f.is_file() and (include_direct or 'OnechanbaraDirect' not in f.parts) and 'desktop' not in f.parts}
 def run(p,fail=False):
  r=subprocess.run([PS,'-NoProfile','-File',str(R/'test_install_harness.ps1'),'-Fixture',str(p),'-Bundle',str(bundle)]+(['-FailLink'] if fail else []),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
  if (r.returncode==0)==fail:raise AssertionError(r.stdout+'\n'+r.stderr)
  return r
 p=fixture('새 설치 공백');before=snap(p);run(p)
 home=p/'config/OnechanbaraDirect';link=p/'desktop/오네찬바라.lnk'
 ok(snap(p)==before,'fresh install preserves source EXE, ISO, common settings, other game, profile and save')
 lnk=json.loads(link.read_text(encoding='utf-8-sig'));print(repr(lnk),repr(str(home)),flush=True);ok(os.path.samefile(lnk['TargetPath'],home/'Onechanbara_Launcher.exe') and not lnk['Arguments'],'desktop directly starts native launcher with no PowerShell arguments')
 cfg=tomllib.loads((home/'Onechanbara.config.toml').read_text(encoding='utf-8-sig'))
 ok(cfg['Vulkan']['vulkan_direct_dxgi'] is True and cfg['GPU']['render_target_path_vulkan']=='fsi','direct DXGI enabled with Vulkan FSI')
 ok(all(cfg['Vulkan'][key] is False for key in ('vulkan_allow_present_mode_immediate','vulkan_allow_present_mode_mailbox','vulkan_allow_present_mode_fifo_relaxed')),'present mode flags match the user-tested mode')
 ok(not any((home/'cache').iterdir()),'clean fixture begins with an empty game cache')
 ok(os.path.samefile(cfg['Storage']['content_root'],p/'content'),'original content root retained')
 ok(not(home/'SyncToggle').exists(),'no NVIDIA profile state or watcher installed')
 run(p);ok(snap(p)==before,'repeat install accepts its native shortcut and leaves unrelated files unchanged')
 old_runtime=(home/'runtime/xenia_onechanbara.exe').read_bytes()
 (bundle/'xenia_onechanbara.exe').write_bytes(b'new candidate emulator fixture with a different SHA256')
 source=re.sub(r"(?m)^\$KnownRuntimeHash='[^']+'",lambda _:"$KnownRuntimeHash='"+h(bundle/'xenia_onechanbara.exe')+"'",source)
 (bundle/'Manage-Onechanbara.ps1').write_text(source,encoding='utf-8-sig')
 run(p)
 ok((home/'runtime/xenia_onechanbara.exe').read_bytes()!=old_runtime and h(home/'runtime/xenia_onechanbara.exe')==h(bundle/'xenia_onechanbara.exe'),'upgrade from prior direct runtime accepts the old receipt and installs the new executable')
 ok(snap(p)==before and json.loads((home/'install.json').read_text(encoding='utf-8-sig'))['ExeSha256']==h(bundle/'xenia_onechanbara.exe'),'runtime upgrade preserves originals and updates its hash receipt')
 prior=snap(p,True);priorlink=link.read_bytes();run(p,True)
 # Backups may be added, but every pre-existing file and shortcut must survive.
 ok(all(h(p/k)==v for k,v in prior.items()) and link.read_bytes()==priorlink,'failed update restores all prior managed files and shortcut')
 p=fixture('failed first');before=snap(p);run(p,True)
 ok(snap(p)==before and not(p/'config/OnechanbaraDirect').exists() and not(p/'desktop/오네찬바라.lnk').exists(),'failed new install removes incomplete output and preserves inputs')
 p=fixture('기존 자동 동기화',True);before=snap(p);previous_link=(p/'desktop/오네찬바라.lnk').read_bytes();run(p);home=p/'config/OnechanbaraDirect'
 ok(snap(p)==before,'migration from prior sync shortcut preserves old configs, runtime data, NVIDIA state, saves')
 ok((home/'xconfig.settings').read_bytes()==b'xconfig sentinel' and (home/'patches/own.patch.toml').is_file(),'existing isolated host settings and title patch preserved by copy')
 ok((home/'cache/shaders/shareable/445007D2.bin').read_bytes()==b'cached shader sentinel','existing game shader cache reused by copy')
 ok((home/'이전 실행 바로가기.lnk').read_bytes()==previous_link,'previous working shortcut retained as a separate exact backup')
(R/'install-validation.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'actual_production_install_script':True,'native_windows':False,'mocked':'COM shortcut API and original-emulator identity; real filesystem and production installer'},ensure_ascii=False,indent=2))
