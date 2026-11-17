#!/usr/bin/env python3
"""Check this review snapshot's files. Never execute programs or contact a model."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.directory.resolve()
    manifest = json.loads((root / 'SYNC_MANIFEST.json').read_text())
    files = manifest['files']
    canonical = json.dumps(files, sort_keys=True, separators=(',', ':')).encode()
    if hashlib.sha256(canonical).hexdigest() != manifest['bundle_sha256']:
        raise ValueError('The manifest file list differs from its recorded identity')
    failures = []
    for name, expected in files.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe manifest path')
        path = root / relative
        if not path.is_file():
            failures.append({'file': name, 'issue': 'missing'})
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append({'file': name, 'issue': 'changed'})
    print(json.dumps({'study': manifest['study_id'], 'files_checked': len(files),
                      'bundle_sha256': manifest['bundle_sha256'],
                      'status': 'verified' if not failures else 'mismatch',
                      'failures': failures}, indent=2))
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
