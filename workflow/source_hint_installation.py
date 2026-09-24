"""Install validated source guidance into new, explicitly named study branches.

Historical branches are never advanced. Guidance lives beside declarations;
the small treatment receipt records provenance, not prompt-delivered JSON hints.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from .ablation import bind, load, verify_artifact
from .execution import atomic_json, ownership
from .source_hints import index_source_hints, strip_source_hints
from .treatment_versions import _run, _safe_path, _trees, _blob, _install, _check_worktree

LEGACY_HINTS = '.aideal/treatments/error_hints.json'
RECEIPT = '.aideal/treatments/source_hints_validation.json'


def _validated(path):
    from .source_hint_development import verify_development_validation
    value = verify_development_validation(path)
    if value.get('status') != 'validated' or not value.get('installable_sources'):
        raise ValueError('Only replay-verified development guidance can be installed')
    return value


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def install_source_hints(validation_path, targets_path, output):
    """Create new branches and commit identical, annotation-only hint sources."""
    validation_path, targets_path = Path(validation_path).resolve(), Path(targets_path).resolve()
    validation, plan = _validated(validation_path), load(targets_path)
    if set(plan) != {'schema_version', 'repository', 'targets'} or plan['schema_version'] != 1:
        raise ValueError('Expected installation plan schema_version 1')
    if set(plan['targets']) != {'error_hints_only', 'combined'}:
        raise ValueError('Install the same frozen hints in Error Hints only and Combined')
    repo = Path(plan['repository']).resolve(strict=True)
    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError('Output must not be a symlink')
    output = output.resolve()
    source_root = Path(validation['source_root']).resolve(strict=True)
    baseline = validation['baseline_revision']
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', baseline):
        raise ValueError('Source baseline must be an exact commit')
    baseline_tree = _trees(source_root, baseline)
    if _trees(repo, baseline) != baseline_tree:
        raise ValueError('Destination repository lacks the verified source baseline')
    # Refuse a source revision changed after development validation.
    if _run(source_root, 'rev-parse', 'HEAD') != baseline:
        raise ValueError('Development source revision changed')

    data, paths = {}, set()
    for item in validation['installable_sources']:
        relative, artifact = item['path'], item['artifact']
        if relative in paths or not verify_artifact(artifact):
            raise ValueError('Duplicate or modified validated source artifact')
        paths.add(relative)
        original = _safe_path(source_root, relative).read_bytes()
        edited = Path(artifact['path']).read_bytes()
        if _sha(original) != item['baseline_sha256']:
            raise ValueError('Baseline source hash changed: ' + relative)
        if strip_source_hints(edited.decode()) != original.decode():
            raise ValueError('Guidance changes executable source: ' + relative)
        data[relative] = edited
    receipt = {'schema_version': 1, 'status': 'validated_development',
               'delivery': 'function-local source comments',
               'baseline_revision': baseline, 'validation_sha256': bind(validation_path)['sha256'],
               'sources': {name: _sha(value) for name, value in sorted(data.items())},
               'scope': 'Development replay controls; not a held-out audience result.'}
    data[RECEIPT] = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
    identity = {'validation': bind(validation_path), 'targets': bind(targets_path)}
    final = output / 'application.json'
    if final.exists():
        previous = load(final)
        if previous.get('identity') != identity or previous.get('status') != 'installed_validated_development':
            raise ValueError('Installation output belongs to another or incomplete version')
        if set(previous.get('targets', {})) != set(plan['targets']):
            raise ValueError('Installed target set changed')
        for arm, record in previous['targets'].items():
            target = plan['targets'][arm]
            if (record.get('path') != str(Path(target['path']).resolve())
                    or record.get('branch') != target['branch']
                    or record.get('base_revision') != target['base_revision']
                    or record.get('source_files') != sorted(paths)
                    or record.get('status') != 'committed'):
                raise ValueError('Installed target differs from bound plan')
            root = Path(record['path'])
            if (_run(root, 'rev-parse', 'HEAD') != record['commit']
                    or _run(root, 'symbolic-ref', '--short', 'HEAD') != target['branch']
                    or _run(root, 'show', '-s', '--format=%P', record['commit']) != target['base_revision']):
                raise ValueError('Installed branch changed')
            _check_worktree(root, record['commit'], {})
            expected_tree = _trees(root, target['base_revision'])
            removed_legacy = LEGACY_HINTS in expected_tree
            expected_tree.pop(LEGACY_HINTS, None)
            algorithm = _run(root, 'rev-parse', '--show-object-format')
            for name, value in data.items():
                mode = expected_tree.get(name, ('100644',))[0]
                expected_tree[name] = (mode, _blob(value, algorithm))
            if (_trees(root, record['commit']) != expected_tree
                    or record.get('removed_legacy_hint_file') != removed_legacy):
                raise ValueError('Installed commit tree or legacy-removal receipt changed')
            if any(_safe_path(root, name).read_bytes() != value for name, value in data.items()):
                raise ValueError('Installed guidance changed')
            if (root / LEGACY_HINTS).exists():
                raise ValueError('Legacy hint delivery reappeared')
            index = index_source_hints(root, sorted(paths), validation['api_function_ids'])
            if record.get('hint_count') != len(index['records']) or record.get('coverage') != index['coverage']:
                raise ValueError('Installed coverage receipt changed')
        return previous
    if output.exists() and any(output.iterdir()):
        raise ValueError('Unfinished installation exists; inspect its journal before retrying')

    targets, branches, destinations = {}, set(), set()
    refs = set(_run(repo, 'for-each-ref', '--format=%(refname)', 'refs/heads').splitlines())
    for arm, item in plan['targets'].items():
        if set(item) != {'branch', 'base_revision', 'path'}:
            raise ValueError('Each target needs branch, base_revision and path')
        branch, parent = item['branch'], item['base_revision']
        _run(repo, 'check-ref-format', '--branch', branch)
        if branch in branches or 'refs/heads/' + branch in refs:
            raise ValueError('Target branch already exists or is repeated')
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', parent):
            raise ValueError('Target parent must be an exact commit')
        destination = Path(item['path']).absolute()
        if destination.exists() or destination.is_symlink():
            raise ValueError('New worktree destination must not exist')
        destination = destination.resolve()
        if (destination in destinations or destination.is_relative_to(source_root)
                or destination.is_relative_to(output) or output.is_relative_to(destination)
                or any(destination.is_relative_to(p) or p.is_relative_to(destination) for p in destinations)):
            raise ValueError('Worktree destinations overlap source or output')
        _run(repo, 'merge-base', '--is-ancestor', baseline, parent)
        tree = _trees(repo, parent)
        if any(tree.get(name) != entry for name, entry in baseline_tree.items()
               if not name.startswith('.aideal/')):
            raise ValueError('Target parent changed baseline library files')
        if RECEIPT in tree:
            raise ValueError('Target already contains a source-guidance receipt')
        targets[arm] = {**item, 'path': str(destination)}
        branches.add(branch)
        destinations.add(destination)

    with ownership(output):
        journal = {'identity': identity, 'status': 'installing', 'targets': {}}
        atomic_json(output / 'journal.json', journal)
        for arm, item in targets.items():
            root, parent = Path(item['path']), item['base_revision']
            journal['targets'][arm] = {**item, 'status': 'creating_worktree'}
            atomic_json(output / 'journal.json', journal)
            _run(repo, 'worktree', 'add', '-b', item['branch'], str(root), parent)
            _check_worktree(root, parent, {})
            algorithm = _run(root, 'rev-parse', '--show-object-format')
            tree = _trees(root, parent)
            files = {name: {'role': name, 'mode': tree.get(name, ('100644',))[0],
                            'git_blob': _blob(value, algorithm)} for name, value in data.items()}
            removed = [LEGACY_HINTS] if LEGACY_HINTS in tree else []
            _install(root, files, removed, data, output / ('blobs-' + arm))
            index = index_source_hints(root, sorted(paths), validation['api_function_ids'])
            if not index['records'] or any(row['status'] != 'validated_development' for row in index['records']):
                raise ValueError('Installed annotations failed to round-trip as validated development guidance')
            _run(root, 'commit', '-m', 'Embed validated development error guidance beside API functions')
            head = _run(root, 'rev-parse', 'HEAD')
            _check_worktree(root, head, {})
            changed = set(_run(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', head).splitlines())
            if changed != set(files) | set(removed):
                raise ValueError('Unexpected paths in source-guidance commit')
            record = {**item, 'commit': head, 'hint_count': len(index['records']),
                      'source_files': sorted(paths), 'coverage': index['coverage'],
                      'removed_legacy_hint_file': bool(removed), 'status': 'committed'}
            journal['targets'][arm] = record
            atomic_json(output / 'journal.json', journal)
        result = {**journal, 'status': 'installed_validated_development'}
        atomic_json(final, result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation', required=True)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    print(json.dumps(install_source_hints(args.validation, args.targets, args.output), indent=2))


if __name__ == '__main__':
    main()
