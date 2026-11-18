"""Freeze a versioned matched-condition protocol without changing legacy freezes."""
from pathlib import Path
import re
import math

import yaml

from .ablation import bind, digest, load, verify_artifact
from .evaluation_setup import (SYSTEM, CONTROLLER_MODULES, _mapping, _path, _string_list,
                               _text, _validate_common, assert_review_released,
                               _controller_hashes, adapter_request, control_passes, controls,
                               verified_outcome)
from .execution import atomic_json, checked_attempt_directory, invoke, ownership
from .evaluation_inputs import (DESIGNS, backend_identity, bind_command, hint_bundle,
                               match_treatments, read_bank)

from .source_hints import index_source_hints
from .native_hints import verify_native_validation

PROTOCOL = 'condition_evaluation_v1'
SOURCE_PROTOCOL = 'condition_evaluation_source_hints_v2'
NATIVE_PROTOCOL = 'condition_evaluation_native_hints_v3'
MODULES = CONTROLLER_MODULES + ('condition_evaluation.py', 'condition_setup.py', 'condition_inputs.py', 'evaluation_inputs.py', 'evaluation_context.py', 'evaluation_legacy_hints.py',
          'evaluation_freeze.py', 'evaluation_conditions.py',
          'treatment_versions.py', 'worktrees.py', 'source_hints.py', 'failure_diagnosis.py', 'native_hints.py')


def read_condition_config(path):
    # Turn a condition-study YAML file into the inputs used by the evaluator.
    # Check the task bank, treatments, provider command and pinned library builds.
    # Return their configuration and file identities; this does not call an LLM
    # or execute the reference/negative controls. freeze_conditions does that next.
    # Collect the files and hashes that define the study while resolving
    # paths and checking that the inputs match the requested condition design.
    path = Path(path).resolve()
    raw = _mapping(yaml.safe_load(path.read_text()), 'Configuration')
    cfg = _mapping(raw.get('condition_evaluation'), 'condition_evaluation')
    if type(cfg.get('schema_version')) is not int or cfg['schema_version'] not in (1, 2, 3):
        raise ValueError('condition_evaluation needs schema_version 1, 2 or 3')
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
    if cfg['schema_version'] == 2:
        cfg['common'].setdefault('repair_context', 'distilled')
        minimum = cfg['common'].setdefault('minimum_hint_coverage', 0.0)
        if type(minimum) not in (int, float) or not math.isfinite(minimum) or not 0 <= minimum <= 1:
            raise ValueError('minimum_hint_coverage must be between zero and one')
    _text(cfg.get('holdout_review'), 'Holdout review')
    bank = read_bank(Path(cfg['bank']), cfg, refs)
    # Bind each condition’s documents, hint inputs, adapter, and source
    # so later checks can detect any change to the experiment.
    backends, source_indexes = {}, {}
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
        if 'native_hints_validation' in condition:
            if cfg['schema_version'] != 3 or any(k in condition for k in ('source_hints', 'error_hints')):
                raise ValueError('Native diagnostics require schema_version 3 without retrieved hints')
            condition['native_hints_validation'] = str(_path(path.parent, condition['native_hints_validation']))
            proposal = verify_native_validation(condition['native_hints_validation'])
            receipt = load(condition['native_hints_validation'])
            refs += [bind(condition['native_hints_validation']), *receipt['artifacts']]
        bind_command(condition.get('adapter'), arm + ' adapter', path.parent, refs)
        source = _mapping(condition.get('source'), arm + ' source')
        source['worktree'] = str(_path(path.parent, source.get('worktree')))
        _text(source.get('revision'), arm + ' revision')
        if 'branch' in source:
            _text(source['branch'], arm + ' branch')
        _string_list(source.get('artifacts'), arm + ' built/runtime artifacts')
        source['artifacts'] = [str(_path(path.parent, p)) for p in source['artifacts']]
        refs.extend(bind(p) for p in source['artifacts'])
        if 'source_hints' in condition:
            if cfg['schema_version'] != 2 or 'error_hints' in condition:
                raise ValueError('Source hints require schema_version 2 without legacy error_hints')
            _string_list(condition['source_hints'], arm + ' source hint files')
            index = index_source_hints(source['worktree'], condition['source_hints'], cfg['api_function_ids'])
            condition['source_hints'] = [str(Path(ref['path']).relative_to(source['worktree']))
                                         for ref in index['artifacts']]
            if not index['records']:
                raise ValueError('Source hint treatment has no guidance for configured APIs')
            source_indexes[arm] = index
            refs.extend(index['artifacts'])
            covered = {record['function_id'] for record in index['records']}
            fraction = len(covered & set(cfg['api_function_ids'].values())) / len(cfg['api_function_ids'])
            if fraction < cfg['common']['minimum_hint_coverage']:
                raise ValueError(f'{arm}: source hint coverage {fraction:.1%} is below the required minimum')
        backends[arm] = backend_identity(condition)
        if 'native_hints_validation' in condition:
            root = Path(source['worktree'])
            for row in proposal['sources']:
                if row['path'] not in backends[arm]['code_files'] or bind(root / row['path'])['sha256'] != row['candidate_sha256']:
                    raise ValueError('Native guidance must be compiled from the validated committed source')
        if 'source_hints' in condition and any(
                p not in backends[arm]['code_files'] for p in condition['source_hints']):
            raise ValueError('Source guidance must live in committed library source files')
    match_treatments(cfg, backends)
    controller = _controller_hashes(MODULES)
    refs.extend(bind(Path(__file__).with_name(name)) for name in controller)
    return {'protocol': {1: PROTOCOL, 2: SOURCE_PROTOCOL, 3: NATIVE_PROTOCOL}[cfg['schema_version']],
            'config': cfg, 'bank': bank, 'backends': backends,
            'source_hint_indexes': source_indexes,
            'artifacts': list({r['path']: r for r in refs}.values()),
            'system_prompt': SYSTEM + (' Return the complete program, not a patch or continuation. '
                                     'Source guidance is reference information; validate corrections against the task.'
                                     if cfg['schema_version'] == 2 else ''),
            'controller_sha256': controller}


