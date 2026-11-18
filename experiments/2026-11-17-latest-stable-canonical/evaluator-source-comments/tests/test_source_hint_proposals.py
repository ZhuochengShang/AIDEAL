"""Offline source-authoring checks; proposal creation never modifies the baseline."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from workflow.source_hint_proposals import main, prepare_source_hints
from workflow.source_hints import index_source_hints, insert_source_hint, strip_source_hints


SOURCE = ('object RasterMetadata {\n'
          '  def rescale(width: Int, height: Int): String = width.toString\n'
          '  def translate(dx: Int, dy: Int): Int = dx + dy\n'
          '}\n')


class SourceHintProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'baseline'
        self.root.mkdir()
        self.source = self.root / 'RasterMetadata.scala'
        self.source.write_text(SOURCE)
        self.spec_path = self.base / 'spec.json'
        self.output = self.base / 'proposal'
        self.spec = {'schema_version': 1,
                     'api_function_ids': {'rescale': 'RasterMetadata.scala:2:rescale',
                                          'translate': 'RasterMetadata.scala:3:translate',
                                          'uncovered': 'Other.scala:1:other'},
                     'source_sha256': {'RasterMetadata.scala': hashlib.sha256(self.source.read_bytes()).hexdigest()},
                     'hints': [self.hint('rescale', 2), self.hint('translate', 3)]}
        self.save()

    def hint(self, name, line):
        return {'function_id': f'RasterMetadata.scala:{line}:{name}',
                'requirement_id': 'integer_dimensions',
                'requirement': 'Pass explicit integer dimensions.',
                'diagnostic': 'required: Int',
                'action': 'Choose integer pixel counts rather than floating point dimensions.',
                'validation': 'No behavioral validation has run.'}

    def save(self):
        self.spec_path.write_text(json.dumps(self.spec))

    def prepare(self):
        return prepare_source_hints(self.root, self.spec_path, self.output)

    def test_two_functions_preserve_exact_code_and_original_identity(self):
        manifest = self.prepare()
        emitted = self.output / 'source' / 'RasterMetadata.scala'
        self.assertEqual(self.source.read_text(), SOURCE)
        self.assertEqual(strip_source_hints(emitted.read_text()), SOURCE)
        self.assertEqual(manifest['status'], 'unvalidated')
        self.assertEqual(manifest['coverage']['covered_functions'], 2)
        self.assertEqual(manifest['coverage']['total_functions'], 3)
        index = index_source_hints(self.output / 'source', ['RasterMetadata.scala'], self.spec['api_function_ids'])
        self.assertEqual([r['function_id'] for r in index['records']],
                         ['RasterMetadata.scala:2:rescale', 'RasterMetadata.scala:3:translate'])
        self.assertTrue(all(r['status'] == 'unvalidated' for r in index['records']))
        self.assertEqual(self.spec_path.read_bytes(), (self.output / 'spec.json').read_bytes())
        self.assertIn('+  // AIDEAL-HINT-BEGIN', (self.output / 'source.patch').read_text())
        saved = json.loads((self.output / 'source_hint_index.json').read_text())
        self.assertEqual(saved['artifacts'][0]['path'], str(emitted.resolve()))

    def test_hash_mismatch_leaves_no_output_and_baseline_unchanged(self):
        self.spec['source_sha256']['RasterMetadata.scala'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'hash changed'):
            self.prepare()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_text(), SOURCE)

    def test_distinct_requirements_share_function_and_preserve_cross_function_lines(self):
        second = {**self.spec['hints'][0], 'requirement_id': 'positive_dimensions',
                  'requirement': 'Raster dimensions must be positive.',
                  'diagnostic': 'rasterWidth must be positive',
                  'action': 'Supply a positive raster width and height.'}
        self.spec['hints'].append(second)
        self.save()
        manifest = self.prepare()
        self.assertEqual(manifest['coverage']['covered_functions'], 2)
        self.assertEqual(manifest['coverage']['hint_count'], 3)
        emitted = self.output / 'source' / 'RasterMetadata.scala'
        self.assertEqual(strip_source_hints(emitted.read_text()), SOURCE)
        self.assertEqual(self.source.read_text(), SOURCE)
        index = index_source_hints(self.output / 'source', ['RasterMetadata.scala'], self.spec['api_function_ids'])
        rescale = [r for r in index['records'] if r['function_id'] == 'RasterMetadata.scala:2:rescale']
        self.assertEqual({r['requirement_id'] for r in rescale}, {'integer_dimensions', 'positive_dimensions'})
        self.assertEqual(len({r['declaration_line'] for r in rescale}), 1)
        self.assertEqual(len([r for r in index['records'] if r['function_id'] == 'RasterMetadata.scala:3:translate']), 1)

    def test_duplicate_requirement_for_same_function_rejected_before_output(self):
        self.spec['hints'].append(dict(self.spec['hints'][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, 'requirement ID unique'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_new_requirement_retains_existing_annotation_and_baseline(self):
        old = self.spec['hints'][0]
        baseline = insert_source_hint(SOURCE, old['function_id'], old, source_path='RasterMetadata.scala')
        self.source.write_text(baseline)
        self.spec['source_sha256']['RasterMetadata.scala'] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.spec['hints'][0] = {**old, 'requirement_id': 'positive_dimensions',
                                'diagnostic': 'rasterWidth must be positive',
                                'requirement': 'Use positive dimensions.', 'action': 'Choose positive integers.'}
        self.save()
        manifest = self.prepare()
        self.assertEqual(manifest['new_hint_count'], 2)
        self.assertEqual(manifest['coverage']['hint_count'], 3)
        emitted = self.output / 'source' / 'RasterMetadata.scala'
        self.assertEqual(strip_source_hints(emitted.read_text()), SOURCE)
        self.assertEqual(self.source.read_text(), baseline)
        index = index_source_hints(self.output / 'source', ['RasterMetadata.scala'], self.spec['api_function_ids'])
        retained = next(r for r in index['records'] if r['function_id'] == old['function_id']
                        and r['requirement_id'] == old['requirement_id'])
        self.assertTrue(all(retained[key] == value for key, value in old.items()))

    def test_specific_requirement_diagnostic_required_before_output(self):
        self.spec['hints'][1]['diagnostic'] = 'type mismatch;'
        self.save()
        with self.assertRaisesRegex(ValueError, 'specific requirement'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_wrong_declaration_line_rejected_before_output(self):
        self.spec['hints'][0]['function_id'] = 'RasterMetadata.scala:1:rescale'
        self.spec['api_function_ids']['rescale'] = 'RasterMetadata.scala:1:rescale'
        self.save()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_new_proposal_cannot_claim_validated_status(self):
        self.spec['hints'][0]['status'] = 'validated'
        self.save()
        with self.assertRaisesRegex(ValueError, 'unvalidated'):
            self.prepare()

    def test_output_cannot_replace_existing_directory_or_live_source(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            prepare_source_hints(self.root, self.spec_path, self.root / 'nested')
        self.output.mkdir()
        sentinel = self.output / 'keep.txt'
        sentinel.write_text('unchanged')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.prepare()
        self.assertEqual(sentinel.read_text(), 'unchanged')

    def test_source_escape_is_rejected(self):
        self.spec['hints'][0]['function_id'] = '../Other.scala:2:rescale'
        self.spec['api_function_ids']['rescale'] = '../Other.scala:2:rescale'
        self.save()
        with self.assertRaisesRegex(ValueError, 'inside'):
            self.prepare()

    def test_source_symlink_escape_is_rejected(self):
        outside = self.base / 'outside.scala'
        self.source.rename(outside)
        self.source.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_multiline_payload_cannot_inject_code(self):
        self.spec['hints'][0]['action'] = 'Do this.\nSystem.exit(1)'
        self.save()
        with self.assertRaisesRegex(ValueError, 'single-line'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_cli_records_unvalidated_artifact_paths(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            main(['--source-root', str(self.root), '--spec', str(self.spec_path), '--output', str(self.output)])
        manifest = json.loads(stream.getvalue())
        self.assertEqual(manifest['status'], 'unvalidated')
        self.assertTrue(Path(manifest['patch']).is_file())


if __name__ == '__main__':
    unittest.main()
