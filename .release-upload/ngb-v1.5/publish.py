"""Publish the previously verified public v1.5 archive, without rebuilding it."""
import hashlib
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

REPO = "slimshadykor-cmd/korean-patches"
RELEASE_ID = 415405366
TAG = "ngb-v1.5"
TARGET = "c673c27e1d26f0f2f89f2b08f5ce8cfecbc011a8"
ZIP_NAME = "NGB_Korean_Patch_v1.5.zip"
ZIP_SIZE = 49486705
ZIP_SHA = "3e31105e9748370776542faec3cf5b6bbc63f8ff36d0033300e666a8866a2f78"
ROOT = Path(__file__).resolve().parent
API = "https://api.github.com/repos/" + REPO


def request(url, method="GET", data=None, content_type="application/json"):
    if not url.startswith((API + "/", "https://uploads.github.com/repos/" + REPO + "/")):
        raise RuntimeError("Unexpected API destination")
    headers = {
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": content_type,
        "User-Agent": "ngb-v1.5-publication",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def check_asset(asset, name, data):
    expected = "sha256:" + hashlib.sha256(data).hexdigest()
    if not (asset["name"] == name and asset["size"] == len(data)
            and asset["state"] == "uploaded" and asset.get("digest") == expected):
        raise RuntimeError("Remote asset integrity mismatch: " + name)


def main():
    parts = sorted(ROOT.glob("archive.part*"))
    if [p.name for p in parts] != [f"archive.part{i:02d}" for i in range(7)]:
        raise RuntimeError("Unexpected archive parts")
    archive = b"".join(p.read_bytes() for p in parts)
    if len(archive) != ZIP_SIZE or hashlib.sha256(archive).hexdigest() != ZIP_SHA:
        raise RuntimeError("Archive reconstruction failed integrity verification")
    files = {
        ZIP_NAME: archive,
        "SHA256SUMS.txt": (ROOT / "SHA256SUMS.txt").read_bytes(),
        "ORIGINAL_HASHES.txt": (ROOT / "ORIGINAL_HASHES.txt").read_bytes(),
    }
    if files["SHA256SUMS.txt"].decode().strip() != ZIP_SHA + "  " + ZIP_NAME:
        raise RuntimeError("Checksum file mismatch")
    release_url = API + f"/releases/{RELEASE_ID}"
    release = request(release_url)
    if release["tag_name"] != TAG or release["prerelease"]:
        raise RuntimeError("Unexpected release target")
    existing = {asset["name"]: asset for asset in release["assets"]}
    if set(existing) - set(files):
        raise RuntimeError("Release contains unexpected assets")
    for name, data in files.items():
        if name in existing:
            asset = existing[name]
        elif not release["draft"]:
            raise RuntimeError("Refusing to alter an incomplete published release")
        else:
            upload_url = release["upload_url"].split("{")[0]
            asset = request(upload_url + "?" + urllib.parse.urlencode({"name": name}),
                            "POST", data,
                            "application/zip" if name.endswith(".zip") else "text/plain")
        check_asset(asset, name, data)
        print("Verified uploaded asset:", name, len(data), asset["digest"], flush=True)
    release = request(release_url)
    if set(a["name"] for a in release["assets"]) != set(files):
        raise RuntimeError("Final asset list mismatch")
    for asset in release["assets"]:
        check_asset(asset, asset["name"], files[asset["name"]])
    if release["draft"]:
        release = request(release_url, "PATCH", json.dumps({
            "draft": False, "prerelease": False,
            "target_commitish": TARGET, "make_latest": "true",
        }).encode())
    release = request(release_url)
    if release["draft"] or release["tag_name"] != TAG or not release["published_at"]:
        raise RuntimeError("Release publication was not confirmed")
    print("Published:", release["html_url"], flush=True)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
        summary.write(f"Published [{TAG}]({release['html_url']}).\n\n")
        summary.write(f"ZIP SHA-256: `{ZIP_SHA}`\n")


if __name__ == "__main__":
    main()
