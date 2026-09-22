"""Run a frozen three-README study one task/trial/condition at a time.

Read from top to bottom: build public prompts, select documentation, schedule
unfinished units, and execute bounded solution/repair attempts. Setup and report
formatting live in evaluation_setup.py and reporting.py.
"""
from pathlib import Path
import random
import re

from .ablation import digest, load, verify_artifact
from .execution import atomic_json, invoke, next_directory, ownership
from .evaluation_setup import (
    CONDITIONS, SYSTEM, adapter_request, verified_outcome,
    read_config, validate_bank, freeze_evaluation, open_frozen, assert_review_released,
    _checked_execution,
)
from .reporting import report, write_report

# Setup functions remain importable here for existing study launchers. They are
# imports, not second implementations; new callers may import evaluation_setup.

def audience_prompt(case, documentation, previous=None):
    """Build public model context; exclude oracle paths and reference answers."""
    sections = ['TASK\n' + case['prompt'], 'SHARED CONTRACT\n' + case.get('public_context', ''),
                'DOCUMENTATION\n' + documentation]
    if previous:
        sections += ['COMPLETE PREVIOUS SOLUTION\n' + previous['code'],
                     'EXECUTION FEEDBACK\n' + previous['feedback']]
    return '\n\n'.join(sections)


def select_documentation(paths, targets, max_characters):
    """Same deterministic heading retrieval for every condition; log actual exposure.

    Short documents are delivered in full. Long documents rank level-two sections
    by exact API-name mentions, with stable file order breaking ties. No LLM
    selects text, and no test answer enters retrieval.
    """
    text = '\n\n'.join(Path(p).read_text() for p in paths)
    chunks = re.split(r'(?m)(?=^## )', text)
    selected = []
    if len(text) <= max_characters:
        delivered = text
        selected = list(range(len(chunks)))
    else:
        def relevance(index):
            return sum(len(re.findall(r'(?<!\w)' + re.escape(t) + r'(?!\w)', chunks[index])) for t in targets)
        order = sorted(range(len(chunks)), key=lambda i: (-relevance(i), i))
        delivered = ''
        for i in order:
            remaining = max_characters - len(delivered)
            if remaining <= 2:
                break
            delivered += ('\n\n' if delivered else '') + chunks[i][:remaining - 2]
            selected.append(i)
    return delivered, {'source_characters': len(text), 'delivered_characters': len(delivered),
                       'selected_section_indices': selected, 'truncated': len(delivered) < len(text),
                       'delivered_sha256': digest(delivered)}


def run_evaluation(study, output, condition=None, max_units=None, retry_provider=False):
    """Resume matching unfinished units; preserve completed outcomes and all attempts."""
    assert_review_released(Path(study).resolve().parent)
    if max_units is not None and (type(max_units) is not int or max_units < 1):
        raise ValueError('max_units must be a positive integer')
    frozen = open_frozen(study)
    cfg, bank = frozen['config'], frozen['bank']
    common = cfg['common']
    if condition is not None and condition not in CONDITIONS:
        raise ValueError('Unknown documentation condition')
    output = Path(output).resolve()
    with ownership(output):
        identity = output / 'identity.json'
        if identity.exists() and load(identity)['study_sha256'] != frozen['study_sha256']:
            raise ValueError('This run directory belongs to another frozen study')
        atomic_json(identity, {'study_sha256': frozen['study_sha256']})
        rows = _load_completed_rows(output)
        report(frozen, list(rows.values()))  # Validate resumed rows before any model call.
        schedule = [(a, c, t) for a in CONDITIONS for c in bank['cases'] for t in common['trial_ids']]
        random.Random(common.get('ordering_seed', 42)).shuffle(schedule)
        processed = 0
        for arm, case, trial in schedule:
            key = (arm, case['id'], trial)
            if condition and arm != condition:
                continue
            if rows.get(key, {}).get('status') in ('pass', 'fail'):
                continue
            if max_units is not None and processed >= max_units:
                break
            # Verify treatments/runtime again before each unit, including resumed units.
            if not all(verify_artifact(r) for r in frozen['artifacts']):
                raise ValueError('Study inputs changed while running')
            directory = output / arm / f"{case['id']}--{trial}"
            directory.mkdir(parents=True, exist_ok=True)
            docs, exposure = select_documentation(cfg['documents'][arm], case['target_apis'],
                                                  common.get('documentation_max_characters', 32000))
            atomic_json(directory / 'documentation_exposure.json', exposure)
            row = _run_unit(frozen, arm, case, trial, docs, directory, retry_provider)
            atomic_json(directory / 'result.json', row)
            rows[key] = row
            summary = report(frozen, list(rows.values()))
            write_report(output, summary)
            print(f"{arm} | {case['id']} | {trial}: {row['status']}", flush=True)
            processed += 1
            # Do not burn the entire bank when transport or adapter infrastructure is broken.
            if row['status'] in ('provider_pending', 'unverified'):
                break
        summary = report(frozen, list(rows.values()))
        write_report(output, summary)
        return summary


