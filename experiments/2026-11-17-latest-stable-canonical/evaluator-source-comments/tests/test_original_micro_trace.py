"""Trace the actual native repair loop, prompt feedback and checkpoint reuse."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


class OriginalMicroTraceTests(unittest.TestCase):
    def test_round_limits_feedback_execution_resume_and_pause(self):
        for repairs, fail, pause in ((0, False, False), (1, False, False),
                                     (2, False, True), (2, True, False)):
            with self.subTest(repairs=repairs, fail=fail), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'trace'
                command = [sys.executable, str(ROOT / 'scripts/trace_original_micro.py'),
                           '--output', str(output), '--repairs', str(repairs)]
                command += ['--fail'] if fail else []
                command += ['--pause'] if pause else []
                options = dict(text=True, capture_output=True, timeout=30,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                process = subprocess.run(command, input='\n' * 20, **options)
                self.assertEqual(0, process.returncode, process.stdout + process.stderr)
                result = json.loads((output / 'result.json').read_text())
                metric = result['metrics']['double']
                passed = repairs == 2 and not fail
                self.assertEqual('pass' if passed else 'fail', metric['status'])
                self.assertEqual(repairs + 1, metric['attempts'])
                self.assertEqual(repairs, result['run']['max_fix_rounds'])
                self.assertEqual(2 if passed else None, metric['pass_round'])
                resumed = json.loads((output / 'resume_result.json').read_text())
                self.assertEqual(1, resumed['run']['resumed_apis'])
                attempts = sorted((output / 'execution/run_double').glob('attempt_*'))
                self.assertEqual(repairs + 1, len(attempts))
                transcript = (output / 'trace.log').read_text()
                for number, attempt in enumerate(attempts):
                    request = json.loads((attempt / 'request.json').read_text())
                    self.assertEqual(number, request['round'])
                    self.assertIn(request['system'], transcript)
                    self.assertIn(request['user'], transcript)
                    self.assertIn(f'R{number} actual execution command', transcript)
                    if number:
                        self.assertIn('expected 5, got 6', request['user'])
                        self.assertLess(transcript.index(f'R{number-1} standard error'),
                                        transcript.index(f'3. R{number} fixer input'))
                    if number == 2:
                        self.assertIn('expected 7, got 6', request['user'])
                    self.assertTrue((attempt / 'Generated.py').is_file())
                self.assertIn('OFFLINE DEMO', transcript)
                self.assertIn('Unavailable: no provider call', transcript)
                self.assertIn('for attempt in range(1 + max_fix_rounds)', transcript)
                self.assertIn('aideal.doc_check_execution._comprehension_execute', transcript)
                self.assertIn('comprehension_write_exec.md', transcript)
                if pause:
                    self.assertIn('[Pause]', transcript)
                self.assertIn('__CHECK__ double(3)=6' if passed else 'AssertionError',
                              (attempts[-1] / ('stdout.txt' if passed else 'stderr.txt')).read_text())
                original = (output / 'result.json').read_bytes()
                repeated = subprocess.run(command, **options)
                self.assertNotEqual(0, repeated.returncode)
                self.assertIn('existing results are never overwritten', repeated.stderr)
                self.assertEqual(original, (output / 'result.json').read_bytes())


class OriginalMicroLiveTraceTests(unittest.TestCase):
    """Exercise the live control path offline, using the real native Python runner."""

    def setUp(self):
        # Reuse the launcher's small library fixture rather than local RDPro jars.
        fixture_spec = importlib.util.spec_from_file_location(
            'trace_launcher_fixture', ROOT / 'tests/test_original_micro_launcher.py')
        fixture_module = importlib.util.module_from_spec(fixture_spec)
        fixture_spec.loader.exec_module(fixture_module)
        self.fixture = fixture_module.OriginalMicroLauncherTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.launcher = fixture_module.launcher
        trace_spec = importlib.util.spec_from_file_location(
            'tested_original_micro_trace', ROOT / 'scripts/trace_original_micro.py')
        self.trace = importlib.util.module_from_spec(trace_spec)
        trace_spec.loader.exec_module(self.trace)
        self.catalog = self.fixture.root / 'catalog.yaml'
        self.catalog.write_text(yaml.safe_dump({'rdpro': self.fixture.library}))
        self.output = self.fixture.root / 'trace'

    def run_live_trace(self, response):
        """Replace only preparation inputs and the remote response, preserving execution."""
        calls = []
        original_prepare = self.launcher.prepare
        library = self.fixture.library

        def prepare_fixture(spec, *args, **kwargs):
            self.assertEqual(library, spec)
            return original_prepare(library, *args, **kwargs)

        def model_response(spec, system, user):
            calls.append((spec, system, user))
            if isinstance(response, Exception):
                raise response
            return response

        args = SimpleNamespace(library='rdpro', api='f', repairs=2, live=True,
                               model='offline-test-gemini', fail=False, pause=False,
                               catalog=self.catalog)
        transcript = io.StringIO()
        with patch.object(self.trace, 'prepare', new=prepare_fixture), \
             patch.object(self.trace, 'invoke_text', new=model_response), \
             patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-google-placeholder',
                                     'GEMINI_API_KEY': 'test-gemini-placeholder',
                                     'AIDEAL_GOOGLE_MAX_RETRIES': '1'}), \
             redirect_stdout(transcript), redirect_stderr(transcript):
            status = self.trace.walkthrough(self.output, args)
        self.fixture.assert_original_unchanged()
        return status, calls, transcript.getvalue()

    def test_live_early_pass_uses_one_request_and_reuses_checkpoint(self):
        response = ('import os\n'
                    'assert os.getenv("GOOGLE_API_KEY") is None\n'
                    'assert os.getenv("GEMINI_API_KEY") is None\n'
                    'assert f(3) == 3\nprint("__CHECK__ f(3)=3")')
        status, calls, transcript = self.run_live_trace(response)
        self.assertEqual(0, status)
        self.assertEqual(1, len(calls))
        result = json.loads((self.output / 'result.json').read_text())
        metric = result['metrics']['f']
        self.assertEqual(('pass', 0, 1),
                         (metric['status'], metric['pass_round'], metric['attempts']))
        self.assertTrue(result['run']['complete'])
        self.assertEqual({'f'}, set(result['metrics']))
        attempts = sorted((self.output / 'execution/run_f').glob('attempt_*'))
        self.assertEqual(1, len(attempts))
        request = json.loads((attempts[0] / 'request.json').read_text())
        self.assertEqual(calls[0][1:], (request['system'], request['user']))
        self.assertEqual((0, 'google', 'offline-test-gemini'),
                         (request['round'], request['provider'], request['model']))
        self.assertEqual(response, (attempts[0] / 'response.txt').read_text())
        self.assertTrue((attempts[0] / 'execution.json').is_file())
        self.assertTrue((attempts[0] / 'trace_provider.json').is_file())
        self.assertIn('__CHECK__ f(3)=3', (attempts[0] / 'stdout.txt').read_text())
        self.assertIn(request['user'], transcript)
        self.assertNotIn('test-google-placeholder', transcript)
        self.assertNotIn('test-gemini-placeholder', transcript)
        resumed = json.loads((self.output / 'resume_result.json').read_text())
        self.assertEqual(1, resumed['run']['resumed_apis'])
        summary = json.loads((self.output / 'summary.json').read_text())
        self.assertEqual((1, 'passed at R0'), (summary['requests'], summary['stop_reason']))

    def test_live_provider_failure_saves_pending_evidence_without_execution_or_retry(self):
        status, calls, transcript = self.run_live_trace(RuntimeError('synthetic provider outage'))
        self.assertEqual((2, 1), (status, len(calls)))
        result = json.loads((self.output / 'result.json').read_text())
        self.assertFalse(result['run']['complete'])
        self.assertTrue(result['run']['stopped_on_provider_error'])
        self.assertEqual('llm-error', result['metrics']['f']['error_category'])
        attempts = sorted((self.output / 'execution/run_f').glob('attempt_*'))
        self.assertEqual(1, len(attempts))
        request = json.loads((attempts[0] / 'request.json').read_text())
        self.assertEqual(calls[0][1:], (request['system'], request['user']))
        provider = json.loads((attempts[0] / 'provider.json').read_text())
        self.assertEqual('error', provider['status'])
        self.assertIn('synthetic provider outage', provider['error'])
        self.assertTrue((attempts[0] / 'trace_provider.json').is_file())
        for absent in ('response.txt', 'Generated.py', 'execution.json', 'command.txt'):
            self.assertFalse((attempts[0] / absent).exists())
        self.assertFalse((self.output / 'resume_result.json').exists())
        summary = json.loads((self.output / 'summary.json').read_text())
        self.assertFalse(summary['complete'])
        self.assertIsNone(summary['score_with_infra'])
        self.assertEqual(1, summary['requests'])
        self.assertIn('No automatic retry', transcript)

    def test_prepare_trace_modes_bind_one_api_and_repairs(self):
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Preparation cannot call a model')):
            for mode, provider, model in (('trace-mock', 'mock', 'offline-rdpro-trace'),
                                          ('trace-live', 'google', 'offline-test-gemini')):
                destination = self.fixture.root / mode
                cfg, names = self.launcher.prepare(
                    self.fixture.library, destination, 'offline-test-gemini', None,
                    api='g', max_fix_rounds=2, mode=mode)
                self.assertEqual(['g'], names)
                self.assertEqual(['g'], json.loads((destination / 'inputs/api_manifest.json').read_text()))
                identity = json.loads((destination / 'launch.json').read_text())
                self.assertEqual(('g', mode, 2), (identity['api'], identity['mode'], identity['repairs']))
                self.assertEqual(2, cfg.comprehension['execute']['max_fix_rounds'])
                selected = cfg.model_for_role('audience')
                self.assertEqual((provider, model), (selected.provider, selected.model))
                with self.assertRaisesRegex(ValueError, 'Prepared input changed'):
                    self.launcher.prepare(self.fixture.library, destination, 'offline-test-gemini', None,
                                          api='f', max_fix_rounds=2, mode=mode)
        self.fixture.assert_original_unchanged()

    def test_prepare_rejects_missing_runtime_and_invalid_selection_before_writes(self):
        missing = {**self.fixture.library, 'runtime_artifacts': [str(self.fixture.root / 'absent.jar')]}
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Preparation cannot call a model')):
            with self.assertRaisesRegex(ValueError, 'Missing runtime artifacts'):
                self.launcher.prepare(missing, self.output, 'offline-test-gemini', None,
                                      api='f', max_fix_rounds=2, mode='trace-live')
            self.assertFalse(self.output.exists())
            with self.assertRaisesRegex(ValueError, 'not in the configured manifest'):
                self.launcher.prepare(self.fixture.library, self.output, 'offline-test-gemini', None,
                                      api='not_an_api', max_fix_rounds=2, mode='trace-live')
            self.assertFalse(self.output.exists())
            with self.assertRaisesRegex(ValueError, 'sample=None'):
                self.launcher.prepare(self.fixture.library, self.output, 'offline-test-gemini', 1,
                                      api='f', max_fix_rounds=2, mode='trace-live')
            self.assertFalse(self.output.exists())
        self.fixture.assert_original_unchanged()


if __name__ == '__main__':
    unittest.main()
