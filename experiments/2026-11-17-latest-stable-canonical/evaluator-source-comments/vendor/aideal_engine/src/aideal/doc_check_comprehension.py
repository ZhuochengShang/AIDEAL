"""Public comprehension check: choose documentation and route grading or execution."""
from __future__ import annotations

import random
from .config import AidealConfig
from .error_log import ErrorLog, new_run_id
from .doc_check_sources import (
    _build_catalogue_context, _comprehension_inventory, _load_manifest,
    _resolve_class_context,
)
from .doc_check_inputs import _execute_sample_data
from .doc_check_execution import _comprehension_execute


def comprehension_check(cfg: AidealConfig, sample: int | None = None, seed: int = 42,
                        doc_source: str = "aideal", execute: bool = False,
                        show_code: bool = False, api: str | None = None,
                        class_context: bool | None = None,
                        rerun_failed: bool = False,
                        max_fix_rounds: int | None = None,
                        resume: bool = False,
                        timeout_s: int | None = None,
                        full_doc: bool | None = None,
                        doc_scope: str | None = None,
                        manifest: str | None = None) -> dict:
    """Given only the documentation, the audience model writes code; the author
    model grades strictly against the doc. Failures go to the error log.

    rerun_failed: restrict the inventory to functions whose MOST-RECENT outcome in
             error_log is `fail` (via _exec_status_map — `fixed`/`pass` are skipped).
             Lets you re-test just the last run's failures instead of the whole
             surface. Applies to both --execute and the LLM-graded path.

    doc_source:
      "aideal"   - per-API entries from LLM_readme.md (the AIDEAL format)
      "original" - the project's ORIGINAL readme as the only context, with
                   target functions sampled from the code surface. This is
                   the baseline condition for original-vs-AIDEAL comparisons.
    execute: if True, the audience snippet is compiled/run via the configured
             `comprehension.execute` command instead of being LLM-graded —
             real execution ground truth. Defaults to ALL documented APIs.
    class_context: INDEX-FIRST read path. When on (CLI --class-context or config
             comprehension.class_context), each tested API's body is prefixed with
             its catalogue class header (how to obtain the receiver + one verified
             sibling's real call pattern) instead of the bare per-API body — the A/B
             lever against the ~53% receiver/entry-point failure class. None -> config.
    """
    from .llm import invoke_text
    from .profile import require_profile
    from .prompts import load as load_prompt
    from .readme_agent import _class_context_body

    require_profile(cfg)  # user must have entered project/target-user/domain fields
    if full_doc is None:
        full_doc = bool((cfg.comprehension or {}).get("full_doc", False))
    doc_scope = doc_scope or ("full" if full_doc else "entry")
    if doc_scope not in {"full", "relevant", "entry"}:
        raise ValueError(f"unknown doc_scope={doc_scope!r}")
    if doc_scope == "full":
        full_doc = True
    elif doc_scope == "relevant":
        full_doc = False
    manifest_names = _load_manifest(cfg, manifest)
    inventory, shared_doc, err = _comprehension_inventory(
        cfg, doc_source, manifest=manifest_names, full_doc=full_doc,
        doc_scope=doc_scope)
    if err:
        return err
    if full_doc and not execute:
        return {"check": "comprehension", "passed": False, "score": 0.0,
                "details": {"error": "--full-doc requires --execute (the LLM-graded "
                            "path would duplicate the whole document per entry)"}}
    if doc_scope == "relevant" and not execute:
        return {"check": "comprehension", "passed": False, "score": 0.0,
                "details": {"error": "--doc-scope relevant requires --execute"}}
    if api:  # test ONE specific documented API (covers both LLM-graded and --execute)
        names = [e.name for e in inventory]
        inventory = [e for e in inventory if e.name == api]
        if not inventory:
            return {"check": "comprehension", "passed": False, "error":
                    f"API '{api}' not found in {doc_source} doc. Available: "
                    f"{', '.join(sorted(names)[:40])}"}
    if rerun_failed:  # re-test ONLY functions whose most-recent error_log outcome is fail
        from .readme_agent import _exec_status_map
        failed = {fn for fn, s in _exec_status_map(cfg).items() if s == "fail"}
        inventory = [e for e in inventory if e.name in failed]
        if not inventory:
            return {"check": "comprehension", "doc_source": doc_source, "passed": True,
                    "score": 1.0, "details": {"note": "no function has a most-recent FAIL in "
                    "error_log — nothing to rerun (fixed/pass are skipped)"}}
    cc = _resolve_class_context(cfg, class_context)
    if execute:
        out = _comprehension_execute(cfg, inventory, sample, seed, doc_source,
                                     show_code=show_code, class_context=cc,
                                     max_fix_rounds=max_fix_rounds,
                                     resume=resume, timeout_s=timeout_s,
                                     shared_doc=shared_doc, doc_scope=doc_scope)
        if isinstance(out, dict) and isinstance(out.get("run"), dict):
            out["run"]["full_doc"] = bool(shared_doc is not None)
            out["run"]["doc_scope"] = doc_scope
            out["run"]["doc_chars"] = (len(shared_doc) if shared_doc else
                                         sum(len(e.body) for e in inventory))
            out["run"]["manifest"] = {"path": manifest,
                                      "apis": len(manifest_names)} if manifest_names else None
        return out
    k = len(inventory) if sample == 0 else (sample or cfg.comprehension_apis_sampled)
    if k < len(inventory):
        inventory = random.Random(seed).sample(inventory, k)

    # INDEX-FIRST: class header (receiver + verified sibling) prefixed to each body.
    # doc_source "original" has no per-class model — the flag is a no-op there.
    ctx = _build_catalogue_context(cfg) if (cc and doc_source == "aideal") else None
    body_for = (lambda e: _class_context_body(e, *ctx)) if ctx else (lambda e: e.body)

    log = ErrorLog(cfg.error_log)
    run_id = new_run_id()
    per_api: dict[str, object] = {}
    passed_n = 0
    ex = cfg.comprehension.get("execute", {}) if cfg.comprehension else {}
    _sample_data, available_inputs, _sd_warnings = _execute_sample_data(cfg, ex)
    for entry in inventory:
        code = invoke_text(
            cfg.model_for_role("audience"),
            *load_prompt(cfg, "aideal/comprehension_write",
                         api_body=body_for(entry), api_name=entry.name,
                         available_inputs=available_inputs),
        )
        verdict = invoke_text(
            cfg.model_for_role("author"),
            *load_prompt(cfg, "aideal/comprehension_grade",
                         api_body=entry.body, code=code),
        )
        if verdict.strip().upper().startswith("PASS"):
            passed_n += 1
            per_api[entry.name] = {"status": "pass", "code": code.strip()} if show_code else "pass"
        else:
            reason = verdict.split(":", 1)[-1].strip()[:200]
            per_api[entry.name] = (
                {"status": "fail", "reason": reason, "code": code.strip()}
                if show_code else f"fail: {reason}"
            )
            log.append(run_id=run_id, step="readme-unit-test", language=cfg.language,
                       task=f"comprehension_{doc_source}", status="fail",
                       function=entry.name, error=reason, root_cause="",
                       suggested_fix_code="")
    n = len(inventory)
    return {
        "check": "comprehension",
        "doc_source": doc_source,
        "passed": bool(n) and passed_n == n,
        "score": round(passed_n / n, 3) if n else 0.0,
        "details": per_api,
    }
