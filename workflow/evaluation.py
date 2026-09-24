"""Run a frozen three-README study one task/trial/condition at a time.

Read from top to bottom: build public prompts, select documentation, schedule
unfinished units, and execute bounded solution/repair attempts. Setup and report
formatting live in evaluation_setup.py and reporting.py.
"""
from pathlib import Path
import random
import re

from .ablation import bind, digest, load, verify_artifact
from .execution import atomic_json, invoke, next_directory, ownership
from .evaluation_setup import (
    CONDITIONS, SYSTEM, adapter_request, verified_outcome, conditions_for,
    read_config, validate_bank, freeze_evaluation, open_frozen, assert_review_released,
    _checked_execution,
)
from .reporting import report, write_report
from .generation import (STOPPED_STATUSES, attempts, generation_record, mark_generation, model_response,
                         output_limit, rounds, save_generation, selected_response, verify_generation)
from .repair_context import compact_previous, public_failure

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


def select_documentation(paths, targets, max_characters, selection=None):
    """Select bounded public documentation using a default or explicit policy.

    Without an explicit policy, short documents are delivered in full and long
    documents rank H2 sections by API-name occurrence count, with stable source
    order breaking ties. The opt-in qualified_sections policy logs target-level
    coverage. No LLM selects text and no private answer enters retrieval.
    """
    if selection is not None:
        from .documentation_selection import select_qualified_sections
        return select_qualified_sections(paths, targets, max_characters, selection)
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
    conditions = conditions_for(cfg)
    if condition is not None and condition not in conditions:
        raise ValueError('Unknown documentation condition')
    output = Path(output).resolve()
    with ownership(output):
        identity = output / 'identity.json'
        if identity.exists() and load(identity)['study_sha256'] != frozen['study_sha256']:
            raise ValueError('This run directory belongs to another frozen study')
        atomic_json(identity, {'study_sha256': frozen['study_sha256']})
        rows = _load_completed_rows(output)
        report(frozen, list(rows.values()))  # Validate resumed rows before any model call.
        for (arm, case_id, trial), row in rows.items():
            _verify_readme_row(frozen, row, output / arm / f'{case_id}--{trial}')
        schedule = [(a, c, t) for a in conditions for c in bank['cases'] for t in common['trial_ids']]
        random.Random(common.get('ordering_seed', 42)).shuffle(schedule)
        processed = 0
        for arm, case, trial in schedule:
            key = (arm, case['id'], trial)
            if condition and arm != condition:
                continue
            if rows.get(key, {}).get('status') in STOPPED_STATUSES:
                continue
            if max_units is not None and processed >= max_units:
                break
            # Verify treatments/runtime again before each unit, including resumed units.
            if not all(verify_artifact(r) for r in frozen['artifacts']):
                raise ValueError('Study inputs changed while running')
            directory = output / arm / f"{case['id']}--{trial}"
            directory.mkdir(parents=True, exist_ok=True)
            docs, exposure = select_documentation(cfg['documents'][arm], case['target_apis'],
                                                  common.get('documentation_max_characters', 32000),
                                                  common.get('documentation_selection'))
            atomic_json(directory / 'documentation_exposure.json', exposure)
            row = _run_unit(frozen, arm, case, trial, docs, directory, retry_provider)
            _verify_readme_row(frozen, row, directory)
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


def _readme_request(frozen, case, documentation, previous, round_number):
    cfg, common = frozen['config'], frozen['config']['common']
    receipt = None
    if previous and common.get('repair_context') == 'distilled':
        previous, receipt = compact_previous(previous)
    return {'system': frozen['system_prompt'], 'prompt': audience_prompt(case, documentation, previous),
            'model': cfg['model']['name'], 'temperature': common['temperature'],
            'max_output_tokens': output_limit(common, round_number)}, receipt


def _run_unit(frozen, arm, case, trial, documentation, directory, retry_provider=False):
    cfg = frozen['config']
    common = cfg['common']
    row = {'arm': arm, 'case_id': case['id'], 'trial_id': trial, 'study_sha256': frozen['study_sha256'],
           'status': 'not_run', 'first_attempt_pass': False}
    previous = None
    for round_number in range(common['max_snippet_fixes'] + 1):
        root = directory / f'round_{round_number:02d}'
        request, repair_receipt = _readme_request(frozen, case, documentation, previous, round_number)
        if repair_receipt is not None:
            atomic_json(root / 'repair_context.json', repair_receipt)
        # Never include hidden oracle paths, references, or expected values in this request.
        response = _request_solution(cfg, request, root, retry_provider)
        if response is None:
            row['status'] = 'provider_pending'
            break
        if not mark_generation(row, response, round_number):
            break
        code = response['code']
        if code.strip().startswith('```'):
            match = re.fullmatch(r'\s*```[^\n]*\n(.*?)\n```\s*', code, re.S)
            if match:
                code = match[1]
        destination, result = _checked_execution(cfg, case, code, root, prefix='execution_')
        passed = verified_outcome(result)
        if passed is None:
            row['status'] = 'unverified'
            break
        row.update({k: result['payload'][k] for k in ('execution_pass', 'oracle_pass', 'target_reached')})
        row.update(last_checked_round=round_number, code_sha256=digest(code),
                   adjudication={'process': bind(destination / 'process.json'),
                                 'request': bind(destination / 'request.json')})
        if passed:
            row.update(status='pass', first_attempt_pass=round_number == 0, first_pass_round=round_number)
            break
        row['status'] = 'fail'
        # Adapter public feedback must not reveal hidden inputs/expected answers.
        # Complete compiler/runtime logs remain saved in the execution directory.
        previous = previous_result(code, result['payload'], 'Independent checks did not pass.')
    row['resources'] = _collect_resources(directory)
    row['round_evidence'] = rounds(directory)
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
    """Compatibility entry point shared by cached and new provider responses."""
    return model_response(result)


