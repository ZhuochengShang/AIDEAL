#!/usr/bin/env python3
"""Install a completed README on unchecked-out Git branch refs only.

Uses temporary indexes and an atomic compare-and-swap ref transaction. The
Original checkout and its index are never switched, staged, or rewritten.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def git(repo, *args, data=None, env=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], input=data, env=env, stderr=subprocess.PIPE)


def original_identity(repo):
    head = git(repo, 'rev-parse', 'HEAD').decode().strip()
    try:
        branch = git(repo, 'symbolic-ref', '--quiet', 'HEAD').decode().strip()
    except subprocess.CalledProcessError as error:
        if error.returncode != 1:  # 1 means HEAD is not a symbolic reference.
            raise
        branch = None
    return {'head': head, 'branch': branch,
            'working_diff_sha256': sha(git(repo, 'diff', '--binary')),
            'index_diff_sha256': sha(git(repo, 'diff', '--cached', '--binary'))}


def install(manifest_path, receipt_path):
    manifest_path, receipt_path = Path(manifest_path), Path(receipt_path)
    spec = json.loads(manifest_path.read_text())
    repo, readme = Path(spec['repository']).resolve(), Path(spec['readme']).resolve()
    completion_path = Path(spec['completion']).resolve()
    completion = json.loads(completion_path.read_text())
    content = readme.read_bytes()
    if completion.get('status') != 'authored_not_execution_validated' or completion.get('readme_sha256') != sha(content):
        raise ValueError('README has no matching successful author completion receipt')
    destination = spec.get('destination', 'docs/LLM_readme.md')
    path = PurePosixPath(destination)
    if path.is_absolute() or not path.parts or any(p in ('..', '.git') for p in path.parts) or '\n' in destination:
        raise ValueError('Destination must be a repository-relative documentation file')
    branches = spec['branches']
    if not isinstance(branches, dict) or not branches:
        raise ValueError('Provide target branch names and exact expected old commits')
    refs = {}
    for name, old in branches.items():
        git(repo, 'check-ref-format', '--branch', name)
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', old):
            raise ValueError('Expected branch commits must be complete Git hashes')
        refs['refs/heads/' + name] = old
    common = Path(git(repo, 'rev-parse', '--git-common-dir').decode().strip())
    if not common.is_absolute():
        common = repo / common
    with (common / 'aideal-readme-install.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        worktrees = git(repo, 'worktree', 'list', '--porcelain').decode().splitlines()
        checked_out = {line[7:] for line in worktrees if line.startswith('branch ')}
        if set(refs) & checked_out:
            raise ValueError('Target branch is checked out; refs-only installation refused')
        identity = {'manifest_sha256': sha(manifest_path.read_bytes()), 'readme_sha256': sha(content),
                    'completion_sha256': sha(completion_path.read_bytes()), 'repository': str(repo),
                    'destination': destination, 'original': original_identity(repo)}
        pending = receipt_path.with_suffix(receipt_path.suffix + '.pending')
        saved_path = receipt_path if receipt_path.exists() else pending
        if saved_path.exists():
            result = json.loads(saved_path.read_text())
            if result['identity'] != identity:
                raise ValueError('Installation inputs or Original checkout changed')
        else:
            updates = {}
            for ref, old in refs.items():
                if git(repo, 'rev-parse', ref).decode().strip() != old:
                    raise ValueError('Target branch changed before installation: ' + ref)
                existing = git(repo, 'ls-tree', old, '--', destination).decode().strip()
                if existing:
                    mode, kind, _ = existing.split('\t')[0].split()
                    if kind != 'blob' or mode not in ('100644', '100755') or git(repo, 'show', old + ':' + destination) != content:
                        raise ValueError('Destination already contains different content; preserve it and use a new branch/path')
                    updates[ref] = {'old': old, 'new': old}
                    continue
                with tempfile.TemporaryDirectory(prefix='aideal-readme-index-') as temporary:
                    env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
                    git(repo, 'read-tree', old, env=env)
                    blob = git(repo, 'hash-object', '-w', '--stdin', data=content).decode().strip()
                    git(repo, 'update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + destination, env=env)
                    tree = git(repo, 'write-tree', env=env).decode().strip()
                    new = git(repo, '-c', 'commit.gpgsign=false', 'commit-tree', tree, '-p', old,
                              data=b'Add completed AIDEAL-generated API documentation\n').decode().strip()
                    updates[ref] = {'old': old, 'new': new}
            result = {'status': 'installed', 'identity': identity, 'branches': updates}
            atomic(pending, result)
        actual = {ref: git(repo, 'rev-parse', ref).decode().strip() for ref in refs}
        if any(actual[ref] not in (row['old'], row['new']) for ref, row in result['branches'].items()):
            raise ValueError('Target branch changed after preparation')
        changed = [ref for ref, row in result['branches'].items() if row['old'] != row['new']]
        if changed and not (all(actual[r] == result['branches'][r]['old'] for r in changed) or
                            all(actual[r] == result['branches'][r]['new'] for r in changed)):
            raise ValueError('Mixed branch state; explicit review required')
        if any(actual[ref] != row['new'] for ref, row in result['branches'].items()):
            commands = ['start']
            for ref, row in result['branches'].items():
                commands.append(f"update {ref} {row['new']} {row['old']}")
            git(repo, 'update-ref', '--stdin', data=('\n'.join(commands + ['prepare', 'commit', ''])).encode())
        for ref, row in result['branches'].items():
            if git(repo, 'rev-parse', ref).decode().strip() != row['new'] or git(repo, 'show', ref + ':' + destination) != content:
                raise ValueError('Installed branch verification failed')
        if original_identity(repo) != identity['original']:
            raise ValueError('Original checkout changed during installation')
        if not receipt_path.exists():
            atomic(receipt_path, result)
        pending.unlink(missing_ok=True)
        return result


def preflight_generation(manifest_path):
    """Catch branch and Git identity blockers before starting paid generation."""
    spec = json.loads(Path(manifest_path).read_text())
    repo = Path(spec['repository']).resolve()
    original_identity(repo)
    checked = {line[7:] for line in git(repo, 'worktree', 'list', '--porcelain').decode().splitlines()
               if line.startswith('branch ')}
    for name, old in spec['branches'].items():
        git(repo, 'check-ref-format', '--branch', name)
        ref = 'refs/heads/' + name
        if ref in checked or git(repo, 'rev-parse', ref).decode().strip() != old:
            raise ValueError('Target branch is checked out or differs from its expected baseline')
    git(repo, 'var', 'GIT_AUTHOR_IDENT')
    git(repo, 'var', 'GIT_COMMITTER_IDENT')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--run-command', nargs=argparse.REMAINDER,
                        help='Optional exact generation argv to run successfully before installation')
    args = parser.parse_args()
    recovering = args.receipt.exists() or args.receipt.with_suffix(args.receipt.suffix + '.pending').exists()
    if args.run_command and not recovering:
        preflight_generation(args.manifest)
        completed = subprocess.run(args.run_command)
        if completed.returncode:
            return completed.returncode
    result = install(args.manifest, args.receipt)
    print(json.dumps({'status': result['status'], 'destination': result['identity']['destination'],
                      'branches': result['branches']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
