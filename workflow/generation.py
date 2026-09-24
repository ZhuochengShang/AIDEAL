"""Auditable generation outcomes, separate from executable program outcomes."""
from pathlib import Path
import re

from .ablation import bind, digest, load
from .execution import atomic_json
from .response_status import solution_state


GENERATION_STATUSES = frozenset('generation_' + status for status in
                                ('incomplete', 'refusal', 'empty', 'provider_failure'))
STOPPED_STATUSES = frozenset(('pass', 'fail')) | GENERATION_STATUSES


def output_limit(common, round_number):
    return common.get('repair_max_output_tokens', common['max_output_tokens']) if round_number else common['max_output_tokens']


def model_response(result):
    payload = result.get('payload')
    if result.get('status') == 'ok' and isinstance(payload, dict) and isinstance(payload.get('code'), str):
        return payload
    return None


def attempts(root, prefix):
    records = []
    for directory in sorted(root.glob(prefix + '*')):
        if not directory.is_dir() or re.fullmatch(re.escape(prefix) + r'\d{3,}', directory.name) is None:
            raise ValueError('Unexpected condition attempt directory')
        records.append({'directory': str(directory), 'files': {
            name: bind(directory / name) for name in (
                'request.json', 'process.json', 'stdout.txt', 'stderr.txt', 'invocation.json',
                *(p.relative_to(directory).as_posix()
                  for p in sorted((directory / 'provider_audit').glob('*.json'))))
            if (directory / name).exists()}})
    return records


def rounds(directory, exposure=False):
    records = []
    for root in sorted(directory.glob('round_*')):
        if not root.is_dir() or re.fullmatch(r'round_\d{2,}', root.name) is None:
            raise ValueError('Unexpected condition round directory')
        record = {'round': int(root.name.removeprefix('round_')),
                  'providers': attempts(root, 'provider_'), 'executions': attempts(root, 'execution_')}
        if exposure:
            record['exposure'] = bind(root / 'context_exposure.json')
        if (root / 'repair_context.json').exists():
            record['repair_context'] = bind(root / 'repair_context.json')
        if (root / 'generation.json').exists():
            record['generation'] = bind(root / 'generation.json')
        records.append(record)
    return sorted(records, key=lambda record: record['round'])


def selected_response(providers, request):
    """Validate every request, including interrupted attempts; select once only."""
    selected = None
    for attempt in providers:
        files = attempt['files']
        if 'request.json' in files and load(files['request.json']['path']) != request:
            raise ValueError('Saved provider request differs from the frozen public prompt')
        if 'process.json' in files:
            if 'request.json' not in files:
                raise ValueError('Saved provider process lacks its request')
            response = model_response(load(files['process.json']['path']))
            if selected is not None:
                raise ValueError('Saved provider attempt follows an already returned response')
            if response is not None:
                selected = (response, files)
        elif selected is not None:
            raise ValueError('Saved provider attempt follows an already returned response')
    return selected


def generation_record(response, files):
    return {'schema_version': 1, **solution_state(response),
            'response_sha256': digest(response),
            'provider': {name: files[name] for name in ('request.json', 'process.json')}}


def save_generation(root, response, files):
    record = generation_record(response, files)
    path = root / 'generation.json'
    if path.exists() and load(path) != record:
        raise ValueError('Saved generation evidence differs from the selected provider response')
    atomic_json(path, record)
    return record


def verify_generation(item, response, files):
    expected = generation_record(response, files)
    receipt = item.get('generation')
    if not receipt or load(receipt['path']) != expected:
        raise ValueError('Saved generation evidence differs from the selected provider response')
    return expected


def mark_generation(row, response, number):
    state = solution_state(response)
    row.update(generation_status=state['status'], generation_reason=state['reason'], last_generation_round=number)
    if not state['executable']:
        row['status'] = 'generation_' + state['status']
    return state['executable']


def generation_counts(rows, arms):
    return {arm: {status: sum(row.get('status') == status for row in rows if row['arm'] == arm)
                  for status in sorted(GENERATION_STATUSES)} for arm in arms}
