"""Run the explicit matched-condition protocol; legacy three-README code is intact."""
from pathlib import Path
import random
import re

from .ablation import bind, digest, load, verify_artifact
from .evaluation import (_collect_resources, _load_completed_rows, _model_response, _request_solution,
                         previous_result, verify_result_fields)
from .generation import (STOPPED_STATUSES, attempts, mark_generation, output_limit, rounds,
                         selected_response, verify_generation)
from .evaluation_setup import assert_review_released
from .execution import atomic_json, ownership
from .condition_context import public_context
from .condition_inputs import measured_conditions
from .condition_reporting import report_conditions, write_condition_report
from .condition_setup import (checked_outcome, checker_request, execute_condition,
                               freeze_conditions, open_conditions, verify_inputs)


def _candidate_body(code):
    if code.strip().startswith('```'):
        match = re.fullmatch(r'\s*```[^\n]*\n(.*?)\n```\s*', code, re.S)
        if match:
            return match[1]
    return code


def _attempt_evidence(root, prefix):
    return attempts(root, prefix)


def _round_evidence(directory):
    return rounds(directory, exposure=True)


def _model_request(frozen, prompt, number=0):
    common = frozen['config']['common']
    return {'system': frozen['system_prompt'], 'prompt': prompt, 'model': frozen['config']['model']['name'],
            'temperature': common['temperature'], 'max_output_tokens': output_limit(common, number)}


def run_condition_unit(frozen, arm, case, trial, directory, retry_provider=False):
    cfg, common = frozen['config'], frozen['config']['common']
    backend = frozen['backends'][arm]['sha256']
    row = {'arm': arm, 'case_id': case['id'], 'trial_id': trial,
           'study_sha256': frozen['study_sha256'], 'backend_sha256': backend,
           'status': 'not_run', 'first_attempt_pass': False}
    previous = None
    for number in range(common['max_snippet_fixes'] + 1):
        root = directory / f'round_{number:02d}'
        prompt, exposure = public_context(frozen, arm, case, previous)
        atomic_json(root / 'context_exposure.json', exposure)
        request = _model_request(frozen, prompt, number)
        response = _request_solution(cfg, request, root, retry_provider)
        verify_inputs(frozen)
        if response is None:
            row['status'] = 'provider_pending'
            break
        if not mark_generation(row, response, number):
            break
        code = _candidate_body(response['code'])
        destination, process = execute_condition(frozen, arm, case, code, root)
        verify_inputs(frozen)
        passed = checked_outcome(process, backend)
        if passed is None:
            row['status'] = 'unverified'
            break
        row.update({k: process['payload'][k] for k in ('execution_pass', 'oracle_pass', 'target_reached')})
        row.update(last_checked_round=number, code_sha256=digest(code),
                   adjudication={'process': bind(destination / 'process.json'),
                                 'request': bind(destination / 'request.json')})
        if passed:
            row.update(status='pass', first_attempt_pass=number == 0, first_pass_round=number)
            break
        row['status'] = 'fail'
        previous = previous_result(code, process['payload'])
    row['resources'] = _collect_resources(directory)
    row['context_exposures'] = [bind(p) for p in sorted(directory.glob('round_*/context_exposure.json'))]
    row['round_evidence'] = _round_evidence(directory)
    return row


