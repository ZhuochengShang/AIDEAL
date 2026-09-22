"""Install complete treatment bundles in attached worktrees, without executing them.

Only explicit treatment paths enter local commits. Each proposal is a complete
version: omitted artifacts remove only files owned by the previous AIDEAL
version. Application records are final, immutable evidence; an unfinished
journal can be resumed without resetting a worktree or discarding user edits.
"""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re

from .ablation import digest, load
from .evaluation_setup import assert_review_released
from .execution import atomic_json, ownership
from .preparation import CONDITION_FOLDERS
from .worktrees import _git


FIXED_TARGETS = {
    'readme': '.aideal/treatments/README.md',
    'alias_interface': '.aideal/treatments/ALIASES.md',
    'error_hints': '.aideal/treatments/error_hints.json',
}
ROUTES = {'readme': ('readme_only', 'combined'),
          'alias': ('alias_only', 'combined'),
          'alias_interface': ('alias_only', 'combined'),
          'error_hints': ('error_hints_only', 'combined')}


def _run(root, *args):
    # Generated .gitattributes cannot activate clean filters: staging below uses
    # raw blobs and update-index. Hooks, signing, and automatic maintenance are
    # disabled per command; no repository/global configuration is changed.
    if any(os.environ.get(key) for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE',
           'GIT_OBJECT_DIRECTORY', 'GIT_COMMON_DIR', 'GIT_NAMESPACE',
           'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT', 'GIT_AUTHOR_NAME',
           'GIT_AUTHOR_EMAIL', 'GIT_COMMITTER_NAME', 'GIT_COMMITTER_EMAIL')):
        raise ValueError('Unset Git repository/index/config/identity environment overrides before installing')
    return _git(root, '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                '-c', 'core.fsmonitor=false', '-c', 'gc.auto=0',
                '-c', 'maintenance.auto=false', '-c', 'user.name=AIDEAL',
                '-c', 'user.email=aideal@localhost', '--literal-pathspecs', *args)


def _relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or '\0' in value
            or PurePosixPath(value).is_absolute()
            or any(p in ('', '.', '..') or p.casefold() == '.git' for p in value.split('/'))):
        raise ValueError('Treatment target must be a safe repository-relative filename')
    return value


def _safe_path(root, relative):
    path = root
    for part in _relative(relative).split('/'):
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Symlink is not allowed in a treatment path: {path}')
    return path


def _record(path, value):
    if path.parent.resolve() != path.parent or path.is_symlink() or path.with_suffix(path.suffix + '.tmp').is_symlink():
        raise ValueError('Symlink in application record path')
    atomic_json(path, value)


def _artifact_role(key):
    return 'alias' if re.fullmatch(r'alias_[0-9]{4,6}', key) else key


def _read_proposal(path, baseline):
    path = Path(path).expanduser().absolute()
    if path.is_symlink():
        raise ValueError('Proposal must not be a symlink')
    path = path.resolve(strict=True)
    proposal = load(path)
    if (not isinstance(proposal, dict) or type(proposal.get('schema_version')) is not int
            or proposal['schema_version'] not in (1, 2) or proposal.get('baseline_revision') != baseline):
        raise ValueError('Proposal schema or baseline revision does not match the attachment')
    artifacts = proposal.get('artifacts')
    if (not isinstance(artifacts, dict) or not artifacts
            or any(_artifact_role(k) not in ROUTES for k in artifacts)
            or (proposal['schema_version'] == 1 and set(artifacts) - set(ROUTES))):
        raise ValueError('Supply at least one known treatment artifact')
    if any(_artifact_role(k) == 'alias' for k in artifacts) != ('alias_interface' in artifacts):
        raise ValueError('Alias source and alias interface must be supplied together')
    data = {}
    targets = set()
    for key, binding in artifacts.items():
        role = _artifact_role(key)
        if not isinstance(binding, dict) or not isinstance(binding.get('path'), str):
            raise ValueError(f'Invalid artifact binding: {role}')
        source = Path(binding['path'])
        if not source.is_absolute() or '..' in source.parts:
            raise ValueError('Artifact paths must be absolute and inside the proposal directory')
        try:
            relative = source.relative_to(path.parent).as_posix()
        except ValueError as exc:
            raise ValueError('Artifact escapes the proposal directory') from exc
        source = _safe_path(path.parent, relative)
        if not source.is_file():
            raise ValueError(f'Artifact is not a regular file: {source}')
        content = source.read_bytes()
        if (not content or type(binding.get('bytes')) is not int or binding['bytes'] != len(content)
                or binding.get('sha256') != hashlib.sha256(content).hexdigest()):
            raise ValueError(f'Artifact hash/size mismatch or empty artifact: {role}')
        if role == 'alias':
            target = _relative(binding.get('target'))
            if target.split('/')[0].casefold() == '.aideal':
                raise ValueError('Alias source must be outside the reserved .aideal directory')
        elif 'target' in binding and binding['target'] != FIXED_TARGETS[role]:
            raise ValueError(f'{role} has a fixed treatment target')
        target = binding.get('target', FIXED_TARGETS.get(role))
        if any(target.casefold() == old or target.casefold().startswith(old + '/')
               or old.startswith(target.casefold() + '/') for old in targets):
            raise ValueError('Duplicate or conflicting treatment destination')
        targets.add(target.casefold())
        data[key] = content
    return proposal, data


