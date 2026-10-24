from PIL import Image,ImageDraw
from pathlib import Path
import math,json
P=Path('mark_release');marks={};N=20;S=8
for mode in ['black','storm']:
 mask=Image.new('L',(N*S,N*S));d=ImageDraw.Draw(mask)
 def poly(points):d.polygon([(round(x*S),round(y*S)) for x,y in points],fill=255)
 if mode=='black':
  # Diagonal katana: narrow curved blade, short guard and wrapped grip.
  poly([(6.3,13.1),(10.1,8),(15,2.9),(18.8,.7),(17.4,4.2),(12.1,9.7),(8.2,14.4)])
  poly([(4.6,11.2),(9.9,15.5),(9.1,16.5),(3.8,12.2)])
  poly([(5.2,13.3),(6.8,14.7),(3.5,19),(1.8,17.6)])
 else:
  # One tapered brush-like spiral with a separate outer wind stroke.
  left=[];right=[]
  for i in range(241):
   t=i/240;a=-.8+t*math.pi*3.55;r=8.1*(1-t)+.8;w=1.45*(1-t)+.35
   left.append((10+(r+w)*math.cos(a),10+(r+w)*math.sin(a)))
   right.append((10+(r-w)*math.cos(a),10+(r-w)*math.sin(a)))
  poly(left+right[::-1])
  outer=[];inner=[]
  for i in range(81):
   t=i/80;a=-2.7+t*1.25;w=.65*math.sin(math.pi*t)
   outer.append((10+(9.4+w)*math.cos(a),10+(9.4+w)*math.sin(a)))
   inner.append((10+(9.4-w)*math.cos(a),10+(9.4-w)*math.sin(a)))
  poly(outer+inner[::-1])
 mask=mask.resize((N,N),Image.Resampling.LANCZOS);pixels={}
 for y in range(N):
  for x in range(N):
   a=min(255,round(mask.getpixel((x,y))/85)*85)
   if not a:continue
   bright=(x+y<20) if mode=='black' else (y<9)
   rgb=(0xf3f5ff if bright else 0xaab8d0) if mode=='black' else (0xffe6a3 if bright else 0xc29448)
   pixels[x,y]=(a<<24)|rgb
 rects=[]
 for y in range(N):
  x=0
  while x<N:
   color=pixels.get((x,y),0)
   if not color:x+=1;continue
   st=x
   while x<N and pixels.get((x,y))==color:x+=1
   match=next((r for r in rects if r[0]==st and r[2]==x-st and r[1]+r[3]==y and r[4]==color),None)
   if match:match[3]+=1
   else:rects.append([st,y,x-st,1,color])
 marks[mode]=rects
 im=Image.new('RGBA',(N,N))
 for (x,y),c in pixels.items():im.putpixel((x,y),((c>>16)&255,(c>>8)&255,c&255,c>>24))
 im.save(P/(mode+'.png'))
text=''
for mode,rects in marks.items():
 text+=mode+'_rects:\n .long '+str(len(rects))+'\n'
 for r in rects:text+=' .byte '+','.join(map(str,r[:4]))+'\n .long '+hex(r[4])+'\n'
(P/'rects.inc').write_text(text);(P/'rects.json').write_text(json.dumps(marks));print({m:len(r) for m,r in marks.items()})
preview=Image.new('RGBA',(360,100),'#15171b')
for name,x in [('black',55),('storm',235)]:
 im=Image.open(P/(name+'.png')).resize((60,60),Image.Resampling.NEAREST);preview.alpha_composite(im,(x,20))
preview.convert('RGB').save(P/'preview.png')
