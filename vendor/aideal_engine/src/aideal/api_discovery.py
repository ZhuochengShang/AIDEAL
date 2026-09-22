"""Public API discovery, source listings, surface audits, and documentation coverage."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig
from .api_signatures import (
    _doc_at,
    _java_param_record,
    _java_return_type,
    _python_qualified_identities,
    _signature_at,
)
from .api_visibility import (
    _NONPUBLIC_MOD_RE,
    _is_public,
    _iter_defs,
    visibility_model,
)
from .readme_format import (
    parse_readme,
)


def public_api_surface(cfg: AidealConfig, override_filter: str | None = None) -> set[str]:
    """Public API names, optionally narrowed to the INTENDED API by a general,
    codebase-agnostic `surface_filter` (pass override_filter='all' for the raw
    discovered surface):
      all                       - every visible public def (raw surface)
      documented                - has a doc comment (author signalled intent)
      non_override              - not an `override` (excludes inherited/interface impls)
      documented_non_override   - both (tightest intended-API set)
    Default `all` (back-compat)."""
    model = visibility_model(cfg)
    flt = (override_filter or cfg.surface_filter or "all").lower()
    if flt in ("intent_score", "intent"):
        from .api_intent import intent_scores
        return {n for n, info in intent_scores(cfg).items() if info["selected"]}
    if flt in ("intended_llm", "intent_llm"):
        from .api_intent import intended_api_llm
        return intended_api_llm(cfg)[0]
    file_cache: dict[str, list[str]] = {}
    all_names: set[str] = set()
    documented: set[str] = set()
    non_override: set[str] = set()
    py_identities = _python_qualified_identities(cfg) if cfg.language.lower() == "python" else None
    for name, prefix, path, i, _line in _iter_defs(cfg):
        if name in cfg.exclude_names or not _is_public(name, prefix, model):
            continue
        if py_identities is not None:
            rel = str(Path(path).relative_to(cfg.root)).replace("\\", "/")
            if (rel, i + 1, name) not in py_identities:
                continue
        all_names.add(name)
        if not re.search(r"\boverride\b", prefix):
            non_override.add(name)
        if flt.startswith("documented"):
            lines = file_cache.setdefault(
                path, Path(path).read_text(encoding="utf-8", errors="ignore").splitlines())
            if _doc_at(cfg, lines, i).strip():
                documented.add(name)
    # Intent signals, in order of preference: documentation, then tests (a unit
    # test exercising an API is also author intent). Structural `non_override`
    # is the last resort because it's over-inclusive (can't tell API from
    # internal helper). So `documented` degrades: docs -> tested -> non_override
    # -> all, never empty.
    def _tested() -> set[str]:
        if not cfg.test_globs:
            return set()
        names = set()
        for g in cfg.test_globs:
            for p in globmod.glob(str(cfg.root / g), recursive=True):
                txt = Path(p).read_text(encoding="utf-8", errors="ignore")
                for nm in all_names:
                    if nm not in names and re.search(rf"\b{re.escape(nm)}\s*[\(\[]|\.{re.escape(nm)}\b", txt):
                        names.add(nm)
        return names

    if flt == "documented":
        return documented or _tested() or non_override or all_names
    if flt == "tested":
        return _tested() or documented or non_override or all_names
    if flt == "non_override":
        return non_override or all_names
    if flt in ("documented_non_override", "documented_and_non_override"):
        return (documented & non_override) or documented or _tested() or non_override or all_names
    if flt in ("documented_or_tested", "intended"):
        return (documented | _tested()) or non_override or all_names
    return all_names


def public_api_details(cfg: AidealConfig) -> list[dict]:
    """Per-definition records for the surface: name, signature, params, return,
    description, visibility, file, line. One record per definition site (not
    collapsed), so overloads across classes stay distinct."""
    model = visibility_model(cfg)
    py_identities = _python_qualified_identities(cfg) if cfg.language.lower() == "python" else {}
    file_cache: dict[str, list[str]] = {}
    out: list[dict] = []
    for name, prefix, path, i, line in _iter_defs(cfg):
        if name in cfg.exclude_names:
            continue
        public = _is_public(name, prefix, model)
        lines = file_cache.setdefault(
            path, Path(path).read_text(encoding="utf-8", errors="ignore").splitlines())
        m = re.compile(cfg.public_def_regex).search(line)
        rel = str(Path(path).relative_to(cfg.root))
        identity = py_identities.get((rel, i + 1, name), {})
        if cfg.language.lower() == "python" and not identity:
            continue
        if cfg.language.lower() == "python":
            # Python signatures come from AST, not the Scala-style colon
            # parser: in ``class X(Base): \"\"\"doc\"\"\"`` the colon starts
            # the body, not a return type, and Base is inheritance rather than
            # a constructor parameter.
            raw = identity.get("signature", name)
            params = identity.get("params", [])
            ret = identity.get("returns", "")
        else:
            raw, params, ret = _signature_at(lines, i, m.start() if m else 0,
                                             m.end(1) if m else 0)
            if cfg.language.lower() == "java":
                params = [_java_param_record(p["name"]) for p in params]
                ret = _java_return_type(raw, name)
        out.append({
            "name": name,
            "qualified_name": identity.get("qualified_name", name),
            "module": identity.get("module", ""),
            "owner": identity.get("owner", ""),
            "definition_kind": identity.get("kind", ""),
            "visibility": "public" if public else "non-public",
            "signature": raw,
            "params": params,
            "returns": ret,
            "description": _doc_at(cfg, lines, i),
            "file": rel,
            "line": i + 1,
        })
    return out


def render_api_surface(cfg: AidealConfig, include_nonpublic: bool = False) -> str:
    """Plain-text dump of the discovered API surface (Step 1 of the test plan)."""
    details = public_api_details(cfg)
    pub = [d for d in details if d["visibility"] == "public"]
    shown = details if include_nonpublic else pub
    by_name: dict[str, list[dict]] = {}
    for d in shown:
        by_name.setdefault(d["name"], []).append(d)
    lines = [
        f"API SURFACE — {cfg.project_name} ({cfg.language})",
        f"globs: {', '.join(cfg.source_globs)}",
        f"visibility model: {visibility_model(cfg).get('mode')}",
        f"public names: {len(by_name)}   public defs: {len(pub)}   "
        f"non-public defs filtered: {len(details) - len(pub)}",
        "=" * 64,
    ]
    for name in sorted(by_name):
        recs = by_name[name]
        lines.append(f"\n{name}  ({len(recs)} definition{'s' if len(recs) > 1 else ''})")
        for d in recs:
            lines.append(f"  - file   : {d['file']}:{d['line']}  [{d['visibility']}]")
            if d["params"]:
                pstr = "; ".join(
                    f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p.get("default") else "")
                    if p.get("type") else p["name"]
                    for p in d["params"])
                lines.append(f"    params : {pstr}")
            else:
                lines.append("    params : (none)")
            lines.append(f"    returns: {d['returns'] or '(unspecified)'}")
            if d["description"]:
                lines.append(f"    doc    : {d['description'][:200]}")
    return "\n".join(lines)


# --- surface audit: catalog vs the CURRENT visibility-correct surface --------

def surface_audit(cfg: AidealConfig) -> dict:
    """Cross-check every LLM_readme catalog entry against the current API
    surface. Catches the private-function leak class after a visibility-model
    fix: entries whose canonical definition is non-public (private/protected,
    incl. scoped `private[pkg]` and non-public enclosing containers), whose
    file is excluded by `codebase.exclude_path_patterns`, or which fell below
    the intent threshold. These entries burn fix-loop rounds and can never
    pass from an external harness — prune or exclude them instead of fixing.

    Returns counts + per-entry verdicts; CLI: `aideal surface-audit`."""
    entries = [e.name for e in parse_readme(cfg.llm_readme)]
    det = public_api_details(cfg)
    by_name: dict[str, list[dict]] = {}
    for d in det:
        by_name.setdefault(d["name"], []).append(d)
    # modifier evidence per non-public site (via the same prefix _is_public saw)
    mods_of: dict[str, list[str]] = {}
    for name, prefix, path, i, _line in _iter_defs(cfg):
        if name not in entries:
            continue
        found = _NONPUBLIC_MOD_RE.findall(prefix)
        if found:
            rel = str(Path(path).relative_to(cfg.root))
            mods_of.setdefault(name, []).append(f"{' '.join(found)} @ {rel}:{i + 1}")
    selected = public_api_surface(cfg)   # respects surface_filter (intent_score...)
    verdicts: dict[str, dict] = {}
    for n in entries:
        recs = by_name.get(n, [])
        if not recs:
            verdicts[n] = {"status": "not-on-surface",
                           "why": "no definition matched (path-excluded via "
                                  "exclude_path_patterns, moved, or renamed)"}
        elif all(r["visibility"] != "public" for r in recs):
            verdicts[n] = {"status": "non-public",
                           "why": "; ".join(mods_of.get(n, [])[:3]) or
                                  "private/protected (incl. enclosing container)",
                           "sites": [f"{r['file']}:{r['line']}" for r in recs[:3]]}
        elif n not in selected:
            verdicts[n] = {"status": "deselected",
                           "why": f"below intent threshold under surface_filter="
                                  f"{cfg.surface_filter}"}
        else:
            verdicts[n] = {"status": "ok"}
    from collections import Counter
    counts = dict(Counter(v["status"] for v in verdicts.values()))
    prune = sorted(n for n, v in verdicts.items() if v["status"] != "ok")
    return {"check": "surface-audit",
            "catalog_entries": len(entries),
            "public_names_on_surface": len({d["name"] for d in det
                                            if d["visibility"] == "public"}),
            "counts": counts,
            "prune_candidates": prune,
            "verdicts": {n: v for n, v in verdicts.items() if v["status"] != "ok"}}


# --- coverage: which APIs does each documentation set actually document? ----

def api_coverage(cfg: AidealConfig) -> dict:
    """Compare original/generated documentation coverage over a shared API scope:

      S = frozen runnable public surface (visibility-correct + intent filter)
      O = APIs documented in the ORIGINAL bundle (evidence-based: code block /
          backticks / call-form via _doc_code_mentions — bare prose words do
          not count), resolved against S
      G = APIs with a generated LLM_readme entry, resolved against S
      T = S ∩ O ∩ G — the SHARED manifest every pass-rate cell must consume

    Coverage (|S∩O|/|S| vs |S∩G|/|S|) is a first-class result on its own;
    pass rates are only causally comparable on T."""
    from .api_intent import _doc_code_mentions

    S = set(public_api_surface(cfg))
    docs_text = cfg.original_readme_text(limit=None) if cfg.original_readme_files else ""
    coverage_cfg = ((cfg.raw or {}).get("coverage") or {})
    call_patterns = coverage_cfg.get("documentation_call_patterns")
    O = _doc_code_mentions(docs_text, S, call_patterns=call_patterns)
    G = ({e.name for e in parse_readme(cfg.llm_readme)} & S
         if cfg.llm_readme.exists() else set())
    T = S & O & G
    def pct(x):
        return round(100.0 * len(x) / len(S), 1) if S else 0.0
    return {
        "surface_S": sorted(S), "n_surface": len(S),
        "original_documented_O": sorted(O),
        "generated_documented_G": sorted(G),
        "shared_T": sorted(T),
        "coverage": {"original_pct_of_S": pct(O),
                     "generated_pct_of_S": pct(G),
                     "shared_pct_of_S": pct(T)},
        "undocumented_in_original": sorted(S - O),
        "undocumented_in_generated": sorted(S - G),
        "original_doc_files": [str(x.relative_to(cfg.root))
                               for x in cfg.original_readme_files],
        "original_doc_chars": len(docs_text),
    }