def _blob(data, algorithm):
    return hashlib.new(algorithm, b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def _trees(root, revision=None):
    records = (_run(root, 'ls-tree', '-rz', revision) if revision else
               _run(root, 'ls-files', '--stage', '-z'))
    result = {}
    for record in records.split('\0'):
        if not record:
            continue
        metadata, path = record.split('\t', 1)
        mode, middle, last = metadata.split(' ')
        if not revision and last != '0':
            raise ValueError('Worktree has an unresolved index conflict')
        if mode not in ('100644', '100755', '120000'):
            raise ValueError('Treatment installation does not support submodule/gitlink entries')
        result[path] = (mode, last if revision else middle)
    return result


def _disk_entry(root, name, algorithm):
    path = root / name
    if path.is_symlink():
        resolved = path.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f'Escaping symlink in worktree: {path}')
        return ('120000', _blob(os.fsencode(os.readlink(path)), algorithm))
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError(f'Expected a regular tracked file: {path}')
    return ('100755' if path.stat().st_mode & 0o111 else '100644', _blob(path.read_bytes(), algorithm))


def _bundle(proposal, data, algorithm):
    bundle = {arm: {} for arm in CONDITION_FOLDERS}
    for key, binding in proposal['artifacts'].items():
        role = _artifact_role(key)
        target = binding['target'] if role == 'alias' else FIXED_TARGETS[role]
        for arm in ROUTES[role]:
            bundle[arm][target] = {'role': role, 'sha256': binding['sha256'],
                                  'bytes': binding['bytes'], 'git_blob': _blob(data[key], algorithm)}
            if key != role:
                bundle[arm][target]['data_key'] = key
    return bundle


def _binding_entry(binding):
    return (binding.get('mode', '100644'), binding['git_blob'])


def _check_target_paths(root, baseline, files):
    for target, binding in files.items():
        path = _safe_path(root, target)
        if path.exists() and not path.is_file():
            raise ValueError(f'Treatment target conflicts with a directory: {target}')
        if binding['role'] == 'alias':
            target = target.casefold()
            if any(p.casefold() == target or p.casefold().startswith(target + '/')
                   or target.startswith(p.casefold() + '/')
                   for p in baseline):
                raise ValueError('Alias target must be a NEW path, absent from the baseline')


def _check_worktree(root, head, desired, *, installing=False):
    """Compare raw file/index blobs, without invoking attributes or Git filters."""
    algorithm = _run(root, 'rev-parse', '--show-object-format')
    tree, index = _trees(root, head), _trees(root)
    changes = {name: _binding_entry(binding) if binding is not None else None
               for name, binding in desired.items()}
    for name in set(tree) | set(index) | set(changes):
        before = tree.get(name)
        allowed = {before}
        if installing and name in changes:
            allowed.add(changes[name])
        # Removed AIDEAL files are represented by an explicit None entry.
        if installing and name in desired and desired[name] is None:
            allowed.add(None)
        if index.get(name) not in allowed:
            raise ValueError(f'Unrelated or changed staged edit: {name}')
        if _disk_entry(root, name, algorithm) not in allowed:
            raise ValueError(f'Unrelated or changed tracked/source edit: {name}')
    for name in _run(root, 'ls-files', '--others', '-z').split('\0'):
        if not name:
            continue
        if installing and name in changes:
            if _disk_entry(root, name, algorithm) == changes[name]:
                continue
        # Attachment instrumentation is deliberately untracked. New treatment
        # files are allowed only after this version has journaled ownership.
        if name.startswith('.aideal/') and not name.startswith('.aideal/treatments/'):
            _safe_path(root, name)
            continue
        raise ValueError(f'Unrelated untracked source/treatment file: {name}')
    scaffold = root / '.aideal'
    if scaffold.is_symlink():
        raise ValueError('Symlinked .aideal workspace is not allowed')
    if scaffold.is_dir():
        for path in scaffold.rglob('*'):
            if path.is_symlink():
                raise ValueError(f'Symlinked scaffold is not allowed: {path}')


