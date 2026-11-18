"""Constructor targets must not be described as same-named instance methods."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/aideal_engine/src"))
from aideal.doc_check_inputs import _owner_map, _receiver_hint
from aideal.config import load_config
from aideal.prompts import load as load_prompt


class ConstructorReceiverHintTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="aideal-class-receiver-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cfg = SimpleNamespace(root=self.root, comprehension={})

    def owners(self, *details):
        with patch("aideal.readme_agent.public_api_details", return_value=list(details)):
            return _owner_map(self.cfg)

    @staticmethod
    def declaration(owner="sample.Tile", name="Tile", kind="class_constructor",
                    owner_kind="class"):
        api_id = "scala:" + (owner if kind == "class_constructor" else owner_kind + ":" + owner + "." + name)
        return dict(api_id=api_id, name=name, owner=owner, owner_kind=owner_kind,
                    kind=kind, file="source/Tile.scala", is_abstract=False)

    def test_class_target_is_not_a_same_named_instance_method(self):
        row = self.declaration()
        owners = self.owners(row)
        self.assertEqual(("sample.Tile", "type"), owners[row["api_id"]])
        hint = _receiver_hint(row["api_id"], owners)
        self.assertIn("CLASS/TYPE `sample.Tile`", hint)
        self.assertIn("documented construction pattern", hint)
        self.assertNotIn("INSTANCE method", hint)
        self.assertNotIn("then call `.Tile`", hint)

    def test_abstract_itile_does_not_require_direct_instantiation(self):
        # The frozen Scala constructor row has is_abstract=False even though its
        # enclosing ITile class is abstract. Do not trust that flag as a promise
        # of direct construction, and do not hard-code RDPro-specific knowledge.
        row = self.declaration("edu.ucr.cs.bdlab.beast.geolite.ITile", "ITile")
        hint = _receiver_hint(row["api_id"], self.owners(row))
        self.assertIn("documented concrete implementation", hint)
        self.assertIn("valid subclass", hint)
        self.assertIn("instead of directly instantiating the abstract type", hint)
        self.assertNotIn("then call `.ITile`", hint)
        self.assertNotIn("new ITile", hint)

    def test_normal_instance_method_preserves_receiver_instruction(self):
        row = self.declaration(name="getPixelValue", kind="method")
        owners = self.owners(row)
        self.assertEqual(("sample.Tile", "instance"), owners[row["api_id"]])
        hint = _receiver_hint(row["api_id"], owners)
        self.assertIn("INSTANCE method on `sample.Tile`", hint)
        self.assertIn("then call `.getPixelValue`", hint)
        self.assertNotIn("CLASS/TYPE", hint)

    def test_static_companion_method_preserves_call_expression(self):
        row = self.declaration(name="create", kind="method", owner_kind="object")
        owners = self.owners(row)
        self.assertEqual(("sample.Tile", "static"), owners[row["api_id"]])
        hint = _receiver_hint(row["api_id"], owners)
        self.assertIn("sample.Tile.create(...)", hint)
        self.assertNotIn("CLASS/TYPE", hint)

    def test_method_named_like_its_class_is_still_a_method(self):
        row = self.declaration(name="Tile", kind="method")
        hint = _receiver_hint(row["api_id"], self.owners(row))
        self.assertIn("INSTANCE method", hint)
        self.assertIn("then call `.Tile`", hint)

    def test_definition_kind_survives_consumer_schema_normalization(self):
        row = self.declaration()
        row["definition_kind"] = "constructor"
        row["kind"] = "class"
        self.assertEqual("type", self.owners(row)[row["api_id"]][1])

    def test_type_guidance_reaches_actual_audience_template_without_source(self):
        (self.root / "configs").mkdir()
        (self.root / "configs/aideal.yaml").write_text(
            "project: {name: sample, language: Scala}\n"
            "models:\n  registry:\n    fake: {provider: mock, model: no-provider}\n"
            "  roles: {audience: fake}\n")
        cfg = load_config(self.root / "configs/aideal.yaml")
        row = self.declaration("edu.ucr.cs.bdlab.beast.geolite.ITile", "ITile")
        row["body"] = "SECRET_IMPLEMENTATION_BODY"
        hint = _receiver_hint(row["api_id"], self.owners(row))
        messages = load_prompt(cfg, "aideal/comprehension_write_exec",
            api_body="Supplied original documentation.", api_name=row["api_id"],
            available_inputs="No preloaded object.", receiver=hint, known_failures="none",
            execution_context="Scala 2.12; return body statements.", exec_hints="", io_hints="")
        delivered = "\n".join(messages)
        self.assertIn("CLASS/TYPE", delivered)
        self.assertIn("valid subclass", delivered)
        self.assertNotIn("INSTANCE method on", delivered)
        self.assertNotIn("SECRET_IMPLEMENTATION_BODY", delivered)


if __name__ == "__main__":
    unittest.main()
