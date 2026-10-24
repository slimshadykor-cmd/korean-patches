"""Reproduce the verified v1.3.0 Windows patcher from the official v1.2.9 release.

This is release packaging infrastructure. It is not shipped to patch users.
Only the three named public files enter the downloadable release ZIP.
"""
from pathlib import Path
import argparse, gzip, hashlib, io, json, shutil, urllib.request, zipfile

HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-zip',type=Path)
    parser.add_argument('--out',type=Path,default=Path('release-dist'))
    args=parser.parse_args()
    recipe=json.loads((HERE/'recipe.json').read_text())
    assert recipe['format']=='verified-exe-copy-literal-v1'
    args.out.mkdir(parents=True,exist_ok=True)
    baseline=args.baseline_zip or args.out/'baseline-v129.zip'
    if not baseline.exists():
        urllib.request.urlretrieve(recipe['baseline_release_url'],baseline)
    assert sha(baseline.read_bytes())==recipe['baseline_release_sha256'],'Baseline release hash mismatch'
    with zipfile.ZipFile(baseline) as z:
        old=z.read(recipe['baseline_exe'])
    assert sha(old)==recipe['baseline_exe_sha256']
    packed=b''.join((HERE/name).read_bytes() for name in recipe['literal_parts'])
    assert sha(packed)==recipe['compressed_literals_sha256']
    literals=gzip.decompress(packed);assert sha(literals)==recipe['literals_sha256']
    result=bytearray()
    for kind,offset,length in recipe['commands']:
        assert kind in ('copy','literal') and offset>=0 and length>0
        source=old if kind=='copy' else literals
        assert offset+length<=len(source)
        result.extend(source[offset:offset+length])
    assert len(result)==recipe['result_exe_size'] and sha(result)==recipe['result_exe_sha256']
    assert recipe['result_exe']=='Onechanbara_ISO_Korean_v1.3.0.exe'
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        assert z.testzip() is None
        assert sha(z.read('manifest.tsv'))==recipe['inner_manifest_sha256']
        rows=[line.split('\t') for line in z.read('manifest.tsv').decode().splitlines() if line and not line.startswith('#')]
        assert len(rows)==158
        assert set(z.namelist())=={'manifest.tsv'}|{'payload/'+r[4] for r in rows}
    exe=args.out/recipe['result_exe'];exe.write_bytes(result)
    public_files=['Onechanbara_ISO_Korean_v1.3.0.exe','먼저읽기.txt','원본ISO_해시.txt']
    assert recipe['public_files']==public_files
    for name in public_files[1:]:shutil.copyfile(HERE/name,args.out/name)
    release=args.out/'Onechanbara_ISO_Korean_v1.3.0_Release.zip'
    with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in public_files:
            info=zipfile.ZipInfo(name,date_time=(2026,10,24,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,(args.out/name).read_bytes(),compresslevel=6)
    with zipfile.ZipFile(release) as z:
        assert z.testzip() is None and z.namelist()==public_files
        assert sha(z.read(public_files[0]))==recipe['result_exe_sha256']
    assert sha(release.read_bytes())==recipe['release_sha256'], 'Final ZIP hash mismatch'
    print(json.dumps({'release':str(release),'bytes':release.stat().st_size,'sha256':sha(release.read_bytes()),'exe_sha256':recipe['result_exe_sha256'],'public_files':public_files},ensure_ascii=False))
if __name__=='__main__':main()


