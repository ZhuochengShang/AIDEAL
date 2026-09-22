"""Report refactoring must preserve counts and detect altered artifacts."""
import json
from pathlib import Path
import tempfile
import unittest

from workflow.ablation import file_hash, load, save
from workflow.reporting import verify
from studies.historical.reporting import reproduce


class ReportingTests(unittest.TestCase):
    def test_archived_report_recounts_native_and_example_records_without_live_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            native = root / 'evidence/historical/native/synthetic.json'
            save(native, {'metrics': {'first': {'status': 'pass', 'pass_round': 0},
                                      'repaired': {'status': 'pass', 'pass_round': 2},
                                      'failed': {'status': 'fail'}, 'pending': {'status': 'pending'}}})
            save(root / 'evidence/historical/RESULTS.json', {
                'historical_verified': {'label': 'synthetic historical memo'},
                'RDPro_v5': {'label': 'synthetic legacy summary'},
            })
            for variant in ('default', 'setup_variant_v2', 'configured'):
                path = root / f'studies/sedonadb/evidence/{variant}_results.jsonl'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('\n'.join(json.dumps(row) for row in [
                    {'case_id': 'one', 'status': 'executed'},
                    {'case_id': 'two', 'status': 'executed'},
                    {'case_id': 'three', 'status': 'outer_timeout'}]) + '\n')
            report = reproduce(root)
            self.assertEqual({'selected': 4, 'native_passes': 2, 'initial_native_passes': 1,
                              'first_pass_rounds': {'0': 1, '2': 1}, 'source_sha256': file_hash(native),
                              'independent_semantic_validation': False}, report['native_cells']['synthetic.json'])
            for cell in report['sedonadb_rust_documentation_sweeps'].values():
                self.assertEqual(3, cell['example_blocks'])
                self.assertEqual({'executed': 2, 'outer_timeout': 1}, cell['statuses'])
                self.assertFalse(cell['semantic_correctness_verified'])
                self.assertEqual(0, cell['llm_calls'])
            self.assertIsNone(report['new_five_arm_results'])
            self.assertEqual({'label': 'synthetic historical memo'}, report['historical_external_summary'])

    def test_verification_reports_changed_artifacts_without_rewriting_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save(root / 'evidence/historical/RESULTS.json', {
                'historical_verified': {}, 'RDPro_v5': {},
            })
            for variant in ('default', 'setup_variant_v2', 'configured'):
                path = root / f'studies/sedonadb/evidence/{variant}_results.jsonl'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({'case_id': 'f__001', 'status': 'executed'}) + '\n')
            save(root / 'configs/active_arm.json', {
                'arm': 'original', 'readme': False, 'aliases': False, 'error_hints': False,
            })
            artifact = root / 'README.md'
            artifact.write_text('original')
            save(root / 'evidence/manifest.json', {
                'files': [{'path': 'README.md', 'sha256': file_hash(artifact)}],
            })
            save(root / 'evidence/expected_reproduction.json', reproduce(root))
            self.assertTrue(verify(root)['verified'])
            artifact.write_text('intentional pending edit')
            report = verify(root)
            self.assertFalse(report['verified'])
            self.assertEqual(['README.md'], report['changed'])
            self.assertEqual('intentional pending edit', artifact.read_text())


if __name__ == '__main__':
    unittest.main()
