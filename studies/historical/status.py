"""Read study preparation evidence; never launch a job or imply run readiness."""
from collections import Counter
from pathlib import Path

from workflow.ablation import ARMS, bank_errors, load


def study_status(root, repo="rdpro"):
    root = Path(root)
    scope = load(root / "configs/study_order.json")
    if repo not in scope["repositories"]:
        raise ValueError("Unknown repository: " + repo)
    result = {"repository": repo, "first_study": scope["first_study"],
              "scope": scope["repositories"][repo],
              "arms": list(ARMS), "launch_authorized_by_this_report": False}
    if repo != "rdpro":
        result["matched_five_arm_results"] = None
        result["next"] = "Finish the RDPro reference study, then validate this repository's adapter and alias candidates."
        return result
    plan = load(root / "configs/plan.draft.json")
    bank = load(root / "configs/bank.draft.json")
    review = load(root / "proposals/rdpro/review_status.json")
    cases = bank.get("cases", [])
    errors = bank_errors(bank, plan["api_names"])
    result.update({
        "study_id": plan["study_id"], "plan_status": plan["status"],
        "selected_api_names": len(plan["api_names"]),
        "candidate_cases": dict(Counter(c["kind"] for c in cases)),
        "missing_task_prompts": sum(not c.get("prompt") for c in cases),
        "oracle_status_labels": dict(Counter((c.get("oracle") or {}).get("status", "missing") for c in cases)),
        "bank_validation_issue_count": len(errors),
        "bank_validation_issue_examples": errors[:5],
        "treatment_references_present": {k: bool(v) for k, v in plan.get("treatments", {}).items()},
        "alias_review": review,
        "adapter_validation_reference_present": bool(plan.get("adapter_validation")),
        "matched_five_arm_results": None,
        "next": "studies/rdpro/READINESS.md",
        "limitation": "Reads draft preparation records, not live execution status or admission. Present references and status labels alone do not validate artifacts."
    })
    return result
