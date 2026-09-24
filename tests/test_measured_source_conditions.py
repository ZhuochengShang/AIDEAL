"""Two measured hint arms retain five backend controls and fixed task scope."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

import test_source_guided_evaluation as fixtures
from workflow.ablation import load
from workflow.condition_context import public_context
from workflow.condition_evaluation import run_conditions
from workflow.condition_reporting import report_conditions
from workflow.condition_setup import read_condition_config
from workflow.source_hints import insert_source_hint, strip_source_hints


class MeasuredSourceConditionsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SourceGuidedEvaluationTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.f = self.fixture.fixture
        self.cfg = self.f.cfg['condition_evaluation']
        self.cfg['measured_conditions'] = ['error_hints_only', 'combined']
        self.cfg['common'].update(max_snippet_fixes=2, max_output_tokens=8192,
                                  repair_max_output_tokens=8192)
        self.f.write_config()

    def test_all_five_controls_but_only_two_audience_arms_r0_r1_r2_and_resume(self):
        f = self.f
        f.model.write_text('''import json,sys
r=json.load(sys.stdin)
p=r['prompt']
code='correct' if 'COMPLETE PREVIOUS SOLUTION\\nwrong2' in p else 'wrong2' if 'COMPLETE PREVIOUS SOLUTION' in p else 'wrong'
print(json.dumps({'code':code,'usage':{'input_tokens':7,'output_tokens':3}}))
''')
        study = f.freeze()
        frozen = load(study)
        self.assertEqual(len(frozen['validation']['controls']), 30)
        self.assertEqual({r['arm'] for r in frozen['validation']['controls']}, set(self.cfg['conditions']))
        out = f.root / 'measured-run'
        report = run_conditions(study, out)
        self.assertTrue(report['all_complete'])
        self.assertEqual(report['conditions'], ['error_hints_only', 'combined'])
        self.assertEqual(report['unmeasured_conditions'], ['original', 'readme_only', 'alias_only'])
        self.assertEqual(report['measurement_scope']['planned_units'], 4)
        self.assertEqual(report['metrics_baseline'], 'error_hints_only')
        self.assertEqual(len(report['paired_comparisons']), 2)
        self.assertEqual(sum(v['provider_calls'] for v in report['resources'].values()), 12)
        self.assertEqual(sum(v['reported_input_tokens'] for v in report['resources'].values()), 84)
        self.assertEqual(sum(v['reported_output_tokens'] for v in report['resources'].values()), 36)
        for arm in report['unmeasured_conditions']:
            self.assertFalse((out / arm).exists())
        for row_path in out.glob('*/*/result.json'):
            row = load(row_path)
            self.assertEqual(row['first_pass_round'], 2)
            self.assertEqual([r['round'] for r in row['round_evidence']], [0, 1, 2])
        for path in out.glob('*/**/provider_*/request.json'):
            self.assertEqual(load(path)['max_output_tokens'], 8192)
            self.assertNotIn('POST-FAILURE DEVELOPMENT HINTS', path.read_text())
            self.assertNotIn('PRIVATE_EXPECTATION', path.read_text())
        for kinds in report['metrics'].values():
            for metric in kinds.values():
                self.assertNotIn('recoveries_vs_original', metric)
        with patch('workflow.condition_evaluation._request_solution') as provider:
            self.assertEqual(report, run_conditions(study, out))
            provider.assert_not_called()
            with self.assertRaisesRegex(ValueError, 'measured_conditions'):
                run_conditions(study, out, condition='original')
            provider.assert_not_called()

    def _add_helper(self):
        self.cfg['source_api_function_ids'] = {'f': 'lib.py:1:f', 'fixture.g': 'lib.py:3:g'}
        fields = {'requirement_id': 'helper_numeric', 'requirement': 'The helper input must be numeric.',
                  'diagnostic': 'expected helper numeric argument', 'action': 'Use a numeric helper input.',
                  'validation': 'Check the corrected helper call.'}
        for arm, c in self.cfg['conditions'].items():
            root = Path(c['source']['worktree'])
            path = root / 'lib.py'
            text = path.read_text() + 'def g(y):\n    return y + 2\n'
            if arm in ('error_hints_only', 'combined'):
                text = insert_source_hint(text, 'lib.py:3:g', fields, source_path='lib.py')
            path.write_text(text)
            self.f.git(root, 'add', 'lib.py')
            self.f.git(root, 'commit', '-qm', 'Fixture helper')
            c['source']['revision'] = self.f.git(root, 'rev-parse', 'HEAD')
        self.f.write_config()

    def test_helper_failure_selects_source_guidance_without_changing_bank_denominator(self):
        self._add_helper()
        payload = read_condition_config(self.f.config)
        payload['study_sha256'] = 'fixture'
        index = payload['source_hint_indexes']['error_hints_only']
        self.assertEqual(index['coverage']['total_functions'], 2)
        self.assertEqual(len(index['records']), 2)
        previous = {'code': 'from fixture import g\ng("bad")',
                    'feedback': 'Candidate.py:2: error: expected helper numeric argument\ng("bad")\n ^'}
        prompt, receipt = public_context(payload, 'error_hints_only', payload['bank']['cases'][0], previous)
        self.assertEqual(receipt['hints']['reason'], 'matched')
        self.assertIn('def g(y)', prompt)
        self.assertNotIn('return y + 2', prompt)
        self.assertNotIn('Use a numeric argument', prompt)
        report = report_conditions(payload, [])
        self.assertEqual(report['measurement_scope']['task_bank_api_count'], 1)
        self.assertEqual(report['measurement_scope']['source_attribution_api_count'], 2)
        self.assertEqual(report['metrics']['error_hints_only']['micro']['selected'], 1)
        self.assertEqual(report['source_hint_coverage']['error_hints_only']['covered_task_bank_api_count'], 1)
        self.assertEqual(self.cfg['api_function_ids'], {'f': 'lib.py:1:f'})
        left = Path(self.cfg['conditions']['original']['source']['worktree']) / 'lib.py'
        right = Path(self.cfg['conditions']['error_hints_only']['source']['worktree']) / 'lib.py'
        self.assertEqual(left.read_text(), strip_source_hints(right.read_text()))

    def test_helper_guidance_must_match_between_both_hint_arms(self):
        self._add_helper()
        c = self.cfg['conditions']['combined']
        root = Path(c['source']['worktree'])
        path = root / 'lib.py'
        path.write_text(path.read_text().replace('Use a numeric helper input.', 'Different helper guidance.'))
        self.f.git(root, 'add', 'lib.py')
        self.f.git(root, 'commit', '-qm', 'Mismatched helper treatment')
        c['source']['revision'] = self.f.git(root, 'rev-parse', 'HEAD')
        self.f.write_config()
        with self.assertRaisesRegex(ValueError, 'reuse the individual source guidance'):
            read_condition_config(self.f.config)

    def test_invalid_measured_scopes_are_rejected_before_checker(self):
        for value in ([], ['combined', 'combined'], ['unknown'], 'combined'):
            self.cfg['measured_conditions'] = value
            self.f.write_config()
            with patch('workflow.condition_setup.invoke') as checker:
                with self.assertRaisesRegex(ValueError, 'measured_conditions'):
                    self.f.freeze()
                checker.assert_not_called()

    def test_source_catalog_cannot_relabel_or_duplicate_task_identities(self):
        for value in ({}, {'f': 'other.py:1:f'}, {'f': 'lib.py:1:f', 'duplicate': 'lib.py:1:f'}):
            self.cfg['source_api_function_ids'] = value
            self.f.write_config()
            with self.assertRaisesRegex(ValueError, 'Source API catalog'):
                read_condition_config(self.f.config)

    def test_out_of_scope_result_cannot_be_counted_as_audience_measurement(self):
        payload = read_condition_config(self.f.config)
        payload['study_sha256'] = 'fixture'
        with self.assertRaisesRegex(ValueError, 'measured_conditions'):
            report_conditions(payload, [{'arm': 'original'}])

    def test_192_units_are_fixed_by_cases_trials_and_measured_arms(self):
        payload = read_condition_config(self.f.config)
        payload['study_sha256'] = 'fixture'
        cases = payload['bank']['cases']
        payload['bank']['cases'] = [dict(deepcopy(c), id=f"{c['kind']}_{i}") for c in cases for i in range(16)]
        payload['config']['common']['trial_ids'] = ['trial_01', 'trial_02', 'trial_03']
        report = report_conditions(payload, [])
        self.assertEqual(report['measurement_scope']['planned_units'], 192)
        self.assertEqual(sum(m['unresolved'] for ks in report['metrics'].values() for m in ks.values()), 192)
        self.assertEqual(report['metrics']['combined']['micro']['selected'], 48)

    def test_source_protocol_never_falls_back_to_legacy_json(self):
        payload = read_condition_config(self.f.config)
        payload['config']['conditions']['combined']['error_hints'] = '/does/not/exist.json'
        with patch('workflow.condition_context.load') as reader:
            with self.assertRaisesRegex(ValueError, 'forbids legacy JSON'):
                public_context(payload, 'combined', payload['bank']['cases'][0], {'code': 'bad', 'feedback': 'bad'})
            reader.assert_not_called()

    def test_all_five_metrics_retain_original_baseline(self):
        self.cfg.pop('measured_conditions')
        self.f.write_config()
        payload = read_condition_config(self.f.config)
        payload['study_sha256'] = 'fixture'
        report = report_conditions(payload, [])
        self.assertEqual(report['metrics_baseline'], 'original')
        self.assertEqual(len(report['conditions']), 5)
        self.assertIn('recoveries_vs_original', report['metrics']['combined']['micro'])

    def test_explicit_documentation_selection_is_preserved_during_repair(self):
        payload = read_condition_config(self.f.config)
        selection = {'policy': 'explicit frozen section selection'}
        payload['config']['common']['documentation_selection'] = selection
        case = payload['bank']['cases'][0]
        with patch('workflow.condition_context.select_documentation',
                   return_value=('SELECTED PUBLIC SECTIONS', {})) as select, \
             patch('workflow.condition_context.distill_documentation') as distill:
            prompt, receipt = public_context(payload, 'original', case,
                                             {'code': 'complete candidate', 'feedback': 'diagnostic'})
        select.assert_called_once_with(payload['config']['conditions']['original']['documents'],
                                       case['target_apis'],
                                       payload['config']['common']['documentation_max_characters'],
                                       selection)
        distill.assert_not_called()
        self.assertIn('SELECTED PUBLIC SECTIONS', prompt)
        self.assertFalse(receipt['repair_context']['code_truncated'])


if __name__ == '__main__':
    unittest.main()
