"""Reproduce a ZIP from verified public baseline/payload entries, without recompression."""
from pathlib import Path, PurePosixPath
import hashlib,json,struct,zipfile

def sha(b): return hashlib.sha256(b).hexdigest()

def assemble(base_path,payload_path,manifest_path,out_path):
    m=json.loads(Path(manifest_path).read_text())
    assert sha(Path(base_path).read_bytes())==m['base_sha256']
    assert sha(Path(payload_path).read_bytes())==m['payload_sha256']
    central=[];names=set();date=((2026-1980)<<9)|(10<<5)|24
    with zipfile.ZipFile(base_path) as base,zipfile.ZipFile(payload_path) as payload,open(out_path,'wb') as out:
        for f in m['files']:
            name=f['name'];parts=PurePosixPath(name)
            assert not parts.is_absolute() and '..' not in parts.parts and name not in names
            names.add(name);z=base if f['source']=='base' else payload;info=z.getinfo(f['entry'])
            data=z.read(info);assert sha(data)==f['sha256']
            assert info.compress_type in [0,8] and not info.flag_bits&1
            z.fp.seek(info.header_offset);h=z.fp.read(30)
            n,e=struct.unpack_from('<HH',h,26);z.fp.seek(n+e,1);compressed=z.fp.read(info.compress_size)
            nameb=name.encode('utf-8');offset=out.tell();flag=0x800
            out.write(struct.pack('<IHHHHHIIIHH',0x04034b50,20,flag,info.compress_type,0,date,
                info.CRC,info.compress_size,info.file_size,len(nameb),0)+nameb+compressed)
            central.append(struct.pack('<I6H3I5H2I',0x02014b50,0x314,20,flag,info.compress_type,0,date,
                info.CRC,info.compress_size,info.file_size,len(nameb),0,0,0,0,0o100644<<16,offset)+nameb)
        start=out.tell()
        for c in central:out.write(c)
        length=out.tell()-start
        out.write(struct.pack('<I4H2IH',0x06054b50,0,0,len(central),len(central),length,start,0))
    with zipfile.ZipFile(out_path) as z:assert z.testzip() is None and len(z.infolist())==len(names)
    digest=sha(Path(out_path).read_bytes())
    if m.get('output_sha256'):assert digest==m['output_sha256']
    return digest

if __name__=='__main__':
    import sys
    print(assemble(*sys.argv[1:]))
