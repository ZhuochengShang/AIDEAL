"""Request candidate programs for evaluation and record their outcomes.

The selected README provides context for the model request. README authoring
is implemented in the vendored engine's readme_generation.py.
"""
import re

from .ablation import bind, digest, load
from .execution import atomic_json, invoke, next_directory
from .response_status import solution_state


GENERATION_STATUSES = frozenset('generation_' + status for status in
                                ('incomplete', 'refusal', 'empty', 'provider_failure'))
STOPPED_STATUSES = frozenset(('pass', 'fail')) | GENERATION_STATUSES


def verify_checkpoint_extension(saved, current):
    """Permit new attempts after an unresolved checkpoint, never changed history.

    Each previously recorded attempt includes immutable file bindings. A retry
    uses a new numbered directory, so even adding files to an old attempt is not
    a valid extension. Callers must also replay both snapshots against the frozen
    requests and enforce that only unresolved results may have an extension.
    """
    # Compare saved and current rounds in order. An existing attempt list must remain
    # an exact prefix of its current list.
    if len(current) < len(saved):
        raise ValueError('Saved condition attempt evidence changed')
    for old, new in zip(saved, current):
        if set(new) - set(old) - {'generation'}:
            raise ValueError('Saved condition attempt evidence changed')
        for key, value in old.items():
            actual = new.get(key)
            if key in ('providers', 'executions') and isinstance(actual, list):
                actual = actual[:len(value)]
            if actual != value:
                raise ValueError('Saved condition attempt evidence changed')


def model_request(frozen, prompt, round_number):
    """Build the exact public provider request used by execution and replay."""
    # Round zero uses the base output limit. Later rounds use the configured repair
    # limit when one was supplied.
    config = frozen['config']
    common = config['common']
    limit = common['max_output_tokens']
    if round_number:
        limit = common.get('repair_max_output_tokens', limit)
    return {'system': frozen['system_prompt'], 'prompt': prompt, 'model': config['model']['name'],
            'temperature': common['temperature'], 'max_output_tokens': limit}


def _request_solution(cfg, request, root, retry_provider):
    # Request a candidate program using the prompt already built for this round.
    # Reuse a compatible saved response, or call the adapter in numbered attempts.
    # Save generation evidence and return the response, including stopped outputs;
    # return None if no response is obtained within the transport-attempt allowance.
    """Reuse any model outcome; only transport failures consume retry allowance."""
    common = cfg['common']
    providers = attempts(root, 'provider_')
    selected = selected_response(providers, request)
    if selected is not None:
        response, files = selected
        save_generation(root, response, files)
        return response
    if (root / 'generation.json').exists():
        raise ValueError('Saved generation evidence lacks a provider response')
    attempted = len(providers)
    # Count existing attempts against the configured limit. An explicit
    # provider retry grants one more allowance after the saved attempts.
    limit = common['provider_attempt_limit'] + (attempted if retry_provider else 0)
    for _ in range(attempted, limit):
        destination = next_directory(root, 'provider_')
        result = invoke(cfg['model']['command'], request, destination, common['provider_timeout_s'])
        response = model_response(result)
        if response is not None:
            save_generation(root, response, {'request.json': bind(destination / 'request.json'),
                                            'process.json': bind(destination / 'process.json')})
            return response
    return None


def model_response(result):
    # Extract a provider payload only when the adapter completed and supplied a string
    # code field. Completion classification follows separately.
    payload = result.get('payload')
    if result.get('status') == 'ok' and isinstance(payload, dict) and isinstance(payload.get('code'), str):
        return payload
    return None


def attempts(root, prefix):
    # Collect file references from the numbered provider or execution folders.
    # Interrupted attempts can have only some of the four files.
    records = []
    for directory in sorted(root.glob(prefix + '*')):
        if not directory.is_dir() or re.fullmatch(re.escape(prefix) + r'\d{3,}', directory.name) is None:
            raise ValueError('Unexpected condition attempt directory')
        records.append({'directory': str(directory), 'files': {
            name: bind(directory / name) for name in ('request.json', 'process.json', 'stdout.txt', 'stderr.txt')
            if (directory / name).exists()}})
    return records


def rounds(directory, exposure=False):
    # Return one evidence record per round, with provider calls, checker calls and any
    # applicable receipts. Sort by the numeric round index.
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
    # Replay the recorded attempts against the expected request and return the first
    # usable response with its files, or None.
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
    # Pair the completion decision with a fingerprint of the full response and the
    # exact provider request and process references.
    return {'schema_version': 1, **solution_state(response),
            'response_sha256': digest(response),
            'provider': {name: files[name] for name in ('request.json', 'process.json')}}


def save_generation(root, response, files):
    # Store the completion receipt in this round. If a receipt already exists, it must
    # agree with the selected response.
    record = generation_record(response, files)
    path = root / 'generation.json'
    if path.exists() and load(path) != record:
        raise ValueError('Saved generation evidence differs from the selected provider response')
    atomic_json(path, record)
    return record


def verify_generation(item, response, files):
    # Recompute the receipt from provider evidence and compare it with the stored
    # JSON. Return the expected record if they agree.
    expected = generation_record(response, files)
    receipt = item.get('generation')
    if not receipt or load(receipt['path']) != expected:
        raise ValueError('Saved generation evidence differs from the selected provider response')
    return expected


def mark_generation(row, response, number):
    # Update the result row with this round's completion status and return whether the
    # checker may execute the response.
    state = solution_state(response)
    row.update(generation_status=state['status'], generation_reason=state['reason'], last_generation_round=number)
    if not state['executable']:
        row['status'] = 'generation_' + state['status']
    return state['executable']


def generation_counts(rows, arms):
    # Count only generation stop states for each arm. The report keeps those counts
    # distinct from checker passes and failures.
    return {arm: {status: sum(row.get('status') == status for row in rows if row['arm'] == arm)
                  for status in sorted(GENERATION_STATUSES)} for arm in arms}
