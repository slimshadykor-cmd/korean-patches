from pathlib import Path
import gzip, hashlib, json, shutil, zipfile

R = Path(__file__).resolve().parent
D = R / 'publication'
D.mkdir(exist_ok=True)
base = Path('hakux_audit/unified/NGB_Korean_Patch_v2.0.zip').resolve()
target = R / 'NGB_Korean_Patch_v2.0.zip'
sha = lambda b: hashlib.sha256(b).hexdigest()
bp = 'NGB_Korean_Patch_v2.0/'
tp = 'NGB_Korean_Patch_v2.0/'
assert sha(base.read_bytes()) == 'cf92f7dc22b44f0ff6d76ac688435223de33b47ff4f7124ba321b36e53424464'
with zipfile.ZipFile(base) as b, zipfile.ZipFile(target) as t, zipfile.ZipFile(D/'payload.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as payload:
    original = json.loads(b.read(bp+'ngb_native11/assets/build_plan.json'))
    plan = json.loads(t.read(tp+'ngb_native11/assets/build_plan.json'))
    for key in ['archives', 'root_patches']:
        assert plan[key] == original[key]
    def encode(value, path=()):
        try:
            old = original
            for key in path: old = old[key]
            if old == value: return ['ref', list(path)]
        except (KeyError, IndexError, TypeError): pass
        if isinstance(value, dict): return ['dict', {k:encode(v,path+(k,)) for k,v in value.items()}]
        if isinstance(value, list): return ['list', [encode(v,path+(i,)) for i,v in enumerate(value)]]
        return ['value', value]
    (D/'plan_delta.json.gz').write_bytes(gzip.compress(json.dumps(encode(plan), ensure_ascii=False, separators=(',',':')).encode(), mtime=0))
    files = []
    for info in t.infolist():
        rel = info.filename.removeprefix(tp)
        data = t.read(info.filename)
        if rel == 'ngb_native11/assets/build_plan.json': source, entry = 'plan', ''
        elif bp+rel in b.namelist() and b.read(bp+rel) == data: source, entry = 'base', bp+rel
        else:
            source, entry = 'payload', rel
            payload.writestr(rel, data)
        attrs = {k:getattr(info,k) for k in ['date_time','compress_type','create_system','create_version','extract_version','reserved','flag_bits','volume','internal_attr','external_attr','extra','comment']}
        for k in ['extra','comment']: attrs[k] = attrs[k].hex()
        files.append({'name':info.filename,'entry':entry,'source':source,'sha256':sha(data),'info':attrs})
before = json.loads((R/'release_before.json').read_text())
manifest = {'base_sha256':sha(base.read_bytes()),'base_url':'https://github.com/slimshadykor-cmd/korean-patches/releases/download/ngb-v2.0/NGB_Korean_Patch_v2.0.zip','output_sha256':sha(target.read_bytes()),'payload_sha256':sha((D/'payload.zip').read_bytes()),'release_body_before_sha256':sha(before['body'].encode()),'files':files}
(D/'manifest.json.gz').write_bytes(gzip.compress(json.dumps(manifest,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
for name in ['SHA256SUMS.txt','RELEASE_NOTES.md','receipt.json']: shutil.copyfile(R/name,D/name)
print(json.dumps({'files':len(files),'base_files':sum(f['source']=='base' for f in files),'payload_bytes':(D/'payload.zip').stat().st_size,'delta_bytes':(D/'plan_delta.json.gz').stat().st_size,'manifest_bytes':(D/'manifest.json.gz').stat().st_size},indent=2))
