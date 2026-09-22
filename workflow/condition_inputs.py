"""Explicit condition protocol: matched documents, Git backends and hint inputs."""
from pathlib import Path

from .ablation import bind, digest, load
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
    _mapping(item, name)
    _string_list(item.get('command'), name + ' command')
    item['command'] = [str(_path(base, s)) if (base / s).is_file() else s for s in item['command']]
    _string_list(item.get('artifacts'), name + ' artifacts')
    item['artifacts'] = [str(_path(base, p)) for p in item['artifacts']]
    refs.extend(bind(p) for p in item['artifacts'])
    refs.extend(bind(p) for p in item['command'] if Path(p).is_file())


def read_bank(path, cfg, refs):
    """The v1 protocol keeps canonical target IDs and requires all three controls."""
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
    conditions = cfg['conditions']
    signatures = {arm: [bind(p)['sha256'] for p in c['documents']] for arm, c in conditions.items()}
    original = signatures['original']
    for arm, c in conditions.items():
        if arm not in README_ARMS and signatures[arm] != original:
            raise ValueError(f'{arm} must receive the original documentation bytes')
        for field, allowed in (('alias_interface', ALIAS_ARMS), ('error_hints', HINT_ARMS)):
            if (field in c) != (arm in allowed):
                raise ValueError(f'{arm}: unexpected or missing {field}')
        if arm in ('readme_only', 'error_hints_only'):
            if backends[arm]['code_tree_sha256'] != backends['original']['code_tree_sha256']:
                raise ValueError(f'{arm} must retain the original backend code tree')
    if 'combined' in conditions:
        if signatures['readme_only'] != signatures['combined']:
            raise ValueError('Combined must reuse the README-only documentation bytes')
        for field, arm in (('alias_interface', 'alias_only'), ('error_hints', 'error_hints_only')):
            if bind(conditions[arm][field])['sha256'] != bind(conditions['combined'][field])['sha256']:
                raise ValueError('Combined must reuse the individual ' + field + ' bytes')
        if backends['combined']['code_tree_sha256'] != backends['alias_only']['code_tree_sha256']:
            raise ValueError('Combined must reuse the alias-only backend code tree')
        if backends['alias_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
            raise ValueError('Alias treatment requires a changed backend code tree')
        baseline, aliases = backends['original']['code_files'], backends['alias_only']['code_files']
        if any(aliases.get(path) != entry for path, entry in baseline.items()):
            raise ValueError('Alias-only must add wrappers without modifying baseline tracked files')
    if 'refactor_only' in conditions and backends['refactor_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
        raise ValueError('Refactor-only requires a changed backend with the original target IDs')
