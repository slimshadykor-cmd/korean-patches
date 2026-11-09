using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;
using Onechanbara.Diagnostics;

class WindowsRegression {
 static readonly List<string> checks=new List<string>();
 static readonly Dictionary<string,object> report=new Dictionary<string,object>();
 static string root,fixtures;
 static void Check(bool ok,string name){if(!ok)throw new Exception("FAIL: "+name);checks.Add(name);Console.WriteLine("PASS: "+name);}
 static void Reject(Action a,string name){bool failed=false;try{a();}catch{failed=true;}Check(failed,name);}
 static Dictionary<string,object> OldRead(string path){using(var f=File.OpenRead(path))return (Dictionary<string,object>)new DataContractJsonSerializer(typeof(Dictionary<string,object>),new DataContractJsonSerializerSettings{UseSimpleDictionaryFormat=true}).ReadObject(f);}
 static void OldWrite(string path,Dictionary<string,object> data){using(var f=File.Create(path))new DataContractJsonSerializer(typeof(Dictionary<string,object>),new DataContractJsonSerializerSettings{UseSimpleDictionaryFormat=true}).WriteObject(f,data);}
 static string P(string name){return Path.Combine(root,name);}
 static void JsonCases(){
  string plain="{\"Owner\":\"Onechanbara.445007D2.DirectDXGI\",\"Version\":\"1.7\",\"ContentMode\":\"OriginalSharedContent\",\"GamePath\":\"E:\\\\한글 공백\\\\게임.iso\",\"GameLength\":8589934592,\"GameWriteUtcTicks\":\"638982503999999999\",\"trueValue\":true,\"falseValue\":false,\"missing\":null,\"Profiles\":[\"A\",\"B\"],\"Nested\":{\"key\":\"값\"}}";
  var cases=new Dictionary<string,Encoding>{{"utf8",new UTF8Encoding(false,true)},{"utf8-bom",new UTF8Encoding(true,true)},{"utf16-le",new UnicodeEncoding(false,true,true)},{"utf16-be",new UnicodeEncoding(true,true,true)}};
  foreach(var item in cases){string file=P(item.Key+".json");File.WriteAllText(file,plain,item.Value);string before=Core.Hash(file);var d=Core.ReadJson(file);Check(Core.S(d,"Owner")=="Onechanbara.445007D2.DirectDXGI",item.Key+" receipt owner");Check(Core.S(d,"GamePath")==@"E:\한글 공백\게임.iso",item.Key+" Korean escaped path");Check(Core.S(d,"GameLength")=="8589934592",item.Key+" 64-bit ISO length");Check(Core.S(d,"GameWriteUtcTicks")=="638982503999999999",item.Key+" ticks exact");Check((bool)d["trueValue"]&&!(bool)d["falseValue"]&&d["missing"]==null,item.Key+" bool/null");Check(((System.Collections.IList)d["Profiles"]).Count==2&&Core.S((Dictionary<string,object>)d["Nested"],"key")=="값",item.Key+" nested values and array preserved");Check(Core.Hash(file)==before,item.Key+" source unchanged");}
  bool reproduced=false;string oldError="";try{OldRead(P("utf8-bom.json"));}catch(Exception e){reproduced=true;oldError=e.ToString();}report["old_utf8_bom_error"]=oldError;Check(reproduced,"old shipped DataContract reader reproduces UTF-8 BOM startup failure");
  string discovery=P("auto-discovery");Directory.CreateDirectory(Path.Combine(discovery,"config","OnechanbaraDirect"));File.Copy(P("utf8-bom.json"),Path.Combine(discovery,"config","OnechanbaraDirect","install.json"));Check(Core.FindReceiptFromAncestors(Path.Combine(discovery,"unpacked"))==Path.Combine(discovery,"config","OnechanbaraDirect","install.json"),"BOM receipt auto-discovery works");
  var ps=Core.ReadJson(Path.Combine(fixtures,"powershell51-receipt.json"));Check(Core.S(ps,"GamePath")==@"E:\한글 공백\게임.iso","real Windows PowerShell 5.1 Korean path");Check(Core.S(ps,"GameWriteUtcTicks")=="638982503999999999"&&Core.S(ps,"GameLength")=="8589934592","real Windows PowerShell 5.1 ConvertTo-Json receipt");
  Check(Core.RuntimeHash(Path.Combine(fixtures,"original-runtime-build.json"))=="653b2fa6fa15b72e30a21da8b2ae13d89b15236740951f1218b250094248e28e","actual shipped runtime manifest");
  var meta=new Dictionary<string,object>{{"Mode","direct-guest"},{"Bytes",(long)8589934592},{"Source",@"E:\한글 공백\cache"},{"DriverSettingsChanged",false},{"Timestamp","638982503999999999"}};
  OldWrite(P("legacy-cache.json"),meta);Check(Core.S(Core.ReadJson(P("legacy-cache.json")),"Bytes")=="8589934592","prior DataContract cache metadata readable");
  Core.WriteJson(P("new-cache.json"),meta);var round=Core.ReadJson(P("new-cache.json"));Check(Core.S(round,"Source")==@"E:\한글 공백\cache"&&Core.S(round,"Timestamp")=="638982503999999999","new metadata roundtrip");Reject(()=>Core.WriteJson(P("new-cache.json"),meta),"existing metadata never overwritten");
  foreach(string bad in new[]{"{bad}","[1,2]","null","{\"a\":1","{\"a\":1} garbage"}){string f=P(Guid.NewGuid()+".json");File.WriteAllText(f,bad);Reject(()=>Core.ReadJson(f),"malformed/root-invalid JSON rejected: "+bad);}
 }
 static void QuoteCases(string fake){
  string dir=P("인자 공백 폴더");Directory.CreateDirectory(dir);string[] expected={@"E:\한글 경로\게임.iso",@"E:\끝나는 경로\",@"E:\a&b (x)\", ""};var args=new List<string>();foreach(var a in expected)args.Add(Core.Q(a));
  using(var p=Process.Start(new ProcessStartInfo(fake,String.Join(" ",args)){WorkingDirectory=dir,UseShellExecute=false,CreateNoWindow=true})){Check(p.WaitForExit(10000)&&p.ExitCode==0,"actual Windows child process launched");}
  var actual=new JavaScriptSerializer().Deserialize<string[]>(File.ReadAllText(Path.Combine(dir,"probe-args.json")));Check(actual.Length==expected.Length,"Windows argument count");for(int i=0;i<expected.Length;i++)Check(actual[i]==expected[i],"Windows argument "+i+" roundtrip");Reject(()=>Core.Q("a\"b"),"command quote injection blocked");Reject(()=>Core.Q("a\nb"),"command newline blocked");
 }
 static void Lifecycle(string fake){
  string home=P("한글 공백 진단"),installed=P("설치 원본"),content=P("원래 저장"),cache=P("원래 캐시"),runtime=Path.Combine(home,"runtime");foreach(string p in new[]{home,installed,content,cache,runtime})Directory.CreateDirectory(p);
  string iso=Path.Combine(installed,"게임 원본.iso"),source=Path.Combine(installed,"Onechanbara.config.toml"),receipt=Path.Combine(installed,"install.json");File.WriteAllText(iso,"mock game input; no copyrighted content");File.WriteAllText(Path.Combine(content,"save-sentinel.dat"),"saved game sentinel");File.WriteAllText(Path.Combine(cache,"shader.bin"),"shader cache sentinel");
  string config="[GPU]\ngpu = \"vulkan\"\nrender_target_path_vulkan = \"fsi\"\nocclusion_query = \"strict\"\ndraw_resolution_scale_x = 2\ndraw_resolution_scale_y = 2\nvsync = true\nframerate_limit = 0\n[General]\ntime_scalar = 1\n[Storage]\ncache_root = "+Core.TomlString(cache)+"\n";File.WriteAllText(source,config,new UTF8Encoding(true));
  var info=new FileInfo(iso);var data=new Dictionary<string,object>{{"Owner","Onechanbara.445007D2.DirectDXGI"},{"Version","1.7"},{"ContentMode","OriginalSharedContent"},{"GamePath",iso},{"OriginalContentRoot",content},{"GameLength",info.Length},{"GameWriteUtcTicks",info.LastWriteTimeUtc.Ticks.ToString(CultureInfo.InvariantCulture)}};File.WriteAllText(receipt,new JavaScriptSerializer().Serialize(data),new UTF8Encoding(true));
  string exe=Path.Combine(runtime,"xenia_onechanbara.exe");File.Copy(fake,exe);Core.WriteJson(Path.Combine(runtime,"build.json"),new Dictionary<string,object>{{"display_revision",Core.Revision},{"exe_sha256",Core.Hash(exe)}});
  var original=new Dictionary<string,string>();foreach(string f in new[]{receipt,source,iso,Path.Combine(content,"save-sentinel.dat"),Path.Combine(cache,"shader.bin")})original[f]=Core.Hash(f);
  Type type=typeof(Core).Assembly.GetType("DiagnosticForm",true);using(var form=(Form)Activator.CreateInstance(type,true)){
   type.GetField("home",BindingFlags.Instance|BindingFlags.NonPublic).SetValue(form,home);IntPtr handle=form.Handle;MethodInfo run=type.GetMethod("Run",BindingFlags.Instance|BindingFlags.NonPublic);
   for(int mode=0;mode<3;mode++)for(int repeat=0;repeat<2;repeat++){
    int captured=mode;var task=Task.Factory.StartNew(()=>{try{return (string)run.Invoke(form,new object[]{receipt,captured});}catch(TargetInvocationException e){throw e.InnerException;}});var watch=Stopwatch.StartNew();while(!task.IsCompleted&&watch.ElapsedMilliseconds<60000){Application.DoEvents();Thread.Sleep(10);}Check(task.IsCompleted,"mode "+mode+" repeat "+repeat+" completes within deadline");string zip=task.Result;Check(File.Exists(zip),"mode "+mode+" repeat "+repeat+" result ZIP generated");
    string[] dirs=Directory.GetDirectories(Path.Combine(home,"sessions"));Array.Sort(dirs,StringComparer.Ordinal);string session=dirs[dirs.Length-1];var meta=Core.ReadJson(Path.Combine(session,"runmeta.json"));Check(Core.S(meta,"ExitCode")=="0"&&!meta.ContainsKey("Error"),"mode "+mode+" repeat "+repeat+" production preparation/launch/exit passes");Check((bool)meta["CacheWasReused"]==(repeat==1),"mode "+mode+" repeat "+repeat+" private cache reuse");Check((bool)meta["SourceConfigUnchanged"]&&(bool)meta["ReceiptUnchanged"],"mode "+mode+" repeat "+repeat+" install unchanged");Check(File.ReadAllText(Path.Combine(session,"stdout.log")).Contains("MOCK_RUNTIME_STARTED")&&File.ReadAllText(Path.Combine(session,"stderr.log")).Contains("MOCK_STDERR_CAPTURED"),"mode "+mode+" repeat "+repeat+" output streams captured");
    string actualConfig=File.ReadAllText(Path.Combine(session,"actual.config.toml"));Check(Core.Value(actualConfig,"General","time_scalar")=="1"&&Core.Value(actualConfig,"GPU","draw_resolution_scale_x")=="2"&&Core.Value(actualConfig,"GPU","draw_resolution_scale_y")=="2"&&Core.Value(actualConfig,"GPU","occlusion_query")=="\"strict\""&&Core.Value(actualConfig,"GPU","render_target_path_vulkan")=="\"fsi\"","mode "+mode+" repeat "+repeat+" timing/resolution/render settings preserved");
    var args=new JavaScriptSerializer().Deserialize<string[]>(File.ReadAllText(Path.Combine(session,"probe-args.json")));Check(args[0]==iso&&Array.IndexOf(args,"--onechanbara_guest_output="+(mode==0?"true":"false"))>=0&&Array.IndexOf(args,"--vulkan_direct_dxgi="+(mode==2?"false":"true"))>=0,"mode "+mode+" repeat "+repeat+" actual runtime arguments");
    using(var archive=ZipFile.OpenRead(zip)){foreach(var entry in archive.Entries)Check(!entry.FullName.EndsWith(".iso")&&!entry.FullName.EndsWith(".dat")&&!entry.FullName.EndsWith(".bin"),"ZIP safe entry "+entry.FullName);}
   }
  }
  foreach(var pair in original)Check(Core.Hash(pair.Key)==pair.Value,"original byte hash preserved: "+Path.GetFileName(pair.Key));
 }
 [STAThread]static int Main(string[] args){
  root=Path.GetFullPath(args[0]);fixtures=Path.GetFullPath(args[1]);Directory.CreateDirectory(root);string output=Path.GetFullPath(args[2]);try{
   Check(Environment.OSVersion.Platform==PlatformID.Win32NT,"actual Windows execution");int release=(int)Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full","Release",0);Check(release>=528040,".NET Framework 4.8 or newer installed");report["framework_release"]=release;report["clr_version"]=Environment.Version.ToString();Check(typeof(Core).Assembly.Location.EndsWith("Onechanbara_Diagnostics.exe",StringComparison.OrdinalIgnoreCase),"test calls compiled production EXE");
   JsonCases();string fake=Path.Combine(fixtures,"FakeRuntime.exe");QuoteCases(fake);Lifecycle(fake);report["actual_production_launcher_lifecycle_with_mock_runtime"]=true;report["success"]=true;return 0;
  }catch(Exception e){report["success"]=false;report["error"]=e.ToString();Console.Error.WriteLine(e);return 1;}
  finally{report["passed"]=checks.Count;report["checks"]=checks;report["actual_windows_netframework_execution"]=true;report["actual_gpu_gameplay_test"]=false;report["launcher_sha256"]=Core.Hash(typeof(Core).Assembly.Location);File.WriteAllText(output,new JavaScriptSerializer{MaxJsonLength=Int32.MaxValue}.Serialize(report),new UTF8Encoding(false));}
 }
}