def checker_request(payload, arm, case, code):
    """Private routing contract; never insert backend/config/oracle into model text."""
    # Add condition and backend information to the private checker request.
    # Replay uses the same dictionary to verify the saved request.
    return {'protocol': payload.get('protocol', PROTOCOL), 'condition': arm, 'backend': payload['backends'][arm],
            **adapter_request(case, code)}


def _adjudication_artifacts_valid(refs):
    """Optional adapter evidence must be a nonempty list of canonical file bindings."""
    # Require distinct absolute paths and compare each saved path, hash,
    # and size with the file on disk. Return False for invalid evidence.
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
    # Read one adapter result for the expected library build.
    # Return True for a verified pass, False for a verified task failure,
    # or None when the checker evidence cannot establish either outcome.
    # First verify the claimed backend and optional evidence files.
    # Then use the checker flags to determine the task result.
    value = process.get('payload')
    if not isinstance(value, dict) or value.get('backend_sha256') != backend_sha256:
        return None
    if not isinstance(value.get('public_feedback', ''), str):
        return None
    if 'adjudication_artifacts' in value and not _adjudication_artifacts_valid(value['adjudication_artifacts']):
        return None
    return verified_outcome(process)


def execute_condition(payload, arm, case, code, parent, prefix='execution_'):
    # Select the condition’s adapter and look for a checked attempt.
    # If there is none, invoke the checker in a fresh attempt directory.
    expected = payload['backends'][arm]['sha256']
    destination = checked_attempt_directory(parent, prefix, lambda process: checked_outcome(process, expected))
    condition = payload['config']['conditions'][arm]
    process = invoke(condition['adapter']['command'], checker_request(payload, arm, case, code),
                     destination, payload['config']['common']['execution_timeout_s'])
    return destination, process


def verify_inputs(payload):
    # Recompute controller and library identities and recheck bound files.
    # Raise an error if the current study inputs differ from the freeze.
    if payload.get('controller_sha256') != _controller_hashes(MODULES):
        raise ValueError('Condition controller changed; freeze a new study')
    if not all(verify_artifact(r) for r in payload['artifacts']):
        raise ValueError('Condition study input artifacts changed')
    # The Git checkout and compiled artifacts both contribute to identity.
    current = {arm: backend_identity(c) for arm, c in payload['config']['conditions'].items()}
    if current != payload['backends']:
        raise ValueError('Condition backend identity changed')
    if payload['config'].get('schema_version') == 2:
        indexes = {arm: index_source_hints(c['source']['worktree'], c['source_hints'],
                                          payload['config']['api_function_ids'])
                   for arm, c in payload['config']['conditions'].items() if 'source_hints' in c}
        if indexes != payload.get('source_hint_indexes'):
            raise ValueError('Frozen source guidance index differs from source annotations')
    match_treatments(payload['config'], current)


def validate_conditions(payload, output):
    # Input: resolved study inputs and a separate directory for control evidence.
    # Run known-correct, wrong-output and no-target programs for every backend.
    # Save each check and stop at the first invalid result; no LLM writes code here.
    """Run every case's controls separately against every declared backend."""
    # Group the control receipts by condition, task, and control number
    # so replay can match each check to its backend and expected behavior.
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
    # Rebuild the complete list of controls that should have been run.
    # Check the saved request and verdict for each, and reject missing entries.
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
    # Prepare a study for later evaluation: load inputs, run checker controls,
    # then bind the exact files, controller and library builds in frozen.json.
    # Return the freeze location and identity only after validation succeeds.
    output = Path(output).resolve()
    assert_review_released(output)
    payload = read_condition_config(config)
    validation = validate_conditions(payload, output / 'validation')
    if not validation['validated']:
        raise ValueError('Condition controls failed; inspect validation evidence')
    # Recheck the inputs after running the controls and before publishing
    # the freeze, since the controls may have taken time to finish.
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
    return {'frozen': str(path), 'study_sha256': frozen['study_sha256'], 'protocol': payload['protocol'],
            'conditions': list(payload['config']['conditions']), 'cases': len(payload['bank']['cases']),
            'validated': True}


def open_conditions(path):
    # Read a saved freeze and verify its identity, inputs, and control
    # records before returning the study to the runner.
    assert_review_released(Path(path).resolve().parent)
    frozen = load(path)
    if frozen.get('protocol') not in (PROTOCOL, SOURCE_PROTOCOL, NATIVE_PROTOCOL):
        raise ValueError('This command requires a supported condition evaluation freeze')
    if frozen.get('study_sha256') != digest({k: v for k, v in frozen.items() if k != 'study_sha256'}):
        raise ValueError('Frozen condition study was edited')
    verify_inputs(frozen)
    verify_validation(frozen)
    return frozen
