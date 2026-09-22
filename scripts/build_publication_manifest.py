#!/usr/bin/env python3
"""Bind portable release files; never include studies, credentials or runtime caches."""
import argparse
import hashlib
import json
from pathlib import Path

MANIFEST = Path('evidence/manifest.json')
SKIP_DIRS = {'.git', '__pycache__', '.venv', '.pytest_cache', '.mypy_cache'}
PRIVATE_DIRS = {'.runs', '.local', '.metals', '.scala-build', '.vscode', 'proposals', 'paper'}
BINARY_OUTPUTS = {'.pyc', '.pyo', '.jar', '.class', '.tif', '.tiff', '.zip', '.gz', '.tar'}


def generate(root):
    root = Path(root).resolve(strict=True)
    records = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts) or relative == MANIFEST:
            continue
        if path.is_symlink():
            raise ValueError('Publication files must not be symlinks: ' + relative.as_posix())
        if path.is_dir():
            continue
        if (any(part in PRIVATE_DIRS for part in relative.parts)
                or (path.name.startswith('.env') and path.name != '.env.example')
                or path.suffix.lower() in BINARY_OUTPUTS
                or (relative.parts[0] == 'studies' and path.suffix != '.py')
                or relative.parts[0] == 'evidence'):
            raise ValueError('Private or generated output in publication snapshot: ' + relative.as_posix())
        data = path.read_bytes()
        records.append({'path': relative.as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    value = {'schema_version': 1, 'kind': 'publication_integrity_manifest',
             'scope': 'Portable release source, tests, configuration and documentation only; no study results.',
             'limitations': 'Integrity inventory, not a signature, treatment approval or successful evaluation.',
             'files': records}
    target = root / MANIFEST
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + '\n')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    data = generate(parser.parse_args().root)
    print(f"Bound {len(data['files'])} publication files; no model, library or study execution.")
