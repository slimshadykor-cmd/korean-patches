param([string]$Fixture,[string]$Bundle,[switch]$FailLink)
$ErrorActionPreference='Stop';$env:WINDIR=Join-Path $Fixture 'Windows'
$global:InjectLinkFailure=[bool]$FailLink
function global:Get-FileHash {
 param([string]$LiteralPath,[string]$Algorithm='SHA256')
 if([IO.Path]::GetFileName($LiteralPath)-ceq'xenia_canary.exe'){return [pscustomobject]@{Hash='64AC262FE55E0E252FA46CEBAE006978AFA48BB109996E1304F3F64EEB9D4932'}}
 Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $LiteralPath -Algorithm $Algorithm
}
function New-MockShell {
 $o=[pscustomobject]@{}
 $o|Add-Member ScriptMethod CreateShortcut {
  param($path)
  $s=[pscustomobject]@{Path=$path;TargetPath='';Arguments='';WorkingDirectory='';IconLocation='';Description='';WindowStyle=0}
  if([IO.File]::Exists($path)){$old=[IO.File]::ReadAllText($path)|ConvertFrom-Json;foreach($p in $old.PSObject.Properties){$s.($p.Name)=$p.Value}}
  $s|Add-Member ScriptMethod Save {
   if($global:InjectLinkFailure){throw 'injected shortcut write failure'}
   [IO.File]::WriteAllText($this.Path,($this|Select-Object Path,TargetPath,Arguments,WorkingDirectory,IconLocation,Description,WindowStyle|ConvertTo-Json))
  };return $s
 };return $o
}
function global:New-Object {
 [CmdletBinding(PositionalBinding=$false)]
 param([Parameter(Position=0)][string]$TypeName,[string]$ComObject,[Parameter(Position=1)][object[]]$ArgumentList)
 if($ComObject-ceq'WScript.Shell'){return New-MockShell}
 Microsoft.PowerShell.Utility\New-Object @PSBoundParameters
}
$game=Join-Path $Fixture 'game.iso';$sha=(Microsoft.PowerShell.Utility\Get-FileHash $game -Algorithm SHA256).Hash
& (Join-Path $Bundle 'Manage-Onechanbara.ps1') -Mode Install -Root $Fixture -GamePath $game -GameSha256 $sha -DesktopPath (Join-Path $Fixture 'desktop') -TemplatePath (Join-Path $PSScriptRoot 'source/Onechanbara.config.toml') -NoUI
exit $LASTEXITCODE
