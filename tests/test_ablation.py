from pathlib import Path
import tempfile
import unittest

from workflow.ablation import (ARMS, approval_valid, automatic_hint, bank_errors, bind, capture_attempt,
                      diagnostic_excerpt, digest, freeze, preflight, score,
                      treatment_inputs)


class AblationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        p = self.root / "fixture.txt"
        p.write_text("synthetic unit-test artifact; not experiment evidence")
        self.ref = bind(p)
        self.bank = {"cases": [
            {"id": "micro_f", "kind": "micro", "split": "held_out", "target_apis": ["f"],
             "prompt": "Compute f on a fixed input", "fixtures": [self.ref],
             "oracle": {"status": "validated", "reference": self.ref, "validation": self.ref}},
            {"id": "puzzle_f", "kind": "puzzle", "split": "held_out", "target_apis": ["f"],
             "prompt": "Compose a workflow", "fixtures": [self.ref],
             "oracle": {"status": "validated", "reference": self.ref, "validation": self.ref}}]}
        self.plan = {"api_names": ["f"],
                     "arms": {name: dict(zip(("readme", "aliases", "error_hints"), flags)) for name, flags in ARMS.items()},
                     "shared_artifacts": [self.ref], "common": {
                         "model": "unit-test-no-model", "temperature": 0, "max_output_tokens": 1,
                         "max_snippet_fixes": 5, "provider_attempt_limit": 3, "execution_timeout_s": 1,
                         "trial_ids": ["t1"], "prompt_sha256": "synthetic"},
                     "development_case_ids": [], "adapter_validation": self.ref,
                     "treatments": {key: self.ref for key in ("original_readme", "improved_readme", "alias_interface", "error_hints")}}
        self.proposal = {"artifacts": [self.ref]}
        self.decision = {"decision": "approve", "proposal_sha256": digest(self.proposal),
                         "human_decision_reference": "UNIT TEST ONLY; not a human approval"}

    def row(self, arm="original", case_id="micro_f", status="pass", **kw):
        return {"arm": arm, "case_id": case_id, "trial_id": "t1", "status": status,
                "study_sha256": "test", "execution_pass": status == "pass",
                "oracle_pass": status == "pass", "target_reached": status == "pass",
                "first_attempt_pass": status == "pass", "first_pass_round": 0, **kw}

    def metrics(self, rows):
        return score(self.bank, ["t1"], rows, study_sha256="test")

    def test_valid_freeze_is_exclusive(self):
        self.assertEqual(preflight(self.plan, self.bank, self.proposal, self.decision), [])
        out = self.root / "frozen.json"
        freeze(self.plan, self.bank, out, self.proposal, self.decision)
        with self.assertRaises(FileExistsError):
            freeze(self.plan, self.bank, out, self.proposal, self.decision)

    def test_missing_oracle_blocks(self):
        self.bank["cases"][0]["oracle"] = {"status": "pending"}
        with self.assertRaises(ValueError):
            freeze(self.plan, self.bank, self.root / "bad.json", self.proposal, self.decision)

    def test_changed_fixture_blocks(self):
        Path(self.ref["path"]).write_text("changed bytes")
        self.assertTrue(bank_errors(self.bank, ["f"]))
        self.assertFalse(approval_valid(self.proposal, self.decision))

    def test_no_approval_and_stale_approval_block(self):
        self.assertFalse(approval_valid(self.proposal, None))
        self.assertTrue(preflight(self.plan, self.bank, self.proposal))
        self.proposal["reason"] = "changed patch rationale"
        self.assertFalse(approval_valid(self.proposal, self.decision))

    def test_bank_and_manifest_must_match(self):
        self.assertTrue(bank_errors(self.bank, ["f", "g"]))
        self.bank["cases"].append(self.bank["cases"][0])
        self.assertTrue(bank_errors(self.bank, ["f"]))

    def test_holdout_overlap_blocks(self):
        self.plan["development_case_ids"] = ["micro_f"]
        self.assertIn("Development and held-out case IDs overlap", preflight(self.plan, self.bank, self.proposal, self.decision))

    def test_treatment_mismatch_blocks(self):
        self.plan["arms"]["readme_only"]["aliases"] = True
        self.assertTrue(any("factors changed" in x for x in preflight(self.plan, self.bank, self.proposal, self.decision)))

    def test_hint_and_alias_exposure(self):
        for arm, flags in ARMS.items():
            routed = treatment_inputs(self.plan, arm)
            self.assertEqual(routed["error_hints"] is not None, flags[2])
            self.assertEqual(routed["alias_interface"] is not None, flags[1])
            self.assertTrue(routed["save_full_logs"])

    def test_marker_only_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            self.metrics([self.row(oracle_pass=False)])
        with self.assertRaises(ValueError):
            self.metrics([self.row(target_reached=False)])

    def test_provider_pending_keeps_denominator(self):
        m = self.metrics([self.row(status="provider_pending")])["original"]["micro"]
        self.assertEqual((m["selected"], m["completed"], m["unresolved"]), (1, 0, 1))
        self.assertIsNone(m["final_within_budget_pct"])

    def test_duplicate_or_incompatible_result_rejected(self):
        with self.assertRaises(ValueError):
            self.metrics([self.row(), self.row()])
        with self.assertRaises(ValueError):
            self.metrics([self.row(study_sha256="historical")])

    def test_repairs_budget_and_first_attempt(self):
        with self.assertRaises(ValueError):
            self.metrics([self.row(first_pass_round=6, first_attempt_pass=False)])
        m = self.metrics([self.row(first_pass_round=2, first_attempt_pass=False)])["original"]["micro"]
        self.assertEqual(m["first_attempt_correct"], 0)
        self.assertEqual(m["correct_within_budget"], 1)

    def test_unverified_initial_success_rejected(self):
        with self.assertRaises(ValueError):
            self.metrics([self.row(status="unverified", first_attempt_pass=True)])

    def test_recoveries_and_regressions_are_paired(self):
        rows = [self.row(status="fail"), self.row(arm="combined"),
                self.row(case_id="puzzle_f"), self.row(arm="combined", case_id="puzzle_f", status="fail")]
        m = self.metrics(rows)["combined"]
        self.assertEqual(m["micro"]["recoveries_vs_original"], 1)
        self.assertEqual(m["puzzle"]["regressions_vs_original"], 1)

    def test_long_path_does_not_hide_java_error(self):
        error = "/Users/" + "long_experiment/" * 70 + "ApiTest.java:9: error: cannot find symbol\n  symbol: method getRenderingHints()\n  location: variable resizer of type Resizer"
        extracted = diagnostic_excerpt(error)["text"]
        self.assertIn("cannot find symbol", extracted)
        self.assertIn("location: variable resizer of type Resizer", extracted)
        self.assertLess(len(extracted), 500)
        code = "// full source\n" + "int value = 1;\n" * 300
        rec = capture_attempt(self.root / "attempt_0001", test_code=code, stdout="", stderr=error,
                              delivered_prompt="entire actual prompt", fix_hint="Try AbstractResizer")
        self.assertEqual(Path(rec["artifacts"]["test.txt"]["path"]).read_text(), code)
        self.assertEqual(Path(rec["artifacts"]["stderr.txt"]["path"]).read_text(), error)
        self.assertEqual(rec["fix_hint_status"], "unverified")
        with self.assertRaises(FileExistsError):
            capture_attempt(self.root / "attempt_0001", test_code="", stdout="", stderr="", delivered_prompt="")

    def test_hint_is_automatic_but_not_claimed_verified(self):
        rec = capture_attempt(self.root / "failure", test_code="full test", stdout="",
                              stderr="error: ambiguous reference to overloaded method", delivered_prompt="full prompt",
                              metadata={"passed": False})
        self.assertEqual(rec["automatic_hint"]["category"], "ambiguous-overload")
        self.assertEqual(rec["fix_hint_status"], "unverified")
        self.assertIn("do not remove the API", automatic_hint("ModuleNotFoundError")["text"])


if __name__ == "__main__":
    unittest.main()
