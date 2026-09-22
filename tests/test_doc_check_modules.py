"""Offline compatibility/parity checks for the native documentation-check split.

Only synthetic files and mocked providers/processes are used. These tests are
self-contained: archived source is not needed to run the regression suite.
"""
from contextlib import ExitStack, redirect_stderr
import inspect
import io
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal import doc_checks, doc_check_execution, doc_check_provenance
from aideal.config import load_config
from aideal.readme_agent import ApiEntry


HELPERS = (
    '_sha256_files', '_comprehension_fingerprint_components', '_checkpoint_row_reusable',
    'form_check', '_load_manifest', '_shared_doc_text', '_markdown_chunks',
    '_relevant_original_texts', '_relevant_doc_inventory',
    '_comprehension_inventory', '_build_catalogue_context', '_resolve_class_context',
    'comprehension_check', '_fill_scaffold', '_strip_fences', '_kind_of',
    '_validate_sample_data', '_discover_fixtures', '_base_type', '_consumed_type_counts',
    '_useful_readers', '_drop_unconsumed_lines', '_resolve_preamble', '_resolve_io_hints',
    '_execute_sample_data', '_classify_error_py', '_classify_error_java', '_classify_error',
    '_owner_map', '_receiver_hint', '_codebase_frames', '_comprehension_execute',
    '_normalize', 'completeness_check', 'puzzle_check',
)


class DocCheckModuleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-doc-check-parity-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'configs').mkdir()
        (self.root / 'docs').mkdir()
        (self.root / 'runtime').mkdir()
        (self.root / 'runtime/synthetic.jar').write_bytes(b'not an executable library')
        (self.root / 'source.py').write_text('def f(x):\n    return x\n')
        (self.root / 'README.md').write_text('# Library\nUse `f(1)`.\n')
        (self.root / 'docs/LLM_readme.md').write_text(
            '## API Test: `f`\n### Goal\nReturn the input.\n'
            '### Prompt Snippet\nCall `f(1)`.\n')
        (self.root / 'scaffold.py').write_text('# AIDEAL_DATA_BINDINGS\n# START\n# END\n')
        config = {
            'project': {'name': 'synthetic', 'language': 'Python'},
            'codebase': {'source_globs': ['source.py']},
            'files': {'original_readme': 'README.md'},
            'models': {
                'registry': {'fake': {'provider': 'synthetic', 'model': 'no-provider'}},
                'roles': {'audience': 'fake', 'author': 'fake'},
            },
            'checks': {'required_sections': ['Goal', 'Prompt Snippet']},
            'comprehension': {'execute': {
                'command': 'synthetic {test_file}', 'scaffold': 'scaffold.py',
                'region': ['# START', '# END'], 'work_dir': 'work',
                'test_filename': 'Generated.py', 'success_marker': 'DONE',
                'spark_jars': 'runtime/*.jar', 'max_fix_rounds': 1,
                'output_dir': str(self.root / 'output'), 'local_uris': False,
            }},
            'puzzle': {'command': 'synthetic --docs {api_doc} {runner_args}',
                       'runner_args': ['--name', 'two words']},
        }
        path = self.root / 'configs/aideal.yaml'
        path.write_text(yaml.safe_dump(config))
        self.cfg = load_config(path)

    def helper_result(self, name, *args, **kwargs):
        return getattr(doc_checks, name)(*args, **kwargs)

    def test_facade_keeps_shared_helpers_and_entrypoint_signature(self):
        for name in HELPERS:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(doc_checks, name)))
        self.assertEqual('raster_tif', doc_checks._FIXTURE_TYPES['.tif'])
        self.assertEqual({'.tif', '.tiff'}, doc_checks._SUFFIXES_FOR_TYPE['raster_tif'])
        self.assertIs(doc_checks._comprehension_execute, doc_check_execution._comprehension_execute)
        parameters = inspect.signature(doc_checks.comprehension_check).parameters
        self.assertEqual(['cfg', 'sample', 'seed', 'doc_source', 'execute', 'show_code', 'api',
                          'class_context', 'rerun_failed', 'max_fix_rounds', 'resume',
                          'timeout_s', 'full_doc', 'doc_scope', 'manifest'], list(parameters))
        self.assertIsNone(parameters['max_fix_rounds'].default)
        self.assertIs(parameters['resume'].default, False)

    def test_markdown_manifest_and_inventory_preserve_document_exposure(self):
        text = '# Intro\ntext\n## Call\n```python\n# not a heading\nf(1)\n```\n## End\ntail'
        chunks = self.helper_result('_markdown_chunks', text)
        self.assertEqual(3, len(chunks))
        self.assertIn('# not a heading', chunks[1])
        self.assertEqual(['f'], [entry.name for entry in self.helper_result('_comprehension_inventory', self.cfg, 'aideal')[0]])
        full, shared, error = self.helper_result('_comprehension_inventory', self.cfg, 'original', manifest=['f'], full_doc=True)
        self.assertIsNone(error)
        self.assertEqual('', full[0].body)
        self.assertIn('Use `f(1)`', shared)
        self.assertTrue(self.helper_result('form_check', self.cfg)['passed'])
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(['f', 'f']))
        self.assertEqual(['f'], self.helper_result('_load_manifest', self.cfg, 'manifest.json'))
        manifest.write_text(json.dumps(['not_public']))
        with self.assertRaisesRegex(ValueError, 'outside the configured public surface'):
            doc_checks._load_manifest(self.cfg, 'manifest.json')
        self.assertEqual('===== README.md =====\n# Library\nUse `f(1)`.',
                         self.helper_result('_relevant_original_texts', self.cfg, ['f'], 80)['f'])
        self.assertTrue(self.helper_result('completeness_check', self.cfg)['passed'])

    def test_scaffolds_fixtures_and_receiver_hints_preserve_contract(self):
        scaffold = 'def run():\n    # START\n    old()\n    # END\n    path="{{PATH}}"'
        rendered = self.helper_result('_fill_scaffold', scaffold, 'f()\nprint(1)', ['# START', '# END'], {'PATH': '/x'})
        self.assertIn('    f()\n    print(1)', rendered)
        self.assertNotIn('old()', rendered)
        self.assertIn('path="/x"', rendered)
        self.assertEqual('f()', self.helper_result('_strip_fences', '```python\nimport x\nf()\n```', strip_imports=True))
        fixtures = self.root / 'fixtures'
        fixtures.mkdir()
        raster = fixtures / 'a.tif'
        raster.write_bytes(b'synthetic fixture')
        self.assertEqual(str(raster), self.helper_result('_discover_fixtures', self.cfg, {})['raster_tif'])
        self.assertTrue(self.helper_result('_validate_sample_data', {'vector_shapefile': str(raster)}))
        data, description, warnings = self.helper_result('_execute_sample_data', self.cfg, {'local_uris': False})
        self.assertEqual([], warnings)
        self.assertEqual(str(raster), data['raster_tif'])
        self.assertIn('output_dir', description)
        self.assertIn('STATIC method', self.helper_result('_receiver_hint', 'f', {'f': ('Factory', 'static')}))
        self.assertEqual('RDD', self.helper_result('_base_type', 'pkg.RDD[Tile[Int]]'))
        self.assertEqual('val keep: RDD[Int] = f()', self.helper_result('_drop_unconsumed_lines',
            'val keep: RDD[Int] = f()\nval drop: Unknown = g()', {'RDD': 1}))
        self.assertEqual('literal', self.helper_result('_resolve_preamble', self.cfg, {'preamble': ' literal '}, {}))
        self.assertEqual('hint', self.helper_result('_resolve_io_hints', self.cfg, {'io_hints': ' hint '}, {}))

    def test_error_categories_and_source_frames_keep_exact_results(self):
        cases = [
            ('SyntaxError: invalid syntax', 1, 'python', 'compile'),
            ('ModuleNotFoundError: missing', 1, 'python', 'infra'),
            ('ImportError: cannot import name bad', 1, 'python', 'api-import'),
            ('Source.java:9: error: cannot find symbol', 1, 'java', 'compile'),
            ('java.lang.NoClassDefFoundError: absent/Thing', 1, 'java', 'infra'),
            ('Source.scala:2: error: not found', 1, 'scala', 'compile'),
            ('__ERR__ wrong\n at app.call(Source.scala:7)', 1, 'scala', 'runtime'),
            ('partial', 124, 'python', 'timeout'),
        ]
        for text, code, language, expected in cases:
            with self.subTest(language=language, text=text):
                self.assertEqual(expected, self.helper_result('_classify_error', text, code, '__ERR__', language)[0])
        self.assertEqual(['src/Source.scala:7', 'source.py:3'], self.helper_result('_codebase_frames',
            'at app.call(Source.scala:7)\nat app.call(Source.scala:7)\nFile "/tmp/source.py", line 3',
            {'Source.scala': 'src/Source.scala', 'source.py': 'source.py'}))
        self.assertTrue(self.helper_result('_checkpoint_row_reusable', {'experiment_fingerprint': 'x', 'status': 'pass'}, 'x'))
        self.assertFalse(self.helper_result('_checkpoint_row_reusable', {'experiment_fingerprint': 'x', 'error_category': 'llm-error'}, 'x'))

    def fingerprint_arguments(self):
        return dict(ex=self.cfg.comprehension['execute'], doc_source='aideal', doc_scope='entry',
                    max_fix_rounds=1, manifest_sha256='manifest', document_sha256='document',
                    scaffold_file=self.root / 'scaffold.py', sample_data={'output_dir': str(self.root / 'output')},
                    class_context=False, timeout=20)

    def test_fingerprint_keeps_inputs_and_tracks_all_split_implementation_files(self):
        arguments = self.fingerprint_arguments()
        before = doc_checks._comprehension_fingerprint_components(self.cfg, **arguments)
        self.assertEqual('document', before['document_sha256'])
        self.assertEqual('manifest', before['manifest_sha256'])
        self.assertEqual(1, before['source']['file_count'])
        self.assertEqual(0, before['fixtures']['file_count'])  # Output contents are not fixture inputs.
        captured = []
        real_hash = doc_check_provenance._sha256_files
        def capture(paths, root=None):
            captured.extend(paths)
            return real_hash(paths, root)
        with patch.object(doc_check_provenance, '_sha256_files', side_effect=capture):
            doc_checks._comprehension_fingerprint_components(self.cfg, **arguments)
        engine_directory = Path(doc_checks.__file__).parent
        expected = {p.name for pattern in ('doc_check_*.py', 'readme_*.py', 'api_*.py')
                    for p in engine_directory.glob(pattern)}
        expected.add('scaffold_generation.py')
        self.assertTrue(expected <= {p.name for p in captured})
        self.assertTrue(all((engine_directory / name).is_file() for name in expected))
        # Hash a temporary relocated package, then edit just a moved module.
        copied = self.root / 'copied_engine'
        copied.mkdir()
        for path in captured:
            if path.is_file() and path.parent == Path(doc_checks.__file__).parent:
                shutil.copy2(path, copied / path.name)
        with patch.object(doc_check_provenance, '__file__', str(copied / 'doc_check_provenance.py')):
            first = doc_checks._comprehension_fingerprint_components(self.cfg, **arguments)
            changed = copied / 'doc_check_inputs.py'
            changed.write_text(changed.read_text() + '\n# synthetic implementation change\n')
            second = doc_checks._comprehension_fingerprint_components(self.cfg, **arguments)
        self.assertNotEqual(first['engine']['sha256'], second['engine']['sha256'])

    def _mocked_native_run(self, module, outcome):
        shutil.rmtree(self.root / 'work', ignore_errors=True)
        self.cfg.error_log.unlink(missing_ok=True)
        generated = ['print("first")', 'print("fixed")']
        runs = [subprocess.CompletedProcess('synthetic', 0, 'DONE', '')]
        if outcome == 'repair':
            runs.insert(0, subprocess.CompletedProcess('synthetic', 1, '', 'ValueError: synthetic wrong result'))
        elif outcome == 'provider_failure':
            generated = [RuntimeError('synthetic provider outage')]
        elif outcome == 'timeout':
            runs = [subprocess.TimeoutExpired('synthetic', 1, output=b'partial', stderr=b'trace')]
        with ExitStack() as stack:
            stack.enter_context(redirect_stderr(io.StringIO()))
            provider = stack.enter_context(patch('aideal.llm.invoke_text', side_effect=generated))
            executor = stack.enter_context(patch('aideal.execution.run_command', side_effect=runs))
            stack.enter_context(patch('subprocess.run', side_effect=AssertionError('Unexpected external process')))
            stack.enter_context(patch.object(module, 'public_api_details', return_value=[]))
            stack.enter_context(patch.object(module, 'public_api_surface', return_value={'f'}))
            stack.enter_context(patch('aideal.readme_agent.public_api_details', return_value=[]))
            stack.enter_context(patch.object(module, 'new_run_id', return_value='synthetic-run'))
            stack.enter_context(patch('time.time', return_value=100.0))
            result = module._comprehension_execute(self.cfg,
                [ApiEntry('f', 'Return input', '', 'Documentation for f')], 0, 42, 'aideal',
                show_code=True, max_fix_rounds=1 if outcome == 'repair' else 0)
            prompts = [call.args for call in provider.call_args_list]
        checkpoint = [json.loads(line) for line in Path(result['run']['checkpoint']).read_text().splitlines()]
        self.assertEqual(result['run']['experiment_fingerprint'], checkpoint[0]['experiment_fingerprint'])
        components = result['run']['fingerprint_components']
        expected = hashlib.sha256(json.dumps(components, sort_keys=True,
            separators=(',', ':'), default=str).encode('utf-8')).hexdigest()
        self.assertEqual(expected, result['run']['experiment_fingerprint'])
        identity = json.loads((self.root / 'work/run_identity.json').read_text())
        self.assertEqual(components, identity['fingerprint_components'])
        self.assertEqual(expected, identity['experiment_fingerprint'])
        return result, prompts, executor.call_count

    def test_native_success_repair_timeout_and_provider_failure_keep_contract(self):
        for outcome in ('success', 'repair', 'timeout', 'provider_failure'):
            with self.subTest(outcome=outcome):
                result, prompts, calls = self._mocked_native_run(doc_check_execution, outcome)
                self.assertEqual(outcome in ('success', 'repair'), result['passed'])
                self.assertEqual(2 if outcome == 'repair' else 1, len(prompts))
                if outcome == 'provider_failure':
                    self.assertEqual(0, calls)
                    self.assertEqual('llm-error', result['metrics']['f']['error_category'])
                if outcome == 'timeout':
                    self.assertEqual('timeout', result['metrics']['f']['error_category'])

    def test_public_grading_and_puzzle_entrypoints_use_mocked_boundaries(self):
        with patch('aideal.profile.require_profile', return_value={}), \
             patch('aideal.llm.invoke_text', side_effect=['f(1)', 'PASS: documented']) as provider, \
             patch('aideal.execution.run_command', side_effect=AssertionError('Unexpected execution')):
            result = doc_checks.comprehension_check(self.cfg, sample=0, show_code=True)
            self.assertEqual(2, provider.call_count)
            self.assertTrue(result['passed'])
            self.assertEqual({'status': 'pass', 'code': 'f(1)'}, result['details']['f'])
        with patch('subprocess.run', return_value=subprocess.CompletedProcess('synthetic', 0, 'finished', '')) as runner, \
             patch('aideal.llm.invoke_text', side_effect=AssertionError('Unexpected model call')):
            result = doc_checks.puzzle_check(self.cfg, dry_run=True, memory='off')
            self.assertEqual(1, runner.call_count)
            self.assertTrue(result['passed'])
            self.assertIsNone(result['score'])
            self.assertIn('--dry-run', runner.call_args.args[0])
            self.assertIn('two words', runner.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
