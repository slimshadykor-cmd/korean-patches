using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Collections.Generic;
using System.Security.Cryptography;

namespace OnechanbaraPatch {
public class Item {
 public string Path,Payload,Mode,Hash;public long Size;public bool Required;public HashSet<string> Accepted;
}
public class Entry {public string Path;public long Offset,Size,Record;}
public sealed class ImageReader : IDisposable {
 public FileStream Stream;public long Base;public Dictionary<string,Entry> Entries=new Dictionary<string,Entry>(StringComparer.OrdinalIgnoreCase);
 HashSet<long> dirs=new HashSet<long>();
 public ImageReader(string path) {
  Stream=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.Read);
  try {
   bool found=false;foreach(long b in new long[]{0,0xFB20,0x20600,0x2080000,0xFD90000}) {
    if(b+0x10800>Stream.Length)continue;
    byte[] d=Read(b+0x10000,2048);
    if(Encoding.ASCII.GetString(d,0,20)!="MICROSOFT*XBOX*MEDIA")continue;
    if(Encoding.ASCII.GetString(d,2028,20)!="MICROSOFT*XBOX*MEDIA")continue;
    Base=b;ReadDir(b+(long)BitConverter.ToUInt32(d,20)*2048,BitConverter.ToUInt32(d,24),"",0);found=true;break;
   }
   if(!found)throw new InvalidDataException("지원하는 Xbox 360 ISO 구조를 찾을 수 없습니다.");
  }catch{Stream.Dispose();throw;}
 }
 public byte[] Read(long at,int size) {if(at<0||size<0||at>Stream.Length-size)throw new InvalidDataException("ISO 데이터 범위를 벗어났습니다.");byte[] b=new byte[size];Stream.Position=at;int n=0;while(n<size){int k=Stream.Read(b,n,size-n);if(k==0)throw new EndOfStreamException();n+=k;}return b;}
 void ReadDir(long at,long size,string parent,int depth) {
  if(size==0)return;if(size<14||size>32*1024*1024||depth>64||!dirs.Add(at))throw new InvalidDataException("ISO 폴더 구조가 손상되었습니다.");
  byte[] d=Read(at,(int)size);Stack<int> todo=new Stack<int>();HashSet<int> seen=new HashSet<int>();todo.Push(0);
  while(todo.Count>0){int o=todo.Pop();if(o<0||o+14>d.Length||!seen.Add(o))throw new InvalidDataException("잘못된 ISO 폴더 항목입니다.");
   int nl=d[o+13];if(nl==0||o+14+nl>d.Length)throw new InvalidDataException("잘못된 ISO 파일명입니다.");
   string name=Encoding.ASCII.GetString(d,o+14,nl);if(name=="."||name==".."||name.IndexOfAny(new char[]{'/','\\','\0'})>=0)throw new InvalidDataException("잘못된 ISO 경로입니다.");
   string p=parent+name;long off=Base+(long)BitConverter.ToUInt32(d,o+4)*2048,len=BitConverter.ToUInt32(d,o+8);
   if(off<0||off>Stream.Length-len)throw new InvalidDataException("ISO 파일이 잘렸습니다: "+p);
   if((d[o+12]&16)!=0)ReadDir(off,len,p+"/",depth+1);
   else{if(Entries.ContainsKey(p))throw new InvalidDataException("중복 ISO 경로: "+p);Entries.Add(p,new Entry{Path=p,Offset=off,Size=len,Record=at+o});}
   int l=BitConverter.ToUInt16(d,o)*4,r=BitConverter.ToUInt16(d,o+2)*4;if(l!=0)todo.Push(l);if(r!=0)todo.Push(r);
  }
 }
 public void Dispose(){Stream.Dispose();}
}
public static class Core {
 public static string Hash(Stream s,long at,long size){s.Position=at;using(SHA256 h=SHA256.Create()){byte[] b=new byte[1048576];while(size>0){int n=s.Read(b,0,(int)Math.Min(b.Length,size));if(n==0)throw new EndOfStreamException();h.TransformBlock(b,0,n,null,0);size-=n;}h.TransformFinalBlock(new byte[0],0,0);return BitConverter.ToString(h.Hash).Replace("-","").ToLowerInvariant();}}
 static bool SafePath(string p){if(string.IsNullOrEmpty(p)||p.IndexOfAny(new char[]{'\\',':','\0'})>=0||p.StartsWith("/"))return false;foreach(string s in p.Split('/'))if(s.Length==0||s=="."||s=="..")return false;return true;}
 static bool IsHash(string h){if(h.Length!=64)return false;foreach(char c in h)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;}
 public static List<Item> Manifest(string folder){List<Item> items=new List<Item>();HashSet<string> paths=new HashSet<string>(StringComparer.OrdinalIgnoreCase);Dictionary<string,string> payloads=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
  foreach(string line in File.ReadAllLines(System.IO.Path.Combine(folder,"manifest.tsv"),Encoding.UTF8)){if(line.Length==0||line[0]=='#')continue;string[] a=line.Split('\t');long size;
   if(a.Length!=7||!SafePath(a[0])||!SafePath(a[4])||!paths.Add(a[0])||!long.TryParse(a[1],out size)||size<=0||size>uint.MaxValue||!IsHash(a[2])||(a[5]!="delta"&&a[5]!="full")||(a[6]!="0"&&a[6]!="1"))throw new InvalidDataException("패치 목록이 손상되었습니다.");
   HashSet<string> accepted=new HashSet<string>(a[3].Split(','));foreach(string h in accepted)if(!IsHash(h))throw new InvalidDataException("원본 검사 정보가 손상되었습니다.");
   string signature=a[1]+":"+a[2]+":"+a[5],existing;if(payloads.TryGetValue(a[4],out existing)&&existing!=signature)throw new InvalidDataException("중복 패치 데이터 정보가 다릅니다.");payloads[a[4]]=signature;
   items.Add(new Item{Path=a[0],Size=size,Hash=a[2],Accepted=accepted,Payload=a[4],Mode=a[5],Required=a[6]=="1"});}
  if(items.Count==0)throw new InvalidDataException("패치 목록이 비어 있습니다.");return items;
 }
 static byte[] Delta(ImageReader iso,Entry e,Item item,string package) {
  if(e.Size!=item.Size||item.Size>64*1024*1024)throw new InvalidDataException("패치 대상 크기가 다릅니다: "+item.Path);
  byte[] data=iso.Read(e.Offset,(int)e.Size);
  using(FileStream f=File.OpenRead(System.IO.Path.Combine(package,"payload",item.Payload)))using(GZipStream z=new GZipStream(f,CompressionMode.Decompress))using(BinaryReader r=new BinaryReader(z)){
   if(r.ReadUInt32()!=0x3144504F||r.ReadInt32()!=data.Length)throw new InvalidDataException("델타 헤더 오류");
   int n=r.ReadInt32();if(n<0||n>1000000)throw new InvalidDataException("델타 항목 오류");long last=0;
   for(int i=0;i<n;i++){int off=r.ReadInt32(),len=r.ReadInt32();if(off<last||len<0||off>data.Length-len)throw new InvalidDataException("델타 범위 오류");byte[] b=r.ReadBytes(len);if(b.Length!=len)throw new EndOfStreamException();Buffer.BlockCopy(b,0,data,off,len);last=(long)off+len;}
   if(z.ReadByte()!=-1)throw new InvalidDataException("델타 끝 오류");
  }
  using(MemoryStream m=new MemoryStream(data,false))if(Hash(m,0,data.Length)!=item.Hash)throw new InvalidDataException("패치 결과 검증 실패: "+item.Path);
  return data;
 }
 public static void Apply(string input,string output,string package,Action<string> log) {
  input=System.IO.Path.GetFullPath(input);output=System.IO.Path.GetFullPath(output);
  if(string.Equals(input,output,StringComparison.OrdinalIgnoreCase)||File.Exists(output))throw new IOException("출력 파일이 이미 있습니다. 다른 이름을 선택하세요.");
  string temporary=output+".partial";if(File.Exists(temporary))throw new IOException("작업 중 파일이 이미 있습니다: "+temporary);
  List<Item> all=Manifest(package),work=new List<Item>();Dictionary<string,byte[]> deltas=new Dictionary<string,byte[]>();HashSet<string> checkedPayload=new HashSet<string>();Dictionary<string,string> sourceHashes=new Dictionary<string,string>();
  using(ImageReader iso=new ImageReader(input)){
   HashSet<string> presentGroups=new HashSet<string>(StringComparer.OrdinalIgnoreCase);foreach(Item it in all)if(iso.Entries.ContainsKey(it.Path))presentGroups.Add(it.Payload);
   foreach(Item it in all)if(!it.Required&&!presentGroups.Contains(it.Payload))throw new InvalidDataException("필수 영상이 없습니다: "+System.IO.Path.GetFileName(it.Path));
   foreach(Item it in all){Entry e;if(!iso.Entries.TryGetValue(it.Path,out e)){if(it.Required)throw new InvalidDataException("필수 게임 파일이 없습니다: "+it.Path);continue;}
    log("원본 확인: "+it.Path);string hash,key=e.Offset+":"+e.Size;if(!sourceHashes.TryGetValue(key,out hash)){hash=Hash(iso.Stream,e.Offset,e.Size);sourceHashes.Add(key,hash);}if(hash==it.Hash)continue;
    if(!it.Accepted.Contains(hash))throw new InvalidDataException("지원하는 일본판 원본 또는 기존 한글판 ISO를 선택해 주세요: "+it.Path);
    if(it.Mode=="delta")deltas[it.Payload]=Delta(iso,e,it,package);
    else if(it.Mode=="full") {if(checkedPayload.Add(it.Payload))using(FileStream f=File.OpenRead(System.IO.Path.Combine(package,"payload",it.Payload))){if(f.Length!=it.Size||Hash(f,0,f.Length)!=it.Hash)throw new InvalidDataException("패치 데이터가 손상되었습니다: "+it.Payload);}}
    else throw new InvalidDataException("알 수 없는 패치 형식");work.Add(it);
   }
   if(work.Count==0)throw new InvalidOperationException("이미 이 패치가 적용된 ISO입니다.");
   bool created=false;
   try {
    using(FileStream dst=new FileStream(temporary,FileMode.CreateNew,FileAccess.ReadWrite,FileShare.None)){
     created=true;log("한글판 ISO 생성 중 — 원본은 보존됩니다.");iso.Stream.Position=0;byte[] copy=new byte[4*1024*1024];long copied=0;int lastPercent=-1,n;
     while((n=iso.Stream.Read(copy,0,copy.Length))>0){dst.Write(copy,0,n);copied+=n;int percent=(int)(copied*100/iso.Stream.Length);if(percent/10!=lastPercent/10||lastPercent<0||percent==100){log("ISO 복사: "+percent+"%");lastPercent=percent;}}
     Dictionary<string,long> extents=new Dictionary<string,long>();
     foreach(Item it in work){Entry e=iso.Entries[it.Path];long off;
      if(!extents.TryGetValue(it.Hash,out off)){
       off=iso.Base+((dst.Length-iso.Base+2047)/2048)*2048;dst.Position=off;
       if(it.Mode=="delta"){byte[] b=deltas[it.Payload];dst.Write(b,0,b.Length);}else using(FileStream f=File.OpenRead(System.IO.Path.Combine(package,"payload",it.Payload)))f.CopyTo(dst);
       long final=iso.Base+((dst.Length-iso.Base+2047)/2048)*2048;dst.SetLength(final);extents.Add(it.Hash,off);
       if(Hash(dst,off,it.Size)!=it.Hash)throw new IOException("ISO 기록 검증 실패: "+it.Path);
      }
      log("적용: "+it.Path);dst.Position=e.Record+4;using(BinaryWriter w=new BinaryWriter(dst,Encoding.UTF8,true)){w.Write(checked((uint)((off-iso.Base)/2048)));w.Write(checked((uint)it.Size));}
     }
     dst.Flush(true);
    }
    using(ImageReader check=new ImageReader(temporary)){foreach(Item it in work){Entry e=check.Entries[it.Path];if(e.Size!=it.Size||Hash(check.Stream,e.Offset,e.Size)!=it.Hash)throw new IOException("완료 후 검증 실패: "+it.Path);}}
    File.Move(temporary,output);log("완료: "+output);
   }catch{if(created&&File.Exists(temporary))File.Delete(temporary);throw;}
  }
 }
}
}
