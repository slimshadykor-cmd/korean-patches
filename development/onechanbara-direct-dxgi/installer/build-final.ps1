$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$stage = Join-Path $PSScriptRoot 'release'
[void][IO.Directory]::CreateDirectory($stage)
$original = Join-Path $stage 'original.zip'
curl.exe -fsSL --retry 2 'https://github.com/slimshadykor-cmd/korean-patches/releases/download/onechanbara-v1.4.0/Onechanbara_Korean_v1.7.zip' -o $original
if ($LASTEXITCODE -ne 0 -or (Get-FileHash $original).Hash -ine 'bc003bb63403c8e92da32da8c034255287190fd708a5fdbe391a70c30346e734') { throw 'Original release verification failed' }
Expand-Archive $original (Join-Path $stage 'original')
Expand-Archive '../runtime/Onechanbara_DirectDXGI_Runtime_v1.7.zip' (Join-Path $stage 'runtime')
$runtime = Join-Path $stage 'runtime/xenia_onechanbara.exe'
if ((Get-FileHash $runtime).Hash -ine 'e5bf46df465b720642c45bda6c3bd95c0e308251fb5e55316b2416bc190b0f51') { throw 'Runtime is not the user-tested executable' }

$oldExe = Join-Path $stage 'original/Onechanbara_Korean_v1.7.exe'
$old = [Reflection.Assembly]::LoadFile($oldExe)
$payload = Join-Path $stage 'payload.zip'
$src = $old.GetManifestResourceStream('OnechanbaraPackage.zip')
if (!$src) { throw 'Original patch resource not found' }
$dst = [IO.File]::Create($payload)
try { $src.CopyTo($dst) } finally { $dst.Dispose(); $src.Dispose() }
Add-Type -AssemblyName System.Drawing
$ico = Join-Path $stage 'Onechanbara.ico'
$icon = [Drawing.Icon]::ExtractAssociatedIcon($oldExe)
$dst = [IO.File]::Create($ico)
try { $icon.Save($dst) } finally { $dst.Dispose(); $icon.Dispose() }

$csc = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$refs = @('/r:System.dll','/r:System.Core.dll','/r:System.Drawing.dll','/r:System.Windows.Forms.dll','/r:System.IO.Compression.dll','/r:System.Web.Extensions.dll')
$launcher = Join-Path $stage 'Onechanbara_Launcher.exe'
& $csc /nologo /target:winexe /platform:x64 /codepage:65001 /optimize+ "/out:$launcher" "/win32icon:$ico" /win32manifest:source/app.manifest $refs NativeLauncher.cs source/AssemblyInfo.cs
if ($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed' }
$script = Join-Path $stage 'Manage-Onechanbara.ps1'
$srcText = [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'source/Manage-Onechanbara.ps1'))
foreach ($entry in @(@('KnownRuntimeHash',$runtime),@('KnownLauncherHash',$launcher))) {
 $pattern = '(?m)^\$' + $entry[0] + "='[^']+'"
 if ([regex]::Matches($srcText,$pattern).Count -ne 1) { throw 'Missing installer hash binding' }
 $value = '$' + $entry[0] + "='" + (Get-FileHash $entry[1]).Hash + "'"
 $srcText = [regex]::Replace($srcText,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{param($match) $value})
}
[IO.File]::WriteAllText($script,$srcText,[Text.UTF8Encoding]::new($true))
$exe = Join-Path $stage 'Onechanbara_Korean_v1.7.exe'
& $csc /nologo /target:winexe /platform:x64 /codepage:65001 /optimize+ "/out:$exe" "/win32icon:$ico" /win32manifest:source/app.manifest $refs "/resource:$payload,OnechanbaraPackage.zip" "/resource:$script,Manage-Onechanbara.ps1" "/resource:source/Onechanbara.config.toml,Onechanbara.config.toml" "/resource:$runtime,xenia_onechanbara.exe" "/resource:$launcher,Onechanbara_Launcher.exe" source/IsoCore.cs source/Standalone.cs source/LauncherGlue.cs source/Program.cs source/AssemblyInfo.cs
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
$new = [Reflection.Assembly]::LoadFile($exe)
foreach ($entry in @(@('OnechanbaraPackage.zip',$payload),@('xenia_onechanbara.exe',$runtime),@('Onechanbara_Launcher.exe',$launcher),@('Manage-Onechanbara.ps1',$script))) {
 $src = $new.GetManifestResourceStream($entry[0])
 if (!$src) { throw "Missing installer resource: $($entry[0])" }
 $sha = [Security.Cryptography.SHA256]::Create()
 try { $actual = [BitConverter]::ToString($sha.ComputeHash($src)).Replace('-','') } finally { $src.Dispose(); $sha.Dispose() }
 if ($actual -ine (Get-FileHash $entry[1]).Hash) { throw "Installer resource mismatch: $($entry[0])" }
}
