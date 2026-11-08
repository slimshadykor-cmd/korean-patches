param([switch]$LauncherOnly)
$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.dll')
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.CSharp.dll')
$root=$PSScriptRoot;$source=Join-Path $root 'source';$release=Join-Path $root 'release';[void][IO.Directory]::CreateDirectory($release)
$base=Join-Path $root '../integrated_v17'
$refRoot=Join-Path $base 'dependencies/net48/build/.NETFramework/v4.8'
$refs=New-Object 'Collections.Generic.List[Microsoft.CodeAnalysis.MetadataReference]'
foreach($name in 'mscorlib.dll','System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.IO.Compression.dll','System.Web.Extensions.dll'){$refs.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile((Join-Path $refRoot $name)))}
function Build([string]$name,[string[]]$sources,$resourcePaths){
 $trees=New-Object 'Collections.Generic.List[Microsoft.CodeAnalysis.SyntaxTree]'
 foreach($path in $sources){$trees.Add([Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText([IO.File]::ReadAllText($path)))}
 $options=[Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions]::new([Microsoft.CodeAnalysis.OutputKind]::WindowsApplication).WithPlatform([Microsoft.CodeAnalysis.Platform]::X64).WithOptimizationLevel([Microsoft.CodeAnalysis.OptimizationLevel]::Release).WithDeterministic($true)
 $comp=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create($name,$trees,$refs,$options)
 $resources=New-Object 'Collections.Generic.List[Microsoft.CodeAnalysis.ResourceDescription]'
 foreach($k in $resourcePaths.Keys){$p=$resourcePaths[$k];$provider=[Func[IO.Stream]]{[IO.File]::OpenRead($p)}.GetNewClosure();$resources.Add([Microsoft.CodeAnalysis.ResourceDescription]::new($k,$provider,$true))}
 $exe=Join-Path $release ($name+'.exe');$stream=[IO.File]::Create($exe);$icon=[IO.File]::OpenRead((Join-Path $source 'Onechanbara.ico'))
 $manifest=[IO.File]::OpenRead((Join-Path $source 'app.manifest'))
 $win32=$comp.CreateDefaultWin32Resources($true,$false,$manifest,$icon)
 try{$result=$comp.Emit($stream,$null,$null,$win32,$resources);if(-not$result.Success){throw (($result.Diagnostics|ForEach-Object{$_.ToString()})-join "`n")}}
 finally{$stream.Dispose();$win32.Dispose();$manifest.Dispose();$icon.Dispose()}
 Write-Output ('Built '+$exe)
}
Build 'Onechanbara_Launcher' @((Join-Path $root '../non_nv/integration/NativeLauncher.cs'),(Join-Path $source 'AssemblyInfo.cs')) @{}
if($LauncherOnly){exit 0}
$runtime=Join-Path $root 'runtime/xenia_onechanbara.exe'
$launcher=Join-Path $release 'Onechanbara_Launcher.exe'
$script=Join-Path $source 'Manage-Onechanbara.ps1'
$text=[IO.File]::ReadAllText($script)
foreach($binding in @(@('KnownRuntimeHash',$runtime),@('KnownLauncherHash',$launcher))){
 $pattern='(?m)^\$'+$binding[0]+"='[^']+'"
 if([regex]::Matches($text,$pattern).Count-ne1){throw ('Missing unique executable hash binding: '+$binding[0])}
 $replacement='$'+$binding[0]+"='"+(Get-FileHash -LiteralPath $binding[1] -Algorithm SHA256).Hash+"'"
 $evaluator=[Text.RegularExpressions.MatchEvaluator]({param($m)$replacement}.GetNewClosure())
 $text=[regex]::Replace($text,$pattern,$evaluator)
}
[IO.File]::WriteAllText($script,$text,[Text.UTF8Encoding]::new($true))
$files=@();foreach($f in 'IsoCore.cs','Standalone.cs','LauncherGlue.cs','Program.cs','AssemblyInfo.cs'){$files+=Join-Path $source $f}
$resources=@{'OnechanbaraPackage.zip'=(Join-Path $base 'payload.zip');'Manage-Onechanbara.ps1'=$script;'Onechanbara.config.toml'=(Join-Path $source 'Onechanbara.config.toml');'xenia_onechanbara.exe'=$runtime;'Onechanbara_Launcher.exe'=$launcher}
Build 'Onechanbara_Korean_v1.7' $files $resources
