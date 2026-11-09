param([string]$LauncherPath=(Join-Path $PSScriptRoot 'Onechanbara_Diagnostics.exe'))
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform-ne[PlatformID]::Win32NT-or$PSVersionTable.PSEdition-ne'Desktop'){throw 'Run with Windows PowerShell 5.1 to test the shipped .NET Framework executable.'}
[void][Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $LauncherPath).Path)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root=Join-Path $PSScriptRoot ('tests/layout_'+[Guid]::NewGuid().ToString('N'))
$launcherPath=Join-Path $root '한글 공백 launcher'
$parentRuntime=Join-Path $root 'runtime';$localRuntime=Join-Path $launcherPath 'runtime'
[void][IO.Directory]::CreateDirectory($launcherPath);[void][IO.Directory]::CreateDirectory($parentRuntime)
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($launcherPath)-cne$parentRuntime){throw 'Parent runtime fallback failed'}
[void][IO.Directory]::CreateDirectory($localRuntime)
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($launcherPath)-cne$localRuntime){throw 'Adjacent runtime precedence failed'}
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($root)-cne$parentRuntime){throw 'Flat package root runtime failed'}
$linkHome=Join-Path $root 'linked';[void][IO.Directory]::CreateDirectory($linkHome)
New-Item -ItemType Junction -Path (Join-Path $linkHome 'runtime') -Target $parentRuntime|Out-Null
$rejected=$false;try{[void][Onechanbara.Diagnostics.Core]::RuntimeDirectory($linkHome)}catch{$rejected=$true}
if(-not$rejected){throw 'Reparse runtime accepted'}
[ordered]@{passed=4;checks=@('parent runtime fallback','adjacent runtime precedence','flat package layout','reparse runtime rejection');windows_gui_executed=$false;actual_code_executed='Shipped Onechanbara_Diagnostics.exe via Windows PowerShell 5.1 .NET Framework';runtime=[Environment]::Version.ToString()}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'layout-test-results.json') -Encoding utf8
Write-Output 'Passed 4 runtime layout checks.'
