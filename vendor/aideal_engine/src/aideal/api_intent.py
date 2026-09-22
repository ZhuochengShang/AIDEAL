"""Auditable API intent scoring and optional model-based selection."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
)
from .api_signatures import (
    _doc_at,
    _python_qualified_identities,
)
from .api_visibility import (
    _is_public,
    _iter_defs,
    visibility_model,
)


# Generic boilerplate/lifecycle names (cross-language plumbing, not domain API).
_BOILERPLATE_NAMES = {
    "hasNext", "next", "close", "compareTo", "copy", "apply", "unapply",
    "equals", "hashCode", "toString", "iterator", "clone", "finalize",
    "productElement", "productArity", "productIterator", "productPrefix",
    "canEqual", "get", "set", "read", "write", "getClass", "wait", "notify",
}


_INTERNAL_PATH_SEGMENTS = ("/internal/", "/impl/", "/detail/", "/private/",
                           "/generated/", "/internals/")


_DEFAULT_INTENT_WEIGHTS = {
    "documented": 2, "tested": 3, "mentioned_in_docs": 4, "non_override": 1,
    "override": -3, "internal_path": -5, "boilerplate_name": -4,
    "many_impls": -3,  # interface-method detector: name defined at >= many_impls_threshold sites
    "llm_common": 0,   # off by default; >0 + intent.use_llm enables the LLM signal
}


def llm_common_apis(cfg: AidealConfig, candidates: set[str], refresh: bool = False) -> set[str]:
    """OPTIONAL LLM signal: the author model (with the role/domain persona) judges
    which candidates are commonly-used, user-facing operations. ONE call over the
    whole list, then CACHED to docs/intent_common.json so the intent score stays
    reproducible across runs (delete the cache or pass refresh to re-judge)."""
    import json as _json
    cache = cfg.llm_readme.parent / "intent_common.json"
    if cache.exists() and not refresh:
        try:
            cached = _json.loads(cache.read_text(encoding="utf-8"))
            if cached:  # an EMPTY cached list is a failed judge run, not a
                return set(cached) & candidates  # verdict — treat as a miss
        except Exception:
            pass
    from .llm import invoke_text
    from .prompts import load as load_prompt
    from .profile import require_profile
    require_profile(cfg)
    details = {d["name"]: d for d in public_api_details(cfg)}
    listing = "\n".join(f"- {n}: {details.get(n, {}).get('signature', n)}"
                        for n in sorted(candidates))
    system, user = load_prompt(cfg, "aideal/intent_common", api_list=listing)
    # dump the exact rendered prompt + raw response so the LLM step is auditable
    dump = cache.parent / "intent_common_prompt.txt"
    dump.parent.mkdir(parents=True, exist_ok=True)
    resp = invoke_text(cfg.model_for_role("author"), system, user)
    dump.write_text(
        f"MODEL: {cfg.model_for_role('author')}\n\n"
        f"===== SYSTEM =====\n{system}\n\n===== USER =====\n{user}\n\n"
        f"===== RESPONSE =====\n{resp}\n",
        encoding="utf-8")
    try:
        picked = set(_json.loads(resp[resp.index("["):resp.rindex("]") + 1]))
    except Exception:
        picked = {ln.strip("-* `").strip() for ln in resp.splitlines() if ln.strip()}
    picked &= candidates
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(_json.dumps(sorted(picked), indent=2), encoding="utf-8")
    return picked


def intended_api_llm(cfg: AidealConfig) -> tuple[set[str], dict]:
    """Token-efficient intended-API selection: STATIC evidence auto-includes the
    obvious (score >= include_threshold) and auto-excludes the clearly-internal
    (score <= exclude_threshold); the LLM adjudicates ONLY the ambiguous middle
    band, in batches, from COMPACT records (name/signature/doc/score/signals) —
    never source. Decisions are cached with provenance (`intended_api.cache`) so
    runs are reproducible. Returns (selected_names, decisions)."""
    import json as _json
    ia = (cfg.raw.get("codebase", {}) or {}).get("intended_api", {}) or {}
    inc_t = int(ia.get("static_include_threshold", 8))
    exc_t = int(ia.get("static_exclude_threshold", 1))
    batch = int(ia.get("batch_size", 25))
    selection_limit = int(ia.get("selection_limit", 0) or 0)
    rubric_version = int(ia.get("rubric_version", 2))
    refresh = bool(ia.get("refresh", False))
    cache_path = (cfg.root / ia.get("cache", "docs/intended_api_decisions.json")).resolve()

    scores = intent_scores(cfg)
    identity = str(ia.get("identity", "bare"))
    all_details = [d for d in public_api_details(cfg) if d["visibility"] == "public"]
    if identity == "qualified" and cfg.language.lower() == "python":
        # Exact qualified duplicates can arise from conditional definitions;
        # elect one canonical record deterministically. Distinct owners remain
        # distinct (RMSD.run != AnalysisBase.run).
        details = {}
        for d in sorted(all_details, key=lambda r: (
                r["qualified_name"], not bool(r["description"]),
                -len(r["params"]), r["file"], r["line"])):
            details.setdefault(d["qualified_name"], d)
        if ia.get("candidate_filter", "static_selected") == "static_selected":
            details = {q: d for q, d in details.items()
                       if scores.get(d["name"], {}).get("selected")}
        candidate_scores = {q: scores[d["name"]] for q, d in details.items()}
    else:
        details = {d["name"]: d for d in all_details}
        candidate_scores = scores
        if ia.get("candidate_filter", "static_selected") == "static_selected":
            candidate_scores = {n: info for n, info in scores.items()
                                if info.get("selected") and n in details}
            details = {n: details[n] for n in candidate_scores}
    selected: set[str] = set()
    decisions: dict[str, dict] = {}
    ambiguous: list[str] = []
    for name, info in candidate_scores.items():
        s = info["score"]
        if s >= inc_t:
            selected.add(name); decisions[name] = {"decision": "include", "by": "static", "score": s}
        elif s <= exc_t:
            decisions[name] = {"decision": "exclude", "by": "static", "score": s}
        else:
            ambiguous.append(name)

    cache: dict = {}
    if cache_path.exists() and not refresh:
        try:
            cache = _json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    # A cached judgment is reusable only when it was produced with the same
    # rubric.  This prevents an older binary include/exclude pilot from being
    # silently mixed with a later scored ranking experiment.
    todo = [n for n in ambiguous
            if n not in cache or cache[n].get("rubric_version") != rubric_version]
    if todo:
        try:
            import hashlib as _hashlib
            from .llm import invoke_text
            from .prompts import load as load_prompt
            from .profile import require_profile
            require_profile(cfg)
            model = cfg.model_for_role("author")
            for i in range(0, len(todo), batch):
                chunk = todo[i:i + batch]
                recs = [{"name": n,
                         "bare_name": details.get(n, {}).get("name", n),
                         "module": details.get(n, {}).get("module", ""),
                         "owner": details.get(n, {}).get("owner", ""),
                         "kind": details.get(n, {}).get("definition_kind", ""),
                         "signature": details.get(n, {}).get("signature", n),
                         "doc": (details.get(n, {}).get("description", "") or "")[:240],
                         "static_score": candidate_scores[n]["score"],
                         "signals": candidate_scores[n]["reasons"],
                         "available_receiver_types": ia.get("available_receiver_types", [])}
                        for n in chunk]
                system, user = load_prompt(
                    cfg, "aideal/intended_review",
                    records=_json.dumps(recs, ensure_ascii=False, indent=2))
                prompt_sha = _hashlib.sha256(
                    (system + "\0" + user).encode("utf-8")).hexdigest()
                resp = invoke_text(model, system, user)
                parsed = []
                try:
                    parsed = _json.loads(resp[resp.index("["):resp.rindex("]") + 1])
                except Exception:
                    parsed = []
                bydec = {d.get("name"): d for d in parsed if isinstance(d, dict)}
                for n in chunk:
                    d = bydec.get(n, {})
                    ratings = d.get("ratings", {}) if isinstance(d.get("ratings"), dict) else {}
                    clean_ratings = {
                        key: max(0, min(3, int(ratings.get(key, 0) or 0)))
                        for key in ("user_facing", "fixture_runnable",
                                    "oracle_strength", "domain_relevance")
                    }
                    family = str(d.get("capability_family", "")).strip().lower()
                    family = re.sub(r"[^a-z0-9_.:/+-]+", "-", family).strip("-")
                    if not family:
                        # Deterministic fallback: a missing model label cannot
                        # erase the symbol from family-coverage accounting.
                        family = (details[n].get("module", "unknown") + "/" +
                                  details[n].get("name", n)).lower()
                    cache[n] = {"decision": d.get("decision", "uncertain"),
                                "reason": d.get("reason", ""), "by": "llm",
                                "score": candidate_scores[n]["score"], "model": model.model,
                                "provider": model.provider, "identity": identity,
                                "ratings": clean_ratings,
                                "capability_family": family,
                                "rubric_version": rubric_version,
                                "prompt_sha256": prompt_sha,
                                "source": f"{details[n]['file']}:{details[n]['line']}"}
                # Crash-safe intent progress: each paid batch is durable.
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(
                    _json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            if ia.get("require_llm", False):
                raise
            pass  # LLM unavailable -> fall back to the static threshold below

    thr = candidate_scores and next(iter(candidate_scores.values())).get("threshold", 5)
    for n in ambiguous:
        d = cache.get(n)
        if d is None:                       # LLM unavailable: fall back to intent threshold
            inc = candidate_scores[n]["score"] >= (thr or 5)
            decisions[n] = {"decision": "include" if inc else "exclude",
                            "by": "static_fallback", "score": candidate_scores[n]["score"]}
        else:
            decisions[n] = d
        if decisions[n]["decision"] == "include":
            selected.add(n)

    # Optional fixed-budget selection.  The LLM supplies auditable semantic
    # ratings; the tool performs the final ranking deterministically.  Static
    # evidence is deliberately a small tie-breaker rather than the main score,
    # because large libraries often give hundreds of symbols the same static
    # score.  Soft owner/module caps improve breadth; if they prevent filling
    # the requested budget, the remaining highest-ranked symbols fill it.
    if selection_limit and len(selected) > selection_limit:
        weights = {"user_facing": 4, "fixture_runnable": 4,
                   "oracle_strength": 3, "domain_relevance": 2,
                   "static_score": 1}
        weights.update(ia.get("ranking_weights", {}) or {})

        def _rank_score(name: str) -> int:
            ratings = decisions[name].get("ratings", {}) or {}
            value = sum(int(weights[k]) * int(ratings.get(k, 0) or 0)
                        for k in ("user_facing", "fixture_runnable",
                                  "oracle_strength", "domain_relevance"))
            # Bound the legacy score so it cannot dominate semantic quality.
            static = max(-5, min(10, int(candidate_scores[name]["score"])))
            return value + int(weights["static_score"]) * static

        ranked = sorted(selected, key=lambda n: (
            -_rank_score(n), details[n].get("module", ""),
            details[n].get("owner", ""), n))
        max_owner = int(ia.get("max_per_owner", 0) or 0)
        max_module = int(ia.get("max_per_module", 0) or 0)
        owner_counts: dict[str, int] = {}
        module_counts: dict[str, int] = {}
        chosen: list[str] = []
        deferred: list[str] = []
        # First take the strongest representative of every capability family.
        # If there are more families than budget, their strongest members
        # compete on the same global score. Remaining slots then return to the
        # ordinary global ranking. This prevents a dense family of near-aliases
        # from crowding an entire operation family out of the experiment.
        family_heads: list[str] = []
        seen_families: set[str] = set()
        for n in ranked:
            family = decisions[n].get("capability_family", "unknown")
            if family not in seen_families:
                family_heads.append(n)
                seen_families.add(family)
        family_head_set = set(family_heads[:selection_limit])
        ordered = family_heads[:selection_limit] + [n for n in ranked if n not in family_head_set]
        for n in ordered:
            owner = details[n].get("owner", "") or "<module>"
            module = details[n].get("module", "") or "<unknown>"
            if ((max_owner and owner_counts.get(owner, 0) >= max_owner) or
                    (max_module and module_counts.get(module, 0) >= max_module)):
                deferred.append(n)
                continue
            chosen.append(n)
            owner_counts[owner] = owner_counts.get(owner, 0) + 1
            module_counts[module] = module_counts.get(module, 0) + 1
            if len(chosen) == selection_limit:
                break
        if len(chosen) < selection_limit:
            chosen.extend(deferred[:selection_limit - len(chosen)])
        selected = set(chosen)
        rank_by_name = {n: i + 1 for i, n in enumerate(ranked)}
        for n in ranked:
            decisions[n]["ranking_score"] = _rank_score(n)
            decisions[n]["rank"] = rank_by_name[n]
            decisions[n]["selected_in_budget"] = n in selected
            if n not in selected:
                decisions[n]["adjudication"] = decisions[n]["decision"]
                decisions[n]["decision"] = "exclude"
                decisions[n]["reason"] = "outside fixed selection budget; " + decisions[n].get("reason", "")
        represented = {decisions[n].get("capability_family", "unknown") for n in selected}
        eligible_families = {decisions[n].get("capability_family", "unknown") for n in ranked}
        for n in ranked:
            decisions[n]["selection_summary"] = {
                "budget": selection_limit,
                "eligible_apis": len(ranked),
                "eligible_families": len(eligible_families),
                "represented_families": len(represented),
            }
    return selected, decisions


def _names_called_in(text: str, names: set[str]) -> set[str]:
    """Subset of `names` that appear as a call/use in `text`."""
    if not text or not names:
        return set()
    alternatives = "|".join(sorted((re.escape(n) for n in names),
                                     key=len, reverse=True))
    pattern = re.compile(
        rf"\b(?P<call>{alternatives})\s*[\(\[]|\.\s*(?P<member>{alternatives})\b")
    return {m.group("call") or m.group("member") for m in pattern.finditer(text)}


def _doc_code_mentions(docs_text: str, names: set[str],
                       call_patterns: list[str] | None = None) -> set[str]:
    """Subset of `names` mentioned in a CODE context of the baseline docs:
    inside a fenced code block, inside inline backticks, or in call form
    (`.name` / `name(`) anywhere. A bare English-word match in prose does NOT
    count — with plain `\\b name \\b` matching, common-word APIs (RDPro:
    `run`, `this`, `close`, `write`, `read`) earned a spurious
    mentioned_in_docs(+4) just because the README uses those words in
    sentences."""
    if not docs_text or not names:
        return set()
    # Parse fenced and inline code separately. The old `` `([^`]+)` `` also
    # matched pieces of triple-backtick fences and could span prose between
    # them, turning ordinary words such as "area" or "build" into false code
    # evidence. Inline spans may not touch another backtick or cross a line.
    fenced = re.findall(r"```[^\n]*\n(.*?)\n```", docs_text, re.S)
    without_fences = re.sub(r"```[^\n]*\n.*?\n```", "", docs_text,
                            flags=re.S)
    inline = re.findall(r"(?<!`)`([^`\n]+)`(?!`)", without_fences)
    code = "\n".join(fenced) + "\n" + " ".join(inline)
    out: set[str] = set()
    alternatives = "|".join(sorted((re.escape(n) for n in names),
                                     key=len, reverse=True))
    code_pattern = re.compile(rf"\b(?P<aideal_code_api>{alternatives})\b")
    out.update(m.group("aideal_code_api") for m in code_pattern.finditer(code))
    # Patterns are format strings containing ``{name}``; adapters/projects may
    # add syntax such as Rust ``{name}!`` or Ruby ``:{name}`` without changing
    # tool code. Backticks/fenced code remain language-neutral evidence.
    patterns = call_patterns or [r"\.{name}\b", r"\b{name}\s*\(",
                                 r"\b{name}\s*\["]
    for i, pattern in enumerate(patterns):
        group = f"aideal_syntax_api_{i}"
        rendered = pattern.format(name=f"(?P<{group}>{alternatives})")
        out.update(m.group(group) for m in re.finditer(rendered, docs_text))
    return out


def intent_scores(cfg: AidealConfig, force_llm: bool | None = None) -> dict[str, dict]:
    """Score each public API by GENERIC evidence of user-facing intent and select
    those at/above a threshold. Codebase-agnostic: signals are documentation,
    tests, original-doc mentions, visibility/override, internal-path and
    boilerplate-name penalties. Weights/threshold/manual overrides come from
    `codebase.intent` in aideal.yaml. Returns {name: {score, reasons, selected}}
    — auditable, with per-API reasons."""
    intent = (cfg.raw.get("codebase", {}) or {}).get("intent", {}) or {}
    W = dict(_DEFAULT_INTENT_WEIGHTS); W.update(intent.get("weights", {}) or {})
    threshold = int(intent.get("threshold", 5))
    manual_inc = set(intent.get("manual_include", []) or [])
    manual_exc = set(intent.get("manual_exclude", []) or [])
    excl_pats = [re.compile(p) for p in (intent.get("exclude_name_patterns", []) or [])]
    boiler = _BOILERPLATE_NAMES | set(intent.get("boilerplate_names", []) or [])
    # interface-method detector: a name with many definition sites is (almost
    # always) a trait/interface method implemented per class, not one operation
    # (RDPro: run×29, write×27, close×27, read×24). Penalty is evidence-based
    # and auditable; strong real APIs (documented+tested+code-mentioned)
    # survive it. Tune via codebase.intent.{weights.many_impls, many_impls_threshold}.
    many_thr = int(intent.get("many_impls_threshold", 5))
    # docs_mention_mode: "code" (default) counts a doc mention only in code
    # context (fenced block / backticks / call form); "any" is the legacy
    # plain word match — kept for A/B comparison.
    mention_mode = intent.get("docs_mention_mode", "code")

    model = visibility_model(cfg)
    # Python's regex scanner sees nested local functions as well as importable
    # module/class APIs. Keep the intent denominator aligned with
    # public_api_details(), which uses AST-derived identities to reject locals.
    py_identities = _python_qualified_identities(cfg) if cfg.language.lower() == "python" else None
    file_cache: dict[str, list[str]] = {}
    recs: dict[str, dict] = {}
    for name, prefix, path, i, _line in _iter_defs(cfg):
        if name in cfg.exclude_names or not _is_public(name, prefix, model):
            continue
        if py_identities is not None:
            rel = str(Path(path).relative_to(cfg.root)).replace("\\", "/")
            if (rel, i + 1, name) not in py_identities:
                continue
        r = recs.setdefault(name, {"documented": False, "non_override": False,
                                   "internal": False, "sites": 0})
        r["sites"] += 1
        if not re.search(r"\boverride\b", prefix):
            r["non_override"] = True
        norm = "/" + path.replace("\\", "/").lower() + "/"
        if any(seg in norm for seg in _INTERNAL_PATH_SEGMENTS):
            r["internal"] = True
        lines = file_cache.setdefault(path, Path(path).read_text(encoding="utf-8", errors="ignore").splitlines())
        if _doc_at(cfg, lines, i).strip():
            r["documented"] = True

    names = set(recs)
    # evidence from tests and the original docs (computed once over the corpus)
    tested = set()
    for g in cfg.test_globs:
        for p in globmod.glob(str(cfg.root / g), recursive=True):
            tested |= _names_called_in(Path(p).read_text(encoding="utf-8", errors="ignore"), names - tested)
    docs_text = cfg.original_readme_text() if cfg.original_readme_files else ""
    if mention_mode == "code":
        mentioned = _doc_code_mentions(docs_text, names)
    else:  # "any" — legacy plain word match (A/B baseline)
        mentioned = {n for n in names if docs_text and re.search(rf"\b{re.escape(n)}\b", docs_text)}
    # optional LLM "commonly-used" signal (opt-in, cached for reproducibility).
    # force_llm overrides config: True = run it (default weight 4 if unset),
    # False = skip it (static-only). None = honor codebase.intent.use_llm.
    use_llm = intent.get("use_llm") if force_llm is None else force_llm
    if force_llm and not W.get("llm_common", 0):
        W["llm_common"] = 4
    common: set[str] = set()
    if W.get("llm_common", 0) and use_llm:
        # opt-in signal: degrade to static on ANY failure (missing key, profile
        # gate's SystemExit, network) so the score never crashes.
        try:
            common = llm_common_apis(cfg, names, refresh=bool(intent.get("refresh_llm")))
        except (Exception, SystemExit):
            common = set()

    out: dict[str, dict] = {}
    for name, r in recs.items():
        score = 0; reasons = []
        if r["documented"]:           score += W["documented"];      reasons.append(f"documented(+{W['documented']})")
        if name in tested:            score += W["tested"];          reasons.append(f"tested(+{W['tested']})")
        if name in mentioned:         score += W["mentioned_in_docs"]; reasons.append(f"mentioned_in_docs(+{W['mentioned_in_docs']})")
        if r["non_override"]:         score += W["non_override"];    reasons.append(f"non_override(+{W['non_override']})")
        else:                         score += W["override"];        reasons.append(f"override({W['override']})")
        if r["internal"]:             score += W["internal_path"];   reasons.append(f"internal_path({W['internal_path']})")
        if name in boiler or any(p.search(name) for p in excl_pats):
            score += W["boilerplate_name"]; reasons.append(f"boilerplate_name({W['boilerplate_name']})")
        if W.get("many_impls", 0) and r["sites"] >= many_thr:
            score += W["many_impls"]; reasons.append(f"many_impls({r['sites']} sites,{W['many_impls']})")
        if name in common:
            score += W["llm_common"]; reasons.append(f"llm_common(+{W['llm_common']})")
        selected = score >= threshold
        if name in manual_inc: selected = True;  reasons.append("manual_include")
        if name in manual_exc: selected = False; reasons.append("manual_exclude")
        out[name] = {"score": score, "reasons": reasons, "selected": selected,
                     "threshold": threshold, "sites": r["sites"]}
    return dict(sorted(out.items(), key=lambda kv: (-kv[1]["score"], kv[0])))


def intent_compare(cfg: AidealConfig) -> dict:
    """Compare intended-API selection WITHOUT the LLM signal vs WITH it.

    Runs intent twice on the same surface: static-only (force_llm=False) and
    static+LLM (force_llm=True, default weight 4). Reports counts, Jaccard
    overlap, and the APIs each side adds/drops, so the LLM signal's effect on
    the coverage denominator is auditable. `llm_signal_fired` is False when the
    LLM run silently fell back to static (no API key, unfilled profile, etc.)."""
    static = intent_scores(cfg, force_llm=False)
    llm = intent_scores(cfg, force_llm=True)
    s = {k for k, v in static.items() if v["selected"]}
    l = {k for k, v in llm.items() if v["selected"]}
    union = s | l
    jaccard = round(len(s & l) / len(union), 4) if union else 1.0
    llm_fired = any("llm_common" in "".join(v["reasons"]) for v in llm.values())
    return {
        "surface": len(static),
        "selected_static": len(s),
        "selected_llm": len(l),
        "shared": len(s & l),
        "jaccard": jaccard,
        "added_by_llm": sorted(l - s),
        "dropped_with_llm": sorted(s - l),
        "llm_signal_fired": llm_fired,
    }
