from pathlib import Path
from PIL import Image
import struct
src=next(Path('save_crash_fix/extracted').rglob('demo.spr')); b=src.read_bytes()
w,h=512,64;dataoff=0x800+0x3fb000;paloff=0x800+0x1e7800
pal=[tuple(b[paloff+i*4+j] for j in [2,1,0,3]) for i in range(256)]
def sw(x,y):
 z=0;k=0
 for j in range(9):
  z|=((x>>j)&1)<<k;k+=1
  if j<6:z|=((y>>j)&1)<<k;k+=1
 return z
im=Image.new('RGBA',(w,h));im.putdata([pal[b[dataoff+sw(x,y)]] for y in range(h) for x in range(w)]);im.resize((1024,128)).save('release20/title_before.png')
