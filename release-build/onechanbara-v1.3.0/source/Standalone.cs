using System;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Collections.Generic;
using OnechanbaraPatch;
public static class Standalone {
 public static void Apply(string input,string output,Action<string> log) {
  string temp=Path.Combine(Path.GetTempPath(),"OnechanbaraPatch_"+Guid.NewGuid().ToString("N"));
  Directory.CreateDirectory(temp);
  try {
   log("패치 데이터를 준비하고 있습니다.");
   using(Stream resource=Assembly.GetExecutingAssembly().GetManifestResourceStream("OnechanbaraPackage.zip")) {
    if(resource==null)throw new InvalidDataException("내장 패치 데이터가 없습니다.");
    using(var zip=new ZipArchive(resource,ZipArchiveMode.Read)) {
     var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
     foreach(var entry in zip.Entries) {
      string name=entry.FullName;
      if(name!="manifest.tsv" && !name.StartsWith("payload/",StringComparison.Ordinal))throw new InvalidDataException("내장 패치 경로 오류");
      if(name.IndexOfAny(new char[]{'\\',':','\0'})>=0 || !seen.Add(name))throw new InvalidDataException("내장 패치 경로 오류");
      foreach(string part in name.Split('/'))if(part.Length==0||part=="."||part=="..")throw new InvalidDataException("내장 패치 경로 오류");
      string destination=Path.Combine(temp,name.Replace('/',Path.DirectorySeparatorChar));
      Directory.CreateDirectory(Path.GetDirectoryName(destination));
      using(Stream src=entry.Open())using(var dst=new FileStream(destination,FileMode.CreateNew,FileAccess.Write))src.CopyTo(dst);
     }
    }
   }
   Core.Apply(input,output,temp,log);
  }finally {if(Directory.Exists(temp))Directory.Delete(temp,true);}
 }
}

