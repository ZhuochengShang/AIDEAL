"""Fix-loop analysis: a READABLE markdown report of what a run actually did.

Answers, per run and against a baseline run, the questions raw JSON hides:
  1. Did anything improve? (pass deltas, newly-fixed, regressed, rescued-by-round)
  2. Which failures are the SAME issue not being solved? (per-API: last error
     signature unchanged vs baseline; cross-run: same signature over N runs)
  3. WHY does each API fail? (category, error head, codebase source line,
     reached stack frames, round-by-round error evolution, stuck detection)

Inputs it merges:
  - a comprehension/bench result JSON (`aideal comprehension --execute` output,
    detected by check=comprehension) or a docfix report JSON (check=fix-docs),
  - logs/error_log.jsonl (per-round rows; rows carry `round` since 2026-07-14,
    older rows fall back to line order within a run_id),
  - optionally a BASELINE result JSON of the same kind to diff against.

CLI: `aideal fix-report --run docs/run.json [--baseline docs/prev.json]`.
Comprehension/docfix runs also auto-write this report next to the catalog
(docs/fix_report_latest.md) unless comprehension.execute.auto_report is false.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .config import AidealConfig
from .error_log import ErrorLog

# --- error-signature normalization -----------------------------------------

_MASKS = [
    (re.compile(r"(/[\w.\-]+)+\.(scala|java|py)"), "<path>"),
    (re.compile(r'File "[^"]+"'), 'File "<path>"'),
    (re.compile(r"\bline \d+\b"), "line <n>"),
    (re.compile(r":\d+"), ":<n>"),
    (re.compile(r"0x[0-9a-fA-F]+"), "<hex>"),
    (re.compile(r"\b\d{3,}\b"), "<num>"),
    (re.compile(r"\s+"), " "),
]


def error_signature(category: str, message: str, *, mask_names: bool = False,
                    width: int = 140) -> str:
    """Stable signature of an error for same-issue detection. Paths, line
    numbers and big literals are masked; with mask_names=True, quoted/backtick
    identifiers are masked too (for CROSS-API clustering, where 'value fooX is
    not a member' and 'value fooY is not a member' are the same issue)."""
    s = (message or "").strip()
    for pat, repl in _MASKS:
        s = pat.sub(repl, s)
    if mask_names:
        s = re.sub(r"value \w+", "value <name>", s)
        s = re.sub(r"not found: (value|type) \w+", r"not found: \1 <name>", s)
        s = re.sub(r"`[^`]+`", "<name>", s)
        s = re.sub(r"'[^']+'", "<name>", s)
    return f"[{category or 'unknown'}] {s[:width].strip()}"


# --- loading & normalizing run artifacts ------------------------------------

def _details_error(det) -> tuple[str, str]:
    """(category, message) from a comprehension `details[name]` value —
    a plain string, a show-code dict, or a {status, rounds} dict whose real
    error lives in the last failing round."""
    if isinstance(det, dict):
        cat = det.get("error_category", "") or ""
        msg = det.get("error", "") or ""
        if not msg:
            for r in reversed(det.get("rounds") or []):
                if r.get("status") == "fail" and r.get("error"):
                    cat, msg = cat or r.get("category", ""), r.get("error", "")
                    break
        if not msg:
            m = re.match(r"fail \[([^\]]+)\]:\s*(.*)", str(det.get("status") or ""))
            if m:
                cat, msg = cat or m.group(1), m.group(2)
        return cat, msg
    if isinstance(det, str):
        m = re.match(r"fail \[([^\]]+)\]:\s*(.*)", det)
        if m:
            return m.group(1), m.group(2)
    return "", str(det or "")


def _rounds_of(det) -> list[dict]:
    if isinstance(det, dict) and isinstance(det.get("rounds"), list):
        return det["rounds"]
    return []


def load_run(path: str | Path) -> dict:
    """Normalize a result JSON (comprehension or fix-docs) into
    {kind, run_id, models, apis: {name: {...}}, meta}."""
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    kind = obj.get("check", "comprehension")
    apis: dict[str, dict] = {}
    if kind == "fix-docs":
        for name, r in (obj.get("apis") or {}).items():
            retry = r.get("retry") or {}
            status = (r.get("status") or "").split(" ")[0]
            # iterative mode: map the doc_rounds trail (deep-dive -> rewrite ->
            # run per round, with understanding flags) onto the generic rounds
            # shape so the per-API timeline renders like any fix loop.
            rounds = []
            last_cat, last_err = retry.get("error_category") or "", ""
            for dr in (r.get("doc_rounds") or []):
                flags = []
                if "diagnosis_changed" in dr:
                    flags.append("new diagnosis" if dr["diagnosis_changed"]
                                 else "diagnosis UNCHANGED")
                if "error_progressed" in dr:
                    flags.append("error moved" if dr["error_progressed"]
                                 else "error SAME")
                note = f"[{'; '.join(flags)}] " if flags else ""
                if dr.get("outcome"):          # rejected / not-testable rounds
                    rounds.append({"round": dr.get("round"), "status": "fail",
                                   "category": "doc-repair",
                                   "error": note + dr["outcome"]})
                    continue
                ok = dr.get("retry_status") == "pass"
                rounds.append({"round": dr.get("round"),
                               "status": "pass" if ok else "fail",
                               "category": dr.get("error_category") or "",
                               "error": note + (dr.get("error_head") or "")})
                if not ok:
                    last_cat = dr.get("error_category") or last_cat
                    last_err = dr.get("error_head") or last_err
            apis[name] = {
                "status": "pass" if status in ("doc-fixed", "doc-created") else "fail",
                "outcome": r.get("status", ""),
                "attempts": r.get("rounds_used") or retry.get("attempts"),
                "pass_round": retry.get("pass_round"),
                "error_category": last_cat,
                "error": last_err,
                "source": retry.get("source"),
                "frames": retry.get("codebase_frames") or [],
                "rounds": rounds,
                "diagnosis_head": r.get("diagnosis_head", ""),
                "tokens": r.get("tokens"),
                "wall_s": r.get("wall_s"),
            }
        meta = {k: obj.get(k) for k in ("model", "target_source", "attempted",
                                        "doc_fixed", "fix_rate", "outcomes",
                                        "deep_dive_first", "doc_rounds",
                                        "retry_rounds")}
        return {"kind": kind, "run_id": None, "models": {"fixer": obj.get("model")},
                "apis": apis, "meta": meta, "raw": obj}
    metrics = obj.get("metrics") or {}
    details = obj.get("details") or {}
    for name, m in metrics.items():
        if not isinstance(m, dict):
            continue
        det = details.get(name)
        cat, msg = _details_error(det)
        apis[name] = {
            "status": m.get("status", ""),
            "outcome": m.get("status", ""),
            "attempts": m.get("attempts"),
            "pass_round": m.get("pass_round"),
            "error_category": m.get("error_category") or cat,
            "error": msg,
            "source": m.get("source"),
            "frames": m.get("codebase_frames") or [],
            "rounds": _rounds_of(det),
            "tokens": {"in": m.get("input_tokens"), "out": m.get("output_tokens")},
            "wall_s": m.get("wall_s"),
        }
    run = obj.get("run") or {}
    meta = {"score": obj.get("score"), "score_with_infra": obj.get("score_with_infra"),
            "infra_excluded": obj.get("infra_excluded"),
            "wall_s": run.get("wall_s"), "usage": run.get("usage"),
            "max_fix_rounds": run.get("max_fix_rounds"),
            "class_context": run.get("class_context")}
    return {"kind": kind, "run_id": run.get("run_id"), "models": run.get("models") or {},
            "apis": apis, "meta": meta, "raw": obj}


def _log_rounds(log_entries: list[dict], run_id: str | None,
                name: str) -> list[dict]:
    """Round rows for one API in one run from the error log (fallback when the
    result JSON has no per-round detail). Ordered by `round` when present."""
    rows = [e for e in log_entries
            if e.get("function") == name and (run_id is None or e.get("run_id") == run_id)
            and e.get("step") in ("readme-exec-test", "code-test", "doc-fix")]
    out = []
    for seq, e in enumerate(rows):
        rnd = e.get("round")
        out.append({"round": rnd if isinstance(rnd, int) else seq,
                    "status": e.get("status", ""),
                    "category": e.get("error_category", ""),
                    "error": (e.get("error") or "")[:160],
                    "fix_hint": (e.get("suggested_fix_code") or "")[:100]})
    return out


# --- analyses ----------------------------------------------------------------

def _last_sig(api: dict, *, mask_names: bool = False) -> str:
    return error_signature(api.get("error_category", ""), api.get("error", ""),
                           mask_names=mask_names)


def compare_runs(run: dict, baseline: dict) -> dict:
    """fail->pass / pass->fail / still-failing split into same-signature
    (the issue is NOT being solved) vs changed-signature (churn/progress)."""
    a, b = baseline["apis"], run["apis"]
    both = sorted(set(a) & set(b))
    only_run = sorted(set(b) - set(a))
    only_base = sorted(set(a) - set(b))
    fixed = [n for n in both if a[n]["status"] != "pass" and b[n]["status"] == "pass"]
    regressed = [n for n in both if a[n]["status"] == "pass" and b[n]["status"] != "pass"]
    still = [n for n in both if a[n]["status"] != "pass" and b[n]["status"] != "pass"]
    same_issue, changed_issue = [], []
    for n in still:
        if _last_sig(a[n]) == _last_sig(b[n]):
            same_issue.append(n)
        else:
            changed_issue.append((n, _last_sig(a[n]), _last_sig(b[n])))
    def _cats(apis):
        from collections import Counter
        return dict(Counter(v.get("error_category") or "?" for v in apis.values()
                            if v["status"] != "pass"))
    return {"fixed": fixed, "regressed": regressed,
            "still_same_issue": same_issue, "still_changed_issue": changed_issue,
            "only_in_run": only_run, "only_in_baseline": only_base,
            "pass_run": sum(1 for v in b.values() if v["status"] == "pass"),
            "pass_base": sum(1 for v in a.values() if v["status"] == "pass"),
            "n_run": len(b), "n_base": len(a),
            "cats_run": _cats(b), "cats_base": _cats(a)}


def cluster_failures(run: dict, top: int = 12) -> list[dict]:
    """Cross-API clustering of the run's failures by masked signature —
    'which ONE issue is costing the most APIs'."""
    groups: dict[str, list[str]] = {}
    for n, v in run["apis"].items():
        if v["status"] == "pass":
            continue
        groups.setdefault(_last_sig(v, mask_names=True), []).append(n)
    out = [{"signature": sig, "count": len(names), "apis": sorted(names)}
           for sig, names in groups.items()]
    out.sort(key=lambda g: -g["count"])
    return out[:top]


def recurrence(log_entries: list[dict], names: list[str]) -> dict[str, dict]:
    """Cross-RUN persistence per failing API: how many distinct runs recorded a
    failure, whether the LAST error signature is identical across those runs
    (same issue never solved), and when it was first seen."""
    out: dict[str, dict] = {}
    for n in names:
        rows = [e for e in log_entries if e.get("function") == n
                and e.get("status") == "fail"]
        if not rows:
            continue
        by_run: dict[str, dict] = {}
        for e in rows:
            by_run[e.get("run_id") or "?"] = e          # keep last row per run
        sigs = [error_signature(e.get("error_category", ""), e.get("error", ""))
                for e in by_run.values()]
        out[n] = {"runs_failed": len(by_run),
                  "same_sig_runs": max((sigs.count(s) for s in set(sigs)), default=0),
                  "distinct_sigs": len(set(sigs)),
                  "first_seen": min((e.get("timestamp") or "" for e in rows),
                                    default="")[:10]}
    return out


def _stuckness(rounds: list[dict]) -> str:
    """Human verdict on the loop's trajectory for one API."""
    fails = [r for r in rounds if r.get("status") == "fail"]
    if not fails:
        return ""
    sigs = [error_signature(r.get("category", ""), r.get("error", "")) for r in fails]
    if any(r.get("status") == "stuck-stop" for r in rounds):
        return f"STUCK (stopped: same error repeated; {len(fails)} failing rounds)"
    if len(set(sigs)) == 1 and len(sigs) > 1:
        return f"STUCK (same error x{len(sigs)}, never changed)"
    if len(set(sigs)) < len(sigs):
        return f"CHURNING ({len(set(sigs))} distinct errors over {len(sigs)} rounds)"
    return f"PROGRESSING (error changed every round, {len(sigs)} rounds)"


# --- rendering ---------------------------------------------------------------

def _pct(k: int, n: int) -> str:
    return f"{100.0 * k / n:.1f}%" if n else "n/a"


_ABS_SRC = re.compile(r"/[^\s:]+/([\w$]+\.(?:scala|java|py)):")


def _short(text: str, width: int = 220) -> str:
    """Readability: collapse absolute file paths to basenames in error heads."""
    return _ABS_SRC.sub(r"\1:", text or "")[:width]


def render_markdown(run: dict, baseline: dict | None = None,
                    log_entries: list[dict] | None = None,
                    run_label: str = "run", baseline_label: str = "baseline",
                    top_clusters: int = 12, max_api_detail: int = 80) -> str:
    log_entries = log_entries or []
    apis = run["apis"]
    n = len(apis)
    passed = sum(1 for v in apis.values() if v["status"] == "pass")
    infra = [k for k, v in apis.items() if (v.get("error_category") or "") == "infra"]
    llmerr = [k for k, v in apis.items() if (v.get("error_category") or "") == "llm-error"]
    scored_n = n - len(infra)
    scored_p = passed  # passes are never infra
    L: list[str] = []
    ts = time.strftime("%Y-%m-%d %H:%M")
    L.append(f"# Fix-loop report — {run_label}")
    L.append("")
    L.append(f"_Generated {ts} by `aideal fix-report`._")
    L.append("")
    kind = run.get("kind")
    models = ", ".join(f"{k}={v}" for k, v in (run.get("models") or {}).items()) or "?"
    meta = run.get("meta") or {}
    L.append(f"- kind: **{kind}**  ·  run_id: `{run.get('run_id')}`  ·  models: {models}")
    if kind == "fix-docs":
        L.append(f"- outcomes: `{meta.get('outcomes')}`  ·  doc_fixed **{meta.get('doc_fixed')}"
                 f"/{meta.get('attempted')}**  ·  targets from `{meta.get('target_source')}`"
                 f"{'  ·  deep-dive-first' if meta.get('deep_dive_first') else ''}"
                 + (f"  ·  iterative x{meta.get('doc_rounds')} doc-rounds "
                    f"(retry={meta.get('retry_rounds')})"
                    if (meta.get('doc_rounds') or 1) > 1 else ""))
    else:
        L.append(f"- pass **{passed}/{n}** raw ({_pct(passed, n)})  ·  scored "
                 f"**{scored_p}/{scored_n}** ({_pct(scored_p, scored_n)}) after excluding "
                 f"{len(infra)} infra"
                 + (f"  ·  {len(llmerr)} llm-error (provider, rerun these)" if llmerr else ""))
        u = (meta.get("usage") or {})
        if u:
            L.append(f"- wall {round((meta.get('wall_s') or 0)/3600, 2)} h  ·  tokens "
                     f"in {u.get('input_tokens'):,} / out {u.get('output_tokens'):,} "
                     f"·  llm calls {u.get('calls')}  ·  max_fix_rounds {meta.get('max_fix_rounds')}")
        # rescued-by-round histogram: is the fix loop earning its rounds?
        from collections import Counter
        pr = Counter(v.get("pass_round") for v in apis.values()
                     if v["status"] == "pass" and v.get("pass_round") is not None)
        if pr:
            hist = "  ".join(f"r{k}:{v}" for k, v in sorted(pr.items()))
            rescued = sum(v for k, v in pr.items() if k and k > 0)
            L.append(f"- pass-by-round: {hist}  ·  **{rescued} rescued by the fix loop** "
                     f"(pass@0 = {pr.get(0, 0)})")
    L.append("")

    # ---- comparison verdict ----
    if baseline is not None:
        c = compare_runs(run, baseline)
        L.append(f"## Verdict vs {baseline_label}")
        L.append("")
        d = c["pass_run"] - c["pass_base"]
        L.append(f"|  | {baseline_label} | {run_label} | delta |")
        L.append("|---|---|---|---|")
        L.append(f"| pass | {c['pass_base']}/{c['n_base']} ({_pct(c['pass_base'], c['n_base'])}) "
                 f"| {c['pass_run']}/{c['n_run']} ({_pct(c['pass_run'], c['n_run'])}) "
                 f"| **{'+' if d >= 0 else ''}{d}** |")
        cats = sorted(set(c["cats_base"]) | set(c["cats_run"]))
        for cat in cats:
            b_, r_ = c["cats_base"].get(cat, 0), c["cats_run"].get(cat, 0)
            L.append(f"| {cat} failures | {b_} | {r_} | {'+' if r_ - b_ >= 0 else ''}{r_ - b_} |")
        L.append("")
        L.append(f"**Improved — failed before, passes now ({len(c['fixed'])}):** "
                 + (", ".join(f"`{x}`" for x in c["fixed"]) or "_none_"))
        L.append("")
        L.append(f"**Regressed — passed before, fails now ({len(c['regressed'])}):** "
                 + (", ".join(f"`{x}`" for x in c["regressed"]) or "_none_"))
        L.append("")
        L.append(f"### Same issue NOT solved ({len(c['still_same_issue'])})")
        L.append("")
        L.append("_Still failing with the IDENTICAL error signature as the baseline — "
                 "the fix loop is not moving these._")
        L.append("")
        for x in c["still_same_issue"]:
            v = run["apis"][x]
            L.append(f"- `{x}` — [{v.get('error_category') or '?'}] "
                     f"{_short(v.get('error', ''), 170)}")
        if not c["still_same_issue"]:
            L.append("_none_")
        L.append("")
        if c["still_changed_issue"]:
            L.append(f"### Still failing, but the error CHANGED ({len(c['still_changed_issue'])})")
            L.append("")
            L.append("_Not fixed, but not stuck either — the failure moved (often "
                     "compile → runtime = the doc/snippet got further)._")
            L.append("")
            for x, sa, sb in c["still_changed_issue"]:
                L.append(f"- `{x}`\n  - was: {sa}\n  - now: {sb}")
            L.append("")
        if c["only_in_run"] or c["only_in_baseline"]:
            L.append(f"_Denominator drift: {len(c['only_in_run'])} APIs only in {run_label}, "
                     f"{len(c['only_in_baseline'])} only in {baseline_label} — deltas above "
                     f"use the intersection._")
            L.append("")

    # ---- cross-run recurrence ----
    failing = sorted(k for k, v in apis.items() if v["status"] != "pass")
    rec = recurrence(log_entries, failing) if log_entries else {}
    chronic = {k: v for k, v in rec.items()
               if v["runs_failed"] >= 2 and v["same_sig_runs"] >= 2}
    if chronic:
        L.append(f"## Chronic failures across runs ({len(chronic)})")
        L.append("")
        L.append("_Failed in ≥2 recorded runs with the same error signature at least "
                 "twice — candidates for doc-repair with deep-dive, exclusion, or a "
                 "harness/fixture fix rather than more snippet retries._")
        L.append("")
        L.append("| API | runs failed | same-sig runs | distinct sigs | first seen |")
        L.append("|---|---|---|---|---|")
        for k in sorted(chronic, key=lambda x: -chronic[x]["runs_failed"]):
            v = chronic[k]
            L.append(f"| `{k}` | {v['runs_failed']} | {v['same_sig_runs']} "
                     f"| {v['distinct_sigs']} | {v['first_seen']} |")
        L.append("")

    # ---- clusters ----
    clusters = cluster_failures(run, top=top_clusters)
    if clusters:
        L.append(f"## Failure clusters (one issue, many APIs)")
        L.append("")
        L.append("_Current failures grouped by normalized error signature (identifiers "
                 "masked). Fixing the top cluster's root cause pays across all its APIs._")
        L.append("")
        for g in clusters:
            L.append(f"- **{g['count']}x** {g['signature']}")
            L.append(f"  - {', '.join(f'`{x}`' for x in g['apis'][:14])}"
                     + (" …" if len(g["apis"]) > 14 else ""))
        L.append("")

    # ---- per-API appendix ----
    L.append(f"## Why each API fails ({len(failing)} failing)")
    L.append("")
    shown = failing[:max_api_detail]
    for name in shown:
        v = apis[name]
        rounds = v.get("rounds") or _log_rounds(log_entries, run.get("run_id"), name)
        L.append(f"### `{name}` — {v.get('error_category') or '?'}"
                 + (f" · {v.get('outcome')}" if v.get("outcome") not in ("fail", "") else ""))
        L.append("")
        if v.get("source"):
            L.append(f"- canonical source: `{v['source']}`"
                     + (f" · reached: {', '.join(f'`{f}`' for f in v['frames'][:3])}"
                        if v.get("frames") else ""))
        if v.get("error"):
            L.append(f"- last error: {_short(v['error'], 300)}")
        if v.get("diagnosis_head"):
            head = " ".join(v["diagnosis_head"].split())[:280]
            L.append(f"- docfix diagnosis: {head}")
        verdict = _stuckness(rounds)
        if verdict:
            L.append(f"- loop trajectory: **{verdict}**")
        if rounds:
            L.append("- rounds:")
            for r in rounds[:10]:
                if r.get("status") == "pass":
                    L.append(f"  - r{r.get('round')}: PASS")
                elif r.get("status") == "stuck-stop":
                    L.append(f"  - r{r.get('round')}: stopped — {r.get('note', 'stuck')}")
                else:
                    hint = f"  → hint: {_short(r['fix_hint'], 100)}" if r.get("fix_hint") else ""
                    L.append(f"  - r{r.get('round')} [{r.get('category') or '?'}] "
                             f"{_short(r.get('error', ''), 150)}{hint}")
            if len(rounds) > 10:
                L.append(f"  - … {len(rounds) - 10} more rounds")
        elif v.get("attempts"):
            L.append(f"- attempts: {v['attempts']} (no per-round trace recorded — "
                     f"older run; new runs log `round` in error_log.jsonl)")
        L.append("")
    if len(failing) > max_api_detail:
        L.append(f"_… {len(failing) - max_api_detail} more failing APIs omitted "
                 f"(--max-api-detail to raise)._")
        L.append("")
    if infra:
        L.append(f"**Infra failures excluded from doc-quality scoring ({len(infra)}):** "
                 + ", ".join(f"`{x}`" for x in infra))
        L.append("")
    return "\n".join(L)


# --- entry points ------------------------------------------------------------

def write_report(cfg: AidealConfig, run_path: str | Path,
                 baseline_path: str | Path | None = None,
                 out_path: str | Path | None = None,
                 top_clusters: int = 12, max_api_detail: int = 80) -> dict:
    run = load_run(run_path)
    baseline = load_run(baseline_path) if baseline_path else None
    log_entries = ErrorLog(cfg.error_log).entries() if cfg.error_log.exists() else []
    md = render_markdown(run, baseline, log_entries,
                         run_label=Path(run_path).stem,
                         baseline_label=Path(baseline_path).stem if baseline_path else "baseline",
                         top_clusters=top_clusters, max_api_detail=max_api_detail)
    out = Path(out_path) if out_path else (
        cfg.llm_readme.parent / f"fix_report_{Path(run_path).stem}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    latest = cfg.llm_readme.parent / "fix_report_latest.md"
    try:
        latest.write_text(md, encoding="utf-8")
    except OSError:
        pass
    return {"check": "fix-report", "written": str(out), "latest": str(latest),
            "apis": len(run["apis"]),
            "failing": sum(1 for v in run["apis"].values() if v["status"] != "pass"),
            "baseline": str(baseline_path) if baseline_path else None}


def auto_report(cfg: AidealConfig, result: dict) -> str | None:
    """Best-effort readable report straight from an in-memory result dict
    (called at the end of comprehension --execute / fix-docs unless
    comprehension.execute.auto_report is false). Never raises."""
    try:
        ex = (cfg.comprehension or {}).get("execute", {}) or {}
        if not ex.get("auto_report", True):
            return None
        if not (result.get("metrics") or result.get("apis")):
            return None
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         prefix="aideal_run_") as f:
            json.dump(result, f)
            tmp = f.name
        run_id = ((result.get("run") or {}).get("run_id")
                  or time.strftime("%Y%m%d-%H%M%S"))
        out = cfg.llm_readme.parent / f"fix_report_{run_id}.md"
        rep = write_report(cfg, tmp, out_path=out)
        Path(tmp).unlink(missing_ok=True)
        return rep["written"]
    except Exception:
        return None
