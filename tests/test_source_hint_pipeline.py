"""Offline end-to-end author/checker evidence through the real Git installer.

The author is a local fixture script, and validation executes real Python
programs against a tiny library. No validation or installer verifier is mocked.
"""
from pathlib import Path
import unittest

import test_source_hint_development as development
from workflow.ablation import load
from workflow.source_hint_installation import LEGACY_HINTS, RECEIPT, install_source_hints
from workflow.source_hints import index_source_hints, strip_source_hints
from workflow.treatment_versions import _run


class SourceHintPipelineTests(unittest.TestCase):
    def test_checked_model_proposal_installs_and_resumes_two_real_branches(self):
        fixture = development.SourceHintDevelopmentTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        validation_path = fixture.validated()
        validation = load(validation_path)
        self.assertEqual(validation['status'], 'validated')
        self.assertEqual(len(validation['checks']), 4)
        self.assertTrue(all(row['valid'] for row in validation['checks']))

        original_head = _run(fixture.source, 'rev-parse', 'HEAD')
        original_branch = _run(fixture.source, 'symbolic-ref', '--short', 'HEAD')
        historical, targets = {}, {}
        for arm in ('error_hints_only', 'combined'):
            root = fixture.root / ('historical-' + arm)
            branch = 'historical/' + arm
            _run(fixture.source, 'worktree', 'add', '-b', branch, str(root), original_head)
            legacy = root / LEGACY_HINTS
            legacy.parent.mkdir(parents=True)
            legacy.write_text('{"hints": [{"status": "historical"}]}\n')
            if arm == 'combined':
                (root / 'aliases.py').write_text('from lib import f\ndef easier_f(x): return f(x)\n')
                (root / '.aideal/treatments/README.md').write_text('Generated documentation.\n')
                (root / '.aideal/treatments/ALIASES.md').write_text('Use easier_f(x).\n')
            _run(root, 'add', '.')
            _run(root, 'commit', '-m', 'Preserved historical fixture treatment')
            parent = _run(root, 'rev-parse', 'HEAD')
            historical[arm] = {'path': root, 'branch': branch, 'commit': parent}
            targets[arm] = {'branch': 'source-guided/' + arm, 'base_revision': parent,
                            'path': str(fixture.root / ('new-' + arm))}

        plan_path, output = fixture.root / 'targets.json', fixture.root / 'installation'
        fixture.write(plan_path, {'schema_version': 1, 'repository': str(fixture.source), 'targets': targets})
        result = install_source_hints(validation_path, plan_path, output)
        self.assertEqual(result['status'], 'installed_validated_development')
        installed_sources, receipts = [], []
        for arm, record in result['targets'].items():
            root = Path(record['path'])
            self.assertEqual(_run(root, 'symbolic-ref', '--short', 'HEAD'), targets[arm]['branch'])
            self.assertEqual(_run(root, 'show', '-s', '--format=%P', record['commit']), targets[arm]['base_revision'])
            source = (root / 'lib.py').read_text()
            index = index_source_hints(root, ['lib.py'], {'lib.f': fixture.identity})
            self.assertEqual(len(index['records']), 1)
            self.assertEqual(index['records'][0]['status'], 'validated_development')
            self.assertEqual(record['hint_count'], 1)
            self.assertEqual(source.count('AIDEAL-HINT-BEGIN'), 1)
            self.assertIn('Evidence: dev-one', source)
            self.assertEqual(strip_source_hints(source), fixture.original)
            self.assertFalse((root / LEGACY_HINTS).exists())
            self.assertTrue(record['removed_legacy_hint_file'])
            self.assertEqual(_run(root, 'status', '--porcelain'), '')
            self.assertEqual(set(_run(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', record['commit']).splitlines()),
                             {'lib.py', LEGACY_HINTS, RECEIPT})
            installed_sources.append(source)
            receipts.append((root / RECEIPT).read_bytes())
        self.assertEqual(installed_sources[0], installed_sources[1])
        self.assertEqual(receipts[0], receipts[1])
        combined = Path(result['targets']['combined']['path'])
        self.assertEqual((combined / 'aliases.py').read_bytes(), (historical['combined']['path'] / 'aliases.py').read_bytes())
        self.assertEqual((combined / '.aideal/treatments/README.md').read_text(), 'Generated documentation.\n')

        application = (output / 'application.json').read_bytes()
        commits = _run(fixture.source, 'rev-list', '--all', '--count')
        self.assertEqual(install_source_hints(validation_path, plan_path, output), result)
        self.assertEqual((output / 'application.json').read_bytes(), application)
        self.assertEqual(_run(fixture.source, 'rev-list', '--all', '--count'), commits)
        self.assertEqual(_run(fixture.source, 'rev-parse', 'HEAD'), original_head)
        self.assertEqual(_run(fixture.source, 'symbolic-ref', '--short', 'HEAD'), original_branch)
        self.assertEqual((fixture.source / 'lib.py').read_text(), fixture.original)
        for old in historical.values():
            self.assertEqual(_run(fixture.source, 'rev-parse', old['branch']), old['commit'])
            self.assertEqual((old['path'] / 'lib.py').read_text(), fixture.original)
            self.assertTrue((old['path'] / LEGACY_HINTS).exists())


if __name__ == '__main__':
    unittest.main()
