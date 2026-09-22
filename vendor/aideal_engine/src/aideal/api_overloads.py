"""Canonical overload selection and duplicate-signature reporting."""
from __future__ import annotations

import re
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
)
from .api_intent import (
    intent_scores,
)


def _subsume_overloads(recs: list[dict],
                       deprioritize: tuple = ()) -> tuple[list[dict], list[tuple[dict, dict]]]:
    """Telescoping-overload analysis for ONE name's definition sites.

    Same function, different parameter lists: within the SAME file (one class
    family), an overload whose parameter types are a proper prefix of a longer
    sibling's is a convenience form of that sibling (it delegates with
    defaults) — the catalog needs only the LONGEST form ("needed longest
    parameters"), e.g. `foo(x)` and `foo(x,y)` are one function documented as
    `foo(x,y)`. Cross-file same-name defs (Java facades, interface
    implementations) are never subsumed — different receiver contexts.

    Returns (maximals, subsumed): `maximals` sorted longest-params-first (then
    documented, shallowest path, line — so [0] is the canonical signature);
    `subsumed` = [(rec, subsumed_by_rec)] pointing at the LONGEST subsumer, so
    a chain foo(x) ⊂ foo(x,y) ⊂ foo(x,y,z) maps both short forms to the full one.
    """
    def _types(r: dict) -> tuple:
        return tuple((p.get("type") or "?") for p in r["params"])

    by_file: dict[str, list[dict]] = {}
    for r in recs:
        by_file.setdefault(r["file"], []).append(r)
    subsumed: list[tuple[dict, dict]] = []
    losers: set[int] = set()
    for group in by_file.values():
        for a in group:
            ta = _types(a)
            best = None
            for b in group:
                tb = _types(b)
                if b is not a and len(tb) > len(ta) and tb[:len(ta)] == ta:
                    if best is None or len(tb) > len(_types(best)):
                        best = b
            if best is not None:
                subsumed.append((a, best))
                losers.add(id(a))
    maximals = [r for r in recs if id(r) not in losers]
    # Election among the surviving maximals: within one file the longest
    # already won via subsumption; ACROSS files prefer non-deprioritized
    # paths (facade duplicates — e.g. Beast's Java* wrappers returning
    # JavaRasterRDD, the form the pipeline deliberately avoids because it
    # forced invented .toRDD adapters), then the documented context, then the
    # longest signature.
    def _depri(r: dict) -> bool:
        return any(p.search(r["file"]) for p in deprioritize)
    maximals.sort(key=lambda r: (_depri(r), not r["description"].strip(),
                                 -len(r["params"]),
                                 r["file"].count("/"), r["file"], r["line"]))
    return maximals, subsumed


def _dedup_deprioritize(cfg: AidealConfig) -> tuple:
    """Compiled `codebase.dedup.deprioritize_paths` patterns (adapter-level
    default for scala-spark: Java facade files `Java*.scala`)."""
    pats = ((cfg.raw.get("codebase", {}) or {}).get("dedup", {}) or {}).get(
        "deprioritize_paths", []) or []
    return tuple(re.compile(p) for p in pats)


