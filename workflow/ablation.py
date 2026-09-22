"""Offline ablation integrity, evidence capture, and matched scoring.

This module does not claim to be a provider/execution adapter. It refuses to
freeze unvalidated banks and never applies alias patches to a repository.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ARMS = {
    "original": (False, False, False),
    "readme_only": (True, False, False),
    "alias_only": (False, True, False),
    "error_hints_only": (False, False, True),
    "combined": (True, True, True),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    """Read a UTF-8 JSON artifact."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def bind(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"Missing artifact: {path}")
    return {"path": str(path), "sha256": file_hash(path), "bytes": path.stat().st_size}


def verify_artifact(ref):
    return Path(ref["path"]).is_file() and file_hash(ref["path"]) == ref["sha256"]


def approval_valid(proposal, decision):
    """A hash-bound audit check, NOT reviewer authentication.

    A trusted operator must record an actual human decision. Never synthesize
    a decision from a model response or an actor string.
    """
    return bool(decision and decision.get("decision") == "approve"
                and decision.get("proposal_sha256") == digest(proposal)
                and decision.get("human_decision_reference")
                and all(verify_artifact(x) for x in proposal.get("artifacts", []))
                and proposal.get("artifacts"))


def bank_errors(bank, api_names):
    errors, ids, micro = [], set(), set()
    expected_apis = set(api_names)
    cases = bank.get("cases", [])
    if not cases:
        return ["Bank is empty"]
    for c in cases:
        cid = c.get("id")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", cid):
            errors.append(f"Unsafe/missing case ID: {cid}")
        if cid in ids:
            errors.append(f"Duplicate case: {cid}")
        ids.add(cid)
        if c.get("split") != "held_out":
            errors.append(f"{cid}: evaluation case must be held_out")
        if c.get("kind") not in {"micro", "puzzle"}:
            errors.append(f"{cid}: invalid case kind")
        targets = c.get("target_apis", [])
        if not targets or set(targets) - expected_apis:
            errors.append(f"{cid}: missing or unknown original target APIs")
        if c.get("kind") == "micro":
            if len(targets) != 1:
                errors.append(f"{cid}: micro case must have exactly one target")
            micro.update(targets)
        if not c.get("prompt"):
            errors.append(f"{cid}: task prompt missing")
        oracle = c.get("oracle") or {}
        if oracle.get("status") != "validated" or not oracle.get("reference") or not oracle.get("validation"):
            errors.append(f"{cid}: independently validated oracle missing")
        else:
            for ref in (oracle["reference"], oracle["validation"]):
                if not verify_artifact(ref):
                    errors.append(f"{cid}: oracle artifact changed/missing")
        for ref in c.get("fixtures", []):
            if not verify_artifact(ref):
                errors.append(f"{cid}: fixture changed/missing")
    if micro != expected_apis:
        errors.append("Micro bank does not cover exactly the original API manifest")
    if not any(c.get("kind") == "puzzle" for c in cases):
        errors.append("No puzzle cases")
    return errors


def preflight(plan, bank, proposal=None, decision=None):
    errors = bank_errors(bank, plan["api_names"])
    if len(set(plan["api_names"])) != len(plan["api_names"]):
        errors.append("Duplicate API names")
    if set(plan["arms"]) != set(ARMS):
        errors.append("The five-arm matrix changed")
    for name, flags in ARMS.items():
        a = plan["arms"].get(name, {})
        if tuple(a.get(x) for x in ("readme", "aliases", "error_hints")) != flags:
            errors.append(f"{name}: treatment factors changed")
    for ref in plan.get("shared_artifacts", []):
        if not verify_artifact(ref):
            errors.append(f"Shared artifact changed/missing: {ref['path']}")
    if not plan.get("shared_artifacts"):
        errors.append("No shared source/runtime/prompt/fixture identity")
    common = plan.get("common", {})
    for key in ("model", "temperature", "max_output_tokens", "max_snippet_fixes",
                "provider_attempt_limit", "execution_timeout_s", "trial_ids", "prompt_sha256"):
        if common.get(key) is None:
            errors.append(f"Shared setting missing: {key}")
    development = set(plan.get("development_case_ids", []))
    if development & {c["id"] for c in bank["cases"]}:
        errors.append("Development and held-out case IDs overlap")
    for key in ("original_readme", "improved_readme", "alias_interface", "error_hints"):
        ref = plan.get("treatments", {}).get(key)
        if not ref or not verify_artifact(ref):
            errors.append(f"Treatment artifact missing/changed: {key}")
    if not approval_valid(proposal or {}, decision):
        errors.append("Alias patch requires an actual human decision bound to the reviewed artifacts")
    if not plan.get("adapter_validation") or not verify_artifact(plan["adapter_validation"]):
        errors.append("Measured runner/prompt exposure adapter has not been validated")
    return errors


