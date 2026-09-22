"""Preparation reporting must not turn a draft bank into measured results."""
import json
import tempfile
import unittest
from pathlib import Path

from studies.historical.status import study_status


class StudyReporting(unittest.TestCase):
    def test_pending_tasks_remain_pending_and_alias_flags_are_not_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = {
                "configs/study_order.json": {"first_study": "rdpro", "repositories": {"rdpro": "first", "sedonadb": "later"}},
                "configs/plan.draft.json": {"study_id": "test", "status": "draft", "api_names": ["read"], "treatments": {"improved_readme": None}},
                "configs/bank.draft.json": {"cases": [{"id": "read", "kind": "micro", "split": "held_out", "target_apis": ["read"], "prompt": None, "oracle": {"status": "pending"}}]},
                "proposals/rdpro/review_status.json": {"human_decision": None, "applied": False},
            }
            for name, value in records.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(value))
            report = study_status(root)
            self.assertEqual(1, report["missing_task_prompts"])
            self.assertGreater(report["bank_validation_issue_count"], 0)
            self.assertIsNone(report["matched_five_arm_results"])
            self.assertFalse(report["launch_authorized_by_this_report"])
            self.assertIsNone(report["alias_review"]["human_decision"])
            other = study_status(root, "sedonadb")
            self.assertIsNone(other["matched_five_arm_results"])
            self.assertNotIn("candidate_cases", other)


if __name__ == "__main__":
    unittest.main()
