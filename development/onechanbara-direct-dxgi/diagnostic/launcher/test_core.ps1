param([string]$LauncherPath=(Join-Path $PSScriptRoot 'Onechanbara_Diagnostics.exe'))
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform-ne[PlatformID]::Win32NT-or$PSVersionTable.PSEdition-ne'Desktop'){throw 'Run with Windows PowerShell 5.1 to test the shipped .NET Framework executable.'}
[void][Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $LauncherPath).Path)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$testRoot=Join-Path $PSScriptRoot ('tests/run_'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($testRoot)
$checks=[Collections.Generic.List[string]]::new()
function Check([bool]$ok,[string]$name){if(-not$ok){throw "FAIL: $name"};$checks.Add($name)}
function MustFail([scriptblock]$body,[string]$name){$failed=$false;try{&$body}catch{$failed=$true};Check $failed $name}
$inputConfig=Join-Path $PSScriptRoot '../../installer/source/Onechanbara.config.toml'
$source=[IO.File]::ReadAllText($inputConfig)
$sourceHash=[Onechanbara.Diagnostics.Core]::Hash($inputConfig)
foreach($mode in 0..2){
 $run=Join-Path $testRoot "mode_$mode";$cache=Join-Path $testRoot "cache_$mode";$content=Join-Path $testRoot '기존 저장';$log=Join-Path $run 'xenia.log'
 $actual=[Onechanbara.Diagnostics.Core]::BuildConfig($source,$run,$cache,$content,$log,$mode)
 foreach($pair in @(@('GPU','draw_resolution_scale_x','2'),@('GPU','draw_resolution_scale_y','2'),@('General','time_scalar','1'),@('GPU','vsync','true'),@('GPU','render_target_path_vulkan','"fsi"'),@('GPU','occlusion_query','"strict"'))){Check ([Onechanbara.Diagnostics.Core]::Value($actual,$pair[0],$pair[1])-ceq$pair[2]) "mode $mode preserves $($pair[1])"}
 foreach($key in 'vulkan_allow_present_mode_immediate','vulkan_allow_present_mode_mailbox','vulkan_allow_present_mode_fifo_relaxed'){Check ([Onechanbara.Diagnostics.Core]::Value($actual,'Vulkan',$key)-ceq'false') "mode $mode disables $key"}
 Check ([Onechanbara.Diagnostics.Core]::StringValue($actual,'Storage','content_root')-ceq$content) "mode $mode retains shared content path"
 Check ([Onechanbara.Diagnostics.Core]::StringValue($actual,'Storage','storage_root')-ceq$run) "mode $mode isolates storage"
 $args=[Onechanbara.Diagnostics.Core]::Args('E:\한글 경로\게임.iso',(Join-Path $run 'actual.config.toml'),$run,$cache,$content,$log,$mode)
 Check ($args.Contains('--onechanbara_diagnostics=true')) "mode $mode enables diagnostics"
 Check ($args.Contains('--onechanbara_guest_output='+$(if($mode-eq0){'true'}else{'false'}))) "mode $mode guest policy"
 Check ($args.Contains('--vulkan_direct_dxgi='+$(if($mode-eq2){'false'}else{'true'}))) "mode $mode output backend"
 [IO.File]::WriteAllText((Join-Path $testRoot "mode_$mode.toml"),$actual)
}
Check ([Onechanbara.Diagnostics.Core]::Hash($inputConfig)-ceq$sourceHash) 'original config byte hash unchanged'
MustFail {[Onechanbara.Diagnostics.Core]::BuildConfig($source.Replace('time_scalar = 1','time_scalar = 2'),$testRoot,$testRoot,$testRoot,(Join-Path $testRoot 'bad.log'),0)} 'nonstandard game time rejected without correction'
MustFail {[Onechanbara.Diagnostics.Core]::Value("[GPU]`nvsync = true`nvsync = false",'GPU','vsync')} 'duplicate setting rejected'
Check ([Onechanbara.Diagnostics.Core]::StringValue('[Storage]'+"`n"+'cache_root = "E:\\한글 # 경로\\cache" # comment','Storage','cache_root')-ceq'E:\한글 # 경로\cache') 'TOML escaped path and literal comment handling'
Check ([Onechanbara.Diagnostics.Core]::Q('E:\한글 경로\')-ceq'"E:\한글 경로\\"') 'Windows quote trailing slash'
MustFail {[Onechanbara.Diagnostics.Core]::Q('abc"def')} 'quote injection rejected'
$original=Join-Path $testRoot 'original-cache';[void][IO.Directory]::CreateDirectory($original);[IO.File]::WriteAllText((Join-Path $original 'shader.bin'),'shader sentinel')
$originalHash=[Onechanbara.Diagnostics.Core]::Hash((Join-Path $original 'shader.bin'))
$metadata=[Collections.Generic.Dictionary[string,object]]::new();$metadata.Add('Mode','fixture');$metadata.Add('Bytes',[long]15)
$snapshot=Join-Path $testRoot 'snapshot'
Check ([Onechanbara.Diagnostics.Core]::PrepareSnapshot($original,$snapshot,'seed.json',$metadata)) 'atomic snapshot created'
Check (-not[Onechanbara.Diagnostics.Core]::PrepareSnapshot($original,$snapshot,'seed.json',$metadata)) 'repeat snapshot reuses completed private copy'
[IO.File]::WriteAllText((Join-Path $snapshot 'data/shader.bin'),'runtime private cache update')
Check ([Onechanbara.Diagnostics.Core]::Hash((Join-Path $original 'shader.bin'))-ceq$originalHash) 'cache reuse never changes original source'
$read=[Onechanbara.Diagnostics.Core]::ReadJson((Join-Path $snapshot 'seed.json'));Check ($read['Mode']-ceq'fixture'-and$read['Bytes']-eq15) 'JSON metadata roundtrip'
MustFail {[Onechanbara.Diagnostics.Core]::CopyTree($original,(Join-Path $original 'nested'),$null)} 'copy overlap blocked'
MustFail {[Onechanbara.Diagnostics.Core]::CopyFile((Join-Path $original 'shader.bin'),(Join-Path $original 'shader.bin'))} 'original file overwrite blocked'
$link=Join-Path $testRoot 'cache-link';New-Item -ItemType Junction -Path $link -Target $original|Out-Null
MustFail {[Onechanbara.Diagnostics.Core]::SafePath($link)} 'reparse source blocked'
$badOriginal=Join-Path $testRoot 'bad-cache';[void][IO.Directory]::CreateDirectory($badOriginal);New-Item -ItemType Junction -Path (Join-Path $badOriginal 'escape') -Target $original|Out-Null
$badTarget=Join-Path $testRoot 'bad-snapshot'
MustFail {[Onechanbara.Diagnostics.Core]::PrepareSnapshot($badOriginal,$badTarget,'seed.json',$metadata)} 'failed snapshot does not publish incomplete cache'
Check (-not[IO.Directory]::Exists($badTarget)) 'failed preparation retry target remains free'
$zipRun=Join-Path $testRoot 'ziprun';[void][IO.Directory]::CreateDirectory($zipRun)
foreach($name in 'xenia.log','runmeta.json','actual.config.toml','trace.csv','game.iso','save.dat'){[IO.File]::WriteAllText((Join-Path $zipRun $name),'fixture')}
$zip=[Onechanbara.Diagnostics.Core]::ZipRun($zipRun)
$archive=[IO.Compression.ZipFile]::OpenRead($zip);try{$names=@($archive.Entries.FullName);Check ($names.Count-eq4-and'game.iso'-notin$names-and'save.dat'-notin$names) 'ZIP excludes ISO and save data'}finally{$archive.Dispose()}
$zipRun2=Join-Path $testRoot 'ziprun2';[void][IO.Directory]::CreateDirectory($zipRun2);[IO.File]::WriteAllText((Join-Path $zipRun2 'xenia.log'),'second run');[IO.File]::WriteAllText((Join-Path $zipRun2 'game.iso'),'never include')
$combined=[Onechanbara.Diagnostics.Core]::ZipRuns(@($zipRun,$zipRun2),(Join-Path $testRoot 'combined.zip'))
$archive=[IO.Compression.ZipFile]::OpenRead($combined);try{$names=@($archive.Entries.FullName);Check ('ziprun/xenia.log'-in$names-and'ziprun2/xenia.log'-in$names-and'comparison-runs.txt'-in$names) 'combined ZIP includes all launcher session runs';Check (-not($names|Where-Object{$_-like'*.iso'-or$_-like'*.dat'})) 'combined ZIP excludes ISO/save/cache data'}finally{$archive.Dispose()}
$receiptDir=Join-Path $testRoot '한글 공백 설치/config/OnechanbaraDirect';[void][IO.Directory]::CreateDirectory($receiptDir)
$r=[Collections.Generic.Dictionary[string,object]]::new();$r.Add('Owner','Onechanbara.445007D2.DirectDXGI');$r.Add('ContentMode','OriginalSharedContent');[Onechanbara.Diagnostics.Core]::WriteJson((Join-Path $receiptDir 'install.json'),$r)
Check ([Onechanbara.Diagnostics.Core]::FindReceipt((Join-Path $testRoot '한글 공백 설치/unpacked/launcher'))-ceq(Join-Path $receiptDir 'install.json')) 'automatic parent root receipt discovery'
$manifest=[Collections.Generic.Dictionary[string,object]]::new();$manifest.Add('display_revision','diagnostic-output-1');$manifest.Add('exe_sha256',('a'*64));[Onechanbara.Diagnostics.Core]::WriteJson((Join-Path $testRoot 'build.json'),$manifest)
Check ([Onechanbara.Diagnostics.Core]::RuntimeHash((Join-Path $testRoot 'build.json'))-ceq('a'*64)) 'runtime lower-case exe_sha256 schema supported'
[ordered]@{passed=$checks.Count;checks=$checks;actual_code_executed='Shipped Onechanbara_Diagnostics.exe via Windows PowerShell 5.1 .NET Framework';runtime=[Environment]::Version.ToString();native_windows_gui=$false;gpu_execution=$false}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'test-results.json') -Encoding utf8
Write-Output "Passed $($checks.Count) checks; GUI/GPU were not executed."
