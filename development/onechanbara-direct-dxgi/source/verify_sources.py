"""Verify tracked text sources using Git's LF canonical representation."""
from pathlib import Path
import hashlib
import json


def verify_sources(source_root, manifest_path=None):
    manifest_path = manifest_path or Path(__file__).with_name('source-manifest.json')
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8-sig'))
    for name, expected in manifest['files'].items():
        # Git for Windows checks these text files out as CRLF. Only normalize
        # that representation; preserve all other bytes, whitespace and BOMs.
        data = (Path(source_root) / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Source hash mismatch: ' + name)
    return len(manifest['files'])


if __name__ == '__main__':
    print('Verified canonical source hashes:', verify_sources(Path.cwd()))
