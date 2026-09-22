"""Freeze a versioned matched-condition protocol without changing legacy freezes."""
from pathlib import Path
import re

import yaml

from .ablation import bind, digest, file_hash, load, verify_artifact
from .evaluation_setup import (SYSTEM, CONTROLLER_MODULES, _mapping, _path, _string_list,
                               _text, _validate_common, assert_review_released,
                               control_passes, verified_outcome)
from .execution import atomic_json, invoke, next_directory, ownership
from .condition_inputs import (DESIGNS, backend_identity, bind_command, hint_bundle,
                               match_treatments, read_bank)

PROTOCOL = 'condition_evaluation_v1'
MODULES = CONTROLLER_MODULES + ('condition_inputs.py', 'condition_context.py',
          'condition_setup.py', 'condition_evaluation.py', 'condition_reporting.py',
          'treatment_versions.py', 'worktrees.py')


def _controller(cfg=None):
    optional = ('documentation_selection.py',) if cfg and 'documentation_selection' in cfg['common'] else ()
    return {name: file_hash(Path(__file__).with_name(name)) for name in MODULES + optional}


def read_condition_config(path):
    path = Path(path).resolve()
    raw = _mapping(yaml.safe_load(path.read_text()), 'Configuration')
    cfg = _mapping(raw.get('condition_evaluation'), 'condition_evaluation')
    if type(cfg.get('schema_version')) is not int or cfg['schema_version'] != 1:
        raise ValueError('condition_evaluation needs schema_version 1')
    if not isinstance(cfg.get('design'), str) or cfg['design'] not in DESIGNS:
        raise ValueError('Choose five_arm, refactor_pair, or six_arm')
    arms = DESIGNS[cfg['design']]
    conditions = _mapping(cfg.get('conditions'), 'conditions')
    if set(conditions) != set(arms):
        raise ValueError('Conditions do not match the declared design')
    cfg['conditions'] = {arm: conditions[arm] for arm in arms}
    refs = [bind(path)]
    cfg['bank'] = str(_path(path.parent, cfg.get('bank')))
    refs.append(bind(cfg['bank']))
    bind_command(cfg.get('model'), 'model', path.parent, refs)
    _validate_common(_mapping(cfg.get('common'), 'common'), cfg['model'])
    for field in ('alias_max_characters', 'hint_max_characters'):
        value = cfg['common'].setdefault(field, 4000)
        if type(value) is not int or value < 1:
            raise ValueError(field + ' must be a positive integer')
    _text(cfg.get('holdout_review'), 'Holdout review')
    bank = read_bank(Path(cfg['bank']), cfg, refs)
    if 'documentation_selection' in cfg['common']:
        from .documentation_selection import validate_documentation_selection
        validate_documentation_selection(cfg['common']['documentation_selection'], bank['api_names'])
    backends = {}
    for arm, condition in cfg['conditions'].items():
        _mapping(condition, arm)
        _string_list(condition.get('documents'), arm + ' documents')
        condition['documents'] = [str(_path(path.parent, p)) for p in condition['documents']]
        refs.extend(bind(p) for p in condition['documents'])
        for field in ('alias_interface', 'error_hints'):
            if field in condition:
                condition[field] = str(_path(path.parent, condition[field]))
                refs.append(bind(condition[field]))
                if field == 'alias_interface' and not Path(condition[field]).read_text().strip():
                    raise ValueError('Alias interface must not be empty')
        if 'error_hints' in condition:
            hint_bundle(condition['error_hints'], set(cfg['api_function_ids'].values()))
        bind_command(condition.get('adapter'), arm + ' adapter', path.parent, refs)
        source = _mapping(condition.get('source'), arm + ' source')
        source['worktree'] = str(_path(path.parent, source.get('worktree')))
        _text(source.get('revision'), arm + ' revision')
        if 'branch' in source:
            _text(source['branch'], arm + ' branch')
        _string_list(source.get('artifacts'), arm + ' built/runtime artifacts')
        source['artifacts'] = [str(_path(path.parent, p)) for p in source['artifacts']]
        refs.extend(bind(p) for p in source['artifacts'])
        backends[arm] = backend_identity(condition)
    match_treatments(cfg, backends)
    controller = _controller(cfg)
    refs.extend(bind(Path(__file__).with_name(name)) for name in controller)
    return {'protocol': PROTOCOL, 'config': cfg, 'bank': bank, 'backends': backends,
            'artifacts': list({r['path']: r for r in refs}.values()),
            'system_prompt': SYSTEM, 'controller_sha256': controller}


def checker_request(payload, arm, case, code):
    """Private routing contract; never insert backend/config/oracle into model text."""
    return {'protocol': PROTOCOL, 'condition': arm, 'backend': payload['backends'][arm],
            'code': code, 'case_id': case['id'], 'oracle_path': case['oracle'],
            'target_apis': case['target_apis']}


def _adjudication_artifacts_valid(refs):
    """Optional adapter evidence must be a nonempty list of canonical file bindings."""
    if not isinstance(refs, list) or not refs:
        return False
    seen = set()
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {'path', 'sha256', 'bytes'}
                or not isinstance(ref['path'], str) or not Path(ref['path']).is_absolute()
                or not isinstance(ref['sha256'], str) or re.fullmatch(r'[0-9a-f]{64}', ref['sha256']) is None
                or type(ref['bytes']) is not int or ref['bytes'] < 0 or ref['path'] in seen):
            return False
        seen.add(ref['path'])
        try:
            if bind(ref['path']) != ref:
                return False
        except (OSError, ValueError, RuntimeError):
            return False
    return True


