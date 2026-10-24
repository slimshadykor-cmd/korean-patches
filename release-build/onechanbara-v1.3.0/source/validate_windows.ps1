$ErrorActionPreference = 'Stop'
$buildRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Resolve-Path (Join-Path $buildRoot '../..')
$dist = Join-Path $projectRoot 'release-dist'
$exe = Join-Path $dist 'Onechanbara_ISO_Korean_v1.3.0.exe'
$testRoot = Join-Path $env:RUNNER_TEMP 'onechanbara-v130-native-validation'
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$processTemp = Join-Path $testRoot 'temp'
New-Item -ItemType Directory -Path $processTemp -Force | Out-Null
$env:TEMP = $processTemp
$env:TMP = $processTemp
$driver = Join-Path $testRoot 'ShippingDriver.exe'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
& $compiler /nologo /target:exe /platform:x64 "/out:$driver" (Join-Path $PSScriptRoot 'ShippingDriver.cs')
if ($LASTEXITCODE -ne 0) { throw 'Native validation driver compilation failed' }
$inputPath = Join-Path $testRoot 'invalid.iso'
[IO.File]::WriteAllText($inputPath, 'not-an-iso')
$before = (Get-FileHash $inputPath -Algorithm SHA256).Hash
$passed = @()
foreach ($case in @('invalid-iso', 'existing-output', 'input-equals-output')) {
    $outputPath = Join-Path $testRoot ($case + '.iso')
    if ($case -eq 'existing-output') { [IO.File]::WriteAllText($outputPath, 'KEEP EXISTING OUTPUT') }
    if ($case -eq 'input-equals-output') { $outputPath = $inputPath }
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $driver
    $start.Arguments = ('"{0}" "{1}" "{2}"' -f $exe, $inputPath, $outputPath)
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($start)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 1) { throw "Expected rejection missing: $case $stdout $stderr" }
    if ($case -eq 'invalid-iso' -and $stderr -notlike '*System.IO.InvalidDataException*') { throw $stderr }
    if ($case -ne 'invalid-iso' -and $stderr -notlike '*System.IO.IOException*') { throw $stderr }
    if ((Get-FileHash $inputPath -Algorithm SHA256).Hash -ne $before) { throw 'Input changed' }
    if ($case -eq 'existing-output' -and [IO.File]::ReadAllText($outputPath) -ne 'KEEP EXISTING OUTPUT') { throw 'Existing output changed' }
    if ($case -eq 'invalid-iso' -and [IO.File]::Exists($outputPath)) { throw 'Output created for invalid ISO' }
    if ([IO.File]::Exists($outputPath + '.partial')) { throw 'Partial output retained' }
    if (@(Get-ChildItem $processTemp -Filter 'OnechanbaraPatch_*' -Directory).Count -ne 0) { throw 'Patch temporary directory retained' }
    $passed += $case
}
@{ platform = 'Windows .NET Framework'; shipping_exe_loaded = $true; rejections = $passed; input_preserved = $true; temporary_directories_removed = $true; gui_rendered = $false; xenia_gameplay = $false } | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $dist 'windows-validation.json') -Encoding UTF8
Write-Host ('Native Windows validation passed: ' + ($passed -join ', '))
