"""Documentation checks, manifest selection, and audience documentation context."""
from __future__ import annotations

import re
from .config import AidealConfig
from .readme_agent import parse_readme, public_api_surface
from .doc_check_inputs import _owner_map


def form_check(cfg: AidealConfig) -> dict:
    inventory = parse_readme(cfg.llm_readme)
    failures: dict[str, list[str]] = {}
    for entry in inventory:
        missing = [
            req for req in cfg.required_sections
            if not any(re.search(rf"^### {re.escape(a)}\s*$", entry.body, re.MULTILINE)
                       for a in req.split("|"))
        ]
        if "TODO" in entry.body:
            missing.append("unfilled TODOs")  # a skeleton is not documentation
        if missing:
            failures[entry.name] = missing
    n = len(inventory)
    return {
        "check": "form",
        "passed": bool(n) and not failures,
        "score": round((n - len(failures)) / n, 3) if n else 0.0,
        "details": {"apis": n, "complete": n - len(failures), "missing_sections": failures},
    }


def _load_manifest(cfg: AidealConfig, manifest: str | None) -> list[str] | None:
    """Frozen API manifest: ONE list of names used by every experiment cell, so
    pass-rate deltas can never come from denominator drift (2x2 requirement).
    Accepts a JSON array or {"apis": [...]}; paths resolve against cfg.root."""
    if not manifest:
        return None
    import json as _json
    from pathlib import Path
    p = Path(manifest) if str(manifest).startswith("/") else (cfg.root / manifest)
    data = _json.loads(p.read_text(encoding="utf-8"))
    names = data["apis"] if isinstance(data, dict) else data
    if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):
        raise ValueError(f"manifest {p} must contain a non-empty-string API list")
    names = list(dict.fromkeys(names))
    unknown = sorted(set(names) - set(public_api_surface(cfg)))
    # The primary experiment remains strictly source-surface bounded. A
    # secondary artifact-scale analysis may intentionally evaluate every entry
    # emitted into a generated README, including names later rejected by the
    # surface/intent filter. Such a manifest must opt in explicitly so a typo or
    # arbitrary name can never silently enter an ordinary experiment.
    allow_artifact_entries = (
        isinstance(data, dict)
        and data.get("allow_outside_surface") == "generated_document_entries"
    )
    if unknown and not allow_artifact_entries:
        raise ValueError(f"manifest {p} contains APIs outside the configured public surface: "
                         f"{', '.join(unknown[:10])}")
    return names


def _shared_doc_text(cfg: AidealConfig, doc_source: str) -> str:
    """FULL-DOCUMENT audience context (no truncation — the experiment requires
    the audience to receive the ENTIRE selected documentation; the size is
    recorded in the run JSON so exposure is auditable).

      original         -> every configured baseline doc, whole
      aideal           -> the whole generated LLM_readme.md
      original+aideal  -> both (the B1 arm: original docs + entries the
                          doc-repair loop has created so far)
    """
    parts: list[str] = []
    if doc_source in ("original", "original+aideal"):
        parts.append(cfg.original_readme_text(limit=None))
    if doc_source in ("aideal", "original+aideal"):
        if cfg.llm_readme.exists():
            parts.append("===== GENERATED / REPAIRED API ENTRIES =====\n"
                         + cfg.llm_readme.read_text(encoding="utf-8", errors="ignore"))
        elif doc_source == "aideal":
            raise FileNotFoundError(f"{cfg.llm_readme} missing (doc_source=aideal)")
    return "\n\n".join(p for p in parts if p.strip())


