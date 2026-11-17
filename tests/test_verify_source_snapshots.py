import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
if ROOT.name == 'tests':
    ROOT = ROOT.parent
spec = importlib.util.spec_from_file_location('snapshots', ROOT / 'scripts/verify_source_snapshots.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExactSnapshotTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='aideal-snapshot-test-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.upstream = self.root / 'upstream'
        self.remote = self.root / 'remote'
        for p in (self.upstream, self.remote):
            p.mkdir()
            self.git(p, 'init', '-q')
            self.git(p, 'config', 'user.name', 'Offline Test')
            self.git(p, 'config', 'user.email', 'offline@example.invalid')
        (self.upstream / '.gitattributes').write_text('metadata.txt export-subst\n')
        (self.upstream / '.gitignore').write_text('*.ignored\n*.so\n')
        (self.upstream / 'metadata.txt').write_text('$Format:%H$\n')
        (self.upstream / 'fixture.ignored').write_text('Tracked upstream fixture\n')
        self.git(self.upstream, 'add', '-A')
        self.git(self.upstream, 'add', '-f', 'fixture.ignored')
        self.git(self.upstream, 'commit', '-qm', 'Upstream')
        self.expected = self.git(self.upstream, 'rev-parse', 'HEAD^{tree}')
        self.archive = self.root / 'source.tar.gz'
        self.git(self.upstream, 'archive', '--format=tar.gz', '--output=' + str(self.archive), 'HEAD')
        with tarfile.open(self.archive) as stream:
            stream.extractall(self.remote)
        (self.remote / 'runtime.so').write_bytes(b'build output must never be committed')
        self.git(self.remote, 'add', '-A')
        self.git(self.remote, 'commit', '-qm', 'Initial archive snapshot')
        self.git(self.remote, 'branch', '-m', module.PREFIX + 'original')
        self.original = self.git(self.remote, 'rev-parse', 'HEAD')
        for arm in module.ARMS[1:]:
            self.git(self.remote, 'branch', module.PREFIX + arm)
        data = (self.upstream / 'metadata.txt').read_bytes()
        (self.root / 'metadata-original.txt').write_bytes(data)
        self.supplements = [{'relative': 'metadata.txt', 'payload': 'metadata-original.txt',
                             'sha256': hashlib.sha256(data).hexdigest(), 'mode': '100644'}]

    @staticmethod
    def git(path, *args):
        return subprocess.check_output(['git', '-C', str(path), *args]).decode().strip()

    def action(self, apply):
        return module.audit_or_repair('demo', self.remote, self.archive, self.supplements,
                                      self.root, self.expected, apply)

    def test_exact_fix_handles_ignored_tracked_file_and_export_substitution(self):
        audit = self.action(False)
        self.assertEqual(['fixture.ignored', 'metadata.txt'], audit['tree_changes'])
        self.assertEqual(self.original, self.git(self.remote, 'rev-parse', 'HEAD'))
        repaired = self.action(True)
        self.assertEqual('corrected', repaired['status'])
        self.assertEqual(self.expected, self.git(self.remote, 'rev-parse', 'HEAD^{tree}'))
        self.assertEqual(self.original, self.git(self.remote, 'rev-parse', 'HEAD^'))
        self.assertEqual('', self.git(self.remote, 'status', '--porcelain'))
        self.assertNotIn('runtime.so', self.git(self.remote, 'ls-files'))
        self.assertEqual(1, len(set(repaired['branches'].values())))

    def test_diverged_treatment_branch_is_preserved(self):
        self.git(self.remote, 'checkout', '-q', module.PREFIX + 'readme-only')
        (self.remote / 'treatment.md').write_text('Independent treatment')
        self.git(self.remote, 'add', 'treatment.md')
        self.git(self.remote, 'commit', '-qm', 'Treatment')
        self.git(self.remote, 'checkout', '-q', module.PREFIX + 'original')
        with self.assertRaisesRegex(ValueError, 'diverged'):
            self.action(True)
        self.assertEqual(self.original, self.git(self.remote, 'rev-parse', 'HEAD'))


if __name__ == '__main__':
    unittest.main()
