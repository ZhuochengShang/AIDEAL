"""Grounded README generation, document distillation, and resumable authoring."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
    public_api_surface,
)
from .api_examples import (
    api_test_examples,
)
from .api_overloads import (
    _dedup_deprioritize,
    _subsume_overloads,
)
from .readme_format import (
    ApiEntry,
    _entry_skeleton,
    _section_between,
    parse_readme,
)


def distilled_readme_context(cfg: AidealConfig, *, refresh: bool = False) -> str:
    """Summarize the original README ONCE into a compact, reusable context note.

    Cached next to the LLM readme; reused across every entry generation so the
    full README isn't re-sent per API (efficient + accurate). Returns a
    'generate fresh' note when the project has no original README."""
    if not cfg.original_readme_files:
        return ("No original README exists for this project — generate documentation "
                "fresh from the signature and project profile only.")
    cache = cfg.llm_readme.parent / "original_readme_notes.md"
    newest = max(p.stat().st_mtime for p in cfg.original_readme_files)
    if cache.exists() and not refresh and cache.stat().st_mtime >= newest:
        return cache.read_text(encoding="utf-8")
    from .llm import invoke_text
    from .prompts import load as load_prompt
    raw = cfg.original_readme_text(limit=150000)  # all baseline docs, summarized once
    note = invoke_text(
        cfg.model_for_role("author"),
        *load_prompt(cfg, "aideal/readme_distill", original_readme=raw),
    ).strip()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(note, encoding="utf-8")
    return note


def _original_readme_snippets(cfg: AidealConfig, names, max_per_api: int = 2,
                              max_chars: int = 1400) -> dict[str, list[str]]:
    """Index VERBATIM code blocks from the ORIGINAL readme by the API name(s) they
    call. `distilled_readme_context` summarizes the docs ONCE and drops per-API
    snippets, so an entry never sees the project's REAL call form — e.g. the docs'
    instance-style `raster.mapPixels(f)` gets paraphrased into a non-compiling
    free-function `mapPixels(raster, f)`. Feeding the exact block back lets the
    author reproduce the true receiver/qualifier. Returns {name: [code blocks]}."""
    if not cfg.original_readme_files:
        return {}
    from collections import defaultdict
    raw = cfg.original_readme_text(limit=200000)
    # tolerant fence match: any info-string after ``` and REQUIRE the closing ```
    # to start its own line (\n```), so inline `code` / stray backticks in prose
    # don't desync the open/close pairing across the concatenated docs.
    blocks = re.findall(r"```[^\n]*\n(.*?)\n```", raw, re.DOTALL)
    idx: dict[str, list[str]] = defaultdict(list)
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        for name in names:
            if len(idx[name]) >= max_per_api:
                continue
            # a real call/use of the name: `name(`, `.name(`, `name[`
            if re.search(rf"(?:\b|\.){re.escape(name)}\s*[\(\[]", b):
                idx[name].append(b[:max_chars])
    return dict(idx)


def find_or_create(cfg: AidealConfig, generate: bool = False, max_generated: int = 10,
                   force: bool = False, resume: bool = False) -> dict:
    """Return status of the LLM readme; create a skeleton if missing.

    If the readme already exists it is returned as-is, UNLESS `force=True`
    (regenerate/overwrite) — use this to rerun `--generate` over an existing
    file instead of getting an instant "found" no-op."""
    if cfg.llm_readme.exists() and not force and not resume:
        entries = parse_readme(cfg.llm_readme)
        return {
            "action": "found",
            "path": str(cfg.llm_readme),
            "api_entries": len(entries),
            "apis": [e.name for e in entries],
            "note": "already exists; pass --force to regenerate/overwrite",
        }

    # group every definition site by name (overloads stay together), restricted
    # to the intended-API surface (cfg.surface_filter) so we document the real
    # API, not the raw regex surface.
    allowed = public_api_surface(cfg)
    by_name: dict[str, list[dict]] = {}
    for d in public_api_details(cfg):
        if d["visibility"] == "public" and d["name"] in allowed:
            by_name.setdefault(d["name"], []).append(d)
    surface = sorted(by_name)
    lang = cfg.language.lower()
    _intro = ("Generated skeleton — fill the TODOs." if not generate
              else "Generated from the API surface, project profile, and distilled docs.")
    header = f"# {cfg.project_name} — LLM_readme\n\nLLM-facing API documentation. {_intro}\n\n"
    targets = surface[:max_generated] if (generate and max_generated) else surface
    failures: list[dict] = []
    cfg.llm_readme.parent.mkdir(parents=True, exist_ok=True)

    if generate:
        # Durable generation identity. A partial README is safe to resume only
        # when its source/config/model inputs still match. This prevents an old
        # pilot (or a changed knowledge YAML) from being silently mixed into a
        # production all-API document.
        import hashlib as _hashlib
        import json as _json
        import os as _os
        import sys as _sysmod

        def _generation_files_hash(paths: list[Path], root: Path) -> dict:
            digest = _hashlib.sha256()
            files = sorted(set(p.resolve() for p in paths if p.is_file()), key=str)
            for path in files:
                try:
                    label = path.relative_to(root.resolve())
                except ValueError:
                    label = path
                digest.update(str(label).encode("utf-8"))
                digest.update(b"\0")
                digest.update(path.read_bytes())
                digest.update(b"\0")
            return {"sha256": digest.hexdigest(), "file_count": len(files)}

        _author = cfg.model_for_role("author")
        _source_files = [Path(p) for pattern in cfg.source_globs for p in
                         globmod.glob(str(cfg.root / pattern), recursive=True)]
        _profile_sub = cfg.raw.get("files", {}).get(
            "project_profile", "configs/project_profile.yaml")
        _profile_path = (cfg.root / _profile_sub).resolve()
        _engine_dir = Path(__file__).resolve().parent
        _engine_files = [_engine_dir / name for name in (
            "config.py", "llm.py", "profile.py", "prompts.py", "readme_agent.py",
            "readme_format.py",
            "readme_evidence.py",
            "readme_catalogue.py",
            "api_visibility.py",
            "api_examples.py",
            "scaffold_generation.py",
            "api_intent.py",
            "api_overloads.py",
            "api_signatures.py",
            "api_discovery.py",
            "readme_generation.py")]
        _generation_payload = {
            "schema": 2,
            "project": cfg.project_name,
            "language": cfg.language,
            "author": f"{_author.provider}:{_author.model}",
            "config": cfg.raw,
            "project_profile": _generation_files_hash([_profile_path], cfg.root),
            "source": _generation_files_hash(_source_files, cfg.root),
            "engine": _generation_files_hash(_engine_files, _engine_dir),
            "interpreter": {
                "executable": _os.path.realpath(_sysmod.executable),
                "version": _sysmod.version,
                "environment_sha256": _os.environ.get("AIDEAL_ENV_FINGERPRINT", ""),
            },
            "targets": targets,
            "definitions": {
                n: [r.get("signature", "") for r in by_name[n]] for n in targets
            },
            "original_document_sha256": _hashlib.sha256(
                cfg.original_readme_text(limit=None).encode("utf-8")
            ).hexdigest(),
        }
        generation_fingerprint = _hashlib.sha256(
            _json.dumps(_generation_payload, sort_keys=True, default=str,
                        ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        state_path = cfg.root / ".aideal_exec" / "readme_generation_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)

        existing_complete: dict[str, ApiEntry] = {}
        if resume:
            if not state_path.is_file():
                raise ValueError(
                    f"cannot resume README generation: missing state file {state_path}; "
                    "start a fresh run with --force")
            try:
                previous_state = _json.loads(state_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise ValueError(f"cannot resume README generation: invalid state: {exc}") from exc
            if previous_state.get("generation_fingerprint") != generation_fingerprint:
                raise ValueError(
                    "cannot resume README generation: source/config/model fingerprint changed; "
                    "start a fresh run with --force")
            existing_complete = {
                e.name: e for e in parse_readme(cfg.llm_readme)
                if e.name in targets and "TODO" not in e.body
            }
        resumed_entries = len(existing_complete)

        def _write_generation_state(*, complete: bool = False) -> None:
            state = {
                "generation_fingerprint": generation_fingerprint,
                "target_count": len(targets),
                "completed_count": len(existing_complete),
                "completed_apis": sorted(existing_complete),
                "complete": complete,
            }
            tmp = state_path.with_suffix(".json.tmp")
            tmp.write_text(_json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(state_path)

        _write_generation_state()
        # the readme is being (re)written -> invalidate readme-DERIVED caches so
        # io_hints / preamble rebuild from the NEW readme instead of a stale one.
        for _stale in ("io_hints.txt", "preamble.scala"):
            _p = cfg.llm_readme.parent / _stale
            if _p.exists():
                _p.unlink()
        import sys as _sys
        from .llm import invoke_text
        from .profile import require_profile
        from .prompts import load as load_prompt

        require_profile(cfg)  # generation is domain-aware: profile must be filled
        # distil the original README ONCE; reuse the note for every entry.
        # --force also re-distils (so prompt/cap changes take effect, since the
        # mtime-based cache wouldn't otherwise notice a prompt change).
        readme_ctx = distilled_readme_context(cfg, refresh=force)
        # index real usage from the existing test suite ONCE (ground-truth examples)
        test_index = api_test_examples(cfg)
        # ...and the VERBATIM per-API code blocks from the original readme, so the
        # entry can reproduce the project's real call form (which the distilled note
        # summarizes away) instead of paraphrasing it into a non-compiling shape.
        orig_snippet_index = _original_readme_snippets(cfg, set(by_name))
        # sibling grounding: map each API to its defining class and index which
        # classes have tested methods, so an API with NO direct test can borrow
        # the tested call pattern of a sibling on the same object/class.
        import os as _os
        from collections import defaultdict as _dd
        _class_of = {n: (_os.path.basename(r[0].get("file", ""))[:-6]
                         if r and r[0].get("file", "").endswith(".scala") else "")
                     for n, r in by_name.items()}
        _sibs_by_class = _dd(list)
        for _n, _exs in test_index.items():
            if _exs and _class_of.get(_n):
                _sibs_by_class[_class_of[_n]].append((_n, _exs))
        # Version B ("try first") toggle: comprehension.execute.probe_on_missing.
        # When on, a function with no test/sibling is RUN once before its entry is
        # written, so the author grounds on real execution instead of a blind guess.
        _probe_on_missing = bool(((cfg.comprehension or {}).get("execute", {}) or {}).get("probe_on_missing"))
        total = len(targets)
        # stream each entry to disk as it completes: progress is visible and a
        # crash mid-run keeps everything generated so far (resumable by hand).
        with cfg.llm_readme.open("w", encoding="utf-8") as fh:
            fh.write(header)
            for i, name in enumerate(targets, 1):
                if name in existing_complete:
                    fh.write(existing_complete[name].body.rstrip() + "\n\n")
                    fh.flush()
                    print(f"[{i}/{total}] {name} … RESUMED", file=_sys.stderr)
                    continue
                recs = by_name[name]
                # canonical = the maximal telescoping overload ("needed longest
                # parameters"): a same-file overload whose param types are a
                # prefix of a longer sibling's is the SAME function with
                # defaults — documented once via the longest signature and NOT
                # listed as a separate overload. Only genuinely distinct
                # signatures (different types / other receiver contexts)
                # remain in `overloads`.
                maximals, _subsumed = _subsume_overloads(recs, _dedup_deprioritize(cfg))
                primary = maximals[0]
                skeleton = _entry_skeleton(name, lang, recs)
                # Scaladoc usually sits on the SHORT base overload; if the
                # maximal form is undocumented, borrow the family's doc.
                _doc = primary["description"] or next(
                    (r["description"] for r in recs if r["description"].strip()), None)
                facts = {
                    "name": name,
                    "signature": primary["signature"] or name,
                    "params": primary["params"],           # [{name, type, default}]
                    "returns": primary["returns"] or None,
                    "source_doc": _doc,
                    "overloads": [r["signature"] for r in maximals[1:]][:5],
                }
                examples = test_index.get(name, [])
                if examples:
                    tests_text = "\n\n".join(
                        f"// from {e['file']} — test(\"{e['test']}\")\n{e['code']}" for e in examples)
                else:
                    # no direct test -> borrow the tested SIBLING pattern (same class)
                    _cls = _class_of.get(name, "")
                    _sibs = [(sn, se) for sn, se in _sibs_by_class.get(_cls, []) if sn != name][:2]
                    if _sibs:
                        _blocks = "\n\n".join(
                            f"// SIBLING `{sn}` on the same object/class `{_cls}` — mirror this call "
                            f"style (same receiver and argument order)\n// from {se[0]['file']}\n{se[0]['code']}"
                            for sn, se in _sibs)
                        tests_text = ("(no direct test for this API; use the tested SIBLING method(s) below "
                                      "as the authoritative call pattern)\n\n" + _blocks)
                    else:
                        tests_text = "(no existing test found for this API)"
                        # Version B: run the function once and ground the entry on
                        # the outcome (pass -> real call pattern; fail -> real error
                        # trace). Opt-in and fully guarded — a probe error keeps the
                        # default text so generation never breaks.
                        if _probe_on_missing:
                            try:
                                from .probe import run_probe, probe_grounding_block
                                _pr = run_probe(cfg, name, signature=primary["signature"] or "",
                                                params=primary["params"], returns=primary["returns"] or "")
                                if _pr.status in ("pass", "fail"):
                                    tests_text = probe_grounding_block(_pr, name)
                                print(f"    [probe] {name}: {_pr.status}", file=_sys.stderr)
                            except Exception as _pe:
                                print(f"    [probe] {name}: skipped ({type(_pe).__name__}: {_pe})", file=_sys.stderr)
                _orig = orig_snippet_index.get(name, [])
                orig_examples_text = ("\n\n".join(_orig) if _orig
                                      else "(no verbatim code example for this API in the original readme)")
                try:
                    entry = invoke_text(
                        cfg.model_for_role("author"),
                        *load_prompt(cfg, "aideal/readme_entry", api_name=name,
                                     api_facts=_json.dumps(facts, ensure_ascii=False, indent=2),
                                     original_readme_context=readme_ctx,
                                     original_examples=orig_examples_text,
                                     test_examples=tests_text,
                                     template=skeleton),
                    ).strip()
                    if (f"## API Test: `{name}`" not in entry or "TODO" in entry):
                        raise ValueError("author returned an incomplete or wrong-API entry")
                    status = "ok"
                except Exception as e:  # fell back to skeleton — record why, don't hide it
                    failures.append({"api": name, "error": f"{type(e).__name__}: {e}"})
                    entry = skeleton
                    status = "FALLBACK"
                fh.write(entry + "\n\n")
                fh.flush()
                if status == "ok":
                    existing_complete[name] = ApiEntry(
                        name=name,
                        goal=_section_between(entry, "Goal"),
                        snippet=_section_between(entry, "Prompt Snippet"),
                        body=entry,
                    )
                _write_generation_state()
                print(f"[{i}/{total}] {name} … {status}", file=_sys.stderr)
        _write_generation_state(complete=(len(existing_complete) == len(targets)))
        # eager: build the readme-DERIVED io_hints / preamble now (config value
        # `auto`), so the readme bundle ships complete and in sync. Best-effort —
        # failures here never block readme generation.
        try:
            from .doc_checks import _resolve_io_hints, _resolve_preamble, _execute_sample_data
            _ex = (cfg.comprehension or {}).get("execute", {}) or {}
            _auto = lambda k: str(_ex.get(k, "")).strip().lower() == "auto"
            if _auto("io_hints") or _auto("preamble"):
                _sd, _, _ = _execute_sample_data(cfg, _ex)
                if _auto("io_hints"):
                    _resolve_io_hints(cfg, _ex, _sd)
                if _auto("preamble"):
                    _resolve_preamble(cfg, _ex, _sd)
                print("[io_hints/preamble] regenerated from the new readme", file=_sys.stderr)
        except Exception:
            pass
    else:
        with cfg.llm_readme.open("w", encoding="utf-8") as fh:
            fh.write(header)
            for name in targets:
                fh.write(_entry_skeleton(name, lang, by_name[name]) + "\n\n")

    result = {
        "action": "created_skeleton" if not generate else "created_generated",
        "path": str(cfg.llm_readme),
        "api_entries": len(targets),
        "used_original_readme": [str(p.relative_to(cfg.root)) for p in cfg.original_readme_files],
        "note": "fill TODOs or rerun with --generate (uses the author model)",
    }
    if generate:
        result["generated_ok"] = len(existing_complete)
        result["resumed_entries"] = resumed_entries
        result["newly_generated"] = len(existing_complete) - resumed_entries
        result["fallback_to_skeleton"] = len(failures)
        result["generation_fingerprint"] = generation_fingerprint
        result["generation_state"] = str(state_path)
        if failures:
            result["failures"] = failures[:5]
            result["note"] = (f"{len(failures)}/{len(targets)} entries fell back to "
                              f"skeleton — see 'failures' for the error")
    return result