def freeze(plan, bank, output, proposal=None, decision=None):
    errors = preflight(plan, bank, proposal, decision)
    if errors:
        raise ValueError("Preflight failed:\n" + "\n".join(errors))
    payload = {"plan": plan, "bank": bank, "proposal": proposal, "decision": decision}
    frozen = {"study_sha256": digest(payload), **payload}
    # Never overwrite a frozen study, including an identical one.
    with Path(output).open("x") as f:
        json.dump(frozen, f, indent=2, allow_nan=False)
    return frozen


def treatment_inputs(plan, arm):
    """Explicit prompt/artifact routing; a future runner must use this route."""
    readme, aliases, hints = ARMS[arm]
    t = plan["treatments"]
    return {"readme": t["improved_readme" if readme else "original_readme"],
            "alias_interface": t["alias_interface"] if aliases else None,
            "error_hints": t["error_hints"] if hints else None,
            "compile_approved_alias_module": aliases,
            "save_full_logs": True}


def diagnostic_excerpt(stderr, max_chars=6000):
    """Message-first context, not the first characters of a long path."""
    lines = stderr.splitlines()
    positions = [i for i, line in enumerate(lines) if re.search(
        r"error\b|exception\b|caused by:|cannot find symbol|symbol:|location:|found\s*:|required\s*:",
        line, re.I)]
    selected = sorted({j for i in positions for j in range(max(0, i - 1), min(len(lines), i + 5))})
    source = "\n".join(lines[i] for i in selected) if selected else stderr
    # Keep the raw bytes in stderr.txt; remove only directory prefixes here.
    text = re.sub(r"(?:/[A-Za-z0-9_. -]+)+/([^/\n:]+\.(?:scala|java|py|rs))", r"\1", source)
    return {"text": text[:max_chars], "truncated": len(text) > max_chars,
            "source_characters": len(stderr), "selected_characters": len(text)}


def automatic_hint(stderr):
    """Conservative triage, not a source-verified diagnosis or fix."""
    rules = [
        (r"ambiguous|overloaded method", "ambiguous-overload",
         "Inspect the available overloads. Supply a value or explicit type matching the documented constructor; avoid an untyped null."),
        (r"cannot find symbol|not a member|has no attribute|no method named", "name-or-receiver",
         "Check the method spelling, declaring class, and static type of the receiver against the supplied documentation. A missing name can also indicate a dependency/version mismatch."),
        (r"type mismatch|mismatched types|incompatible types|ClassCastException", "type-contract",
         "Compare required and actual argument/receiver types. Verify input data types before selecting a generic type parameter; a cast is not a data conversion."),
        (r"NoClassDefFoundError|ClassNotFoundException|ModuleNotFoundError", "import-or-dependency",
         "Check both the requested import and the installed version/classpath. A generated invalid import and a missing dependency require different fixes; do not remove the API from the denominator."),
        (r"FileNotFound|No such file|Input path does not exist", "file-input",
         "Check the supplied fixture path, file-versus-directory contract, and required sidecars. Create output directories only within the assigned workspace."),
        (r"AssertionError|assertion failed", "assertion-or-behavior",
         "Compare the observed value with the independent oracle and documented contract. Do not weaken or remove the assertion merely to obtain a pass."),
        (r"504|DEADLINE_EXCEEDED|ReadTimeout", "provider-or-service-timeout",
         "Inspect which process timed out. If this is provider transport, record it separately and retry within the provider budget; it is not evidence that the target API failed."),
    ]
    for pattern, category, hint in rules:
        if re.search(pattern, stderr, re.I):
            return {"category": category, "text": hint, "status": "unverified", "method": "deterministic pattern rule"}
    return {"category": "unknown", "text": "Inspect the complete diagnostic and the exact previous test before proposing a change.",
            "status": "unverified", "method": "fallback"}


