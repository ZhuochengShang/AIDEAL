"""Offline integration tests for isolated, recorded README generation."""
from contextlib import redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import re
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
spec = importlib.util.spec_from_file_location('readme_launcher', ROOT / 'scripts/run_readme_generation.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
from aideal.readme_recording import ReadmeCallRecorder, ReadmeGenerationStopped
from aideal.config import ModelSpec


def entry(name):
    return f'## API Test: `{name}`\n\n### Goal\nCompute a small number.\n\n### Prompt Snippet\n```python\n{name}(1)\n```\n'


class ReadmeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='aideal-readme-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.original = self.root / 'original'
        self.source = self.original / 'source'
        self.source.mkdir(parents=True)
        (self.original / 'configs').mkdir()
        (self.source / 'api.py').write_text('def alpha(x):\n    return x\n\ndef beta(x):\n    return x+1\n')
        (self.source / 'README.md').write_text('Call alpha(x) or beta(x) with an integer.\n')
        profile = {'project': {'name': 'demo', 'language': 'Python', 'description': 'Integer operations.'},
                   'domain': 'numbers', 'target_users': ['Python users'], 'use_cases': ['Compute small integers']}
        (self.original / 'configs/project_profile.yaml').write_text(yaml.safe_dump(profile))
        config = {'project': {'name': 'demo', 'language': 'Python'},
                  'codebase': {'source_globs': ['source/*.py'], 'surface_filter': 'all'},
                  'files': {'project_profile': 'configs/project_profile.yaml', 'original_readme': 'source/README.md'},
                  'models': {'registry': {'old': {'provider': 'aideal-codex-audited', 'model': 'old', 'bridge': {'ignore': 'old'}}},
                             'roles': {'author': 'old'}},
                  'comprehension': {'execute': {'probe_on_missing': True, 'io_hints': 'auto', 'preamble': 'auto'}}}
        self.config = self.original / 'configs/aideal.yaml'
        self.config.write_text(yaml.safe_dump(config))
        self.manifest = self.original / 'manifest.json'
        self.manifest.write_text(json.dumps(['beta']))
        self.library = {'base_config': str(self.config), 'manifest': str(self.manifest),
                        'source_link': {'name': 'source', 'target': str(self.source)}}
        self.destination = self.root / 'batch/demo'
        self.original_bytes = {p: p.read_bytes() for p in self.original.rglob('*') if p.is_file()}

    def prepare(self, **kwargs):
        return launcher.prepare(self.library, self.destination, 'gemini-3.1-flash-lite', **kwargs)

    def generate(self, prepared, responses):
        with patch('aideal.llm.invoke_text', side_effect=responses) as model:
            result = launcher.run_library(prepared[0], self.destination, prepared[1], prepared[2])
        return result, model

    def test_preparation_is_offline_isolated_and_all_surface_by_default(self):
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No provider during preparation')):
            cfg, manifest, identity = self.prepare()
        self.assertEqual(['alpha', 'beta'], manifest['names'])
        self.assertEqual('google', cfg.model_for_role('author').provider)
        self.assertNotIn('bridge', json.dumps(cfg.raw))
        self.assertEqual(False, cfg.comprehension['execute']['probe_on_missing'])
        self.assertEqual('', cfg.comprehension['execute']['preamble'])
        self.assertEqual(self.destination, cfg.root)
        self.assertEqual(self.original_bytes, {p: p.read_bytes() for p in self.original.rglob('*') if p.is_file()})
        again = self.prepare()
        self.assertEqual(identity, again[2])
        with self.assertRaisesRegex(ValueError, 'Prepared README inputs changed'):
            self.prepare(scope='manifest')

    def test_manifest_scope_is_explicit_and_bound(self):
        cfg, manifest, identity = self.prepare(scope='manifest')
        self.assertEqual(['beta'], manifest['names'])
        self.assertEqual(1, len(manifest['definitions']['beta']))
        result, model = self.generate((cfg, manifest, identity), ['summary', entry('beta')])
        self.assertEqual(2, model.call_count)
        self.assertEqual(1, result['selected'])
        self.assertEqual(['beta'], [e.name for e in launcher.parse_readme(cfg.llm_readme)])

    def test_failed_call_stops_and_resume_replays_completed_calls(self):
        prepared = self.prepare()
        with patch('aideal.llm.invoke_text', side_effect=['summary', entry('alpha'), RuntimeError('transport')]) as model:
            with self.assertRaises(ReadmeGenerationStopped):
                launcher.run_library(prepared[0], self.destination, prepared[1], prepared[2])
        self.assertEqual(3, model.call_count)
        self.assertFalse((self.destination / 'completion.json').exists())
        self.assertFalse(prepared[0].llm_readme.exists())
        state = json.loads((self.destination / '.aideal_exec/readme_generation_state.json').read_text())
        self.assertFalse(state['complete'])
        old_calls = {p: p.read_bytes() for p in (self.destination / 'author_calls').rglob('*') if p.is_file()}
        result, model = self.generate(self.prepare(), [entry('beta')])
        self.assertEqual(1, model.call_count)
        self.assertEqual(2, result['reused_calls'])
        self.assertEqual('authored_not_execution_validated', result['status'])
        self.assertTrue(all(p.read_bytes() == b for p, b in old_calls.items()))
        again, model = self.generate(self.prepare(), [AssertionError('No more paid calls')])
        self.assertEqual(result, again)
        self.assertEqual(0, model.call_count)
        calls = [json.loads(p.read_text()) for p in (self.destination / 'author_calls').rglob('request.json')]
        self.assertEqual(4, len(calls))
        self.assertTrue(all('system' in c and 'user' in c and 'model' in c for c in calls))
        provider = [json.loads(p.read_text()) for p in (self.destination / 'author_calls').rglob('provider.json')]
        self.assertTrue(all('seconds' in c and 'usage' in c for c in provider))

    def test_invalid_entry_cannot_be_published_or_reused_as_success(self):
        prepared = self.prepare()
        with patch('aideal.llm.invoke_text', side_effect=['summary', entry('wrong')]) as model:
            with self.assertRaises(ReadmeGenerationStopped):
                launcher.run_library(prepared[0], self.destination, prepared[1], prepared[2])
        self.assertEqual(2, model.call_count)
        self.assertFalse(prepared[0].llm_readme.exists())
        result, model = self.generate(self.prepare(), [entry('alpha'), entry('beta')])
        self.assertEqual(2, model.call_count)
        self.assertEqual(1, result['reused_calls'])

    def test_changed_source_or_model_rejected_before_any_resume_call(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'Prepared README inputs changed'):
            launcher.prepare(self.library, self.destination, 'other-model')
        # Use a different destination because a failed preparation never rewrites inputs.
        (self.source / 'api.py').write_text('def alpha(x):\n    return x+5\n\ndef beta(x):\n    return x+1\n')
        with self.assertRaisesRegex(ValueError, 'Prepared README inputs changed'):
            self.prepare()

    def test_completed_document_and_receipt_tampering_rejected(self):
        prepared = self.prepare()
        self.generate(prepared, ['summary', entry('alpha'), entry('beta')])
        original = prepared[0].llm_readme.read_bytes()
        prepared[0].llm_readme.write_text('edited')
        with self.assertRaisesRegex(ValueError, 'Completed README or its identity changed'):
            self.generate(self.prepare(), [])
        prepared[0].llm_readme.write_bytes(original)
        response = next((self.destination / 'author_calls').rglob('response.txt'))
        response.write_text('edited')
        with self.assertRaisesRegex(ValueError, 'author evidence changed'):
            self.generate(self.prepare(), [])

    def test_keyboard_interrupt_receipt_and_prior_document_are_preserved(self):
        prepared = self.prepare()
        cfg = prepared[0]
        # Native recorder can protect an existing document when explicitly forced.
        cfg.llm_readme.parent.mkdir(parents=True, exist_ok=True)
        cfg.llm_readme.write_text('prior document\n')
        recorder = ReadmeCallRecorder(self.destination / 'author_calls', prepared[2]['identity_sha256'])
        with patch('aideal.llm.invoke_text', side_effect=['summary', KeyboardInterrupt]), redirect_stderr(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                launcher.find_or_create(cfg, generate=True, max_generated=0, force=True,
                                        api_names=prepared[1]['names'], recorder=recorder)
        self.assertEqual('prior document\n', cfg.llm_readme.read_text())
        states = [json.loads(p.read_text()) for p in (self.destination / 'author_calls').rglob('provider.json')]
        self.assertTrue(any(s.get('error_type') == 'KeyboardInterrupt' for s in states))

    def test_missing_manifest_name_fails_before_provider(self):
        self.manifest.write_text(json.dumps(['absent']))
        with patch('aideal.llm.invoke_text', side_effect=AssertionError('No provider')):
            with self.assertRaisesRegex(ValueError, 'outside the configured public surface'):
                self.prepare(scope='manifest')

    def test_complete_state_without_completion_still_replays_receipts(self):
        prepared = self.prepare()
        result, _ = self.generate(prepared, ['summary', entry('alpha'), entry('beta')])
        (self.destination / 'completion.json').unlink()
        again, model = self.generate(self.prepare(), [AssertionError('Replay must avoid provider')])
        self.assertEqual(0, model.call_count)
        self.assertEqual(3, again['reused_calls'])
        self.assertEqual(result['readme_sha256'], again['readme_sha256'])

    def test_actual_author_prompt_keeps_nested_owners_and_every_definition_site(self):
        prepared = self.prepare(scope='manifest')
        original = next(d for d in launcher.public_api_details(prepared[0]) if d['name'] == 'beta')
        definitions = [{**original, 'qualified_name': f'sample.Outer.Inner{i}.beta',
                        'owner': f'sample.Outer.Inner{i}', 'owner_kind': 'class',
                        'line': 10 + i, 'site_id': f'compiler-site-{i}',
                        'file_sha256': '0' * 64} for i in range(7)]
        with patch('aideal.readme_generation.public_api_details', return_value=definitions), \
             patch('aideal.llm.invoke_text', side_effect=['summary', entry('beta')]) as provider:
            launcher.run_library(prepared[0], self.destination, prepared[1], prepared[2])
        self.assertEqual(2, provider.call_count)
        user = provider.call_args_list[1].args[2]
        facts = json.loads(re.search(r'```json\n(.*?)\n```', user, re.S).group(1))
        self.assertEqual('sample.Outer.Inner0.beta', facts['qualified_name'])
        self.assertEqual('sample.Outer.Inner0', facts['owner'])
        self.assertEqual('class', facts['owner_kind'])
        self.assertEqual('compiler-site-0', facts['source']['site_id'])
        self.assertEqual(original['signature'], facts['signature'])
        self.assertEqual([d['qualified_name'] for d in definitions],
                         [d['qualified_name'] for d in facts['definition_sites']])
        self.assertEqual(list(range(10, 17)), [d['source']['line'] for d in facts['definition_sites']])
        self.assertEqual(7, facts['definition_site_count'])
        self.assertFalse(facts['definition_sites_truncated'])
        self.assertEqual(5, len(facts['overloads']))
        self.assertTrue(facts['overloads_truncated'])


if __name__ == '__main__':
    unittest.main()
