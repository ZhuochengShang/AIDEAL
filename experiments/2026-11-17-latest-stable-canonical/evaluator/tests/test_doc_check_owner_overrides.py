"""Source receiver corrections remain explicit, validated and resumable."""
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/aideal_engine/src"))
from aideal.doc_check_inputs import _owner_map, _receiver_hint
from aideal.doc_check_provenance import _comprehension_fingerprint_components
from aideal.config import load_config


class OwnerOverrideTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="aideal-owner-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "Feature.scala").write_text("class Feature {}\nobject Feature {}\n")
        (self.root / "Other.scala").write_text("object Other {}\n")
        self.cfg = SimpleNamespace(root=self.root, comprehension={})
        self.details = [
            {"file": "Feature.scala", "name": "readType"},
            {"file": "Feature.scala", "name": "writeType"},
            {"file": "Other.scala", "name": "readType"},
        ]
        mocked = patch("aideal.readme_agent.public_api_details", return_value=self.details)
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_default_extraction_stays_unchanged(self):
        self.assertEqual({"readType": ("Other", "static"),
                          "writeType": ("Feature", "instance")}, _owner_map(self.cfg))

    def test_explicit_corrections_replace_ambiguous_receiver_guidance(self):
        self.cfg.comprehension["owner_overrides"] = {
            "readType": ["Feature", "static"], "writeType": ["Feature", "static"]}
        owners = _owner_map(self.cfg)
        self.assertEqual(("Feature", "static"), owners["readType"])
        self.assertEqual(("Feature", "static"), owners["writeType"])
        self.assertIn("Feature.readType(...)", _receiver_hint("readType", owners))

    def test_malformed_or_unknown_overrides_fail_closed(self):
        for overrides in ([], {"absent": ["Feature", "static"]},
                          {"readType": "Feature"}, {"readType": ["Bad owner", "static"]},
                          {"readType": ["Feature", "constructor"]}):
            with self.subTest(overrides=overrides):
                self.cfg.comprehension["owner_overrides"] = overrides
                with self.assertRaises(ValueError):
                    _owner_map(self.cfg)

    def test_receiver_override_changes_checkpoint_identity(self):
        (self.root / "configs").mkdir()
        (self.root / "configs/aideal.yaml").write_text(
            "project: {name: sample, language: Scala}\n"
            "models:\n  registry:\n    mock: {provider: mock, model: mock}\n"
            "  roles: {audience: mock, fixer: mock}\n")
        cfg = load_config(self.root / "configs/aideal.yaml")
        args = dict(ex={}, doc_source="original", doc_scope="relevant", max_fix_rounds=0,
                    manifest_sha256="manifest", document_sha256="doc",
                    scaffold_file=self.root / "Feature.scala", sample_data={},
                    class_context=False, timeout=10)
        before = _comprehension_fingerprint_components(cfg, **args)
        cfg.comprehension["owner_overrides"] = {"readType": ["Feature", "static"]}
        after = _comprehension_fingerprint_components(cfg, **args)
        self.assertNotEqual(before["owner_overrides"], after["owner_overrides"])


if __name__ == "__main__":
    unittest.main()