def dedup_report(cfg: AidealConfig) -> dict:
    """Redundancy audit of the SELECTED surface. Deterministic (no LLM).

    Four redundancy classes, each auditable:
      1. overload collapse — one catalog entry per name; canonical site elected
         (documented > shallowest path > lowest line), others become variants;
      2. forwarder alias edges — `def a(...) = b(...)` one-liners where both
         names are selected: `a` should be catalogued as an alias of `b`, not
         documented twice;
      3. same-file same-signature twins — review list (often legitimate pairs
         like compress/decompress; never auto-dropped);
      4. alias-registry cross-check — registry aliases (aliases.json + any
         *.scala alias object using the ``(alias for `X`)`` doc convention)
         must point at a selected canonical and not shadow a surface name.
    """
    import json as _json
    det = [d for d in public_api_details(cfg) if d["visibility"] == "public"]
    scores = intent_scores(cfg)
    sel = {n for n, v in scores.items() if v["selected"]}
    by_name: dict[str, list[dict]] = {}
    for d in det:
        if d["name"] in sel:
            by_name.setdefault(d["name"], []).append(d)

    # 1. overload collapse — subsumption-aware: canonical = the maximal
    # telescoping overload ("needed longest parameters"); same-file
    # prefix-shorter forms are the SAME function with defaults, recorded under
    # subsumed_overloads, not as distinct variants.
    collapse: dict[str, dict] = {}
    subsumed_total = 0
    _depri_pats = _dedup_deprioritize(cfg)
    for n, recs in sorted(by_name.items()):
        maximals, subsumed = _subsume_overloads(recs, _depri_pats)
        canon = maximals[0]
        subsumed_total += len(subsumed)
        collapse[n] = {"sites": len(recs),
                       "canonical": f"{canon['file']}:{canon['line']}",
                       "signature": canon["signature"],
                       "subsumed_overloads": [
                           {"site": f"{a['file']}:{a['line']}",
                            "params": len(a["params"]),
                            "same_function_as": f"{b['file']}:{b['line']}"}
                           for a, b in subsumed],
                       "distinct_variants": len(maximals) - 1}

    # 2. forwarder alias edges (same-line `= callee(...)`). An edge only
    # COLLAPSES a catalog entry when EVERY def site of the name forwards to
    # the same canonical ("full"); otherwise it is "partial" — e.g. RDPro's
    # `shapefile` forwards to `spatialFile` in the Java context but is the
    # documented first-class entry point in the Scala mixin, so it stays.
    fcache: dict[str, list[str]] = {}
    forwarders: list[dict] = []
    for n, recs in sorted(by_name.items()):
        callees, sites = set(), []
        for d in recs:
            try:
                lines = fcache.setdefault(
                    d["file"], (cfg.root / d["file"]).read_text(encoding="utf-8", errors="ignore").splitlines())
                m = re.search(r"=\s*([A-Za-z_][\w.]*)\s*[\(\[]", lines[d["line"] - 1])
            except (OSError, IndexError):
                m = None
            callee = m.group(1).split(".")[-1] if m else None
            if callee in sel and callee != n:
                callees.add(callee); sites.append(f"{d['file']}:{d['line']}")
            else:
                callees.add(None)  # at least one non-forwarding site
        real = callees - {None}
        if real:
            full = None not in callees and len(real) == 1
            forwarders.append({"alias": n, "canonical": sorted(real)[0] if full else sorted(real),
                               "collapse": "full" if full else "partial",
                               "sites": sites})

    # 3. same-file same-signature twins
    twin_ix: dict[tuple, set[str]] = {}
    for n, recs in by_name.items():
        for d in recs:
            key = (d["file"], tuple((p.get("type") or "?") for p in d["params"]),
                   d["returns"] or "?")
            twin_ix.setdefault(key, set()).add(n)
    twins = [{"file": k[0], "params": list(k[1]), "returns": k[2], "names": sorted(v)}
             for k, v in sorted(twin_ix.items()) if len(v) > 1]

    # 4. alias-registry cross-check
    reg_aliases: list[dict] = []
    try:
        if cfg.aliases_file.exists():
            for r in _json.loads(cfg.aliases_file.read_text(encoding="utf-8")):
                reg_aliases.append({"alias": r["alias"], "canonical": r["canonical"],
                                    "status": r.get("status"), "source": cfg.aliases_file.name,
                                    "shadows_surface": r["alias"] in sel,
                                    "canonical_in_surface": r["canonical"] in sel})
    except Exception:
        pass
    for sf in sorted(cfg.aliases_file.parent.glob("*.scala")):
        text = sf.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"\(alias for `([\w\[\]]+)`\).*?\bdef\s+(\w+)", text, re.S):
            reg_aliases.append({"alias": m.group(2), "canonical": m.group(1),
                                "status": "added", "source": sf.name,
                                "shadows_surface": m.group(2) in sel,
                                "canonical_in_surface": m.group(1) in sel})

    sites_total = sum(c["sites"] for c in collapse.values())
    full_fwd = {f["alias"] for f in forwarders if f["collapse"] == "full"}
    return {
        "selected_names": len(by_name),
        "selected_def_sites": sites_total,
        "collapsed_variants": sites_total - len(by_name),
        "subsumed_overload_sites": subsumed_total,
        "forwarder_alias_edges": forwarders,
        "catalog_entries_after_aliasing": len(by_name) - len(full_fwd),
        "same_signature_twins": twins,
        "registry_aliases": reg_aliases,
        "collapse": collapse,
    }
