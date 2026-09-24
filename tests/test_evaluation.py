"""End-to-end control runs with synthetic adapters, never research scores."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from workflow import evaluation_setup
from workflow.ablation import digest, file_hash, load
from workflow.evaluation import (CONDITIONS, audience_prompt, freeze_evaluation,
                                 open_frozen, read_config, run_evaluation,
                                 _load_completed_rows, _model_response, _collect_resources)
from workflow.execution import ownership
from workflow.model_adapter import response_record


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.adapter = self.root / 'adapter.py'
        self.adapter.write_text('''import json, sys
from pathlib import Path
r=json.load(sys.stdin)
expected=json.loads(Path(r['oracle_path']).read_text())['answer']
print(json.dumps(dict(execution_pass=True, oracle_pass=r['code']==expected,
                     target_reached=r['code'] in ('correct', 'wrong'),
                     public_feedback='Independent checks failed')))
''')
        self.model = self.root / 'model.py'
        self.model.write_text('''import json,sys
r=json.load(sys.stdin)
assert 'oracle_path' not in r and 'PRIVATE_ANSWER' not in str(r)
print(json.dumps({'code': 'correct' if 'TREATMENT_GOOD' in r['prompt'] else 'wrong',
                  'usage': {'input_tokens': 5, 'output_tokens': 2}}))
''')
        (self.root / 'reference.txt').write_text('correct')
        (self.root / 'negative.txt').write_text('wrong')
        (self.root / 'oracle.json').write_text(json.dumps({'answer': 'correct', 'secret': 'PRIVATE_ANSWER'}))
        (self.root / 'source.txt').write_text('SYNTHETIC implementation')
        cases = [dict(id=kind, kind=kind, split='held_out', target_apis=['f'], prompt='Compute f(x).',
                      reference='reference.txt', negative_controls=['negative.txt'], oracle='oracle.json')
                 for kind in ('micro', 'puzzle')]
        (self.root / 'bank.json').write_text(json.dumps(dict(api_names=['f'], cases=cases)))
        documents = {}
        for index, name in enumerate(CONDITIONS):
            p = self.root / f'doc_{index}.txt'
            p.write_text('TREATMENT_GOOD' if index else 'baseline')
            documents[name] = [str(p)]
        self.config = {'readme_evaluation': {
            'bank': 'bank.json', 'documents': documents,
            'adapter': {'command': [sys.executable, str(self.adapter)], 'artifacts': [str(self.adapter)]},
            'model': {'name': 'synthetic-no-LLM', 'command': [sys.executable, str(self.model)], 'artifacts': [str(self.model)]},
            'source': {'revision': 'synthetic', 'artifacts': ['source.txt']},
            'common': {'temperature': 0, 'max_output_tokens': 100, 'provider_attempt_limit': 2,
                       'execution_timeout_s': 5, 'provider_timeout_s': 5, 'max_snippet_fixes': 0,
                       'trial_ids': ['trial_01']},
            'holdout_review': 'Synthetic software controls; no experiment claims'}}
        self.yaml = self.root / 'study.yaml'
        self.write_config()

    def write_config(self):
        self.yaml.write_text(yaml.safe_dump(self.config))

    def freeze(self):
        return Path(freeze_evaluation(self.yaml, self.root / 'freeze')['frozen'])

    def test_three_conditions_execute_and_resume_without_duplicate_calls(self):
        study = self.freeze()
        out = self.root / 'run'
        first = run_evaluation(study, out, max_units=2)
        self.assertFalse(first['all_complete'])
        full = run_evaluation(study, out)
        self.assertTrue(full['all_complete'])
        self.assertEqual(0, full['metrics']['Original README']['micro']['correct_within_budget'])
        self.assertEqual(1, full['metrics']['Generated README']['micro']['correct_within_budget'])
        self.assertEqual(6, len(full['paired_comparisons']))
        self.assertEqual(100, full['paired_comparisons'][0]['final_lift_percentage_points'])
        before = list(out.glob('*/**/provider_*'))
        self.assertEqual(full, run_evaluation(study, out))
        self.assertEqual(before, list(out.glob('*/**/provider_*')))
        for p in out.glob('*/**/provider_*/request.json'):
            self.assertNotIn('PRIVATE_ANSWER', p.read_text())
            self.assertNotIn('oracle_path', p.read_text())

    def test_controls_reject_an_oracle_that_always_passes(self):
        self.adapter.write_text(self.adapter.read_text().replace("r['code']==expected", 'True'))
        with self.assertRaisesRegex(ValueError, 'Oracle controls failed'):
            self.freeze()
        self.assertFalse((self.root / 'freeze/frozen.json').exists())

    def test_placeholders_do_not_freeze(self):
        bank = load(self.root / 'bank.json')
        bank['cases'][0]['prompt'] = None
        (self.root / 'bank.json').write_text(json.dumps(bank))
        with self.assertRaisesRegex(ValueError, 'placeholders'):
            self.freeze()

    def test_changed_docs_code_or_oracle_refuse_resume(self):
        study = self.freeze()
        for p in (self.root / 'doc_0.txt', self.root / 'source.txt', self.root / 'oracle.json', self.adapter):
            original = p.read_bytes()
            p.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'changed'):
                open_frozen(study)
            p.write_bytes(original)

    def test_pending_transport_keeps_denominator_and_stops_batch(self):
        self.model.write_text('raise RuntimeError("synthetic provider failure")')
        study = self.freeze()
        report = run_evaluation(study, self.root / 'run')
        self.assertFalse(report['all_complete'])
        self.assertEqual(6, sum(m['unresolved'] for a in report['metrics'].values() for m in a.values()))
        self.assertEqual(2, sum(r['provider_calls'] for r in report['resources'].values()))

    def test_fixer_receives_full_previous_code_and_public_feedback_only(self):
        previous = {'code': 'x' * 12000, 'feedback': 'compiler message'}
        prompt = audience_prompt({'prompt': 'task', 'oracle': 'PRIVATE_ANSWER'}, 'docs', previous)
        self.assertIn(previous['code'], prompt)
        self.assertIn(previous['feedback'], prompt)
        self.assertNotIn('PRIVATE_ANSWER', prompt)

    def test_concurrent_output_owner_is_rejected(self):
        with ownership(self.root / 'output'):
            with self.assertRaisesRegex(ValueError, 'Another worker'):
                with ownership(self.root / 'output'):
                    pass

    def test_bank_scope_and_overlap_are_not_silently_reduced(self):
        self.config['readme_evaluation']['development_case_ids'] = ['micro']
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            read_config(self.yaml)

    def test_repair_budget_and_full_previous_solution_are_used(self):
        self.config['readme_evaluation']['common']['max_snippet_fixes'] = 1
        self.write_config()
        self.model.write_text('''import json,sys
r=json.load(sys.stdin)
repaired='COMPLETE PREVIOUS SOLUTION' in r['prompt']
if repaired: assert 'wrong' in r['prompt'] and 'Independent checks failed' in r['prompt']
print(json.dumps({'code': 'correct' if repaired else 'wrong'}))
''')
        result = run_evaluation(self.freeze(), self.root / 'run')
        self.assertTrue(result['all_complete'])
        for metrics in result['metrics'].values():
            for value in metrics.values():
                self.assertEqual(0, value['first_attempt_correct'])
                self.assertEqual(1, value['correct_within_budget'])
        self.assertEqual(12, sum(x['provider_calls'] for x in result['resources'].values()))

    def test_explicit_transport_retry_preserves_previous_calls(self):
        ready = self.root / 'provider_recovered'
        self.model.write_text('import json,sys\nfrom pathlib import Path\n'
                              + f'assert Path({str(ready)!r}).exists()\n'
                              + 'json.load(sys.stdin)\nprint(json.dumps({"code":"correct"}))\n')
        study = self.freeze()
        output = self.root / 'run'
        first = run_evaluation(study, output)
        self.assertFalse(first['all_complete'])
        ready.touch()
        result = run_evaluation(study, output, retry_provider=True)
        self.assertTrue(result['all_complete'])
        self.assertEqual(8, sum(x['provider_calls'] for x in result['resources'].values()))

    def test_conditions_cannot_reuse_another_frozen_run(self):
        study = self.freeze()
        output = self.root / 'run'
        run_evaluation(study, output, max_units=1)
        identity = load(output / 'identity.json')
        identity['study_sha256'] = 'other'
        (output / 'identity.json').write_text(json.dumps(identity))
        with self.assertRaisesRegex(ValueError, 'another frozen study'):
            run_evaluation(study, output)

    def test_review_hold_blocks_before_any_command(self):
        (self.root / 'REVIEW_HOLD.json').write_text('{"reason":"user review"}')
        with patch('workflow.evaluation_setup.invoke') as controls, patch('workflow.evaluation.invoke') as runner:
            with self.assertRaisesRegex(ValueError, 'paused for user code review'):
                self.freeze()
            with self.assertRaisesRegex(ValueError, 'paused for user code review'):
                run_evaluation(self.root / 'frozen/frozen.json', self.root / 'run')
            controls.assert_not_called()
            runner.assert_not_called()
        self.assertFalse((self.root / 'run').exists())

    def test_unsafe_ids_and_separator_collisions_rejected(self):
        path = self.root / 'bank.json'
        bank = load(path)
        for case_id in ('.', '..', 'task--trial', '../escape'):
            bank['cases'][0]['id'] = case_id
            path.write_text(json.dumps(bank))
            with self.subTest(case_id=case_id), self.assertRaisesRegex(ValueError, 'Unsafe case ID'):
                read_config(self.yaml)

    def test_numeric_budgets_are_finite_and_have_correct_types(self):
        common = self.config['readme_evaluation']['common']
        for key, invalid in (('max_snippet_fixes', True), ('provider_attempt_limit', 1.5),
                             ('max_output_tokens', False), ('provider_timeout_s', float('inf')),
                             ('temperature', float('nan'))):
            original = common[key]
            common[key] = invalid
            self.write_config()
            with self.subTest(setting=key), self.assertRaises(ValueError):
                read_config(self.yaml)
            common[key] = original

    def test_malformed_study_fields_are_rejected_before_commands_or_output(self):
        original_config = deepcopy(self.config)
        original_bank = load(self.root / 'bank.json')
        invalid_fields = [
            ('config', (), []),
            ('config', ('readme_evaluation',), []),
            ('config', ('readme_evaluation', 'model'), None),
            ('config', ('readme_evaluation', 'adapter'), []),
            ('config', ('readme_evaluation', 'source'), 'source'),
            ('config', ('readme_evaluation', 'common'), []),
            ('config', ('readme_evaluation', 'common', 'ordering_seed'), []),
            ('config', ('readme_evaluation', 'common', 'ordering_seed'), {}),
            ('config', ('readme_evaluation', 'common', 'ordering_seed'), None),
            ('config', ('readme_evaluation', 'common', 'ordering_seed'), True),
            ('config', ('readme_evaluation', 'common', 'source_access'), []),
            ('config', ('readme_evaluation', 'common', 'source_access'), {}),
            ('config', ('readme_evaluation', 'common', 'source_access'), 0),
            ('config', ('readme_evaluation', 'model', 'name'), 123),
            ('config', ('readme_evaluation', 'model', 'name'), '   '),
            ('config', ('readme_evaluation', 'holdout_review'), {'note': 'reviewed'}),
            ('config', ('readme_evaluation', 'holdout_review'), '   '),
            ('config', ('readme_evaluation', 'source', 'revision'), 123),
            ('config', ('readme_evaluation', 'source', 'revision'), '   '),
            ('config', ('readme_evaluation', 'model', 'artifacts'), str(self.model)),
            ('config', ('readme_evaluation', 'adapter', 'artifacts'), [123]),
            ('config', ('readme_evaluation', 'source', 'artifacts'), ['   ']),
            ('config', ('readme_evaluation', 'development_case_ids'), 'development'),
            ('bank', (), []),
            ('bank', ('cases',), {}),
            ('bank', ('cases',), ['case']),
            ('bank', ('api_names',), 'f'),
            ('bank', ('api_names',), [123]),
            ('bank', ('api_names',), ['   ']),
            ('bank', ('cases', 0, 'prompt'), 123),
            ('bank', ('cases', 0, 'prompt'), '   '),
            ('bank', ('cases', 0, 'public_context'), ['contract']),
            ('bank', ('cases', 0, 'public_context'), None),
            ('bank', ('cases', 0, 'target_apis'), 'f'),
            ('bank', ('cases', 0, 'target_apis'), [123]),
            ('bank', ('cases', 0, 'target_apis'), ['   ']),
            ('bank', ('cases', 0, 'reference'), 123),
            ('bank', ('cases', 0, 'oracle'), '   '),
            ('bank', ('cases', 0, 'negative_controls'), 'negative.txt'),
            ('bank', ('cases', 0, 'negative_controls'), ['   ']),
            ('bank', ('cases', 0, 'target_negative_controls'), 'negative.txt'),
        ]
        for index, (source, keys, invalid) in enumerate(invalid_fields):
            with self.subTest(source=source, field=keys, invalid=invalid):
                values = {'config': deepcopy(original_config), 'bank': deepcopy(original_bank)}
                if keys:
                    target = values[source]
                    for key in keys[:-1]:
                        target = target[key]
                    target[keys[-1]] = invalid
                else:
                    values[source] = invalid
                self.config = values['config']
                self.write_config()
                (self.root / 'bank.json').write_text(json.dumps(values['bank']))
                output = self.root / f'invalid_freeze_{index}'
                with patch('workflow.evaluation_setup.invoke',
                           side_effect=AssertionError('Malformed input reached a command')) as command:
                    with self.assertRaises(ValueError):
                        freeze_evaluation(self.yaml, output)
                    command.assert_not_called()
                self.assertFalse(output.exists())

    def test_empty_optional_context_and_control_lists_remain_valid(self):
        bank = load(self.root / 'bank.json')
        for case in bank['cases']:
            case['public_context'] = ''
            case['target_negative_controls'] = []
        (self.root / 'bank.json').write_text(json.dumps(bank))
        self.config['readme_evaluation']['development_case_ids'] = []
        common = deepcopy(self.config['readme_evaluation']['common'])
        for settings in ({}, {'source_access': False, 'ordering_seed': 0},
                         {'source_access': False, 'ordering_seed': -7}):
            with self.subTest(settings=settings):
                self.config['readme_evaluation']['common'] = dict(common, **settings)
                self.write_config()
                payload = read_config(self.yaml)
                self.assertEqual('', payload['bank']['cases'][0]['public_context'])
                for key, value in settings.items():
                    self.assertEqual(value, payload['config']['common'][key])

    def test_control_validation_retries_infrastructure_failure_and_preserves_evidence(self):
        ready, calls = self.root / 'checker_ready', self.root / 'checker_calls.json'
        self.adapter.write_text('''import json, sys
from pathlib import Path
r=json.load(sys.stdin)
''' + f'calls=Path({str(calls)!r})\nready=Path({str(ready)!r})\n' + '''
counts=json.loads(calls.read_text()) if calls.exists() else {}
key=r['case_id'] + ':' + r['code']
counts[key]=counts.get(key, 0)+1
calls.write_text(json.dumps(counts))
if r['case_id']=='micro' and r['code']=='wrong' and not ready.exists():
    raise RuntimeError('Synthetic transient checker outage')
print(json.dumps(dict(execution_pass=True, oracle_pass=r['code']=='correct', target_reached=True)))
''')
        with self.assertRaisesRegex(ValueError, 'Oracle controls failed'):
            self.freeze()
        validation = self.root / 'freeze/validation'
        reference = validation / 'micro/reference/attempt_001/process.json'
        failed = validation / 'micro/negative_1/attempt_001'
        reference_bytes = reference.read_bytes()
        failed_bytes = {p.name: p.read_bytes() for p in failed.iterdir() if p.is_file()}
        self.assertEqual('adapter_error', load(failed / 'process.json')['status'])
        ready.touch()
        frozen = self.freeze()
        self.assertTrue(open_frozen(frozen)['validation']['validated'])
        self.assertEqual(reference_bytes, reference.read_bytes())
        self.assertEqual(failed_bytes, {p.name: p.read_bytes() for p in failed.iterdir() if p.is_file()})
        self.assertEqual('ok', load(failed.parent / 'attempt_002/process.json')['status'])
        expected = {'micro:correct': 1, 'micro:wrong': 2, 'puzzle:correct': 1, 'puzzle:wrong': 1}
        self.assertEqual(expected, load(calls))
        self.freeze()
        self.assertEqual(expected, load(calls))

    def test_semantically_failed_control_is_reused_without_rerolling(self):
        ready, calls = self.root / 'checker_changed_behavior', self.root / 'checker_calls.txt'
        self.adapter.write_text('''import json, sys
from pathlib import Path
r=json.load(sys.stdin)
''' + f'calls=Path({str(calls)!r})\nready=Path({str(ready)!r})\n' + '''
calls.write_text(str(int(calls.read_text())+1) if calls.exists() else '1')
print(json.dumps(dict(execution_pass=True,
    oracle_pass=r['code']=='correct' or not ready.exists(), target_reached=True)))
''')
        with self.assertRaisesRegex(ValueError, 'Oracle controls failed'):
            self.freeze()
        failed = self.root / 'freeze/validation/micro/negative_1/attempt_001/process.json'
        original = failed.read_bytes()
        self.assertEqual('ok', load(failed)['status'])
        ready.touch()
        with self.assertRaisesRegex(ValueError, 'Oracle controls failed'):
            self.freeze()
        self.assertEqual('2', calls.read_text())
        self.assertEqual(original, failed.read_bytes())
        self.assertFalse((failed.parent.parent / 'attempt_002').exists())
        self.assertFalse((self.root / 'freeze/frozen.json').exists())

    def _copy_controller(self):
        destination = self.root / 'controller_copy'
        shutil.copytree(Path(evaluation_setup.__file__).parent, destination / 'workflow',
                        ignore=shutil.ignore_patterns('__pycache__'))
        return destination

    def _run_copied_controller(self, directory, code, *arguments):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(directory))
        completed = subprocess.run([sys.executable, '-c', code, *map(str, arguments)],
                                   cwd=directory, env=environment, text=True, capture_output=True, timeout=15)
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_identical_copied_controller_accepts_frozen_identity(self):
        frozen = self.freeze()
        expected_names = {'evaluation.py', 'evaluation_setup.py', 'execution.py', 'reporting.py', 'ablation.py',
                          'generation.py', 'repair_context.py', 'response_status.py'}
        identity = load(frozen)['controller_sha256']
        self.assertEqual(expected_names, set(identity))
        controller = Path(evaluation_setup.__file__).parent
        self.assertEqual({name: file_hash(controller / name) for name in expected_names}, identity)
        copied = self._copy_controller()
        result = self._run_copied_controller(copied, '''import json, sys
from workflow.evaluation_setup import open_frozen
print(json.dumps({'study_sha256': open_frozen(sys.argv[1])['study_sha256']}))
''', frozen)
        self.assertEqual(load(frozen)['study_sha256'], result['study_sha256'])

    def test_changed_copied_controller_is_rejected_before_any_command(self):
        frozen = self.freeze()
        copied = self._copy_controller()
        module = copied / 'workflow/evaluation.py'
        module.write_text(module.read_text() + '\n# Synthetic edit to the active copied controller.\n')
        output = self.root / 'copied_run'
        result = self._run_copied_controller(copied, '''import json, sys
from pathlib import Path
from unittest.mock import patch
from workflow.evaluation import run_evaluation
with patch('workflow.evaluation.invoke', side_effect=AssertionError('Unexpected model/checker call')) as runner, \\
     patch('workflow.evaluation_setup.invoke', side_effect=AssertionError('Unexpected validation call')) as controls:
    try:
        run_evaluation(sys.argv[1], sys.argv[2], max_units=1)
    except Exception as exc:
        result={'error_type':type(exc).__name__, 'message':str(exc)}
    else:
        result={'error_type':None, 'message':''}
    result.update(command_calls=runner.call_count+controls.call_count, output_exists=Path(sys.argv[2]).exists())
print(json.dumps(result))
''', frozen, output)
        self.assertEqual('ValueError', result['error_type'], result)
        self.assertRegex(result['message'], '(?i)controller')
        self.assertEqual(0, result['command_calls'])
        self.assertFalse(result['output_exists'])

    def test_missing_controller_identity_requires_refreeze_without_mutating_legacy_file(self):
        frozen = self.freeze()
        legacy = load(frozen)
        legacy.pop('controller_sha256', None)
        legacy['study_sha256'] = digest({key: value for key, value in legacy.items() if key != 'study_sha256'})
        legacy_path = self.root / 'legacy_frozen.json'
        legacy_path.write_text(json.dumps(legacy))
        before = legacy_path.read_bytes()
        with self.assertRaisesRegex(ValueError, '(?i)(re-freeze|freeze.*new|new.*freez)'):
            open_frozen(legacy_path)
        self.assertEqual(before, legacy_path.read_bytes())

    def test_checkpoint_directory_must_match_its_identity(self):
        path = self.root / 'run/Original README/wrong-name/result.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'arm': 'Original README', 'case_id': 'micro', 'trial_id': 'trial_01'}))
        with self.assertRaisesRegex(ValueError, 'does not match its directory'):
            _load_completed_rows(self.root / 'run')

    def test_malformed_provider_payload_is_unresolved_without_crashing(self):
        for payload in (None, [], 'text', {'code': 42}):
            self.assertIsNone(_model_response({'status': 'ok', 'payload': payload}))
        folder = self.root / 'unit/round_00/provider_001'
        folder.mkdir(parents=True)
        (folder / 'process.json').write_text(json.dumps({'payload': [], 'seconds': 1}))
        self.assertEqual(1, _collect_resources(self.root / 'unit')['calls_without_usage'])

    def test_empty_answer_preserves_usage_and_is_not_a_transport_error(self):
        response = SimpleNamespace(text=None, model_version='synthetic', usage_metadata=SimpleNamespace(
            prompt_token_count=5, candidates_token_count=0, thoughts_token_count=7))
        record = response_record(response)
        self.assertEqual('', record['code'])
        self.assertEqual('empty_model_output', record['response_kind'])
        self.assertEqual({'input_tokens': 5, 'output_tokens': 7}, record['usage'])


if __name__ == '__main__':
    unittest.main()
