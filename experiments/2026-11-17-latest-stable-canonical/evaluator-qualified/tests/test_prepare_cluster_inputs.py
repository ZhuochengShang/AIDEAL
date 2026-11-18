"""Offline packaging checks using a tiny temporary source repository."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'tests':
    ROOT = ROOT.parent
SCRIPT = next(path for path in (ROOT / 'scripts/prepare_cluster_inputs.py', ROOT / 'prepare_cluster_inputs.py') if path.is_file())
spec = importlib.util.spec_from_file_location('prepare', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aideal-package-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Offline Test')
        self.git('config', 'user.email', 'offline@example.invalid')
        (self.source / 'module.py').write_text('def f(): return 1\n')
        (self.source / 'generated.c').write_text('/* upstream generated C */\n')
        (self.source / 'data').mkdir()
        (self.source / 'data/trajectory.xtc').write_bytes(b'fixture')
        self.git('add', '.')
        self.git('commit', '-qm', 'Pinned source')
        self.args = argparse.Namespace(remote_study='/remote/study', output=self.root / 'out',
                                       runtime_json=None, export=False, model='offline')
        self.exporter = module.Exporter(self.args)
        self.exporter.sources['demo'] = module.source_inventory('demo', self.source)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args])

    def test_inventory_records_generated_changes_without_exporting_overlay(self):
        (self.source / 'generated.c').write_text('/* local Cython rebuild */\n')
        inventory = module.source_inventory('demo', self.source)
        self.assertEqual(['generated.c'], inventory['excluded_working_tree_changes'])
        self.assertEqual('exact_git_HEAD_no_working_tree_overlays', inventory['archive_policy'])
        self.assertEqual(3, inventory['tracked_files'])

    def test_required_modified_input_rejected(self):
        (self.source / 'module.py').write_text('def f(): return 2\n')
        self.exporter.sources['demo'] = module.source_inventory('demo', self.source)
        with self.assertRaisesRegex(ValueError, 'differs from pinned HEAD'):
            self.exporter.reference(self.source / 'module.py', library='demo', category='original_docs')

    def test_generated_fixture_caches_do_not_duplicate_directory(self):
        (self.source / 'data/.trajectory.xtc_offsets.npz').write_bytes(b'cache')
        (self.source / 'data/.trajectory.xtc_offsets.lock').write_bytes(b'')
        target = self.exporter.reference(self.source / 'data', library='demo', category='fixtures')
        self.assertEqual('/remote/study/sources/demo/data', target)
        self.assertEqual({}, self.exporter.copies)
        self.assertEqual(2, len(self.exporter.excluded_input_caches))

    def test_jar_bytes_are_deduplicated_across_names(self):
        first = self.root / 'a.jar'
        second = self.root / 'b.jar'
        first.write_bytes(b'identical jar bytes')
        second.write_bytes(first.read_bytes())
        self.assertEqual(self.exporter.jar(first, 'demo'), self.exporter.jar(second, 'demo'))
        self.assertEqual(1, len(self.exporter.copies))


if __name__ == '__main__':
    unittest.main()
