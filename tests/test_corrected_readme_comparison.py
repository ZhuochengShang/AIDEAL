"""Offline guards for fresh matched O/D1/D2 evaluation preparation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('corrected_comparison', ROOT / 'scripts/run_corrected_readme_comparison.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class CorrectedComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, value):
        path = self.root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def evidence(self):
        fp = {name: {'sha256': name} for name in
              ('source', 'fixtures', 'api_inventory', 'scaffold', 'canonical_requested_targets')}
        result = {'details': {'python:lib.f': {'status': 'pass'}}, 'run': {
            'complete': True, 'remaining_api_count': 0, 'max_fix_rounds': 0,
            'fingerprint_components': fp}}
        old = self.write('old/result.json', result)
        gen = self.write('gen/result.json', result)
        corrected = self.write('replay/result.json', {'source_result': comparison.binding(gen)})
        document = self.root / 'd2/docs/D2.md'
        document.parent.mkdir(parents=True)
        document.write_text('## API Test: `python:lib.f`\n### Goal\nUse f.\n')
        launch = self.write('d2/launch.json', {'identity_sha256': 'identity',
            'all_apis': ['python:lib.f'], 'selected': [],
            'bindings': {str(corrected): comparison.binding(corrected)['sha256']},
            'spec': {'result': str(corrected)}})
        d2 = self.write('d2/completion.json', {'status': 'complete', 'identity_sha256': 'identity',
            'output': str(document), 'readme_sha256': comparison.binding(document)['sha256'],
            'selected': 0, 'accepted': 0, 'outcomes': {},
            'scope': 'D2_from_corrected_R0_development_failures',
            'validation': 'corrected_native_execution_of_authored_example_not_independent_oracle'})
        return {'original_result': str(old), 'generated_result': str(gen),
                'd2_completion': str(d2), 'output': str(self.root / 'fresh')}, document, launch

    def test_completed_matched_inputs_are_hash_bound(self):
        spec, _, _ = self.evidence()
        *_, names, receipts = comparison.validate_evidence(spec)
        self.assertEqual(names, {'python:lib.f'})
        comparison.verify(receipts)
        Path(spec['generated_result']).write_text('{}')
        with self.assertRaisesRegex(ValueError, 'input changed'):
            comparison.verify(receipts)

    def test_changed_d2_document_is_rejected_before_calls(self):
        spec, document, _ = self.evidence()
        document.write_text('different D2')
        with self.assertRaisesRegex(ValueError, 'D2 document hash'):
            comparison.validate_evidence(spec)

    def test_different_source_or_unfinished_old_bank_is_rejected(self):
        spec, _, _ = self.evidence()
        p = Path(spec['generated_result'])
        result = comparison.read(p)
        result['run']['fingerprint_components']['source'] = 'different'
        p.write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'inputs differ: source'):
            comparison.validate_evidence(spec)
        result['run']['complete'] = False
        p.write_text(json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'complete matched'):
            comparison.validate_evidence(spec)

    def test_d2_from_another_replay_is_rejected(self):
        spec, _, launch = self.evidence()
        replay = Path(comparison.read(launch)['spec']['result'])
        replay.write_text(json.dumps({'source_result': {'path': '/wrong', 'sha256': 'wrong'}}))
        with self.assertRaisesRegex(ValueError, 'not developed from this D1'):
            comparison.validate_evidence(spec)

    def test_output_and_memory_paths_are_fresh_but_input_fixture_is_preserved(self):
        raw = {'files': {'error_log': '/old/errors', 'notes_to_self': '/old/memory'},
               'comprehension': {'execute': {'sample_data': {
                   'grid_png': '/source/tests/grid.png', 'output_path': '/old/output/test.png',
                   'output_dir': '/old/output'}, 'max_fix_rounds': 2}}}
        original = deepcopy(raw)
        result = comparison.condition_raw(raw, self.root / 'fresh', None)
        self.assertEqual(raw, original)
        self.assertEqual(result['files']['error_log'], 'logs/error_log.jsonl')
        self.assertEqual(result['files']['notes_to_self'], 'logs/notes_to_self.md')
        ex = result['comprehension']['execute']
        self.assertEqual(ex['sample_data']['grid_png'], '/source/tests/grid.png')
        self.assertEqual(ex['sample_data']['output_path'], str(self.root / 'fresh/execution/output/test.png'))
        self.assertEqual(ex['max_fix_rounds'], 0)

    def test_child_queue_stops_on_incomplete_arm(self):
        with patch.object(comparison.subprocess, 'run') as run:
            run.return_value.returncode = 2
            code = comparison.run_children(self.root / 'spec.json', 'mir_eval', {})
        self.assertEqual(code, 2)
        self.assertEqual(run.call_count, 1)
        self.assertIn('original', run.call_args.args[0])

    def test_child_queue_uses_three_fresh_processes_in_order(self):
        with patch.object(comparison.subprocess, 'run') as run:
            run.return_value.returncode = 0
            self.assertEqual(comparison.run_children(self.root / 'spec.json', 'rdpro_java', {}), 0)
        arms = [call.args[0][call.args[0].index('--condition') + 1] for call in run.call_args_list]
        self.assertEqual(arms, list(comparison.ARMS))

    def test_all_arms_receive_the_same_runtime_override(self):
        raw = {'files': {}, 'comprehension': {'execute': {'command': '/old/python {test_file}'}}}
        profile = {'profile_binding': {'path': '/receipts/runtime.json'}}
        with patch.object(comparison, 'remap_runtime_command', return_value='/overlay/python {test_file}') as remap:
            conditions = [comparison.condition_raw(raw, self.root / arm, None, profile)
                          for arm in comparison.ARMS]
        self.assertEqual(remap.call_count, 3)
        for condition in conditions:
            execution = condition['comprehension']['execute']
            self.assertEqual(execution['command'], '/overlay/python {test_file}')
            self.assertEqual(execution['runtime_profile'], '/receipts/runtime.json')

    def test_fresh_run_rejects_d2_from_a_different_runtime(self):
        spec, _, _ = self.evidence()
        path = Path(spec['d2_completion'])
        data = comparison.read(path)
        data['runtime_profile'] = [{'path': '/wrong/profile.json', 'sha256': 'wrong'}]
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'same runtime profile'):
            comparison.validate_evidence(spec)


if __name__ == '__main__':
    unittest.main()
