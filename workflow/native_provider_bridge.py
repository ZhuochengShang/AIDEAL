"""Explicit audited native text route through the shared budgeted Codex adapter."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

from . import openai_codex_adapter
from .provider_budget import BudgetLedger, MODEL, digest

PROVIDER = 'aideal-codex-audited'
CONTROLLER_FILES = ('workflow/provider_budget.py', 'workflow/openai_codex_adapter.py',
                    'workflow/response_status.py',
                    'workflow/native_provider_bridge.py', 'vendor/aideal_engine/src/aideal/llm.py',
                    'vendor/aideal_engine/src/aideal/config.py')
FIELDS = {'policy', 'study_id', 'stage', 'budget_ledger', 'max_cost_usd',
          'max_output_tokens', 'evidence_dir', 'controller_sha256'}


class NativeBridgeError(RuntimeError):
    """The audited route failed; callers must not substitute another provider."""


def active_controller_hashes():
    root = Path(__file__).resolve().parent.parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in CONTROLLER_FILES}


def _path(value, label):
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise NativeBridgeError(label + ' must be an explicit absolute path')
    path = Path(value)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise NativeBridgeError(label + ' must not traverse a symlink')
    return path.resolve()


def guarded_native_contract(spec):
    """Read-only policy/implementation validation for preparation and session pins."""
    if spec.provider != PROVIDER or spec.model != MODEL:
        raise NativeBridgeError('Native audited provider and gpt-5.3-codex must be explicitly selected')
    config = getattr(spec, 'bridge', None)
    if not isinstance(config, dict) or set(config) != FIELDS:
        raise NativeBridgeError('Native bridge requires exactly its documented configuration fields')
    if config['policy'] != 'study-v2':
        raise NativeBridgeError('Native bridge requires a new explicit study-v2 budget')
    stage = config['stage']
    if not isinstance(stage, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,95}', stage):
        raise NativeBridgeError('Stage must be a stable nonempty label')
    cap = config['max_output_tokens']
    if type(cap) is not int or not 0 < cap <= 128000:
        raise NativeBridgeError('max_output_tokens must be an integer from 1 to 128000')
    evidence = _path(config['evidence_dir'], 'evidence_dir')
    ledger_path = _path(config['budget_ledger'], 'budget_ledger')
    if ledger_path == evidence or evidence in ledger_path.parents:
        raise NativeBridgeError('Keep the shared mutable ledger outside the stage evidence directory')
    ledger = BudgetLedger(ledger_path, config['max_cost_usd'], policy=config['policy'], study_id=config['study_id'])
    actual = active_controller_hashes()
    if config['controller_sha256'] != actual:
        raise NativeBridgeError('Pinned native bridge implementation differs from the active installation')
    result = {'schema_version': 1, 'provider': PROVIDER, 'model': MODEL,
              'stage': stage, 'budget_ledger': str(ledger_path), 'budget_identity': ledger.identity,
              'max_output_tokens': cap, 'evidence_dir': str(evidence), 'controller_sha256': actual}
    return {**result, 'identity_sha256': digest(result)}


def _write(path, value):
    """Exclusive durable writes; a partial/crashed call is retained, never reused."""
    data = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    with path.open('xb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def invoke_native(spec, system, user):
    """Persist one exact request and route it through the shared adapter once."""
    contract = guarded_native_contract(spec)
    if not isinstance(system, str) or not isinstance(user, str):
        raise NativeBridgeError('Native prompts must be strings')
    root = Path(contract['evidence_dir'])
    root.mkdir(parents=True, exist_ok=True)
    marker = root / 'contract.json'
    try:
        _write(marker, contract)
    except FileExistsError:
        if marker.is_symlink() or json.loads(marker.read_text()) != contract:
            raise NativeBridgeError('Stage evidence directory belongs to a different immutable contract') from None
    call_dir = root / ('call-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex)
    call_dir.mkdir()
    started_at, started = datetime.now(timezone.utc).isoformat(), time.monotonic()
    request = {'model': MODEL, 'system': system, 'prompt': user,
               'max_output_tokens': contract['max_output_tokens'], 'temperature': 0,
               'native_context': {'stage': contract['stage'], 'contract_sha256': contract['identity_sha256']}}
    _write(call_dir / 'request.json', request)
    _write(call_dir / 'contract.json', contract)
    ledger = BudgetLedger(contract['budget_ledger'], spec.bridge['max_cost_usd'],
                          policy='study-v2', study_id=spec.bridge['study_id'])
    try:
        record = openai_codex_adapter.invoke(request, ledger,
            audit=lambda event, value: _write(call_dir / (event + '.json'), value))
        if (record['response_status'] != 'completed' or record['response_kind'] != 'solution'
                or not record['code'].strip() or record['refusals'] or record['truncated']
                or record['budget']['state'] != 'settled'):
            raise NativeBridgeError('Native authoring requires complete nonempty output with final accounted usage')
        # Detect source/config changes during the HTTP call before using its text.
        if guarded_native_contract(spec) != contract:
            raise NativeBridgeError('Native contract changed during the provider call')
        _write(call_dir / 'outcome.json', {'status': 'completed', 'request_sha256': digest(request),
                                         'result_sha256': digest(record), 'started_at': started_at,
                                         'finished_at': datetime.now(timezone.utc).isoformat(),
                                         'seconds': time.monotonic() - started})
        return record
    except Exception as exc:
        _write(call_dir / 'outcome.json', {'status': 'failed_closed', 'error_type': type(exc).__name__,
                                         'request_sha256': digest(request), 'started_at': started_at,
                                         'finished_at': datetime.now(timezone.utc).isoformat(),
                                         'seconds': time.monotonic() - started})
        error = NativeBridgeError(f'Native audited call failed ({type(exc).__name__}); evidence: {call_dir}')
        error.call_directory = str(call_dir)
        raise error from None
