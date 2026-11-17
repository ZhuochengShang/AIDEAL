import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cluster_queue_layout', ROOT / 'scripts/make_cluster_queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class QueueLayoutTests(unittest.TestCase):
    def test_distinct_job_containers_and_nested_launcher_completion_paths(self):
        plan = queue.build('/tmp/study', '/tmp/release', '/usr/bin/python3', '/tmp/catalog.yaml')
        self.assertEqual(12, len(plan['jobs']))
        self.assertEqual(12, len({job['output'] for job in plan['jobs']}))
        for job in plan['jobs']:
            self.assertEqual(job['library'], Path(job['output']).name)
            self.assertEqual(job['library'], Path(job['complete_artifact']).parent.name)
            self.assertIn('--run', job['command'])
            self.assertNotIn('--sample', job['command'])

    def test_venv_python_symlink_is_not_replaced_by_base_interpreter(self):
        with tempfile.TemporaryDirectory() as temporary:
            python = Path(temporary).resolve() / 'venv-python'
            python.symlink_to('/usr/bin/python3')
            plan = queue.build('/tmp/study', '/tmp/release', python, '/tmp/catalog.yaml')
            self.assertEqual(str(python), plan['jobs'][0]['command'][0])

    def test_install_wrapper_targets_generated_document_and_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            manifests = root / 'install'
            manifests.mkdir()
            inner = root / 'authoring/rdpro/rdpro'
            (manifests / 'rdpro.json').write_text(json.dumps({'readme': str(inner / 'docs/LLM_readme.md'),
                                                            'completion': str(inner / 'completion.json')}))
            plan = queue.build(root, '/tmp/release', '/usr/bin/python3', '/tmp/catalog.yaml', manifests, ['rdpro'])
            job = plan['jobs'][1]
            self.assertIn('--run-command', job['command'])
            self.assertEqual(str(root / 'authoring/rdpro/installation.json'), job['complete_artifact'])


if __name__ == '__main__':
    unittest.main()
