"""Synthetic preview/observer contracts; no model call or scientific program runs."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import yaml

ROOT = Path(os.environ.get('AIDEAL_TOOLKIT', str(Path(__file__).resolve().parents[1]))).resolve()
STAGE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor/aideal_engine/src'), str(ROOT / 'tests')]
import test_original_micro_launcher as fixture_module

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


class GenericTracePreviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.OriginalMicroLauncherTests()
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        with patch.dict(os.environ, {'AIDEAL_TOOLKIT': str(ROOT)}):
            self.trace = module('generic_trace_under_test', STAGE / 'scripts/trace_original_micro.py')
            self.view = module('generic_view_under_test', STAGE / 'scripts/trace_view.py')
        # The patch remains staged; unchanged source/template dependencies come
        # from the canonical toolkit solely for these synthetic unit checks.
        self.trace.build_trace_view = lambda roots, output: self.view.build_trace_view(roots, output, repo=ROOT)
        self.trace.snapshot_sources = lambda root: self.view.snapshot_sources(root, repo=ROOT)
        self.catalog = self.fixture.root / 'catalog.yaml'
        self.names = ('rdpro', 'mdanalysis', 'tslearn', 'mir_eval', 'thumbnailator', 'sedonadb')
        self.catalog.write_text(yaml.safe_dump({name: self.fixture.library for name in self.names}))

    def args(self, library, preview=True):
        return SimpleNamespace(library=library, api='f', repairs=2, live=not preview, preview=preview,
                               model='offline-contract-model', fail=False, pause=False, catalog=self.catalog)

    def test_all_six_catalog_keys_preview_native_exact_r0_without_provider_or_program(self):
        for name in self.names:
            with self.subTest(library=name):
                output = self.fixture.root / ('preview-' + name)
                calls = []
                def forbidden_provider(*args):
                    calls.append('provider'); raise AssertionError('No remote model')
                def forbidden_program(*args, **kwargs):
                    calls.append('program'); raise AssertionError('No program')
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                        patch.object(self.trace, 'invoke_text', new=forbidden_provider), \
                        patch.object(self.trace, 'run_command', new=forbidden_program):
                    self.assertEqual(0, self.trace.walkthrough(output, self.args(name)))
                self.assertEqual([], calls)
                request_paths = list(output.glob('execution/run_f/attempt_*/request.json'))
                self.assertEqual(1, len(request_paths))
                request = json.loads(request_paths[0].read_text())
                self.assertEqual((0, 'google', 'offline-contract-model'), (request['round'], request['provider'], request['model']))
                self.assertIn('Original example library', request['user'])
                self.assertIn('(none yet)', request['user'])
                for forbidden in ('provider.json', 'response.txt', 'execution.json', 'Generated.py'):
                    self.assertFalse((request_paths[0].parent / forbidden).exists())
                summary = json.loads((output / 'preview.json').read_text())
                self.assertEqual((0, 0), (summary['model_calls'], summary['snippet_executions']))
                self.assertFalse((output / 'result.json').exists())
                view = self.view.read_run(output)
                self.assertEqual('preview', view['mode'])
                self.assertFalse(view['attempts'][0]['pending'])
                self.assertIsNone(view['attempts'][0]['verdict'])
                self.assertTrue((output / 'TRACE.html').is_file())
        self.fixture.assert_original_unchanged()

    def test_generic_live_observer_uses_native_r0_r1_r2_with_full_evidence(self):
        output = self.fixture.root / 'generic-live-unit'
        process_calls = []
        def synthetic_process(command, **kwargs):
            number = len(process_calls); process_calls.append(command)
            return subprocess.CompletedProcess(command, 1 if number < 2 else 0,
                '' if number < 2 else '__CHECK__ f value=3\nDONE\n',
                'AssertionError: unit failure R' + str(number) if number < 2 else '')
        response = 'assert f(3) == 3\nprint("__CHECK__ f value=3")'
        provider_calls = []
        def synthetic_provider(*args):
            provider_calls.append(args); return response
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                patch.object(self.trace, 'invoke_text', new=synthetic_provider), \
                patch.object(self.trace, 'run_command', new=synthetic_process):
            self.assertEqual(0, self.trace.walkthrough(output, self.args('sedonadb', preview=False)))
        self.assertEqual(3, len(provider_calls))
        result = json.loads((output / 'result.json').read_text())
        self.assertEqual(2, result['metrics']['f']['pass_round'])
        view = self.view.read_run(output)
        self.assertEqual([0, 1, 2], [a['round'] for a in view['attempts']])
        for number, attempt in enumerate(view['attempts']):
            self.assertEqual(response, attempt['response'])
            self.assertIn(response.splitlines()[0], attempt['program'])
            self.assertIsNotNone(attempt['execution'])
            if number: self.assertIn('unit failure R' + str(number - 1), attempt['request']['user'])
        self.fixture.assert_original_unchanged()

    def test_viewer_reads_configured_java_program_name(self):
        root = self.fixture.root / 'java-evidence'; attempt = root / 'execution/run_f/attempt_0001'
        attempt.mkdir(parents=True)
        (root / 'launch.json').write_text('{"api":"f","mode":"trace-live"}')
        (attempt / 'request.json').write_text('{"api":"f","round":0,"user":"exact user","system":"exact system"}')
        (attempt / 'ApiTest.java').write_text('class ApiTest { void run() {} }')
        observed = self.view.read_run(root)['attempts'][0]
        self.assertIn('class ApiTest', observed['program'])
        self.assertIn('ApiTest.java', [a['name'] for a in observed['artifacts']])

    def test_preview_accepts_native_default_test_filename(self):
        config = self.fixture.config
        value = yaml.safe_load(config.read_text())
        value['comprehension']['execute'].pop('test_filename')
        config.write_text(yaml.safe_dump(value))
        output = self.fixture.root / 'default-filename-preview'
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(0, self.trace.walkthrough(output, self.args('rdpro')))
        self.assertEqual(0, json.loads((output / 'preview.json').read_text())['snippet_executions'])

    def test_preview_does_not_read_a_supplied_nonexistent_key_file(self):
        output = self.fixture.root / 'preview-key-ignored'
        missing = self.fixture.root / 'this-private-key-does-not-exist'
        argv = ['trace_original_micro.py', '--library', 'sedonadb', '--api', 'f',
                '--catalog', str(self.catalog), '--preview', '--key-file', str(missing), '--output', str(output)]
        with patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(0, self.trace.main())
        self.assertFalse(missing.exists())
        self.assertEqual(0, json.loads((output / 'preview.json').read_text())['model_calls'])

    def test_live_key_file_is_loaded_without_printing_or_calling_a_provider(self):
        fake_key = 'bounded-unit-placeholder-not-a-real-key'
        key_file = self.fixture.root / 'private-test-key.txt'; key_file.write_text(fake_key + '\n')
        output = self.fixture.root / 'fake-live-no-calls'
        argv = ['trace_original_micro.py', '--library', 'sedonadb', '--api', 'f',
                '--catalog', str(self.catalog), '--live', '--key-file', str(key_file), '--output', str(output)]
        observed = []
        def no_calls(root, args):
            observed.append(os.environ['GOOGLE_API_KEY'])
            return 0
        transcript = io.StringIO()
        with patch.object(sys, 'argv', argv), patch.dict(os.environ, {'GOOGLE_API_KEY': '', 'GEMINI_API_KEY': ''}), \
                patch.object(self.trace, 'walkthrough', new=no_calls), redirect_stdout(transcript), redirect_stderr(transcript):
            self.assertEqual(0, self.trace.main())
        self.assertEqual([fake_key], observed)
        self.assertNotIn(fake_key, transcript.getvalue())
        self.assertNotIn(fake_key, (output / 'trace.log').read_text())

    def test_live_rejects_empty_or_multiline_key_without_disclosing_it(self):
        key_file = self.fixture.root / 'invalid-test-key.txt'
        for value in ('', 'first-private-placeholder\nsecond-private-placeholder', 'embedded whitespace'):
            key_file.write_text(value)
            argv = ['trace_original_micro.py', '--library', 'sedonadb', '--api', 'f', '--live',
                    '--key-file', str(key_file), '--output', str(self.fixture.root / 'unused')]
            errors = io.StringIO()
            with patch.object(sys, 'argv', argv), redirect_stderr(errors), \
                    patch.object(self.trace, 'walkthrough', side_effect=AssertionError('No calls')):
                with self.assertRaises(SystemExit) as stopped: self.trace.main()
            self.assertEqual(2, stopped.exception.code)
            if value: self.assertNotIn(value, errors.getvalue())


if __name__ == '__main__': unittest.main()
