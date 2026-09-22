"""A release inventory must detect edits without bringing private study data along."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from workflow.reporting import verify

spec = importlib.util.spec_from_file_location(
    'build_publication_manifest', Path(__file__).resolve().parents[1] / 'scripts/build_publication_manifest.py')
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)


class PublicationManifestTests(unittest.TestCase):
    def test_manifest_is_reproducible_excludes_git_and_detects_source_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'configs').mkdir()
            (root / 'configs/active_arm.json').write_text(json.dumps(
                {'arm': 'original', 'readme': False, 'aliases': False, 'error_hints': False}))
            (root / 'README.md').write_text('portable source')
            (root / '.git').mkdir()
            (root / '.git/config').write_text('not a release artifact')
            first = manifest.generate(root)
            self.assertEqual(first, manifest.generate(root))
            self.assertTrue(verify(root)['verified'])
            self.assertEqual({'README.md', 'configs/active_arm.json'}, {r['path'] for r in first['files']})
            (root / 'README.md').write_text('edited source')
            self.assertEqual(['README.md'], verify(root)['changed'])

    def test_private_fixtures_credentials_and_binary_caches_refuse_publication(self):
        for name in ('studies/example/oracle.json', '.env', '.runs/result.json', 'library.jar'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic private fixture')
                with self.assertRaisesRegex(ValueError, 'Private or generated'):
                    manifest.generate(root)
                self.assertFalse((root / 'evidence/manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
