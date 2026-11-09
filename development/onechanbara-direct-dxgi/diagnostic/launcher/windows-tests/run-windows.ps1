$ErrorActionPreference='Stop'
if ($PSVersionTable.PSEdition -ne 'Desktop' -or $PSVersionTable.PSVersion.Major -ne 5) { throw 'Run this script using Windows PowerShell 5.1 (.NET Framework).' }
$launcher=Split-Path $PSScriptRoot -Parent
$out=Join-Path $launcher 'windows-build'
[void][IO.Directory]::CreateDirectory($out)
$csc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$references=@('/r:System.dll','/r:System.Core.dll','/r:System.Drawing.dll','/r:System.Windows.Forms.dll','/r:System.IO.Compression.dll','/r:System.IO.Compression.FileSystem.dll','/r:System.Runtime.Serialization.dll','/r:System.Web.Extensions.dll','/r:System.Xml.dll')
$exe=Join-Path $out 'Onechanbara_Diagnostics.exe'
& $csc /nologo /codepage:65001 /target:winexe /platform:x64 /optimize+ "/out:$exe" "/win32manifest:$(Join-Path $launcher 'app.manifest')" $references (Join-Path $launcher 'DiagnosticCore.cs') (Join-Path $launcher 'DiagnosticLauncher.cs') (Join-Path $launcher 'AssemblyInfo.cs')
if ($LASTEXITCODE -ne 0) { throw 'Production .NET Framework launcher compile failed.' }
$fake=Join-Path $PSScriptRoot 'FakeRuntime.exe'
& $csc /nologo /codepage:65001 /target:exe /platform:x64 /optimize+ "/out:$fake" $references (Join-Path $PSScriptRoot 'FakeRuntime.cs')
if ($LASTEXITCODE -ne 0) { throw 'Fixture executable compile failed.' }
$test=Join-Path $out 'WindowsRegression.exe'
& $csc /nologo /codepage:65001 /target:exe /platform:x64 /optimize+ "/out:$test" "/r:$exe" $references (Join-Path $PSScriptRoot 'WindowsRegression.cs')
if ($LASTEXITCODE -ne 0) { throw 'Windows regression harness compile failed.' }
[ordered]@{Owner='Onechanbara.445007D2.DirectDXGI';Version='1.7';ContentMode='OriginalSharedContent';GamePath='E:\한글 공백\게임.iso';GameLength=[long]8589934592;GameWriteUtcTicks='638982503999999999';Profiles=@('A','B');Flag=$true;Missing=$null}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'powershell51-receipt.json') -Encoding UTF8
$result=Join-Path $out 'Windows-test-results.json'
$testRoot=Join-Path $env:RUNNER_TEMP ('Onechanbara-진단 공백-'+[Guid]::NewGuid().ToString('N'))
& $test $testRoot $PSScriptRoot $result
if ($LASTEXITCODE -ne 0) { if(Test-Path $result){Get-Content -Raw $result}; throw 'Windows regression execution failed.' }
& (Join-Path $launcher 'test_core.ps1') -LauncherPath $exe
& (Join-Path $launcher 'test_runtime_layout.ps1') -LauncherPath $exe
Copy-Item -LiteralPath (Join-Path $launcher 'test-results.json') -Destination $out
Copy-Item -LiteralPath (Join-Path $launcher 'layout-test-results.json') -Destination $out
$r=Get-Content -Raw $result|ConvertFrom-Json
if (!$r.success) { throw 'Windows regression report marked failed.' }
$utf8=[Text.UTF8Encoding]::new($false)
$build=[ordered]@{artifact='Onechanbara_Diagnostics.exe';target='net48-x64-winforms';revision='diagnostic-output-1';launcher_revision='json-bom-fix-1';sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();windows_netframework_test=$true;production_lifecycle_mock_test=$true;gpu_test=$false;source_commit=$env:GITHUB_SHA;run_url="https://github.com/$env:GITHUB_REPOSITORY/actions/runs/$env:GITHUB_RUN_ID"}
[IO.File]::WriteAllText((Join-Path $out 'launcher-build.json'),($build|ConvertTo-Json -Depth 8),$utf8)
Remove-Item -LiteralPath $test
Write-Host "Windows Framework checks passed: $($r.passed); production launcher: $($build.sha256)"
