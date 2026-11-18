"""Local queue checks; fake credentials, no provider or network calls."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cluster_experiment', ROOT / 'scripts/run_cluster_experiment.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class ClusterExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='aideal-queue-offline-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.key = self.root / 'key.txt'
        self.key.write_text('offline-test-credential')
        self.release = self.root / 'release'
        self.release.mkdir()
        self.script = self.release / 'job.py'
        self.script.write_text('import os, pathlib, sys\n'
            'assert "GEMINI_API_KEY" not in os.environ\n'
            'print(os.environ["GOOGLE_API_KEY"])\n'
            'p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True,exist_ok=True)\n'
            'p.write_text("complete")\n')
        self.plan = {'root': str(self.root / 'study'), 'release': str(self.release), 'jobs': []}
        for name in ('a', 'b', 'c'):
            output = self.root / 'study' / name
            self.plan['jobs'].append({'id': name, 'library': name, 'stage': 'r0', 'output': str(output),
                'command': [sys.executable, str(self.script), str(output / 'result.json')]})

    def test_two_worker_queue_sanitizes_logs_and_verified_resume_skips_jobs(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'inherited-must-be-removed'}):
            result = queue.supervise(self.plan, self.key)
        self.assertTrue(result['complete'])
        supervisor = self.root / 'study/supervisor'
        saved = {p: p.read_bytes() for p in supervisor.rglob('*') if p.is_file() and p.name != 'summary.json'}
        self.assertTrue(all(b'offline-test-credential' not in data for data in saved.values()))
        self.assertTrue(any(b'[REDACTED]' in data for data in saved.values()))
        again = queue.supervise(self.plan, self.key)
        self.assertTrue(again['complete'])
        self.assertEqual(saved, {p: p.read_bytes() for p in supervisor.rglob('*') if p.is_file() and p.name != 'summary.json'})
        (self.root / 'study/a/result.json').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Completed output changed'):
            queue.supervise(self.plan, self.key)

    def test_failed_jobs_have_separate_attempts_on_explicit_resume(self):
        self.script.write_text('raise SystemExit(3)\n')
        first = queue.supervise(self.plan, self.key)
        self.assertFalse(first['complete'])
        queue.supervise(self.plan, self.key)
        attempts = list((self.root / 'study/supervisor/a').glob('attempt_*'))
        self.assertEqual(2, len(attempts))
        self.assertEqual(3, json.loads((attempts[0] / 'result.json').read_text())['exit_code'])

    def test_development_jobs_require_explicit_completion_artifact(self):
        self.plan['jobs'][0]['stage'] = 'development'
        with self.assertRaisesRegex(ValueError, 'explicit completion artifact'):
            queue.prepare(self.plan, 'offline-test-credential')

    def test_development_completion_is_distinct_from_evaluation_result(self):
        self.plan['jobs'] = [self.plan['jobs'][0]]
        job = self.plan['jobs'][0]
        job['stage'] = 'development'
        artifact = Path(job['output']) / 'proposal_completion.json'
        job['complete_artifact'] = str(artifact)
        job['command'][-1] = str(artifact)
        result = queue.supervise(self.plan, self.key)
        self.assertTrue(result['complete'])
        self.assertEqual(result['jobs']['a']['stage'], 'development')
        self.assertTrue(artifact.is_file())
        self.assertFalse((Path(job['output']) / 'result.json').exists())

    def test_changed_commands_and_duplicate_ids_are_rejected(self):
        queue.supervise(self.plan, self.key)
        self.script.write_text('print("changed")\n')
        with self.assertRaisesRegex(ValueError, 'command files changed'):
            queue.supervise(self.plan, self.key)
        duplicate = json.loads(json.dumps(self.plan))
        duplicate['jobs'][1]['id'] = 'a'
        with self.assertRaisesRegex(ValueError, 'unique simple names'):
            queue.prepare(duplicate, 'offline-test-credential')


if __name__ == '__main__':
    unittest.main()
