$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $PSScriptRoot 'DiagnosticCore.cs')
$root=Join-Path $PSScriptRoot ('tests/layout_'+[Guid]::NewGuid().ToString('N'))
$launcherPath=Join-Path $root '한글 공백 launcher'
$parentRuntime=Join-Path $root 'runtime';$localRuntime=Join-Path $launcherPath 'runtime'
[void][IO.Directory]::CreateDirectory($launcherPath);[void][IO.Directory]::CreateDirectory($parentRuntime)
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($launcherPath)-cne$parentRuntime){throw 'Parent runtime fallback failed'}
[void][IO.Directory]::CreateDirectory($localRuntime)
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($launcherPath)-cne$localRuntime){throw 'Adjacent runtime precedence failed'}
if([Onechanbara.Diagnostics.Core]::RuntimeDirectory($root)-cne$parentRuntime){throw 'Flat package root runtime failed'}
$linkHome=Join-Path $root 'linked';[void][IO.Directory]::CreateDirectory($linkHome)
New-Item -ItemType SymbolicLink -Path (Join-Path $linkHome 'runtime') -Target $parentRuntime|Out-Null
$rejected=$false;try{[void][Onechanbara.Diagnostics.Core]::RuntimeDirectory($linkHome)}catch{$rejected=$true}
if(-not$rejected){throw 'Reparse runtime accepted'}
[ordered]@{passed=4;checks=@('parent runtime fallback','adjacent runtime precedence','flat package layout','reparse runtime rejection');windows_gui_executed=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'layout-test-results.json') -Encoding utf8
Write-Output 'Passed 4 runtime layout checks.'
