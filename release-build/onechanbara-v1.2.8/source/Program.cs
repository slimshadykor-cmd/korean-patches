using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;
using OnechanbaraPatch;
class PatchWindow:Form {
 Button select;TextBox log;bool busy;
 public PatchWindow(){Text="오네찬바라 볼텍스 ISO 한글패치 v1.2.8";ClientSize=new Size(740,490);MinimumSize=Size;StartPosition=FormStartPosition.CenterScreen;Font=new Font("Malgun Gothic",10);
  Controls.Add(new Label{Text="~기혈을 잇는 자들~  |  한글화 슬림쉐이디\n일본판 원본 / v1.2.2~v1.2.7 한글판 / 여신상 수정 적용판을 새 v1.2.8로 만듭니다.",Location=new Point(20,18),Size=new Size(700,58)});
  select=new Button{Text="원본 / 기존 한글판 ISO 선택하여 v1.2.8 적용",Location=new Point(20,88),Size=new Size(700,44),Anchor=AnchorStyles.Top|AnchorStyles.Left|AnchorStyles.Right};Controls.Add(select);
  log=new TextBox{Multiline=true,ReadOnly=true,ScrollBars=ScrollBars.Vertical,Location=new Point(20,150),Size=new Size(700,318),Anchor=AnchorStyles.Top|AnchorStyles.Bottom|AnchorStyles.Left|AnchorStyles.Right};Controls.Add(log);
  select.Click+=async delegate{string source,target;
   using(var d=new OpenFileDialog{Title="일본판 원본 또는 기존 한글판 ISO 선택",Filter="Xbox 360 ISO (*.iso)|*.iso",CheckFileExists=true}){if(d.ShowDialog()!=DialogResult.OK)return;source=d.FileName;}
   using(var d=new SaveFileDialog{Title="한글판 ISO 저장 위치",Filter="Xbox 360 ISO (*.iso)|*.iso",InitialDirectory=Path.GetDirectoryName(source),FileName=Path.GetFileNameWithoutExtension(source)+"_KOR_v1.2.8.iso",AddExtension=true,DefaultExt="iso",OverwritePrompt=true}){if(d.ShowDialog()!=DialogResult.OK)return;target=d.FileName;}
   busy=true;select.Enabled=false;log.Clear();
   try{await Task.Run(()=>Standalone.Apply(source,target,Append));MessageBox.Show(this,"한글판 ISO를 만들었습니다.\n제니아에서 다음 ISO를 직접 불러오세요.\n\n"+target,"패치 완료",MessageBoxButtons.OK,MessageBoxIcon.Information);}
   catch(Exception ex){Append("중단: "+ex.Message);MessageBox.Show(this,ex.Message,"패치 중단",MessageBoxButtons.OK,MessageBoxIcon.Error);}
   finally{busy=false;select.Enabled=true;}
  };
  FormClosing+=delegate(object s,FormClosingEventArgs e){if(busy){e.Cancel=true;MessageBox.Show(this,"ISO 작업 중입니다. 완료될 때까지 기다려 주세요.");}};
 }
 void Append(string s){if(InvokeRequired){BeginInvoke(new Action<string>(Append),s);return;}log.AppendText(s+Environment.NewLine);}
 [STAThread]static void Main(){Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new PatchWindow());}
}

