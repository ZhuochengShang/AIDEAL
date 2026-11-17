"""Grounding reports and promotion of recorded execution evidence into documentation."""
from __future__ import annotations

import re
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
)
from .api_examples import (
    api_test_examples,
)
from .readme_format import (
    API_HEADER_RE,
    _replace_section,
    _section_has_code,
    parse_readme,
)


_TIER_BADGE = {"verified": "★", "grounded": "✅", "sibling": "🟡", "guessed": "⚠️"}
_TIER_RANK = {"verified": 0, "grounded": 1, "sibling": 2, "guessed": 3}
_EXEC_RANK = {"pass": 0, "": 1, "fail": 2}


def _recency_key(e: dict) -> str:
    """Sort key for 'newest wins'. Use run_id first: it is set on EVERY entry and
    has one consistent, lexically-sortable format (%Y%m%d-%H%M%SZ). The newer ISO
    `timestamp` field is absent on legacy rows and, being a different string shape,
    would sort inconsistently against run_id if the two were mixed — so run_id is
    the reliable ordering key and [-1] is truly the most recent."""
    return e.get("run_id") or e.get("timestamp") or ""


def _is_stale(e: dict, current_version: str) -> bool:
    """A memory entry is stale when it was recorded against a DIFFERENT code
    version than the one we're documenting now. Entries with no version tag
    (legacy rows) can't be proven stale, so they're kept."""
    v = (e.get("library_version") or "").strip()
    return bool(current_version) and bool(v) and v != current_version


def _fresh(entries: list[dict], current_version: str) -> list[dict]:
    """Drop version-mismatched entries, then sort oldest->newest so callers can
    take [-1] as the freshest trustworthy one. This is the staleness guard for
    promoting a verified example: without it, a `pass` snippet from three commits
    ago could be promoted as the current call pattern purely because it was the
    last line appended to the log."""
    return sorted((e for e in entries if not _is_stale(e, current_version)), key=_recency_key)


def _augment_block(block: str, fails: list[dict], only_missing: bool = False,
                   current_version: str = "") -> tuple[str, list[str]]:
    """Rewrite one entry from real log rows: Common Failure Modes + Fix Code Hint
    from failures, and a `Verified Example` from the latest PASSING execution — a
    compiled-and-ran snippet, the strongest possible grounding for the entry.

    `only_missing=True` = GAP-FILL: write the verified example / fix-hint code ONLY
    when the entry doesn't already have that code (so generated/curated examples are
    preserved). Common Failure Modes is always refreshed from the log either way.
    Returns (new_block, sections_added) where sections_added ⊆ {"example", "fix"}."""
    added: list[str] = []
    # verified example: the most recent snippet that compiled AND ran (status=pass
    # rows carry the working snippet in `code`). A proven example beats a written
    # one, so PROMOTE it into Valid Call Patterns.
    passed = _fresh([e for e in fails if e.get("status") == "pass" and e.get("code")], current_version)
    if passed and not (only_missing and _section_has_code(block, "Valid Call Patterns")):
        _p = passed[-1]
        _src = _p.get("library_version") or _p.get("timestamp") or "unversioned"
        block = _replace_section(
            block, "Valid Call Patterns",
            f"```\n{_p['code'].strip()}\n```\n_(verified: compiled + ran via `comprehension --execute` / probe; source @ {_src})_")
        added.append("example")
    seen: dict[tuple, int] = {}
    for e in fails:
        if e.get("status") == "fail":
            raw = (e.get("error", "") or "").strip().splitlines()[0] if e.get("error") else ""
            raw = re.sub(r"^\S+\.\w+:\d+:\s*", "", raw)   # drop "/path/File.scala:NN:"
            key = (e.get("error_category", "") or "error", raw[:200])
            seen[key] = seen.get(key, 0) + 1
    lines = [f"- **[{cat}]** {msg}" + (f" _(seen {n}x)_" if n > 1 else "")
             for (cat, msg), n in sorted(seen.items(), key=lambda kv: -kv[1])[:6]]
    cfm = "\n".join(lines) if lines else "- (no failures observed yet)"
    # prefer a real working fix (status=fixed); else fall back to any fix hint
    fixed = _fresh([e for e in fails if e.get("status") == "fixed" and e.get("suggested_fix_code")], current_version)
    real_fix = None
    if fixed:
        real_fix = ("Observed working code (from the fix loop):\n\n```scala\n"
                    + fixed[-1]["suggested_fix_code"].strip() + "\n```")
    else:
        hints = [e.get("suggested_fix_code", "").strip() for e in fails
                 if e.get("suggested_fix_code", "").strip()]
        if hints:
            real_fix = hints[-1]
    # Common Failure Modes is observational, not code — always refresh it from the log.
    block = _replace_section(block, "Common Failure Modes", cfm)
    # Fix Code Hint: in only_missing mode write ONLY real fix code into an entry that
    # lacks it (never overwrite existing code, never fill with the "no fix yet" stub).
    if only_missing:
        if real_fix and not _section_has_code(block, "Fix Code Hint"):
            block = _replace_section(block, "Fix Code Hint", real_fix)
            added.append("fix")
    else:
        block = _replace_section(
            block, "Fix Code Hint",
            real_fix or "- No confirmed fix yet; avoid the failures above.")
        if real_fix:
            added.append("fix")
    return block, added


