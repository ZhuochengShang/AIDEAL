"""Offline crash-boundary recovery; all inputs and commands are synthetic."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_evaluation as legacy_fixtures
import test_condition_evaluation as condition_fixtures
from workflow import evaluation as legacy, condition_evaluation as condition
from workflow import evaluation_program_generation
from workflow.ablation import load
from workflow.execution import invoke


class EvaluationRecoveryTests(unittest.TestCase):
    def fixture(self, mode, outage='checker', repairs=0):
        factory = (legacy_fixtures.EvaluationTests if mode == 'readme'
                   else condition_fixtures.ConditionEvaluationTests)
        fixture = factory(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        if mode == 'readme':
            cfg = fixture.config['readme_evaluation']
            runner, entry, arm = legacy, legacy.run_evaluation, 'Original README'
        else:
            cfg = fixture.cfg['condition_evaluation']
            cfg['design'] = 'refactor_pair'
            cfg['conditions'] = {a: cfg['conditions'][a] for a in ('original', 'refactor_only')}
            runner, entry, arm = condition, condition.run_conditions, 'original'
        cfg['common'].update(max_snippet_fixes=repairs, provider_attempt_limit=1)
        fixture.write_config()
        ready = fixture.root / 'ready'
        ready.touch()
        target = fixture.adapter if outage == 'checker' else fixture.model
        target.write_text('from pathlib import Path\nif not Path(' + repr(str(ready))
                          + ').exists(): raise RuntimeError("synthetic outage")\n' + target.read_text())
        with redirect_stdout(io.StringIO()):
            study = fixture.freeze()
        output = fixture.root / 'run'
        def run():
            with redirect_stdout(io.StringIO()):
                return entry(study, output, condition=arm, max_units=1, retry_provider=True)
        ready.unlink()
        run()
        result = next(output.glob('*/*/result.json'))
        self.assertEqual('unverified' if outage == 'checker' else 'provider_pending', load(result)['status'])
        ready.touch()
        return fixture, runner, run, result

    def interrupt_before_result(self, runner, run):
        original = runner.atomic_json
        def write(destination, value):
            if destination.name == 'result.json':
                raise KeyboardInterrupt('synthetic interruption before result checkpoint')
            return original(destination, value)
        with patch.object(runner, 'atomic_json', side_effect=write):
            with self.assertRaises(KeyboardInterrupt):
                run()

    def test_interrupted_provider_and_checker_retries_preserve_history_and_reuse_calls(self):
        for mode in ('readme', 'condition'):
            for outage in ('provider', 'checker'):
                with self.subTest(mode=mode, outage=outage):
                    _, runner, run, result = self.fixture(mode, outage)
                    checkpoint = result.read_bytes()
                    before = {p: p.read_bytes() for p in result.parent.glob('round_*/*/*') if p.is_file()}
                    self.interrupt_before_result(runner, run)
                    self.assertEqual(checkpoint, result.read_bytes())
                    processes = list(result.parent.glob('round_*/*/process.json'))
                    run()
                    self.assertEqual('fail', load(result)['status'])
                    self.assertEqual(processes, list(result.parent.glob('round_*/*/process.json')))
                    for path, content in before.items():
                        self.assertEqual(content, path.read_bytes())

    def test_extended_checkpoint_rejects_edited_or_deleted_bound_history_before_model(self):
        for mode in ('readme', 'condition'):
            for mutation in ('edit', 'delete'):
                with self.subTest(mode=mode, mutation=mutation):
                    _, runner, run, result = self.fixture(mode)
                    self.interrupt_before_result(runner, run)
                    original = result.parent / 'round_00/execution_001/process.json'
                    if mutation == 'edit':
                        original.write_text(original.read_text() + '\n')
                    else:
                        original.unlink()
                    with patch.object(runner, '_request_solution') as model:
                        with self.assertRaisesRegex(ValueError, 'attempt evidence changed'):
                            run()
                        model.assert_not_called()

    def test_extended_checkpoint_replays_new_provider_and_checker_requests_before_calls(self):
        for mode in ('readme', 'condition'):
            for outage in ('provider', 'checker'):
                with self.subTest(mode=mode, outage=outage):
                    _, runner, run, result = self.fixture(mode, outage)
                    self.interrupt_before_result(runner, run)
                    kind = 'provider' if outage == 'provider' else 'execution'
                    request = result.parent / f'round_00/{kind}_002/request.json'
                    value = load(request)
                    value['prompt' if outage == 'provider' else 'code'] = 'altered request'
                    request.write_text(json.dumps(value))
                    with patch.object(runner, '_request_solution') as model:
                        with self.assertRaisesRegex(ValueError, 'provider request|checker candidate'):
                            run()
                        model.assert_not_called()

    def test_terminal_checkpoint_rejects_any_appended_attempt(self):
        for mode in ('readme', 'condition'):
            with self.subTest(mode=mode):
                _, runner, run, result = self.fixture(mode)
                run()
                (result.parent / 'round_00/execution_003').mkdir()
                with patch.object(runner, '_request_solution') as model:
                    with self.assertRaisesRegex(ValueError, 'attempt evidence changed'):
                        run()
                    model.assert_not_called()

    def test_interrupted_retry_can_resume_between_failed_check_and_next_repair(self):
        for mode in ('readme', 'condition'):
            with self.subTest(mode=mode):
                _, runner, run, result = self.fixture(mode, repairs=1)
                original = runner._request_solution
                def interrupt_next_round(cfg, request, root, retry_provider):
                    if root.name == 'round_01':
                        raise KeyboardInterrupt('synthetic interruption before repair generation')
                    return original(cfg, request, root, retry_provider)
                with patch.object(runner, '_request_solution', side_effect=interrupt_next_round):
                    with self.assertRaises(KeyboardInterrupt):
                        run()
                run()
                self.assertEqual('fail', load(result)['status'])
                self.assertEqual(1, load(result)['last_checked_round'])

    def test_missing_generation_after_new_provider_response_is_recreated_without_call(self):
        for mode in ('readme', 'condition'):
            with self.subTest(mode=mode):
                _, runner, run, result = self.fixture(mode, outage='provider')
                with patch.object(evaluation_program_generation, 'save_generation',
                                  side_effect=KeyboardInterrupt('receipt interruption')):
                    with self.assertRaises(KeyboardInterrupt):
                        run()
                self.assertFalse((result.parent / 'round_00/generation.json').exists())
                before = list(result.parent.glob('round_*/provider_*/process.json'))
                run()
                self.assertEqual('fail', load(result)['status'])
                self.assertEqual(before, list(result.parent.glob('round_*/provider_*/process.json')))

    def test_legacy_input_changes_during_provider_or_checker_never_publish(self):
        for phase in ('provider', 'checker'):
            with self.subTest(phase=phase):
                fixture = legacy_fixtures.EvaluationTests(methodName='runTest')
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                with redirect_stdout(io.StringIO()):
                    study = fixture.freeze()
                output = fixture.root / 'run'
                name = '_request_solution' if phase == 'provider' else '_checked_execution'
                original = getattr(legacy, name)
                def mutate(*args, **kwargs):
                    value = original(*args, **kwargs)
                    (fixture.root / 'source.txt').write_text('source changed during call')
                    return value
                with patch.object(legacy, name, side_effect=mutate):
                    with self.assertRaisesRegex(ValueError, 'inputs changed'):
                        legacy.run_evaluation(study, output, max_units=1)
                self.assertFalse(list(output.glob('*/*/result.json')))
                self.assertFalse((output / 'report.json').exists())
                self.assertTrue(list(output.glob('*/*/round_*/provider_*/process.json')))
                executions = list(output.glob('*/*/round_*/execution_*/process.json'))
                self.assertEqual(0 if phase == 'provider' else 1, len(executions))

    def test_launch_error_has_durable_process_evidence_and_cached_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'attempt'
            request = {'prompt': 'synthetic request'}
            command = [str(Path(directory) / 'missing-executable')]
            result = invoke(command, request, output, 1)
            self.assertEqual('adapter_error', result['status'])
            self.assertIsNone(result['returncode'])
            self.assertEqual('FileNotFoundError', result['launch_error']['type'])
            self.assertEqual(result, load(output / 'process.json'))
            self.assertIn('FileNotFoundError', (output / 'stderr.txt').read_text())
            self.assertEqual(result, invoke(command, request, output, 1))

    def test_missing_provider_executable_stops_at_transport_budget_with_report(self):
        fixture = legacy_fixtures.EvaluationTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.config['readme_evaluation']['model']['command'] = [str(fixture.root / 'missing-provider')]
        fixture.write_config()
        with redirect_stdout(io.StringIO()):
            study = fixture.freeze()
            output = fixture.root / 'run'
            summary = legacy.run_evaluation(study, output)
        self.assertFalse(summary['all_complete'])
        row = load(next(output.glob('*/*/result.json')))
        self.assertEqual('provider_pending', row['status'])
        self.assertEqual(2, row['resources']['provider_calls'])
        processes = list(output.glob('*/*/round_*/provider_*/process.json'))
        self.assertEqual(2, len(processes))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(summary, legacy.run_evaluation(study, output))
        self.assertEqual(processes, list(output.glob('*/*/round_*/provider_*/process.json')))


if __name__ == '__main__':
    unittest.main()
