import hashlib
import json
import os
from pathlib import Path
import urllib.request

REPO = "slimshadykor-cmd/korean-patches"
assert os.environ["GITHUB_REPOSITORY"] == REPO
API = "https://api.github.com/repos/" + REPO
headers = {"Authorization": "Bearer " + os.environ["GH_TOKEN"],
           "Accept": "application/vnd.github+json", "User-Agent": "NGB-Hash-Update"}

def request(url, method="GET", payload=None, data=None):
    h = dict(headers)
    if payload is not None:
        data = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    elif data is not None:
        h["Content-Type"] = "text/plain; charset=utf-8"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=120) as response:
        body = response.read()
        return json.loads(body) if body else None

release = request(API + "/releases/tags/ngb-v1.0")
assert release["id"] == 409696104 and not release["draft"]
assets = {x["name"]: x for x in release["assets"]}
assert assets["NGB_Korean_Patch_v1.0.zip"]["digest"] == "sha256:6a9880e124713e1ee744808e3d60c127dba18da97c31f2a5dd360619ddc3c743"
body = Path("xbox/ninja-gaiden-black/RELEASE_NOTES.md").read_text()
assert "9e09ba06bab10c53b8460f4c43b98b18" in body
assert "8581d5d0e2f90dcbcb63bd94bcb958a764f6d3a5" in body
request(API + "/releases/409696104", "PATCH", payload={"body": body})
data = Path("xbox/ninja-gaiden-black/ORIGINAL_HASHES.txt").read_bytes()
digest = "sha256:" + hashlib.sha256(data).hexdigest()
existing = assets.get("ORIGINAL_HASHES.txt")
if not existing or existing.get("digest") != digest:
    if existing:
        assert existing["id"] == 630867048
        request(API + "/releases/assets/" + str(existing["id"]), "DELETE")
    uploaded = request(release["upload_url"].split("{")[0] + "?name=ORIGINAL_HASHES.txt", "POST", data=data)
    assert uploaded["digest"] == digest
print("Original ISO MD5 and SHA-1 updated; public patch ZIP unchanged.")
