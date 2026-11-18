"""Whole-library files coexist; refactors stay off the five treatment branches."""
import hashlib
import json
from pathlib import Path
import unittest

import test_treatment_versions as version_fixtures
from workflow.ablation import bind, load
from workflow.treatment_bundles import bundle_proposals
from workflow.treatment_versions import apply_treatments
from workflow.source_refactors import install_refactor, study_versions


class LibraryVersionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = version_fixtures.TreatmentVersionTests(methodName='runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

    def test_multiple_alias_sources_survive_bundle_install_and_match_combined(self):
        f = self.fixture
        proposals = [f.proposal('batch_a', roles=['alias', 'alias_interface'], alias='src/first.py'),
                     f.proposal('batch_b', roles=['alias', 'alias_interface'], alias='src/second.py')]
        result = bundle_proposals(proposals, self.root / 'bundle')
        applied = apply_treatments(f.study, result['proposal'])
        self.assertEqual(2, result['alias_source_files'])
        for target in ('src/first.py', 'src/second.py', '.aideal/treatments/ALIASES.md'):
            self.assertEqual((f.paths['alias_only'] / target).read_bytes(),
                             (f.paths['combined'] / target).read_bytes())
            self.assertFalse((f.paths['original'] / target).exists())
        self.assertEqual(applied, apply_treatments(f.study, result['proposal']))
        f.assert_original_unchanged()

    def test_legacy_hints_require_opt_in_and_default_install_keeps_native_targets_clear(self):
        f = self.fixture
        source = f.proposal('mixed')
        original = load(source)
        hints_path = Path(original['artifacts']['error_hints']['path'])
        hints = [{'function_id': 'src/library.py:1:original',
                  'match': 'invalid value', 'hint': 'Use the supported argument.'}]
        f.write_json(hints_path, {'schema_version': 1, 'hints': hints})
        original['artifacts']['error_hints'] = bind(hints_path)
        f.write_json(source, original)
        source_bytes, hint_bytes = source.read_bytes(), hints_path.read_bytes()

        for include, folder in ((False, 'current'), (True, 'legacy')):
            with self.subTest(include_legacy_hints=include):
                bundled = (bundle_proposals([source], self.root / folder, include_legacy_hints=True)
                           if include else bundle_proposals([source], self.root / folder))
                proposal = load(bundled['proposal'])
                receipt = load(proposal['legacy_hint_selection']['path'])
                self.assertEqual(int(include), bundled['hints'])
                self.assertEqual(int(not include), bundled['omitted_legacy_hints'])
                self.assertEqual(1, receipt['candidate_count'])
                self.assertEqual(int(include), receipt['installed_count'])
                self.assertEqual(int(not include), receipt['omitted_count'])
                self.assertEqual([original['artifacts']['error_hints']], receipt['source_artifacts'])
                self.assertEqual([{**hints[0], 'status': 'unverified'}], receipt['candidates'])
                self.assertEqual(include, 'error_hints' in proposal['artifacts'])
                self.assertEqual(source_bytes, (self.root / folder / 'batch_0001.json').read_bytes())
                applied = apply_treatments(f.study, bundled['proposal'])
                for arm in ('error_hints_only', 'combined'):
                    installed = f.paths[arm] / '.aideal/treatments/error_hints.json'
                    self.assertEqual(include, installed.exists())
                    if include:
                        self.assertEqual(receipt['candidates'], load(installed)['hints'])
                    self.assertNotIn('.aideal/treatments/legacy_hint_selection.json',
                                     applied['arms'][arm]['files'])
                before = Path(bundled['proposal']).read_bytes()
                with self.assertRaises(FileExistsError):
                    bundle_proposals([source], self.root / folder,
                                     include_legacy_hints=not include)
                self.assertEqual(before, Path(bundled['proposal']).read_bytes())
        self.assertEqual(source_bytes, source.read_bytes())
        self.assertEqual(hint_bytes, hints_path.read_bytes())
        f.assert_original_unchanged()

    def test_bundle_rejects_collisions_and_mismatched_baselines_before_output(self):
        f = self.fixture
        first = f.proposal('a', roles=['alias', 'alias_interface'])
        second = f.proposal('b', roles=['alias', 'alias_interface'])
        with self.assertRaisesRegex(ValueError, 'Duplicate alias source'):
            bundle_proposals([first, second], self.root / 'bundle')
        self.assertFalse((self.root / 'bundle').exists())
        record = load(second)
        record['baseline_revision'] = '0' * 40
        f.write_json(second, record)
        with self.assertRaisesRegex(ValueError, 'baseline revision'):
            bundle_proposals([first, second], self.root / 'bundle')

    def test_bundle_rejects_file_directory_prefix_before_installation(self):
        f = self.fixture
        first = f.proposal('first', roles=['alias', 'alias_interface'], alias='src/aliases.py')
        second = f.proposal('second', roles=['alias', 'alias_interface'], alias='src/aliases.py/other.py')
        with self.assertRaisesRegex(ValueError, 'path prefix'):
            bundle_proposals([first, second], self.root / 'bundle')
        self.assertFalse((self.root / 'bundle').exists())
        self.assertEqual({arm: f.baseline for arm in f.paths}, f.heads())

    def test_refactor_review_is_preserved_without_becoming_an_alias(self):
        f = self.fixture
        alias = f.proposal('aliases', roles=['alias', 'alias_interface'])
        review_dir = self.root / 'review'
        review_dir.mkdir()
        review = review_dir / 'refactors.json'
        review.write_text('{"status":"unverified","refactors":[]}\n')
        path = review_dir / 'proposal.json'
        f.write_json(path, {'schema_version': 1, 'baseline_revision': f.baseline,
                           'status': 'review_candidates_only', 'artifacts': {},
                           'refactor_suggestions': bind(review)})
        result = bundle_proposals([alias, path], self.root / 'bundle')
        combined = load(result['proposal'])
        self.assertEqual(1, len(combined['refactor_reviews']))
        self.assertEqual({'alias_0001', 'alias_interface'}, set(combined['artifacts']))
        apply_treatments(f.study, result['proposal'])
        self.assertFalse((f.paths['combined'] / 'refactors.json').exists())

    def refactor(self):
        f = self.fixture
        directory = self.root / 'refactor-proposal'
        directory.mkdir()
        replacement = directory / 'library.py'
        replacement.write_text('def original():\n    return int(True)\n')
        path = directory / 'proposal.json'
        f.write_json(path, {'schema_version': 1, 'kind': 'source_refactor',
            'baseline_revision': f.baseline, 'preserve_public_api': True,
            'validation_plan': ['Check original() returns integer 1; same public signature.'],
            'changes': [{'path': 'src/library.py',
                         'before_sha256': hashlib.sha256((f.source / 'src/library.py').read_bytes()).hexdigest(),
                         'after': bind(replacement)}]})
        return path

    def test_refactor_is_separate_version_commit_and_original_stays_unchanged(self):
        f = self.fixture
        proposal = self.refactor()
        before = f.heads()
        result = install_refactor(f.study, proposal)
        self.assertEqual('installed_unvalidated', result['status'])
        self.assertEqual(before, f.heads())
        self.assertNotEqual(f.baseline, result['commit_revision'])
        self.assertEqual(f.baseline, f.git(Path(result['source']), 'rev-parse', 'HEAD^'))
        self.assertEqual(result, install_refactor(f.study, proposal))
        source = Path(result['source']) / 'src/library.py'
        self.assertIn('int(True)', source.read_text())
        self.assertEqual(6, len(study_versions(f.study)['conditions']))
        source.write_text('user edit\n')
        with self.assertRaises(ValueError):
            install_refactor(f.study, proposal)
        self.assertEqual('user edit\n', source.read_text())
        f.assert_original_unchanged()

    def test_refactor_rejects_stale_before_hash_or_implicit_delete(self):
        f = self.fixture
        proposal = self.refactor()
        record = load(proposal)
        record['changes'][0]['before_sha256'] = '0' * 64
        f.write_json(proposal, record)
        with self.assertRaisesRegex(ValueError, 'before_sha256'):
            install_refactor(f.study, proposal)
        self.assertFalse((f.study / 'Refactor only').exists())
        record['changes'][0].pop('after')
        f.write_json(proposal, record)
        with self.assertRaisesRegex(ValueError, 'explicit after'):
            install_refactor(f.study, proposal)


if __name__ == '__main__':
    unittest.main()
