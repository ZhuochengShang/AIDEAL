"""Explicit condition protocol: matched documents, Git backends and hint inputs."""
from pathlib import Path

from .ablation import bind, digest, load
from .source_hints import strip_source_hints, index_source_hints
from .native_hints import verify_native_validation
from .evaluation_setup import (_mapping, _path, _string_list, _text, _valid_identifier,
                               assert_review_released)
from .treatment_versions import _run, _trees, _check_worktree

FIVE_ARMS = ('original', 'readme_only', 'alias_only', 'error_hints_only', 'combined')
DESIGNS = {'five_arm': FIVE_ARMS, 'refactor_pair': ('original', 'refactor_only'),
           'six_arm': FIVE_ARMS + ('refactor_only',)}
ALIAS_ARMS = ('alias_only', 'combined')
HINT_ARMS = ('error_hints_only', 'combined')
README_ARMS = ('readme_only', 'combined')


def bind_command(item, name, base, refs):
    # Validate the command and artifact lists. Resolve file arguments
    # relative to the YAML and append their bindings to refs in place.
    _mapping(item, name)
    _string_list(item.get('command'), name + ' command')
    item['command'] = [str(_path(base, s)) if (base / s).is_file() else s for s in item['command']]
    _string_list(item.get('artifacts'), name + ' artifacts')
    item['artifacts'] = [str(_path(base, p)) for p in item['artifacts']]
    refs.extend(bind(p) for p in item['artifacts'])
    refs.extend(bind(p) for p in item['command'] if Path(p).is_file())


def read_bank(path, cfg, refs):
    """The v1 protocol keeps canonical target IDs and requires all three controls."""
    # Read held-out tasks and add their reference, oracle, and negative
    # control files to refs. Return the validated task bank.
    bank = _mapping(load(path), 'Bank')
    _text(bank.get('scope_note', ''), 'Scope note', allow_empty=True)
    api_names = _string_list(bank.get('api_names'), 'API names')
    if len(set(api_names)) != len(api_names):
        raise ValueError('Duplicate API scope')
    cases = bank.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('Bank needs nonempty cases')
    ids, micro = set(), set()
    development = _string_list(cfg.get('development_case_ids', []), 'Development IDs', allow_empty=True)
    for c in cases:
        _mapping(c, 'Case')
        if not _valid_identifier(c.get('id')) or c['id'] in ids:
            raise ValueError('Unsafe or duplicate case ID')
        ids.add(c['id'])
        if c.get('kind') not in ('micro', 'puzzle') or c.get('split') != 'held_out':
            raise ValueError('Cases need micro/puzzle kind and held_out split')
        _text(c.get('prompt'), 'Case prompt')
        _text(c.get('public_context', ''), 'Public context', allow_empty=True)
        targets = _string_list(c.get('target_apis'), 'Canonical target APIs')
        if set(targets) - set(api_names) or len(set(targets)) != len(targets):
            raise ValueError('Targets must be unique members of the canonical API scope')
        if c['kind'] == 'micro':
            if len(targets) != 1:
                raise ValueError('Microtasks require one canonical target')
            micro.update(targets)
        for field in ('oracle', 'reference'):
            c[field] = str(_path(path.parent, c.get(field)))
            refs.append(bind(c[field]))
        for field in ('negative_controls', 'target_negative_controls'):
            _string_list(c.get(field), field)
            c[field] = [str(_path(path.parent, p)) for p in c[field]]
            refs.extend(bind(p) for p in c[field])
    if ids & set(development):
        raise ValueError('Development/evaluation IDs overlap')
    if micro != set(api_names) or not any(c['kind'] == 'puzzle' for c in cases):
        raise ValueError('Bank needs complete declared micro API coverage and puzzles')
    mapping = cfg.get('api_function_ids', {name: name for name in api_names})
    _mapping(mapping, 'api_function_ids')
    if set(mapping) != set(api_names):
        raise ValueError('api_function_ids must map every canonical API exactly once')
    for value in mapping.values():
        _text(value, 'Qualified function ID')
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('Qualified function IDs must be distinct')
    cfg['api_function_ids'] = mapping
    return bank


