import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('continuation', Path(__file__).with_name('alias_continuation.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContinuationTests(unittest.TestCase):
    def test_exact_partition_accepts_original_union(self):
        m.verify_partition(['a','b','c'], ['a'], ['c','b'])

    def test_missing_extra_overlap_or_duplicate_identity_rejected(self):
        for prefix, remaining in [(['a'],['b']), (['a'],['b','c','d']), (['a','b'],['b','c']),
                                  (['a'],['b','b','c']), (['a','a'],['b','c'])]:
            with self.subTest(prefix=prefix, remaining=remaining), self.assertRaises(ValueError):
                m.verify_partition(['a','b','c'],prefix,remaining)

    def test_duplicate_aliases_or_existing_names_rejected(self):
        for names in [['new','new'], ['original']]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                m.verify_alias_names(names, ['original'])
        m.verify_alias_names(['new','other'],['original'])

    def test_tampered_manifest_or_preview_rejected(self):
        class Fake:
            def __init__(self, manifest, verify):self.value,self.verify=manifest,verify
            def load(self,path):return self.value
            def digest(self,value):return 'valid'
            def verify_artifact(self,ref):return self.verify
        for manifest, verify in [({'manifest_sha256':'tampered'}, True),
                                  ({'manifest_sha256':'valid','artifacts':[{}]},False),
                                  ({'manifest_sha256':'valid','artifacts':[],'batches':[{'preview':{}}]},False)]:
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                m.verified_manifest('unused',Fake(manifest,verify))


if __name__ == '__main__':
    unittest.main()
