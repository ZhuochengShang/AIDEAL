"""Run the explicit matched-condition protocol; legacy three-README code is intact."""
from pathlib import Path
import random
import re

from .ablation import bind, digest, load, verify_artifact
from .evaluation import _collect_resources, _load_completed_rows, _model_response, _request_solution
from .evaluation_setup import assert_review_released
from .execution import atomic_json, ownership
from .condition_context import public_context
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
    receipts = []
    for directory in sorted(root.glob(prefix + '*')):
        if not directory.is_dir() or re.fullmatch(re.escape(prefix) + r'\d{3,}', directory.name) is None:
            raise ValueError('Unexpected condition attempt directory')
        receipts.append({'directory': str(directory), 'files': {
            name: bind(directory / name) for name in ('request.json', 'process.json', 'stdout.txt', 'stderr.txt')
            if (directory / name).exists()}})
    return receipts


def _round_evidence(directory):
    receipts = []
    for root in sorted(directory.glob('round_*')):
        if not root.is_dir() or re.fullmatch(r'round_\d{2,}', root.name) is None:
            raise ValueError('Unexpected condition round directory')
        receipts.append({'round': int(root.name.removeprefix('round_')),
                         'exposure': bind(root / 'context_exposure.json'),
                         'providers': _attempt_evidence(root, 'provider_'),
                         'executions': _attempt_evidence(root, 'execution_')})
    return sorted(receipts, key=lambda item: item['round'])


def _model_request(frozen, prompt):
    common = frozen['config']['common']
    return {'system': frozen['system_prompt'], 'prompt': prompt, 'model': frozen['config']['model']['name'],
            'temperature': common['temperature'], 'max_output_tokens': common['max_output_tokens']}


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
        request = _model_request(frozen, prompt)
        response = _request_solution(cfg, request, root, retry_provider)
        verify_inputs(frozen)
        if response is None:
            row['status'] = 'provider_pending'
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
        previous = {'code': code, 'feedback': process['payload'].get('public_feedback', 'Independent checks failed.')}
    row['resources'] = _collect_resources(directory)
    row['context_exposures'] = [bind(p) for p in sorted(directory.glob('round_*/context_exposure.json'))]
    row['round_evidence'] = _round_evidence(directory)
    return row


