"""Execute explicitly prepared, guarded README sessions in isolated outputs."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import subprocess
import uuid

from .readme_authoring import REPORT_MARKER, digest, engine_imports
from .readme_spans import candidate_bytes, compose
from .readme_receipts import invoke_recorded, verify_provider_evidence
from .preparation import _engine_config_module


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())


@contextmanager
def session_lock(directory):
    with (directory / '.session.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def load_verified(directory):
    """Fail before any provider call if input, output or provider policy changed."""
    session = json.loads((directory / 'session.json').read_text())
    if session['identity_sha256'] != digest({k: v for k, v in session.items() if k != 'identity_sha256'}):
        raise ValueError('Prepared session identity changed')
    if digest(session['requests']) != session['requests_sha256']:
        raise ValueError('Prepared requests changed')
    if digest((directory / 'base.md').read_bytes()) != session['base_sha256']:
        raise ValueError('Immutable base snapshot changed')
    for item in session['inputs']:
        path = Path(item['path'])
        if not path.is_file() or digest(path.read_bytes()) != item['sha256']:
            raise ValueError('Session input changed: ' + str(path))
    manifest = session['manifest']
    head = subprocess.check_output(['git', '-C', manifest['repository'], 'rev-parse', 'HEAD']).decode().strip()
    if head != manifest['revision']:
        raise ValueError('Pinned repository HEAD changed')
    cfg = _engine_config_module().load_config(session['config_path'])
    if cfg.raw != session['effective_config']:
        raise ValueError('Effective layered configuration changed')
    from .native_provider_bridge import guarded_native_contract
    specs = {role: cfg.model_for_role(role) for role in session['provider_contracts']}
    for role, spec in specs.items():
        if guarded_native_contract(spec) != session['provider_contracts'][role]:
            raise ValueError('Guarded native provider contract changed')
    for index, request in enumerate(session['requests']):
        entry = directory / f'entry_{index:04d}'
        if json.loads((entry / 'prepared.json').read_text()) != request:
            raise ValueError('Prepared entry changed')
        for name in request['phases']:
            state_path = entry / (name + '.state.json')
            if not state_path.exists():
                continue
            state = json.loads(state_path.read_text())
            if state.get('status') != 'complete':
                raise ValueError('Prior incomplete/failed invocation requires explicit reconciliation')
            saved = json.loads((entry / (name + '.request.json')).read_text())
            if digest(saved) != state.get('request_sha256') or digest(state.get('text')) != state.get('text_sha256'):
                raise ValueError('Saved phase evidence changed')
            contract = session['provider_contracts'][request['phase_roles'][name]]
            verify_provider_evidence(state.get('provider_evidence'), state['text'], saved, contract)
        candidate = entry / 'candidate.md'
        final_name = 'entry' if session['mode'] == 'full' else 'rewrite'
        final_state = entry / (final_name + '.state.json')
        if candidate.exists():
            if not final_state.exists() or candidate.read_bytes() != candidate_bytes(json.loads(final_state.read_text())['text'], request['heading']):
                raise ValueError('Saved candidate changed')
    return session, specs


def phase(directory, name, request, invoke, contract):
    """One attempted invocation per phase; uncertain/failed calls never auto-repeat."""
    request_path, state_path = directory / (name + '.request.json'), directory / (name + '.state.json')
    expected = digest(request)
    if request_path.exists():
        if json.loads(request_path.read_text()) != request:
            raise ValueError('Saved exact request differs from bound phase')
    else:
        atomic_json(request_path, request)
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state.get('request_sha256') != expected:
            raise ValueError('Phase request identity changed')
        if state.get('status') != 'complete':
            raise ValueError('Phase has a prior incomplete/failed invocation; explicit reconciliation required')
        if digest(state['text']) != state.get('text_sha256'):
            raise ValueError('Saved phase response changed')
        verify_provider_evidence(state.get('provider_evidence'), state['text'], request, contract)
        return state['text']
    atomic_json(state_path, {'status': 'started', 'request_sha256': expected})
    try:
        result = invoke(request['system'], request['prompt'])
        text = result['text']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Provider returned no text')
        verify_provider_evidence(result.get('provider_evidence'), text, request, contract)
    except Exception as exc:
        atomic_json(state_path, {'status': 'failed_or_uncertain', 'request_sha256': expected,
                                 'error_type': type(exc).__name__})
        raise
    atomic_json(state_path, {'status': 'complete', 'request_sha256': expected,
                             'text': text, 'text_sha256': digest(text),
                             'provider_evidence': result['provider_evidence']})
    return text


def run_readme_session(directory, max_entries=None):
    """Generate candidates only. There is no execution-based acceptance claim.

    Existing complete phases resume by exact hashes. New refresh entries call
    fresh deep-dive then one rewrite. No legacy journals/caches are consulted.
    """
    directory = Path(directory).resolve()
    if max_entries is not None and (type(max_entries) is not int or max_entries < 1):
        raise ValueError('max_entries must be positive')
    with session_lock(directory):
        session, specs = load_verified(directory)
        engine_imports()
        from aideal.llm import invoke_text
        candidates = {}
        for index, prepared in enumerate(session['requests']):
            if max_entries is not None and index >= max_entries:
                break
            root = directory / f'entry_{index:04d}'
            def call_for(name):
                role = prepared['phase_roles'][name]
                return lambda system, prompt: invoke_recorded(invoke_text, specs[role], system, prompt,
                                                              session['provider_contracts'][role])
            def contract_for(name):
                return session['provider_contracts'][prepared['phase_roles'][name]]
            if session['mode'] == 'refresh':
                report = phase(root, 'deep_dive', prepared['phases']['deep_dive'], call_for('deep_dive'), contract_for('deep_dive'))
                load_verified(directory)  # Recheck bindings after any paid phase.
                template = prepared['phases']['rewrite']
                request = {k: v.replace(REPORT_MARKER, report) for k, v in template.items()}
                # The exact rendered request carries the input report identity.
                request['deep_dive_sha256'] = digest(report)
                text = phase(root, 'rewrite', request, call_for('rewrite'), contract_for('rewrite'))
            else:
                text = phase(root, 'entry', prepared['phases']['entry'], call_for('entry'), contract_for('entry'))
            load_verified(directory)
            candidate = candidate_bytes(text, prepared['heading'])
            path = root / 'candidate.md'
            if path.exists() and path.read_bytes() != candidate:
                raise ValueError('Saved candidate changed')
            atomic_bytes(path, candidate)
            candidates[prepared['id']] = text
        if len(candidates) != len(session['requests']):
            return {'status': 'partial_candidates', 'completed_entries': len(candidates),
                    'total_entries': len(session['requests']), 'output': None}
        base = (directory / 'base.md').read_bytes()
        output = compose(base, session['manifest']['entries'], candidates)
        path = directory / 'README.md'
        if path.exists() and path.read_bytes() != output:
            raise ValueError('Existing composed output changed')
        atomic_bytes(path, output)
        result = {'status': 'authored_not_execution_validated', 'identity_sha256': session['identity_sha256'],
                  'output': str(path), 'output_sha256': digest(output), 'base_sha256': session['base_sha256'],
                  'candidate_sha256': {key: digest(candidate_bytes(text, next(e['heading'] for e in session['manifest']['entries'] if e['id'] == key)))
                                       for key, text in candidates.items()},
                  'completed_entries': len(candidates), 'cache_policy': session['cache_policy'],
                  'validation_status': 'not_executed', 'legacy_deep_dive_reused': False}
        completion = directory / 'completion.json'
        if completion.exists() and json.loads(completion.read_text()) != result:
            raise ValueError('Completion receipt changed')
        atomic_json(completion, result)
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True)
    parser.add_argument('--max-entries', type=int)
    args = parser.parse_args()
    print(json.dumps(run_readme_session(args.session, args.max_entries), indent=2))
