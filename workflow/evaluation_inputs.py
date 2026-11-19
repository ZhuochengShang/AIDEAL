"""Explicit condition protocol: matched documents, Git backends and hint inputs."""
from pathlib import Path

from .ablation import bind, digest, load
from .source_hints import strip_source_hints, index_source_hints
from .native_hints import verify_native_validation
from .evaluation_setup import (_mapping, _path, _string_list, _text, _valid_identifier,
                               assert_review_released)
from .treatment_versions import _run, _trees, _check_worktree, _read_proposal, _artifact_role

FIVE_ARMS = ('original', 'readme_only', 'alias_only', 'error_hints_only', 'combined')
EIGHT_ARMS = FIVE_ARMS[:-1] + ('readme_alias', 'readme_error_hints', 'alias_error_hints', 'combined')
DESIGNS = {'eight_arm': EIGHT_ARMS, 'five_arm': FIVE_ARMS, 'refactor_pair': ('original', 'refactor_only'),
           'six_arm': FIVE_ARMS + ('refactor_only',)}
ALIAS_ARMS = ('alias_only', 'readme_alias', 'alias_error_hints', 'combined')
HINT_ARMS = ('error_hints_only', 'readme_error_hints', 'alias_error_hints', 'combined')
README_ARMS = ('readme_only', 'readme_alias', 'readme_error_hints', 'combined')


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
    """Match each factor's exact resources across every participating condition."""
    conditions = cfg['conditions']
    signatures = {arm: [bind(p)['sha256'] for p in c['documents']] for arm, c in conditions.items()}
    hint_field = {1: 'error_hints', 2: 'source_hints', 3: 'native_hints_validation'}[cfg['schema_version']]
    for arm, condition in conditions.items():
        label = 'Combined' if arm == 'combined' else arm
        reference = 'readme_only' if arm in README_ARMS else 'original'
        if signatures[arm] != signatures[reference]:
            raise ValueError(f'{label} must reuse the {reference} documentation bytes')
        if any(field in condition for field in ('error_hints', 'source_hints', 'native_hints_validation') if field != hint_field):
            raise ValueError(f'{arm}: mixed hint delivery protocols')
        for field, allowed in (('alias_interface', ALIAS_ARMS), (hint_field, HINT_ARMS)):
            if (field in condition) != (arm in allowed):
                raise ValueError(f'{arm}: unexpected or missing {field}')
        if arm in ALIAS_ARMS:
            if bind(condition['alias_interface'])['sha256'] != bind(conditions['alias_only']['alias_interface'])['sha256']:
                raise ValueError(f'{label} must reuse the individual alias_interface bytes')
        if arm in HINT_ARMS:
            baseline = conditions['error_hints_only']
            if cfg['schema_version'] == 3:
                same = _native_content(condition) == _native_content(baseline)
            elif cfg['schema_version'] == 2:
                same = _hint_content(condition, cfg['api_function_ids']) == _hint_content(baseline, cfg['api_function_ids'])
            else:
                same = bind(condition['error_hints'])['sha256'] == bind(baseline['error_hints'])['sha256']
            if not same:
                kind = {1: 'error_hints bytes', 2: 'source guidance', 3: 'native error guidance'}[cfg['schema_version']]
                raise ValueError(f'{label} must reuse the individual {kind}')
        if arm not in ('original', 'alias_only', 'refactor_only'):
            baseline = 'alias_only' if arm in ALIAS_ARMS else 'original'
            if not _matching_implementation(cfg, backends, baseline, arm):
                raise ValueError(f'{label} must reuse the {baseline.replace("_", "-")} backend code tree')
    if 'alias_only' in conditions:
        if backends['alias_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
            raise ValueError('Alias treatment requires a changed backend code tree')
        baseline, aliases = backends['original']['code_files'], backends['alias_only']['code_files']
        if any(aliases.get(path) != entry for path, entry in baseline.items()):
            raise ValueError('Alias-only must add wrappers without modifying baseline tracked files')
    if 'refactor_only' in conditions and backends['refactor_only']['code_tree_sha256'] == backends['original']['code_tree_sha256']:
        raise ValueError('Refactor-only requires a changed backend with the original target IDs')


def read_alias_controls(cfg, base, bank, backends, refs):
    """Bind the complete installed alias bundle and its independent development controls.

    A proposal's syntax/install status is not validation. Every declared wrapper
    needs valid-input and error-behavior pairs, plus wrong-result and alias-bypass
    controls. The freeze executes them before admitting an eight-arm study.
    """
    plan = _mapping(cfg.get('alias_validation'), 'Eight-arm alias_validation')
    proposal_path = _path(base, plan.get('proposal'))
    proposal, _ = _read_proposal(proposal_path, cfg['conditions']['original']['source']['revision'])
    aliases = proposal.get('aliases')
    if not isinstance(aliases, list) or not aliases:
        raise ValueError('Alias bundle needs its complete declared wrapper inventory')
    names = {}
    for alias in aliases:
        _mapping(alias, 'Alias inventory entry')
        name = _text(alias.get('name'), 'Alias name')
        target = _text(alias.get('target_function'), 'Alias target')
        if name in names or target not in cfg['api_function_ids'].values():
            raise ValueError('Alias names must be unique and target the declared API scope')
        names[name] = target
    alias_root = Path(cfg['conditions']['alias_only']['source']['worktree'])
    artifacts = proposal['artifacts']
    sources = {item['target']: item for key, item in artifacts.items() if _artifact_role(key) == 'alias'}
    added = set(backends['alias_only']['code_files']) - set(backends['original']['code_files'])
    if set(sources) != added or any(bind(alias_root / path)['sha256'] != item['sha256'] for path, item in sources.items()):
        raise ValueError('Installed alias source must exactly match the complete declared bundle')
    if bind(cfg['conditions']['alias_only']['alias_interface'])['sha256'] != artifacts['alias_interface']['sha256']:
        raise ValueError('Installed alias interface differs from the declared bundle')
    refs.extend([bind(proposal_path), *(bind(item['path']) for item in artifacts.values())])
    cases = plan.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('Eight-arm aliases require development control cases')
    held_out = {case['id'] for case in bank['cases']}
    development = set(cfg.get('development_case_ids', []))
    seen, coverage = set(), {name: set() for name in names}
    for case in cases:
        _mapping(case, 'Alias development control')
        if (not _valid_identifier(case.get('id')) or case['id'] in seen or case['id'] in held_out
                or case['id'] not in development or case.get('split') != 'development'):
            raise ValueError('Alias controls need distinct declared development IDs outside the held-out bank')
        seen.add(case['id'])
        alias, api = case.get('alias'), case.get('target_api')
        if alias not in names or cfg['api_function_ids'].get(api) != names[alias]:
            raise ValueError('Alias control target does not match its bundle mapping')
        if case.get('kind') not in ('valid', 'error'):
            raise ValueError('Alias controls must label valid or error behavior')
        coverage[alias].add(case['kind'])
        case['target_apis'] = [api]
        for key in ('canonical_reference', 'alias_reference', 'oracle'):
            case[key] = str(_path(base, case.get(key)))
            refs.append(bind(case[key]))
        for key in ('negative_controls', 'alias_negative_controls'):
            _string_list(case.get(key), 'Alias ' + key)
            case[key] = [str(_path(base, item)) for item in case[key]]
            refs.extend(bind(item) for item in case[key])
    if any(kinds != {'valid', 'error'} for kinds in coverage.values()):
        raise ValueError('Every declared alias needs valid and error development controls')
    plan['proposal'] = str(proposal_path)
    plan['aliases'] = names
    return plan


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
