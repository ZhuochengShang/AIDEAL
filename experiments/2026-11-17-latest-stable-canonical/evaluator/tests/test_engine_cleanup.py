"""Offline behavior checks for shared engine helpers and removed private adapters."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/aideal_engine/src'))
from aideal import checkpoint_compatibility, doc_checks, experiment_identity, probe
from aideal import readme_agent, readme_catalogue, readme_evidence


class EngineCleanupTests(unittest.TestCase):
    def test_batched_doc_retrieval_keeps_ranking_boundaries_and_character_cap(self):
        inline = '# Inline\nUse `f`.'
        first = '# First\nUse `f(1)`.'
        second = '# Second\nUse `f(2)`.'
        strongest = '# Strong\nUse `f(3)` then `f(4)`.'
        other = '# Other\nUse `g()` and `fExtra()`.'
        raw = '\n'.join(['# Prose\nf is a common name.', inline, first,
                         second, strongest, other])
        cfg = SimpleNamespace(raw={}, original_readme_text=Mock(return_value=raw))
        result = doc_checks._relevant_original_texts(cfg, ['f', 'g', 'absent'], 1000)
        self.assertEqual('\n\n'.join([strongest, first, second, inline]), result['f'])
        self.assertEqual(other, result['g'])
        missing = ('No code-context section for `absent` was found in the '
                   'configured original documentation.')
        self.assertEqual(missing, result['absent'])
        cfg.original_readme_text.assert_called_once_with(limit=None)
        for limit in (1, len(strongest), len(strongest) + 1,
                      len(strongest) + 2, len(strongest) + 6):
            with self.subTest(limit=limit):
                actual = doc_checks._relevant_original_texts(cfg, ['f'], limit)['f']
                expected = (strongest[:limit] if limit <= len(strongest) + 2
                            else strongest + '\n\n' + first[:limit - len(strongest) - 2])
                self.assertEqual(expected, actual)
                self.assertLessEqual(len(actual), limit)
        cfg.raw = {'coverage': {'documentation_call_patterns': [r'\b{name}!']}}
        cfg.original_readme_text.return_value = '# Macro\nInvoke f! now.'
        self.assertEqual('# Macro\nInvoke f! now.',
                         doc_checks._relevant_original_texts(cfg, ['f'], 100)['f'])

    def test_native_digest_preserves_exact_serialization_and_public_signatures(self):
        canonical = b'{"a":{"path":"relative/file","text":"\\u03b2"},"z":[1,true,null]}'
        expected = hashlib.sha256(canonical).hexdigest()
        components = {'z': [1, True, None], 'a': {'text': '\u03b2', 'path': Path('relative/file')}}
        self.assertEqual(expected, checkpoint_compatibility.fingerprint(parts=components))
        self.assertEqual(expected, experiment_identity.digest_native(components=components))
        reordered = {'a': {'path': 'relative/file', 'text': '\u03b2'}, 'z': [1, True, None]}
        self.assertEqual(expected, experiment_identity.digest_native(reordered))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run_identity.json'
            experiment_identity.write_run_identity(path, reordered)
            self.assertEqual({'schema': 1, 'experiment_fingerprint': expected,
                              'fingerprint_components': reordered}, json.loads(path.read_text()))

    def test_catalogue_and_index_preserve_tier_status_order_and_badges(self):
        tiers = {'guess': 'guessed', 'sibling': 'sibling', 'ground': 'grounded',
                 'verified_fail': 'verified', 'verified_unknown': 'verified',
                 'verified_z': 'verified', 'verified_a': 'verified'}
        statuses = {'guess': 'pass', 'ground': 'fail', 'verified_fail': 'fail',
                    'verified_z': 'pass', 'verified_a': 'pass'}
        class_of = dict.fromkeys(tiers, 'Ops')
        expected = ['verified_a', 'verified_z', 'verified_unknown', 'verified_fail',
                    'ground', 'sibling', 'guess']
        entries = [readme_agent.ApiEntry(name, 'Goal for ' + name, '', '') for name in tiers]
        model = readme_catalogue._catalogue_model(entries, tiers, statuses, class_of, {})
        self.assertEqual(expected, [member['name'] for member in model['Ops']['members']])
        self.assertEqual('verified_a', model['Ops']['primary'])
        with tempfile.TemporaryDirectory() as directory:
            cfg = SimpleNamespace(project_name='Synthetic', llm_readme=Path(directory) / 'LLM_readme.md')
            with patch.object(readme_evidence, '_grounding_tiers', return_value=(tiers, class_of, {})), \
                 patch.object(readme_evidence, '_exec_status_map', return_value=statuses):
                report = readme_evidence.organize_report(cfg, write_index=True)
            index = (Path(directory) / 'readme_index.md').read_text()
        self.assertEqual(expected, re.findall(r'^- \S+ `([^`]+)`', index, re.MULTILINE))
        self.assertIn('- ★ `verified_a` — verified · exec pass **(primary)**', index)
        self.assertIn('- ✅ `ground` — grounded · exec fail', index)
        self.assertIn('- 🟡 `sibling` — sibling', index)
        self.assertIn('- ⚠️ `guess` — guessed · exec pass', index)
        self.assertEqual({'Ops': {'primary': 'verified_a', 'count': 7}}, report['categories_sample'])
        # Existing facade constants remain available after moving their owner.
        self.assertEqual('★', readme_agent._TIER_BADGE['verified'])
        self.assertEqual(3, readme_agent._TIER_RANK['guessed'])
        self.assertEqual(2, readme_agent._EXEC_RANK['fail'])

    def test_probe_keeps_version_evidence_without_a_forwarding_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cfg = SimpleNamespace(root=root, language='Scala', error_log=root / 'error.jsonl')
            ctx = {'sample_data': {'table_csv': '/synthetic/input.csv'}, 'ex': {},
                   'work_dir': root / 'work', 'command': 'synthetic {scala_file}',
                   'uberjar': '', 'jars': '', 'classpath': '', 'packages_flag': '',
                   'repositories_flag': '', 'scaffold': '// START\n// END',
                   'bindings': '', 'region': ['// START', '// END'],
                   'check_marker': '__CHECK__', 'success_marker': 'DONE',
                   'error_marker': '__ERR__', 'require_correctness': True, 'timeout': 1}
            outcomes = [subprocess.CompletedProcess('synthetic', 0, 'DONE\n__CHECK__ load 3', ''),
                        subprocess.CompletedProcess('synthetic', 1, '', 'ApiTest.scala:4: error: not found: value bad')]
            with patch.object(probe, 'resolve_exec_context', return_value=ctx), \
                 patch.object(probe, 'git_version', return_value='synthetic-commit') as version, \
                 patch.object(probe.subprocess, 'run', side_effect=outcomes) as runner, \
                 patch.object(probe, '_llm_probe_snippet', side_effect=AssertionError('Unexpected model call')):
                for expected in ('pass', 'fail'):
                    result = probe.run_probe(cfg, 'load', returns='DataFrame', use_llm=False, max_fix_rounds=0)
                    self.assertEqual(expected, result.status)
                    self.assertEqual('table_csv', result.input_var)
                    self.assertTrue(Path(result.scala_file).is_file())
                self.assertEqual(2, runner.call_count)
                self.assertEqual(2, version.call_count)
                version.assert_called_with(root)
                dry = probe.run_probe(cfg, 'load', returns='DataFrame', dry_run=True)
                self.assertEqual('dry-run', dry.status)
                self.assertEqual(2, runner.call_count)
                self.assertEqual(2, version.call_count)
            rows = [json.loads(line) for line in cfg.error_log.read_text().splitlines()]
            self.assertEqual(['pass', 'fail'], [row['status'] for row in rows])
            self.assertEqual(['synthetic-commit'] * 2, [row['library_version'] for row in rows])


if __name__ == '__main__':
    unittest.main()
