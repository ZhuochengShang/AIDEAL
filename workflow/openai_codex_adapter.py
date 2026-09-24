"""One low-reasoning Codex Responses call guarded by an explicit shared ledger."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time

if __package__:
    from .provider_budget import BudgetLedger, MODEL, digest
    from .response_status import classify_record
else:
    from provider_budget import BudgetLedger, MODEL, digest
    from response_status import classify_record


def response_record(response):
    messages, refusals = [], []
    for item in response.output or []:
        if getattr(item, 'type', None) != 'message' or getattr(item, 'role', None) != 'assistant':
            continue
        text = ''.join(part.text for part in item.content if part.type == 'output_text')
        refusals.extend(part.refusal for part in item.content if part.type == 'refusal')
        messages.append({'id': item.id, 'phase': getattr(item, 'phase', None),
                         'status': item.status, 'text': text})
    final = [item for item in messages if item['phase'] == 'final_answer']
    selected = final if final else [item for item in messages if item['phase'] is None]
    code = ''.join(item['text'] for item in selected)
    status = response.status
    reason = getattr(response.incomplete_details, 'reason', None)
    record = {'code': code, 'model_version': response.model, 'response_id': response.id,
              'response_status': status, 'incomplete_reason': reason,
              'truncated': reason == 'max_output_tokens', 'refusals': refusals,
              'completion_metadata_expected': True,
              'messages': messages, 'error_code': getattr(response.error, 'code', None)}
    usage = response.usage
    if usage is not None:
        reasoning = getattr(usage.output_tokens_details, 'reasoning_tokens', None)
        record['usage'] = {'input_tokens': usage.input_tokens, 'output_tokens': usage.output_tokens,
                           'reasoning_tokens': reasoning,
                           'non_reasoning_output_tokens': usage.output_tokens - reasoning if type(reasoning) is int else None,
                           'cached_input_tokens': getattr(usage.input_tokens_details, 'cached_tokens', None),
                           'total_tokens': usage.total_tokens}
    return classify_record(record)


def _failure(exc):
    """Never persist raw SDK error bodies, URLs, headers, or exception messages."""
    code = getattr(exc, 'code', None)
    request_id = getattr(exc, 'request_id', None)
    status = getattr(exc, 'status_code', None)
    return {'type': type(exc).__name__,
            'status_code': status if type(status) is int and 100 <= status <= 599 else None,
            'code': code if isinstance(code, str) and re.fullmatch(r'[a-z_]{1,64}', code) else None,
            'request_id': request_id if isinstance(request_id, str) and re.fullmatch(r'req_[a-zA-Z0-9]{1,128}', request_id) else None}


def invoke(request, ledger, *, audit=None):
    """Shared CLI/native transport. Audit settings and reservation before HTTP.

    The optional callback receives only normalized, secret-free records. Caller
    persistence errors fail closed; provider errors retain uncertain reservations.
    """
    emit = audit or (lambda event, value: None)
    started_at, started = datetime.now(timezone.utc).isoformat(), time.monotonic()
    if request['model'] != MODEL:
        raise ValueError('This adapter requires model gpt-5.3-codex')
    if not all(isinstance(request[key], str) for key in ('system', 'prompt')):
        raise ValueError('system and prompt must be strings')
    cap = request['max_output_tokens']
    if type(cap) is not int or not 0 < cap <= 128000:
        raise ValueError('max_output_tokens must be an integer from 1 to 128000')
    temperature = request['temperature']
    if type(temperature) not in (int, float) or not math.isfinite(temperature):
        raise ValueError('Requested temperature must be a finite number')
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('Set OPENAI_API_KEY in the launching environment')
    import openai  # Optional SDK; --help and module inspection stay offline.

    parameters = {'model': MODEL, 'reasoning': {'effort': 'low'}, 'max_output_tokens': cap,
                  'store': False, 'tools': [], 'tool_choice': 'none', 'service_tier': 'default',
                  'background': False, 'stream': False, 'truncation': 'disabled'}
    settings = {'endpoint': 'https://api.openai.com/v1', 'api': 'responses', 'timeout_s': 120,
                'max_retries': 0, 'sdk_version': openai.__version__, 'parameters': parameters,
                'requested_temperature': temperature, 'temperature_sent': False,
                'effective_temperature': 'provider_default_not_explicitly_set',
                'instructions_sha256': digest(request['system']), 'input_sha256': digest(request['prompt']),
                'budget_ledger': str(ledger.path), 'max_cost_nanousd': ledger.identity['max_cost_nanousd']}
    if ledger.identity['schema_version'] == 2:
        settings['budget_policy_identity'] = ledger.identity
    request_hash, settings_hash = digest(request), digest(settings)
    reservation = None
    try:
        emit('settings', settings)
        with openai.OpenAI(api_key=key, base_url=settings['endpoint'], max_retries=0, timeout=120.0) as client:
            reservation = ledger.reserve(request['system'], request['prompt'], cap, request_hash, settings_hash)
            emit('reservation', {'reservation_id': reservation, 'request_sha256': request_hash,
                                 'settings_sha256': settings_hash})
            response = client.responses.create(instructions=request['system'], input=request['prompt'], **parameters)
        record = response_record(response)
    except Exception as exc:
        failure = _failure(exc)
        if reservation is not None:
            try:
                ledger.finish(reservation, failure=failure)
            except Exception as ledger_error:
                failure['ledger_error_type'] = type(ledger_error).__name__
        emit('failure', {'failure': failure, 'reservation_id': reservation,
                         'request_sha256': request_hash, 'settings_sha256': settings_hash,
                         'started_at': started_at, 'finished_at': datetime.now(timezone.utc).isoformat(),
                         'seconds': time.monotonic() - started})
        raise RuntimeError('Codex request failed: ' + json.dumps(failure)) from None
    emit('response', record)
    receipt = ledger.finish(reservation, usage=record.get('usage'), response_id=record['response_id'],
                            status=record['response_status'])
    record.update(adapter_settings=settings, adapter_settings_sha256=settings_hash,
                  request_sha256=request_hash, budget=receipt,
                  started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat(),
                  seconds=time.monotonic() - started)
    emit('result', record)
    # Returned non-final responses remain auditable evidence. The caller checks
    # solution_state before execution, without silently retrying a paid request.
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--budget-ledger', required=True,
                        help='Use --budget-ledger=/absolute/path so controllers do not hash this mutable file')
    parser.add_argument('--max-cost-usd', default='5', help='Immutable cap: legacy-v1 <=$5; explicit study-v2 <=$100')
    parser.add_argument('--budget-policy', choices=('legacy-v1', 'study-v2'), default='legacy-v1')
    parser.add_argument('--study-id', help='Required immutable identity for a new study-v2 ledger')
    parser.add_argument('--audit-directory', default='provider_audit',
                        help='New local evidence directory; default is inside this adapter attempt')
    args = parser.parse_args(argv)
    request = json.load(sys.stdin)
    ledger = BudgetLedger(args.budget_ledger, args.max_cost_usd, policy=args.budget_policy, study_id=args.study_id)
    evidence = Path(args.audit_directory)
    evidence.mkdir(parents=True, exist_ok=False)
    def audit(event, value):
        # Same secret-free events used by the native bridge, including failed calls.
        with (evidence / (event + '.json')).open('x') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
    audit('request', request)
    record = invoke(request, ledger, audit=audit)
    print(json.dumps(record, allow_nan=False))


if __name__ == '__main__':
    main()
