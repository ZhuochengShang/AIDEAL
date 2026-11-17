"""Report refactoring must preserve counts and detect altered artifacts."""
import json
from pathlib import Path
import tempfile
import unittest

from workflow.ablation import file_hash, load, save
from workflow.evaluation_report import verify
from studies.historical.reporting import reproduce


class ReportingTests(unittest.TestCase):
    def test_archived_report_still_matches_the_saved_expected_result(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(load(root / 'evidence/expected_reproduction.json'), reproduce(root))

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
