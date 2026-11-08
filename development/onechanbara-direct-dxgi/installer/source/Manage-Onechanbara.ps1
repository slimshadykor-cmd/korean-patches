[CmdletBinding()]
param(
 [ValidateSet('Check','Install')][string]$Mode='Check',
 [string]$Root='', [string]$GamePath='', [string]$GameSha256='',
 [string]$DesktopPath='', [string]$TemplatePath='', [switch]$NoUI,
 [ValidateSet('Ask','Original','Private')][string]$SaveChoice='Ask', [switch]$AllowSavePrompt
)
Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$Version='1.7'
$ToolRevision='1.7'
$Owner='Onechanbara.445007D2.DirectDXGI'
$KnownExeHash='64AC262FE55E0E252FA46CEBAE006978AFA48BB109996E1304F3F64EEB9D4932'
$RuntimeSource=Join-Path $PSScriptRoot 'xenia_onechanbara.exe'
$LauncherSource=Join-Path $PSScriptRoot 'Onechanbara_Launcher.exe'
$KnownRuntimeHash='13929E0D0AD3FDD3FEC7E7359DCEAEFA35165038CC46EE018A93FA86D0150CCC'
$KnownLauncherHash='160534A30A3F66FE760CC8A8178A093B04E2923CE53048D8DA4E4F5075C6E113'
$Utf8=New-Object Text.UTF8Encoding($true)
$Stage='';$Committed=$false;$GameLock=$null;$RunLock=$null;$SetupLock=$null
$OriginalContent='';$ProfileIds=@()
$SaveStamp=(Get-Date -Format 'yyyyMMdd_HHmmss_fff')+'_'+[Guid]::NewGuid().ToString('N').Substring(0,8)
try {[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)} catch {}
function Hash([string]$p) {return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function No-Link([string]$p) {
 $p=[IO.Path]::GetFullPath($p)
 while($p){
  if(Test-Path -LiteralPath $p){if(([IO.File]::GetAttributes($p) -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('연결된 경로는 사용하지 않습니다: '+$p)}}
  $q=[IO.Path]::GetDirectoryName($p);if($q -eq $p){break};$p=$q
 }
}
function Closed {
 if(@(Get-Process -Name 'xenia*','ocb17_*' -ErrorAction SilentlyContinue).Count){throw '제니아를 모두 종료한 뒤 진행하세요. 실행 중인 게임은 강제로 종료하지 않습니다.'}
}
function Quote([string]$s) {
 if($s.IndexOfAny([char[]]@('"',"`r","`n",[char]0)) -ge 0){throw '지원하지 않는 경로 문자입니다.'}
 $tail='';if($s -match '(\\+)$'){$tail=$Matches[1]}
 return '"'+$s+$tail+'"'
}
function Read-Text([string]$p) {return [IO.File]::ReadAllText($p).TrimStart([char]0xFEFF)}
function Value([string]$text,[string]$section,[string]$key,[string]$fallback='') {
 $inside=$false;$found=@();$count=0
 foreach($line in ($text -split '\r?\n')){
  if($line -match '^\s*\[([^\]]+)\]\s*(?:#.*)?$'){$inside=($Matches[1] -ceq $section);if($inside){$count++};continue}
  if($inside -and $line -match ('^\s*'+[regex]::Escape($key)+'\s*=\s*([^#]*?)(?:\s*#.*)?$')){$found+=$Matches[1].Trim()}
 }
 if($count -gt 1 -or $found.Count -gt 1){throw ('중복 설정: '+$section+'.'+$key)}
 if($found.Count){return [string]$found[0]};return $fallback
}
function Set-Value([string]$text,[string]$section,[string]$key,[string]$value) {
 [void](Value $text $section $key)
 $lines=New-Object 'System.Collections.Generic.List[string]'
 foreach($line in ($text -split '\r?\n')){$lines.Add($line)}
 $start=-1;$end=$lines.Count
 for($i=0;$i -lt $lines.Count;$i++){
  if($lines[$i] -match '^\s*\[([^\]]+)\]\s*(?:#.*)?$'){
   if($start -ge 0){$end=$i;break};if($Matches[1] -ceq $section){$start=$i}
  }
 }
 if($start -lt 0){$lines.Add('');$lines.Add('['+$section+']');$lines.Add($key+' = '+$value)}
 else {
  $done=$false
  for($i=$start+1;$i -lt $end;$i++){if($lines[$i] -match ('^\s*'+[regex]::Escape($key)+'\s*=')){$lines[$i]=$key+' = '+$value;$done=$true;break}}
  if(-not $done){$lines.Insert($end,$key+' = '+$value)}
 }
 return ($lines -join "`r`n")
}
function Toml-String([string]$s) {return '"'+$s.Replace('\','\\').Replace('"','\"')+'"'}
function String-Value([string]$text,[string]$section,[string]$key) {
 $v=Value $text $section $key '""'
 if($v -match "^'([^']*)'$"){return $Matches[1]}
 if($v -notmatch '^"((?:[^"\\]|\\[\\"/])*)"$'){throw ('저장 경로 형식을 확인할 수 없습니다: '+$key)}
 return [regex]::Replace($Matches[1],'\\([\\"/])','$1')
}
function Copy-File([string]$a,[string]$b) {
 No-Link $a;No-Link $b
 [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($b))
 [IO.File]::Copy($a,$b,$false)
 [IO.File]::SetAttributes($b,[IO.FileAttributes]::Normal)
 if((Hash $a) -ne (Hash $b)){throw '전용 파일 복사 검증 실패'}
}
function Copy-Tree([string]$a,[string]$b) {
 if(-not [IO.Directory]::Exists($a)){return};No-Link $a
 foreach($f in Get-ChildItem -LiteralPath $a -Force){
  No-Link $f.FullName;$dest=Join-Path $b $f.Name
  if($f.PSIsContainer){Copy-Tree $f.FullName $dest}else{Copy-File $f.FullName $dest}
 }
}
function Snapshot {
 $result=@{}
 foreach($p in @($SourceExe,(Join-Path $Root 'xenia-canary.config.toml'))){if([IO.File]::Exists($p)){$result[$p]=(Hash $p)+'|'+[int][IO.File]::GetAttributes($p)}}
 if([IO.Directory]::Exists((Join-Path $Root 'config'))){
  foreach($f in Get-ChildItem -LiteralPath (Join-Path $Root 'config') -Filter '*.toml' -File -Recurse -Force){
   if($f.FullName.StartsWith($PrivateRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){continue}
   if($Stage -ne '' -and $f.FullName.StartsWith($Stage+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){continue}
   No-Link $f.FullName;$result[$f.FullName]=(Hash $f.FullName)+'|'+[int]$f.Attributes
  }
 }
 return $result
}
function Assert-Snapshot($before) {
 $after=Snapshot
 if($before.Count -ne $after.Count){throw '다른 설정 파일 구성이 변경됐습니다. 자동 덮어쓰기는 하지 않았습니다.'}
 foreach($k in $before.Keys){if(-not $after.ContainsKey($k) -or $before[$k] -cne $after[$k]){throw ('다른 파일 변경 감지: '+$k)}}
}
function Read-Receipt {
 if(-not [IO.File]::Exists($Receipt)){throw '전용 실행 연결 기록이 없습니다. 패치 프로그램에서 다시 연결하세요.'}
 $r=(Read-Text $Receipt)|ConvertFrom-Json
 if($r.Owner -cne $Owner -or @('1.6.0','1.6.1',$Version) -notcontains $r.Version){throw '지원하지 않는 전용 폴더입니다. 기존 내용을 덮어쓰지 않았습니다.'}
 return $r
}
function Settings([string]$text) {
 foreach($key in @('load_module_map','trace_function_data_path')){$text=Set-Value $text 'CPU' $key '""'}
 foreach($key in @('dump_translated_hir_functions','trace_function_coverage','trace_function_data','trace_function_references','trace_functions')){$text=Set-Value $text 'CPU' $key 'false'}
 foreach($key in @('launch_module','notification_sound_path')){$text=Set-Value $text 'General' $key '""'}
 foreach($x in @(@('gpu','"vulkan"'),@('render_target_path_vulkan','"fsi"'),@('occlusion_query','"strict"'),@('draw_resolution_scale_x','2'),@('draw_resolution_scale_y','2'),@('vsync','true'),@('framerate_limit','0'))){$text=Set-Value $text 'GPU' $x[0] $x[1]}
 $text=Set-Value $text 'General' 'time_scalar' '1'
$text=Set-Value $text 'Vulkan' 'vulkan_direct_dxgi' 'true'
 foreach($x in @(@('storage_root',$PrivateRoot),@('content_root',$OriginalContent),@('cache_root',(Join-Path $PrivateRoot 'cache')))){$text=Set-Value $text 'Storage' $x[0] (Toml-String $x[1])}
 $text=Set-Value $text 'Logging' 'log_file' (Toml-String (Join-Path $PrivateRoot 'logs/xenia.log'))
 $text=Set-Value $text 'General' 'recent_titles_entry_amount' '0'
 foreach($key in @('dump_shaders','target_trace_file','trace_dump_path')){$text=Set-Value $text 'GPU.Debug' $key '""'}
 $text=Set-Value $text 'GPU.Debug' 'trace_gpu_prefix' (Toml-String (Join-Path $PrivateRoot 'scratch/gpu/'))
 $text=Set-Value $text 'GPU.Debug' 'trace_gpu_stream' 'false'
 $text=Set-Value $text 'GPU.Debug' 'store_shaders' 'true'
 $text=Set-Value $text 'UI' 'custom_font_path' '""'
 $async=Value $text 'GPU' 'async_shader_compilation' 'false'
 if(@('true','false') -notcontains $async){throw '셰이더 설정 형식이 올바르지 않습니다.'}
 $text=Set-Value $text 'GPU' 'async_shader_compilation' $async
 return $text
}
function Same-Location([string]$actual,[string]$expected) {
 if([string]::IsNullOrWhiteSpace($actual) -or [string]::IsNullOrWhiteSpace($expected)){return $false}
 $a=$actual.Replace('/','\').TrimEnd('\')
 $b=$expected.Replace('/','\').TrimEnd('\')
 return [string]::Equals($a,$b,[StringComparison]::OrdinalIgnoreCase)
}
function Check-PrivateSettings([string]$text) {
 foreach($x in @(@('gpu','"vulkan"'),@('render_target_path_vulkan','"fsi"'),@('occlusion_query','"strict"'),@('vsync','true'))){if((Value $text 'GPU' $x[0]) -cne $x[1]){throw ('전용 설정 확인 필요: '+$x[0])}}
 if((Value $text 'General' 'time_scalar') -cne '1' -or (Value $text 'GPU' 'framerate_limit') -cne '0'){throw '게임 속도 설정이 기준값과 다릅니다. 패치 프로그램의 전용 실행 연결로 기준값을 다시 적용하세요.'}
 foreach($x in @(@('storage_root',$PrivateRoot),@('content_root',$OriginalContent),@('cache_root',(Join-Path $PrivateRoot 'cache')))){
  if(-not (Same-Location (String-Value $text 'Storage' $x[0]) $x[1])){throw '전용 저장 경로가 변경되었습니다. 다른 폴더에 기록하지 않도록 중단합니다.'}
 }
 foreach($key in @('dump_shaders','target_trace_file','trace_dump_path')){if((String-Value $text 'GPU.Debug' $key) -ne ''){throw '외부 출력 경로가 지정되어 실행을 중단합니다.'}}
 foreach($key in @('load_module_map','trace_function_data_path')){if((String-Value $text 'CPU' $key) -ne ''){throw '외부 분석 경로가 지정되어 있습니다.'}}
 if((String-Value $text 'General' 'launch_module') -ne ''){throw '외부 실행 모듈이 지정되어 있습니다.'}
 if(-not (Same-Location (String-Value $text 'GPU.Debug' 'trace_gpu_prefix') (Join-Path $PrivateRoot 'scratch/gpu/'))){throw '전용 추적 경로가 변경되었습니다.'}
 if((String-Value $text 'UI' 'custom_font_path') -ne ''){throw '외부 글꼴 경로가 지정되어 있습니다.'}
 if([IO.Directory]::Exists((Join-Path $PrivateRoot 'config')) -and @(Get-ChildItem -LiteralPath (Join-Path $PrivateRoot 'config') -Recurse -File -Filter '*.toml').Count){throw '전용 폴더 안에 추가 게임 설정이 있습니다. 설정 중복 적용을 막기 위해 중단합니다.'}
}
function Original-Content {
 # Xenia b083312b8 Windows defaults portable=true, even without portable.txt.
 $storage=$Root
 $text='';$common=Join-Path $storage 'xenia-canary.config.toml'
 if([IO.File]::Exists($common)){No-Link $common;$text=Read-Text $common}
 # storage_root is chosen before SetupConfig, and per-title settings load after ContentManager.
 $content=String-Value $text 'Storage' 'content_root'
 if($content -eq ''){$content=Join-Path $storage 'content'}elseif(-not [IO.Path]::IsPathRooted($content)){$content=Join-Path $storage $content}
 $content=[IO.Path]::GetFullPath($content);No-Link $content
 if($content.TrimEnd([char[]]@('/','\')) -ieq $PrivateRoot -or $content.StartsWith($PrivateRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw '원래 저장 위치가 전용 폴더를 가리킵니다. 원본을 추측하여 덮어쓰지 않았습니다.'}
 return $content
}

# The emulator uses the existing content root directly. No profile or save copying.
function Tree-Safe([string]$p) {
 No-Link $p
 if([IO.Directory]::Exists($p)){foreach($f in Get-ChildItem -LiteralPath $p -Force){if($f.PSIsContainer){Tree-Safe $f.FullName}else{No-Link $f.FullName}}}
}
function Read-OriginalProfiles {
 No-Link $OriginalContent
 if(-not [IO.Directory]::Exists($OriginalContent)){throw ('기존 제니아 content 폴더가 없습니다: '+$OriginalContent)}
 $ids=@()
 foreach($dir in Get-ChildItem -LiteralPath $OriginalContent -Directory -Force){
  if($dir.Name -notmatch '^[0-9A-Fa-f]{16}$' -or $dir.Name -eq '0000000000000000'){continue}
  No-Link $dir.FullName
  $account=Join-Path $dir.FullName ('FFFE07D1/00010000/'+$dir.Name)
  if([IO.File]::Exists($account)){No-Link $account;$ids+=$dir.Name}
  elseif([IO.File]::Exists((Join-Path $account 'Account'))){Tree-Safe (Join-Path $dir.FullName 'FFFE07D1');$ids+=$dir.Name}
 }
 if($ids.Count -eq 0){throw ('기존 제니아 프로필을 찾지 못했습니다. 새 프로필은 만들지 않았습니다. 확인한 위치: '+$OriginalContent)}
 return $ids
}
function Profile-Settings([string]$text,[bool]$autoSelect) {
 $active=0
 foreach($slot in 0..3){
  $key='logged_profile_slot_'+$slot+'_xuid';$id=String-Value $text 'Profiles' $key
  if($id -ne ''){
   if($id -notmatch '^[0-9A-Fa-f]{16}$' -or $ProfileIds -notcontains $id){throw ('기존 위치에서 해당 로그인 프로필을 찾지 못했습니다: '+$id+' / '+$OriginalContent+' — 프로필을 복사하거나 새로 만들지 않고 중단했습니다.')}
   $active++
  }
 }
 if($autoSelect -and $active -eq 0 -and $ProfileIds.Count -eq 1){$text=Set-Value $text 'Profiles' 'logged_profile_slot_0_xuid' (Toml-String ([string]$ProfileIds[0]))}
 return $text
}
function Validate-ManagedTree {
 # Legacy content and save_backups are retained, unused and never traversed/migrated.
 foreach($name in @('runtime','cache','logs','patches','config','scratch')){Tree-Safe (Join-Path $PrivateRoot $name)}
 foreach($name in @('Onechanbara.config.toml','Manage-Onechanbara.ps1','install.json','Onechanbara.ico','gamecontrollerdb.txt','xconfig.settings','session.lock','launch_data.bin')){No-Link (Join-Path $PrivateRoot $name)}
}
function Import-OwnRuntimeData([string]$text) {
 $cache=String-Value $text 'Storage' 'cache_root'
 if($cache -eq ''){$cache=Join-Path $Root 'cache_host'}elseif(-not [IO.Path]::IsPathRooted($cache)){$cache=Join-Path $Root $cache}
 foreach($rel in @('shaders/shareable/445007D2','shaders/local/445007D2','445007D2')){Copy-Tree (Join-Path $cache $rel) (Join-Path $Stage ('cache/'+$rel))}
 foreach($rel in @('shaders/shareable','shaders/local')){
  $dir=Join-Path $cache $rel
  if([IO.Directory]::Exists($dir)){No-Link $dir;foreach($f in Get-ChildItem -LiteralPath $dir -File -Force){if($f.Name -match '^445007D2(?:\.|$)'){Copy-File $f.FullName (Join-Path $Stage ('cache/'+$rel+'/'+$f.Name))}}}
 }
 $patches=Join-Path $LegacyRoot 'patches'
 if(-not[IO.Directory]::Exists($patches)){$patches=Join-Path $Root 'patches'}
 $oldXconfig=Join-Path $LegacyRoot 'xconfig.settings'
 if([IO.File]::Exists($oldXconfig)){Copy-File $oldXconfig (Join-Path $Stage 'xconfig.settings')}
 if([IO.Directory]::Exists($patches)){
  No-Link $patches
  foreach($f in Get-ChildItem -LiteralPath $patches -File -Recurse -Filter '*.patch.toml'){
   No-Link $f.FullName;$ptext=Read-Text $f.FullName
   $ids=@([regex]::Matches($ptext,'(?im)^\s*title_id\s*=\s*["'']([0-9A-F]{8})["'']')|ForEach-Object {$_.Groups[1].Value.ToUpperInvariant()}|Select-Object -Unique)
   if($ids.Count -eq 1 -and $ids[0] -eq '445007D2'){
    $relative=$f.FullName.Substring($patches.Length).TrimStart([char[]]@('/','\'))
    Copy-File $f.FullName (Join-Path $Stage ('patches/'+$relative))
   }
  }
 }
 $mapping=String-Value $text 'SDL' 'mappings_file'
 if($mapping -ne ''){
  if(-not [IO.Path]::IsPathRooted($mapping)){if([IO.File]::Exists((Join-Path $LegacyRoot $mapping))){$mapping=Join-Path $LegacyRoot $mapping}else{$mapping=Join-Path $Root $mapping}}
  if([IO.File]::Exists($mapping)){Copy-File $mapping (Join-Path $Stage 'gamecontrollerdb.txt')}
  $text=Set-Value $text 'SDL' 'mappings_file' '"gamecontrollerdb.txt"'
 }
 return $text
}

function Write-GameIcon([string]$p) {
 [IO.File]::WriteAllBytes($p,[Convert]::FromBase64String('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'))
 if((Hash $p) -cne '2448D26A821549DD58263C9F56707F241DA1A442F0192BA7F201744B5C5D8763'){throw '게임 아이콘 저장 확인 실패'}
}
function Shell {return New-Object -ComObject WScript.Shell}
function Check-Link($shell,[string]$link) {
 if(-not [IO.File]::Exists($link)){return};No-Link $link;$old=$shell.CreateShortcut($link)
 $a=[string]$old.Arguments;$t=[string]$old.TargetPath
 $known=@((Join-Path $PrivateRoot 'Manage-Onechanbara.ps1'),(Join-Path $Root 'config/_onechanbara_preserve/Manage-XeniaSettings.ps1'))
 $syncReceipt=Join-Path $LegacyRoot 'SyncToggle/installed.json'
 if([IO.File]::Exists($syncReceipt)){
  No-Link $syncReceipt;$sync=Read-Text $syncReceipt|ConvertFrom-Json
  if($sync.Owner-ceq'Onechanbara.SyncLauncher.1'-and$sync.Build-notmatch '[^0-9a-f]'-and$sync.Build.Length-eq64){
   $expected=Join-Path $LegacyRoot ('SyncToggle/Launcher/'+$sync.Build+'/Sync-Toggle.ps1')
   if([string]$sync.Entry-ceq$expected){$known+=$expected}
  }
 }
 $owned=($t-ieq$NativeLauncher -and $a-eq'')
 $known+=(Join-Path $LegacyRoot 'Manage-Onechanbara.ps1')
 foreach($p in $known){if($t -ieq $PowerShell -and $a.IndexOf(('"'+$p+'"'),[StringComparison]::OrdinalIgnoreCase) -ge 0){$owned=$true}}
 if(-not $owned){throw '같은 이름의 다른 바로가기가 있습니다. 덮어쓰지 않았습니다.'}
}
try {
 if($Root -eq ''){throw '제니아 실행파일 위치가 필요합니다.'}
 $Root=[IO.Path]::GetFullPath($Root);No-Link $Root
 $LegacyRoot=Join-Path $Root 'config/Onechanbara'
 $PrivateRoot=Join-Path $Root 'config/OnechanbaraDirect';No-Link $PrivateRoot
 $SourceExe=Join-Path $Root 'xenia_canary.exe'
 $PrivateExe=Join-Path $PrivateRoot 'runtime/xenia_onechanbara.exe'
 $NativeLauncher=Join-Path $PrivateRoot 'Onechanbara_Launcher.exe'
 $Config=Join-Path $PrivateRoot 'Onechanbara.config.toml'
 $Receipt=Join-Path $PrivateRoot 'install.json'
 $Runner=Join-Path $PrivateRoot 'Manage-Onechanbara.ps1'
 $GameIcon=Join-Path $PrivateRoot 'Onechanbara.ico'
 $PowerShell=Join-Path $env:WINDIR 'System32/WindowsPowerShell/v1.0/powershell.exe'
 Closed
 if($Mode -ne 'Run'){
  No-Link $SourceExe
  if(-not [IO.File]::Exists($SourceExe) -or (Hash $SourceExe) -cne $KnownExeHash){throw '전용 실행은 검증한 Xenia Canary b083312b8 빌드가 필요합니다. 원본 실행파일은 수정하지 않습니다.'}
  if([IO.Directory]::Exists($PrivateRoot)){[void](Read-Receipt)}
  if($Mode -eq 'Check'){Write-Host '확인 통과. 기존 프로필과 저장 위치를 사용하며 공용 설정·원본 실행파일은 수정하지 않습니다.';exit 0}
 }
 $before=Snapshot
 if($Mode -eq 'Install'){
  if((Hash $RuntimeSource)-cne$KnownRuntimeHash -or (Hash $LauncherSource)-cne$KnownLauncherHash){throw '내장 실행파일 검증 실패'}
  $syncWork=Join-Path $LegacyRoot 'SyncToggle';No-Link $syncWork
  if([IO.File]::Exists((Join-Path $syncWork 'active.lock'))){
   $syncLock=Join-Path $syncWork 'active.lock';No-Link $syncLock
   try{$SetupLock=[IO.File]::Open($syncLock,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}catch{throw '동기화 실행 또는 종료 처리 중이므로 설치를 시작하지 않았습니다.'}
  }
  if(-not [IO.File]::Exists($GamePath) -or $GameSha256 -notmatch '^[0-9A-Fa-f]{64}$'){throw '완성된 한글 ISO를 선택하세요.'}
  $GamePath=[IO.Path]::GetFullPath($GamePath);No-Link $GamePath
  if((Hash $GamePath) -ine $GameSha256){throw '등록할 한글 ISO가 검사 이후 변경되었습니다.'}
  if($DesktopPath -eq ''){$DesktopPath=[Environment]::GetFolderPath('DesktopDirectory')}
  if(-not [IO.Directory]::Exists($DesktopPath)){throw '바탕화면 폴더를 찾을 수 없습니다.'}
  $link=Join-Path $DesktopPath '오네찬바라.lnk';$shell=Shell;Check-Link $shell $link
  $existing=[IO.Directory]::Exists($PrivateRoot)
  $oldLinkBytes=$null;if([IO.File]::Exists($link)){$oldLinkBytes=[IO.File]::ReadAllBytes($link)}
  $OriginalContent=Original-Content
  $ProfileIds=@(Read-OriginalProfiles)
  $settingsSource='included';$settingsText=''
  if($existing){
   $previous=Read-Receipt;Validate-ManagedTree
   if(-not [IO.File]::Exists($PrivateExe) -or (Hash $PrivateExe) -cne [string]$previous.ExeSha256){throw '전용 제니아 실행파일이 없거나 변경됐습니다. 기존 내용을 덮어쓰지 않았습니다.'}
   if(-not [IO.File]::Exists($Config)){throw '기존 전용 설정이 없습니다. 기존 폴더를 백업한 뒤 새로 연결하세요.'}
   $settingsText=Read-Text $Config;$settingsSource='existing isolated graphics'
  }else{
   $legacy=Join-Path $LegacyRoot 'Onechanbara.config.toml'
   if(-not[IO.File]::Exists($legacy)){$legacy=Join-Path $Root 'config/445007D2.config.toml'}
   if([IO.File]::Exists($legacy)){No-Link $legacy;$settingsText=Read-Text $legacy;$settingsSource='existing Onechanbara graphics'}
   elseif([IO.File]::Exists($TemplatePath)){$settingsText=Read-Text $TemplatePath}else{throw '내장 전용 설정이 없습니다.'}
  }
  $settingsText=Profile-Settings $settingsText $true
  $Stage=Join-Path ([IO.Path]::GetDirectoryName($PrivateRoot)) ('Onechanbara_install_'+[Guid]::NewGuid().ToString('N'))
  [void][IO.Directory]::CreateDirectory($Stage)
  if(-not $existing){
   $settingsText=Import-OwnRuntimeData $settingsText
   # The original emulator is never copied over or modified.
   foreach($name in @('cache','logs')){[void][IO.Directory]::CreateDirectory((Join-Path $Stage $name))}
  }
  Copy-File $RuntimeSource (Join-Path $Stage 'runtime/xenia_onechanbara.exe')
  Copy-File $LauncherSource (Join-Path $Stage 'Onechanbara_Launcher.exe')
  if(-not $existing -and $null-ne$oldLinkBytes){[IO.File]::WriteAllBytes((Join-Path $Stage '이전 실행 바로가기.lnk'),$oldLinkBytes)}
  $newText=Settings $settingsText
  Check-PrivateSettings $newText
  [IO.File]::WriteAllText((Join-Path $Stage 'Onechanbara.config.toml'),$newText,$Utf8)
  [IO.File]::Copy($PSCommandPath,(Join-Path $Stage 'Manage-Onechanbara.ps1'),$false)
  Write-GameIcon (Join-Path $Stage 'Onechanbara.ico')
  $info=Get-Item -LiteralPath $GamePath
  $r=[ordered]@{Owner=$Owner;Version=$Version;ToolRevision=$ToolRevision;GamePath=$GamePath;GameSha256=$GameSha256.ToUpperInvariant();GameLength=$info.Length;GameWriteUtcTicks=$info.LastWriteTimeUtc.Ticks.ToString();ExeSha256=$KnownRuntimeHash;SettingsSource=$settingsSource;OriginalContentRoot=$OriginalContent;ContentMode='OriginalSharedContent';Profiles=$ProfileIds;Created=(Get-Date -Format 'o')}
  [IO.File]::WriteAllText((Join-Path $Stage 'install.json'),($r|ConvertTo-Json -Depth 8),$Utf8)
  Closed;Assert-Snapshot $before
  $undo=@{}
  try {
   if($existing){
    $backupRoot=Join-Path $PrivateRoot ('setup_backups/'+(Get-Date -Format 'yyyyMMdd_HHmmss_fff')+'_'+[Guid]::NewGuid().ToString('N').Substring(0,8));No-Link $backupRoot
    foreach($name in @('Onechanbara.config.toml','Manage-Onechanbara.ps1','install.json','Onechanbara.ico','runtime/xenia_onechanbara.exe','Onechanbara_Launcher.exe')){
     $p=Join-Path $PrivateRoot $name;No-Link $p;$undo[$name]=$null
     if([IO.File]::Exists($p)){$undo[$name]=[IO.File]::ReadAllBytes($p);Copy-File $p (Join-Path $backupRoot $name)}
    }
    foreach($name in $undo.Keys){[IO.File]::Copy((Join-Path $Stage $name),(Join-Path $PrivateRoot $name),$true)}
   }else{[IO.Directory]::Move($Stage,$PrivateRoot);$Stage=''}
   Validate-ManagedTree
   $new=$shell.CreateShortcut($link);$new.TargetPath=$NativeLauncher
   $new.Arguments=''
   $new.WorkingDirectory=$PrivateRoot;$new.IconLocation=$GameIcon+',0';$new.Description='오네찬바라 한글판 v1.7 · 기존 프로필 · 전용 그래픽';$new.WindowStyle=7;$new.Save()
   $check=$shell.CreateShortcut($link)
   if($check.TargetPath -ine $NativeLauncher -or $check.Arguments -cne $new.Arguments -or $check.IconLocation -ine $new.IconLocation -or $check.WorkingDirectory -ine $PrivateRoot){throw '바탕화면 바로가기 저장 확인 실패'}
   # No NVIDIA profiles are created, edited or removed.
   Assert-Snapshot $before;$Committed=$true
  }catch{
   if($existing){foreach($name in $undo.Keys){$p=Join-Path $PrivateRoot $name;if($null -eq $undo[$name]){if([IO.File]::Exists($p)){[IO.File]::Delete($p)}}else{[IO.File]::WriteAllBytes($p,$undo[$name])}}}
   elseif([IO.Directory]::Exists($PrivateRoot)){[IO.Directory]::Delete($PrivateRoot,$true)}
   if($null -ne $oldLinkBytes){[IO.File]::WriteAllBytes($link,$oldLinkBytes)}elseif([IO.File]::Exists($link)){[IO.File]::Delete($link)}
   throw
  }
  Write-Host '완료: 기존 프로필과 저장 위치를 사용하는 바탕화면 오네찬바라 바로가기를 연결했습니다.'
  Write-Host ('프로필·세이브·의상·DLC 위치: '+$OriginalContent)
  Write-Host '프로필 복사·생성, 세이브 이동, 저장 폴더 연결은 수행하지 않았습니다.'
  Write-Host '공용 설정·원본 실행파일·다른 게임 파일은 수정하지 않았습니다.'
  if($existing -and [IO.Directory]::Exists((Join-Path $PrivateRoot 'content'))){Write-Host '이전 전용 content 폴더는 사용하지 않으며, 복구 자료로 그대로 남겨두었습니다. 자동 합치기나 삭제는 하지 않았습니다.'}
  exit 0
 }
 throw '바탕화면 바로가기로 실행하세요.'
}catch{
 $message=$_.Exception.Message;Write-Host ('중단: '+$message)
 if(-not $NoUI){try{Add-Type -AssemblyName System.Windows.Forms;[void][Windows.Forms.MessageBox]::Show($message,'오네찬바라 확인 필요')}catch{}}
 exit 1
}finally{
 if($null -ne $GameLock){$GameLock.Dispose()};if($null -ne $RunLock){$RunLock.Dispose()}
 if($null -ne $SetupLock){$SetupLock.Dispose()}
 if($Stage -ne '' -and [IO.Directory]::Exists($Stage)){[IO.Directory]::Delete($Stage,$true)}
}
