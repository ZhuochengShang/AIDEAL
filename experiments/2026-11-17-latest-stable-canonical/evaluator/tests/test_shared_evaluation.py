"""Cross-protocol safety and context checks for the shared execution lifecycle."""
from contextlib import redirect_stdout
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_evaluation as readme_fixtures
import test_condition_evaluation as condition_fixtures
from workflow import evaluation, condition_evaluation
from workflow.ablation import load
from workflow.evaluation_program_generation import rounds


class SharedEvaluationTests(unittest.TestCase):
    def fixture(self, mode):
        factory = readme_fixtures.EvaluationTests if mode == 'readme' else condition_fixtures.ConditionEvaluationTests
        fixture = factory(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        if mode == 'readme':
            return fixture, evaluation, evaluation.run_evaluation, 'Original README'
        cfg = fixture.cfg['condition_evaluation']
        cfg['design'] = 'refactor_pair'
        cfg['conditions'] = {arm: cfg['conditions'][arm] for arm in ('original', 'refactor_only')}
        fixture.write_config()
        return fixture, condition_evaluation, condition_evaluation.run_conditions, 'original'

    def test_saved_preparation_imports_share_canonical_implementations(self):
        aliases = [('condition_setup', 'evaluation_freeze', 'read_condition_config'),
                   ('condition_inputs', 'evaluation_inputs', 'bind_command')]
        for old_name, current_name, function in aliases:
            with self.subTest(alias=old_name):
                old = importlib.import_module('workflow.' + old_name)
                current = importlib.import_module('workflow.' + current_name)
                self.assertIs(old, current)
                with patch.object(old, function) as replacement:
                    self.assertIs(replacement, getattr(current, function))

    def test_changed_shared_runner_rejects_both_protocols_before_commands(self):
        for mode in ('readme', 'condition'):
            with self.subTest(mode=mode), redirect_stdout(io.StringIO()):
                fixture, module, run, arm = self.fixture(mode)
                study = fixture.freeze()
                copied = fixture.root / 'controller-copy'
                shutil.copytree(Path(evaluation.__file__).parent, copied / 'workflow',
                                ignore=shutil.ignore_patterns('__pycache__'))
                shared = copied / 'workflow/evaluation_runner.py'
                shared.write_text(shared.read_text() + '\n# Synthetic controller edit.\n')
                output = fixture.root / 'copy-run'
                script = '''import importlib, json, sys
from pathlib import Path
from unittest.mock import patch
module = importlib.import_module(sys.argv[1])
with patch('workflow.evaluation_program_generation.invoke', side_effect=AssertionError('Unexpected provider call')) as provider, \\
     patch('workflow.evaluation_freeze.invoke', side_effect=AssertionError('Unexpected checker call')) as checker:
    try:
        getattr(module, sys.argv[2])(sys.argv[3], sys.argv[4], max_units=1)
    except Exception as error:
        result = {'type':type(error).__name__, 'message':str(error)}
    else:
        result = {'type':None, 'message':''}
    result.update(calls=provider.call_count+checker.call_count, output_exists=Path(sys.argv[4]).exists())
print(json.dumps(result))
'''
                process = subprocess.run([sys.executable, '-c', script, module.__name__, run.__name__,
                                          str(study), str(output)], cwd=copied, text=True, capture_output=True,
                                         env=dict(os.environ, PYTHONPATH=str(copied), PYTHONDONTWRITEBYTECODE='1'),
                                         timeout=15)
                self.assertEqual(0, process.returncode, process.stderr)
                result = json.loads(process.stdout)
                self.assertEqual('ValueError', result['type'], result)
                self.assertIn('controller', result['message'].lower())
                self.assertEqual(0, result['calls'])
                self.assertFalse(result['output_exists'])

    def test_output_review_hold_blocks_both_protocols_before_provider_or_output(self):
        for mode in ('readme', 'condition'):
            with self.subTest(mode=mode), redirect_stdout(io.StringIO()):
                fixture, module, run, arm = self.fixture(mode)
                study = fixture.freeze()
                parent = fixture.root / 'separate-output'
                parent.mkdir()
                (parent / 'REVIEW_HOLD.json').write_text('{"reason":"Review this output first"}')
                output = parent / 'run'
                with patch.object(module, '_request_solution') as provider:
                    with self.assertRaisesRegex(ValueError, 'paused for user code review'):
                        run(study, output, condition=arm)
                    provider.assert_not_called()
                self.assertFalse(output.exists())

    def test_readme_distilled_receipt_is_replayed_not_only_hash_checked(self):
        with redirect_stdout(io.StringIO()):
            fixture, module, run, arm = self.fixture('readme')
            cfg = fixture.config['readme_evaluation']
            cfg['common'].update(repair_context='distilled', max_snippet_fixes=1, repair_max_output_tokens=77)
            fixture.write_config()
            study = fixture.freeze()
            output = fixture.root / 'run'
            run(study, output, condition=arm, max_units=1)
            result = next(output.glob('*/*/result.json'))
            receipt = result.parent / 'round_01/repair_context.json'
            self.assertTrue(receipt.exists())
            request = load(next((result.parent / 'round_01').glob('provider_*/request.json')))
            self.assertEqual(77, request['max_output_tokens'])
            # Complete the remaining unit so a normal resume has no outstanding work.
            summary = run(study, output, condition=arm)
            with patch.object(module, '_request_solution') as provider:
                self.assertEqual(summary, run(study, output, condition=arm))
                provider.assert_not_called()
            value = load(receipt)
            value['code_truncated'] = not value['code_truncated']
            receipt.write_text(json.dumps(value))
            row = load(result)
            row['round_evidence'] = rounds(result.parent.resolve())
            result.write_text(json.dumps(row))
            with patch.object(module, '_request_solution') as provider:
                with self.assertRaisesRegex(ValueError, 'repair context differs from the frozen prompt'):
                    run(study, output, condition=arm)
                provider.assert_not_called()

    def test_native_diagnostic_reaches_repair_without_external_hint_retrieval(self):
        with redirect_stdout(io.StringIO()):
            fixture, module, run, arm = self.fixture('condition')
            cfg = fixture.cfg['condition_evaluation']
            cfg['schema_version'] = 3
            marker = '[AIDEAL fix:numeric_input] Pass a numeric argument.'
            fixture.adapter.write_text(fixture.adapter.read_text().replace(
                'TypeError: expected numeric argument', 'TypeError: expected numeric argument. ' + marker))
            fixture.model.write_text('import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({"code": '
                                     '"correct" if "[AIDEAL fix:numeric_input]" in r["prompt"] else "wrong", '
                                     '"usage":{"input_tokens":5,"output_tokens":2}}))\n')
            fixture.write_config()
            study = fixture.freeze()
            output = fixture.root / 'native-run'
            with patch('workflow.evaluation_legacy_hints.append_legacy_guidance', side_effect=AssertionError('No retrieval')):
                summary = run(study, output, condition=arm)
                for result in output.glob('*/*/result.json'):
                    self.assertEqual(1, load(result)['first_pass_round'])
                    first = load(next((result.parent / 'round_00').glob('provider_*/request.json')))
                    repair = load(next((result.parent / 'round_01').glob('provider_*/request.json')))
                    self.assertNotIn(marker, first['prompt'])
                    self.assertEqual(1, repair['prompt'].count(marker))
                    receipt = load(result.parent / 'round_01/context_exposure.json')
                    self.assertEqual(['numeric_input'], receipt['native_diagnostics']['observed_requirement_ids'])
                    self.assertFalse(receipt['native_diagnostics']['guidance_retrieved'])
                    self.assertEqual(0, receipt['hint_characters'])
                with patch.object(module, '_request_solution') as provider:
                    self.assertEqual(summary, run(study, output, condition=arm))
                    provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
