"""Read-only local task/attempt index; never call providers or rerun checkers."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re

TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_tokens',
              'non_reasoning_output_tokens', 'total_tokens')
DIAGNOSTIC_RULES = {
    'type_mismatch': r'\btype mismatch\b|\bincompatible types\b',
    'missing_name_or_import': r'not found: (?:value|type|object)|cannot find symbol|No module named|\b(?:ModuleNotFoundError|ImportError|NameError)\b',
    'wrong_argument_count': r'not enough arguments|too many arguments|wrong number of arguments|missing .*required positional argument|takes .*arguments? but',
    'wrong_receiver_or_member': r'is not a member of|has no attribute|cannot find member',
    'syntax_error': r'\bSyntaxError\b|expected but .*found|illegal start|unclosed (?:string|comment)|unexpected (?:token|indent|EOF)',
    'runtime_exception': r'Exception in thread|Traceback \(most recent call last\)|\b[A-Za-z][\w.]*(?:Exception|Error)(?::|$)',
    'timeout': r'\b(?:TimeoutExpired|TimeoutException)\b|timed out',
}


def _diagnostics(directory):
    """Heuristic tags point to saved lines; never expose diagnostic/private values."""
    tags = []
    for name in ('compile.stderr', 'run.stderr', 'program/program.stderr', 'program/debugger.stderr'):
        path = directory / name
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            continue
        lines = path.read_text(errors='replace').splitlines()
        for tag, pattern in DIAGNOSTIC_RULES.items():
            matched = [i for i, line in enumerate(lines, 1) if re.search(pattern, line)]
            if matched:
                tags.append({'tag': tag, 'basis': 'heuristic_pattern_not_verified_root_cause',
                             'pattern': pattern, 'line_numbers': matched, 'evidence': _binding(path)})
    return tags


def _read(path):
    result = json.loads(path.read_text()) if path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)) else {}
    if not isinstance(result, dict):
        raise ValueError('Expected an evidence object')
    return result


def _binding(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def _files(root):
    """Prune library checkouts/private banks; do not traverse symlink directories."""
    for current, directories, names in os.walk(root, followlinks=False):
        directories[:] = [d for d in sorted(directories) if d not in
                          ('.git', 'repository.git', 'source', 'bank', '__pycache__')
                          and not (Path(current) / d).is_symlink()]
        for name in sorted(names):
            path = Path(current) / name
            if not path.is_symlink():
                yield path


def _identity(directory, request):
    identity = {'case_id': request.get('case_id'), 'trial_id': None,
                'condition': request.get('condition'), 'fix_round': None,
                'attempt_directory': directory.name}
    for parent in directory.parents:
        if parent.name.startswith('round_') and parent.name[6:].isdigit():
            identity['fix_round'] = int(parent.name[6:])
            unit = parent.parent.name
            if '--' in unit:
                identity['case_id'], identity['trial_id'] = unit.rsplit('--', 1)
            identity['condition'] = parent.parent.parent.name
            break
    if identity['fix_round'] is not None:
        identity['phase'] = 'initial' if identity['fix_round'] == 0 else 'code_repair'
    else:
        identity['phase'] = 'control' if any(p.name.startswith('control_') for p in directory.parents) else 'proposal'
    return identity


def _tokens(payload):
    usage = payload.get('usage') or {}
    return {key: usage.get(key) if type(usage.get(key)) is int and usage[key] >= 0 else None
            for key in TOKEN_KEYS}


def _categories(kind, process, payload, directory):
    status = process.get('status', 'in_progress_or_interrupted')
    if status not in ('ok', 'completed'):
        return [process.get('error_category') or status]
    if kind == 'provider':
        if payload.get('refusals') or payload.get('response_kind') == 'refusal':
            return ['provider_refusal']
        if payload.get('truncated') or payload.get('response_status') == 'incomplete':
            return ['provider_incomplete_output']
        if payload.get('response_status') not in (None, 'completed'):
            return ['provider_noncompleted_status']
        return [] if isinstance(payload.get('code'), str) and payload['code'].strip() else ['provider_empty_or_invalid_output']
    flags = ('execution_pass', 'oracle_pass', 'target_reached')
    if not all(type(payload.get(key)) is bool for key in flags):
        return ['unverified_checker_payload']
    result = []
    if not payload['execution_pass']:
        compile_log = directory / 'compile.stderr'
        result.append('candidate_compile_or_execution_failure')
        if compile_log.is_file() and compile_log.stat().st_size:
            result.append('compiler_diagnostic_present')
    else:
        if not payload['oracle_pass']:
            result.append('oracle_mismatch')
        if not payload['target_reached']:
            result.append('required_target_not_observed')
    return result


def _evidence(directory):
    return [_binding(p) for p in sorted(directory.rglob('*')) if p.is_file() and not p.is_symlink()
            and p.suffix not in ('.class', '.jar')
            and not any(parent.is_symlink() for parent in p.parents)]


def _subprocess(directory):
    request = _read(directory / 'request.json')
    process = _read(directory / 'process.json')
    payload = process.get('payload') or {}
    payload = payload if isinstance(payload, dict) else {}
    kind = 'provider' if 'system' in request and 'prompt' in request else 'checker'
    audit = directory / 'provider_audit'
    provider = _read(audit / 'result.json') or _read(audit / 'response.json') or payload
    failure = _read(audit / 'failure.json')
    reservation, settings = _read(audit / 'reservation.json'), _read(audit / 'settings.json')
    invocation = _read(directory / 'invocation.json')
    rejected = _read(directory / 'rejected.json')
    categories = _categories(kind, process, provider if kind == 'provider' else payload, directory)
    if failure.get('failure', {}).get('type'):
        categories.append('provider_' + failure['failure']['type'])
    if rejected.get('status'):
        categories.append(rejected['status'])
    return {'kind': kind, **_identity(directory, request), 'directory': str(directory),
            'process_status': process.get('status', 'in_progress_or_interrupted'),
            'returncode': process.get('returncode'), 'started_at': process.get('started_at', invocation.get('started_at')),
            'finished_at': process.get('finished_at'), 'seconds': process.get('seconds'),
            'response_status': provider.get('response_status') if kind == 'provider' else None,
            'response_id': provider.get('response_id') if kind == 'provider' else None,
            'model': provider.get('model_version', request.get('model')),
            'tokens': _tokens(provider) if kind == 'provider' else None,
            'budget': provider.get('budget') if kind == 'provider' else None,
            'reservation_id': (provider.get('budget') or {}).get('reservation_id', reservation.get('reservation_id')),
            'budget_ledger': settings.get('budget_ledger'),
            'error_categories': categories, 'error_type': process.get('error_type'),
            'diagnostic_tags': _diagnostics(directory) if kind == 'checker' else [],
            'verdict': {key: payload.get(key) for key in ('execution_pass', 'oracle_pass', 'target_reached')} if kind == 'checker' else None,
            'evidence': _evidence(directory)}


def _native(directory, entry):
    result = _read(directory / 'result.json') or _read(directory / 'response.json')
    outcome = _read(directory / 'outcome.json')
    request = _read(directory / 'request.json')
    failure = _read(directory / 'failure.json')
    reservation, settings = _read(directory / 'reservation.json'), _read(directory / 'settings.json')
    status = outcome.get('status', 'in_progress_or_interrupted')
    categories = _categories('provider', {'status': 'completed' if status == 'completed' else status}, result, directory)
    if result and status != 'completed':
        categories += _categories('provider', {'status': 'completed'}, result, directory)
    if failure.get('failure', {}).get('type'):
        categories.append('provider_' + failure['failure']['type'])
    return {'kind': 'provider', 'phase': request.get('native_context', {}).get('stage'),
            **entry, 'directory': str(directory), 'process_status': status,
            'started_at': outcome.get('started_at', result.get('started_at')),
            'finished_at': outcome.get('finished_at', result.get('finished_at')),
            'seconds': outcome.get('seconds', result.get('seconds')),
            'response_status': result.get('response_status'), 'response_id': result.get('response_id'),
            'model': result.get('model_version', request.get('model')), 'tokens': _tokens(result),
            'budget': result.get('budget'), 'error_categories': categories,
            'reservation_id': (result.get('budget') or {}).get('reservation_id', reservation.get('reservation_id')),
            'budget_ledger': settings.get('budget_ledger'),
            'error_type': outcome.get('error_type'), 'evidence': _evidence(directory)}


def collect_telemetry(root):
    """Read saved evidence only. Unknown usage/time stays null, never fabricated."""
    root = Path(root).resolve(strict=True)
    paths = list(_files(root))
    entries, tasks, errors = {}, [], []
    for path in paths:
        if path.name == 'prepared.json' and path.parent.name.startswith('entry_'):
            try:
                prepared = _read(path)
                for phase in prepared.get('phases', {}):
                    state_path = path.parent / (phase + '.state.json')
                    state = _read(state_path)
                    call = (state.get('provider_evidence') or {}).get('call_directory') or state.get('provider_call_directory')
                    context = {'entry_id': prepared.get('id'), 'entry_phase': phase,
                               'state_status': state.get('status', 'not_started'),
                               'state_evidence': _binding(state_path) if state_path.is_file() else None}
                    if call:
                        entries[str(Path(call).resolve())] = context
                    tasks.append({'kind': 'readme_phase', **context, 'directory': str(path.parent),
                                  'started_at': state.get('started_at'), 'finished_at': state.get('finished_at'),
                                  'seconds': state.get('seconds'), 'provider_call_directory': call})
            except (ValueError, OSError, TypeError) as exc:
                errors.append({'path': str(path), 'error_type': type(exc).__name__})
    attempts = []
    directories = sorted({p.parent for p in paths if p.name == 'request.json'
                          and (p.parent.name.startswith(('provider_', 'attempt_', 'execution_'))
                               or p.parent.name == 'model_attempt') and p.parent.name != 'provider_audit'})
    for directory in directories:
        try:
            attempts.append(_subprocess(directory))
        except (ValueError, OSError, TypeError) as exc:
            errors.append({'path': str(directory), 'error_type': type(exc).__name__})
    native = sorted({p.parent for p in paths if p.name == 'request.json' and p.parent.name.startswith('call-')})
    for directory in native:
        try:
            attempts.append(_native(directory, entries.get(str(directory), {})))
        except (ValueError, OSError, TypeError) as exc:
            errors.append({'path': str(directory), 'error_type': type(exc).__name__})
    for path in paths:
        if path.name == 'result.json' and '--' in path.parent.name:
            try:
                row = _read(path)
            except (ValueError, OSError) as exc:
                errors.append({'path': str(path), 'error_type': type(exc).__name__})
                continue
            tasks.append({key: row.get(key) for key in ('arm', 'case_id', 'trial_id', 'status',
                          'first_attempt_pass', 'first_pass_round', 'last_checked_round')} |
                         {'kind': 'audience_unit', 'evidence': _binding(path)})
    providers = [a for a in attempts if a['kind'] == 'provider']
    totals = {key: {'reported_sum': sum(a['tokens'][key] or 0 for a in providers),
                    'calls_without_value': sum(a['tokens'][key] is None for a in providers)} for key in TOKEN_KEYS}
    return {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(), 'root': str(root),
            'scope': 'Local private evidence index. Links may expose checker/private fixture outputs; do not publish wholesale.',
            'limits': ['Read-only derived index, not new evaluation or accounting evidence.',
                       'Provider attempts are distinct from fix_round; retries do not add repair rounds.',
                       'Output tokens already include reasoning; non-reasoning may include formatting tokens.',
                       'Unknown historical timestamps/usage stay null; error categories are descriptive, not score changes.',
                       'Diagnostic tags are literal heuristic matches with evidence/line numbers, not verified root causes or model grading.',
                       'This is a live snapshot; writing evidence may be partial. Rerun after the worker stops.'],
            'tasks': tasks, 'attempts': attempts, 'provider_attempts': len(providers),
            'reported_tokens': totals, 'scan_errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True, help='New JSON snapshot; existing reports are preserved')
    args = parser.parse_args()
    result = collect_telemetry(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output': str(output.resolve()), 'attempts': len(result['attempts']),
                      'tasks': len(result['tasks']), 'scan_errors': result['scan_errors']}))


if __name__ == '__main__':
    main()