def _grounding_tiers(cfg: AidealConfig):
    """Per readme entry, most to least trustworthy:
      verified (doc-derived code compiled AND ran) > grounded (direct test) >
      sibling (a tested method on the same class shows the pattern) > guessed.
    Returns (tiers{name->tier}, class_of{name->class}, test_index)."""
    import os as _os
    details = {d["name"]: d for d in public_api_details(cfg)}
    class_of = {n: (_os.path.basename(details[n].get("file", ""))[:-6]
                    if details[n].get("file", "").endswith(".scala") else "")
                for n in details}
    names = [e.name for e in parse_readme(cfg.llm_readme)]
    test_index = api_test_examples(cfg)
    exec_status = _exec_status_map(cfg)
    tested_classes = {class_of.get(n) for n, ex in test_index.items() if ex and class_of.get(n)}
    tiers = {}
    for n in names:
        if exec_status.get(n) == "pass":              # proven end-to-end in this harness
            tiers[n] = "verified"
        elif test_index.get(n):
            tiers[n] = "grounded"
        elif class_of.get(n) and class_of.get(n) in tested_classes:
            tiers[n] = "sibling"
        else:
            tiers[n] = "guessed"
    return tiers, class_of, test_index


def _exec_status_map(cfg: AidealConfig) -> dict:
    """function -> MOST RECENT execution outcome (pass/fail) from error_log.jsonl.

    error_log.jsonl is append-only, so file order IS chronological. Scan in that
    order and ALWAYS overwrite, so a later failure correctly downgrades an earlier
    pass.

    Fixes the sticky-pass bug: the old `setdefault` branch meant that once a
    function was marked pass, no subsequent fail could downgrade it — e.g.
    `zonalStatsLocal` stayed badged "verified" in readme_index.md while failing
    every recent run. `fixed` (a retry that produced working code) counts as pass;
    any other status does not overwrite a real pass/fail outcome."""
    from .error_log import ErrorLog
    st: dict[str, str] = {}
    for e in ErrorLog(cfg.error_log).entries():
        fn = e.get("function", "")
        if not fn:
            continue
        s = e.get("status", "")
        if s in ("pass", "fixed"):
            st[fn] = "pass"
        elif s == "fail":
            st[fn] = "fail"
    return st


def grounding_report(cfg: AidealConfig, annotate: bool = False) -> dict:
    """Which readme entries are TRUSTWORTHY vs SIBLING-backed vs GUESSED."""
    tiers, class_of, test_index = _grounding_tiers(cfg)
    if not tiers:
        return {"error": "no LLM_readme entries — run `aideal readme --generate`"}
    exec_status = _exec_status_map(cfg)
    counts = {"verified": 0, "grounded": 0, "sibling": 0, "guessed": 0}
    for t in tiers.values():
        counts[t] += 1
    total = len(tiers)
    guessed_fail = sorted(n for n, t in tiers.items() if t == "guessed" and exec_status.get(n) == "fail")
    out = {
        "total": total,
        "verified": counts["verified"], "grounded": counts["grounded"],
        "sibling_grounded": counts["sibling"], "guessed": counts["guessed"],
        "trusted_pct": round(100 * (counts["verified"] + counts["grounded"]) / total, 1),
        "guessed_that_failed_execution": guessed_fail[:40],
        "note": "verified = doc-derived code compiled AND ran (strongest); grounded = direct test; "
                "sibling = tested method on same class; guessed = signature-only (verify by execution).",
    }
    if annotate:
        badge = {"verified": "VERIFIED — doc-derived code compiled and ran via comprehension --execute.",
                 "grounded": "test-backed — usage mined from a real, passing test.",
                 "sibling": "sibling-grounded — a tested method on the same class shows the pattern.",
                 "guessed": "GUESSED — no test; generated from the signature only. Verify by execution."}
        text = cfg.llm_readme.read_text(encoding="utf-8")
        matches = list(API_HEADER_RE.finditer(text))
        parts = [text[:matches[0].start()]] if matches else [text]
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[m.start():end]
            if "_Grounding:" not in block:
                marker = f"_Grounding: {badge.get(tiers.get(m.group(1), 'guessed'))}_"
                hdr, _, rest = block.partition("\n")
                block = f"{hdr}\n{marker}\n{rest}"
            parts.append(block)
        cfg.llm_readme.write_text("".join(parts), encoding="utf-8")
        out["annotated"] = True
    return out


