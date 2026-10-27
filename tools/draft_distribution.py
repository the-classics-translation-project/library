"""Publish only hash-verified imported drafts under the owner's standing policy.

This module never submits a model job, changes the relay queue or edits catalog.json.
It runs in the trusted local main checkout; the private attempt ledgers stay local.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import subprocess

import ctp as c
import relay_coordinator as coordinator


def now():
    return datetime.now(timezone.utc).isoformat()


def git(root, *args, allow_missing=False):
    proc = subprocess.run(['git', '-C', str(root), *args], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        if allow_missing:
            return None
        raise c.ProjectError('Git draft distribution failed at '+args[0]+': '+proc.stderr.strip())
    return proc.stdout.strip()


def git_bytes(root, *args):
    proc = subprocess.run(['git', '-C', str(root), *args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout if proc.returncode == 0 else None


def policy(root):
    value = c.read_json(root/'draft-distribution.json')
    project = c.read_json(root/'project.json')
    c.check(type(value.get('schema_version')) is int and value['schema_version'] == 1 and
            type(value.get('enabled')) is bool,
            'Standing draft-distribution policy has invalid state')
    c.check(value.get('repository') == project['repository'] and
            value.get('authorized_by') in project['maintainers'] and
            value.get('audience') == 'public-git-draft' and
            type(value.get('classes')) is list and
            set(value['classes']) == {'guide', 'translation'},
            'Standing draft-distribution policy is invalid')
    return value


def admitted(root, work):
    c.ident(work)
    wd = root/'books'/work
    rights = c.read_json(wd/'rights.json')
    c.check(rights.get('work') == work and rights.get('eligible') is True and
            rights.get('status') == 'acquired' and
            rights.get('countries', {}).get('US', {}).get('status') == 'pass' and
            rights.get('countries', {}).get('JP', {}).get('status') == 'pass',
            'Draft source lacks admitted US/Japan rights: '+work)
    from acquire_queue import validate_record
    validate_record(wd, rights['ebook_id'])


def _safe_name(root, name):
    c.check(isinstance(name, str) and name and not name.startswith('/') and
            '\\' not in name and not any(ord(ch) < 32 for ch in name),
            'Unsafe draft output path')
    parts = PurePosixPath(name).parts
    c.check(parts and all(part not in ('.', '..') for part in parts) and
            PurePosixPath(name).as_posix() == name and name != 'catalog.json',
            'Unsafe draft output path')
    path = root/name
    local_parts = [root.joinpath(*parts[:i]) for i in range(1, len(parts)+1)]
    c.check(path.resolve().is_relative_to(root) and path.is_file() and
            not any(parent.is_symlink() for parent in local_parts),
            'Missing or linked draft output: '+name)
    return path


def candidates(root):
    """Return only imported coordinator and direct-relay outputs not yet pushed."""
    result = []
    for row in coordinator.records(root):
        if row.get('state') != 'imported' or row.get('pushed_at'):
            continue
        c.check(row.get('authorization') and
                row['authorization'].get('request_sha256') == row['request_sha256'],
                'Imported attempt lacks exact submission authorization: '+row['id'])
        c.check(row.get('adapter') in ('legacy_guide', 'independent_guide', 'translation'),
                'Unsupported draft adapter')
        coordinator.request_path(root, row)
        returned = coordinator.archive(root, row)/'response.zip'
        c.check(returned.is_file() and not returned.is_symlink() and
                c.digest(returned.read_bytes()) == row.get('response_sha256'),
                'Imported attempt lacks its exact return ZIP: '+row['id'])
        allowed = ['books/'+row['work']+'/reference/']
        if row.get('target'):
            allowed += ['books/'+row['work']+'/editions/'+row['target']+'/',
                        'revisions/'+row['work']+'/'+row['target']+'/']
        if row.get('issue') is not None:
            receipt = ('guide-results/' if row['adapter'] == 'legacy_guide' else
                       'translation-results/')+'issue-'+str(row['issue'])+'.json'
            allowed.append(receipt)
        result.append({'kind': 'coordinator', 'id': row['id'], 'work': row['work'],
                       'imported_at': row.get('imported_at', ''), 'outputs': row['outputs'],
                       'allowed': allowed, 'record': row})
    direct = root/'private/relay'
    for path in sorted(direct.glob('ctp-*/publication.json')):
        item = c.read_json(path)
        if item.get('state') != 'imported' or item.get('pushed_at'):
            continue
        attempt = path.parent.name
        c.check(item.get('attempt') == attempt and item.get('schema_version') == 1,
                'Direct draft publication identity mismatch')
        job = c.read_json(path.parent/'job.json')
        c.check(job['manifest']['attempt'] == attempt and
                job['manifest']['work'] == item['work'] and
                job['manifest']['edition'] == item['edition'] and
                job['package_sha256'] == item['request_sha256'],
                'Direct draft request identity mismatch')
        request = path.parent/(attempt+'.zip')
        returned = root/'books'/item['work']/'editions'/item['edition']/'relay'/attempt/'result.zip'
        c.check(request.is_file() and not request.is_symlink() and
                c.digest(request.read_bytes()) == item['request_sha256'] and
                returned.is_file() and not returned.is_symlink() and
                c.digest(returned.read_bytes()) == item['result_sha256'],
                'Direct draft archive differs from import')
        result.append({'kind': 'direct', 'id': attempt, 'work': item['work'],
                       'imported_at': item['imported_at'], 'outputs': item['outputs'],
                       'allowed': ['books/'+item['work']+'/editions/'+item['edition']+'/'],
                       'record': item, 'record_path': path})
    return sorted(result, key=lambda item: (item['imported_at'], item['id']))


def publish_ready(root, push=True):
    """Commit imported drafts exactly once; retry an interrupted push safely."""
    root = root.resolve()
    authorization = policy(root)
    if not authorization['enabled']:
        return {'published': [], 'commit': None, 'pushed': False,
                'disabled': True, 'model_called': False}
    c.check(git(root, 'symbolic-ref', '--short', 'HEAD') == 'main',
            'Automatic draft distribution runs only from local main')
    c.check(not git(root, 'diff', '--cached', '--name-only'),
            'Staged changes require review before draft distribution')
    tracked_dirty = set(git(root, 'diff', '--name-only').splitlines())
    if push:
        remote = git(root, 'remote', 'get-url', 'origin')
        expected = 'https://github.com/'+authorization['repository']
        c.check(remote in (expected, expected+'.git'), 'Origin is not the authorized repository')
        git(root, 'fetch', 'origin')
        c.check(git(root, 'merge-base', '--is-ancestor', 'origin/main', 'HEAD', allow_missing=True) is not None or
                git(root, 'merge-base', '--is-ancestor', 'HEAD', 'origin/main', allow_missing=True) is not None,
                'Local main and origin/main diverged')
        if git(root, 'rev-parse', 'HEAD') != git(root, 'rev-parse', 'origin/main'):
            # A prior local publication commit may be ahead; never reset it.
            if git(root, 'merge-base', '--is-ancestor', 'HEAD', 'origin/main', allow_missing=True) is not None:
                c.check(not tracked_dirty,
                        'Local main is behind GitHub while imported tracked drafts are modified; review before updating')
                git(root, 'merge', '--ff-only', 'origin/main')
            else:
                c.check(git(root, 'merge-base', '--is-ancestor', 'origin/main', 'HEAD', allow_missing=True) is not None,
                        'Local main is not a fast-forward of origin/main')
        authorization = policy(root)  # A fast-forward may have disabled the policy.
        if not authorization['enabled']:
            return {'published': [], 'commit': None, 'pushed': False,
                    'disabled': True, 'model_called': False}
    items = candidates(root)
    if not items:
        return {'published': [], 'commit': None, 'pushed': False, 'model_called': False}
    changes = {}
    for item in items:
        admitted(root, item['work'])
        c.check(isinstance(item['outputs'], dict) and item['outputs'],
                'Imported attempt has no publication outputs: '+item['id'])
        for name, hashes in item['outputs'].items():
            c.check(any(name.startswith(prefix) if prefix.endswith('/') else name == prefix
                        for prefix in item['allowed']),
                    'Draft output outside imported scope: '+name)
            c.check(isinstance(hashes, dict) and
                    (hashes.get('before') is None or isinstance(hashes.get('before'), str)) and
                    isinstance(hashes.get('after'), str) and len(hashes['after']) == 64,
                    'Invalid output hashes: '+name)
            if name in changes:
                c.check(changes[name]['after'] == hashes['before'],
                        'Overlapping imported drafts have a broken version chain: '+name)
                changes[name]['after'] = hashes['after']
            else:
                changes[name] = dict(hashes)
    for name, hashes in changes.items():
        path = _safe_name(root, name)
        c.check(c.digest(path.read_bytes()) == hashes['after'],
                'Draft output changed after import: '+name)
        prior = git_bytes(root, 'show', 'HEAD:'+name)
        prior_hash = c.digest(prior) if prior is not None else None
        c.check(prior_hash == hashes['before'] or prior_hash == hashes['after'],
                'Git baseline differs from imported draft: '+name)
    c.check(tracked_dirty <= set(changes),
            'Unrelated tracked changes require review before draft distribution')
    if push and git(root, 'rev-parse', 'HEAD') != git(root, 'rev-parse', 'origin/main'):
        c.check(git(root, 'rev-list', '--count', 'origin/main..HEAD') == '1' and
                git(root, 'log', '-1', '--format=%s') == 'Import validated draft guides and translations' and
                set(git(root, 'diff', '--name-only', 'origin/main..HEAD').splitlines()) <= set(changes),
                'Local main has unrelated unpushed commits')
    c.validate_project(root)
    names = sorted(changes)
    git(root, 'add', '--', *names)
    staged = set(git(root, 'diff', '--cached', '--name-only').splitlines())
    c.check(staged <= set(names), 'Unrelated files entered the draft commit')
    if staged:
        git(root, 'commit', '-m', 'Import validated draft guides and translations')
    commit = git(root, 'rev-parse', 'HEAD')
    if push:
        git(root, 'push', 'origin', 'HEAD:main')
    for item in items:
        record = item['record']
        record['commit'] = commit
        record['git_distribution_approved_at'] = authorization['authorized_on']
        if push:
            record['pushed_at'] = now()
        if item['kind'] == 'coordinator':
            coordinator.save(root, record)
        else:
            coordinator.atomic_json(item['record_path'], record)
    return {'published': [item['id'] for item in items], 'commit': commit,
            'pushed': push, 'model_called': False}
