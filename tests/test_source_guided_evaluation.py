from pathlib import Path
import unittest
from unittest.mock import patch

import test_condition_evaluation as fixtures
from workflow.ablation import load
from workflow.condition_setup import read_condition_config
from workflow.condition_evaluation import run_conditions
from workflow.source_hints import insert_source_hint


class SourceGuidedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ConditionEvaluationTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        cfg = f.cfg['condition_evaluation']
        cfg.update(schema_version=2, design='five_arm', api_function_ids={'f': 'lib.py:1:f'})
        cfg['conditions'].pop('refactor_only')
        cfg['common'].update(repair_context='distilled', minimum_hint_coverage=1.0, hint_max_characters=2000,
                             repair_max_output_tokens=8192)
        fields = {'requirement_id': 'numeric_input', 'requirement': 'The input must be numeric.',
                  'diagnostic': 'expected numeric argument', 'action': 'FIX_HINT use a numeric argument.',
                  'validation': 'Rerun the independent checks.'}
        for arm in ('error_hints_only', 'combined'):
            c = cfg['conditions'][arm]
            c.pop('error_hints')
            c['source_hints'] = ['lib.py']
            path = Path(c['source']['worktree']) / 'lib.py'
            path.write_text(insert_source_hint(path.read_text(), 'lib.py:1:f', fields, source_path='lib.py'))
            f.git(path.parent, 'add', 'lib.py')
            f.git(path.parent, 'commit', '-qm', 'Add source guidance')
            c['source']['revision'] = f.git(path.parent, 'rev-parse', 'HEAD')
        adapter = f.adapter.read_text().replace("'public_feedback':", "'public_failure':{'function_id':'lib.py:1:f','requirement_id':'numeric_input','diagnostic':'expected numeric argument'}, 'public_feedback':")
        f.adapter.write_text(adapter)
        f.write_config()

    def test_new_source_protocol_executes_and_resumes_with_exact_context(self):
        f = self.fixture
        study = f.freeze()
        frozen = load(study)
        self.assertEqual(frozen['protocol'], 'condition_evaluation_source_hints_v2')
        self.assertEqual(frozen['source_hint_indexes']['error_hints_only']['coverage']['covered_functions'], 1)
        output = f.root / 'source-run'
        report = run_conditions(study, output)
        self.assertTrue(report['all_complete'])
        receipt = load(output / 'error_hints_only/micro--trial_01/round_01/context_exposure.json')
        self.assertEqual(receipt['hints']['reason'], 'matched')
        self.assertEqual(receipt['hints']['delivered'][0]['signature'], 'def f(x)')
        self.assertFalse(receipt['repair_context']['code_truncated'])
        request = load(next((output / 'error_hints_only/micro--trial_01/round_01').glob('provider_*/request.json')))
        self.assertEqual(request['max_output_tokens'], 8192)
        self.assertIn('def f(x)', request['prompt'])
        self.assertNotIn('return x + 1', request['prompt'])
        for path in output.glob('*/**/provider_*/request.json'):
            if 'round_00' in str(path):
                self.assertNotIn('SOURCE-EMBEDDED REPAIR GUIDANCE', path.read_text())
            self.assertNotIn('PRIVATE_EXPECTATION', path.read_text())
        with patch('workflow.condition_evaluation._request_solution') as provider:
            self.assertEqual(report, run_conditions(study, output))
            provider.assert_not_called()

    def test_real_implementation_change_cannot_hide_in_source_hint_arm(self):
        f = self.fixture
        c = f.cfg['condition_evaluation']['conditions']['error_hints_only']
        path = Path(c['source']['worktree']) / 'lib.py'
        path.write_text(path.read_text().replace('x + 1', 'x + 2'))
        f.git(path.parent, 'add', 'lib.py')
        f.git(path.parent, 'commit', '-qm', 'Incorrect body change')
        c['source']['revision'] = f.git(path.parent, 'rev-parse', 'HEAD')
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'original backend code tree'):
            read_condition_config(f.config)

    def test_combined_rejects_different_guidance(self):
        f = self.fixture
        c = f.cfg['condition_evaluation']['conditions']['combined']
        path = Path(c['source']['worktree']) / 'lib.py'
        path.write_text(path.read_text().replace('FIX_HINT use a numeric argument.', 'Use a different corrective action.'))
        f.git(path.parent, 'add', 'lib.py')
        f.git(path.parent, 'commit', '-qm', 'Different guidance')
        c['source']['revision'] = f.git(path.parent, 'rev-parse', 'HEAD')
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'reuse the individual source guidance'):
            read_condition_config(f.config)

    def test_config_rejects_ambiguous_limits(self):
        f = self.fixture
        f.cfg['condition_evaluation']['common']['repair_max_output_tokens'] = True
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'repair_max_output_tokens'):
            read_condition_config(f.config)

    def test_line_ending_change_is_not_an_annotation_only_change(self):
        f = self.fixture
        c = f.cfg['condition_evaluation']['conditions']['error_hints_only']
        path = Path(c['source']['worktree']) / 'lib.py'
        path.write_bytes(path.read_bytes().replace(b'\n', b'\r\n'))
        f.git(path.parent, 'add', 'lib.py')
        f.git(path.parent, 'commit', '-qm', 'Line ending change')
        c['source']['revision'] = f.git(path.parent, 'rev-parse', 'HEAD')
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'original backend code tree'):
            read_condition_config(f.config)

    def test_minimum_coverage_refuses_an_uncovered_selected_api(self):
        f = self.fixture
        cfg = f.cfg['condition_evaluation']
        bank = load(f.root / 'bank.json')
        bank['api_names'].append('other')
        case = dict(bank['cases'][0], id='micro_other', target_apis=['other'])
        bank['cases'].append(case)
        f.write_json(f.root / 'bank.json', bank)
        cfg['api_function_ids']['other'] = 'other.py:1:other'
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'coverage 50.0% is below'):
            read_condition_config(f.config)

    def test_external_style_hint_copy_is_not_library_source(self):
        f = self.fixture
        cfg = f.cfg['condition_evaluation']
        c = cfg['conditions']['error_hints_only']
        relative = '.aideal/treatments/copied.py'
        identity = relative + ':1:f'
        path = Path(c['source']['worktree']) / relative
        fields = {'requirement_id': 'numeric_input', 'requirement': 'Numeric input.',
                  'diagnostic': 'expected numeric argument', 'action': 'Supply a number.', 'validation': 'Recheck.'}
        path.write_text(insert_source_hint('def f(x):\n    return x + 1\n', identity, fields, source_path=relative))
        cfg['api_function_ids'] = {'f': identity}
        c['source_hints'] = [relative]
        f.git(Path(c['source']['worktree']), 'add', relative)
        f.git(Path(c['source']['worktree']), 'commit', '-qm', 'External-style copied function')
        c['source']['revision'] = f.git(Path(c['source']['worktree']), 'rev-parse', 'HEAD')
        f.write_config()
        with self.assertRaisesRegex(ValueError, 'committed library source files'):
            read_condition_config(f.config)