def _verify_saved_row(frozen, row, directory):
    """Rebuild every saved outcome, including unresolved generation stops."""
    if row.get('round_evidence') != _round_evidence(directory):
        raise ValueError('Saved condition attempt evidence changed')
    if row.get('resources') != _collect_resources(directory):
        raise ValueError('Saved condition resource totals differ from attempt evidence')
    evidence = row['round_evidence']
    if not evidence or [r['round'] for r in evidence] != list(range(len(evidence))):
        raise ValueError('Saved condition evidence has missing or unexpected rounds')
    common = frozen['config']['common']
    if len(evidence) > common['max_snippet_fixes'] + 1:
        raise ValueError('Saved result exceeds the common repair budget')
    if row.get('context_exposures') != [item['exposure'] for item in evidence]:
        raise ValueError('Saved public-context exposure changed')
    case = next(c for c in frozen['bank']['cases'] if c['id'] == row['case_id'])
    backend = frozen['backends'][row['arm']]['sha256']
    previous = None
    expected = {'status': 'not_run', 'first_attempt_pass': False}
    for item in evidence:
        number = item['round']
        prompt, exposure = public_context(frozen, row['arm'], case, previous)
        if load(item['exposure']['path']) != exposure:
            raise ValueError('Saved public-context exposure differs from the frozen prompt')
        selected = selected_response(item['providers'], _model_request(frozen, prompt, number))
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
                checker = checker_request(frozen, row['arm'], case, code)
                checked = None
                for attempt in item['executions']:
                    records = attempt['files']
                    if 'request.json' in records and load(records['request.json']['path']) != checker:
                        raise ValueError('Saved checker candidate differs from the provider response')
                    if 'process.json' in records:
                        if 'request.json' not in records:
                            raise ValueError('Saved checker process lacks its request')
                        process = load(records['process.json']['path'])
                        outcome = checked_outcome(process, backend)
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
                    previous = previous_result(code, process['payload'])
        if number < len(evidence) - 1 and expected['status'] != 'fail':
            raise ValueError('Saved repair follows a stopped or already passing round')
    if expected['status'] == 'fail' and len(evidence) != common['max_snippet_fixes'] + 1:
        raise ValueError('Saved failure has not exhausted the common repair budget')
    verify_result_fields(row, expected)


def run_conditions(study, output, condition=None, max_units=None, retry_provider=False):
    assert_review_released(Path(study).resolve().parent)
    if max_units is not None and (type(max_units) is not int or max_units < 1):
        raise ValueError('max_units must be a positive integer')
    frozen = open_conditions(study)
    cfg, bank = frozen['config'], frozen['bank']
    measured = measured_conditions(cfg)
    if condition is not None and condition not in measured:
        raise ValueError('Condition is outside the frozen measured_conditions scope')
    output = Path(output).resolve()
    assert_review_released(output)
    with ownership(output):
        identity = output / 'identity.json'
        if identity.exists() and load(identity).get('study_sha256') != frozen['study_sha256']:
            raise ValueError('Run belongs to another frozen condition study')
        atomic_json(identity, {'study_sha256': frozen['study_sha256'], 'protocol': frozen['protocol']})
        rows = _load_completed_rows(output)
        report_conditions(frozen, list(rows.values()))
        for (arm, case_id, trial), row in rows.items():
            _verify_saved_row(frozen, row, output / arm / f'{case_id}--{trial}')
        schedule = [(a, c, t) for a in measured for c in bank['cases'] for t in cfg['common']['trial_ids']]
        random.Random(cfg['common'].get('ordering_seed', 42)).shuffle(schedule)
        processed = 0
        for arm, case, trial in schedule:
            key = (arm, case['id'], trial)
            if (condition and arm != condition) or rows.get(key, {}).get('status') in STOPPED_STATUSES:
                continue
            if max_units is not None and processed >= max_units:
                break
            verify_inputs(frozen)
            directory = output / arm / f"{case['id']}--{trial}"
            directory.mkdir(parents=True, exist_ok=True)
            row = run_condition_unit(frozen, arm, case, trial, directory, retry_provider)
            verify_inputs(frozen)
            _verify_saved_row(frozen, row, directory)
            atomic_json(directory / 'result.json', row)
            rows[key] = row
            write_condition_report(output, report_conditions(frozen, list(rows.values())))
            processed += 1
            if row['status'] in ('provider_pending', 'unverified'):
                break
        summary = report_conditions(frozen, list(rows.values()))
        write_condition_report(output, summary)
        return summary
