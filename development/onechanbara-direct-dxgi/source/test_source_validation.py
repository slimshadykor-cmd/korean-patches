"""Check LF/CRLF checkout support and reject an actual changed source byte."""
from pathlib import Path
import json
import tempfile
from verify_sources import verify_sources

manifest = Path(__file__).with_name('source-manifest.json')
names = list(json.loads(manifest.read_text())['files'])
original = Path.cwd()
assert verify_sources(original) == len(names)
with tempfile.TemporaryDirectory(prefix='onechanbara-source-check-') as tmp:
    root = Path(tmp)
    for newline in (b'\n', b'\r\n'):
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = (original / name).read_bytes().replace(b'\r\n', b'\n')
            path.write_bytes(data.replace(b'\n', newline))
        assert verify_sources(root) == len(names)
    target = root / names[0]
    target.write_bytes(target.read_bytes() + b'changed source byte')
    try:
        verify_sources(root)
    except ValueError as error:
        assert names[0] in str(error)
    else:
        raise AssertionError('Changed source unexpectedly accepted')
print('Source checks passed: original, LF, CRLF, changed-byte rejection')
