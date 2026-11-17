"""Git installation tests use temporary repositories and no model calls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readme_install', ROOT / 'scripts/install_generated_readme.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ReadmeInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aideal-readme-git-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-b', 'original')
        self.git('config', 'user.name', 'Offline Test')
        self.git('config', 'user.email', 'offline@example.invalid')
        (self.repo / 'README.md').write_text('Original documentation\n')
        self.git('add', 'README.md')
        self.git('commit', '-m', 'baseline')
        self.old = self.git('rev-parse', 'HEAD').decode().strip()
        for branch in ('readme-only', 'combined'):
            self.git('branch', branch)
        self.readme = self.root / 'generated.md'
        self.readme.write_text('# Generated API documentation\n')
        self.completion = self.root / 'completion.json'
        self.completion.write_text(json.dumps({'status': 'authored_not_execution_validated',
                                              'readme_sha256': installer.sha(self.readme.read_bytes())}))
        self.manifest, self.receipt = self.root / 'install.json', self.root / 'receipt.json'
        self.value = {'repository': str(self.repo), 'readme': str(self.readme), 'completion': str(self.completion),
                      'branches': {'readme-only': self.old, 'combined': self.old}}
        self.manifest.write_text(json.dumps(self.value))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE)

    def test_atomic_install_and_idempotent_resume_preserve_original(self):
        original = installer.original_identity(self.repo)
        self.assertEqual('refs/heads/original', original['branch'])
        first = installer.install(self.manifest, self.receipt)
        self.assertEqual(original, installer.original_identity(self.repo))
        self.assertFalse((self.repo / 'docs/LLM_readme.md').exists())
        self.assertEqual(b'Original documentation\n', (self.repo / 'README.md').read_bytes())
        for branch in ('readme-only', 'combined'):
            self.assertEqual(self.readme.read_bytes(), self.git('show', branch + ':docs/LLM_readme.md'))
            self.assertEqual(self.old, self.git('rev-parse', branch + '^').decode().strip())
        self.assertEqual(first, installer.install(self.manifest, self.receipt))
        # Simulate interruption after atomic ref update but before final receipt.
        self.receipt.replace(self.receipt.with_suffix('.json.pending'))
        self.assertEqual(first, installer.install(self.manifest, self.receipt))

    def test_detached_install_preserves_head_index_and_user_edits(self):
        self.git('checkout', '--detach', self.old)
        (self.repo / 'README.md').write_text('Staged user edit.\n')
        self.git('add', 'README.md')
        (self.repo / 'README.md').write_text('Unstaged user edit.\n')
        head_bytes = (self.repo / '.git/HEAD').read_bytes()
        index_bytes = (self.repo / '.git/index').read_bytes()
        before = installer.original_identity(self.repo)
        self.assertEqual(self.old, before['head'])
        self.assertIsNone(before['branch'])
        installer.preflight_generation(self.manifest)
        result = installer.install(self.manifest, self.receipt)
        self.assertIsNone(result['identity']['original']['branch'])
        self.assertEqual(before, installer.original_identity(self.repo))
        self.assertEqual(head_bytes, (self.repo / '.git/HEAD').read_bytes())
        self.assertEqual(index_bytes, (self.repo / '.git/index').read_bytes())
        self.assertEqual('Unstaged user edit.\n', (self.repo / 'README.md').read_text())
        self.assertEqual(b'Staged user edit.\n', self.git('show', ':README.md'))
        self.assertFalse((self.repo / 'docs/LLM_readme.md').exists())
        self.assertEqual(self.old, self.git('rev-parse', 'original').decode().strip())
        for branch in ('readme-only', 'combined'):
            self.assertNotEqual(self.old, self.git('rev-parse', branch).decode().strip())
            self.assertEqual(self.old, self.git('rev-parse', branch + '^').decode().strip())
            self.assertEqual(self.readme.read_bytes(), self.git('show', branch + ':docs/LLM_readme.md'))
        self.assertEqual(result, installer.install(self.manifest, self.receipt))

    def test_identity_errors_block_generation_and_are_not_treated_as_detached(self):
        real_git = installer.git
        def fail_symbolic_ref(repo, *args, **kwargs):
            if args[0] == 'symbolic-ref':
                raise subprocess.CalledProcessError(128, ['git', *args], stderr=b'broken repository')
            return real_git(repo, *args, **kwargs)
        with patch.object(installer, 'git', side_effect=fail_symbolic_ref):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.original_identity(self.repo)
        generated = self.root / 'generation-was-started'
        argv = ['install_generated_readme.py', '--manifest', str(self.manifest), '--receipt', str(self.receipt),
                '--run-command', sys.executable, '-c',
                'from pathlib import Path; Path(' + repr(str(generated)) + ').touch()']
        with patch.object(sys, 'argv', argv), patch.object(installer, 'original_identity', side_effect=ValueError('broken identity')) as identity:
            with self.assertRaisesRegex(ValueError, 'broken identity'):
                installer.main()
            identity.assert_called_once_with(self.repo.resolve())
        self.assertFalse(generated.exists())

    def test_checked_out_target_and_changed_completion_are_refused(self):
        self.git('worktree', 'add', str(self.root / 'target'), 'readme-only')
        with self.assertRaisesRegex(ValueError, 'checked out'):
            installer.install(self.manifest, self.receipt)
        self.git('worktree', 'remove', str(self.root / 'target'))
        self.readme.write_text('changed generated bytes')
        with self.assertRaisesRegex(ValueError, 'completion receipt'):
            installer.install(self.manifest, self.receipt)
        self.assertEqual(self.old, self.git('rev-parse', 'combined').decode().strip())

    def test_wrapper_preflight_detects_checked_out_target_before_generation(self):
        installer.preflight_generation(self.manifest)
        self.git('worktree', 'add', str(self.root / 'target'), 'combined')
        with self.assertRaisesRegex(ValueError, 'checked out'):
            installer.preflight_generation(self.manifest)

    def test_identical_existing_document_needs_no_new_commits(self):
        self.readme.write_bytes((self.repo / 'README.md').read_bytes())
        self.completion.write_text(json.dumps({'status': 'authored_not_execution_validated',
                                              'readme_sha256': installer.sha(self.readme.read_bytes())}))
        self.value['destination'] = 'README.md'
        self.manifest.write_text(json.dumps(self.value))
        result = installer.install(self.manifest, self.receipt)
        self.assertTrue(all(row['old'] == row['new'] for row in result['branches'].values()))

    def test_current_original_user_edits_are_preserved(self):
        (self.repo / 'README.md').write_text('An existing user edit.\n')
        before = installer.original_identity(self.repo)
        installer.install(self.manifest, self.receipt)
        self.assertEqual(before, installer.original_identity(self.repo))
        self.assertEqual('An existing user edit.\n', (self.repo / 'README.md').read_text())

    def test_different_existing_content_is_never_overwritten(self):
        self.value['destination'] = 'README.md'
        self.manifest.write_text(json.dumps(self.value))
        with self.assertRaisesRegex(ValueError, 'different content'):
            installer.install(self.manifest, self.receipt)
        self.assertEqual(self.old, self.git('rev-parse', 'readme-only').decode().strip())
        self.assertEqual(self.old, self.git('rev-parse', 'combined').decode().strip())


if __name__ == '__main__':
    unittest.main()
