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
        return json.load(response)

manifest = json.loads(Path(".github/ngb-v1.0-manifest.json").read_text())
assert manifest["file"] == "NGB_Korean_Patch_v1.0.zip"
assert manifest["bytes"] == 49439325
assert manifest["sha256"] == "6a9880e124713e1ee744808e3d60c127dba18da97c31f2a5dd360619ddc3c743"
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
    assert len(names) == 2709
    for name in names:
        lower = name.lower()
        assert not any(part in {"saves", "savegames", "udata", "tdata"} for part in lower.split("/"))
        assert not lower.endswith((".iso", ".xbe", ".sav", ".qcow2", ".vhd", ".xsv", ".xbs"))
    plan = json.loads(archive.read("ngb_native11/assets/build_plan.json"))
    assert not plan.get("health_protection")
print("Public ZIP reassembled and verified: " + digest.hexdigest())

try:
    release = call(API + "/releases/tags/" + TAG)
except urllib.error.HTTPError as error:
    if error.code != 404:
        raise
    release = call(API + "/releases", "POST", {
        "tag_name": TAG, "target_commitish": os.environ["GITHUB_SHA"],
        "name": "닌자가이덴 블랙 한글패치 v1.0", "draft": True,
        "prerelease": False,
        "body": Path("xbox/ninja-gaiden-black/RELEASE_NOTES.md").read_text()})

assets = [destination, Path("xbox/ninja-gaiden-black/SHA256SUMS.txt"),
          Path("xbox/ninja-gaiden-black/ORIGINAL_HASHES.txt")]
existing = {asset["name"]: asset for asset in release.get("assets", [])}
for path in assets:
    data = path.read_bytes()
    expected = "sha256:" + hashlib.sha256(data).hexdigest()
    if path.name in existing:
        assert existing[path.name].get("digest") == expected, "Existing release asset differs"
        continue
    assert release["draft"], "Refuse to add files to an already-published release"
    upload = release["upload_url"].split("{")[0]
    mime = "application/zip" if path.suffix == ".zip" else "text/plain"
    asset = call(upload + "?name=" + urllib.parse.quote(path.name), "POST", binary=data, mime=mime)
    assert asset["size"] == len(data)
    assert asset.get("digest") == expected
    print("Uploaded and verified: " + path.name)

if release["draft"]:
    release = call(API + "/releases/" + str(release["id"]), "PATCH", {"draft": False, "make_latest": "true"})
print("Published: " + release["html_url"])