def _attachment(study):
    attachment = load(_safe_path(study, 'attachment.json'))
    if (attachment.get('status') != 'attached_scaffolded_pending_validation'
            or set(attachment.get('worktrees', {})) != set(CONDITION_FOLDERS)):
        raise ValueError('Treatments require a complete five-worktree attachment')
    baseline = attachment.get('revision')
    clone = _safe_path(study, 'repository.git')
    if _run(clone, 'rev-parse', '--verify', str(baseline) + '^{commit}') != baseline:
        raise ValueError('Attachment baseline is not an exact Git commit')
    for arm, folder in CONDITION_FOLDERS.items():
        info = attachment['worktrees'][arm]
        expected = _safe_path(study, folder + '/source')
        assert_review_released(expected)
        branch = 'aideal/' + arm.replace('_', '-')
        if (info.get('path') != str(expected) or info.get('branch') != branch
                or info.get('base_revision') != baseline):
            raise ValueError(f'Unexpected attached worktree identity: {arm}')
        common = Path(_run(expected, 'rev-parse', '--git-common-dir'))
        if not common.is_absolute():
            common = expected / common
        if common.resolve() != clone or Path(_run(expected, 'rev-parse', '--show-toplevel')) != expected:
            raise ValueError(f'Worktree is not part of this isolated attachment: {arm}')
        if _run(expected, 'symbolic-ref', '--quiet', '--short', 'HEAD') != branch:
            raise ValueError(f'Unexpected worktree branch: {arm}')
    return attachment


def _current(versions):
    path = _safe_path(versions, 'current.json')
    if not path.exists():
        return None, None
    pointer = load(path)
    version = pointer.get('proposal_sha256', '')
    if not re.fullmatch(r'[0-9a-f]{64}', version):
        raise ValueError('Invalid current treatment version')
    application = load(_safe_path(versions, version + '/application.json'))
    if (digest(application) != pointer.get('application_sha256')
            or application.get('proposal_sha256') != version
            or application.get('status') != 'applied_unvalidated'):
        raise ValueError('Current treatment application record changed')
    return version, application


def _expected_changes(root, parent, files, removed):
    tree = _trees(root, parent)
    after = {name: _binding_entry(binding) for name, binding in files.items()}
    after.update({name: None for name in removed})
    return {name: value for name, value in after.items() if tree.get(name) != value}


def _committed(root, parent, head, files, removed, message):
    if _run(root, 'show', '-s', '--format=%P', head) != parent:
        return False
    if _run(root, 'show', '-s', '--format=%B', head) != message:
        return False
    before, after = _trees(root, parent), _trees(root, head)
    changes = {p: after.get(p) for p in set(before) | set(after) if before.get(p) != after.get(p)}
    return changes == _expected_changes(root, parent, files, removed)


