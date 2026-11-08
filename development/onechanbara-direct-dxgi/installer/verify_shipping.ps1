$ErrorActionPreference='Stop'
$file=Join-Path $PSScriptRoot 'release/Onechanbara_Korean_v1.7.exe'
$asm=[Reflection.Assembly]::LoadFile($file)
$expected=@{
 'OnechanbaraPackage.zip'=(Join-Path $PSScriptRoot '../integrated_v17/payload.zip')
 'Manage-Onechanbara.ps1'=(Join-Path $PSScriptRoot 'source/Manage-Onechanbara.ps1')
 'Onechanbara.config.toml'=(Join-Path $PSScriptRoot 'source/Onechanbara.config.toml')
 'xenia_onechanbara.exe'=(Join-Path $PSScriptRoot 'runtime/xenia_onechanbara.exe')
 'Onechanbara_Launcher.exe'=(Join-Path $PSScriptRoot 'release/Onechanbara_Launcher.exe')
}
if($asm.GetManifestResourceNames().Count-ne$expected.Count){throw 'Unexpected embedded resource count'}
$result=[ordered]@{AssemblyVersion=$asm.GetName().Version.ToString();Resources=@{};NativeWindowsGPU=$false}
foreach($name in $asm.GetManifestResourceNames()){
 if(-not$expected.ContainsKey($name)){throw ('Unexpected resource: '+$name)}
 $stream=$asm.GetManifestResourceStream($name);$sha=[Security.Cryptography.SHA256]::Create()
 try{$hash=[BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant()}finally{$stream.Dispose();$sha.Dispose()}
 if($hash-cne(Get-FileHash -LiteralPath $expected[$name] -Algorithm SHA256).Hash.ToLowerInvariant()){throw ('Resource mismatch: '+$name)}
 $result.Resources[$name]=$hash
}
if($result.AssemblyVersion-cne'1.7.0.0'){throw 'Version mismatch'}
$v=[Diagnostics.FileVersionInfo]::GetVersionInfo($file)
if($v.FileVersion-cne'1.7'-or$v.ProductVersion-cne'1.7'){throw 'Visible version mismatch'}
$bad=Join-Path $PSScriptRoot 'invalid.iso';[IO.File]::WriteAllText($bad,'invalid fixture')
$rejected=$false
try{$asm.GetType('LauncherGlue').GetMethod('VerifyFinalIso').Invoke($null,@($bad,[Action[string]]{param($s)}))}catch{$rejected=$true}
if(-not$rejected){throw 'Actual shipping verifier accepted an invalid ISO'}
[IO.File]::Delete($bad)
$result.ActualShippingVerifierRejectsInvalidISO=$true
$script=[IO.File]::ReadAllText($expected['Manage-Onechanbara.ps1'])
if($script.Contains('__RUNTIME_SHA256__')-or$script.Contains('__LAUNCHER_SHA256__')){throw 'Unresolved resource hash placeholder'}
foreach($badText in 'Install-Sync.ps1','NvidiaTemporary.cs','RunAs','EnsureProfile','SaveSettings'){
 if($script.Contains($badText)){throw ('Driver/elevation path present: '+$badText)}
}
if(-not$script.Contains('$new.TargetPath=$NativeLauncher')){throw 'Native shortcut missing'}
$result.NoDriverOrElevationInstallPath=$true
foreach($exe in @($file,$expected['Onechanbara_Launcher.exe'])){
 $bytes=[IO.File]::ReadAllBytes($exe);$text=[Text.Encoding]::UTF8.GetString($bytes)
 if(-not$text.Contains('level="asInvoker"')-or$text.Contains('level="requireAdministrator"')){throw 'Executable elevation manifest mismatch'}
}
$result.BothManagedProgramsAsInvoker=$true
$result|ConvertTo-Json -Depth 5|Set-Content (Join-Path $PSScriptRoot 'shipping-validation.json')
Write-Output 'Shipping resources, v1.7, unchanged patch payload, invalid ISO rejection, native shortcut and asInvoker manifests verified'
