"""Temporary Git recovery fixtures; no generated library code is executed."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_treatment_versions as fixtures
from workflow.ablation import bind, digest, load
from workflow import source_refactors as refactors


class RefactorRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.TreatmentVersionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.study = self.fixture.study

    def proposal(self, name='one', replacement='def original():\n    return 1\n'):
        folder = self.fixture.root / name
        folder.mkdir()
        source = folder / 'replacement.py'
        source.write_text(replacement)
        baseline = self.fixture.paths['original'] / 'src/library.py'
        proposal = {'schema_version': 1, 'kind': 'source_refactor',
                    'baseline_revision': self.fixture.baseline, 'preserve_public_api': True,
                    'validation_plan': ['Check return and exception behavior through original().'],
                    'changes': [{'path': 'src/library.py',
                                 'before_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
                                 'after': bind(source)}]}
        path = folder / 'proposal.json'
        path.write_text(json.dumps(proposal))
        return path

    def current(self):
        return load(self.study / 'refactors/current.json')['version']

    def test_completed_record_repairs_pointer_after_interrupted_final_write(self):
        proposal = self.proposal()
        version = digest(load(proposal))
        original_record = refactors._record

        def interrupted(path, value):
            if Path(path).name == 'current.json':
                raise OSError('Simulated interruption before pointer write')
            original_record(path, value)

        with patch.object(refactors, '_record', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'Simulated'):
                refactors.install_refactor(self.study, proposal)
        self.assertTrue((self.study / 'refactors' / (version + '.json')).exists())
        self.assertFalse((self.study / 'refactors/current.json').exists())
        record = refactors.install_refactor(self.study, proposal)
        self.assertEqual(version, self.current())
        self.assertEqual('installed_unvalidated', record['status'])
        self.fixture.assert_original_unchanged()

    def test_reapplying_old_version_preserves_newer_current_pointer(self):
        first, second = self.proposal(), self.proposal('two', 'def original():\n    value = 1\n    return value\n')
        old = refactors.install_refactor(self.study, first)
        new = refactors.install_refactor(self.study, second)
        self.assertEqual(old['proposal_sha256'], new['previous_version'])
        pointer = (self.study / 'refactors/current.json').read_bytes()
        self.assertEqual(old, refactors.install_refactor(self.study, first))
        self.assertEqual(pointer, (self.study / 'refactors/current.json').read_bytes())

    def test_missing_pointer_recovers_only_latest_explicit_lineage(self):
        first, second = self.proposal(), self.proposal('two', 'def original():\n    value = 1\n    return value\n')
        refactors.install_refactor(self.study, first)
        new = refactors.install_refactor(self.study, second)
        (self.study / 'refactors/current.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Newer completed'):
            refactors.install_refactor(self.study, first)
        refactors.install_refactor(self.study, second)
        self.assertEqual(new['proposal_sha256'], self.current())

    def test_new_version_cannot_bypass_incomplete_predecessor(self):
        first, second = self.proposal(), self.proposal('two', 'def original():\n    value = 1\n    return value\n')
        original_record = refactors._record

        def interrupted(path, value):
            if Path(path).name == 'current.json':
                raise OSError('Interrupted')
            original_record(path, value)

        with patch.object(refactors, '_record', side_effect=interrupted):
            with self.assertRaises(OSError):
                refactors.install_refactor(self.study, first)
        with self.assertRaisesRegex(ValueError, 'recovery'):
            refactors.install_refactor(self.study, second)

    def test_reuses_baseline_branch_after_worktree_creation_interruption(self):
        proposal = self.proposal()
        original_run = refactors._run

        def interrupted(root, *args):
            if args[:3] == ('worktree', 'add', '-b'):
                original_run(root, 'branch', args[3], args[5])
                raise OSError('Interrupted after branch creation')
            return original_run(root, *args)

        with patch.object(refactors, '_run', side_effect=interrupted):
            with self.assertRaisesRegex(OSError, 'branch creation'):
                refactors.install_refactor(self.study, proposal)
        record = refactors.install_refactor(self.study, proposal)
        self.assertEqual(record['proposal_sha256'], self.current())
        self.fixture.assert_original_unchanged()

    def test_current_temporary_symlink_is_rejected_without_touching_target(self):
        proposal = self.proposal()
        records = self.study / 'refactors'
        records.mkdir()
        victim = self.fixture.root / 'unrelated.txt'
        victim.write_text('preserve me')
        (records / 'current.json.tmp').symlink_to(victim)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            refactors.install_refactor(self.study, proposal)
        self.assertEqual('preserve me', victim.read_text())
        (records / 'current.json.tmp').unlink()
        refactors.install_refactor(self.study, proposal)
        self.assertEqual(digest(load(proposal)), self.current())

    def test_completed_worktree_must_still_belong_to_attached_repository(self):
        proposal = self.proposal()
        record = refactors.install_refactor(self.study, proposal)
        original_run = refactors._run

        def different_repository(root, *args):
            if Path(root) == Path(record['source']) and args == ('rev-parse', '--git-common-dir'):
                return str(self.fixture.root / 'another.git')
            return original_run(root, *args)

        pointer = (self.study / 'refactors/current.json').read_bytes()
        with patch.object(refactors, '_run', side_effect=different_repository):
            with self.assertRaisesRegex(ValueError, 'different repository'):
                refactors.install_refactor(self.study, proposal)
        self.assertEqual(pointer, (self.study / 'refactors/current.json').read_bytes())

    def test_changed_predecessor_record_cannot_be_hidden_by_current_pointer(self):
        first, second = self.proposal(), self.proposal('two', 'def original():\n    value = 1\n    return value\n')
        old = refactors.install_refactor(self.study, first)
        new = refactors.install_refactor(self.study, second)
        path = self.study / 'refactors' / (old['proposal_sha256'] + '.json')
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'Previous refactor record changed'):
            refactors.install_refactor(self.study, second)
        self.assertEqual(new['proposal_sha256'], self.current())

    def test_bad_schema_or_replacement_size_is_rejected_before_records(self):
        for name, mutate in [('schema', lambda v: v.update(schema_version=True)),
                             ('size', lambda v: v['changes'][0]['after'].update(bytes=1))]:
            with self.subTest(name=name):
                proposal = self.proposal(name)
                value = load(proposal)
                mutate(value)
                proposal.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    refactors.install_refactor(self.study, proposal)
                self.assertFalse((self.study / 'refactors').exists())
        self.fixture.assert_original_unchanged()


if __name__ == '__main__':
    unittest.main()
