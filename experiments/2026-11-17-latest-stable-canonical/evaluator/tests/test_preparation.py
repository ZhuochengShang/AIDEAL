"""Study setup reuses the archived YAML loader without launching its commands."""
from importlib.util import find_spec
from pathlib import Path
import tempfile
import unittest

from workflow.ablation import ARMS, load
from workflow.preparation import CONDITION_FOLDERS, prepare_study


@unittest.skipUnless(find_spec('yaml'), 'YAML setup requires PyYAML; install requirements.txt')
class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'project'
        self.config = self.project / 'configs/aideal.yaml'
        self.config.parent.mkdir(parents=True)
        (self.project / 'README.md').write_text('Original public documentation')
        (self.project / 'USAGE.md').write_text('Additional examples')
        self.config.write_text('''extends: [python]
project:
  name: AnyLibrary
codebase:
  source_globs: [src/**/*.py]
  test_globs: [tests/**/*.py]
files:
  original_readme: [README.md, USAGE.md, README.md]
evaluation:
  model: explicit-test-model-no-call
  max_snippet_fixes: 5
''')
        self.output = self.root / 'study'

    def test_yaml_prepares_five_conditions_and_one_shared_document_bundle(self):
        report = prepare_study(self.config, self.output)
        self.assertFalse(report['launched'])
        self.assertEqual('Python', report['source']['language'])
        self.assertEqual(str(self.project.resolve()), report['source']['workspace_root'])
        self.assertEqual(3, len(report['source']['configuration_layers']))
        self.assertEqual(2, len(report['source']['original_documentation']))
        self.assertTrue(report['preflight_issues'])
        plan = load(self.output / 'plan.draft.json')
        self.assertEqual('explicit-test-model-no-call', plan['common']['model'])
        self.assertIsNone(plan['common']['trial_ids'])
        for arm, folder in CONDITION_FOLDERS.items():
            condition = load(self.output / folder / 'condition.json')
            self.assertEqual(ARMS[arm], tuple(condition[k] for k in ('readme', 'aliases', 'error_hints')))
            self.assertEqual('../bank.draft.json', condition['shared_bank'])
            self.assertIsNone(condition['backend_path'])
        text = Path(plan['treatments']['original_readme']['path']).read_text()
        self.assertEqual(1, text.count('Original public documentation'))
        self.assertIn('Additional examples', text)
        self.assertFalse((self.project / '.aideal_exec').exists())

    def test_existing_study_is_never_replaced(self):
        prepare_study(self.config, self.output)
        before = (self.output / 'plan.draft.json').read_bytes()
        with self.assertRaises(FileExistsError):
            prepare_study(self.config, self.output)
        self.assertEqual(before, (self.output / 'plan.draft.json').read_bytes())

    def test_missing_docs_fail_before_output_creation(self):
        self.config.write_text(self.config.read_text().replace('[README.md, USAGE.md, README.md]', '[missing.md]'))
        with self.assertRaisesRegex(ValueError, 'did not resolve'):
            prepare_study(self.config, self.output)
        self.assertFalse(self.output.exists())

    def test_missing_adapter_is_not_silently_ignored_by_study_setup(self):
        self.config.write_text(self.config.read_text().replace('[python]', '[missing-adapter]'))
        with self.assertRaisesRegex(ValueError, 'Unknown extends adapter'):
            prepare_study(self.config, self.output)
        self.assertFalse(self.output.exists())


@unittest.skipUnless(find_spec('yaml'), 'YAML setup requires PyYAML')
class AttachmentTests(unittest.TestCase):
    def test_attach_creates_real_branches_without_changing_the_target(self):
        import subprocess
        from workflow.worktrees import attach
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / 'library'
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
            git('init', '-q')
            git('config', 'user.name', 'Synthetic Test')
            git('config', 'user.email', 'test@example.invalid')
            (repo / 'README.md').write_text('Original docs')
            config = repo / 'configs/aideal.yaml'
            config.parent.mkdir()
            config.write_text('project: {name: AnyLibrary, language: Python}\ncodebase: {source_globs: [src/**/*.py]}\nfiles: {original_readme: README.md}\n')
            git('add', '.')
            git('commit', '-qm', 'Synthetic baseline')
            revision = git('rev-parse', 'HEAD')
            branches = git('branch', '--list')
            result = attach(repo, config, root / 'study')
            self.assertEqual('attached_scaffolded_pending_validation', result['attachment']['status'])
            self.assertEqual(branches, git('branch', '--list'))
            self.assertEqual('', git('status', '--porcelain'))
            harness_hashes = set()
            from workflow.ablation import file_hash
            for item in result['attachment']['worktrees'].values():
                head = subprocess.check_output(['git', '-C', item['path'], 'rev-parse', 'HEAD'], text=True).strip()
                self.assertEqual(revision, head)
                self.assertEqual('Original docs', (Path(item['path']) / 'README.md').read_text())
                instrumentation = Path(item['path']) / '.aideal'
                scaffold = load(instrumentation / 'scaffold.json')
                self.assertFalse(scaffold['evaluation_ready'])
                harness_hashes.add(file_hash(scaffold['harness']['path']))
                self.assertTrue((instrumentation / 'configs/aideal.draft.yaml').is_file())
            self.assertEqual(5, len(result['attachment']['worktrees']))
            self.assertEqual(1, len(harness_hashes))
            self.assertFalse((repo / '.aideal').exists())
            (repo / 'README.md').write_text('Uncommitted user work')
            with self.assertRaisesRegex(ValueError, 'uncommitted'):
                attach(repo, config, root / 'must-not-exist')
            self.assertFalse((root / 'must-not-exist').exists())


if __name__ == '__main__':
    unittest.main()
