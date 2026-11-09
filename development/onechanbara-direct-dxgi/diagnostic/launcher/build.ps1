param([string]$ReferenceRoot='')
$ErrorActionPreference='Stop'
if([Environment]::OSVersion.Platform-ne[PlatformID]::Win32NT){throw 'Build on Windows with .NET Framework 4.8 installed.'}
$csc=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
if(-not(Test-Path -LiteralPath $csc)){throw 'The .NET Framework x64 C# compiler was not found.'}
if(-not$ReferenceRoot){
 $ReferenceRoot=Join-Path ${env:ProgramFiles(x86)} 'Reference Assemblies/Microsoft/Framework/.NETFramework/v4.8'
 if(-not(Test-Path -LiteralPath $ReferenceRoot)){$ReferenceRoot=Split-Path -Parent $csc}
}
$exe=Join-Path $PSScriptRoot 'Onechanbara_Diagnostics.exe'
$compileArgs=@('/nologo','/utf8output','/codepage:65001','/target:winexe','/platform:x64','/optimize+','/nostdlib+',('/out:'+$exe),('/win32manifest:'+(Join-Path $PSScriptRoot 'app.manifest')))
foreach($name in 'mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll','System.Web.Extensions.dll','System.Xml.dll'){
 $reference=Join-Path $ReferenceRoot $name
 if(-not(Test-Path -LiteralPath $reference)){throw "Missing .NET Framework reference: $reference"}
 $compileArgs+=('/reference:'+$reference)
}
foreach($name in 'DiagnosticCore.cs','DiagnosticLauncher.cs','AssemblyInfo.cs'){$compileArgs+=(Join-Path $PSScriptRoot $name)}
& $csc @compileArgs
if($LASTEXITCODE-ne0){throw "Launcher compilation failed: $LASTEXITCODE"}
[ordered]@{artifact='Onechanbara_Diagnostics.exe';target='net48-x64-winforms';revision='diagnostic-output-1';launcher_revision='encoding-fix-1';sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();native_windows_gui_test=$false;gpu_test=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launcher-build.json') -Encoding utf8
Write-Output "Built $exe"
