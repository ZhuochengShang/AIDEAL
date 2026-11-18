"""Offline treatment installation using temporary Git repos; no generated code runs."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from workflow.ablation import digest, load
from workflow.preparation import CONDITION_FOLDERS
from workflow.treatment_versions import apply_treatments
from workflow import treatment_versions as installer


class TreatmentVersionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='aideal-treatments-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'original-checkout'
        self.source.mkdir()
        self.git(self.source, 'init', '-q')
        (self.source / 'src').mkdir()
        (self.source / 'src/library.py').write_text('def original(): return 1\n')
        (self.source / 'README.md').write_text('Original documentation\n')
        (self.source / '.gitattributes').write_text('src/aliases.py filter=never_run\n')
        self.git(self.source, 'add', '.')
        self.git(self.source, 'commit', '-qm', 'Baseline')
        self.baseline = self.git(self.source, 'rev-parse', 'HEAD')
        self.study = self.root / 'study'
        self.study.mkdir()
        self.clone = self.study / 'repository.git'
        self.git(self.study, 'clone', '--bare', '--no-hardlinks', str(self.source), str(self.clone))
        worktrees = {}
        self.paths = {}
        for arm, folder in CONDITION_FOLDERS.items():
            path = self.study / folder / 'source'
            branch = 'aideal/' + arm.replace('_', '-')
            self.git(self.clone, 'worktree', 'add', '-b', branch, str(path), self.baseline)
            scaffold = path / '.aideal/harness/test.py'
            scaffold.parent.mkdir(parents=True)
            scaffold.write_text('raise RuntimeError("Unvalidated skeleton")\n')
            self.paths[arm] = path
            worktrees[arm] = {'path': str(path), 'branch': branch, 'base_revision': self.baseline}
        self.write_json(self.study / 'attachment.json', {
            'status': 'attached_scaffolded_pending_validation', 'revision': self.baseline,
            'repository': str(self.source), 'worktrees': worktrees})
        self.source_snapshot = self.snapshot(self.source)
        self.original_snapshot = self.snapshot(self.paths['original'])

    @staticmethod
    def git(path, *args):
        result = subprocess.run(['git', '-C', str(path), '-c', 'user.name=Fixture',
                                 '-c', 'user.email=fixture@localhost', '-c', 'commit.gpgsign=false',
                                 *args], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    @staticmethod
    def write_json(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n')

    @staticmethod
    def snapshot(path):
        return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*')
                if p.is_file() and '.git' not in p.relative_to(path).parts}

    def proposal(self, name='one', roles=None, alias='src/aliases.py'):
        content = {'readme': b'Improved documentation\n',
                   'alias': b'raise RuntimeError("Generated source must not execute during install")\n',
                   'alias_interface': b'Alias interface contract\n',
                   'error_hints': b'{"hint":"Read the public error explanation"}\n'}
        bindings = {}
        directory = self.root / 'proposals' / name
        directory.mkdir(parents=True)
        for role in content if roles is None else roles:
            path = directory / (role + '.artifact')
            path.write_bytes(content[role] + (name.encode() if role == 'readme' else b''))
            data = path.read_bytes()
            bindings[role] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
            if role == 'alias':
                bindings[role]['target'] = alias
        path = directory / 'proposal.json'
        self.write_json(path, {'schema_version': 1, 'baseline_revision': self.baseline, 'artifacts': bindings})
        return path

    def heads(self):
        return {arm: self.git(path, 'rev-parse', 'HEAD') for arm, path in self.paths.items()}

    def assert_original_unchanged(self):
        self.assertEqual(self.source_snapshot, self.snapshot(self.source))
        self.assertEqual(self.original_snapshot, self.snapshot(self.paths['original']))
        self.assertEqual(self.baseline, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(self.baseline, self.git(self.paths['original'], 'rev-parse', 'HEAD'))
        self.assertEqual('Original documentation\n', (self.paths['original'] / 'README.md').read_text())
        self.assertFalse((self.paths['original'] / '.aideal/treatments').exists())

    def test_routes_exact_bytes_and_only_explicit_paths_without_hooks_or_filters(self):
        proposal = self.proposal()
        marker = self.root / 'unexpected-execution'
        hook = self.root / 'hooks/pre-commit'
        hook.parent.mkdir()
        hook.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 1\n')
        hook.chmod(0o755)
        ref_hook = hook.with_name('reference-transaction')
        ref_hook.write_text(hook.read_text())
        ref_hook.chmod(0o755)
        self.git(self.clone, 'config', 'core.hooksPath', str(hook.parent))
        self.git(self.clone, 'config', 'commit.gpgsign', 'true')
        self.git(self.clone, 'config', 'filter.never_run.clean', f'touch "{marker}"; cat')
        result = apply_treatments(self.study, proposal)
        self.assertEqual('applied_unvalidated', result['status'])
        self.assertEqual('complete_replace_owned', result['bundle_semantics'])
        self.assertFalse(result['evaluated'])
        for arm, entry in result['arms'].items():
            path = self.paths[arm]
            changed = set(self.git(path, 'diff-tree', '--no-commit-id', '--name-only', '-r', entry['commit_revision']).splitlines())
            if arm == 'original':
                self.assertEqual({}, entry['files'])
                continue
            self.assertEqual(set(entry['files']), changed)
            self.assertEqual(self.baseline, entry['parent_revision'])
            self.assertEqual('AIDEAL <aideal@localhost>|AIDEAL <aideal@localhost>',
                             self.git(path, 'show', '-s', '--format=%an <%ae>|%cn <%ce>', entry['commit_revision']))
            for target, binding in entry['files'].items():
                source = load(proposal)['artifacts'][binding['role']]['path']
                self.assertEqual(Path(source).read_bytes(), (path / target).read_bytes())
            self.assertNotIn('.aideal/harness/test.py', self.git(path, 'ls-files').splitlines())
            self.assertEqual('Original documentation\n', (path / 'README.md').read_text())
        self.assertFalse(marker.exists())
        self.assertEqual('true', self.git(self.clone, 'config', '--local', '--get', 'commit.gpgsign'))
        self.assertEqual(str(hook.parent), self.git(self.clone, 'config', 'core.hooksPath'))
        self.assert_original_unchanged()

    def test_current_version_is_idempotent_and_later_complete_bundle_preserves_history(self):
        first = self.proposal()
        result = apply_treatments(self.study, first)
        application = Path(result['application_path'])
        original_record = application.read_bytes()
        heads = self.heads()
        self.assertEqual(result, apply_treatments(self.study, first))
        self.assertEqual(heads, self.heads())
        second = self.proposal('two', roles=['readme'])
        next_result = apply_treatments(self.study, second)
        self.assertEqual(result['proposal_sha256'], next_result['previous_version'])
        self.assertEqual(original_record, application.read_bytes())
        for arm in ('alias_only', 'combined'):
            self.assertFalse((self.paths[arm] / 'src/aliases.py').exists())
            self.assertFalse((self.paths[arm] / '.aideal/treatments/ALIASES.md').exists())
        for arm in ('error_hints_only', 'combined'):
            self.assertFalse((self.paths[arm] / '.aideal/treatments/error_hints.json').exists())
        self.assertEqual(digest(load(second)), load(self.study / 'treatments/current.json')['proposal_sha256'])
        with self.assertRaisesRegex(ValueError, 'historical version'):
            apply_treatments(self.study, first)
        self.assert_original_unchanged()

    def test_alias_updates_only_previously_owned_new_source_path(self):
        first = self.proposal(roles=['alias', 'alias_interface'])
        initial = apply_treatments(self.study, first)
        second = self.proposal('two', roles=['alias', 'alias_interface'])
        updated = load(second)
        source = Path(updated['artifacts']['alias']['path'])
        source.write_bytes(source.read_bytes() + b'# Updated alias version\n')
        updated['artifacts']['alias'].update(sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                            bytes=source.stat().st_size)
        self.write_json(second, updated)
        result = apply_treatments(self.study, second)
        for arm in ('alias_only', 'combined'):
            self.assertEqual(source.read_bytes(), (self.paths[arm] / 'src/aliases.py').read_bytes())
            self.assertEqual(initial['arms'][arm]['commit_revision'], result['arms'][arm]['parent_revision'])
        third = self.proposal('three', roles=['alias', 'alias_interface'], alias='src/next_alias.py')
        moved = apply_treatments(self.study, third)
        for arm in ('alias_only', 'combined'):
            self.assertFalse((self.paths[arm] / 'src/aliases.py').exists())
            self.assertTrue((self.paths[arm] / 'src/next_alias.py').exists())
            self.assertEqual(result['arms'][arm]['commit_revision'], moved['arms'][arm]['parent_revision'])
        self.assert_original_unchanged()

    def test_partial_cross_arm_failure_and_post_commit_interruption_resume(self):
        proposal = self.proposal()
        real = installer._run
        interrupted = False

        def stop_after_branch_update(root, *args):
            nonlocal interrupted
            result = real(root, *args)
            if args[0] == 'update-ref' and Path(root) == self.paths['alias_only'] and not interrupted:
                interrupted = True
                raise RuntimeError('Simulated interruption after a real local commit')
            return result

        with patch.object(installer, '_run', side_effect=stop_after_branch_update):
            with self.assertRaisesRegex(RuntimeError, 'Simulated interruption'):
                apply_treatments(self.study, proposal)
        version = digest(load(proposal))
        journal = self.study / 'treatments' / version / 'journal.json'
        self.assertTrue(journal.exists())
        self.assertFalse((journal.parent / 'application.json').exists())
        self.assertFalse((self.study / 'treatments/current.json').exists())
        completed_head = self.git(self.paths['readme_only'], 'rev-parse', 'HEAD')
        recovered_commit = self.git(self.paths['alias_only'], 'rev-parse', 'HEAD')
        other = self.proposal('other', roles=['readme'])
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            apply_treatments(self.study, other)
        result = apply_treatments(self.study, proposal)
        self.assertEqual(completed_head, result['arms']['readme_only']['commit_revision'])
        self.assertEqual(recovered_commit, result['arms']['alias_only']['commit_revision'])
        self.assert_original_unchanged()

    def test_interruption_with_owned_staged_files_resumes_but_user_edits_do_not(self):
        proposal = self.proposal(roles=['alias', 'alias_interface'])
        real = installer._run

        def stop_before_commit(root, *args):
            if args[0] == 'commit-tree':
                raise RuntimeError('Synthetic commit failure')
            return real(root, *args)

        with patch.object(installer, '_run', side_effect=stop_before_commit):
            with self.assertRaises(RuntimeError):
                apply_treatments(self.study, proposal)
        alias = self.paths['alias_only'] / 'src/aliases.py'
        expected = alias.read_bytes()
        alias.write_text('User changed the pending alias\n')
        with self.assertRaisesRegex(ValueError, 'tracked/source edit'):
            apply_treatments(self.study, proposal)
        self.assertEqual('User changed the pending alias\n', alias.read_text())
        alias.write_bytes(expected)
        self.assertEqual('applied_unvalidated', apply_treatments(self.study, proposal)['status'])

    def test_proposal_validation_and_conflicts_do_not_change_any_branch(self):
        proposal = self.proposal()
        original = load(proposal)
        heads = self.heads()
        outside = self.root / 'outside'
        outside.write_text('outside')
        for label, change in (
                ('baseline', lambda p: p.update(baseline_revision='0' * 40)),
                ('pair', lambda p: p['artifacts'].pop('alias_interface')),
                ('empty', lambda p: p.update(artifacts={})),
                ('tampered', lambda p: p['artifacts']['readme'].update(sha256='0' * 64)),
                ('outside', lambda p: p['artifacts']['readme'].update(path=str(outside))),
                ('traversal', lambda p: p['artifacts']['alias'].update(target='../outside.py')),
                ('git', lambda p: p['artifacts']['alias'].update(target='.git/config')),
                ('reserved', lambda p: p['artifacts']['alias'].update(target='.aideal/harness/new.py')),
                ('tracked', lambda p: p['artifacts']['alias'].update(target='src/library.py')),
                ('directory', lambda p: p['artifacts']['alias'].update(target='src'))):
            with self.subTest(label=label):
                changed = json.loads(json.dumps(original))
                change(changed)
                self.write_json(proposal, changed)
                with self.assertRaises(ValueError):
                    apply_treatments(self.study, proposal)
                self.assertEqual(heads, self.heads())
        self.write_json(proposal, original)
        alias = self.paths['alias_only'] / 'src/aliases.py'
        alias.write_text('User file')
        with self.assertRaisesRegex(ValueError, 'untracked'):
            apply_treatments(self.study, proposal)
        self.assertEqual('User file', alias.read_text())
        self.assert_original_unchanged()

    def test_rejects_source_edits_staged_scaffold_symlinks_and_review_hold(self):
        proposal = self.proposal()
        root = self.paths['combined']
        source = root / 'src/library.py'
        baseline = source.read_bytes()
        source.write_text('User edit\n')
        with self.assertRaisesRegex(ValueError, 'tracked/source edit'):
            apply_treatments(self.study, proposal)
        source.write_bytes(baseline)
        scaffold = root / '.aideal/harness/test.py'
        self.git(root, 'add', str(scaffold))
        with self.assertRaisesRegex(ValueError, 'staged edit'):
            apply_treatments(self.study, proposal)
        self.git(root, 'reset', '-q', 'HEAD', '--', str(scaffold))
        scaffold.unlink()
        scaffold.symlink_to(self.root / 'outside.py')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            apply_treatments(self.study, proposal)
        scaffold.unlink()
        scaffold.write_text('Untracked scaffold restored')
        self.write_json(self.study / 'REVIEW_HOLD.json', {'reason': 'Review pending'})
        with self.assertRaisesRegex(ValueError, 'paused'):
            apply_treatments(self.study, proposal)
        self.assertEqual({arm: self.baseline for arm in CONDITION_FOLDERS}, self.heads())

    def test_artifact_symlink_and_unexpected_head_or_branch_are_rejected(self):
        proposal = self.proposal()
        artifact = Path(load(proposal)['artifacts']['readme']['path'])
        content = artifact.read_bytes()
        target = self.root / 'outside-artifact'
        target.write_bytes(content)
        artifact.unlink()
        artifact.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            apply_treatments(self.study, proposal)
        artifact.unlink()
        artifact.write_bytes(content)
        root = self.paths['readme_only']
        self.git(root, 'checkout', '-qb', 'user-branch')
        with self.assertRaisesRegex(ValueError, 'branch'):
            apply_treatments(self.study, proposal)
        self.git(root, 'checkout', 'aideal/readme-only')
        self.git(root, 'commit', '--allow-empty', '-qm', 'User commit')
        with self.assertRaisesRegex(ValueError, 'HEAD'):
            apply_treatments(self.study, proposal)
        self.assertEqual('User commit', self.git(root, 'show', '-s', '--format=%s', 'HEAD'))

    def test_record_symlinks_and_git_environment_overrides_never_redirect_writes(self):
        proposal = self.proposal(roles=['readme'])
        outside = self.root / 'keep.json'
        outside.write_text('Keep this file')
        version = digest(load(proposal))
        directory = self.study / 'treatments' / version
        directory.mkdir(parents=True)
        (directory / 'journal.json.tmp').symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            apply_treatments(self.study, proposal)
        self.assertEqual('Keep this file', outside.read_text())
        self.assertEqual({arm: self.baseline for arm in CONDITION_FOLDERS}, self.heads())
        (directory / 'journal.json.tmp').unlink()
        for key in ('GIT_INDEX_FILE', 'GIT_AUTHOR_NAME'):
            with patch.dict('os.environ', {key: str(outside)}):
                with self.assertRaisesRegex(ValueError, 'environment overrides'):
                    apply_treatments(self.study, proposal)
        self.assertEqual('Keep this file', outside.read_text())

    def test_journal_cannot_claim_unrelated_source_as_owned(self):
        proposal = self.proposal(roles=['readme'])
        def stop_before_write(*args, **kwargs):
            raise RuntimeError('Synthetic interruption')

        with patch.object(installer, '_install', side_effect=stop_before_write):
            with self.assertRaises(RuntimeError):
                apply_treatments(self.study, proposal)
        journal = self.study / 'treatments' / digest(load(proposal)) / 'journal.json'
        changed = load(journal)
        changed['arms']['readme_only']['removed_paths'] = ['.aideal/harness/test.py']
        self.write_json(journal, changed)
        with self.assertRaisesRegex(ValueError, 'mapping changed'):
            apply_treatments(self.study, proposal)
        self.assertTrue((self.paths['readme_only'] / '.aideal/harness/test.py').exists())
        self.assertEqual({arm: self.baseline for arm in CONDITION_FOLDERS}, self.heads())

    def test_artifact_change_during_application_retains_commits_for_safe_resume(self):
        proposal = self.proposal(roles=['readme'])
        artifact = Path(load(proposal)['artifacts']['readme']['path'])
        expected = artifact.read_bytes()
        real = installer._install

        def change_after_install(root, *args, **kwargs):
            real(root, *args, **kwargs)
            if root == self.paths['combined']:
                artifact.write_bytes(expected + b'Unexpected change')

        with patch.object(installer, '_install', side_effect=change_after_install):
            with self.assertRaisesRegex(ValueError, 'Artifact hash'):
                apply_treatments(self.study, proposal)
        heads = self.heads()
        self.assertFalse((self.study / 'treatments/current.json').exists())
        artifact.write_bytes(expected)
        self.assertEqual('applied_unvalidated', apply_treatments(self.study, proposal)['status'])
        self.assertEqual(heads, self.heads())
        self.assert_original_unchanged()


if __name__ == '__main__':
    unittest.main()
