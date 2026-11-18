"""Synthetic runner controls; these are not SedonaDB experiment scores."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from studies.sedonadb.runner import run
from studies.sedonadb.fixtures import relocated_catalog
from workflow.ablation import file_hash


class RunnerControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.binary = self.root / 'synthetic_runner'
        self.binary.write_text('#!' + sys.executable + '\nimport json, sys\n'
                               'print(json.dumps({"result": {"status": "executed", "rows": 1}}))\n'
                               'print("error-context-" * 1000, file=sys.stderr)\n')
        self.binary.chmod(0o700)
        self.catalog = self.root / 'catalog.json'
        self.catalog.write_text(json.dumps([{'kind': 'function_reference', 'api': 'ST_Test',
                                            'examples': ['SELECT ST_Test();'], 'runtime_default': 'scalar'}]))
        self.output = self.root / 'output'

    def test_resume_does_not_execute_twice_and_keeps_complete_stderr(self):
        first = run(self.catalog, self.binary, self.output)
        before = (self.output / 'results.jsonl').read_bytes()
        second = run(self.catalog, self.binary, self.output)
        self.assertEqual(first, second)
        self.assertEqual(before, (self.output / 'results.jsonl').read_bytes())
        self.assertEqual(1, len(list((self.output / 'cases/ST_Test__001').glob('attempt_*'))))
        self.assertGreater((self.output / 'cases/ST_Test__001/attempt_001/stderr.txt').stat().st_size, 10000)
        self.assertFalse(first['semantic_correctness_verified'])

    def test_changed_binary_rejected_without_overwriting_evidence(self):
        run(self.catalog, self.binary, self.output)
        before = (self.output / 'results.jsonl').read_bytes()
        self.binary.write_text(self.binary.read_text() + '# changed\n')
        with self.assertRaisesRegex(ValueError, 'Different input'):
            run(self.catalog, self.binary, self.output)
        self.assertEqual(before, (self.output / 'results.jsonl').read_bytes())

    def test_remote_fixture_is_pending_not_a_pass(self):
        data = json.loads(self.catalog.read_text())
        data[0]['examples'] = ["SELECT ST_Test('https://example.invalid/data');"]
        self.catalog.write_text(json.dumps(data))
        result = run(self.catalog, self.binary, self.output)
        self.assertEqual({'external_fixture_pending': 1}, result['example_statuses'])
        self.assertEqual(1, result['example_blocks'])

    def test_incompatible_or_duplicate_journal_is_rejected_without_rewriting(self):
        run(self.catalog, self.binary, self.output)
        journal = self.output / 'results.jsonl'
        original = journal.read_text()
        row = json.loads(original)
        changed = dict(row, fingerprint='different-study')
        unknown = dict(row, case_id='ST_Unknown__001')
        for text, message in [
            (json.dumps(changed) + '\n', 'Incompatible journal fingerprint'),
            (original + original, 'Duplicate journal case'),
            (json.dumps(unknown) + '\n', 'Unknown journal case'),
            (original + '{partial', 'Invalid journal JSON'),
        ]:
            with self.subTest(message=message):
                journal.write_text(text)
                with self.assertRaisesRegex(ValueError, message):
                    run(self.catalog, self.binary, self.output)
                self.assertEqual(text, journal.read_text())

    def test_malformed_runner_payload_is_recorded_as_failure(self):
        for index, payload in enumerate([None, {'result': None}, {'result': {'status': []}},
                                         {'result': {'status': 'invented-pass'}}]):
            with self.subTest(payload=payload):
                self.binary.write_text('#!' + sys.executable + '\nprint(' + repr(json.dumps(payload)) + ')\n')
                output = self.root / f'malformed_{index}'
                result = run(self.catalog, self.binary, output)
                self.assertEqual({'invalid_runner_output': 1}, result['example_statuses'])
                self.assertTrue((output / 'cases/ST_Test__001/attempt_001/stdout.txt').is_file())

    def test_api_name_cannot_escape_output_directory(self):
        data = json.loads(self.catalog.read_text())
        data[0]['api'] = '../outside'
        self.catalog.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unsafe or missing SQL API name'):
            run(self.catalog, self.binary, self.output)
        self.assertFalse(self.output.exists())

    def test_attempt_numbering_preserves_nonconsecutive_interrupted_attempts(self):
        prior = self.output / 'cases/ST_Test__001/attempt_002'
        prior.mkdir(parents=True)
        (prior / 'partial.txt').write_text('keep')
        run(self.catalog, self.binary, self.output)
        self.assertEqual('keep', (prior / 'partial.txt').read_text())
        self.assertTrue((prior.parent / 'attempt_003/result.json').is_file())

    def test_timeout_recorded_and_interrupted_files_retained(self):
        self.binary.write_text('#!' + sys.executable + '\nimport time\ntime.sleep(5)\n')
        prior = self.output / 'cases/ST_Test__001/attempt_001'
        prior.mkdir(parents=True)
        (prior / 'partial.txt').write_text('interrupted evidence')
        result = run(self.catalog, self.binary, self.output, timeout=0.05)
        self.assertEqual({'outer_timeout': 1}, result['example_statuses'])
        self.assertEqual('interrupted evidence', (prior / 'partial.txt').read_text())
        self.assertTrue((prior.parent / 'attempt_002/result.json').is_file())

    def test_relocation_checks_fixture_hash_and_preserves_original_sql(self):
        folder = self.root / 'studies/sedonadb/evidence'
        folder.mkdir(parents=True)
        fixture = folder / 'x.tif'
        fixture.write_bytes(b'pinned fixture')
        original = "SELECT ST_Test('old/x.tif');"
        catalog = [{'examples': [original], 'fixture_bindings': [{
            'example_index': 1, 'original_locator': 'old/x.tif', 'original_sql': original,
            'local_fixture': {'path': '/old/x.tif', 'sha256': file_hash(fixture)}}]}]
        source = folder / 'sql_reference_local_paths.json'
        source.write_text(json.dumps(catalog))
        destination = self.root / 'bound.json'
        relocated_catalog(self.root, destination)
        self.assertIn(str(fixture), json.loads(destination.read_text())[0]['examples'][0])
        self.assertEqual(catalog, json.loads(source.read_text()))
        fixture.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Pinned fixture changed'):
            relocated_catalog(self.root, self.root / 'other.json')

    def test_relocation_keeps_multiple_fixtures_in_one_sql_block(self):
        root = self.root / "directory's name"
        folder = root / 'studies/sedonadb/evidence'
        folder.mkdir(parents=True)
        original = "SELECT ST_Test('old/a.tif', 'old/b.tif');"
        bindings = []
        for name in ('a.tif', 'b.tif'):
            fixture = folder / name
            fixture.write_bytes(name.encode())
            bindings.append({
                'example_index': 1, 'original_sql': original,
                'original_locator': 'old/' + name,
                'local_fixture': {'path': '/old/' + name, 'sha256': file_hash(fixture)},
            })
        (folder / 'sql_reference_local_paths.json').write_text(json.dumps([
            {'examples': [original], 'fixture_bindings': bindings},
        ]))
        destination = root / 'bound.json'
        relocated_catalog(root, destination)
        sql = json.loads(destination.read_text())[0]['examples'][0]
        for name in ('a.tif', 'b.tif'):
            self.assertIn(str(folder / name).replace("'", "''"), sql)
        self.assertNotIn('old/', sql)


if __name__ == '__main__':
    unittest.main()
