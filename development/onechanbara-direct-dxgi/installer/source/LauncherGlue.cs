using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.Collections.Generic;
using OnechanbaraPatch;

public static class LauncherGlue {
 public static void VerifyFinalIso(string isoPath, Action<string> log) {
  using(var iso=new ImageReader(isoPath))
  using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("OnechanbaraPackage.zip"))
  using(var zip=new ZipArchive(stream,ZipArchiveMode.Read))
  using(var reader=new StreamReader(zip.GetEntry("manifest.tsv").Open())) {
   var rows=new List<string[]>();var groups=new HashSet<string>();string line;
   while((line=reader.ReadLine())!=null){if(line.Length==0||line[0]=='#')continue;var r=line.Split('\t');rows.Add(r);if(iso.Entries.ContainsKey(r[0]))groups.Add(r[4]);}
   foreach(var r in rows){Entry e;if(!iso.Entries.TryGetValue(r[0],out e)){if(r[6]=="1"||!groups.Contains(r[4]))throw new InvalidDataException("완성된 v1.7 한글 ISO가 아닙니다: "+r[0]);continue;}
    string actual=Core.Hash(iso.Stream,e.Offset,e.Size);
    if(e.Size!=long.Parse(r[1])||actual!=r[2])throw new InvalidDataException("v1.7 결과와 다른 파일이 있습니다: "+r[0]);
   }
  }
  log("v1.7 한글 ISO 확인 통과");
 }
 public static string FileHash(string path) {using(var f=File.OpenRead(path))return Core.Hash(f,0,f.Length);}
 public static string Quote(string value) {
  if(value==null||value.IndexOfAny(new char[]{'"','\r','\n','\0'})>=0)throw new ArgumentException("지원하지 않는 경로입니다.");
  int trailing=0;for(int i=value.Length-1;i>=0&&value[i]=='\\';i--)trailing++;
  return "\""+value+new string('\\',trailing)+"\"";
 }
 public static void Configure(string xeniaExe,string iso,string isoHash,bool check,Action<string> log) {
  string root=Path.GetDirectoryName(Path.GetFullPath(xeniaExe));
  if(!string.Equals(Path.GetFileName(xeniaExe),"xenia_canary.exe",StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("기존 xenia_canary.exe를 선택하세요.");
  string temp=Path.Combine(Path.GetTempPath(),"OnechanbaraSetup_"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(temp);
  try {
   string script=Path.Combine(temp,"Manage-Onechanbara.ps1");
   using(var src=Assembly.GetExecutingAssembly().GetManifestResourceStream("Manage-Onechanbara.ps1"))using(var dst=File.Create(script))src.CopyTo(dst);
   string template=Path.Combine(temp,"Onechanbara.config.toml");
   using(var src=Assembly.GetExecutingAssembly().GetManifestResourceStream("Onechanbara.config.toml"))using(var dst=File.Create(template))src.CopyTo(dst);
   foreach(string name in new[]{"xenia_onechanbara.exe","Onechanbara_Launcher.exe"}) {
    using(var src=Assembly.GetExecutingAssembly().GetManifestResourceStream(name))using(var dst=File.Create(Path.Combine(temp,name)))src.CopyTo(dst);
   }
   string args="-NoProfile -NonInteractive -ExecutionPolicy Bypass -STA -File "+Quote(script)+" -NoUI -AllowSavePrompt -Root "+Quote(root)+" -Mode "+(check?"Check":"Install");
   args+=" -TemplatePath "+Quote(template);
   if(!check)args+=" -GamePath "+Quote(Path.GetFullPath(iso))+" -GameSha256 "+Quote(isoHash);
   string ps=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows),"System32","WindowsPowerShell","v1.0","powershell.exe");
   var info=new ProcessStartInfo(ps,args){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=System.Text.Encoding.UTF8,StandardErrorEncoding=System.Text.Encoding.UTF8};
   using(var p=new Process()){p.StartInfo=info;p.OutputDataReceived+=(s,e)=>{if(e.Data!=null)log(e.Data);};p.ErrorDataReceived+=(s,e)=>{if(e.Data!=null)log(e.Data);};
    p.Start();p.BeginOutputReadLine();p.BeginErrorReadLine();p.WaitForExit();if(p.ExitCode!=0)throw new InvalidOperationException("전용 실행 연결을 완료하지 못했습니다. 위 중단 메시지를 확인하세요. 공통 설정을 자동으로 초기화하지 않았습니다.");
   }
  }finally{if(Directory.Exists(temp))Directory.Delete(temp,true);}
 }
}
