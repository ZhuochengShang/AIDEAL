"""Offline policy contracts; no source checkout, network, or model required."""
from copy import deepcopy
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/aideal_engine/src"))
from aideal.api_canonical_selection import POLICY_VERSION, select_canonical_implementations


def record(site_id, name="add", count=1, language="Scala", category="implementation", **extra):
    row = {"site_id": site_id, "language": language, "name": name,
           "owner": "sample.Tools", "path": "Tools.scala" if language == "Scala" else "Tools.java",
           "line": 10, "parameter_count": count,
           "body_classification": {"category": category, "reviewed": True,
                                   "evidence": {"auditor": "unit_fixture", "body": "reviewed"}}}
    row.update(extra)
    return row


def identity(target):
    return {"relation": "exact_source_identical", "canonical_site_id": target,
            "trusted": True, "evidence": {"comparison": "exact source", "reviewer": "fixture"}}


class CanonicalSelectionTests(unittest.TestCase):
    def test_documented_shorter_and_preferred_path_cannot_defeat_maximum_arity(self):
        rows = [record("short", count=1, description="Detailed documentation", path="A.scala"),
                record("long", count=5, description="", path="deep/Z.scala")]
        result = select_canonical_implementations(rows)
        self.assertEqual(["long"], result["winner_site_ids"])
        self.assertEqual("same_name_lower_parameter_count", result["rejected_sites"][0]["reason"])
        self.assertEqual("name_policy_only", result["rejected_sites"][0]["relationship"])

    def test_same_name_across_languages_and_unrelated_owners_has_one_global_winner(self):
        rows = [record("java", count=3, language="Java", owner="Other"), record("scala", count=2)]
        result = select_canonical_implementations(rows)
        self.assertEqual(["java"], result["winner_site_ids"])
        self.assertEqual([], result["by_language"]["Scala"]["winner_names"])
        self.assertEqual(["add"], result["by_language"]["Java"]["winner_names"])
        self.assertFalse(result["policy"]["same_name_omission_claims_equivalence"])

    def test_longer_wrappers_and_facades_are_excluded_before_election(self):
        rows = [record("real", count=2)] + [record(category, count=20, category=category)
                for category in ("wrapper", "direct_forwarder", "facade", "abstract", "no_body")]
        result = select_canonical_implementations(rows)
        self.assertEqual(["real"], result["winner_site_ids"])
        self.assertEqual(5, result["counts"]["excluded_sites"])

    def test_missing_unreviewed_unknown_and_unresolved_are_not_eligible(self):
        rows = [record("missing", body_classification=None),
                record("raw", body_classification="implementation"),
                record("unreviewed", body_classification={"category": "implementation", "reviewed": False, "evidence": "AST"}),
                record("unknown", category="other_body"), record("unresolved", category="unresolved"),
                record("no_evidence", body_classification={"category": "implementation", "reviewed": True})]
        result = select_canonical_implementations(rows)
        self.assertEqual([], result["winner_names"])
        self.assertEqual(6, result["counts"]["excluded_sites"])
        self.assertEqual(set(row["site_id"] for row in rows), set(row["site_id"] for row in result["rejected_sites"]))

    def test_all_wrapper_name_is_absent_and_does_not_fall_back(self):
        result = select_canonical_implementations([record("a", category="wrapper"), record("b", category="direct_forwarder")])
        self.assertEqual([], result["winner_site_ids"])
        self.assertEqual(["add"], result["names_without_winner"])

    def test_ties_and_receipt_are_deterministic_across_input_order(self):
        rows = [record("scala", language="Scala"), record("later", language="Java", line=11),
                record("z", language="Java"), record("a", language="Java")]
        expected = select_canonical_implementations(rows)
        self.assertEqual(["a"], expected["winner_site_ids"])
        for ordered in permutations(rows):
            self.assertEqual(expected, select_canonical_implementations(ordered))
        self.assertEqual(expected, select_canonical_implementations(expected["site_decisions"]))

    def test_case_sensitive_names_and_parameterless_functions_remain_distinct(self):
        result = select_canonical_implementations([record("a", name="x", count=0, owner=""), record("b", name="X", count=0)])
        self.assertEqual(["X", "x"], result["winner_names"])

    def test_duplicate_site_ids_raise_instead_of_overwriting_evidence(self):
        with self.assertRaisesRegex(ValueError, "duplicate site_id"):
            select_canonical_implementations([record("same"), record("same", name="different")])

    def test_params_list_count_and_parameter_count_must_agree(self):
        row = record("a", count=2, params=[{"name": "x"}, {"name": "y"}])
        self.assertEqual(["a"], select_canonical_implementations([row])["winner_site_ids"])
        del row["parameter_count"]
        row["params"] = 2
        self.assertEqual(2, select_canonical_implementations([row])["winners"][0]["parameter_count"])
        row["parameter_count"] = 1
        with self.assertRaisesRegex(ValueError, "disagree"):
            select_canonical_implementations([row])

    def test_malformed_required_fields_raise(self):
        for changes in ({"line": True}, {"line": 0}, {"parameter_count": -1},
                        {"parameter_count": "2"}, {"owner": None}, {"name": ""}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                select_canonical_implementations([record("a", **changes)])

    def test_inputs_are_unchanged_and_receipt_is_json_serializable(self):
        rows = [record("a"), record("b", count=2)]
        original = deepcopy(rows)
        result = select_canonical_implementations(rows)
        self.assertEqual(original, rows)
        json.dumps(result, allow_nan=False)
        result["site_decisions"][0]["body_classification"]["evidence"]["body"] = "changed"
        self.assertEqual(original, rows)

    def test_exact_identity_requires_explicit_trusted_direct_canonical_target(self):
        rows = [record("canonical", name="base"), record("copy", name="alias", source_identity=identity("canonical"))]
        result = select_canonical_implementations(rows)
        self.assertEqual(["base"], result["winner_names"])
        self.assertEqual("trusted_exact_source_identity", result["rejected_sites"][0]["reason"])
        rows[1]["source_identity"]["trusted"] = False
        with self.assertRaisesRegex(ValueError, "trusted"):
            select_canonical_implementations(rows)

    def test_identical_looking_bodies_do_not_trigger_inferred_identity(self):
        result = select_canonical_implementations([record("a", name="one"), record("b", name="two")])
        self.assertEqual(["one", "two"], result["winner_names"])

    def test_identity_cannot_point_to_an_excluded_or_nonwinning_target(self):
        for target in (record("target", count=1, category="wrapper"), record("target", count=1)):
            rows = [target, record("larger", count=2), record("copy", name="alias", source_identity=identity("target"))]
            with self.subTest(target=target), self.assertRaises(ValueError):
                select_canonical_implementations(rows)

    def test_identity_cycles_chains_and_wrong_arity_are_rejected(self):
        cases = [
            [record("a", name="one", source_identity=identity("b")), record("b", name="two", source_identity=identity("a"))],
            [record("a", name="one", source_identity=identity("b")), record("b", name="two", source_identity=identity("c")), record("c", name="three")],
            [record("a", name="one", source_identity=identity("b")), record("b", name="two", count=2)],
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                select_canonical_implementations(rows)

    def test_empty_input_is_a_valid_empty_audit(self):
        result = select_canonical_implementations([])
        self.assertEqual(POLICY_VERSION, result["policy_version"])
        self.assertEqual(0, result["counts"]["input_sites"])
        self.assertEqual({}, result["by_language"])


if __name__ == "__main__":
    unittest.main()