def _install(root, files, removed, data, temporary):
    temporary.mkdir(parents=True, exist_ok=True)
    for index, (target, binding) in enumerate(files.items()):
        destination = _safe_path(root, target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        scratch = _safe_path(temporary, f'{index}.blob')
        scratch.write_bytes(data[binding.get('data_key', binding['role'])])
        mode = binding.get('mode', '100644')
        scratch.chmod(0o755 if mode == '100755' else 0o644)
        os.replace(scratch, destination)
        blob = _run(root, 'hash-object', '-w', '--no-filters', '--', target)
        if blob != binding['git_blob']:
            raise ValueError('Treatment bytes changed before staging')
        _run(root, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},{target}')
    for target in removed:
        destination = _safe_path(root, target)
        if destination.exists():
            destination.unlink()
        _run(root, 'update-index', '--force-remove', '--', target)


def apply_treatments(study, proposal_path):
    """Install a complete proposal, preserving all earlier versions and evidence.

    An omitted artifact removes only its previous AIDEAL-owned treatment files.
    This creates local commits and reports applied_unvalidated, never approval
    or measured results. Reapplying the current version is a checked no-op.
    """
    study = Path(study).expanduser().resolve(strict=True)
    assert_review_released(study)
    attachment = _attachment(study)
    proposal, data = _read_proposal(proposal_path, attachment['revision'])
    version = digest(proposal)
    versions = _safe_path(study, 'treatments')
    _safe_path(versions, '.lock')
    with ownership(versions):
        current_version, previous = _current(versions)
        directory = _safe_path(versions, version)
        journal_path = _safe_path(directory, 'journal.json')
        application_path = _safe_path(directory, 'application.json')
        for pending in versions.glob('*/journal.json'):
            _safe_path(versions, pending.relative_to(versions).as_posix())
            if pending.parent != directory and not (pending.parent / 'application.json').exists():
                raise ValueError('Another treatment version is incomplete; resume its proposal first')
        journal = load(journal_path) if journal_path.exists() else None
        if application_path.exists() and current_version not in (version, (journal or {}).get('previous_version')):
            raise ValueError('This historical version is not current; use a new proposal to change treatments')
        if journal and current_version not in (version, journal.get('previous_version')):
            raise ValueError('Treatment journal does not follow the current version')
        if current_version == version:
            previous = None  # The journal preserves the pre-installation parents.
        clone = Path(study / 'repository.git')
        algorithm = _run(clone, 'rev-parse', '--show-object-format')
        bundle = _bundle(proposal, data, algorithm)
        baseline_tree = _trees(clone, attachment['revision'])
        if journal is None:
            arms = {}
            for arm, info in attachment['worktrees'].items():
                prior = previous['arms'][arm] if previous else None
                files = bundle[arm]
                root = Path(info['path'])
                _check_target_paths(root, baseline_tree, files)
                if prior:
                    _check_target_paths(root, baseline_tree, prior['files'])
                parent = prior['commit_revision'] if prior else attachment['revision']
                if _run(root, 'rev-parse', 'HEAD') != parent:
                    raise ValueError(f'Unexpected worktree HEAD: {arm}')
                _check_worktree(root, parent, {})
                arms[arm] = {'branch': info['branch'], 'path': info['path'], 'parent_revision': parent,
                             'files': files, 'removed_paths': sorted(set(prior['files'] if prior else {}) - set(files)),
                             'state': 'pending'}
            journal = {'schema_version': 1, 'proposal_sha256': version, 'proposal': proposal,
                       'baseline_revision': attachment['revision'], 'previous_version': current_version,
                       'previous_application_sha256': digest(previous) if previous else None,
                       'bundle_semantics': 'complete_replace_owned', 'status': 'applying', 'arms': arms}
            _record(journal_path, journal)
        if (journal.get('proposal_sha256') != version or journal.get('proposal') != proposal
                or journal.get('baseline_revision') != attachment['revision']
                or set(journal.get('arms', {})) != set(CONDITION_FOLDERS)):
            raise ValueError('Treatment journal identity changed')
        previous_version = journal.get('previous_version')
        prior_application = None
        if previous_version is not None:
            if not isinstance(previous_version, str) or not re.fullmatch(r'[0-9a-f]{64}', previous_version):
                raise ValueError('Invalid previous treatment version')
            prior_application = load(_safe_path(versions, previous_version + '/application.json'))
            if digest(prior_application) != journal.get('previous_application_sha256'):
                raise ValueError('Previous immutable application changed')
        # Check every arm before changing another arm, including Original.
        for arm, entry in journal['arms'].items():
            root = Path(attachment['worktrees'][arm]['path'])
            prior = prior_application['arms'][arm] if prior_application else None
            parent = prior['commit_revision'] if prior else attachment['revision']
            removed = sorted(set(prior['files'] if prior else {}) - set(bundle[arm]))
            if (entry['files'] != bundle[arm] or entry['path'] != str(root)
                    or entry['branch'] != attachment['worktrees'][arm]['branch']
                    or entry['parent_revision'] != parent or entry['removed_paths'] != removed
                    or entry.get('state') not in ('pending', 'installing', 'complete')):
                raise ValueError('Treatment journal artifact/worktree mapping changed')
            _check_target_paths(root, baseline_tree, entry['files'])
            _check_target_paths(root, baseline_tree,
                                {p: {'role': 'alias' if not p.startswith('.aideal/') else 'owned'}
                                 for p in entry['removed_paths']})
            message = f'AIDEAL treatment {version} ({arm})'
            head = _run(root, 'rev-parse', 'HEAD')
            expected = entry.get('commit_revision', entry['parent_revision'])
            if head != expected:
                if entry['state'] == 'installing' and _committed(
                        root, entry['parent_revision'], head, entry['files'], entry['removed_paths'], message):
                    entry.update(state='complete', commit_revision=head)
                    _record(journal_path, journal)
                else:
                    raise ValueError(f'Unexpected worktree HEAD: {arm}')
            if entry['state'] == 'complete':
                changes = _expected_changes(root, parent, entry['files'], removed)
                if ((not changes and head != parent) or (changes and not _committed(
                        root, parent, head, entry['files'], removed, message))):
                    raise ValueError(f'Completed treatment commit does not match its journal: {arm}')
            allowed = dict(entry['files'])
            allowed.update({p: None for p in entry['removed_paths']})
            _check_worktree(root, head, allowed if entry['state'] == 'installing' else {},
                            installing=entry['state'] == 'installing')
            if arm == 'original' and (head != attachment['revision'] or entry['files'] or entry['removed_paths']):
                raise ValueError('Original condition must remain at the unchanged baseline')
        for arm, entry in journal['arms'].items():
            if entry['state'] == 'complete':
                continue
            root = Path(entry['path'])
            parent = entry['parent_revision']
            if _run(root, 'rev-parse', 'HEAD') != parent:
                raise ValueError(f'Worktree HEAD changed during installation: {arm}')
            allowed = dict(entry['files'])
            allowed.update({p: None for p in entry['removed_paths']})
            _check_worktree(root, parent, allowed if entry['state'] == 'installing' else {},
                            installing=entry['state'] == 'installing')
            entry['state'] = 'installing'
            _record(journal_path, journal)
            _install(root, entry['files'], entry['removed_paths'], data,
                     _safe_path(directory, 'staging/' + arm))
            expected_tree = _trees(root, parent)
            expected_tree.update({p: _binding_entry(b) for p, b in entry['files'].items()})
            for name in entry['removed_paths']:
                expected_tree.pop(name, None)
            if _trees(root) != expected_tree:
                raise ValueError('Index changed during installation; preserve it for review')
            if _expected_changes(root, parent, entry['files'], entry['removed_paths']):
                # commit-tree avoids git commit's worktree refresh (and hence
                # clean filters). update-ref also checks the expected parent.
                tree = _run(root, 'write-tree')
                commit = _run(root, 'commit-tree', tree, '-p', parent, '-m',
                              f'AIDEAL treatment {version} ({arm})')
                _run(root, 'update-ref', 'refs/heads/' + entry['branch'], commit, parent)
            head = _run(root, 'rev-parse', 'HEAD')
            entry.update(state='complete', commit_revision=head)
            _record(journal_path, journal)
        for arm, entry in journal['arms'].items():
            root = Path(entry['path'])
            if _run(root, 'rev-parse', 'HEAD') != entry['commit_revision']:
                raise ValueError(f'Worktree HEAD changed during installation: {arm}')
            _check_worktree(root, entry['commit_revision'], {})
        assert_review_released(study)
        _attachment(study)
        checked_proposal, checked_data = _read_proposal(proposal_path, attachment['revision'])
        if checked_proposal != proposal or checked_data != data:
            raise ValueError('Proposal artifacts changed during installation; preserve the journal')
        application = {k: v for k, v in journal.items() if k != 'status'}
        application.update(status='applied_unvalidated', evaluated=False)
        if application_path.exists():
            if load(application_path) != application:
                raise ValueError('Immutable application record differs')
        else:
            _record(application_path, application)
        pointer = {'schema_version': 1, 'proposal_sha256': version, 'application_sha256': digest(application)}
        current_path = _safe_path(versions, 'current.json')
        if not current_path.exists() or load(current_path) != pointer:
            _record(current_path, pointer)
        if journal['status'] != 'applied_unvalidated':
            journal['status'] = 'applied_unvalidated'
            _record(journal_path, journal)
        return {**application, 'application_path': str(application_path), 'current_path': str(current_path)}
