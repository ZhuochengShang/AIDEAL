"""Version explicit source-refactor candidates apart from the five treatments."""
import hashlib
from pathlib import Path
import re

from .ablation import bind, digest, load
from .evaluation_setup import assert_review_released
from .execution import ownership
from .improvement_context import original_checkout
from .treatment_versions import (_blob, _check_worktree, _committed, _install,
                                 _record, _relative, _run, _safe_path, _trees)


def _version(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise ValueError('Invalid refactor version identity')
    return value


def _lineage(records, version, expected_sha256=None):
    """Follow explicit predecessor hashes; never infer latest from file times."""
    result = {}
    while version is not None:
        _version(version)
        if version in result:
            raise ValueError('Refactor version lineage contains a cycle')
        path = _safe_path(records, version + '.json')
        if expected_sha256 is not None and bind(path)['sha256'] != expected_sha256:
            raise ValueError('Previous refactor record changed')
        record = load(path)
        if (not isinstance(record, dict) or record.get('proposal_sha256') != version
                or record.get('status') != 'installed_unvalidated' or record.get('evaluated') is not False):
            raise ValueError('Refactor record version changed')
        previous = record.get('previous_version')
        previous_hash = record.get('previous_record_sha256')
        if 'previous_version' not in record or (previous is None) != (previous_hash is None):
            raise ValueError('Refactor record lacks a valid predecessor identity')
        if previous is not None:
            _version(previous)
            _version(previous_hash)
        result[version] = record
        version, expected_sha256 = previous, previous_hash
    return result


def _current(records):
    path = _safe_path(records, 'current.json')
    if not path.exists():
        return None, {}
    pointer = load(path)
    if not isinstance(pointer, dict):
        raise ValueError('Invalid current refactor pointer')
    version = _version(pointer.get('version'))
    expected_path = _safe_path(records, version + '.json')
    if pointer.get('record') != bind(expected_path):
        raise ValueError('Current refactor record changed or escaped its directory')
    return version, _lineage(records, version, pointer['record']['sha256'])


def _other_pending(records, permitted):
    """Prevent a second lineage while an earlier install needs recovery."""
    for path in records.glob('*.pending.json'):
        _safe_path(records, path.name)
        if _version(path.name.removesuffix('.pending.json')) not in permitted:
            raise ValueError('Another refactor version needs recovery first')


def _check_repository(root, clone, branch):
    common = Path(_run(root, 'rev-parse', '--git-common-dir'))
    if not common.is_absolute():
        common = root / common
    if (common.resolve() != clone or _run(root, 'branch', '--show-current') != branch
            or Path(_run(root, 'rev-parse', '--show-toplevel')) != root):
        raise ValueError('Refactor worktree belongs to a different repository or branch')


def _candidate(proposal_path, baseline, original):
    path = Path(proposal_path).expanduser().absolute()
    if path.is_symlink():
        raise ValueError('Refactor proposal must not be a symlink')
    path = path.resolve(strict=True)
    proposal = load(path)
    if (not isinstance(proposal, dict) or type(proposal.get('schema_version')) is not int
            or proposal['schema_version'] != 1 or proposal.get('kind') != 'source_refactor'
            or proposal.get('baseline_revision') != baseline):
        raise ValueError('Refactor proposal must match the exact attached baseline')
    if proposal.get('preserve_public_api') is not True:
        raise ValueError('Refactor comparison requires preserving the original public API')
    checks = proposal.get('validation_plan')
    if not isinstance(checks, list) or not checks or any(not isinstance(x, str) or not x.strip() for x in checks):
        raise ValueError('List concrete compatibility/regression checks in validation_plan')
    changes = proposal.get('changes')
    if not isinstance(changes, list) or not changes:
        raise ValueError('Refactor proposal needs explicit source changes')
    files, removed, data, targets = {}, [], {}, set()
    tracked = _trees(original, baseline)
    algorithm = _run(original, 'rev-parse', '--show-object-format')
    for index, row in enumerate(changes):
        if not isinstance(row, dict) or 'after' not in row:
            raise ValueError('Each source change needs an explicit after binding or null deletion')
        target = _relative(row.get('path'))
        if target.casefold() in targets or any(part.startswith('.') for part in Path(target).parts):
            raise ValueError('Duplicate, hidden or reserved refactor path')
        targets.add(target.casefold())
        if Path(target).suffix not in ('.py', '.java', '.scala', '.rs'):
            raise ValueError('Refactor paths must be supported source files; docs/config/tests stay separate')
        current = _safe_path(original, target)
        if current.exists() and target not in tracked:
            raise ValueError('Refactor baseline path is not tracked')
        before = hashlib.sha256(current.read_bytes()).hexdigest() if current.is_file() else None
        if 'before_sha256' not in row or row['before_sha256'] != before:
            raise ValueError('Refactor before_sha256 does not match baseline: ' + target)
        after = row.get('after')
        if after is None:
            if before is None:
                raise ValueError('Cannot delete an absent source file')
            removed.append(target)
            continue
        if not isinstance(after, dict) or not isinstance(after.get('path'), str):
            raise ValueError('Refactor replacement needs an absolute artifact binding')
        source = Path(after['path'])
        if not source.is_absolute() or '..' in source.parts:
            raise ValueError('Refactor replacement must be inside the proposal directory')
        try:
            relative = source.relative_to(path.parent).as_posix()
        except ValueError as exc:
            raise ValueError('Replacement must be inside the proposal directory') from exc
        source = _safe_path(path.parent, relative)
        content = source.read_bytes()
        if (not content or type(after.get('bytes')) is not int or after['bytes'] != len(content)
                or after.get('sha256') != hashlib.sha256(content).hexdigest()):
            raise ValueError('Refactor replacement hash/size changed; use after:null for deletion')
        key = f'source_{index:04d}'
        data[key] = content
        files[target] = {'role': key, 'sha256': hashlib.sha256(content).hexdigest(),
                         'bytes': len(content), 'git_blob': _blob(content, algorithm),
                         'mode': tracked[target][0] if target in tracked else '100644'}
    if any(a.startswith(b + '/') or b.startswith(a + '/') for a in targets for b in targets if a != b):
        raise ValueError('Conflicting source paths')
    return proposal, files, removed, data


def install_refactor(study, proposal_path):
    """Create one local version branch from baseline; never edit existing arms.

    Exact replacement files/deletions are journaled. This does not execute or
    approve generated code; independent regression and study controls follow.
    """
    study, original, attachment = original_checkout(study)
    assert_review_released(study)
    proposal, files, removed, data = _candidate(proposal_path, attachment['revision'], original)
    version = digest(proposal)
    records = _safe_path(study, 'refactors')
    with ownership(records):
        current_version, current_lineage = _current(records)
        folder = _safe_path(study, 'Refactor only/' + version)
        root = _safe_path(folder, 'source')
        clone = _safe_path(study, 'repository.git')
        branch = 'aideal/refactor-' + version[:16]
        record_path = _safe_path(records, version + '.json')
        journal_path = _safe_path(records, version + '.pending.json')
        parent = attachment['revision']
        message = 'AIDEAL source refactor ' + version
        identity = {'proposal_sha256': version, 'source': str(root), 'branch': branch,
                    'baseline_revision': parent, 'files': files, 'removed_paths': removed}
        if record_path.exists():
            record = load(record_path)
            if not isinstance(record, dict) or any(record.get(k) != v for k, v in identity.items()):
                raise ValueError('Refactor record identity changed')
            lineage = _lineage(records, version)
            _check_repository(root, clone, branch)
            if (_run(root, 'rev-parse', 'HEAD') != record['commit_revision']
                    or not _committed(root, parent, record['commit_revision'], files, removed, message)):
                raise ValueError('Refactor HEAD changed')
            _check_worktree(root, record['commit_revision'], {})
            if version not in current_lineage:
                if current_version is not None and current_version != record['previous_version']:
                    raise ValueError('Refactor is not the next version in the current lineage')
                completed = {p.stem for p in records.glob('*.json') if re.fullmatch(r'[0-9a-f]{64}', p.stem)}
                if not completed <= set(lineage):
                    raise ValueError('Newer completed refactor exists; recover that version first')
                _other_pending(records, set(lineage))
                _record(records / 'current.json', {'version': version, 'record': bind(record_path)})
            return record
        _other_pending(records, set(current_lineage) | {version})
        if current_version is None and any(re.fullmatch(r'[0-9a-f]{64}', p.stem) for p in records.glob('*.json')):
            raise ValueError('Recover the missing current refactor pointer before a new version')
        expected = {**identity, 'previous_version': current_version,
                    'previous_record_sha256': bind(records / (current_version + '.json'))['sha256']
                    if current_version else None}
        if journal_path.exists():
            if load(journal_path) != expected:
                raise ValueError('Refactor journal changed')
        else:
            if root.exists():
                raise ValueError('Refactor destination exists without its journal')
            _record(journal_path, expected)
        if not root.exists():
            folder.mkdir(parents=True, exist_ok=True)
            existing = _run(clone, 'for-each-ref', '--format=%(objectname)', 'refs/heads/' + branch)
            if existing:
                if existing != parent:
                    raise ValueError('Existing refactor branch is not at the baseline')
                _run(clone, 'worktree', 'add', str(root), branch)
            else:
                _run(clone, 'worktree', 'add', '-b', branch, str(root), parent)
        _check_repository(root, clone, branch)
        head = _run(root, 'rev-parse', 'HEAD')
        if head != parent and not _committed(root, parent, head, files, removed, message):
            raise ValueError('Unexpected refactor HEAD; preserve changes for review')
        if head == parent:
            allowed = {**files, **{p: None for p in removed}}
            _check_worktree(root, parent, allowed, installing=True)
            _install(root, files, removed, data, folder / 'staging')
            expected_tree = _trees(root, parent)
            expected_tree.update({p: (b['mode'], b['git_blob']) for p, b in files.items()})
            for name in removed:
                expected_tree.pop(name)
            if _trees(root) != expected_tree:
                raise ValueError('Unexpected staged files during refactor')
            if expected_tree == _trees(root, parent):
                raise ValueError('Refactor makes no source change')
            tree = _run(root, 'write-tree')
            head = _run(root, 'commit-tree', tree, '-p', parent, '-m', message)
            _run(root, 'update-ref', 'refs/heads/' + branch, head, parent)
        _check_worktree(root, head, {})
        original_checkout(study)
        assert_review_released(study)
        if _candidate(proposal_path, parent, original) != (proposal, files, removed, data):
            raise ValueError('Refactor proposal changed during installation')
        record = {**expected, 'commit_revision': head, 'proposal': bind(proposal_path),
                  'status': 'installed_unvalidated', 'evaluated': False,
                  'validation_plan': proposal['validation_plan'],
                  'scope': 'Original README and original public API contract; modified backend only'}
        _record(record_path, record)
        _record(records / 'current.json', {'version': version, 'record': bind(record_path)})
        return record


def study_versions(study):
    """Read current source/artifact pointers; do not switch any Git branch."""
    study = Path(study).expanduser().resolve(strict=True)
    attachment = load(study / 'attachment.json')
    rows = []
    for arm, item in attachment['worktrees'].items():
        root = Path(item['path'])
        rows.append({'condition': arm, 'source': str(root), 'branch': item['branch'],
                     'baseline_revision': item['base_revision'],
                     'current_revision': _run(root, 'rev-parse', 'HEAD'),
                     'original_readme': str(study / 'original_documentation.txt'),
                     'treatment_directory': str(root / '.aideal/treatments')})
    refactor = study / 'refactors/current.json'
    if refactor.exists():
        version, lineage = _current(_safe_path(study, 'refactors'))
        record = lineage[version]
        rows.append({'condition': 'refactor_only', **record,
                     'current_revision': _run(Path(record['source']), 'rev-parse', 'HEAD'),
                     'original_readme': str(study / 'original_documentation.txt')})
    current = study / 'treatments/current.json'
    return {'study': str(study), 'baseline_revision': attachment['revision'],
            'treatment_version': load(current) if current.exists() else None,
            'conditions': rows, 'note': 'Installation is not validation; freeze binds the exact chosen versions.'}
