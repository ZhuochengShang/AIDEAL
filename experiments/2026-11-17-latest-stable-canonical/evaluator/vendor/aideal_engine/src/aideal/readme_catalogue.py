"""Per-class catalogue exports and the audience class-context view."""
from __future__ import annotations

import re
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
)
from .readme_evidence import (
    _TIER_BADGE,
    _TIER_RANK,
    _EXEC_RANK,
    _exec_status_map,
    _grounding_tiers,
)
from .readme_format import (
    _section_between,
    parse_readme,
)


def _safe_filenames(gkey_label: dict[str, str]) -> dict[str, str]:
    """Map each group key -> a UNIQUE, filesystem-safe filename stem. Start from the
    human label (simple class name); when two groups sanitize to the same name (the
    general collision: same simple name in different packages, so two DISTINCT class
    files), disambiguate deterministically with trailing key segments, then a short
    stable hash as a last resort. No collision (e.g. RDPro) -> filename == label, so
    output is byte-identical to before."""
    import collections as _c
    import hashlib as _h
    san = lambda s: re.sub(r"[^\w.-]", "_", s)
    desired = {g: san(lbl) for g, lbl in gkey_label.items()}
    dup = {n for n, c in _c.Counter(desired.values()).items() if c > 1}
    out: dict[str, str] = {}
    used: set[str] = set()
    for g in sorted(gkey_label):                       # deterministic assignment order
        name = desired[g]
        if name in dup:                                # qualify with nearest parent segment(s)
            parts = [p for p in re.split(r"[/\\.]", g) if p]
            name = san(".".join(parts[-2:])) if len(parts) >= 2 else name
            while name in used:                        # last resort: stable content hash
                name = f"{desired[g]}-{_h.sha1(g.encode()).hexdigest()[:6]}"
        out[g] = name
        used.add(name)
    return out


def _catalogue_model(entries, tiers: dict, exec_status: dict, class_of: dict, owner: dict,
                     file_of: dict | None = None) -> dict:
    """Pure/testable: group README entries by defining class, rank each class's
    members the SAME way organize_report does (tier, then execution outcome, then
    name), pick the primary, and take the class purpose from the primary's Goal (no
    new LLM call). Returns {group_key: {label, safe, primary, purpose, kind,
    members:[{name,tier,exec}]}}.

    file_of {name -> source file path}: when given, classes are grouped by their
    DEFINING FILE (collision-safe: two same-named classes in different packages stay
    separate) and each group carries a human `label` + a unique `safe` filename.
    Omitted -> grouping falls back to the simple class name (back-compatible)."""
    from collections import defaultdict
    import os as _os
    by_name = {e.name: e for e in entries}
    groups: dict[str, list] = defaultdict(list)
    gkey_label: dict[str, str] = {}
    for e in entries:
        f = (file_of or {}).get(e.name, "")
        if f.endswith(".scala"):
            gkey = f[:-6]                              # path stem — unique per source file
            label = _os.path.basename(gkey)
        else:
            gkey = class_of.get(e.name) or (owner.get(e.name, ("(ungrouped)",))[0] or "(ungrouped)")
            label = gkey
        groups[gkey].append(e.name)
        gkey_label[gkey] = label
    safe_of = _safe_filenames(gkey_label)
    out: dict[str, dict] = {}
    for gkey, names in groups.items():
        ranked = sorted(names, key=lambda n: (_TIER_RANK.get(tiers.get(n, "guessed"), 3),
                                              _EXEC_RANK.get(exec_status.get(n, ""), 1), n))
        primary = ranked[0]
        pg = (by_name[primary].goal or "").strip()
        if pg and not pg.upper().startswith("TODO"):
            first = pg.splitlines()[0].strip()
            purpose = first if len(first) <= 160 else first[:160].rsplit(" ", 1)[0] + "…"
        else:
            purpose = f"{len(names)} operation(s)"
        out[gkey] = {
            "label": gkey_label[gkey], "safe": safe_of[gkey],
            "primary": primary, "purpose": purpose,
            "kind": owner.get(primary, ("", "instance"))[1],
            "members": [{"name": n, "tier": tiers.get(n, "guessed"),
                         "exec": exec_status.get(n, "")} for n in ranked],
        }
    return out


