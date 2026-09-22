"""Generated harnesses must remain isolated, identical and explicitly unvalidated."""
from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from workflow.ablation import load
from workflow.scaffolding import scaffold_spec, write_scaffold


@unittest.skipUnless(find_spec('yaml'), 'Scaffolding requires the existing YAML dependency')
class ScaffoldingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'library'
        self.config = self.repo / 'configs/aideal.yaml'
        self.config.parent.mkdir(parents=True)
        self.config.write_text('project: {name: ArbitraryLibrary, language: Python}\n'
                               'codebase: {source_globs: [src/**/*.py]}\n')
        self.worktree = self.root / 'condition/source'
        self.worktree.mkdir(parents=True)
        self.study = self.root / 'study'
        self.study.mkdir()

    def test_empty_generated_harness_cannot_pass_and_paths_use_the_worktree(self):
        cfg, spec = scaffold_spec(self.config)
        record = write_scaffold(self.worktree, self.repo, self.study, cfg, spec)
        run = subprocess.run([sys.executable, record['harness']['path']], capture_output=True, text=True)
        self.assertNotEqual(0, run.returncode)
        self.assertIn('NotImplementedError', run.stderr)
        self.assertFalse(record['evaluation_ready'])
        from workflow.preparation import _engine_config_module
        resolved = _engine_config_module().load_config(record['configuration']['path'])
        self.assertEqual([str(self.worktree / 'src/**/*.py')], resolved.source_globs)
        self.assertFalse((self.repo / '.aideal').exists())
        self.assertEqual(record, load(self.worktree / '.aideal/scaffold.json'))

    def test_existing_evaluation_workspace_is_not_overwritten(self):
        cfg, spec = scaffold_spec(self.config)
        existing = self.worktree / '.aideal'
        existing.mkdir()
        (existing / 'keep.txt').write_text('Existing user work')
        with self.assertRaises(FileExistsError):
            write_scaffold(self.worktree, self.repo, self.study, cfg, spec)
        self.assertEqual('Existing user work', (existing / 'keep.txt').read_text())
        self.assertFalse((existing / 'harness').exists())

    def test_configured_harness_is_copied_without_modifying_its_source(self):
        source = self.repo / 'existing_test.py'
        source.write_text('# Existing project harness\nraise RuntimeError("pending test")\n')
        self.config.write_text(self.config.read_text() +
                               'comprehension:\n  execute:\n    scaffold: existing_test.py\n')
        cfg, spec = scaffold_spec(self.config)
        record = write_scaffold(self.worktree, self.repo, self.study, cfg, spec)
        self.assertEqual('configured_harness', record['method'])
        self.assertEqual(source.read_bytes(), Path(record['harness']['path']).read_bytes())
        self.assertFalse(record['evaluation_ready'])

    def test_custom_language_uses_yaml_frame_and_rejects_unsafe_filename(self):
        self.config.write_text('project: {language: CustomLanguage}\n'
                               'comprehension:\n  execute:\n    scaffold_frame: "custom frame {imports}"\n'
                               '    imports: [library]\n    test_filename: test.custom\n')
        _, spec = scaffold_spec(self.config)
        self.assertEqual('custom frame library', spec['text'])
        self.config.write_text(self.config.read_text().replace('test.custom', '../outside.custom'))
        with self.assertRaisesRegex(ValueError, 'filename'):
            scaffold_spec(self.config)


if __name__ == '__main__':
    unittest.main()
