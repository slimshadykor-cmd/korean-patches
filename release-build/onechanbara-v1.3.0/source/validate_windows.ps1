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
$assembly = [Reflection.Assembly]::LoadFile($exe)
$method = $assembly.GetType('Standalone', $true).GetMethod('Apply')
$inputPath = Join-Path $testRoot 'invalid.iso'
[IO.File]::WriteAllText($inputPath, 'not-an-iso')
$before = (Get-FileHash $inputPath -Algorithm SHA256).Hash
$log = [Action[string]] { param($message) }
$passed = @()
foreach ($case in @('invalid-iso', 'existing-output', 'input-equals-output')) {
    $outputPath = Join-Path $testRoot ($case + '.iso')
    if ($case -eq 'existing-output') { [IO.File]::WriteAllText($outputPath, 'KEEP EXISTING OUTPUT') }
    if ($case -eq 'input-equals-output') { $outputPath = $inputPath }
    $caught = $null
    try { $method.Invoke($null, @($inputPath, $outputPath, $log)) | Out-Null }
    catch { $caught = $_.Exception; while ($caught.InnerException) { $caught = $caught.InnerException } }
    if (-not $caught) { throw "Expected rejection missing: $case" }
    if ($case -eq 'invalid-iso' -and $caught.GetType().FullName -ne 'System.IO.InvalidDataException') { throw $caught }
    if ($case -ne 'invalid-iso' -and $caught.GetType().FullName -ne 'System.IO.IOException') { throw $caught }
    if ((Get-FileHash $inputPath -Algorithm SHA256).Hash -ne $before) { throw 'Input changed' }
    if ($case -eq 'existing-output' -and [IO.File]::ReadAllText($outputPath) -ne 'KEEP EXISTING OUTPUT') { throw 'Existing output changed' }
    if ($case -eq 'invalid-iso' -and [IO.File]::Exists($outputPath)) { throw 'Output created for invalid ISO' }
    if ([IO.File]::Exists($outputPath + '.partial')) { throw 'Partial output retained' }
    if (@(Get-ChildItem $processTemp -Filter 'OnechanbaraPatch_*' -Directory).Count -ne 0) { throw 'Patch temporary directory retained' }
    $passed += $case
}
@{ platform = 'Windows .NET Framework'; shipping_exe_loaded = $true; rejections = $passed; input_preserved = $true; temporary_directories_removed = $true; gui_rendered = $false; xenia_gameplay = $false } | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $dist 'windows-validation.json') -Encoding UTF8
Write-Host ('Native Windows validation passed: ' + ($passed -join ', '))
