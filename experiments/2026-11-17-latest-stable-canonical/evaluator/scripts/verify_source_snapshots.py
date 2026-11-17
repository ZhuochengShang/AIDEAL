#!/usr/bin/env python3
"""Audit exact upstream snapshot trees; optional guarded repair of untreated refs.

Default is read-only. --apply requires five identical untouched study branches,
no Git index lock, and exact expected archive tree before any correction. Repairs
create a child commit retaining the original snapshot; no histories are deleted.
Only tracked archive/supplement entries belong to the target tree. Runtime builds,
supplemental fixtures and other untracked files never enter the commit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile

ARMS = ('original', 'readme-only', 'alias-only', 'error-hints-only', 'combined')
PREFIX = 'study/2026-11-16-gemini-3.1-flash-lite/'


def oid(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def tree_oid(entries):
    nested = {}
    for path, entry in entries.items():
        parts = PurePosixPath(path).parts
        node = nested
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = (entry['mode'], entry['oid'])
    def build(node):
        packed = b''
        for name, value in sorted(node.items(), key=lambda row: (row[0] + ('/' if isinstance(row[1], dict) else '')).encode()):
            mode, value_oid = ('40000', build(value)) if isinstance(value, dict) else value
            packed += mode.encode() + b' ' + name.encode() + b'\0' + bytes.fromhex(value_oid)
        return oid('tree', packed)
    return build(nested)


def archive_entries(archive, supplements, root):
    entries = {}
    with tarfile.open(archive) as stream:
        for item in stream.getmembers():
            path = PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or '\n' in item.name:
                raise ValueError('Unsafe archive path')
            if not item.isfile() and not item.issym():
                continue
            data = item.linkname.encode() if item.issym() else stream.extractfile(item).read()
            mode = '120000' if item.issym() else ('100755' if item.mode & 0o111 else '100644')
            entries[item.name] = {'mode': mode, 'oid': oid('blob', data), 'data': data, 'archive_data': data}
    for supplement in supplements:
        data = (root / supplement['payload']).read_bytes()
        if hashlib.sha256(data).hexdigest() != supplement['sha256']:
            raise ValueError('Supplement hash mismatch')
        previous = entries.get(supplement['relative'])
        entries[supplement['relative']] = {'mode': supplement['mode'], 'oid': oid('blob', data), 'data': data,
                                          'archive_data': previous['data'] if previous else None}
    return entries


def audit_or_repair(name, source, archive, supplements, root, expected, apply):
    def git(*args, data=None, env=None, okay=(0,)):
        result = subprocess.run(['git', '-C', str(source), *args], input=data, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env)
        if result.returncode not in okay:
            raise RuntimeError(result.stderr.decode().strip())
        return result.stdout
    entries = archive_entries(archive, supplements, root)
    canonical = tree_oid(entries)
    if canonical != expected:
        raise ValueError(f'{name}: archive/supplement tree {canonical} != upstream tree {expected}; refuse mutation')
    head = git('rev-parse', 'HEAD').decode().strip()
    current_tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
    actual = {}
    for row in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            mode, kind, blob = meta.decode().split()
            actual[path.decode()] = (mode, blob)
    changes = [p for p in sorted(set(entries) | set(actual))
               if actual.get(p) != ((entries[p]['mode'], entries[p]['oid']) if p in entries else None)]
    refs = {}
    for arm in ARMS:
        refs[arm] = git('rev-parse', '--verify', 'refs/heads/' + PREFIX + arm).decode().strip()
    report = {'library': name, 'expected_tree': expected, 'actual_tree': current_tree,
              'old_snapshot_commit': head, 'canonical_files': len(entries), 'tree_changes': changes,
              'branches': refs, 'status': 'verified' if canonical == current_tree else 'correction_required'}
    if not changes:
        if set(refs.values()) != {head}:
            report['status'] = 'tree_verified_branches_diverged'
        return report
    if not apply:
        return report
    if set(refs.values()) != {head} or git('branch', '--show-current').decode().strip() != PREFIX + 'original':
        raise ValueError(f'{name}: branches have diverged or original is not selected; preserve treatments and stop')
    if (source / '.git/index.lock').exists():
        raise ValueError(f'{name}: another Git writer owns the index')
    # Never overwrite an operator edit or generated build source. A changed file
    # must still equal archive bytes (export-subst case) or the desired HEAD bytes.
    for path in changes:
        target = source / path
        if path in entries and target.exists():
            current = os.readlink(target).encode() if target.is_symlink() else target.read_bytes()
            if current not in (entries[path]['data'], entries[path]['archive_data']):
                raise ValueError(f'{name}: working file changed independently: {path}')
    with tempfile.TemporaryDirectory(prefix='aideal-exact-source-index-') as directory:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory) / 'index')}
        git('read-tree', head, env=env)
        rows = []
        for path in changes:
            if path not in entries:
                rows.append('0 ' + '0' * 40 + '\t' + path + '\n')
            else:
                entry = entries[path]
                written = git('hash-object', '-w', '--stdin', data=entry['data']).decode().strip()
                if written != entry['oid']:
                    raise ValueError('Git wrote unexpected blob')
                rows.append(entry['mode'] + ' ' + entry['oid'] + '\t' + path + '\n')
        git('update-index', '--index-info', data=''.join(rows).encode(), env=env)
        result_tree = git('write-tree', env=env).decode().strip()
        if result_tree != expected:
            raise ValueError('Temporary exact-source index has unexpected tree')
        new_commit = git('commit-tree', result_tree, '-p', head,
                         data=b'Restore exact upstream source snapshot bytes after archive attribute substitution\n').decode().strip()
        transaction = 'start\n' + ''.join(f'update refs/heads/{PREFIX}{arm} {new_commit} {head}\n' for arm in ARMS) + 'prepare\ncommit\n'
        git('update-ref', '--stdin', data=transaction.encode())
        git('read-tree', new_commit)
        for path in changes:
            if path not in entries:
                continue  # Extra runtime files remain on disk, now untracked.
            entry, target = entries[path], source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if entry['mode'] == '120000':
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.symlink_to(entry['data'].decode())
            else:
                target.write_bytes(entry['data'])
                target.chmod(int(entry['mode'], 8) & 0o777)
        report.update(status='corrected', new_snapshot_commit=new_commit, actual_tree=result_tree,
                      branches={arm: new_commit for arm in ARMS}, old_snapshot_preserved_as_parent=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--expected-trees', type=Path, required=True)
    parser.add_argument('--libraries', nargs='+')
    parser.add_argument('--sedona-archive', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((args.study / 'export.json').read_text())
    expected = json.loads(args.expected_trees.read_text())
    specs = {row['library']: row for row in manifest['source_trees']}
    if args.sedona_archive:
        specs['sedonadb'] = {'archive': str(args.sedona_archive), 'head_archive_supplements': []}
    results = []
    failed = False
    for name in args.libraries or list(specs):
        try:
            spec = specs[name]
            row = audit_or_repair(name, args.study / 'sources' / name, args.study / spec['archive'],
                                  spec.get('head_archive_supplements', []), args.study, expected[name], args.apply)
            results.append(row)
            failed |= row['status'] not in ('verified', 'corrected')
        except Exception as exc:
            failed = True
            results.append({'library': name, 'status': 'blocked', 'error': str(exc)})
    print(json.dumps({'mode': 'apply' if args.apply else 'read_only', 'sources': results}, indent=2))
    return 2 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
