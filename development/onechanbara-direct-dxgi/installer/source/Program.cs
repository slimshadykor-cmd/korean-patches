using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;

class PatchWindow:Form {
 Button patch,connect;CheckBox vulkan;TextBox log;bool busy;
 public PatchWindow(){Text="오네찬바라 볼텍스 한글패치 v1.7";ClientSize=new Size(800,580);MinimumSize=Size;StartPosition=FormStartPosition.CenterScreen;Font=new Font("Malgun Gothic",10);
  Controls.Add(new Label{Text="한글화 슬림쉐이디  |  기존 한글화 · 로딩 개선 · 화면 동기화 · 기존 프로필과 저장 위치 사용\n일본판 원본 / 기존 한글판 ISO에서 새 v1.7 한글 ISO를 만듭니다. 입력 ISO는 그대로 보존합니다.",Location=new Point(20,15),Size=new Size(760,55)});
  vulkan=new CheckBox{Text="완료 후 바탕화면에 오네찬바라 바로가기 만들기 (일반 권한으로 실행)",Checked=true,Location=new Point(22,75),Size=new Size(755,30)};Controls.Add(vulkan);
  patch=new Button{Text="한글패치 적용 — 새 ISO 만들기",Location=new Point(20,115),Size=new Size(760,48),Anchor=AnchorStyles.Top|AnchorStyles.Left|AnchorStyles.Right};Controls.Add(patch);
  connect=new Button{Text="기존 v1.7 ISO — 바로가기 연결",Location=new Point(20,175),Size=new Size(760,42),Anchor=AnchorStyles.Top|AnchorStyles.Left|AnchorStyles.Right};Controls.Add(connect);
  log=new TextBox{Multiline=true,ReadOnly=true,ScrollBars=ScrollBars.Vertical,Location=new Point(20,232),Size=new Size(760,328),Anchor=AnchorStyles.Top|AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right};Controls.Add(log);
  patch.Click+=async delegate{string source=PickIso("원본 또는 지원하는 기존 한글 ISO 선택");if(source==null)return;string target;
   using(var d=new SaveFileDialog{Title="새 v1.7 한글 ISO 저장 위치",Filter="Xbox 360 ISO (*.iso)|*.iso",InitialDirectory=Path.GetDirectoryName(source),FileName="Onechanbara_vorteX_KOR_v1.7.iso",AddExtension=true,DefaultExt="iso",OverwritePrompt=true}){if(d.ShowDialog(this)!=DialogResult.OK)return;target=d.FileName;}
   bool setup=vulkan.Checked;string exe=setup?PickXenia():null;if(setup&&exe==null)return;
   SetBusy(true);log.Clear();bool patched=false;
   try{if(setup)await Task.Run(()=>LauncherGlue.Configure(exe,null,null,true,Append));
    await Task.Run(()=>Standalone.Apply(source,target,Append));patched=true;
    if(setup){Append("완성된 ISO를 실행 연결에 등록하고 있습니다.");string hash=await Task.Run(()=>LauncherGlue.FileHash(target));await Task.Run(()=>LauncherGlue.Configure(exe,target,hash,false,Append));}
    MessageBox.Show(this,"v1.7 한글 ISO 생성 완료\n"+(setup?"바탕화면의 '오네찬바라' 바로가기로 실행하세요. NVIDIA 설정을 변경하지 않고 실행합니다.":"한글패치만 적용했습니다. 생성된 ISO를 사용하세요.")+"\n\n"+target,"완료",MessageBoxButtons.OK,MessageBoxIcon.Information);
   }catch(Exception ex){Append("중단: "+ex.Message);MessageBox.Show(this,(patched?"한글 ISO 생성은 완료됐지만 실행 연결은 완료되지 않았습니다.\n아래 '기존 v1.7 ISO — 바로가기 연결' 버튼으로 다시 연결할 수 있습니다.\n\n":"")+ex.Message,"확인 필요",MessageBoxButtons.OK,MessageBoxIcon.Error);}
   finally{SetBusy(false);}
  };
  connect.Click+=async delegate{string iso=PickIso("완성된 v1.7 한글 ISO 선택");if(iso==null)return;string exe=PickXenia();if(exe==null)return;SetBusy(true);log.Clear();
   try{await Task.Run(()=>LauncherGlue.VerifyFinalIso(iso,Append));await Task.Run(()=>LauncherGlue.Configure(exe,null,null,true,Append));string hash=await Task.Run(()=>LauncherGlue.FileHash(iso));await Task.Run(()=>LauncherGlue.Configure(exe,iso,hash,false,Append));MessageBox.Show(this,"연결 완료. 기존 프로필·세이브를 그대로 사용합니다. NVIDIA 설정을 변경하지 않고 실행합니다.\n바탕화면의 '오네찬바라' 바로가기로 실행하세요.","완료");}
   catch(Exception ex){Append("중단: "+ex.Message);MessageBox.Show(this,ex.Message,"연결 중단",MessageBoxButtons.OK,MessageBoxIcon.Error);}finally{SetBusy(false);}
  };
  FormClosing+=delegate(object s,FormClosingEventArgs e){if(busy){e.Cancel=true;MessageBox.Show(this,"파일 작업 중입니다. 완료될 때까지 기다려 주세요.");}};
 }
 string PickIso(string title){using(var d=new OpenFileDialog{Title=title,Filter="Xbox 360 ISO (*.iso)|*.iso",CheckFileExists=true})return d.ShowDialog(this)==DialogResult.OK?d.FileName:null;}
 string PickXenia(){using(var d=new OpenFileDialog{Title="기존 xenia_canary.exe 위치 선택",Filter="제니아 실행파일|xenia_canary.exe",CheckFileExists=true,InitialDirectory=Directory.Exists(@"E:\xenia_canary_windows")?@"E:\xenia_canary_windows":null})return d.ShowDialog(this)==DialogResult.OK?d.FileName:null;}
 void SetBusy(bool value){busy=value;patch.Enabled=connect.Enabled=vulkan.Enabled=!value;}
 void Append(string s){if(InvokeRequired){BeginInvoke(new Action<string>(Append),s);return;}log.AppendText(s+Environment.NewLine);}
 [STAThread]static void Main(){Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new PatchWindow());}
}
