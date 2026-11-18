import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cluster_queue_layout', ROOT / 'scripts/make_cluster_queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class QueueLayoutTests(unittest.TestCase):
    def test_cli_uses_actual_catalog_keys_and_requested_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / 'catalog.yaml'
            catalog.write_text(yaml.safe_dump({'rdpro_scala': {}, 'rdpro_java': {}, 'sedonadb': {}}))
            output = root / 'plan.json'
            argv = ['make_cluster_queue.py', '--root', str(root), '--release', '/tmp/release',
                    '--python', sys.executable, '--catalog', str(catalog), '--output', str(output),
                    '--model', 'configured-test-model']
            with patch.object(sys, 'argv', argv):
                queue.main()
            plan = json.loads(output.read_text())
            self.assertEqual(6, len(plan['jobs']))
            self.assertEqual({'rdpro_scala', 'rdpro_java', 'sedonadb'},
                             {job['library'] for job in plan['jobs']})
            for job in plan['jobs']:
                self.assertEqual('configured-test-model', job['command'][job['command'].index('--model')+1])

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
