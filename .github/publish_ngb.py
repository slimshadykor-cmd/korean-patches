"""Assemble and publish the already-validated public NGB v1.0 package."""
import base64
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import zipfile

REPO = "slimshadykor-cmd/korean-patches"
TAG = "ngb-v1.0"
assert os.environ["GITHUB_REPOSITORY"] == REPO
API = "https://api.github.com/repos/" + REPO
HEADERS = {"Authorization": "Bearer " + os.environ["GH_TOKEN"],
           "Accept": "application/vnd.github+json", "User-Agent": "NGB-Release-Publisher"}

def call(url, method="GET", payload=None, binary=None, mime=None):
    headers = dict(HEADERS)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if binary is not None:
        body = binary
        headers["Content-Type"] = mime or "application/octet-stream"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        body = response.read()
        return json.loads(body) if body else None

manifest = json.loads(Path(".github/ngb-v1.0-manifest.json").read_text())
assert manifest["file"] == "NGB_Korean_Patch_v1.0.zip"
assert manifest["bytes"] == 49440638
assert manifest["sha256"] == "d6b3ebde783ef27a0fb752c926d647ee525f1cb3af02762ce1864d400373955b"
destination = Path(os.environ["RUNNER_TEMP"]) / manifest["file"]
digest = hashlib.sha256()
with destination.open("wb") as output:
    for part in manifest["parts"]:
        blob = call(API + "/git/blobs/" + part["sha"])
        assert blob["encoding"] == "base64"
        content = base64.b64decode(blob["content"])
        assert len(content) == part["bytes"]
        assert hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest() == part["sha"]
        output.write(content)
        digest.update(content)
assert destination.stat().st_size == manifest["bytes"]
assert digest.hexdigest() == manifest["sha256"]
with zipfile.ZipFile(destination) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == 2710
    for name in names:
        lower = name.lower()
        assert not any(part in {"saves", "savegames", "udata", "tdata"} for part in lower.split("/"))
        assert not lower.endswith((".iso", ".xbe", ".sav", ".qcow2", ".vhd", ".xsv", ".xbs"))
    plan = json.loads(archive.read("ngb_native11/assets/build_plan.json"))
    assert not plan.get("health_protection")
print("Public ZIP reassembled and verified: " + digest.hexdigest())

release = call(API + "/releases/tags/" + TAG)
assert release['id'] == 409696104 and not release['draft'] and not release.get('immutable')
existing = {a['name']: a for a in release['assets']}
expected = {a['name']: a for a in manifest['oldAssets']}
for path in [destination, Path('xbox/ninja-gaiden-black/SHA256SUMS.txt')]:
    data = path.read_bytes()
    digest = 'sha256:' + hashlib.sha256(data).hexdigest()
    previous = existing.get(path.name)
    if previous and previous.get('digest') == digest:
        continue
    if previous:
        assert previous['id'] == expected[path.name]['id']
        assert previous['digest'] == expected[path.name]['digest']
    pending = existing.get(path.name + '.pending')
    if pending:
        assert pending.get('digest') == digest
    else:
        upload = release['upload_url'].split('{')[0]
        pending = call(upload + '?name=' + urllib.parse.quote(path.name + '.pending'), 'POST', binary=data,
                       mime='application/zip' if path.suffix == '.zip' else 'text/plain')
    assert pending['size'] == len(data) and pending['digest'] == digest
    if previous:
        call(API + '/releases/assets/' + str(previous['id']), 'DELETE')
    renamed = call(API + '/releases/assets/' + str(pending['id']), 'PATCH', {'name': path.name})
    assert renamed['name'] == path.name and renamed['digest'] == digest
    print('Replaced and verified: ' + path.name)
body = Path('xbox/ninja-gaiden-black/RELEASE_NOTES.md').read_text()
call(API + '/releases/409696104', 'PATCH', {'body': body})
print('Corrected public patch replaced in the existing v1.0 release.')

