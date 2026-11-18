"""Offline launcher checks with a synthetic library and mocked model responses.

The original-document path, profile gate, source scan, scaffold rendering,
local Python execution, checkpoints, and reports use the real implementation.
"""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
spec = importlib.util.spec_from_file_location('original_micro_launcher', ROOT / 'scripts/run_original_micro.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class OriginalMicroLauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-original-launcher-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.original = self.root / 'original'
        self.source = self.original / 'library'
        self.source.mkdir(parents=True)
        (self.original / 'configs').mkdir()
        (self.original / 'runtime').mkdir()
        (self.original / 'runtime/synthetic.jar').write_bytes(b'No Spark runtime is used in this Python test.')
        (self.source / 'example.py').write_text(
            'def f(x):\n    return x\n\ndef g(x):\n    return x + 1\n\ndef h(x):\n    return x + 2\n')
        (self.source / 'README.md').write_text(
            '# Original example library\n'
            'Call f(x) to return x, g(x) to add one, or h(x) to add two.\n')
        (self.original / 'scaffold.py').write_text(
            'import sys\n'
            f'sys.path.insert(0, {str(self.source)!r})\n'
            'from example import f, g, h\n'
            '# AIDEAL_DATA_BINDINGS\n# START\n# END\nprint("DONE")\n')
        profile = {
            'project': {'name': 'example', 'language': 'Python', 'description': 'Small integer operations.'},
            'domain': 'arithmetic', 'target_users': ['Python developers'],
            'use_cases': ['Add small integers'],
        }
        (self.original / 'configs/project_profile.yaml').write_text(yaml.safe_dump(profile))
        config = {
            'project': {'name': 'example', 'language': 'Python'},
            'codebase': {'source_globs': ['library/*.py']},
            'files': {'original_readme': 'library/README.md',
                      'project_profile': 'configs/project_profile.yaml'},
            'models': {'registry': {'original': {'provider': 'synthetic', 'model': 'original-model'}},
                       'roles': {'audience': 'original', 'author': 'original'}},
            'comprehension': {'execute': {
                'command': shlex.quote(sys.executable) + ' {test_file}',
                'scaffold': 'scaffold.py', 'region': ['# START', '# END'],
                'test_filename': 'Generated.py', 'work_dir': 'existing_execution',
                'max_fix_rounds': 4, 'success_marker': 'DONE',
                'spark_jars': 'runtime/*.jar', 'local_uris': False,
            }},
        }
        self.config = self.original / 'configs/aideal.yaml'
        self.config.write_text(yaml.safe_dump(config))
        self.manifest = self.original / 'manifest.json'
        self.manifest.write_text(json.dumps(['f', 'g', 'h']))
        self.library = {'base_config': str(self.config), 'manifest': str(self.manifest),
                        'source_link': {'name': 'library', 'target': str(self.source)}}
        self.destination = self.root / 'batch/example'
        self.model = 'synthetic-offline-model'
        self.original_files = {p: p.read_bytes() for p in self.original.rglob('*') if p.is_file()}
        # The launcher temporarily sets MPLCONFIGDIR. Restore the caller's environment.
        self.environment = patch.dict(os.environ, {'PYTHONDONTWRITEBYTECODE': '1'})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def assert_original_unchanged(self):
        current = {p: p.read_bytes() for p in self.original.rglob('*') if p.is_file()}
        self.assertEqual(self.original_files, current)

    def run_library(self, cfg, responses, sample=None):
        with redirect_stdout(io.StringIO()), \
             patch('aideal.llm.invoke_text', side_effect=responses) as provider:
            summary = launcher.run_library(cfg, self.destination, sample)
        result = json.loads((self.destination / 'result.json').read_text())
        return summary, result, provider

    def test_prepare_isolated_original_r0_and_rejects_changed_launch_settings(self):
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('Preparation cannot call a model')):
            cfg, names = launcher.prepare(self.library, self.destination, self.model, 1)
            self.assertEqual(['f', 'g', 'h'], names)
            self.assertEqual(self.source, (self.destination / 'library').resolve())
            self.assertEqual(self.destination, cfg.root)
            self.assertEqual(0, cfg.comprehension['execute']['max_fix_rounds'])
            self.assertTrue(cfg.comprehension['execute']['stop_on_provider_error'])
            self.assertFalse(cfg.comprehension['class_context'])
            self.assertEqual([self.source / 'README.md'], cfg.original_readme_files)
            self.assertEqual(self.destination / 'logs/error_log.jsonl', cfg.error_log)
            saved = (self.destination / 'configs/aideal.yaml').read_bytes()
            same, _ = launcher.prepare(self.library, self.destination, self.model, 1)
            self.assertEqual(cfg.raw, same.raw)
            for model, sample in ((self.model + '-changed', 1), (self.model, 2)):
                with self.subTest(model=model, sample=sample):
                    with self.assertRaisesRegex(ValueError, 'Prepared input changed'):
                        launcher.prepare(self.library, self.destination, model, sample)
            self.assertEqual(saved, (self.destination / 'configs/aideal.yaml').read_bytes())
        self.assert_original_unchanged()

    def test_r0_runs_once_and_resume_reuses_a_completed_failure(self):
        cfg, _ = launcher.prepare(self.library, self.destination, self.model, 1)
        summary, result, provider = self.run_library(cfg, ['raise ValueError("deliberate R0 failure")'], 1)
        self.assertEqual(1, provider.call_count)
        self.assertEqual('completed', summary['status'])
        self.assertEqual(0, summary['passes'])
        self.assertEqual(0, result['run']['max_fix_rounds'])
        self.assertEqual(1, len(result['metrics']))
        metric = next(iter(result['metrics'].values()))
        self.assertEqual(('fail', 1), (metric['status'], metric['attempts']))
        checkpoint = Path(result['run']['checkpoint'])
        before = checkpoint.read_bytes()
        summary, resumed, provider = self.run_library(cfg, [AssertionError('Finished R0 unit must not regenerate')], 1)
        self.assertEqual(0, provider.call_count)
        self.assertEqual('completed', summary['status'])
        self.assertEqual(1, resumed['run']['resumed_apis'])
        self.assertEqual(before, checkpoint.read_bytes())
        self.assertTrue((self.destination / 'REPORT.md').is_file())
        self.assert_original_unchanged()

    def test_provider_outage_is_incomplete_then_resumes_without_replacing_evidence(self):
        cfg, _ = launcher.prepare(self.library, self.destination, self.model, None)
        summary, result, provider = self.run_library(cfg, ['assert f(1) == 1', RuntimeError('offline provider outage')])
        self.assertEqual((2, 'incomplete', 1), (provider.call_count, summary['status'], summary['provider_errors']))
        self.assertEqual((3, 2), (summary['selected'], summary['recorded']))
        self.assertEqual({'f', 'g'}, set(result['metrics']))
        failed_dir = Path(result['metrics']['g']['attempt_evidence'][0])
        request = json.loads((failed_dir / 'request.json').read_text())
        self.assertEqual(provider.call_args.args[1:], (request['system'], request['user']))
        self.assertIn('Original example library', request['user'])
        earlier = {p: p.read_bytes() for p in (self.destination / 'execution').glob('run_*/attempt_*/*')
                   if p.is_file()}
        summary, resumed, provider = self.run_library(cfg, ['assert g(1) == 2', 'assert h(1) == 3'])
        self.assertEqual((2, 'completed', 3), (provider.call_count, summary['status'], summary['passes']))
        self.assertEqual(1, resumed['run']['resumed_apis'])
        self.assertEqual('attempt_0002', Path(resumed['metrics']['g']['attempt_evidence'][0]).name)
        for path, contents in earlier.items():
            self.assertEqual(contents, path.read_bytes())
        rows = [json.loads(line) for line in Path(resumed['run']['checkpoint']).read_text().splitlines()]
        self.assertEqual(['f', 'g', 'g', 'h'], [row['name'] for row in rows])
        self.assert_original_unchanged()


if __name__ == '__main__':
    unittest.main()
