"""Document repair orchestration; durable phases live in repair_journal.py."""
from __future__ import annotations
import hashlib
from pathlib import Path
import time

from .config import AidealConfig
from .error_log import ErrorLog
from . import docfix as helpers
from .repair_journal import RepairJournal, identity as repair_identity, write_text

def run(cfg: AidealConfig, apis: list[str] | None = None,
                max_apis: int | None = None, retry_rounds: int = 2,
                timeout_s: int | None = None, dry_run: bool = False,
                from_results: str | Path | None = None,
                report_path: str | Path | None = None,
                deep_dive_first: bool = False,
                deep_dive_out: str = "docs/deepdive",
                doc_rounds: int = 1,
                doc_stuck: int = 2,
                create_missing: bool = False,
                doc_source: str = "aideal",
                full_doc: bool | None = None,
                doc_scope: str | None = None,
                manifest: str | None = None) -> dict:
    """Doc-repair routing over failed APIs. Returns a report dict.

    doc_rounds=1 → the classic single pass (diagnose → rewrite → retry).
    doc_rounds>1 → iterative deep-dive repair: per API,
    up to N rounds of

        deep-dive (fresh, sees the newest failure + current draft)
        → diagnose → rewrite entry → run the API against the NEW doc
          (retry_rounds snippet fixes; 0 = clean pass-or-not doc measurement)

    with a per-round UNDERSTANDING CHECK: `diagnosis_changed` (root-cause text
    moved vs previous round) and `error_progressed` (the failure signature
    changed after the rewrite). If NEITHER improves for `doc_stuck`
    consecutive rounds, the API stops early — rounds must earn themselves.
    The draft entry is kept across rounds so each round builds on the last;
    the catalog is only left changed if the API finally PASSES (all-rounds
    fail → revert to the original entry; fresh B2 may still regress).
    After every round the incremental JSON report AND the readable
    fix-report markdown are refreshed, so the log is checkable mid-run."""
    from .llm import invoke_text, usage_snapshot, usage_delta
    from .prompts import load as load_prompt
    from .profile import require_profile
    from .readme_agent import parse_readme, _exec_status_map
    from .doc_checks import comprehension_check, _owner_map, _receiver_hint

    require_profile(cfg)
    entries = {e.name: e for e in parse_readme(cfg.llm_readme)} \
        if cfg.llm_readme.exists() else {}
    if apis:
        targets = [a for a in apis if a in entries]
        missing = [a for a in apis if a not in entries]
    elif from_results:
        targets, missing = helpers._failed_apis_from_results(from_results, set(entries))
    else:
        failed = {fn for fn, s in _exec_status_map(cfg).items() if s == "fail"}
        targets = sorted(n for n in failed if n in entries)
        missing = []
    if create_missing and missing:
        # ORIGINAL-README ARM: no catalog entry exists — the loop CREATES one.
        # Round-0 "current doc" = the original README excerpt the audience saw.
        targets = sorted(set(targets) | set(missing))
        missing = []
    if max_apis:
        targets = targets[:max_apis]
    base_report = {"check": "fix-docs", "journal_schema": 4,
                   "target_source": str(from_results) if from_results else
                   ("explicit --api" if apis else "latest error_log failures"),
                   "deep_dive_first": deep_dive_first,
                   "doc_rounds": doc_rounds,
                   "retry_rounds": retry_rounds,
                   "create_missing": create_missing,
                   "retry_doc_source": doc_source,
                   "retry_full_doc": full_doc,
                   "retry_doc_scope": doc_scope,
                   "manifest": manifest,
                   "attempted": len(targets),
                   "not_in_catalog": missing,
                   "apis": {}}
    if dry_run:
        out = {**base_report, "dry_run": True, "targets": targets}
        helpers._write_report(report_path, out)
        return out

    raw_docfix = (cfg.raw or {}).get("docfix", {}) or {}
    ctx_chars = int(raw_docfix.get("context_chars", 12000))

    def _clip(text: str, n: int | None = None) -> str:
        # In full-document experimental mode, repair must receive the same
        # documentation exposure as the audience. Outside that mode, projects
        # can cap context; context_chars=0 also explicitly means unlimited.
        n = (0 if full_doc else ctx_chars) if n is None else n
        t = text or ""
        return t if not n or len(t) <= n else t[:n] + f"\n[... truncated at {n} chars — full text in repo]"

    log = ErrorLog(cfg.error_log)
    owner_map = _owner_map(cfg)
    from .readme_agent import public_api_surface
    raw_surface = public_api_surface(cfg, override_filter="all")
    allowed_members = helpers._allowed_members_from_config(cfg)
    spec = cfg.model_for_role("fixer")   # senior engineer + doc rewriter
    identity_policy = {k: v for k, v in base_report.items() if k not in ('apis', 'attempted', 'not_in_catalog')}
    identity_policy['targets'] = targets
    identity_policy['doc_stuck'] = doc_stuck
    identity_policy['timeout_s'] = timeout_s
    run_identity = repair_identity(cfg, identity_policy)
    base_report['repair_identity'] = run_identity
    prior = helpers._read_report(report_path)
    if prior and prior.get('apis') and prior.get('repair_identity') != run_identity:
        raise ValueError('Legacy or changed document-repair identity; use a new report namespace')
    if (prior and prior.get("target_source") == base_report["target_source"]
            and bool(prior.get("deep_dive_first")) == deep_dive_first
            and prior.get("doc_rounds", 1) == doc_rounds):
        results: dict[str, dict] = dict(prior.get("apis") or {})
    else:
        results = {}
    fixed = sum(1 for v in results.values()
                if v.get("status") in ("doc-fixed", "doc-created"))
    import sys as _sys

    def _flush(blocked_api: str | None = None):
        run_report = {**base_report, "model": f"{spec.provider}:{spec.model}",
                      "doc_fixed": fixed,
                      "fix_rate": round(fixed / len(targets), 3) if targets else None,
                      "outcomes": helpers._outcomes(results),
                      "processed": len(results),
                      "apis": results}
        if blocked_api:
            run_report["blocked"] = True
            run_report["blocked_api"] = blocked_api
        helpers._write_report(report_path, run_report)
        try:                       # readable log refreshed EVERY flush (per round)
            from .fixreport import auto_report
            auto_report(cfg, run_report)
        except Exception:
            pass
        return run_report

    _flush()
    for i, name in enumerate(targets, 1):
        if name in results and not results[name].get("status", "").startswith(
                ("llm-error", "in-progress")):
            continue
        t0 = time.time()
        u0 = usage_snapshot()
        # If a process dies after inserting a B1 entry but before finalizing
        # the API, the partial catalog now contains that name. Preserve the
        # original "created from missing" identity in the incremental report
        # so resume still knows to remove the entry if all repair rounds fail.
        prior_result = results.get(name) or {}
        created = bool(prior_result.get("created_from_missing", name not in entries))
        results[name] = {
            "status": "in-progress",
            "created_from_missing": created,
            "doc_rounds": prior_result.get("doc_rounds", []),
        }
        _flush()
        if created:
            # What the audience actually read. Full-doc mode deliberately keeps
            # the entire bundle here; legacy mode may use the configured cap.
            original_body = ("(No catalog entry exists. The audience read the "
                             "ORIGINAL project documentation"
                             + (" IN FULL (full-doc mode)" if full_doc else "")
                             + "; content below.)\n"
                             + _clip(cfg.original_readme_text(limit=None))
                             + f"\n\nTarget function: `{name}`")
        else:
            original_body = entries[name].body
        window, others = helpers._source_window(cfg, name)
        type_ctx = helpers._type_context(cfg, name)[:7000]
        receiver = _receiver_hint(name, owner_map) or "(not resolved)"
        # newest failure evidence for round 0
        rows = [r for r in log.entries()
                if r.get("function") == name and r.get("status") == "fail"]
        last = rows[-1] if rows else {}
        cur_error = (last.get("error") or "(no recorded error)")[:1500]
        cur_cat = last.get("error_category", "unknown")
        cur_snippet = (last.get("code") or "(snippet not recorded)")[:2000]
        cur_frames = ", ".join(last.get("frames", []) or []) or "(none)"
        journal_path = (Path(report_path).with_suffix('.state') if report_path else
                        cfg.llm_readme.parent / '.docfix_state') / (hashlib.sha256(name.encode()).hexdigest() + '.json')
        journal = RepairJournal(journal_path, run_identity, {'original_body': original_body,
                    'created': created, 'error': cur_error, 'category': cur_cat,
                    'snippet': cur_snippet, 'frames': cur_frames})
        initial = journal.state['initial']
        original_body, created = initial['original_body'], initial['created']
        current_body = original_body
        prev_err_sig = helpers._err_sig(cur_cat, cur_error)
        prev_diag_sig = None
        stagnant = 0
        rounds_trail: list[dict] = []
        passed = False
        outcome = None            # set on early terminal verdicts
        cached = journal.state['context']
        if cached:
            current_body, cur_error, cur_cat = cached['body'], cached['error'], cached['category']
            prev_err_sig, prev_diag_sig = cached['error_signature'], cached['diagnosis_signature']
            stagnant, passed, outcome = cached['stagnant'], cached['passed'], cached['outcome']
        else:
            cur_error, cur_cat = initial['error'], initial['category']
            prev_err_sig = helpers._err_sig(cur_cat, cur_error)
        cur_snippet = cached.get('snippet', initial['snippet'])
        cur_frames = cached.get('frames', initial['frames'])
        rounds_trail = list(journal.state['rounds'])
        def checkpoint():
            journal.checkpoint(rounds_trail, {'body': current_body, 'error': cur_error,
                'category': cur_cat, 'error_signature': prev_err_sig,
                'diagnosis_signature': prev_diag_sig, 'stagnant': stagnant,
                'passed': passed, 'outcome': outcome, 'snippet': cur_snippet, 'frames': cur_frames})
        for rnd in range(len(rounds_trail), doc_rounds):
            if passed or outcome:
                break
            _sys.stderr.write(f"[docfix {i}/{len(targets)}] {name} round {rnd + 1}/"
                              f"{doc_rounds}: deep-dive -> diagnose -> rewrite -> run\n")
            _sys.stderr.flush()
            rrec: dict = {"round": rnd}
            # -- 1. deep-dive: fresh each round; sees the CURRENT draft (readme
            #       already holds it) and the newest failures (error log grows
            #       with every retry), so understanding can actually deepen.
            deep_dive_report = "(not requested)"
            if deep_dive_first:
                try:
                    from .deepdive import deep_dive_run
                    dd = journal.phase(rnd, "deep_dive", lambda: deep_dive_run(cfg, name, out_dir=deep_dive_out,
                                       context_only=False, return_text=True))
                    deep_dive_report = (dd.get("report_text") or "")[:10000]
                    rrec["deep_dive"] = {k: v for k, v in dd.items()
                                         if k in ("tokens", "wall_s", "report")}
                except Exception as exc:
                    results[name] = {"status": "llm-error (run stopped)",
                                     "phase": f"deep-dive round {rnd}",
                                     "error_type": type(exc).__name__,
                                     "error": str(exc)[:1000],
                                     "doc_rounds_done": rounds_trail,
                                     "wall_s": round(time.time() - t0, 1)}
                    return _flush(blocked_api=name)
            # -- 2. diagnose against real source + current failure
            try:
                diagnosis = journal.phase(rnd, "diagnose", lambda: invoke_text(spec, *load_prompt(
                    cfg, "aideal/docfix_diagnose",
                    api_name=name, source_window=window, other_sites=others,
                    type_context=type_ctx,
                    deep_dive_report=deep_dive_report,
                    receiver=receiver,
                    entry_body=_clip(current_body),
                    snippet=cur_snippet,
                    error=cur_error,
                    error_category=cur_cat,
                    frames=cur_frames,
                    language_lower=cfg.language.lower())))
            except Exception as exc:
                results[name] = {"status": "llm-error (run stopped)",
                                 "phase": f"diagnose round {rnd}",
                                 "error_type": type(exc).__name__,
                                 "error": str(exc)[:1000],
                                 "doc_rounds_done": rounds_trail,
                                 "wall_s": round(time.time() - t0, 1)}
                return _flush(blocked_api=name)
            dsig = helpers._diag_sig(diagnosis)
            rrec["diagnosis_head"] = diagnosis.strip()[:300]
            rrec["diagnosis_changed"] = (prev_diag_sig is None
                                         or dsig != prev_diag_sig)
            prev_diag_sig = dsig
            if diagnosis.strip().upper().startswith("VERDICT: NOT-TESTABLE"):
                outcome = "not-testable (entry unchanged)"
                rrec["outcome"] = "not-testable"
                rounds_trail.append(rrec)
                checkpoint()
                _sys.stderr.write(f"[docfix {i}/{len(targets)}] {name}: NOT-TESTABLE — stopped\n")
                break
            # -- 3. rewrite the entry, folding diagnosis in
            try:
                new_entry = journal.phase(rnd, "rewrite", lambda: invoke_text(spec, *load_prompt(
                    cfg, "aideal/docfix_rewrite",
                    api_name=name, diagnosis=diagnosis[:8000],
                    deep_dive_report=deep_dive_report,
                    source_window=window[:8000],
                    entry_body=_clip(current_body),
                    required_sections=", ".join(cfg.required_sections))))
            except Exception as exc:
                results[name] = {"status": "llm-error (run stopped)",
                                 "phase": f"rewrite round {rnd}",
                                 "error_type": type(exc).__name__,
                                 "error": str(exc)[:1000],
                                 "doc_rounds_done": rounds_trail,
                                 "wall_s": round(time.time() - t0, 1)}
                return _flush(blocked_api=name)
            new_entry = new_entry.strip()
            if not new_entry.startswith("## API Test:"):
                new_entry = f"## API Test: `{name}`\n\n" + new_entry
            fab = helpers._fabricated_members(new_entry, raw_surface, name, allowed_members)
            if fab:
                rrec["outcome"] = f"rewrite-rejected (fabricated: {', '.join(fab[:4])})"
                rounds_trail.append(rrec)
                results[name] = {"status": "in-progress",
                                 "created_from_missing": created,
                                 "rounds_used": len(rounds_trail),
                                 "doc_rounds": rounds_trail}
                log.append(step="doc-fix", language=cfg.language, task="docfix",
                           status="fail", function=name, error_category="doc-repair",
                           error=f"round {rnd}: rewrite fabricated members: {', '.join(fab[:6])}",
                           round=rnd)
                _sys.stderr.write(f"[docfix {i}/{len(targets)}] {name} round {rnd + 1}: "
                                  f"REJECTED (fabricated {fab[:3]})\n")
                _flush()
                # a rejected rewrite is not progress; count toward stagnation
                stagnant += 1
                if doc_stuck and stagnant >= doc_stuck:
                    outcome = "still-failing (no-improvement stop)"
                    checkpoint()
                    break
                checkpoint()
                continue
            current_body = new_entry             # next round builds on this draft
            rrec["entry_chars"] = {"old": len(original_body), "new": len(new_entry)}
            # -- 4. put the draft in the catalog and RUN the api against it
            readme_text = (cfg.llm_readme.read_text(encoding="utf-8")
                           if cfg.llm_readme.exists() else "")
            try:
                write_text(cfg.llm_readme, helpers._replace_entry_text(readme_text, name, new_entry))
            except KeyError:
                if created:                       # first accepted rewrite: INSERT
                    cfg.llm_readme.parent.mkdir(parents=True, exist_ok=True)
                    write_text(cfg.llm_readme, helpers._insert_entry_text(readme_text, new_entry))
                else:
                    results[name] = {"status": "error", "note": "entry not found in readme",
                                     "doc_rounds_done": rounds_trail}
                    break
            def validate_draft():
                value = comprehension_check(cfg, api=name, execute=True,
                                        max_fix_rounds=retry_rounds,
                                        timeout_s=timeout_s,
                                        doc_source=doc_source,
                                        full_doc=full_doc,
                                        doc_scope=doc_scope,
                                        manifest=manifest)
                metric = value.get('metrics', {}).get(name, {})
                if metric.get('error_category') == 'llm-error':
                    raise RuntimeError('Provider validation failed; retry this phase without a new rewrite')
                return value
            try:
                retry = journal.phase(rnd, 'validation', validate_draft)
            except Exception as exc:
                # This can be provider, harness, or uncertain phase state. Keep
                # it pending without attributing every pause to the model.
                results[name] = {'status': 'in-progress (validation paused)', 'error': str(exc),
                                 'error_type': type(exc).__name__,
                                 'created_from_missing': created, 'doc_rounds': rounds_trail}
                return _flush(blocked_api=name)
            m = (retry.get("metrics") or {}).get(name, {}) or {}
            rrec["retry_status"] = m.get("status", "fail")
            rrec["error_category"] = m.get("error_category")
            det = (retry.get("details") or {}).get(name)
            err_text = ""
            if isinstance(det, dict):
                err_text = det.get("error", "") or ""
            elif isinstance(det, str):
                err_text = det
            new_sig = helpers._err_sig(m.get("error_category") or "", err_text)
            rrec["error_head"] = err_text[:200]
            rrec["error_progressed"] = (m.get("status") == "pass"
                                        or new_sig != prev_err_sig)
            passed = m.get("status") == "pass"
            rounds_trail.append(rrec)
            # LIVE per-round persistence: the ACTIVE api's rounds are in the
            # JSON/markdown report from the moment they happen (finding #4) —
            # The journal resumes completed phases without a second rewrite.
            results[name] = {"status": "in-progress",
                             "created_from_missing": created,
                             "rounds_used": len(rounds_trail),
                             "doc_rounds": rounds_trail}
            _sys.stderr.write(
                f"[docfix {i}/{len(targets)}] {name} round {rnd + 1}: "
                f"{'PASS' if passed else 'fail'}  "
                f"(diagnosis {'changed' if rrec['diagnosis_changed'] else 'UNCHANGED'}, "
                f"error {'progressed' if rrec['error_progressed'] else 'SAME'})\n")
            _sys.stderr.flush()
            log.append(step="doc-fix", language=cfg.language, task="docfix",
                       status="pass" if passed else "fail", function=name,
                       error_category="doc-repair",
                       error="" if passed else f"round {rnd}: retry still failing",
                       round=rnd)
            # audit trail per round (before/after/diagnosis diffable per round)
            chg = cfg.llm_readme.parent / "docfix_changes"
            chg.mkdir(parents=True, exist_ok=True)
            tag = f"{name}.round{rnd}"
            (chg / f"{tag}.diagnosis.txt").write_text(diagnosis, encoding="utf-8")
            (chg / f"{tag}.after.md").write_text(new_entry, encoding="utf-8")
            if not passed:
                if rrec['diagnosis_changed'] or rrec['error_progressed']:
                    stagnant = 0
                else:
                    stagnant += 1
                    if doc_stuck and stagnant >= doc_stuck:
                        outcome = 'still-failing (no-improvement stop)'
                cur_error = err_text[:1500] or cur_error
                cur_cat = m.get('error_category') or cur_cat
                if isinstance(det, dict):
                    cur_snippet = str(det.get('code') or cur_snippet)[:2000]
                    cur_frames = ', '.join(det.get('frames', []) or []) or cur_frames
                prev_err_sig = new_sig
            checkpoint()
            _flush()
            if passed or outcome:
                break
        # ---- finalize this API ----
        if passed:
            fixed += 1
            chg = cfg.llm_readme.parent / "docfix_changes"
            chg.mkdir(parents=True, exist_ok=True)
            (chg / f"{name}.before.md").write_text(
                original_body if not created else "(no entry existed — created by doc-repair)",
                encoding="utf-8")
            status = "doc-created" if created else "doc-fixed"
        else:
            # Revert this entry; this is not a global fresh-reader guarantee.
            # created entries revert to ABSENT; existing ones to the original.
            if cfg.llm_readme.exists():
                readme_text = cfg.llm_readme.read_text(encoding="utf-8")
                try:
                    write_text(cfg.llm_readme, helpers._remove_entry_text(readme_text, name) if created else
                        helpers._replace_entry_text(readme_text, name, original_body))
                except KeyError:
                    pass
            status = outcome or "still-failing (entry reverted)"
        u = usage_delta(u0)
        results[name] = {
            "status": status,
            "created_from_missing": created,
            "rounds_used": len(rounds_trail),
            "doc_rounds": rounds_trail,
            "diagnosis_head": rounds_trail[-1].get("diagnosis_head", "") if rounds_trail else "",
            "entry_chars": ({"old": len(original_body),
                             "new": rounds_trail[-1]["entry_chars"]["new"]}
                            if rounds_trail and "entry_chars" in rounds_trail[-1] else None),
            "wall_s": round(time.time() - t0, 1),
            "tokens": {"in": u["input_tokens"], "out": u["output_tokens"]},
        }
        _flush()
    final = _flush()
    final["not_in_catalog"] = missing
    helpers._write_report(report_path, final)
    return final
