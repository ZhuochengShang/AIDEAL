"""Nonexecutable model outcomes remain unresolved and cannot become compiler failures."""
import json
import unittest
from unittest.mock import patch

import test_condition_evaluation as fixtures
import test_evaluation as legacy_fixtures
from workflow.ablation import load
from workflow import condition_evaluation as runner
from workflow import evaluation as legacy


class IncompleteEvaluationTests(unittest.TestCase):
    def setup_condition(self, payload=None, model=None):
        fixture = fixtures.ConditionEvaluationTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        cfg = fixture.cfg['condition_evaluation']
        cfg['design'] = 'refactor_pair'
        cfg['conditions'] = {a: cfg['conditions'][a] for a in ('original', 'refactor_only')}
        cfg['common'].update(max_snippet_fixes=1, provider_attempt_limit=3, repair_max_output_tokens=250)
        fixture.model.write_text(model or ('import json,sys\njson.load(sys.stdin)\nprint(' + repr(json.dumps(payload)) + ')\n'))
        fixture.write_config()
        return fixture, fixture.freeze(), fixture.root / 'run'

    def test_all_generation_stops_never_execute_or_retry(self):
        variants = [('incomplete', {'code': 'correct', 'response_status': 'incomplete', 'incomplete_reason': 'max_output_tokens'}),
                    ('empty', {'code': ''}), ('refusal', {'code': '', 'refusals': ['Cannot comply']}),
                    ('provider_failure', {'code': '', 'response_status': 'failed'})]
        for status, payload in variants:
            with self.subTest(status=status):
                payload['usage'] = {'input_tokens': 17, 'output_tokens': 31}
                fixture, study, out = self.setup_condition(payload)
                with patch.object(runner, 'execute_condition') as execute:
                    summary = runner.run_conditions(study, out, condition='original')
                    execute.assert_not_called()
                for path in out.glob('original/*/result.json'):
                    row = load(path)
                    self.assertEqual('generation_' + status, row['status'])
                    self.assertEqual(1, row['resources']['provider_calls'])
                    self.assertEqual(31, row['resources']['reported_output_tokens'])
                    self.assertFalse(list(path.parent.glob('round_*/execution_*')))
                self.assertFalse(summary['all_complete'])
                self.assertEqual(2, summary['generation_classifications']['original']['generation_' + status])
                for metrics in summary['metrics']['original'].values():
                    self.assertEqual(1, metrics['selected'])
                    self.assertEqual(0, metrics['completed'])
                with patch.object(runner, '_request_solution') as provider:
                    self.assertEqual(summary, runner.run_conditions(study, out, condition='original', retry_provider=True))
                    provider.assert_not_called()

    def test_repair_stop_retains_checked_round_and_uses_repair_cap(self):
        model = '''import json,sys
r=json.load(sys.stdin)
repair='COMPLETE PREVIOUS SOLUTION' in r['prompt']
print(json.dumps({'code':'correct' if repair else 'wrong',
 'response_status':'incomplete' if repair else 'completed',
 'incomplete_reason':'max_output_tokens' if repair else None,
 'usage':{'input_tokens':3,'output_tokens':5}}))
'''
        fixture, study, out = self.setup_condition(model=model)
        runner.run_conditions(study, out, condition='original', max_units=1)
        path = next(out.glob('original/*/result.json'))
        row = load(path)
        self.assertEqual('generation_incomplete', row['status'])
        self.assertEqual(0, row['last_checked_round'])
        self.assertEqual(1, row['last_generation_round'])
        self.assertEqual(2, row['resources']['provider_calls'])
        self.assertFalse(list(path.parent.glob('round_01/execution_*')))
        for number, cap in [(0, 100), (1, 250)]:
            self.assertEqual(cap, load(path.parent / f'round_{number:02d}/provider_001/request.json')['max_output_tokens'])
        runner._verify_saved_row(runner.open_conditions(study), row, path.parent)

    def test_rebound_receipt_and_provider_request_reject_before_calls(self):
        fixture, study, out = self.setup_condition({'code': 'partial', 'response_status': 'incomplete'})
        runner.run_conditions(study, out, condition='original', max_units=1)
        path = next(out.glob('original/*/result.json'))
        row = load(path)
        receipt = path.parent / 'round_00/generation.json'
        original = receipt.read_bytes()
        forged = load(receipt)
        forged.update(status='complete', executable=True)
        receipt.write_text(json.dumps(forged))
        row['round_evidence'] = runner._round_evidence(path.parent)
        path.write_text(json.dumps(row))
        with patch.object(runner, '_request_solution') as provider:
            with self.assertRaisesRegex(ValueError, 'generation evidence differs'):
                runner.run_conditions(study, out, condition='original')
            provider.assert_not_called()
        receipt.write_bytes(original)
        request = path.parent / 'round_00/provider_001/request.json'
        value = load(request)
        value['max_output_tokens'] += 1
        request.write_text(json.dumps(value))
        row['round_evidence'] = runner._round_evidence(path.parent)
        path.write_text(json.dumps(row))
        with patch.object(runner, '_request_solution') as provider:
            with self.assertRaisesRegex(ValueError, 'provider request differs'):
                runner.run_conditions(study, out, condition='original')
            provider.assert_not_called()

    def test_legacy_runner_stops_and_replays_status_on_resume(self):
        fixture = legacy_fixtures.EvaluationTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.model.write_text('import json,sys\njson.load(sys.stdin)\nprint(json.dumps({"code":"correct",'
                                 '"response_status":"incomplete","incomplete_reason":"max_output_tokens",'
                                 '"usage":{"input_tokens":13,"output_tokens":21}}))\n')
        study, out = fixture.freeze(), fixture.root / 'run'
        with patch.object(legacy, '_checked_execution') as execute:
            summary = legacy.run_evaluation(study, out)
            execute.assert_not_called()
        self.assertFalse(summary['all_complete'])
        self.assertEqual(6, sum(v['generation_incomplete'] for v in summary['generation_classifications'].values()))
        with patch.object(legacy, '_request_solution') as provider:
            self.assertEqual(summary, legacy.run_evaluation(study, out, retry_provider=True))
            provider.assert_not_called()
        path = next(out.glob('*/*/result.json'))
        row = load(path)
        row['generation_reason'] = 'fabricated'
        path.write_text(json.dumps(row))
        with patch.object(legacy, '_request_solution') as provider:
            with self.assertRaisesRegex(ValueError, 'replayed generation/checker verdict'):
                legacy.run_evaluation(study, out)
            provider.assert_not_called()

    def test_only_validated_public_attribution_enters_repair(self):
        failure = {'function_id': 'lib:f', 'requirement_id': 'integer', 'diagnostic': 'required Int'}
        payload = {'public_feedback': 'error: required Int', 'public_failure': failure,
                   'private_diagnostics': 'PRIVATE', 'oracle': 'PRIVATE'}
        self.assertEqual({'code': 'code', 'feedback': 'error: required Int', 'public_failure': failure},
                         legacy.previous_result('code', payload))
        payload['public_failure'] = {**failure, 'secret': 'PRIVATE'}
        self.assertNotIn('public_failure', legacy.previous_result('code', payload))


if __name__ == '__main__':
    unittest.main()
