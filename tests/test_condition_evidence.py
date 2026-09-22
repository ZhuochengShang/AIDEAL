"""Offline condition evidence and mid-unit input-change regression checks."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_condition_evaluation as fixtures
from workflow.ablation import load
from workflow import condition_evaluation as runner


class ConditionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ConditionEvaluationTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        cfg = self.fixture.cfg['condition_evaluation']
        cfg['design'] = 'refactor_pair'
        cfg['conditions'] = {arm: cfg['conditions'][arm] for arm in ('original', 'refactor_only')}
        self.fixture.write_config()
        self.study = self.fixture.freeze()
        self.output = self.fixture.root / 'run'

    def completed(self):
        runner.run_conditions(self.study, self.output, condition='original', max_units=1)
        path = next(self.output.glob('original/*/result.json'))
        return path, load(path)

    def assert_resume_rejects(self, message):
        with patch.object(runner, '_request_solution') as model:
            with self.assertRaisesRegex(ValueError, message):
                runner.run_conditions(self.study, self.output, condition='original')
            model.assert_not_called()

    def test_deleted_earlier_provider_evidence_refuses_resume(self):
        result, _ = self.completed()
        request = next(result.parent.glob('round_00/provider_*/request.json'))
        (request.parent / 'process.json').unlink()
        request.unlink()
        self.assert_resume_rejects('attempt evidence changed')

    def test_changed_provider_logs_refuse_resume(self):
        result, _ = self.completed()
        stdout = next(result.parent.glob('round_00/provider_*/stdout.txt'))
        stdout.write_text(stdout.read_text() + '\nChanged evidence\n')
        self.assert_resume_rejects('attempt evidence changed')

    def test_changed_earlier_execution_evidence_refuses_resume(self):
        result, _ = self.completed()
        process = next(result.parent.glob('round_00/execution_*/process.json'))
        process.write_text(process.read_text() + '\n')
        self.assert_resume_rejects('attempt evidence changed')

    def test_saved_resource_totals_must_match_bound_attempts(self):
        path, row = self.completed()
        row['resources']['provider_calls'] += 100
        path.write_text(json.dumps(row))
        self.assert_resume_rejects('resource totals')

    def test_rebound_provider_candidate_must_match_checker_request(self):
        path, row = self.completed()
        process = next(path.parent.glob('round_00/provider_*/process.json'))
        value = load(process)
        value['payload']['code'] = 'correct'
        process.write_text(json.dumps(value))
        row['round_evidence'] = runner._round_evidence(path.parent)
        path.write_text(json.dumps(row))
        self.assert_resume_rejects('checker candidate differs')

    def test_rebound_exposure_must_match_frozen_prompt(self):
        path, row = self.completed()
        exposure = path.parent / 'round_00/context_exposure.json'
        value = load(exposure)
        value['public_prompt_characters'] += 1
        exposure.write_text(json.dumps(value))
        row['round_evidence'] = runner._round_evidence(path.parent)
        row['context_exposures'] = [item['exposure'] for item in row['round_evidence']]
        path.write_text(json.dumps(row))
        self.assert_resume_rejects('exposure differs from the frozen prompt')

    def test_input_change_after_provider_preserves_evidence_and_blocks_checker(self):
        original = runner._request_solution

        def mutate(*args, **kwargs):
            value = original(*args, **kwargs)
            source = self.fixture.root / 'original/lib.py'
            source.write_text(source.read_text() + '# changed after provider\n')
            return value

        with patch.object(runner, '_request_solution', side_effect=mutate):
            with patch.object(runner, 'execute_condition') as checker:
                with self.assertRaisesRegex(ValueError, 'input artifacts changed'):
                    runner.run_conditions(self.study, self.output, condition='original', max_units=1)
                checker.assert_not_called()
        self.assertTrue(list(self.output.glob('original/*/round_00/provider_*/process.json')))
        self.assertFalse(list(self.output.glob('original/*/result.json')))

    def test_input_change_after_checker_preserves_evidence_without_terminal_row(self):
        original = runner.execute_condition

        def mutate(*args, **kwargs):
            value = original(*args, **kwargs)
            source = self.fixture.root / 'original/lib.py'
            source.write_text(source.read_text() + '# changed after checker\n')
            return value

        with patch.object(runner, 'execute_condition', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'input artifacts changed'):
                runner.run_conditions(self.study, self.output, condition='original', max_units=1)
        self.assertTrue(list(self.output.glob('original/*/round_00/execution_*/process.json')))
        self.assertFalse(list(self.output.glob('original/*/result.json')))


if __name__ == '__main__':
    unittest.main()