def _verify_saved_row(frozen, row, directory):
    """Verify complete attempt evidence, costs and the public-prompt/candidate chain."""
    if row.get('round_evidence') != _round_evidence(directory):
        raise ValueError('Saved condition attempt evidence changed')
    if row.get('resources') != _collect_resources(directory):
        raise ValueError('Saved condition resource totals differ from attempt evidence')
    if row['status'] not in ('pass', 'fail'):
        return
    evidence = row.get('adjudication')
    if not isinstance(evidence, dict) or set(evidence) != {'process', 'request'}:
        raise ValueError('Terminal condition result lacks adjudication evidence')
    if not all(verify_artifact(r) for r in evidence.values()):
        raise ValueError('Condition result evidence changed')
    number = row.get('last_checked_round')
    if type(number) is not int or not 0 <= number <= frozen['config']['common']['max_snippet_fixes']:
        raise ValueError('Invalid checked round in saved result')
    process_path, request_path = Path(evidence['process']['path']), Path(evidence['request']['path'])
    if (process_path.parent != request_path.parent or process_path.name != 'process.json'
            or request_path.name != 'request.json' or process_path.parent.parent != directory / f'round_{number:02d}'
            or not process_path.parent.name.startswith('execution_')):
        raise ValueError('Adjudication evidence belongs to another unit')
    request, process = load(request_path), load(process_path)
    case = next(c for c in frozen['bank']['cases'] if c['id'] == row['case_id'])
    if request != checker_request(frozen, row['arm'], case, request.get('code')):
        raise ValueError('Adjudication request differs from the frozen case/backend')
    if not isinstance(request.get('code'), str) or digest(request['code']) != row.get('code_sha256'):
        raise ValueError('Saved candidate identity differs')
    outcome = checked_outcome(process, frozen['backends'][row['arm']]['sha256'])
    if outcome is None or outcome != (row['status'] == 'pass'):
        raise ValueError('Saved result differs from the checker verdict')
    if any(row.get(k) is not process['payload'][k] for k in ('execution_pass', 'oracle_pass', 'target_reached')):
        raise ValueError('Saved result flags differ from the checker verdict')
    if row['status'] == 'pass' and row['first_pass_round'] != number:
        raise ValueError('Saved first-pass round differs from adjudication')
    if row['status'] == 'fail' and number != frozen['config']['common']['max_snippet_fixes']:
        raise ValueError('Saved failure has not exhausted the common repair budget')
    exposures = row.get('context_exposures', [])
    expected = {str(directory / f'round_{n:02d}/context_exposure.json') for n in range(number + 1)}
    if ({r.get('path') for r in exposures} != expected or len(exposures) != len(expected)
            or not all(verify_artifact(r) for r in exposures)):
        raise ValueError('Saved public-context exposure changed')
    rounds = row['round_evidence']
    if [item['round'] for item in rounds] != list(range(number + 1)):
        raise ValueError('Saved condition evidence has missing or unexpected rounds')
    previous = None
    for item in rounds:
        prompt, exposure = public_context(frozen, row['arm'], case, previous)
        if load(item['exposure']['path']) != exposure:
            raise ValueError('Saved public-context exposure differs from the frozen prompt')
        expected_model = _model_request(frozen, prompt)
        response = None
        for attempt in item['providers']:
            files = attempt['files']
            if 'request.json' in files and load(files['request.json']['path']) != expected_model:
                raise ValueError('Saved provider request differs from the frozen public prompt')
            if 'process.json' in files:
                if 'request.json' not in files:
                    raise ValueError('Saved provider process lacks its request')
                value = _model_response(load(files['process.json']['path']))
                if response is None and value is not None:
                    response = value
        if response is None:
            raise ValueError('Checked condition round lacks a successful provider response')
        expected_checker = checker_request(frozen, row['arm'], case, _candidate_body(response['code']))
        checked = None
        for attempt in item['executions']:
            files = attempt['files']
            if 'request.json' in files and load(files['request.json']['path']) != expected_checker:
                raise ValueError('Saved checker candidate differs from the provider response')
            if 'process.json' in files:
                if 'request.json' not in files:
                    raise ValueError('Saved checker process lacks its request')
                value = load(files['process.json']['path'])
                outcome = checked_outcome(value, frozen['backends'][row['arm']]['sha256'])
                if outcome is not None:
                    checked = (outcome, value, files)
        if checked is None:
            raise ValueError('Checked condition round lacks verified execution evidence')
        outcome, value, files = checked
        if item['round'] < number and outcome:
            raise ValueError('Saved repair follows an already passing round')
        if item['round'] == number and (files['process.json'] != evidence['process']
                                       or files['request.json'] != evidence['request']):
            raise ValueError('Final adjudication differs from the selected execution attempt')
        previous = {'code': expected_checker['code'],
                    'feedback': value['payload'].get('public_feedback', 'Independent checks failed.')}


def run_conditions(study, output, condition=None, max_units=None, retry_provider=False):
    assert_review_released(Path(study).resolve().parent)
    if max_units is not None and (type(max_units) is not int or max_units < 1):
        raise ValueError('max_units must be a positive integer')
    frozen = open_conditions(study)
    cfg, bank = frozen['config'], frozen['bank']
    if condition is not None and condition not in cfg['conditions']:
        raise ValueError('Unknown study condition')
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
        schedule = [(a, c, t) for a in cfg['conditions'] for c in bank['cases'] for t in cfg['common']['trial_ids']]
        random.Random(cfg['common'].get('ordering_seed', 42)).shuffle(schedule)
        processed = 0
        for arm, case, trial in schedule:
            key = (arm, case['id'], trial)
            if (condition and arm != condition) or rows.get(key, {}).get('status') in ('pass', 'fail'):
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
