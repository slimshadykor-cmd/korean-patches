from pathlib import Path
import io,struct,json
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;A=W.parent/'audit_identifiers_20261019';R=W.parent/'release_v128'
def atlases(b):
 out={}
 for i in range(22):
  at,n,no=struct.unpack_from('>III',b,i*12);name=b[no:b.index(0,no)].decode();im=Image.open(io.BytesIO(b[at:at+n]));im.load();out[int(name[1:3],16)]=im.convert('RGBA')
 return out
sets=[atlases((A/'current/Media/Sys/font.bin').read_bytes()),atlases((W/'changed/Media/Sys/font.bin').read_bytes())]
rows=json.load(open(W/'dialogue_changes.json'));examples=[('demo06_01.cat',8),('demo07_01.cat',0),('demo20_00.cat',35)]
im=Image.new('RGB',(1440,650),(250,250,250));d=ImageDraw.Draw(im);f=ImageFont.truetype(str(R/'dependencies/NotoSansCJKkr-Regular.otf'),24);sm=ImageFont.truetype(str(R/'dependencies/NotoSansCJKkr-Regular.otf'),18)
d.text((20,12),'v1.2.8  2026-10-19 대사 수정 전·후',font=f,fill='#111111');d.text((20,53),'실제 패치 파일의 글꼴·대사를 추출해 재현한 자료입니다. 제니아 실행 화면은 아닙니다.',font=sm,fill='#555555');d.text((20,91),'수정 전',font=f,fill='#a63030');d.text((740,91),'수정 후',font=f,fill='#005f90')
for row,(name,idx) in enumerate(examples):
 y=138+row*155;d.line((20,y-5,1420,y-5),fill='#cccccc');d.text((20,y),f'{name} / 대사 {idx}',font=sm,fill='#555555')
 for col in range(2):
  p=A/'current/Media/Demo'/name if col==0 else W/'changed/Media/Demo'/name;b=p.read_bytes();base=struct.unpack_from('>I',b)[0];start,stride,count,tail=struct.unpack_from('>IIII',b,base);pool=base+start+stride*count;at=pool+struct.unpack_from('>I',b,base+start+idx*stride+16)[0];raw=b[at:b.index(0,at)];left=20+col*720;x=left;yy=y+32;i=0
  while i<len(raw):
   lead=raw[i];n=2 if 0x81<=lead<=0x9f or 0xe0<=lead<=0xfc else 1;code=raw[i:i+n];i+=n
   if x+32>left+680:x=left;yy+=36
   if n==2:
    l,t=code;ax=(t-0x40)%16*32;ay=(t-0x40)//16*32;cell=sets[col][l].crop((ax,ay,ax+32,ay+32));im.paste((20,20,20),(x,yy,x+32,yy+32),cell.getchannel('A'));x+=32
   else:d.text((x,yy),code.decode('ascii'),font=f,fill='#111111');x+=16
(W/'deliverables/Onechanbara_v128_Dialogue_Fix_Proof.png').parent.mkdir(exist_ok=True);im.save(W/'deliverables/Onechanbara_v128_Dialogue_Fix_Proof.png')
