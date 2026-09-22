"""Bind native text results to independently saved provider and budget evidence."""
import fcntl
from decimal import Decimal
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from .provider_budget import BudgetLedger, digest

FILES = ('contract.json', 'request.json', 'settings.json', 'reservation.json',
         'response.json', 'result.json', 'outcome.json')
TIMING = ('started_at', 'finished_at', 'seconds')


def _without_timing(record):
    """Timing is bound by receipt hashes; legacy receipts may lack all three fields."""
    if any(key in record for key in TIMING):
        start, end = (datetime.fromisoformat(record[key]) for key in TIMING[:2])
        seconds = record['seconds']
        if (start.tzinfo is None or end.tzinfo is None
                or type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0):
            raise ValueError('Invalid provider receipt timing')
    return {key: value for key, value in record.items() if key not in TIMING}


def _read(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('Missing or redirected provider evidence: ' + str(path))
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def _provider_request(request, contract):
    return {'model': contract['model'], 'system': request['system'], 'prompt': request['prompt'],
            'max_output_tokens': contract['max_output_tokens'], 'temperature': 0,
            'native_context': {'stage': contract['stage'], 'contract_sha256': contract['identity_sha256']}}


def _ledger_binding(contract, result):
    """Read one settled row under the existing lock; never mutate the ledger."""
    path = Path(contract['budget_ledger'])
    lock_path = Path(str(path) + '.lock')
    if any(p.is_symlink() for p in (lock_path, *lock_path.parents)):
        raise ValueError('Redirected budget lock')
    with lock_path.open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        ledger, _ = _read(path)
        identity = contract['budget_identity']
        policy = BudgetLedger(path, str(Decimal(identity['max_cost_nanousd']) / 1_000_000_000),
                              policy=identity['policy'], study_id=identity['study_id'])
        if policy.identity != identity:
            raise ValueError('Budget contract identity differs')
        policy._validate(ledger, lock.read().strip())
        rows = [row for row in ledger['records'] if row['id'] == result['budget']['reservation_id']]
        if len(rows) != 1:
            raise ValueError('Provider reservation is absent from its ledger')
        row = rows[0]
        expected = {'state': 'settled', 'request_sha256': result['request_sha256'],
                    'settings_sha256': result['adapter_settings_sha256'], 'usage': result['usage'],
                    'response_id': result['response_id'], 'response_status': 'completed',
                    'reserved_nanousd': result['budget']['reserved_nanousd'],
                    'charged_nanousd': result['budget']['charged_nanousd']}
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError('Provider result differs from settled budget evidence')
        return {'path': str(path), 'ledger_id': ledger['ledger_id'], 'reservation_id': row['id'],
                'record_sha256': digest(row)}


def receipt_binding(call_dir, text, request, contract):
    """Validate cross-file identities and bind every original receipt byte."""
    root = Path(contract['evidence_dir'])
    call_dir = Path(call_dir)
    if call_dir.parent != root or not call_dir.name.startswith('call-'):
        raise ValueError('Provider receipt is outside its bound stage')
    stage, stage_hash = _read(root / 'contract.json')
    records, hashes = {}, {}
    for name in FILES:
        records[name], hashes[name] = _read(call_dir / name)
    if stage != contract or records['contract.json'] != contract:
        raise ValueError('Provider evidence contract changed')
    expected = _provider_request(request, contract)
    result, settings = records['result.json'], records['settings.json']
    request_hash, settings_hash = digest(expected), digest(settings)
    if records['request.json'] != expected or result.get('request_sha256') != request_hash:
        raise ValueError('Provider evidence request changed')
    if (result.get('adapter_settings') != settings or result.get('adapter_settings_sha256') != settings_hash
            or settings.get('instructions_sha256') != digest(request['system'])
            or settings.get('input_sha256') != digest(request['prompt'])
            or settings.get('budget_policy_identity') != contract['budget_identity']
            or settings.get('budget_ledger') != contract['budget_ledger']):
        raise ValueError('Provider evidence settings changed')
    response = {key: value for key, value in _without_timing(result).items()
                if key not in ('adapter_settings', 'adapter_settings_sha256', 'request_sha256', 'budget')}
    if records['response.json'] != response or _without_timing(records['outcome.json']) != {
            'status': 'completed', 'request_sha256': request_hash, 'result_sha256': digest(result)}:
        raise ValueError('Provider outcome or response differs from its result')
    if (result.get('code') != text or not isinstance(text, str) or not text.strip()
            or result.get('response_status') != 'completed' or result.get('response_kind') != 'solution'
            or result.get('refusals') or result.get('truncated') or result['budget'].get('state') != 'settled'):
        raise ValueError('Saved phase text differs from complete provider evidence')
    if records['reservation.json'] != {'reservation_id': result['budget']['reservation_id'],
            'request_sha256': request_hash, 'settings_sha256': settings_hash}:
        raise ValueError('Provider reservation evidence changed')
    return {'schema_version': 1, 'call_directory': str(call_dir), 'file_sha256': hashes,
            'stage_contract_sha256': stage_hash, 'ledger': _ledger_binding(contract, result)}


def verify_provider_evidence(binding, text, request, contract):
    if not isinstance(binding, dict) or receipt_binding(binding['call_directory'], text, request, contract) != binding:
        raise ValueError('Saved provider receipt binding changed')


def invoke_recorded(invoke, spec, system, prompt, contract):
    """Invoke native text once, then require one matching newly saved receipt.

    The bridge owns unique call directories. Concurrent unrelated calls are
    ignored; multiple identical new requests fail closed instead of guessing.
    """
    root = Path(contract['evidence_dir'])
    previous = set(root.glob('call-*'))
    text = invoke(spec, system, prompt)
    request = {'system': system, 'prompt': prompt}
    expected = _provider_request(request, contract)
    matches = []
    for directory in set(root.glob('call-*')) - previous:
        if (directory / 'request.json').is_file():
            saved, _ = _read(directory / 'request.json')
            if saved == expected:
                matches.append(directory)
    if len(matches) != 1:
        raise ValueError('Native result has no unique newly saved provider receipt')
    return {'text': text, 'provider_evidence': receipt_binding(matches[0], text, request, contract)}