def _markdown_chunks(text: str) -> list[str]:
    """Stable file/heading chunks for deterministic, non-LLM retrieval."""
    chunks: list[str] = []
    file_header = ""
    current: list[str] = []
    fence: tuple[str, int] | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        # Synthetic file boundaries are authoritative and reset malformed or
        # unclosed Markdown state from the previous source file.
        if line.startswith("===== ") and line.endswith(" ====="):
            if current:
                chunks.append("\n".join(([file_header] if file_header else []) + current).strip())
            file_header, current, fence = line, [], None
            continue
        fm = re.match(r"^(`{3,}|~{3,})", stripped)
        if fm:
            token = fm.group(1)
            marker = (token[0], len(token))
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and marker[1] >= fence[1]:
                fence = None
        if fence is None and re.match(r"^#{1,6}\s+", line) and current:
            chunks.append("\n".join(([file_header] if file_header else []) + current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(([file_header] if file_header else []) + current).strip())
    return [c for c in chunks if c]


def _relevant_original_texts(cfg: AidealConfig, names: list[str], limit: int) -> dict[str, str]:
    """Index the original bundle for every manifest API in one corpus pass.

    The old per-API implementation re-read and re-split a 15 MB Javadoc bundle
    more than a thousand times. This preserves the same deterministic ranking
    and character cap while making all-surface overnight runs practical.
    """
    from .readme_agent import _doc_code_mentions
    raw = cfg.original_readme_text(limit=None)
    coverage_cfg = ((cfg.raw or {}).get("coverage") or {})
    call_patterns = coverage_cfg.get("documentation_call_patterns")
    wanted = set(names)
    matches: dict[str, list[tuple[int, int, str]]] = {name: [] for name in names}
    for pos, chunk in enumerate(_markdown_chunks(raw)):
        for name in _doc_code_mentions(chunk, wanted, call_patterns=call_patterns):
            escaped = re.escape(name)
            calls = len(re.findall(rf"\.{escaped}\b|\b{escaped}\s*[\(\[]", chunk))
            mentions = len(re.findall(rf"\b{escaped}\b", chunk))
            matches[name].append((calls * 100 + mentions, pos, chunk))

    result: dict[str, str] = {}
    for name in names:
        ranked = sorted(matches[name], key=lambda item: (-item[0], item[1]))
        selected: list[str] = []
        used = 0
        for _, _, chunk in ranked:
            separator = 2 if selected else 0
            remaining = limit - used - separator
            if remaining <= 0:
                break
            selected.append(chunk[:remaining])
            used += separator + min(len(chunk), remaining)
        result[name] = ("\n\n".join(selected) if selected else
                        f"No code-context section for `{name}` was found in the configured "
                        "original documentation.")
    return result


def _relevant_doc_inventory(cfg: AidealConfig, doc_source: str, names: list[str]):
    """Per-API relevant documentation with one equal character ceiling per source."""
    from .readme_agent import ApiEntry
    limit = int((cfg.comprehension or {}).get("relevant_doc_chars", 12000) or 12000)
    generated = {e.name: e for e in parse_readme(cfg.llm_readme)} if cfg.llm_readme.exists() else {}
    part_limit = limit // 2 if doc_source == "original+aideal" else limit
    original = (_relevant_original_texts(cfg, names, part_limit)
                if doc_source in ("original", "original+aideal") else {})
    inventory = []
    for name in names:
        parts: list[str] = []
        if doc_source in ("original", "original+aideal"):
            parts.append(original[name])
        if doc_source in ("aideal", "original+aideal"):
            entry = generated.get(name)
            if entry:
                parts.append(entry.body[:part_limit])
        body = "\n\n===== RELATED DOCUMENTATION =====\n\n".join(parts)[:limit]
        inventory.append(ApiEntry(name=name, goal="", snippet="", body=body))
    return inventory


def _comprehension_inventory(cfg: AidealConfig, doc_source: str,
                             manifest: list[str] | None = None,
                             full_doc: bool = False,
                             doc_scope: str | None = None):
    """Build (inventory, shared_doc, error_dict). shared_doc is None unless
    full_doc — then every entry's audience context = shared_doc + target line
    (built late in the execute loop; bodies stay empty to avoid duplicating a
    multi-MB document per entry)."""
    from .readme_agent import ApiEntry
    if doc_scope == "relevant":
        names = manifest or (sorted(public_api_surface(cfg)) if doc_source.startswith("original")
                             else [e.name for e in parse_readme(cfg.llm_readme)
                                   if "TODO" not in e.body])
        return _relevant_doc_inventory(cfg, doc_source, names), None, None
    if full_doc:
        # denominator: the frozen manifest if given, else the doc's own names
        if manifest:
            names = manifest
        elif doc_source in ("original", "original+aideal"):
            names = sorted(public_api_surface(cfg))
        else:
            names = [e.name for e in parse_readme(cfg.llm_readme)
                     if "TODO" not in e.body]
        try:
            shared = _shared_doc_text(cfg, doc_source)
        except FileNotFoundError as exc:
            return None, None, {"check": "comprehension", "passed": False, "score": 0.0,
                                "details": {"error": str(exc)}}
        if not shared.strip():
            return None, None, {"check": "comprehension", "passed": False, "score": 0.0,
                                "details": {"error": f"no documentation text for "
                                            f"doc_source={doc_source}"}}
        return [ApiEntry(name=n, goal="", snippet="", body="") for n in names], \
            shared, None
    if doc_source == "original":
        if not cfg.original_readme_files:
            return None, None, {"check": "comprehension", "passed": False, "score": 0.0,
                                "details": {"error": "files.original_readme not configured or missing"}}
        text = cfg.original_readme_text(limit=12000)   # legacy (non-full-doc) mode
        names = manifest or sorted(public_api_surface(cfg))
        return [ApiEntry(name=n, goal="", snippet="",
                         body=f"(Original project README — the only documentation available)\n"
                              f"{text}\n\nTarget function: `{n}`")
                for n in names], None, None
    if doc_source == "agents":
        # BASELINE ARM: the repo's holistic agent guide (AGENTS.md) as the ONLY
        # context — the industry-standard single-file "how to work in this repo"
        # doc. Path from files.agents_doc (default AGENTS.md at project root).
        from pathlib import Path
        rel = (cfg.raw.get("files", {}) or {}).get("agents_doc", "AGENTS.md")
        p = (cfg.root / rel)
        if not p.exists():
            return None, None, {"check": "comprehension", "passed": False, "score": 0.0,
                                "details": {"error": f"agents doc not found at {rel} "
                                            "(set files.agents_doc, or drop an AGENTS.md at project root)"}}
        text = p.read_text(encoding="utf-8", errors="ignore")[:12000]
        names = manifest or sorted(public_api_surface(cfg))
        return [ApiEntry(name=n, goal="", snippet="",
                         body=f"(Project AGENTS.md — the only agent guidance available)\n"
                              f"{text}\n\nTarget function: `{n}`")
                for n in names], None, None
    inventory = [e for e in parse_readme(cfg.llm_readme) if "TODO" not in e.body]
    if manifest:
        by = {e.name: e for e in inventory}
        inventory = [by[n] for n in manifest if n in by]
    if not inventory:
        return None, None, {"check": "comprehension", "doc_source": doc_source, "passed": False,
                            "score": 0.0,
                            "details": {"error": "LLM_readme has no filled entries (skeleton TODOs "
                                                 "don't count) - run `readme --generate` or fill them"}}
    return inventory, None, None


def _build_catalogue_context(cfg: AidealConfig):
    """(model, name_to_gkey, by_name) for INDEX-FIRST comprehension, or None. Builds
    the SAME catalogue model `write_catalogue` renders, so the receiver line + the
    verified-sibling call pattern handed to the audience match the per-class files."""
    from .readme_agent import (_catalogue_model, _grounding_tiers, _exec_status_map,
                               parse_readme, public_api_details)
    entries = [e for e in parse_readme(cfg.llm_readme) if "TODO" not in e.body]
    if not entries:
        return None
    tiers, class_of, _ = _grounding_tiers(cfg)
    exec_status = _exec_status_map(cfg)
    owner = _owner_map(cfg)
    file_of = {d["name"]: d["file"] for d in public_api_details(cfg)}
    model = _catalogue_model(entries, tiers, exec_status, class_of, owner, file_of=file_of)
    name_to_gkey = {x["name"]: g for g, m in model.items() for x in m["members"]}
    return model, name_to_gkey, {e.name: e for e in entries}


def _resolve_class_context(cfg: AidealConfig, override: bool | None) -> bool:
    """CLI override wins; else the `comprehension.class_context` config flag (default off)."""
    if override is not None:
        return override
    return bool((cfg.comprehension or {}).get("class_context", False))


def _normalize(name: str) -> str:
    return re.sub(r"\[.*\]$", "", name).strip("`")


def completeness_check(cfg: AidealConfig) -> dict:
    surface = public_api_surface(cfg)                       # intended-API set
    raw = public_api_surface(cfg, override_filter="all")    # raw discovered surface
    documented = {_normalize(e.name) for e in parse_readme(cfg.llm_readme)}
    undocumented = sorted(surface - documented)
    n = len(surface)
    return {
        "check": "completeness",
        "passed": not undocumented,
        "score": round((n - len(undocumented)) / n, 3) if n else 0.0,
        "details": {
            "raw_surface": len(raw),               # every visible public def
            "intended_surface": n,                 # surface_filter set = denominator
            "surface_filter": cfg.surface_filter,
            "public_functions": n,                 # (= intended_surface; kept for back-compat)
            "documented": len(documented),
            "undocumented": undocumented,
            "orphan_doc_entries": sorted(documented - surface),
        },
    }