def backend_identity(condition):
    """Bind the Git tree, raw checkout, configured runtime and adapter artifacts."""
    # Require the configured worktree and revision, then fingerprint
    # its tracked code, build outputs, and adapter for use in checker results.
    source, adapter = condition['source'], condition['adapter']
    root = Path(source['worktree'])
    assert_review_released(root)
    if Path(_run(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Backend worktree must be the Git root')
    head = _run(root, 'rev-parse', '--verify', 'HEAD')
    if head != source['revision']:
        raise ValueError('Backend revision changed or is not an exact HEAD commit')
    branch = _run(root, 'symbolic-ref', '--quiet', '--short', 'HEAD')
    if source.get('branch') is not None and source['branch'] != branch:
        raise ValueError('Backend branch changed')
    _check_worktree(root, head, {})
    entries = _trees(root, head)
    # Installer-owned documentation/interface/hint files are treatment context,
    # not a change to the backend's library implementation.
    code = {p: value for p, value in entries.items() if not p.startswith('.aideal/treatments/')}
    identity = {'worktree': str(root), 'revision': head, 'branch': branch,
                'tree': _run(root, 'rev-parse', head + '^{tree}'),
                'code_tree_sha256': digest(code), 'code_files': {p: list(value) for p, value in code.items()},
                'source_artifacts': [bind(p) for p in source['artifacts']],
                'adapter_command': adapter['command'], 'adapter_artifacts': [bind(p) for p in adapter['artifacts']]}
    return {**identity, 'sha256': digest(identity)}


def hint_bundle(path, function_ids):
    # Read the older JSON hint format and check that at least one hint
    # refers to a function in the selected study.
    value = _mapping(load(path), 'Hint bundle')
    if type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise ValueError('Hint bundle needs schema_version 1')
    hints = value.get('hints')
    if not isinstance(hints, list) or not hints:
        raise ValueError('Hint treatment needs nonempty hints')
    known = False
    for h in hints:
        _mapping(h, 'Hint')
        for key in ('function_id', 'error_contains', 'likely_cause', 'validation'):
            _text(h.get(key), 'Hint ' + key)
        _string_list(h.get('fix_steps'), 'Hint fix_steps')
        _text(h.get('suggested_fix_code', ''), 'Hint code', allow_empty=True)
        known |= h['function_id'] in function_ids
    if not known:
        raise ValueError('Hints do not cover selected function IDs; supply api_function_ids')
    return value


def match_treatments(cfg, backends):
    """Reject treatment contamination before any model or checker command."""
    # Check that each arm receives its assigned resources. The combined
    # arm must reuse the same resources as the corresponding individual arms.
    conditions = cfg['conditions']
    signatures = {arm: [bind(p)['sha256'] for p in c['documents']] for arm, c in conditions.items()}
    original = signatures['original']
    for arm, c in conditions.items():
        if arm not in README_ARMS and signatures[arm] != original:
            raise ValueError(f'{arm} must receive the original documentation bytes')
        hint_field = {1: 'error_hints', 2: 'source_hints', 3: 'native_hints_validation'}[cfg['schema_version']]
        if any(field in c for field in ('error_hints', 'source_hints', 'native_hints_validation') if field != hint_field):
            raise ValueError(f'{arm}: mixed hint delivery protocols')
        for field, allowed in (('alias_interface', ALIAS_ARMS), (hint_field, HINT_ARMS)):
            if (field in c) != (arm in allowed):
                raise ValueError(f'{arm}: unexpected or missing {field}')
        if arm in ('readme_only', 'error_hints_only'):
            if not _matching_implementation(cfg, backends, 'original', arm):
                raise ValueError(f'{arm} must retain the original backend code tree')
    if 'combined' in conditions:
        if signatures['readme_only'] != signatures['combined']:
            raise ValueError('Combined must reuse the README-only documentation bytes')
        for field, arm in (('alias_interface', 'alias_only'),):
            if bind(conditions[arm][field])['sha256'] != bind(conditions['combined'][field])['sha256']:
                raise ValueError('Combined must reuse the individual ' + field + ' bytes')
        if cfg['schema_version'] == 3:
            left = _native_content(conditions['error_hints_only'])
            right = _native_content(conditions['combined'])
            if left != right:
                raise ValueError('Combined must reuse the individual native error guidance')
        elif cfg['schema_version'] == 2:
            left = _hint_content(conditions['error_hints_only'], cfg['api_function_ids'])
            right = _hint_content(conditions['combined'], cfg['api_function_ids'])
            if left != right:
                raise ValueError('Combined must reuse the individual source guidance')
        elif bind(conditions['error_hints_only']['error_hints'])['sha256'] != bind(conditions['combined']['error_hints'])['sha256']:
            raise ValueError('Combined must reuse the individual error_hints bytes')
        if not _matching_implementation(cfg, backends, 'alias_only', 'combined'):
            raise ValueError('Combined must reuse the alias-only backend code tree')
        if backends['alias_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
            raise ValueError('Alias treatment requires a changed backend code tree')
        baseline, aliases = backends['original']['code_files'], backends['alias_only']['code_files']
        if any(aliases.get(path) != entry for path, entry in baseline.items()):
            raise ValueError('Alias-only must add wrappers without modifying baseline tracked files')
    if 'refactor_only' in conditions and backends['refactor_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
        raise ValueError('Refactor-only requires a changed backend with the original target IDs')


def _matching_implementation(cfg, backends, baseline, treatment):
    """Allow only removal of validated annotation comment blocks in hint arms.

    Git still binds the actual source bytes. This comparison does not certify
    runtime equivalence; reference and negative controls run for every backend.
    """
    # Return whether both arms share the same code or differ only by
    # the hint edits permitted by the selected protocol.
    left, right = backends[baseline]['code_files'], backends[treatment]['code_files']
    if left == right:
        return True
    condition = cfg['conditions'][treatment]
    # Native hints are validated message patches in the compiled source.
    if cfg['schema_version'] == 3 and treatment in HINT_ARMS:
        if set(left) != set(right):
            return False
        proposal = verify_native_validation(condition['native_hints_validation'])
        sources = {s['path']: s for s in proposal['sources']}
        base = Path(cfg['conditions'][baseline]['source']['worktree'])
        root = Path(condition['source']['worktree'])
        for path in left:
            if left[path] == right[path]:
                continue
            if (path not in sources or left[path][0] != right[path][0]
                    or bind(base / path)['sha256'] != sources[path]['baseline']['sha256']
                    or bind(root / path)['sha256'] != sources[path]['candidate_sha256']):
                return False
        return True
    # The earlier source-comment protocol compares code after stripping
    # the permitted annotation blocks.
    if cfg['schema_version'] != 2 or treatment not in HINT_ARMS or set(left) != set(right):
        return False
    base = Path(cfg['conditions'][baseline]['source']['worktree'])
    root = Path(condition['source']['worktree'])
    permitted = {str(Path(p)) for p in condition['source_hints']}
    for path in left:
        if left[path] == right[path]:
            continue
        if path not in permitted or left[path][0] != right[path][0]:
            return False
        if strip_source_hints((root / path).read_bytes().decode('utf-8')) != (base / path).read_bytes().decode('utf-8'):
            return False
    return True


def _hint_content(condition, function_ids):
    # Extract the guidance fields used to compare two source-comment
    # treatments, sorted so record order does not affect the comparison.
    index = index_source_hints(condition['source']['worktree'], condition['source_hints'], function_ids)
    fields = ('function_id', 'requirement_id', 'requirement', 'signature', 'action', 'validation', 'diagnostic', 'status')
    return sorted((tuple(str(row.get(k)) for k in fields) for row in index['records']))


def _native_content(condition):
    # Check that the installed source matches the validated patches,
    # then return the sorted function, requirement, and emitted message tuples.
    proposal = verify_native_validation(condition['native_hints_validation'])
    root = Path(condition['source']['worktree'])
    for source in proposal['sources']:
        if bind(root / source['path'])['sha256'] != source['candidate_sha256']:
            raise ValueError('Native diagnostic source differs from validated message patch')
    return sorted((h['function_id'], h['requirement_id'], h['emitted_message']) for h in proposal['hints'])
