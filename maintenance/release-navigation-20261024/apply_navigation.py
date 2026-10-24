"""Apply the reviewed release-body changes once; never alter release assets."""
import json
import os
import sys
import urllib.request
from pathlib import Path


def api(repo, path, payload=None):
    request = urllib.request.Request(
        'https://api.github.com/repos/' + repo + '/' + path,
        data=None if payload is None else json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'Content-Type': 'application/json',
            'User-Agent': 'patch-release-navigation',
        },
        method='GET' if payload is None else 'PATCH',
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def invariant(release):
    fields = ('id', 'tag_name', 'name', 'draft', 'prerelease', 'target_commitish', 'published_at', 'immutable')
    asset_fields = ('id', 'name', 'size', 'digest', 'state', 'browser_download_url')
    assets = sorted(
        [{key: asset.get(key) for key in asset_fields} for asset in release['assets']],
        key=lambda asset: asset['id'],
    )
    return {**{key: release.get(key) for key in fields}, 'assets': assets}


def main():
    plan = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    repo = plan['repository']
    if os.environ.get('GITHUB_REPOSITORY') != repo:
        raise RuntimeError('Repository mismatch')
    # Preflight every destination and source before performing any writes.
    for target in plan['destinations']:
        release = api(repo, 'releases/' + str(target['id']))
        if release['tag_name'] != target['tag'] or release['html_url'] != target['url']:
            raise RuntimeError('Destination mismatch')
        if release['draft'] or release['prerelease'] or not release['assets']:
            raise RuntimeError('Destination is not a published release with assets')
    checked = []
    for edit in plan['edits']:
        current = api(repo, 'releases/' + str(edit['id']))
        if current['tag_name'] != edit['tag'] or current['draft'] or current.get('immutable'):
            raise RuntimeError('Source identity/status mismatch: ' + edit['tag'])
        if current.get('body') not in (edit['before'], edit['after']):
            raise RuntimeError('Concurrent release edit detected: ' + edit['tag'])
        checked.append((edit, current))
    if '--apply' not in sys.argv:
        print('Preflight passed:', len(checked), 'release bodies')
        return
    for edit, original in checked:
        path = 'releases/' + str(edit['id'])
        current = api(repo, path)
        if invariant(current) != invariant(original):
            raise RuntimeError('Release metadata changed concurrently: ' + edit['tag'])
        if current.get('body') == edit['after']:
            print('Already current:', edit['tag'])
            continue
        if current.get('body') != edit['before']:
            raise RuntimeError('Concurrent body edit detected: ' + edit['tag'])
        api(repo, path, {'body': edit['after']})
        verified = api(repo, path)
        if verified.get('body') != edit['after'] or invariant(verified) != invariant(original):
            raise RuntimeError('Post-write verification failed: ' + edit['tag'])
        print('Verified navigation only:', edit['tag'])
    print('Completed:', len(checked), 'release bodies')


if __name__ == '__main__':
    main()
