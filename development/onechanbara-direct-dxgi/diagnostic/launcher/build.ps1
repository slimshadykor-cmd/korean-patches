$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.dll')
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.CSharp.dll')
$refRoot=Join-Path $PSScriptRoot '../../integrated_v17/dependencies/net48/build/.NETFramework/v4.8'
$refs=New-Object 'Collections.Generic.List[Microsoft.CodeAnalysis.MetadataReference]'
foreach($name in 'mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll','System.Runtime.Serialization.dll','System.Xml.dll'){$refs.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile((Join-Path $refRoot $name)))}
$trees=New-Object 'Collections.Generic.List[Microsoft.CodeAnalysis.SyntaxTree]'
foreach($name in 'DiagnosticCore.cs','DiagnosticLauncher.cs','AssemblyInfo.cs'){$trees.Add([Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText([IO.File]::ReadAllText((Join-Path $PSScriptRoot $name))))}
$options=[Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions]::new([Microsoft.CodeAnalysis.OutputKind]::WindowsApplication).WithPlatform([Microsoft.CodeAnalysis.Platform]::X64).WithOptimizationLevel([Microsoft.CodeAnalysis.OptimizationLevel]::Release).WithDeterministic($true)
$comp=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create('Onechanbara_Diagnostics',$trees,$refs,$options)
$exe=Join-Path $PSScriptRoot 'Onechanbara_Diagnostics.exe'
$output=[IO.File]::Create($exe);$manifest=[IO.File]::OpenRead((Join-Path $PSScriptRoot 'app.manifest'))
$win32=$comp.CreateDefaultWin32Resources($true,$false,$manifest,$null)
try{$result=$comp.Emit($output,$null,$null,$win32);if(-not$result.Success){throw (($result.Diagnostics|ForEach-Object{$_.ToString()})-join "`n")}}
finally{$output.Dispose();$win32.Dispose();$manifest.Dispose()}
[ordered]@{artifact='Onechanbara_Diagnostics.exe';target='net48-x64-winforms';revision='diagnostic-output-1';sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();native_windows_gui_test=$false;gpu_test=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'launcher-build.json') -Encoding utf8
Write-Output "Built $exe"
