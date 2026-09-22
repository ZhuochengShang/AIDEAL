"""Explicit README comparison labels use one frozen design and legacy defaults."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_evaluation as fixtures
from workflow.ablation import load
from workflow.evaluation import run_evaluation
from workflow.evaluation_setup import CONDITIONS, conditions_for, freeze_evaluation, read_config
from workflow.reporting import report

REFRESH = ('Unchanged generated README', 'Selected API refresh', 'Full README refresh')


class EvaluationDesignTests(unittest.TestCase):
    def setUp(self):
        # Reuse the two-case synthetic files without importing/discovering its
        # TestCase a second time. No real provider or library is executed.
        self.fixture = fixtures.EvaluationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def selective(self):
        cfg = self.fixture.config['readme_evaluation']
        cfg['design'] = 'selective_refresh'
        cfg['documents'] = {new: cfg['documents'][old] for new, old in zip(REFRESH, CONDITIONS)}
        self.fixture.write_config()

    def test_missing_design_and_explicit_three_readme_keep_original_order(self):
        cfg = self.fixture.config['readme_evaluation']
        before = deepcopy(cfg)
        self.assertEqual(CONDITIONS, conditions_for(cfg))
        self.assertEqual(before, cfg)
        self.assertEqual(CONDITIONS, conditions_for(read_config(self.fixture.yaml)['config']))
        cfg['design'] = 'three_readme'
        self.fixture.write_config()
        self.assertEqual(CONDITIONS, conditions_for(read_config(self.fixture.yaml)['config']))

    def test_cli_condition_filter_delegates_to_frozen_design_validation(self):
        from workflow.__main__ import main
        for label in (*REFRESH, *CONDITIONS):
            with self.subTest(label=label):
                command = ['aideal', 'run-evaluation', '--study', 'frozen.json',
                           '--output', 'run', '--condition', label, '--max-units', '1']
                with patch.object(sys, 'argv', command), redirect_stdout(io.StringIO()), \
                     patch('workflow.evaluation.run_evaluation', return_value={'synthetic': True}) as runner:
                    main()
                runner.assert_called_once_with('frozen.json', 'run', label, 1, False)

    def test_selective_names_flow_through_freeze_schedule_report_and_resume(self):
        self.selective()
        result = freeze_evaluation(self.fixture.yaml, self.fixture.root / 'freeze')
        self.assertEqual(list(REFRESH), result['conditions'])
        out = self.fixture.root / 'run'
        summary = run_evaluation(result['frozen'], out)
        self.assertEqual(list(REFRESH), summary['conditions'])
        self.assertEqual(list(REFRESH), list(summary['metrics']))
        self.assertEqual(set(REFRESH), set(summary['resources']))
        self.assertTrue(summary['all_complete'])
        self.assertEqual(0, summary['metrics'][REFRESH[0]]['micro']['correct_within_budget'])
        self.assertEqual(1, summary['metrics'][REFRESH[1]]['micro']['correct_within_budget'])
        self.assertEqual([(REFRESH[0], REFRESH[1]), (REFRESH[0], REFRESH[2]), (REFRESH[1], REFRESH[2])],
                         [(p['baseline'], p['treatment']) for p in summary['paired_comparisons'][::2]])
        self.assertEqual(100, summary['paired_comparisons'][0]['final_lift_percentage_points'])
        text = (out / 'REPORT.md').read_text()
        self.assertLess(text.index('| ' + REFRESH[0]), text.index('| ' + REFRESH[1]))
        self.assertLess(text.index('| ' + REFRESH[1]), text.index('| ' + REFRESH[2]))
        self.assertTrue(all((out / name).is_dir() for name in REFRESH))
        self.assertTrue(all(not (out / name).exists() for name in CONDITIONS))
        with patch('workflow.evaluation.invoke', side_effect=AssertionError('Unexpected provider repeat')):
            self.assertEqual(summary, run_evaluation(result['frozen'], out))

    def test_selected_condition_filter_uses_frozen_names(self):
        self.selective()
        frozen = self.fixture.freeze()
        out = self.fixture.root / 'one'
        summary = run_evaluation(frozen, out, condition=REFRESH[1], max_units=1)
        self.assertEqual(1, sum(r['provider_calls'] for r in summary['resources'].values()))
        self.assertTrue((out / REFRESH[1]).is_dir())
        self.assertFalse((out / REFRESH[0]).exists())
        other = self.fixture.root / 'invalid'
        with self.assertRaisesRegex(ValueError, 'Unknown documentation condition'):
            run_evaluation(frozen, other, condition=CONDITIONS[1])
        self.assertFalse(other.exists())

    def test_unknown_designs_and_mixed_names_fail_before_controls_or_output(self):
        baseline = deepcopy(self.fixture.config)
        for design in ('unknown', '', None, True, [], {}):
            with self.subTest(design=design):
                self.fixture.config = deepcopy(baseline)
                self.fixture.config['readme_evaluation']['design'] = design
                self.fixture.write_config()
                with patch('workflow.evaluation_setup.validate_bank') as controls:
                    with self.assertRaisesRegex(ValueError, 'Unknown.*design'):
                        self.fixture.freeze()
                    controls.assert_not_called()
        self.fixture.config = deepcopy(baseline)
        self.selective()
        cfg = self.fixture.config['readme_evaluation']
        cfg['documents'][CONDITIONS[0]] = cfg['documents'].pop(REFRESH[0])
        self.fixture.write_config()
        with patch('workflow.evaluation_setup.validate_bank') as controls:
            with self.assertRaisesRegex(ValueError, 'explicitly named'):
                self.fixture.freeze()
            controls.assert_not_called()
        self.assertFalse((self.fixture.root / 'freeze').exists())

    def test_report_rejects_old_condition_checkpoint_in_new_design(self):
        self.selective()
        frozen = load(self.fixture.freeze())
        row = {'arm': CONDITIONS[0], 'case_id': 'micro', 'trial_id': 'trial_01',
               'study_sha256': frozen['study_sha256'], 'status': 'fail', 'first_attempt_pass': False}
        with self.assertRaises(ValueError):
            report(frozen, [row])


if __name__ == '__main__':
    unittest.main()
