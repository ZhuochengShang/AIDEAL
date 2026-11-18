"""Large exposure graphs stay auditable without overwhelming author requests."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from workflow import improvement_batches as batches
from workflow import improvement_context as context
from workflow import improvement_suggestions as suggestions
from workflow.ablation import load, verify_artifact


class ContextDistillationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.code = 'raise RuntimeError("SOURCE_MUST_NOT_BE_IMPORTED")\n\ndef convert(value):\n    return value\n'
        (self.source / 'api.py').write_text(self.code)
        self.study = self.root / 'study'
        self.study.mkdir()
        self.cfg = SimpleNamespace(project_name='Synthetic MD-like library', language='Python')
        self.attachment = {'revision': 'frozen-source'}
        self.rows = []
        for name in ['convert', 'scale', 'normalize']:
            paths = [f'library.Reader{n}.{name}' for n in range(142)]
            self.rows.append({'id': 'python:library.IOBase.' + name,
                'api_id': 'python:library.IOBase.' + name, 'name': name,
                'qualified_name': 'library.IOBase.' + name,
                'source_function_id': 'api.py:3:library.IOBase.' + name,
                'file': 'api.py', 'line': 3, 'signature': '(value: Array, inplace: bool = True) -> Array',
                'params': [{'name': 'value', 'type': 'Array'}], 'returns': 'Array',
                'public_access_paths': paths, 'preferred_public_path': paths[-1],
                'exposure_ids': ['python:' + p for p in paths],
                'api_origin': {'full_graph': 'PROVENANCE_ONLY' * 8000},
                'body_classification': {'category': 'implementation', 'evidence': 'AUDIT_ONLY' * 8000}})
        self.assertGreater(len(json.dumps(self.rows[0])), 60000)

    def inputs(self, *args):
        return self.study, self.source, self.attachment, self.cfg, deepcopy(self.rows), []

    def prepare(self, single=False):
        module = context if single else batches
        output = self.root / ('single' if single else 'batches')
        with patch.object(module, '_library_inputs', side_effect=self.inputs), \
             patch.object(module, '_semantic_context', return_value=({}, [])), \
             patch.object(module, 'development_destination', side_effect=lambda study, path: Path(path)):
            if single:
                result = context.preview_improvements(self.study, output, max_context_characters=20000)
                return load(result['preview']), [load(result['preview'])]
            result = batches.preview_library_improvements(self.study, output, batch_size=2,
                apis=[r['id'] for r in self.rows], max_context_characters=6000, max_catalog_characters=1000)
            manifest = load(result['manifest'])
            return manifest, [load(b['preview']['path']) for b in manifest['batches']]

    def test_bounded_batches_preserve_every_target_and_full_audit(self):
        manifest, previews = self.prepare()
        selected = [r for p in previews for r in p['context']['apis']]
        self.assertEqual([r['id'] for r in self.rows], [r['id'] for r in selected])
        self.assertTrue(all(b['context_characters'] <= 6000 for b in manifest['batches']))
        full = load(manifest['api_evidence']['path'])['apis']
        self.assertTrue(verify_artifact(manifest['api_evidence']))
        for original, compact, saved in zip(self.rows, selected, full):
            self.assertEqual(original['signature'], compact['signature'])
            self.assertEqual(saved['source_window'], compact['source_window'])
            self.assertIn('SOURCE_MUST_NOT_BE_IMPORTED', compact['source_window']['text'])
            self.assertEqual(original['preferred_public_path'], compact['public_access_paths'][0])
            self.assertEqual(8, len(compact['public_access_paths']))
            self.assertEqual(134, compact['omitted_public_access_paths'])
            for field in ['api_origin', 'body_classification', 'exposure_ids']:
                self.assertNotIn(field, compact)
                self.assertEqual(original[field], saved[field])
        self.assertEqual(self.code, (self.source / 'api.py').read_text())
        self.assertEqual(1, len(list((self.root / 'batches').rglob('api_evidence.json'))))
        self.assertTrue(all(p['api_evidence'] == manifest['api_evidence'] for p in previews))

    def test_single_preview_uses_the_same_compaction_and_audit(self):
        preview, _ = self.prepare(single=True)
        self.assertEqual(3, len(preview['context']['apis']))
        self.assertNotIn('PROVENANCE_ONLY', json.dumps(preview['context']))
        self.assertNotIn('AUDIT_ONLY', json.dumps(preview['context']))
        self.assertEqual(self.rows[0]['api_origin'], load(preview['api_evidence']['path'])['apis'][0]['api_origin'])
        self.assertEqual(self.code, (self.source / 'api.py').read_text())

    def test_exact_signature_is_never_truncated(self):
        row = deepcopy(self.rows[0])
        row['signature'] = '(' + ', '.join('parameter' + str(i) + ': Array' for i in range(250)) + ') -> Array'
        compact = context.compact_api_context([row])[0]
        self.assertGreater(len(row['signature']), 2000)
        self.assertEqual(row['signature'], compact['signature'])

    def test_changed_full_audit_is_rejected_before_a_proposal(self):
        preview, _ = self.prepare(single=True)
        Path(preview['api_evidence']['path']).write_text('{}\n')
        with patch.object(suggestions, 'original_checkout', return_value=(self.study, self.source, self.attachment)):
            with self.assertRaisesRegex(ValueError, 'input artifacts changed'):
                suggestions._load_preview(self.root / 'single/preview.json')


if __name__ == '__main__':
    unittest.main()