def checked_outcome(process, backend_sha256):
    value = process.get('payload')
    if not isinstance(value, dict) or value.get('backend_sha256') != backend_sha256:
        return None
    if not isinstance(value.get('public_feedback', ''), str):
        return None
    if 'adjudication_artifacts' in value and not _adjudication_artifacts_valid(value['adjudication_artifacts']):
        return None
    return verified_outcome(process)


def execute_condition(payload, arm, case, code, parent, prefix='execution_'):
    expected = payload['backends'][arm]['sha256']
    completed = sorted(parent.glob(prefix + '*/process.json'))
    reusable = [p for p in completed if checked_outcome(load(p), expected) is not None]
    destination = reusable[-1].parent if reusable else next_directory(parent, prefix)
    condition = payload['config']['conditions'][arm]
    process = invoke(condition['adapter']['command'], checker_request(payload, arm, case, code),
                     destination, payload['config']['common']['execution_timeout_s'])
    return destination, process


def controls(case):
    return ([('reference', case['reference'])]
            + [('wrong_output', p) for p in case['negative_controls']]
            + [('no_target_call', p) for p in case['target_negative_controls']])


def verify_inputs(payload):
    if payload.get('controller_sha256') != _controller(payload['config']):
        raise ValueError('Condition controller changed; freeze a new study')
    if not all(verify_artifact(r) for r in payload['artifacts']):
        raise ValueError('Condition study input artifacts changed')
    current = {arm: backend_identity(c) for arm, c in payload['config']['conditions'].items()}
    if current != payload['backends']:
        raise ValueError('Condition backend identity changed')
    match_treatments(payload['config'], current)


def validate_conditions(payload, output):
    """Run every case's controls separately against every declared backend."""
    output = Path(output).resolve()
    assert_review_released(output.parent)
    fingerprint = digest(payload)
    with ownership(output):
        identity = output / 'identity.json'
        if identity.exists() and load(identity).get('fingerprint') != fingerprint:
            raise ValueError('Condition validation inputs changed; choose a new output')
        atomic_json(identity, {'fingerprint': fingerprint})
        records = []
        for arm in payload['config']['conditions']:
            for case in payload['bank']['cases']:
                for index, (role, path) in enumerate(controls(case)):
                    parent = output / arm / case['id'] / f'control_{index:03d}'
                    directory, result = execute_condition(payload, arm, case, Path(path).read_text(),
                                                          parent, prefix='attempt_')
                    valid = (checked_outcome(result, payload['backends'][arm]['sha256']) is not None
                             and control_passes(role, result))
                    records.append({'arm': arm, 'case_id': case['id'], 'control': index, 'role': role,
                                    'backend_sha256': payload['backends'][arm]['sha256'], 'valid': valid,
                                    'evidence': bind(directory / 'process.json'),
                                    'request': bind(directory / 'request.json')})
                    result = {'fingerprint': fingerprint, 'validated': False, 'controls': records}
                    atomic_json(output / 'validation.json', result)
                    if not valid:
                        return result
        result.update(validated=True)
        atomic_json(output / 'validation.json', result)
        return result


def verify_validation(frozen):
    validation = frozen.get('validation', {})
    if validation.get('validated') is not True:
        raise ValueError('Missing successful condition validation')
    expected = {(arm, case['id'], i): (role, case, path)
                for arm in frozen['config']['conditions'] for case in frozen['bank']['cases']
                for i, (role, path) in enumerate(controls(case))}
    seen = set()
    for record in validation.get('controls', []):
        key = (record['arm'], record['case_id'], record['control'])
        if key not in expected or key in seen:
            raise ValueError('Unexpected or duplicate condition control evidence')
        seen.add(key)
        role, case, code_path = expected[key]
        backend = frozen['backends'][key[0]]['sha256']
        if (record.get('valid') is not True or record.get('role') != role
                or record.get('backend_sha256') != backend
                or not all(verify_artifact(record[field]) for field in ('evidence', 'request'))):
            raise ValueError('Condition control evidence changed or has the wrong backend')
        result = load(record['evidence']['path'])
        request = load(record['request']['path'])
        if (request != checker_request(frozen, key[0], case, Path(code_path).read_text())
                or checked_outcome(result, backend) is None or not control_passes(role, result)):
            raise ValueError('Condition control evidence does not validate the declared backend')
    if seen != set(expected):
        raise ValueError('Missing condition control evidence')


def freeze_conditions(config, output):
    output = Path(output).resolve()
    assert_review_released(output)
    payload = read_condition_config(config)
    validation = validate_conditions(payload, output / 'validation')
    if not validation['validated']:
        raise ValueError('Condition controls failed; inspect validation evidence')
    verify_inputs(payload)
    frozen = {**payload, 'validation': validation}
    frozen['study_sha256'] = digest(frozen)
    verify_validation(frozen)
    with ownership(output):
        path = output / 'frozen.json'
        if path.exists() and load(path) != frozen:
            raise ValueError('Existing condition freeze differs')
        if not path.exists():
            atomic_json(path, frozen)
    return {'frozen': str(path), 'study_sha256': frozen['study_sha256'], 'protocol': PROTOCOL,
            'conditions': list(payload['config']['conditions']), 'cases': len(payload['bank']['cases']),
            'validated': True}


def open_conditions(path):
    assert_review_released(Path(path).resolve().parent)
    frozen = load(path)
    if frozen.get('protocol') != PROTOCOL:
        raise ValueError('This command requires a condition_evaluation_v1 freeze')
    if frozen.get('study_sha256') != digest({k: v for k, v in frozen.items() if k != 'study_sha256'}):
        raise ValueError('Frozen condition study was edited')
    verify_inputs(frozen)
    verify_validation(frozen)
    return frozen
