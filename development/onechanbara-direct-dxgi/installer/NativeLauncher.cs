using System;
using System.IO;
using System.Diagnostics;
using System.Text;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
using System.Collections.Generic;
using System.Windows.Forms;

internal static class NativeLauncher {
 static string Hash(string p){using(var f=File.OpenRead(p))using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(f)).Replace("-","");}
 static string S(Dictionary<string,object> r,string k){object v;if(!r.TryGetValue(k,out v)||v==null)throw new InvalidDataException("실행 연결 기록이 올바르지 않습니다: "+k);return Convert.ToString(v,System.Globalization.CultureInfo.InvariantCulture);}
 static string Q(string value){if(value==null||value.IndexOfAny(new[]{'"','\r','\n','\0'})>=0)throw new InvalidDataException("지원하지 않는 경로 문자입니다.");int n=0;for(int i=value.Length-1;i>=0&&value[i]=='\\';--i)++n;return "\""+value+new string('\\',n)+"\"";}
 static void SafePath(string p){for(string a=Path.GetFullPath(p);!String.IsNullOrEmpty(a);a=Path.GetDirectoryName(a)){if((File.Exists(a)||Directory.Exists(a))&&(File.GetAttributes(a)&FileAttributes.ReparsePoint)!=0)throw new InvalidDataException("연결된 실행 경로를 사용할 수 없습니다: "+a);}}
 [STAThread] static void Main(){
  Application.EnableVisualStyles();
  try{
   string home=AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar);
   string receipt=Path.Combine(home,"install.json"),exe=Path.Combine(home,"runtime","xenia_onechanbara.exe"),config=Path.Combine(home,"Onechanbara.config.toml");
   foreach(string p in new[]{home,receipt,exe,config})SafePath(p);
   var r=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(receipt));
   if(S(r,"Owner")!="Onechanbara.445007D2.DirectDXGI"||S(r,"Version")!="1.7"||S(r,"ContentMode")!="OriginalSharedContent")throw new InvalidDataException("오네찬바라 v1.7 실행 연결 기록이 아닙니다.");
   if(!String.Equals(Hash(exe),S(r,"ExeSha256"),StringComparison.OrdinalIgnoreCase))throw new InvalidDataException("전용 실행파일 검증에 실패했습니다. 통합 패치에서 바로가기를 다시 연결해 주세요.");
   string iso=S(r,"GamePath"),content=S(r,"OriginalContentRoot");SafePath(iso);SafePath(content);
   if(!Directory.Exists(content))throw new DirectoryNotFoundException("기존 저장 위치를 찾지 못했습니다: "+content);
   foreach(var other in Process.GetProcesses())using(other){
    string name;try{name=other.ProcessName;}catch{continue;}
    if(name.StartsWith("xenia",StringComparison.OrdinalIgnoreCase)||name.StartsWith("ocb17_",StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("실행 중인 제니아를 종료한 뒤 다시 실행해 주세요.");
   }
   string cache=Path.Combine(home,"cache"),logs=Path.Combine(home,"logs");Directory.CreateDirectory(logs);
   using(var run=File.Open(Path.Combine(home,"session.lock"),FileMode.OpenOrCreate,FileAccess.ReadWrite,FileShare.None))
   using(var game=File.Open(iso,FileMode.Open,FileAccess.Read,FileShare.Read)){
    var file=new FileInfo(iso);
    if(game.Length!=Int64.Parse(S(r,"GameLength"))||file.LastWriteTimeUtc.Ticks.ToString()!=S(r,"GameWriteUtcTicks"))throw new InvalidDataException("연결한 ISO가 변경됐습니다. 통합 패치에서 변경된 ISO를 연결해 주세요.");
    if(File.Exists(Path.Combine(home,"launch_data.bin")))throw new InvalidDataException("이전 재시작 정보가 남아 있습니다: "+Path.Combine(home,"launch_data.bin"));
    string args=Q(iso)+" --config="+Q(config)+" --storage_root="+Q(home)+" --content_root="+Q(content)+" --cache_root="+Q(cache)+" --log_file="+Q(Path.Combine(logs,"xenia.log"))+" --gpu=vulkan --render_target_path_vulkan=fsi --vulkan_direct_dxgi=true";
    using(var p=Process.Start(new ProcessStartInfo(exe,args){UseShellExecute=false,WorkingDirectory=home})){
     if(p==null)throw new InvalidOperationException("제니아 실행을 시작하지 못했습니다.");
     p.WaitForExit();
     var report=new Dictionary<string,object>{{"Version","1.7"},{"ExitCode",p.ExitCode},{"DriverSettingsChanged",false},{"RuntimeSha256",S(r,"ExeSha256")},{"TimeUtc",DateTime.UtcNow.ToString("o")}};
     File.WriteAllText(Path.Combine(logs,"last_run.json"),new JavaScriptSerializer().Serialize(report),new UTF8Encoding(false));
     if(p.ExitCode!=0)throw new InvalidOperationException("제니아가 오류 코드 "+p.ExitCode+"로 종료됐습니다.\n오류 기록: "+Path.Combine(logs,"xenia.log"));
    }
   }
  }catch(Exception ex){MessageBox.Show(ex.GetBaseException().Message,"오네찬바라 v1.7 실행 확인",MessageBoxButtons.OK,MessageBoxIcon.Error);}
 }
}
