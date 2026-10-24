"""Rebuild the existing title-version asset using its established build recipe."""
from pathlib import Path
import gzip,hashlib,io,json,struct,zipfile
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent.parent;A=R.parent/'audit1024'
sha=lambda b:hashlib.sha256(b).hexdigest()
archive=R/'deps/v125_release.zip'
assert sha(archive.read_bytes())=='d0774300d87384b906749b405e4730af1bdcbc4fc47b292b168f0aea1f9093e3'
with zipfile.ZipFile(archive) as z:exe=z.read('Onechanbara_ISO_Korean_v1.2.5.exe')
with zipfile.ZipFile(io.BytesIO(exe)) as z:
    rows={r[0]:r for l in z.read('manifest.tsv').decode().splitlines() if l and not l.startswith('#') for r in [l.split('\t')]}
    raw=gzip.decompress(z.read('payload/'+rows['Media/Menu/title2d.cat'][4]))
    magic,size,count=struct.unpack_from('<4sII',raw);assert magic==b'OPD1'
    out=bytearray((A/'original/Media/Menu/title2d.cat').read_bytes());assert len(out)==size
    pos=12
    for i in range(count):
        at,n=struct.unpack_from('<II',raw,pos);pos+=8;out[at:at+n]=raw[pos:pos+n];pos+=n
    assert pos==len(raw)
    title=bytes(out);assert sha(title)==rows['Media/Menu/title2d.cat'][2]

off,capacity=struct.unpack_from('>II',title)
font=ImageFont.truetype(str(R/'deps/NotoSansCJKkr-Regular.otf'),21)
def build(version):
    im=Image.open(io.BytesIO(title[off:off+capacity])).convert('RGB');assert im.size==(1280,720)
    d=ImageDraw.Draw(im);bbox=d.textbbox((0,0),version,font=font,stroke_width=2)
    d.text((194,684-bbox[1]),version,font=font,fill=(239,249,248),stroke_width=2,stroke_fill=(12,21,25))
    for quality in range(98,89,-1):
        buf=io.BytesIO();im.save(buf,format='JPEG',quality=quality,subsampling=0,optimize=True);jpeg=buf.getvalue()
        if len(jpeg)<=capacity:break
    assert len(jpeg)<=capacity
    result=title[:off]+jpeg+bytes(capacity-len(jpeg))+title[off+capacity:]
    assert len(result)==len(title)
    return result,jpeg,im,quality
old,_,before,_=build('v1.2.9')
assert old==(A/'current/Media/Menu/title2d.cat').read_bytes(),'Established v1.2.9 recipe must reproduce the current image exactly'
new,jpeg,after,quality=build('v1.3.0')
import numpy as np
a=np.asarray(before);b=np.asarray(after);changed=np.any(a!=b,axis=2);ys,xs=np.where(changed)
assert xs.min()>=190 and xs.max()<280 and ys.min()>=680 and ys.max()<715
assert new[:off]==old[:off] and new[off+capacity:]==old[off+capacity:]
p=R/'candidate/Media/Menu/title2d.cat';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
(R/'deliverables/Onechanbara_v1.3.0_Title.jpg').write_bytes(jpeg)
report={'version':'1.3.0','previous_version_recipe_byte_exact':True,'source_render_difference_box':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'other_archive_entries_byte_identical':True,'dimensions':[1280,720],'jpeg_quality':quality,'archive_size':len(new),'result_sha256':sha(new),'actual_gameplay_screenshot':False}
(R/'audit/title_validation.json').write_text(json.dumps(report,indent=2));print(report)
