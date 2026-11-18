"""Recount the preserved historical study results, not new evaluations."""
import json
from collections import Counter
from pathlib import Path

from workflow.ablation import file_hash, load


def _native_counts(path):
    """Count archived native passes; do not reinterpret them as semantic checks."""
    data = load(path)
    metrics = data["metrics"]
    rounds = Counter(str(row.get("pass_round")) for row in metrics.values() if row.get("status") == "pass")
    return {"selected": len(metrics), "native_passes": sum(rounds.values()),
            "initial_native_passes": rounds.get("0", 0), "first_pass_rounds": dict(sorted(rounds.items())),
            "source_sha256": file_hash(path), "independent_semantic_validation": False}


def reproduce(root):
    """Recount archived outcomes, without generating or executing new solutions."""
    root = Path(root)
    native_root = root / "evidence/historical/native"
    cells = {p.name: _native_counts(p) for p in sorted(native_root.glob("*.json"))}
    old = load(root / "evidence/historical/RESULTS.json")
    sedona = {}
    for variant in ("default", "setup_variant_v2", "configured"):
        path = root / "studies/sedonadb/evidence" / (variant + "_results.jsonl")
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len({row['case_id'] for row in rows}) != len(rows):
            raise ValueError('Duplicate archived case IDs: ' + variant)
        sedona[variant] = {"example_blocks": len(rows),
                           "statuses": dict(sorted(Counter(row['status'] for row in rows).items())),
                           "semantic_correctness_verified": False, "llm_calls": 0,
                           "journal_sha256": file_hash(path)}
    return {"kind": "recomputed_archived_evidence_not_new_ablation_results",
            "native_cells": cells,
            "sedonadb_rust_documentation_sweeps": sedona,
            "historical_external_summary": old["historical_verified"],
            "rdpro_v5": old["RDPro_v5"],
            "new_five_arm_results": None,
            "notes": ["Recomputes native cells from archived per-API result rows.",
                      "External summary uses the separately hash-verified historical results memo.",
                      "Same output across Git branches demonstrates report reproducibility, not equal treatment performance.",
                      "Fresh LLM samples are not guaranteed to reproduce exact historical counts."]}


