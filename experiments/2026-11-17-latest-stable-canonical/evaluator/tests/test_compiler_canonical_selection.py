"""Global canonical receipt binding and author-facing definition boundaries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/aideal_engine/src"))
from aideal.api_canonical_selection import POLICY_VERSION, select_canonical_implementations
from aideal.api_registry import configured_api_details
from aideal.api_discovery import public_api_details, public_api_surface


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CompilerCanonicalSelectionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "source").mkdir()
        self.records = []
        for language, filename, methods in [
            ("Java", "Tools.java", [
                ("jshort", "add", "(int x):int", "public static int add(int x) { return x + 1; }", 1),
                ("jlong", "add", "(int x,int y,int z):int", "public static int add(int x, int y, int z) { return x + y + z; }", 3),
                ("jwrap", "wrap", "(int x):int", "public static int wrap(int x) { return add(x); }", 1),
            ]),
            ("Scala", "Tools.scala", [
                ("scala", "add", "[](x:Int,y:Int):Int", "def add(x: Int, y: Int): Int = x + y", 2),
                ("other", "subtract", "[](x:Int,y:Int):Int", "def subtract(x: Int, y: Int): Int = x - y", 2),
            ]),
        ]:
            prefix = "class Tools {\n"
            text = prefix + "\n".join(method[3] for method in methods) + "\n}\n"
            source = self.root / "source" / filename
            source.write_text(text)
            for site_id, name, signature, declaration, count in methods:
                start = text.index(declaration)
                self.records.append({"site_id": site_id, "language": language, "kind": "method",
                    "scope": "production", "declared_visibility": "public", "public_owner_chain": True,
                    "synthetic": False, "path": filename, "source_sha256": sha(source), "name": name,
                    "owner": "Tools", "qualified_name": "Tools." + name, "line": text[:start].count("\n") + 1,
                    "start": start, "end": start + len(declaration), "signature": signature,
                    "parameter_count": count})
        self.inventory_path = self.root / "compiler.json"
        self.inventory_path.write_text(json.dumps({"schema_version": 1, "records": self.records}))
        self.contract_path = self.root / "contract.json"
        self.contract_path.write_text('{"status":"passed"}')
        audited = deepcopy(self.records)
        for row in audited:
            row["body_classification"] = {"category": "direct_forwarder" if row["site_id"] == "jwrap" else "implementation",
                                          "reviewed": True, "evidence": {"reviewer": "fixture", "body": "inspected"}}
        self.receipt = {"schema": 1, "kind": "compiler_global_canonical_selection",
                        "policy_version": POLICY_VERSION, "source_inventory_sha256": sha(self.inventory_path),
                        "selection": select_canonical_implementations(audited)}
        self.receipt_path = self.root / "selection.json"
        self.definition = {"schema": 1, "kind": "compiler_declared_methods", "language": "Java",
            "source_root": "source", "source_inventory": str(self.inventory_path),
            "source_inventory_sha256": sha(self.inventory_path), "parser_contract": str(self.contract_path),
            "parser_contract_sha256": sha(self.contract_path), "declaration_ids": ["jshort", "jlong", "jwrap"],
            "canonical_selection": str(self.receipt_path), "canonical_selection_policy_version": POLICY_VERSION,
            "canonical_declaration_ids": ["jlong"]}
        self.definition_path = self.root / "api_inventory.json"
        self.cfg = SimpleNamespace(root=self.root, language="Java", surface_filter="all", exclude_names=[], raw={"codebase": {}})
        self.freeze()

    def freeze(self):
        self.receipt_path.write_text(json.dumps(self.receipt))
        if "canonical_selection" in self.definition:
            self.definition["canonical_selection_sha256"] = sha(self.receipt_path)
        self.definition_path.write_text(json.dumps(self.definition))
        self.cfg.raw["codebase"].update(api_inventory=str(self.definition_path), api_inventory_sha256=sha(self.definition_path))

    def test_author_facts_contain_only_winning_definition_and_its_parameters(self):
        details = public_api_details(self.cfg)
        self.assertEqual(["jlong"], [row["site_id"] for row in details])
        self.assertEqual({"add"}, public_api_surface(self.cfg))
        self.assertEqual(["x", "y", "z"], [p["name"] for p in details[0]["params"]])
        self.assertEqual("Tools", details[0]["owner"])
        self.assertIn("int z", details[0]["signature"])
        self.assertEqual("(int x,int y,int z):int", details[0]["compiler_signature"])

    def test_other_language_receives_its_disjoint_global_winners(self):
        self.cfg.language = self.definition["language"] = "Scala"
        self.definition["declaration_ids"] = ["scala", "other"]
        self.definition["canonical_declaration_ids"] = ["other"]
        self.freeze()
        self.assertEqual({"subtract"}, public_api_surface(self.cfg))
        self.assertEqual(["other"], [row["site_id"] for row in public_api_details(self.cfg)])

    def test_no_opt_in_preserves_the_complete_legacy_public_inventory(self):
        for key in list(self.definition):
            if key.startswith("canonical_"):
                del self.definition[key]
        self.freeze()
        self.assertEqual(["jshort", "jlong", "jwrap"], [row["site_id"] for row in public_api_details(self.cfg)])

    def test_complete_legacy_scope_cannot_be_replaced_by_the_selected_subset(self):
        self.definition["declaration_ids"] = ["jlong"]
        self.freeze()
        with self.assertRaisesRegex(ValueError, "exactly the public"):
            configured_api_details(self.cfg)

    def test_excluded_source_declarations_are_still_source_validated(self):
        source = self.root / "source/Tools.java"
        source.write_text(source.read_text().replace("return add(x)", "return x"))
        with self.assertRaisesRegex(ValueError, "source evidence changed"):
            configured_api_details(self.cfg)

    def test_receipt_hash_source_binding_and_policy_version_are_required(self):
        original_definition, original_receipt = deepcopy(self.definition), deepcopy(self.receipt)
        cases = ["receipt_hash", "source_hash", "policy", "missing_field"]
        for case in cases:
            self.definition, self.receipt = deepcopy(original_definition), deepcopy(original_receipt)
            if case == "source_hash": self.receipt["source_inventory_sha256"] = "0" * 64
            if case == "policy": self.definition["canonical_selection_policy_version"] = "future_policy"
            if case == "missing_field": del self.definition["canonical_declaration_ids"]
            self.freeze()
            if case == "receipt_hash": self.receipt_path.write_text(self.receipt_path.read_text() + "\n")
            with self.subTest(case=case), self.assertRaises(ValueError):
                configured_api_details(self.cfg)

    def test_manifest_cannot_select_excluded_foreign_missing_or_duplicate_ids(self):
        for selected in (["jshort"], ["jwrap"], ["other"], [], ["jlong", "jlong"]):
            self.definition["canonical_declaration_ids"] = selected
            self.freeze()
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "exactly match"):
                configured_api_details(self.cfg)

    def test_forged_winners_and_counts_fail_receipt_replay(self):
        original = deepcopy(self.receipt)
        for field, value in (("winner_site_ids", ["jshort", "other"]), ("winner_names", ["add"]), ("counts", {})):
            self.receipt = deepcopy(original)
            self.receipt["selection"][field] = value
            self.freeze()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "replay"):
                configured_api_details(self.cfg)

    def test_receipt_cannot_omit_any_language_or_add_nonsource_sites(self):
        original = deepcopy(self.receipt)
        for change in ("omit_scala", "invent_site"):
            self.receipt = deepcopy(original)
            rows = self.receipt["selection"]["site_decisions"]
            if change == "omit_scala": rows = [row for row in rows if row["language"] == "Java"]
            else:
                invented = deepcopy(rows[0]); invented["site_id"] = "invented"; rows.append(invented)
            self.receipt["selection"] = select_canonical_implementations(rows)
            self.freeze()
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "every global"):
                configured_api_details(self.cfg)

    def test_receipt_cannot_relabel_source_owner_path_name_line_or_arity(self):
        original = deepcopy(self.receipt)
        for field, value in (("owner", "Other"), ("path", "Other.java"), ("name", "fake"),
                             ("line", 999), ("parameter_count", 100)):
            self.receipt = deepcopy(original)
            rows = self.receipt["selection"]["site_decisions"]
            next(row for row in rows if row["site_id"] == "jshort")[field] = value
            self.receipt["selection"] = select_canonical_implementations(rows)
            self.freeze()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "differs"):
                configured_api_details(self.cfg)


if __name__ == "__main__":
    unittest.main()