def organize_report(cfg: AidealConfig, write_index: bool = False) -> dict:
    """Axis 1+2 curation: group intended APIs by defining class, rank each by
    robustness (grounded > sibling > guessed, tie-broken by execution outcome),
    and mark the most robust `primary` per group so the agent reaches for it.
    Optionally writes a categorized, robust-first `docs/readme_index.md`."""
    from collections import defaultdict
    tiers, class_of, _ = _grounding_tiers(cfg)
    if not tiers:
        return {"error": "no LLM_readme entries — run `aideal readme --generate`"}
    exec_status = _exec_status_map(cfg)
    cats = defaultdict(list)
    for n, t in tiers.items():
        cats[class_of.get(n) or "(unknown)"].append((n, t, exec_status.get(n, "")))
    result = {}
    for cls, items in cats.items():
        items.sort(key=lambda it: (_TIER_RANK[it[1]], _EXEC_RANK.get(it[2], 1), it[0]))
        result[cls] = {"primary": items[0][0], "count": len(items),
                       "apis": [{"name": n, "tier": t, "exec": ex or "not-run"} for n, t, ex in items]}
    counts = {"verified": 0, "grounded": 0, "sibling": 0, "guessed": 0}
    for t in tiers.values():
        counts[t] += 1
    summary = {"total": len(tiers), "categories": len(result), **counts}
    if write_index:
        L = [f"# {cfg.project_name} — organized API index", "",
             f"{counts['verified']} verified · {counts['grounded']} grounded · "
             f"{counts['sibling']} sibling · {counts['guessed']} guessed · {len(result)} categories", "",
             "Legend: ★ verified (compiled + ran) · ✅ grounded (direct test) · 🟡 sibling-grounded · "
             "⚠️ guessed (verify by execution). **primary** = most robust in its group.", ""]
        for cls in sorted(result):
            L.append(f"## {cls}")
            for a in result[cls]["apis"]:
                star = " **(primary)**" if a["name"] == result[cls]["primary"] else ""
                ex = f" · exec {a['exec']}" if a["exec"] != "not-run" else ""
                L.append(f"- {_TIER_BADGE[a['tier']]} `{a['name']}` — {a['tier']}{ex}{star}")
            L.append("")
        idx = cfg.llm_readme.parent / "readme_index.md"
        idx.write_text("\n".join(L), encoding="utf-8")
        summary["index"] = str(idx)
    return {"summary": summary,
            "categories_sample": {k: {"primary": v["primary"], "count": v["count"]}
                                  for k, v in sorted(result.items())[:12]}}


def augment_from_log(cfg: AidealConfig, dry_run: bool = False,
                     only_missing: bool = False) -> dict:
    """Fold observed failures/fixes from error_log.jsonl into each LLM_readme
    entry's `Common Failure Modes` and `Fix Code Hint` sections, plus a verified
    `Valid Call Patterns` example from a PASSING execution (augment-from-log).
    Evidence only — never invents. Safe to re-run after more comprehension/puzzle passes.

    only_missing=True = GAP-FILL: add the verified example / fix-hint code ONLY to
    entries that don't already have that code (curated/generated code is preserved;
    Common Failure Modes is still refreshed). Use it after a full
    `comprehension --execute` to backfill exactly the entries missing a proven example."""
    from .error_log import ErrorLog, git_version
    if not cfg.llm_readme.exists():
        return {"error": "no LLM_readme.md — run `aideal readme --generate` first"}
    log = ErrorLog(cfg.error_log)
    # tag for staleness: only promote verified examples recorded against the
    # CURRENT code version (mismatched ones are dropped by _fresh). '' when the
    # target isn't a git repo -> staleness falls back to timestamp recency only.
    current_version = git_version(cfg.root)
    by_fn: dict[str, list[dict]] = {}
    for e in log.entries():
        by_fn.setdefault(e.get("function", ""), []).append(e)
    if not by_fn:
        return {"action": "noop", "note": "error_log.jsonl is empty; nothing to fold in"}

    text = cfg.llm_readme.read_text(encoding="utf-8")
    matches = list(API_HEADER_RE.finditer(text))
    parts = [text[:matches[0].start()]] if matches else [text]
    updated: list[str] = []
    example_added: list[str] = []
    fix_added: list[str] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start():end]
        fails = by_fn.get(m.group(1))
        if fails:
            block, added = _augment_block(block, fails, only_missing=only_missing,
                                          current_version=current_version)
            updated.append(m.group(1))
            if "example" in added:
                example_added.append(m.group(1))
            if "fix" in added:
                fix_added.append(m.group(1))
        parts.append(block)
    new_text = "".join(parts)
    if not dry_run:
        cfg.llm_readme.write_text(new_text, encoding="utf-8")
    return {"action": "augmented" if not dry_run else "dry-run",
            "mode": "only-missing" if only_missing else "refresh",
            "path": str(cfg.llm_readme), "entries_updated": len(updated),
            "verified_examples_added": len(example_added),
            "fix_hints_added": len(fix_added),
            "example_apis": example_added[:50],
            "fix_apis": fix_added[:50],
            "note": ("gap-fill: added verified example / fix-hint code only where missing; "
                     "Common Failure Modes refreshed") if only_missing else
                    "Common Failure Modes + Fix Code Hint + verified example rewritten from error_log"}
