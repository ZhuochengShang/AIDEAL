"""Validated, recorded runtime overrides shared by replay and fresh evaluation.

An override selects an isolated interpreter; it never installs dependencies or
changes the historical environment. Executable command paths retain virtual-
environment symlinks. Receipts bind the profile, setup evidence, interpreter
binary and the actual package files listed by the environment manifest.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shlex


@lru_cache(maxsize=16384)
def _cached_digest(path, stat_identity):
    # The stat key includes ctime so restoring an edited file's mtime cannot
    # silently reuse a digest. Large unchanged binaries are read only once.
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    after = Path(path).stat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != stat_identity:
        raise ValueError('Runtime file changed during verification: ' + path)
    return digest.hexdigest()


def _binding(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Runtime evidence paths must be absolute')
    path = path.resolve(strict=True)
    stat = path.stat()
    if not path.is_file():
        raise ValueError('Runtime evidence must be a regular file: ' + str(path))
    identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    return {'path': str(path), 'sha256': _cached_digest(str(path), identity)}


def _verify_binding(record):
    if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
        raise ValueError('Runtime file receipt requires exactly path and sha256')
    if not re.fullmatch('[0-9a-f]{64}', str(record['sha256'])):
        raise ValueError('Runtime file receipt has an invalid SHA256')
    current = _binding(record['path'])
    if current != record:
        raise ValueError('Runtime evidence changed: ' + str(record['path']))
    return current


def _executable(path):
    # Do NOT resolve the command path: venv/bin/python may point at a shared
    # base binary but uses its own pyvenv.cfg to select the environment.
    if not isinstance(path, str) or not Path(path).is_absolute() or '\x00' in path or '\n' in path:
        raise ValueError('Runtime command replacement must be an absolute executable path')
    if not Path(path).is_file() or not os.access(path, os.X_OK):
        raise ValueError('Runtime executable is missing or not executable: ' + path)
    return {'requested_path': path, **_binding(path)}


def load_runtime_profile(path):
    """Read and verify a profile plus actual installed-package evidence."""
    receipt = _binding(path)
    raw = json.loads(Path(receipt['path']).read_text())
    if raw.get('schema') != 1:
        raise ValueError('Runtime profile requires schema 1')
    changes = raw.get('command_replacements')
    if not isinstance(changes, dict) or not changes:
        raise ValueError('Runtime profile must declare executable replacements')
    executables = []
    for before, after in changes.items():
        if before == after:
            raise ValueError('Runtime profile contains a no-op replacement')
        executables.extend([_executable(before), _executable(after)])
    for field in ('environment_manifest', 'setup_report'):
        _verify_binding(raw.get(field))
    manifest = json.loads(Path(raw['environment_manifest']['path']).read_text())
    package_files = manifest.get('file_bindings')
    if not isinstance(package_files, list) or not package_files:
        raise ValueError('Environment manifest must bind actual installed files in file_bindings')
    if len({item.get('path') for item in package_files if isinstance(item, dict)}) != len(package_files):
        raise ValueError('Environment manifest contains duplicate or malformed file bindings')
    for item in package_files:
        _verify_binding(item)
    value = {**raw, 'profile_binding': receipt, 'executable_bindings': executables,
             'installed_file_bindings': package_files, 'validator_binding': _binding(__file__)}
    value['identity_sha256'] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return value


def runtime_profile_receipts(profile):
    """Flat receipts for experiment/authoring identity and resume verification."""
    if profile is None:
        return []
    # The manifest already binds the complete package-file list. Store its
    # receipt once per case instead of duplicating thousands of file hashes.
    records = [profile['profile_binding'], profile['environment_manifest'], profile['setup_report'],
               profile['validator_binding'],
               *({'path': row['path'], 'sha256': row['sha256']} for row in profile['executable_bindings'])]
    return sorted({row['path']: row for row in records}.values(), key=lambda row: row['path'])


def verify_runtime_profile(profile, command=None):
    """Reject receipt, installed-file or interpreter-link drift before/after execution."""
    if profile is None:
        return
    for receipt in runtime_profile_receipts(profile):
        _verify_binding(receipt)
    for receipt in profile['installed_file_bindings']:
        _verify_binding(receipt)
    for previous in profile['executable_bindings']:
        if _executable(previous['requested_path']) != previous:
            raise ValueError('Runtime interpreter link changed: ' + previous['requested_path'])
    if command is not None:
        tokens = set(shlex.split(command))
        changes = profile['command_replacements']
        if tokens.intersection(changes) or not tokens.intersection(changes.values()):
            raise ValueError('Execution command has not applied the declared runtime profile')


def require_runtime_ready(profile, library=None):
    """Block new paid work when the isolated setup still has unresolved prerequisites."""
    if profile is None:
        return
    verify_runtime_profile(profile)
    report = json.loads(Path(profile['setup_report']['path']).read_text())
    supported = report.get('supported_banks', [])
    if supported:
        if library is None and len(supported) == 1:
            library = supported[0]
        if library not in supported:
            raise ValueError('Runtime profile does not establish readiness for this library')
    unresolved = [item for item in report.get('unresolved_setup', [])
                  if not isinstance(item, dict) or not item.get('library')
                  or library is None or item['library'] == library]
    if unresolved:
        raise ValueError('Runtime setup has unresolved prerequisites; paid generation is blocked')


def remap_runtime_command(command, profile):
    """Replace exact executable tokens once, preserving shell operators/arguments."""
    if profile is None:
        return command
    verify_runtime_profile(profile)
    changes = profile['command_replacements']
    names = '|'.join(re.escape(name) for name in sorted(changes, key=len, reverse=True))
    pattern = re.compile(r"(?<![^\s;&|()])(?P<quote>['\"]?)(?P<path>" + names +
                         r")(?P=quote)(?=$|[\s;&|()<>])")
    mapped, count = pattern.subn(lambda match: shlex.quote(changes[match['path']]), command)
    if not count:
        raise ValueError('Runtime profile did not match an executable token in the command')
    return mapped
