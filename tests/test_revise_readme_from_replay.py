"""Tests exercise immutable evidence, selective D2 promotion and safe resume."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(os.environ.get('AIDEAL_TEST_ROOT', Path(__file__).resolve().parents[1]))
sys.path[:0] = [str(ROOT), str(ROOT / 'vendor/aideal_engine/src')]
operator = Path(os.environ.get('AIDEAL_OPERATOR_PATH', ROOT / 'scripts/revise_readme_from_replay.py'))
if not operator.exists():
    operator = Path(__file__).with_name('revise_readme_from_replay.py')
spec = importlib.util.spec_from_file_location('revision', operator)
revision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revision)
from aideal.readme_recording import digest
from aideal.readme_format import api_storage_key


def entry(api, code='print(1)', trailing='\n\n'):
    return (f'## API Test: `{api}`\n\n### Signature\n```python\n(x):int\n```\n\n'
            f'### Valid Call Patterns\n```python\n{code}\n```' + trailing)


class RevisionTests(unittest.TestCase):
    def test_native_manifest_and_author_manifest(self):
        for manifest in [['a', 'b'], {'names': ['a', 'b']}, {'apis': ['a', 'b']}]:
            self.assertEqual(revision.manifest_names(manifest), ['a', 'b'])
        for manifest in [[], ['a', 'a'], {'apis': [{'id': 'a'}]}]:
            with self.assertRaises(ValueError):
                revision.manifest_names(manifest)

    def test_duplicate_entries_rejected(self):
        with self.assertRaises(ValueError):
            revision.entry_parts(entry('a') + entry('a'))

    def test_entry_parts_preserve_bytes(self):
        text = '# User introduction\n\n' + entry('a', trailing='\n\n\n') + entry('b', trailing='\n')
        head, parts = revision.entry_parts(text)
        self.assertEqual(head + ''.join(parts.values()), text)

    def test_example_rejects_missing_and_multiple_blocks(self):
        for text in ['## API Test: `a`', entry('a', '...'), entry('a') + '\n```python\npass\n```']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                revision.validation_example(text, ['Signature', 'Valid Call Patterns'])

    def test_source_window_records_exact_lines_and_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = 'class Owner:\n    def call(self, x):\n        return x\n'
            (root / 'library.py').write_text(content)
            windows, bindings = revision.source_context(SimpleNamespace(root=root),
                {'file': 'library.py', 'line': 2, 'owner': 'Owner'}, [])
            self.assertIn('2 |     def call', windows[0]['text'])
            self.assertEqual(bindings[str((root / 'library.py').resolve())], digest(content.encode()))
            (root / 'reference.qmd').write_text('title: ST_Test\nSELECT ST_Test(1);\n')
            reference, _ = revision.source_context(SimpleNamespace(root=root),
                {'file': 'reference.qmd', 'line': 1}, [])
            self.assertTrue(all(row['evidence_kind'] == 'upstream_reference' for row in reference))

    def test_changed_input_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'input'
            source.write_text('before')
            launch = {'bindings': {str(source): digest(source.read_bytes())}}
            source.write_text('after')
            with self.assertRaises(ValueError):
                revision.verify_inputs(launch)

    def test_runtime_profile_change_is_rejected(self):
        launch = {'bindings': {}, 'spec': {'runtime_profile': '/chosen/profile.json'},
                  'runtime_profile': [{'path': '/chosen/profile.json', 'sha256': 'before'}]}
        with patch.object(revision, 'runtime_receipts', return_value=[{
                'path': '/chosen/profile.json', 'sha256': 'after'}]), self.assertRaises(ValueError):
            revision.verify_inputs(launch)

    def test_blocked_runtime_stops_before_author_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            launch = {'bindings': {}, 'spec': {'library': 'mdanalysis',
                      'runtime_profile': '/chosen/profile.json', 'result': '/rescore/mdanalysis/result.json'}}
            with patch.object(revision, 'runtime_receipts', return_value=[]), \
                 patch('workflow.runtime_profile.load_runtime_profile', return_value={'profile': 'loaded'}), \
                 patch('workflow.runtime_profile.require_runtime_ready',
                       side_effect=ValueError('unresolved prerequisites')) as ready, \
                 patch('aideal.readme_recording.ReadmeCallRecorder.invoke') as author:
                with self.assertRaisesRegex(ValueError, 'unresolved prerequisites'):
                    revision.revise(SimpleNamespace(), launch, Path(temp))
                ready.assert_called_once_with({'profile': 'loaded'}, library='mdanalysis')
                author.assert_not_called()

    def test_wrong_api_heading_is_not_executed_or_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'inputs/entries').mkdir(parents=True)
            (root / 'inputs/D1.md').write_text(entry('a'))
            context = {'definition': {'signature': '(x):int'}, 'source_windows': [{'text': 'source'}],
                       'D1_entry': entry('a'), 'diagnose': {'system': 'system', 'user': 'user'},
                       'audience_context': 'fixture x=1'}
            (root / 'inputs/entries/a.json').write_text(json.dumps(context))
            adapter = root / 'adapter.py'
            adapter.write_text('def run_program_case(*args, **kwargs):\n'
                               '    raise AssertionError("Invalid heading reached execution")\n')
            launch = {'bindings': {}, 'spec': {'replay_adapter': str(adapter), 'result': 'unused'},
                      'model': 'gemini-3.1-flash-lite', 'identity_sha256': 'test',
                      'selected': ['a'], 'validation': 'native_only', 'study': 'same_bank_development'}
            cfg = SimpleNamespace(required_sections=['Signature', 'Valid Call Patterns'], comprehension={})
            with patch('aideal.prompts.load', return_value=('system', 'user')), \
                 patch('aideal.readme_recording.ReadmeCallRecorder.invoke', side_effect=[
                     'A proposed diagnosis', entry('wrong', 'assert True\nprint("__CHECK__ a 1")')]):
                result = revision.revise(cfg, launch, root)
            self.assertEqual(result['accepted'], 0)
            self.assertEqual(result['outcomes']['a']['status'], 'unchanged_rejected_structure')
            self.assertEqual((root / 'docs/D2.md').read_text(), entry('a'))

    def test_prepare_native_list_manifest_retains_exact_request_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'library.py').write_text('def call(x):\n    return x\n')
            old_case = root / 'old/attempt_0001'
            old_case.mkdir(parents=True)
            (old_case / 'execution.json').write_text('{}')
            (old_case / 'request.json').write_text(json.dumps({
                'system': 'Body statements only', 'user': entry('a').strip() + '\nPreloaded x=7'}))
            original = root / 'old/result.json'
            original.write_text(json.dumps({'details': {'a': {'scala_file': str(old_case.parent / 'ApiTest.py')}}}))
            replay = root / 'replay.json'
            replay.write_text(json.dumps({'mode': 'rescored_saved_programs', 'run': {'complete': True},
                'source_result': {'path': str(original), 'sha256': digest(original.read_bytes())},
                'details': {'a': {'status': 'fail', 'code': 'call(7)', 'error': 'observed failure'}}}))
            readme = root / 'D1.md'
            readme.write_text(entry('a'))
            manifest = root / 'manifest.json'
            manifest.write_text('["a"]')
            files = {}
            for name in ('config', 'replay_adapter', 'profile', 'prompt'):
                files[name] = root / name
                files[name].write_text(name)
            spec = {'result': str(replay), 'readme': str(readme), 'manifest': str(manifest),
                    **{name: str(files[name]) for name in ('config', 'replay_adapter')}}
            spec['project_profile'] = str(files['profile'])
            cfg = SimpleNamespace(root=root, language='Python', comprehension={}, raw={})
            definition = {'api_id': 'a', 'name': 'call', 'file': 'library.py', 'line': 1,
                          'signature': '(x):int'}
            with patch('aideal.config.load_config', return_value=cfg), \
                 patch('aideal.api_discovery.public_api_details', return_value=[definition]), \
                 patch('aideal.profile.profile_path', return_value=files['profile']), \
                 patch('aideal.prompts.prompt_path', return_value=files['prompt']), \
                 patch('aideal.prompts.load', return_value=('system', 'user')):
                _, launch = revision.prepare(spec, root / 'out')
                _, resumed = revision.prepare(spec, root / 'out')
                with patch.object(revision, 'runtime_receipts', return_value=[{
                        'path': str(files['profile']), 'sha256': digest(files['profile'].read_bytes())}]), \
                        self.assertRaises(ValueError):
                    revision.prepare(spec, root / 'mismatched-runtime')
            self.assertEqual(launch['identity_sha256'], resumed['identity_sha256'])
            self.assertEqual(cfg.raw['files']['project_profile'], str(files['profile'].resolve()))
            self.assertEqual(launch['selected'], ['a'])
            context = json.loads((root / 'out/inputs/entries/a.json').read_text())
            self.assertIn('Preloaded x=7', context['audience_context'])
            self.assertIn('Body statements only', context['audience_context'])
            self.assertNotIn('## API Test:', context['audience_context'])
            self.assertIn(str((root / 'out/inputs/entries/a.json').resolve()), launch['bindings'])
            self.assertIn(str((root / 'out/inputs/D1.md').resolve()), launch['bindings'])
            (root / 'out/inputs/entries/a.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Bound D2 input changed'):
                revision.verify_inputs(launch)

            definition['file'] = 'missing_source.py'
            with patch('aideal.config.load_config', return_value=cfg), \
                 patch('aideal.api_discovery.public_api_details', return_value=[definition]), \
                 patch('aideal.profile.profile_path', return_value=files['profile']), \
                 patch('aideal.prompts.prompt_path', return_value=files['prompt']):
                _, unsupported = revision.prepare(spec, root / 'unsupported')
            missing = json.loads((root / 'unsupported/inputs/entries/a.json').read_text())
            self.assertIn('unsupported', missing)
            self.assertEqual(unsupported['selected'], ['a'])

    def test_promotes_only_passing_example_and_resume_makes_no_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'inputs/entries').mkdir(parents=True)
            original = '# D1 intro\n\n' + entry('a') + entry('b') + entry('c', trailing='\n')
            (root / 'inputs/D1.md').write_text(original)
            for api in ('a', 'b'):
                context = {'api': api, 'definition': {'signature': '(x):int'},
                           'source_windows': [{'text': 'def call(x): return x'}],
                           'D1_entry': entry(api), 'diagnose': {'system': 'system', 'user': api},
                           'audience_context': 'Preloaded x=1'}
                (root / 'inputs/entries' / (api_storage_key(api) + '.json')).write_text(json.dumps(context))
            adapter = root / 'adapter.py'
            adapter.write_text('def run_program_case(result, api, output, code_override=None, runtime_profile=None):\n'
                               '    return {"status": "pass" if api == "a" else "fail", '
                               '"stdout_tail": "__CHECK__ " + api + " 1"}\n')
            launch = {'bindings': {}, 'spec': {'replay_adapter': str(adapter), 'result': 'unused.json'},
                      'model': 'gemini-3.1-flash-lite', 'identity_sha256': 'test',
                      'selected': ['a', 'b'], 'validation': 'native_only', 'study': 'same_bank_development'}
            cfg = SimpleNamespace(required_sections=['Signature', 'Valid Call Patterns'],
                                  comprehension={'execute': {'execution_context': 'fixture x=1'}})
            def author(_self, _spec, system, user, phase, api=None, **kwargs):
                return 'ROOT CAUSE: incorrect example' if phase == 'diagnose' else entry(api,
                    f'assert {1 if api == "a" else 0}\nprint("__CHECK__ {api} ", 1)')
            with patch('aideal.prompts.load', return_value=('system', 'user')), \
                 patch('aideal.readme_recording.ReadmeCallRecorder.invoke', new=author):
                result = revision.revise(cfg, launch, root)
            self.assertEqual(result['accepted'], 1)
            _, revised = revision.entry_parts((root / 'docs/D2.md').read_text())
            _, old = revision.entry_parts(original)
            self.assertEqual(revised['b'], old['b'])
            self.assertEqual(revised['c'], old['c'])
            self.assertIn('assert 1', revised['a'])
            with patch('aideal.readme_recording.ReadmeCallRecorder.invoke', side_effect=AssertionError('unexpected paid call')):
                resumed = revision.revise(cfg, launch, root)
            self.assertEqual(resumed['accepted'], 1)
            evidence = root / 'entries' / api_storage_key('a') / 'validation.json'
            evidence.write_text('{"status":"changed"}')
            with self.assertRaises(ValueError):
                revision.revise(cfg, launch, root)


if __name__ == '__main__':
    unittest.main()
