"""Prepare unvalidated function-local source hints without changing a library.

The JSON spec is proposal provenance, not the hint-delivery artifact. Evaluation
indexes the emitted source comments. This command never sends model requests,
changes a source checkout, applies its patch, or validates guidance empirically.
"""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from .source_hints import (MAX_SOURCE_BYTES, REQUIRED, index_source_hints,
                           insert_source_hint, strip_source_hints)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _read_spec(path):
    data = path.read_bytes()
    if len(data) > 2_000_000:
        raise ValueError('Source hint spec exceeds size bound')
    spec = json.loads(data)
    required = {'schema_version', 'api_function_ids', 'source_sha256', 'hints'}
    if not isinstance(spec, dict) or set(spec) != required or spec['schema_version'] != 1:
        raise ValueError('Expected source hint spec schema_version 1 and exactly its four fields')
    apis, hashes, hints = spec['api_function_ids'], spec['source_sha256'], spec['hints']
    if not isinstance(apis, dict) or not apis or not all(
            isinstance(k, str) and k and isinstance(v, str) and v for k, v in apis.items()):
        raise ValueError('api_function_ids must map API names to canonical function IDs')
    if len(set(apis.values())) != len(apis):
        raise ValueError('Canonical function IDs must be unique')
    if not isinstance(hashes, dict) or not all(isinstance(k, str) and isinstance(v, str)
            and re.fullmatch(r'[0-9a-f]{64}', v) for k, v in hashes.items()):
        raise ValueError('source_sha256 must contain exact lowercase SHA-256 values')
    if not isinstance(hints, list) or not hints or len(hints) > 2000:
        raise ValueError('Provide between 1 and 2000 source hint proposals')
    return spec, data


def _relative_source(function_id):
    if not isinstance(function_id, str):
        raise ValueError('function_id must be a canonical string')
    parts = function_id.rsplit(':', 2)
    if len(parts) != 3 or not parts[1].isdigit() or int(parts[1]) < 1:
        raise ValueError('function_id must be path:line:name')
    relative = Path(parts[0])
    if relative.is_absolute() or '..' in relative.parts or '\\' in parts[0]:
        raise ValueError('Source path must stay inside the source root')
    if relative.as_posix() != parts[0] or relative.suffix not in ('.py', '.scala', '.java', '.rs'):
        raise ValueError('Use a normalized Python, Scala, Java or Rust source path')
    return relative, int(parts[1])


def prepare_source_hints(source_root, spec_path, output):
    """Return a manifest for a new reviewable annotation-only proposal directory."""
    root, spec_path = Path(source_root).resolve(strict=True), Path(spec_path).resolve(strict=True)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError('Proposal output already exists; choose a new development directory')
    output = output.resolve()
    if not root.is_dir() or output.is_relative_to(root):
        raise ValueError('Proposal output must be outside the source checkout')
    spec, spec_data = _read_spec(spec_path)
    grouped, seen = {}, set()
    for hint in spec['hints']:
        if not isinstance(hint, dict) or set(hint) not in (set(REQUIRED), set(REQUIRED) | {'status'}):
            raise ValueError('A proposal must contain the exact source hint fields')
        if hint.get('status', 'unvalidated') != 'unvalidated':
            raise ValueError('New source hints must remain labelled unvalidated')
        if not all(isinstance(value, str) for value in hint.values()):
            raise ValueError('Source hint fields must be text')
        identity = hint['function_id']
        relative, line = _relative_source(identity)
        requirement = (identity, hint['requirement_id'])
        if identity not in spec['api_function_ids'].values() or requirement in seen:
            raise ValueError('Each proposed function must be mapped and its requirement ID unique')
        seen.add(requirement)
        grouped.setdefault(relative, []).append((line, {**hint, 'status': 'unvalidated'}))
    if set(spec['source_sha256']) != {p.as_posix() for p in grouped}:
        raise ValueError('Provide exactly one baseline hash per modified source file')

    # Validate every source and edit in memory before creating output directories.
    prepared, sources, patches = {}, [], []
    for relative, proposals in sorted(grouped.items()):
        source = (root / relative).resolve(strict=True)
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError('Proposed source escapes the source checkout')
        if source.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError('Proposed source exceeds source size bound')
        original = source.read_bytes()
        if _sha(original) != spec['source_sha256'][relative.as_posix()]:
            raise ValueError('Baseline source hash changed: ' + relative.as_posix())
        text, edited = original.decode('utf-8'), original.decode('utf-8')
        for _, hint in sorted(proposals, key=lambda item: item[0], reverse=True):
            edited = insert_source_hint(edited, hint['function_id'], hint, source_path=relative)
        if strip_source_hints(edited) != strip_source_hints(text):
            raise ValueError('Proposal changed text outside source hint comments')
        prepared[relative] = edited.encode('utf-8')
        sources.append({'path': relative.as_posix(), 'baseline_sha256': _sha(original),
                        'proposed_sha256': _sha(prepared[relative]), 'source_bytes': len(original)})
        for line in difflib.unified_diff(text.splitlines(keepends=True), edited.splitlines(keepends=True),
                fromfile='a/' + relative.as_posix(), tofile='b/' + relative.as_posix()):
            patches.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.' + output.name + '-', dir=output.parent))
    try:
        for relative, data in prepared.items():
            target = stage / 'source' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        index = index_source_hints(stage / 'source', [p.as_posix() for p in prepared], spec['api_function_ids'])
        indexed = {(r['function_id'], r['requirement_id']): r for r in index['records']}
        for hint in spec['hints']:
            actual = indexed.get((hint['function_id'], hint['requirement_id']))
            if actual is None or any(actual[key] != hint[key] for key in REQUIRED) or actual['status'] != 'unvalidated':
                raise ValueError('Emitted source hints did not round-trip through the source index')
        # Index paths must point to the eventual directory, never the staging name.
        for binding in index['artifacts']:
            binding['path'] = str(output / 'source' / Path(binding['path']).relative_to(stage / 'source'))
        patch = ''.join(patches).encode('utf-8')
        (stage / 'source.patch').write_bytes(patch)
        (stage / 'spec.json').write_bytes(spec_data)
        _write_json(stage / 'source_hint_index.json', index)
        manifest = {'schema_version': 1, 'status': 'unvalidated',
                    'source_root': str(root), 'output': str(output),
                    'spec_sha256': _sha(spec_data), 'patch_sha256': _sha(patch),
                    'sources': sources, 'coverage': index['coverage'],
                    'new_hint_count': len(spec['hints']),
                    'source_artifacts': [str(output / 'source' / p) for p in prepared],
                    'patch': str(output / 'source.patch'),
                    'validation': {'annotation_round_trip': 'passed',
                                   'non_annotation_text': 'unchanged', 'behavioral_tests': 'not_run'}}
        _write_json(stage / 'proposal.json', manifest)
        if output.exists() or output.is_symlink():
            raise ValueError('Proposal output appeared during preparation; refusing overwrite')
        os.rename(stage, output)
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    print(json.dumps(prepare_source_hints(args.source_root, args.spec, args.output), indent=2))


if __name__ == '__main__':
    main()
