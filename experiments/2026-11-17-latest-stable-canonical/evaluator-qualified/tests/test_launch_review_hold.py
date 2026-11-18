"""A review hold applies to nested jobs before credentials or model requests."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workflow.evaluation_setup import assert_review_released


class LaunchReviewHoldTests(unittest.TestCase):
    def test_nested_output_obeys_ancestor_hold(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'REVIEW_HOLD.json').write_text('{"reason":"review revised inputs"}')
            with self.assertRaisesRegex(ValueError, 'paused for user code review'):
                assert_review_released(root / 'runs/original/mdanalysis/mdanalysis')
            (root / 'REVIEW_HOLD.json').unlink()
            assert_review_released(root / 'runs/original/mdanalysis/mdanalysis')

    def test_supervisor_stops_before_reading_credentials(self):
        spec = importlib.util.spec_from_file_location('held_supervisor', ROOT / 'scripts/run_cluster_experiment.py')
        supervisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(supervisor)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'REVIEW_HOLD.json').write_text('{}')
            with patch.object(Path, 'read_text', side_effect=AssertionError('No credential read')):
                with self.assertRaisesRegex(ValueError, 'paused for user code review'):
                    supervisor.supervise({'root': str(root)}, root / 'not-a-real-key')


if __name__ == '__main__':
    unittest.main()