def _class_context_body(entry, model: dict, name_to_gkey: dict, by_name: dict) -> str:
    """INDEX-FIRST audience context. Prepend the target API's catalogue class header
    — how to obtain the receiver + ONE verified/grounded sibling's real call pattern —
    to the API's own doc, so the audience model stops inventing the receiver / entry
    point (the ~53% `value X is not a member` / `not found: value` failure class the
    flat per-API body can't prevent). Pure/testable; returns entry.body unchanged when
    the class isn't in the model."""
    gkey = name_to_gkey.get(entry.name)
    m = model.get(gkey) if gkey else None
    if not m:
        return entry.body
    head = [f"## Class context — `{m['label']}`", f"_{m['purpose']}_", "",
            f"**Obtaining the receiver:** {_receiver_line(m['label'], m['kind'])}", ""]
    primary = m["primary"]
    if primary != entry.name:
        ptier = next((x["tier"] for x in m["members"] if x["name"] == primary), "guessed")
        if ptier in ("verified", "grounded") and primary in by_name:
            pat = _section_between(by_name[primary].body, "Valid Call Patterns")
            if pat:
                head += [f"**Proven setup from a {ptier} sibling `{primary}` — reuse its "
                         f"receiver/imports, then call `{entry.name}` instead:**", pat, ""]
    head += ["---", ""]
    return "\n".join(head) + "\n" + entry.body


def _receiver_line(cls: str, kind: str) -> str:
    return (f"static object — call `{cls}.<method>(...)`" if kind == "static"
            else f"instance — obtain a `{cls}` value, then `<value>.<method>(...)`")


def write_catalogue(cfg: AidealConfig) -> dict:
    """ADDITIVE, non-breaking: export the flat LLM_readme into the two-level shape
    (catalogue + per-class files) WITHOUT touching LLM_readme.md or the read path.

    Writes next to LLM_readme.md:
      - LLM_readme_index.md : one section per defining class -> purpose, receiver, and
                              the class's APIs with tier badges (primary marked),
                              each linking into api/<Class>.md.
      - api/<Class>.md      : the actual entries for that class's functions, headed by
                              the class purpose + how to obtain a receiver.

    Class files are named after the source class (the defining file's stem). Reuses
    the exact ranking `organize_report` computes; the rest of the pipeline keeps
    reading the flat file until the read path is switched deliberately (a later step)."""
    from .doc_checks import _owner_map
    entries = parse_readme(cfg.llm_readme)
    if not entries:
        return {"error": "no LLM_readme.md entries — run `aideal readme --generate` first"}
    tiers, class_of, _ = _grounding_tiers(cfg)
    exec_status = _exec_status_map(cfg)
    owner = _owner_map(cfg)
    file_of = {d["name"]: d["file"] for d in public_api_details(cfg)}
    model = _catalogue_model(entries, tiers, exec_status, class_of, owner, file_of=file_of)
    by_name = {e.name: e for e in entries}
    api_dir = cfg.llm_readme.parent / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    idx = [f"# {cfg.project_name} — API catalogue", "",
           f"{len(entries)} APIs across {len(model)} classes. Scan here, then open the one "
           "class file you need (each opens with how to obtain its receiver, then its methods).", "",
           "Legend: ★ verified · ✅ grounded · 🟡 sibling · ⚠️ guessed", ""]
    files = 0
    for gkey in sorted(model, key=lambda g: (model[g]["label"], g)):
        m = model[gkey]
        label, safe = m["label"], m["safe"]
        recv = _receiver_line(label, m["kind"])
        badged = [f"{_TIER_BADGE.get(x['tier'], '⚠️')} `{x['name']}`"
                  + (" **(primary)**" if x["name"] == m["primary"] else "") for x in m["members"]]
        # per-class file: header (purpose + receiver + members) then the real entries
        body = [f"# {label}", "", f"_{m['purpose']}_", "", f"**Receiver:** {recv}", "",
                "**Members** (most robust first): " + ", ".join(badged), "", "---", ""]
        for x in m["members"]:
            body.append(by_name[x["name"]].body.strip())
            body.append("")
        (api_dir / f"{safe}.md").write_text("\n".join(body), encoding="utf-8")
        files += 1
        # catalogue section
        idx += [f"## [{label}](api/{safe}.md)", f"_{m['purpose']}_",
                f"**Receiver:** {recv}", "**APIs:** " + ", ".join(badged), ""]
    idx_path = cfg.llm_readme.parent / "LLM_readme_index.md"
    idx_path.write_text("\n".join(idx), encoding="utf-8")
    return {"action": "catalogue", "classes": len(model), "apis": len(entries),
            "index": str(idx_path), "api_dir": str(api_dir), "class_files": files,
            "note": "additive export; LLM_readme.md and the read path are untouched"}