def capture_attempt(directory, *, test_code, stdout, stderr, delivered_prompt,
                    diagnosis="", fix_hint="", metadata=None):
    """Capture in a NEW attempt directory, so failed attempts cannot disappear."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    generated_hint = None
    if not fix_hint and stderr and (metadata or {}).get("passed") is False:
        generated_hint = automatic_hint(stderr)
        fix_hint = generated_hint["text"]
    refs = {}
    for name, content in {"test.txt": test_code, "stdout.txt": stdout,
                          "stderr.txt": stderr, "delivered_prompt.txt": delivered_prompt,
                          "diagnosis.txt": diagnosis, "fix_hint.txt": fix_hint}.items():
        p = directory / name
        p.write_text(content, encoding="utf-8")
        refs[name] = bind(p)
    record = {"schema_version": 1, "metadata": metadata or {}, "artifacts": refs,
              "diagnostic": diagnostic_excerpt(stderr),
              "fix_hint_status": "unverified" if fix_hint else "absent",
              "automatic_hint": generated_hint,
              "full_test_characters": len(test_code), "full_error_characters": len(stderr)}
    save(directory / "attempt.json", record)
    return record


def score(bank, trial_ids, rows, *, study_sha256, max_snippet_fixes=5,
          arms=None, baseline="original"):
    """One latest adjudicated row per case/trial/arm, not raw attempt history.

    Provider-pending, not-run, and missing-oracle results remain unresolved.
    Do not accept an exit marker as semantic correctness.
    """
    arms = tuple(ARMS if arms is None else arms)
    if not arms or len(set(arms)) != len(arms) or baseline not in arms:
        raise ValueError("Invalid condition matrix/baseline")
    case_by_id = {c["id"]: c for c in bank["cases"]}
    if len(case_by_id) != len(bank["cases"]) or not trial_ids or len(set(trial_ids)) != len(trial_ids):
        raise ValueError("Duplicate cases/trials or empty trial list")
    by_key = {}
    for r in rows:
        key = (r["arm"], r["case_id"], r["trial_id"])
        if r["study_sha256"] != study_sha256 or r["arm"] not in arms:
            raise ValueError("Unmatched study/arm")
        if r["case_id"] not in case_by_id or r["trial_id"] not in trial_ids or key in by_key:
            raise ValueError("Unknown/duplicate case or trial")
        if r["status"] not in {"pass", "fail", "provider_pending", "not_run", "unverified"}:
            raise ValueError("Unknown result status")
        if r.get("first_attempt_pass") is True and r["status"] != "pass":
            raise ValueError("An initial semantic pass must be a verified pass outcome")
        if r["status"] == "pass":
            if not (r.get("execution_pass") is True and r.get("oracle_pass") is True
                    and r.get("target_reached") is True):
                raise ValueError("A pass needs execution, target reachability, and independent oracle")
            if not isinstance(r.get("first_pass_round"), int) or isinstance(r["first_pass_round"], bool) or not 0 <= r["first_pass_round"] <= max_snippet_fixes:
                raise ValueError("Pass is outside the common repair budget")
        if r["status"] == "pass" and r.get("first_attempt_pass") is not (r["first_pass_round"] == 0):
            raise ValueError("Inconsistent first-attempt and recovery outcome")
        by_key[key] = r
    reports = {}
    for arm in arms:
        reports[arm] = {}
        for kind in ("micro", "puzzle"):
            keys = [(arm, cid, tid) for cid, c in case_by_id.items() if c["kind"] == kind for tid in trial_ids]
            selected = [by_key.get(k, {"status": "not_run"}) for k in keys]
            counts = Counter(r["status"] for r in selected)
            n = len(keys)
            terminal = counts["pass"] + counts["fail"]
            initial = sum(r.get("first_attempt_pass") is True for r in selected)
            value = {"selected": n, "completed": terminal, "unresolved": n - terminal,
                     "first_attempt_correct": initial, "correct_within_budget": counts["pass"],
                     "status_counts": dict(counts),
                     "first_attempt_lower_bound_pct": 100 * initial / n if n else None,
                     "within_budget_lower_bound_pct": 100 * counts["pass"] / n if n else None,
                     "final_within_budget_pct": 100 * counts["pass"] / n if n and terminal == n else None}
            baseline_rows = [by_key.get((baseline, k[1], k[2]), {}) for k in keys]
            paired = [(a, b) for a, b in zip(selected, baseline_rows)
                      if a["status"] in {"pass", "fail"} and b.get("status") in {"pass", "fail"}]
            value["paired_completed"] = len(paired)
            value["recoveries_vs_original"] = sum(a["status"] == "pass" and b["status"] == "fail" for a, b in paired)
            value["regressions_vs_original"] = sum(a["status"] == "fail" and b["status"] == "pass" for a, b in paired)
            reports[arm][kind] = value
    return reports
