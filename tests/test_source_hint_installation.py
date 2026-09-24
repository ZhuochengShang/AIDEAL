"""Offline Git integration checks for installing and resuming source hints.

Only development verification is mocked. Real temporary repositories exercise
annotation parsing, branch/worktree creation, commit contents and receipts.
No library study, model endpoint or user's checkout is touched.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import bind, load
from workflow.source_hint_installation import (
    LEGACY_HINTS, RECEIPT, install_source_hints,
)
from workflow.source_hints import insert_source_hint, strip_source_hints
from workflow.treatment_versions import _run


SOURCE = ('object RasterMetadata {\n'
          '  def rescale(width: Int, height: Int): String = width.toString\n'
          '}\n')


class SourceHintInstallationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-source-install-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.repo = self.base / 'repository'
        self.repo.mkdir()
        _run(self.repo, 'init', '-b', 'original')
        self.relative = 'src/RasterMetadata.scala'
        self.source = self.repo / self.relative
        self.source.parent.mkdir()
        self.source.write_text(SOURCE)
        (self.repo / 'README.md').write_text('Original library documentation.\n')
        _run(self.repo, 'add', '.')
        _run(self.repo, 'commit', '-m', 'Original library baseline')
        self.baseline = _run(self.repo, 'rev-parse', 'HEAD')
        self.historical = {}
        self.plan = {'schema_version': 1, 'repository': str(self.repo), 'targets': {}}
        for arm in ('error_hints_only', 'combined'):
            branch = 'historical/' + arm
            root = self.base / ('historical-' + arm)
            _run(self.repo, 'worktree', 'add', '-b', branch, str(root), self.baseline)
            legacy = root / LEGACY_HINTS
            legacy.parent.mkdir(parents=True)
            legacy.write_text('{"delivery": "legacy prompt hints"}\n')
            if arm == 'combined':
                (root / '.aideal/treatments/README.md').write_text('Generated README.\n')
                (root / 'src/Aliases.scala').write_text('object Aliases {}\n')
            _run(root, 'add', '.')
            _run(root, 'commit', '-m', 'Historical treatment artifacts')
            parent = _run(root, 'rev-parse', 'HEAD')
            self.historical[arm] = {'root': root, 'branch': branch, 'commit': parent}
            self.plan['targets'][arm] = {
                'branch': 'source-hints/' + arm, 'base_revision': parent,
                'path': str(self.base / ('new-' + arm)),
            }
        self.identity = self.relative + ':2:rescale'
        fields = {
            'requirement_id': 'integer_dimensions',
            'requirement': 'Pixel dimensions must have type Int.',
            'diagnostic': 'required: Int',
            'action': 'Choose integer pixel counts with explicit rounding.',
            'validation': 'Development replay and negative controls passed.',
            'status': 'validated_development',
        }
        self.edited = insert_source_hint(SOURCE, self.identity, fields)
        self.artifact = self.base / 'verified-source.scala'
        self.artifact.write_text(self.edited)
        self.validation = {
            'status': 'validated', 'source_root': str(self.repo),
            'baseline_revision': self.baseline,
            'api_function_ids': {'example.RasterMetadata.rescale': self.identity},
            'installable_sources': [{
                'path': self.relative, 'artifact': bind(self.artifact),
                'baseline_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
            }],
        }
        self.validation_path = self.base / 'validation.json'
        self.validation_path.write_text(json.dumps(self.validation))
        self.plan_path = self.base / 'targets.json'
        self.save_plan()
        self.output = self.base / 'installation'

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def install(self):
        # The development verifier has separate replay/identity integration tests.
        with patch('workflow.source_hint_installation._validated',
                   return_value=copy.deepcopy(self.validation)):
            return install_source_hints(self.validation_path, self.plan_path, self.output)

    def assert_history_unchanged(self):
        self.assertEqual(_run(self.repo, 'rev-parse', 'HEAD'), self.baseline)
        self.assertEqual(_run(self.repo, 'symbolic-ref', '--short', 'HEAD'), 'original')
        for old in self.historical.values():
            self.assertEqual(_run(self.repo, 'rev-parse', old['branch']), old['commit'])
            self.assertEqual(_run(old['root'], 'rev-parse', 'HEAD'), old['commit'])
            self.assertEqual((old['root'] / self.relative).read_text(), SOURCE)
            self.assertTrue((old['root'] / LEGACY_HINTS).exists())

    def assert_no_new_worktrees(self):
        self.assertFalse(self.output.exists())
        refs = _run(self.repo, 'for-each-ref', '--format=%(refname)', 'refs/heads')
        for item in self.plan['targets'].values():
            self.assertFalse(Path(item['path']).exists())
            self.assertNotIn('refs/heads/' + item['branch'] + '\n', refs + '\n')
        self.assert_history_unchanged()

    def test_new_branches_have_identical_comment_sources_and_preserve_history(self):
        result = self.install()
        self.assertEqual(result['status'], 'installed_validated_development')
        self.assertEqual(set(result['targets']), {'error_hints_only', 'combined'})
        receipts = []
        for arm, record in result['targets'].items():
            root = Path(record['path'])
            self.assertEqual(_run(root, 'symbolic-ref', '--short', 'HEAD'),
                             self.plan['targets'][arm]['branch'])
            self.assertEqual(_run(root, 'show', '-s', '--format=%P', record['commit']),
                             self.plan['targets'][arm]['base_revision'])
            self.assertEqual((root / self.relative).read_text(), self.edited)
            self.assertEqual(strip_source_hints((root / self.relative).read_text()), SOURCE)
            self.assertFalse((root / LEGACY_HINTS).exists())
            self.assertTrue(record['removed_legacy_hint_file'])
            self.assertEqual(record['hint_count'], 1)
            self.assertEqual(record['coverage']['covered_functions'], 1)
            changed = set(_run(root, 'diff-tree', '--no-commit-id', '--name-only',
                               '-r', record['commit']).splitlines())
            self.assertEqual(changed, {self.relative, RECEIPT, LEGACY_HINTS})
            receipts.append((root / RECEIPT).read_bytes())
        self.assertEqual(receipts[0], receipts[1])
        combined = Path(result['targets']['combined']['path'])
        self.assertEqual((combined / 'src/Aliases.scala').read_text(), 'object Aliases {}\n')
        self.assertEqual((combined / '.aideal/treatments/README.md').read_text(),
                         'Generated README.\n')
        self.assertEqual(self.source.read_text(), SOURCE)
        self.assert_history_unchanged()

    def test_exact_resume_is_checked_noop(self):
        first = self.install()
        receipt_bytes = (self.output / 'application.json').read_bytes()
        with patch('workflow.source_hint_installation._install',
                   side_effect=AssertionError('Resume must not reinstall')):
            self.assertEqual(self.install(), first)
        self.assertEqual((self.output / 'application.json').read_bytes(), receipt_bytes)
        self.assert_history_unchanged()

    def test_tampered_validated_artifact_is_rejected_before_branch_creation(self):
        self.artifact.write_text(self.edited + '// changed after validation\n')
        with self.assertRaisesRegex(ValueError, 'modified validated source'):
            self.install()
        self.assert_no_new_worktrees()

    def test_changed_baseline_source_is_rejected_before_branch_creation(self):
        self.source.write_text(SOURCE.replace('width.toString', 'height.toString'))
        with self.assertRaisesRegex(ValueError, 'Baseline source hash changed'):
            self.install()
        self.assert_no_new_worktrees()

    def test_noncomment_change_is_rejected_even_with_updated_artifact_binding(self):
        self.artifact.write_text(self.edited.replace('width.toString', 'height.toString'))
        self.validation['installable_sources'][0]['artifact'] = bind(self.artifact)
        with self.assertRaisesRegex(ValueError, 'changes executable source'):
            self.install()
        self.assert_no_new_worktrees()

    def test_existing_branch_is_rejected_without_advancing_it(self):
        arm = 'error_hints_only'
        self.plan['targets'][arm]['branch'] = self.historical[arm]['branch']
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'branch already exists'):
            self.install()
        self.assertFalse(self.output.exists())
        self.assert_history_unchanged()
        self.assertFalse(Path(self.plan['targets']['combined']['path']).exists())

    def test_changed_target_parent_library_is_rejected_before_branch_creation(self):
        arm = 'combined'
        root = self.historical[arm]['root']
        (root / self.relative).write_text(SOURCE.replace('width.toString', 'height.toString'))
        _run(root, 'add', self.relative)
        _run(root, 'commit', '-m', 'Different library behavior')
        parent = _run(root, 'rev-parse', 'HEAD')
        self.historical[arm]['commit'] = parent
        self.plan['targets'][arm]['base_revision'] = parent
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'changed baseline library'):
            self.install()
        self.assertFalse(self.output.exists())
        for item in self.plan['targets'].values():
            self.assertFalse(Path(item['path']).exists())
        self.assertEqual(_run(root, 'rev-parse', 'HEAD'), parent)

    def test_nested_worktree_destination_is_rejected_before_creation(self):
        self.plan['targets']['combined']['path'] = str(self.repo / 'nested-study')
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'destinations overlap source'):
            self.install()
        self.assert_no_new_worktrees()

    def test_changed_validation_or_plan_does_not_resume(self):
        self.install()
        self.plan['targets']['combined']['branch'] = 'different/combined'
        self.save_plan()
        with self.assertRaisesRegex(ValueError, 'another or incomplete version'):
            self.install()
        self.assert_history_unchanged()

    def test_resume_rejects_modified_worktree_source(self):
        result = self.install()
        root = Path(result['targets']['combined']['path'])
        (root / self.relative).write_text(self.edited + '// local edit\n')
        with self.assertRaisesRegex(ValueError, 'changed tracked/source edit'):
            self.install()
        self.assert_history_unchanged()

    def test_resume_rejects_new_unrecorded_commit(self):
        result = self.install()
        root = Path(result['targets']['combined']['path'])
        _run(root, 'commit', '--allow-empty', '-m', 'Unrecorded later commit')
        with self.assertRaisesRegex(ValueError, 'Installed branch changed'):
            self.install()
        self.assert_history_unchanged()

    def test_resume_rejects_receipt_missing_condition(self):
        self.install()
        path = self.output / 'application.json'
        receipt = load(path)
        del receipt['targets']['combined']
        path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            self.install()

    def test_resume_rejects_receipt_rebound_to_other_condition(self):
        self.install()
        path = self.output / 'application.json'
        receipt = load(path)
        receipt['targets']['combined'] = copy.deepcopy(receipt['targets']['error_hints_only'])
        path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            self.install()

    def test_resume_rejects_checked_out_different_branch_at_same_commit(self):
        result = self.install()
        root = Path(result['targets']['combined']['path'])
        _run(root, 'checkout', '-b', 'unrelated/combined', result['targets']['combined']['commit'])
        with self.assertRaises(ValueError):
            self.install()

    def test_resume_rejects_amended_commit_with_extra_file_and_rebound_hash(self):
        result = self.install()
        root = Path(result['targets']['combined']['path'])
        (root / 'src/Unvalidated.scala').write_text('object Unvalidated {}\n')
        _run(root, 'add', 'src/Unvalidated.scala')
        _run(root, 'commit', '--amend', '--no-edit')
        receipt_path = self.output / 'application.json'
        receipt = load(receipt_path)
        receipt['targets']['combined']['commit'] = _run(root, 'rev-parse', 'HEAD')
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            self.install()

    def test_resume_rejects_forged_legacy_removal_receipt(self):
        self.install()
        path = self.output / 'application.json'
        receipt = load(path)
        receipt['targets']['combined']['removed_legacy_hint_file'] = False
        path.write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):
            self.install()


if __name__ == '__main__':
    unittest.main()