def _run_unit(frozen, arm, case, trial, documentation, directory, retry_provider=False):
    cfg = frozen['config']
    common = cfg['common']
    row = {'arm': arm, 'case_id': case['id'], 'trial_id': trial, 'study_sha256': frozen['study_sha256'],
           'status': 'not_run', 'first_attempt_pass': False}
    previous = None
    for round_number in range(common['max_snippet_fixes'] + 1):
        root = directory / f'round_{round_number:02d}'
        request = {'system': frozen['system_prompt'], 'prompt': audience_prompt(case, documentation, previous),
                   'model': cfg['model']['name'], 'temperature': common['temperature'],
                   'max_output_tokens': common['max_output_tokens']}
        # Never include hidden oracle paths, references, or expected values in this request.
        response = _request_solution(cfg, request, root, retry_provider)
        if response is None:
            row['status'] = 'provider_pending'
            break
        code = response['code']
        if code.strip().startswith('```'):
            match = re.fullmatch(r'\s*```[^\n]*\n(.*?)\n```\s*', code, re.S)
            if match:
                code = match[1]
        _, result = _checked_execution(cfg, case, code, root, prefix='execution_')
        passed = verified_outcome(result)
        if passed is None:
            row['status'] = 'unverified'
            break
        row.update({k: result['payload'][k] for k in ('execution_pass', 'oracle_pass', 'target_reached')})
        if passed:
            row.update(status='pass', first_attempt_pass=round_number == 0, first_pass_round=round_number)
            break
        row['status'] = 'fail'
        # Adapter public feedback must not reveal hidden inputs/expected answers.
        # Complete compiler/runtime logs remain saved in the execution directory.
        previous = {'code': code, 'feedback': result['payload'].get('public_feedback', 'Independent checks did not pass.')}
    row['resources'] = _collect_resources(directory)
    return row


def _load_completed_rows(output):
    """Read only unit checkpoints and reject duplicates before another model call."""
    rows = {}
    for path in output.glob('*/*/result.json'):
        row = load(path)
        key = (row['arm'], row['case_id'], row['trial_id'])
        if key in rows:
            raise ValueError(f'Duplicate saved result: {key}')
        expected = output / key[0] / f'{key[1]}--{key[2]}' / 'result.json'
        if path != expected:
            raise ValueError(f'Saved result does not match its directory: {path}')
        rows[key] = row
    return rows


def _model_response(result):
    """One schema check shared by cached and newly returned provider responses."""
    payload = result.get('payload')
    if result.get('status') == 'ok' and isinstance(payload, dict) and isinstance(payload.get('code'), str):
        return payload
    return None


def _request_solution(cfg, request, root, retry_provider):
    """Reuse a saved response before spending a bounded transport allowance."""
    common = cfg['common']
    for record in sorted(root.glob('provider_*/process.json')):
        if load(record.parent / 'request.json') != request:
            raise ValueError('Resumed prompt differs from recorded prompt')
        response = _model_response(load(record))
        if response is not None:
            return response
    # An interrupted request might already have reached the provider. Retain it
    # and count it toward the allowance instead of quietly starting from zero.
    attempted = len(list(root.glob('provider_*')))
    limit = common['provider_attempt_limit']
    if retry_provider:
        limit += attempted
    for _ in range(attempted, limit):
        result = invoke(cfg['model']['command'], request, next_directory(root, 'provider_'),
                        common['provider_timeout_s'])
        response = _model_response(result)
        if response is not None:
            return response
    return None


def _collect_resources(directory):
    """Count all attempts, including interrupted calls with unknown token usage."""
    resources = {'provider_calls': 0, 'provider_seconds': 0, 'execution_seconds': 0,
                 'reported_input_tokens': 0, 'reported_output_tokens': 0, 'calls_without_usage': 0}
    for p in directory.glob('round_*/provider_*'):
        resources['provider_calls'] += 1
        proc = load(p / 'process.json') if (p / 'process.json').exists() else {}
        resources['provider_seconds'] += proc.get('seconds', 0)
        payload = proc.get('payload')
        usage = payload.get('usage') if isinstance(payload, dict) else None
        usage = usage if isinstance(usage, dict) else {}
        if not all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens')):
            resources['calls_without_usage'] += 1
        else:
            resources['reported_input_tokens'] += usage['input_tokens']
            resources['reported_output_tokens'] += usage['output_tokens']
    for p in directory.glob('round_*/execution_*/process.json'):
        resources['execution_seconds'] += load(p)['seconds']
    return resources