def _request_solution(cfg, request, root, retry_provider):
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
    limit = common['provider_attempt_limit'] + (attempted if retry_provider else 0)
    for _ in range(attempted, limit):
        destination = next_directory(root, 'provider_')
        result = invoke(cfg['model']['command'], request, destination, common['provider_timeout_s'])
        response = _model_response(result)
        if response is not None:
            save_generation(root, response, {'request.json': bind(destination / 'request.json'),
                                            'process.json': bind(destination / 'process.json')})
            return response
    return None


def previous_result(code, payload, fallback='Independent checks failed.'):
    previous = {'code': code, 'feedback': payload.get('public_feedback', fallback)}
    failure = public_failure(payload)
    if failure is not None:
        previous['public_failure'] = failure
    return previous


_RESULT_FIELDS = ('status', 'first_attempt_pass', 'first_pass_round', 'last_checked_round',
                  'code_sha256', 'adjudication', 'execution_pass', 'oracle_pass', 'target_reached',
                  'generation_status', 'generation_reason', 'last_generation_round')


def verify_result_fields(row, expected):
    for key in _RESULT_FIELDS:
        if (key in row) != (key in expected) or row.get(key) != expected.get(key):
            raise ValueError('Saved result differs from the replayed generation/checker verdict: ' + key)


def _verify_readme_row(frozen, row, directory):
    """Rebuild requests and outcomes from raw attempts before any resume."""
    cfg, common = frozen['config'], frozen['config']['common']
    if row.get('round_evidence') != rounds(directory):
        raise ValueError('Saved condition attempt evidence changed')
    if row.get('resources') != _collect_resources(directory):
        raise ValueError('Saved condition resource totals differ from attempt evidence')
    evidence = row['round_evidence']
    if not evidence or [r['round'] for r in evidence] != list(range(len(evidence))):
        raise ValueError('Saved evidence has missing or unexpected rounds')
    if len(evidence) > common['max_snippet_fixes'] + 1:
        raise ValueError('Saved result exceeds the common repair budget')
    case = next(c for c in frozen['bank']['cases'] if c['id'] == row['case_id'])
    docs, exposure = select_documentation(cfg['documents'][row['arm']], case['target_apis'],
                                          common.get('documentation_max_characters', 32000),
                                          common.get('documentation_selection'))
    if load(directory / 'documentation_exposure.json') != exposure:
        raise ValueError('Saved documentation exposure differs from the frozen prompt')
    expected = {'status': 'not_run', 'first_attempt_pass': False}
    previous = None
    for item in evidence:
        number = item['round']
        request, repair_receipt = _readme_request(frozen, case, docs, previous, number)
        if repair_receipt is not None:
            if 'repair_context' not in item or load(item['repair_context']['path']) != repair_receipt:
                raise ValueError('Saved repair context differs from the frozen prompt')
        elif 'repair_context' in item:
            raise ValueError('Unexpected saved repair context')
        selected = selected_response(item['providers'], request)
        if selected is None:
            if item['executions'] or item.get('generation'):
                raise ValueError('Execution/generation evidence lacks a provider response')
            expected['status'] = 'provider_pending'
        else:
            response, files = selected
            executable = mark_generation(expected, response, number)
            if not executable:
                if item['executions']:
                    raise ValueError('Nonexecutable generation has execution evidence')
                verify_generation(item, response, files)
            else:
                code = _candidate_body(response['code'])
                checker = adapter_request(case, code)
                checked = None
                for attempt in item['executions']:
                    records = attempt['files']
                    if 'request.json' in records and load(records['request.json']['path']) != checker:
                        raise ValueError('Saved checker candidate differs from the provider response')
                    if 'process.json' in records:
                        if 'request.json' not in records:
                            raise ValueError('Saved checker process lacks its request')
                        process = load(records['process.json']['path'])
                        outcome = verified_outcome(process)
                        if checked is not None:
                            raise ValueError('Saved execution follows an already checked outcome')
                        if outcome is not None:
                            checked = (outcome, process, records)
                verify_generation(item, response, files)
                if checked is None:
                    expected['status'] = 'unverified'
                else:
                    outcome, process, records = checked
                    expected.update({k: process['payload'][k] for k in ('execution_pass', 'oracle_pass', 'target_reached')})
                    expected.update(status='pass' if outcome else 'fail', last_checked_round=number,
                                    code_sha256=digest(code), adjudication={k: records[v] for k, v in
                                                                         [('process', 'process.json'), ('request', 'request.json')]})
                    if outcome:
                        expected.update(first_attempt_pass=number == 0, first_pass_round=number)
                    previous = previous_result(code, process['payload'], 'Independent checks did not pass.')
        if number < len(evidence) - 1 and expected['status'] != 'fail':
            raise ValueError('Saved repair follows a stopped or already passing round')
    if expected['status'] == 'fail' and len(evidence) != common['max_snippet_fixes'] + 1:
        raise ValueError('Saved failure has not exhausted the common repair budget')
    verify_result_fields(row, expected)


def _candidate_body(code):
    if code.strip().startswith('```'):
        match = re.fullmatch(r'\s*```[^\n]*\n(.*?)\n```\s*', code, re.S)
        if match:
            return match[1]
    return code


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
