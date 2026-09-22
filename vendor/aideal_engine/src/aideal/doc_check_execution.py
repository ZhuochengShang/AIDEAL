"""Native comprehension execution, bounded snippet repair, and checkpoint evidence.

This module preserves the historical native scoring and prompt protocol; it is
separate from the portable three-README evaluator in workflow/."""
from __future__ import annotations

import random
import re
from .config import AidealConfig
from .error_log import ErrorLog, new_run_id
from .execution import exclusive_work_dir
from .readme_agent import public_api_details, public_api_surface
from .doc_check_sources import _build_catalogue_context
from .doc_check_inputs import (
    _execute_sample_data, _fill_scaffold, _owner_map, _receiver_hint,
    _resolve_io_hints, _resolve_preamble, _strip_fences,
)
from .doc_check_errors import _classify_error, _codebase_frames
from .doc_check_provenance import (
    _checkpoint_row_reusable, _comprehension_fingerprint_components,
)


@exclusive_work_dir
def _comprehension_execute(cfg: AidealConfig, inventory, sample, seed, doc_source: str,
                           show_code: bool = False, class_context: bool = False,
                           max_fix_rounds: int | None = None,
                           resume: bool = False, timeout_s: int | None = None,
                           shared_doc: str | None = None,
                           doc_scope: str = "entry") -> dict:
    """Compile/run each API's audience snippet via the configured command.
    PASS = the program runs (success_marker present, exit 0). Real failures
    (compile/runtime) are logged with the actual error text.

    class_context: INDEX-FIRST — prefix each API's body with its catalogue class
    header (receiver + a verified sibling's real call pattern) so the snippet writer
    stops inventing the receiver/entry point. Complements the existing `{receiver}`
    TYPE hint with a proven, compiled example. Off -> bare per-API body (baseline)."""
    import os
    import shlex
    import subprocess
    import tempfile
    from pathlib import Path
    from .llm import invoke_text
    from .prompts import load as load_prompt

    from .llm import usage_snapshot, usage_delta
    import time as _time

    ex = cfg.comprehension.get("execute", {}) if cfg.comprehension else {}
    manifest_inventory_n = len(inventory)
    cmd_template = ex.get("command", "")
    scaffold_path = ex.get("scaffold", "")
    if not cmd_template or not scaffold_path:
        return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                "details": {"error": "configure comprehension.execute.{command,scaffold} in aideal.yaml"}}
    scaffold_file = (cfg.root / scaffold_path).resolve()
    if not scaffold_file.exists():
        return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                "details": {"error": f"scaffold not found: {scaffold_file}"}}
    scaffold = scaffold_file.read_text(encoding="utf-8", errors="ignore")
    region = ex.get("region", ["// TODO API_TEST_START", "// TODO API_TEST_END"])

    # Build the project's own uberjar ONCE, then run snippets against that single
    # jar (no hand-listed dependency jars). build runs in build_cwd; {uberjar}
    # in the command is replaced with the resolved jar path.
    import glob as _glob
    build_cwd = (cfg.root / ex.get("build_cwd", ".")).resolve()
    build_cmd = ex.get("build", "")
    build_info = None
    if build_cmd:
        try:
            bp = subprocess.run(shlex.split(build_cmd), cwd=build_cwd, capture_output=True,
                                text=True, timeout=int(ex.get("build_timeout_seconds", 1800) or 1800))
        except FileNotFoundError as e:
            return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                    "details": {"error": f"build tool not found ({e.filename}). Install Maven on "
                                "PATH, or set comprehension.execute.build: '' and point `uberjar` "
                                "at a prebuilt jar."}}
        except subprocess.TimeoutExpired:
            return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                    "details": {"error": "project build timed out"}}
        build_info = {"exit_code": bp.returncode, "stderr_tail": bp.stderr[-400:]}
        if bp.returncode != 0:
            return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                    "details": {"error": "project build failed", "build": build_info}}
    uberjar = ""
    uber_list: list[str] = []
    if ex.get("uberjar"):
        uber_list = sorted(_glob.glob(str(build_cwd / ex["uberjar"])))
        uberjar = uber_list[-1] if uber_list else ""
    # A glob of a prebuilt distribution's lib/*.jar — comma-joined as {jars}
    # (spark-submit --jars), colon-joined into {classpath} (scalac) below.
    jars = ""
    beast_jars_list: list[str] = []
    if ex.get("jars"):
        jg = str(ex["jars"])
        beast_jars_list = sorted(_glob.glob(jg if jg.startswith("/") else str(cfg.root / jg)))
        if not beast_jars_list:
            return {"check": "comprehension", "mode": "execute", "passed": False, "score": 0.0,
                    "details": {"error": f"no jars matched comprehension.execute.jars: {jg}"}}
        jars = ",".join(beast_jars_list)

    # {classpath} for scalac (COLON-separated): Spark jars + beast jars + the
    # uber jar (the uber carries JTS/GeoTools types so generated snippets that
    # reference them still compile). Runtime deps come from --packages.
    spark_jars: list[str] = []
    spark_jars_glob = ex.get("spark_jars", "")
    if spark_jars_glob:
        sjg = str(spark_jars_glob)
        spark_jars = sorted(_glob.glob(
            sjg if sjg.startswith("/") else str(cfg.root / sjg)))
        if not spark_jars:
            return {"check": "comprehension", "mode": "execute", "passed": False,
                    "score": 0.0, "details": {
                        "error": f"no Spark jars matched comprehension.execute.spark_jars: {sjg}"}}
    else:
        try:
            import pyspark as _pyspark
            _sj = os.path.join(os.path.dirname(_pyspark.__file__), "jars")
            spark_jars = sorted(_glob.glob(os.path.join(_sj, "*.jar")))
        except Exception:
            pass
    classpath = ":".join(beast_jars_list + spark_jars + uber_list)

    def _resolve(v):
        v = str(v)
        return str((cfg.root / v).resolve()) if (not v.startswith("/") and "/" in v) else v

    # Typed sample-data catalog: name -> resolved path. Each becomes a `val` in
    # the scaffold; the model picks the one(s) matching the API's param types.
    sample_data, available_inputs, sample_data_warnings = _execute_sample_data(cfg, ex)
    _lang = cfg.language.lower()
    _is_py = _lang == "python"
    _is_java = _lang == "java"
    bindings = "\n    ".join(
        (f'{k} = r"{p}"' if _is_py else
         f'String {k} = "{p}";' if _is_java else
         f'val {k} = "{p}"')
        for k, p in sample_data.items())
    # Option-2 isolation: a codebase-specific `preamble` pre-loads typed inputs
    # (e.g. rasterRDD, featuresRDD) right after the path vals, so a per-API test
    # writes ONLY the API call — I/O can no longer fail the test. The model is
    # then shown the pre-loaded typed vars instead of raw paths.
    preamble = _resolve_preamble(cfg, ex, sample_data)   # 'auto' -> LLM-generated, cached
    if preamble:
        _cmt = "#" if _is_py else "//"
        bindings += (f"\n\n    {_cmt} pre-loaded typed inputs (comprehension.execute.preamble)\n    "
                     + "\n    ".join(preamble.splitlines()))
        if _is_py:
            preloaded = re.findall(
                r"^\s*(\w+)\s*(?::\s*\w+)?\s*=\s*(?:.*?#\s*type:\s*(.+))?",
                preamble, re.M)
        elif _is_java:
            preloaded = [(name, typ) for typ, name in re.findall(
                r"^\s*(?:final\s+)?([\w.$<>?, \[\]]+)\s+(\w+)\s*=", preamble, re.M)]
        else:
            preloaded = re.findall(r"val\s+(\w+)\s*:\s*([^=]+?)\s*=", preamble)
        preloaded = [(n, (t or "(see preamble)").strip()) for n, t in preloaded if n]
        if preloaded:
            available_inputs = (
                "Pre-loaded and already in scope — use these directly, do NOT re-load:\n"
                + "\n".join(f"- {n}: {t.strip()}" for n, t in preloaded)
                + "\n(raw input path strings also in scope if needed: "
                + ", ".join(sample_data) + ")")
    # legacy {{KEY}} placeholders still supported
    placeholders = {k: _resolve(v) for k, v in (ex.get("placeholders", {}) or {}).items()}
    success_marker = ex.get("success_marker", "")
    error_marker = ex.get("error_marker", "")
    # Phase-A correctness gate: when require_correctness is on, a run only PASSES if
    # it emitted the structured witness (check_marker) — i.e. the snippet actually
    # ran the require(...) correctness assertion and produced a non-degenerate
    # result. Catches a wrong pixel TYPE that reads garbage without throwing, which
    # a plain "it ran" (success_marker) check would let through. Default off.
    check_marker = ex.get("check_marker", "__CHECK__")
    require_correctness = bool(ex.get("require_correctness", False))
    timeout = int(timeout_s or ex.get("timeout_seconds", 600) or 600)
    strip_snippet_imports = bool(ex.get("strip_snippet_imports", False))
    output_tail_chars = int(ex.get("output_tail_chars", 2000) or 2000)
    if max_fix_rounds is None:                                # CLI/bench override wins
        max_fix_rounds = int(ex.get("max_fix_rounds", 3) or 0)   # default 3 fixes (4 attempts)
    # stuck detector: N CONSECUTIVE identical errors -> stop this API's loop.
    # Evidence (g4 fix-all, gemini-2.5-pro, 2026-07-07): every fixable API
    # fixed within 12 rounds; unfixable ones repeated the SAME compile error
    # to the 100-round cap (addTile: 368K output tokens on one API). 0 disables.
    stuck_repeats = int(ex.get("stuck_repeats", 3) or 0)
    work_dir = (cfg.root / ex.get("work_dir", ".aideal_exec")).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    # A resume checkpoint is valid only for the exact experimental treatment.
    # Hash both the ordered denominator and the delivered document so A2 rows
    # can never leak into a repaired B2 run merely because both say "aideal".
    import hashlib as _hashlib
    import json as _json
    from .experiment_identity import digest_native, write_run_identity
    _manifest_payload = "\n".join(e.name for e in inventory).encode("utf-8")
    manifest_sha256 = _hashlib.sha256(_manifest_payload).hexdigest()
    _doc_payload = (shared_doc if shared_doc is not None else
                    "\n\0\n".join(f"{e.name}\n{e.body}" for e in inventory))
    doc_sha256 = _hashlib.sha256(_doc_payload.encode("utf-8")).hexdigest()
    fingerprint_components = _comprehension_fingerprint_components(
        cfg, ex=ex, doc_source=doc_source, doc_scope=doc_scope,
        max_fix_rounds=max_fix_rounds, manifest_sha256=manifest_sha256,
        document_sha256=doc_sha256, scaffold_file=scaffold_file,
        sample_data=sample_data, class_context=class_context, timeout=timeout)
    experiment_fingerprint = digest_native(fingerprint_components)

    # Crash-proof progress: one JSONL row per finished API, flushed as it
    # completes. A killed/crashed full run loses NOTHING: rerun with --resume
    # and already-finished APIs are skipped and pre-filled into the results
    # (the 2026-07-01 all-API run died ~120/218 in and lost every result).
    # Without --resume the checkpoint restarts with the run.
    ckpt = work_dir / "comprehension_progress.jsonl"
    from .checkpoint_compatibility import load_compatibility
    write_run_identity(work_dir / "run_identity.json", fingerprint_components)
    reuse = load_compatibility(ckpt, fingerprint_components) if resume else {}
    legacy_fingerprint = reuse.get("legacy_fingerprint")
    done_rows: dict[str, dict] = {}
    if resume and ckpt.exists():
        for line in ckpt.read_text(encoding="utf-8").splitlines():
            try:
                row = _json.loads(line)
                # Provider/network failures are transient evidence, not a
                # completed API. An overnight restart must retry them instead
                # of silently preserving a quota outage in the final table.
                if (_checkpoint_row_reusable(row, experiment_fingerprint)
                        or (legacy_fingerprint and
                            _checkpoint_row_reusable(row, legacy_fingerprint))):
                    # Native current evidence takes precedence over legacy
                    # rows even when both versions append to the same journal.
                    previous = done_rows.get(row["name"], {})
                    if (previous.get("experiment_fingerprint") == experiment_fingerprint
                            and row.get("experiment_fingerprint") != experiment_fingerprint):
                        continue
                    done_rows[row["name"]] = row
            except Exception:
                continue
    elif ckpt.exists():
        try:
            ckpt.unlink()
        except OSError:          # e.g. cross-mount permission mismatch —
            try:                 # truncating is just as good as deleting
                ckpt.write_text("")
            except OSError:
                pass             # worst case: stale rows only matter under --resume

    # Scope execution to user-facing, runnable APIs. Most of the public surface
    # is internal/utility defs (close, copy, compareTo, hasNext, ...) that aren't
    # standalone-runnable — completeness covers all of them; execution shouldn't.
    include = set(ex.get("include", []) or [])
    exclude = set(ex.get("exclude", []) or [])
    # Reproducible alternative to a hand-list: select by DEFINING CLASS. User-
    # facing ops live in entrypoint classes (the SparkContext/RasterRDD mixin and
    # the operation objects); internal helpers live in tile/reader/serializer
    # classes. Derived from the `file` of each API — no manual judgment.
    entry_classes = set(ex.get("entrypoint_classes", []) or [])
    if entry_classes and not include:
        import os as _os
        include = {d["name"] for d in public_api_details(cfg)
                   if d["visibility"] == "public"
                   and _os.path.basename(d["file"])[:-6] in entry_classes}
    if include:
        inventory = [e for e in inventory if e.name in include]
    if exclude:
        inventory = [e for e in inventory if e.name not in exclude]
    if sample and sample < len(inventory):
        inventory = random.Random(seed).sample(inventory, sample)
    import sys as _count_sys
    _count_sys.stderr.write(
        f"[comprehension] APIs to execute: {len(inventory)} of "
        f"{manifest_inventory_n} (doc_source={doc_source}, doc_scope={doc_scope})\n"
    )
    _count_sys.stderr.flush()

    io_hints_text = _resolve_io_hints(cfg, ex, sample_data)   # 'auto' -> LLM-generated, cached

    # Build the Ivy --packages / --repositories flags from list config so the
    # generic spark-submit command can live in the scala-spark adapter and a
    # project only supplies its `packages:`/`repositories:` lists (empty -> the
    # flag disappears entirely).
    pkgs = ex.get("packages") or []
    repos = ex.get("repositories") or []
    packages_flag = ("--packages " + ",".join(pkgs)) if pkgs else ""
    repositories_flag = ("--repositories " + ",".join(repos)) if repos else ""

    log = ErrorLog(cfg.error_log)
    run_id = new_run_id()
    task = f"comprehension_exec_{doc_source}"
    per_api: dict[str, object] = {}
    passed_n = 0
    infra_n = 0            # runs that failed only on a missing dependency (infra);
                           # excluded from the doc-quality denominator in the result
    # receiver typing: the flat doc renders `value.method`; hand the snippet-writer
    # the DEFINING type per function so it calls the method on the right receiver.
    owner_map = _owner_map(cfg)
    # INDEX-FIRST: build the catalogue model once; prefix each body with its class
    # header (receiver + a verified sibling's proven call pattern). Off -> bare body.
    from .readme_agent import _class_context_body
    if shared_doc is not None:
        # FULL-DOCUMENT mode (2x2 experiment): every audience attempt receives
        # the ENTIRE selected documentation; only the target line differs.
        # No truncation — exposure is total and identical across the manifest.
        import sys as _s
        _s.stderr.write(f"[full-doc] audience context = {len(shared_doc):,} chars "
                        f"per API x {len(inventory)} APIs "
                        f"(~{len(shared_doc) // 4:,} tokens/call)\n")
        body_for = (lambda e: shared_doc
                    + f"\n\n===== TARGET =====\nWrite a snippet that calls `{e.name}`.")
        ctx = None
    else:
        ctx = _build_catalogue_context(cfg) if class_context else None
        body_for = (lambda e: _class_context_body(e, *ctx)) if ctx else (lambda e: e.body)
    # source attribution: which codebase definition each tested name targets
    # (canonical site = same election as `aideal dedup`), plus a basename→path
    # index so runtime stack frames can be mapped back to repo source lines.
    from .readme_agent import _subsume_overloads, _dedup_deprioritize
    import glob as _globmod
    _pub_details = [d for d in public_api_details(cfg) if d["visibility"] == "public"]
    _by_name_det: dict[str, list] = {}
    for _d in _pub_details:
        _by_name_det.setdefault(_d["name"], []).append(_d)
    _depri = _dedup_deprioritize(cfg)
    site_of: dict[str, dict] = {}
    for _n, _recs in _by_name_det.items():
        _mx, _ = _subsume_overloads(_recs, _depri)
        site_of[_n] = {"source": f"{_mx[0]['file']}:{_mx[0]['line']}",
                       "other_sites": len(_recs) - 1}
    file_index: dict[str, str] = {}
    for _g in list(cfg.source_globs) + [g.replace(".scala", ".java")
                                        for g in cfg.source_globs]:
        for _p in _globmod.glob(str(cfg.root / _g), recursive=True):
            file_index.setdefault(os.path.basename(_p),
                                  str(Path(_p).relative_to(cfg.root)))

    # micro-benchmark accounting (per API and per run): wall time + provider-
    # reported tokens + which model wrote/fixed. `fixer` role (fallback:
    # audience) handles attempts >0 — map `roles: fixer` (or CLI --role
    # fixer=google:gemini-2.5-pro) to benchmark a different fixer model.
    metrics: dict[str, dict] = {}
    run_t0 = _time.time()
    run_u0 = usage_snapshot()
    writer_spec = cfg.model_for_role("audience")
    fixer_spec = cfg.model_for_role("fixer")
    for entry in inventory:
        if entry.name in done_rows:      # --resume: finished in a previous run
            row = done_rows[entry.name]
            metrics[entry.name] = {k: row.get(k) for k in (
                "status", "attempts", "pass_round", "wall_s", "llm_calls",
                "input_tokens", "output_tokens", "by_model", "error_category",
                "error", "locus", "doc_chars", "document_sha256", "source",
                "source_other_sites", "codebase_frames", "rendered_prompt_sha256")}
            metrics[entry.name]["evidence_fingerprint"] = row.get("experiment_fingerprint")
            per_api[entry.name] = row.get("execution_evidence") or f"resumed: {row.get('status')}"
            if row.get("status") == "pass":
                passed_n += 1
            if row.get("error_category") == "infra":
                infra_n += 1
            continue
        api_t0 = _time.time()
        api_u0 = usage_snapshot()
        work_api = work_dir / f"run_{entry.name}"
        (work_api / "classes").mkdir(parents=True, exist_ok=True)
        scala_file = work_api / str(ex.get("test_filename", "ApiTest.scala"))
        cmd = (cmd_template.replace("{scala_file}", str(scala_file))
               .replace("{test_file}", str(scala_file))
               .replace("{root}", str(cfg.root))
               .replace("{uberjar}", uberjar).replace("{jars}", jars)
               .replace("{classpath}", classpath).replace("{work}", str(work_api))
               .replace("{packages}", packages_flag)
               .replace("{repositories}", repositories_flag))

        ran = False
        last = {}
        last_run = {"stdout": "", "stderr": "", "exit_code": None}
        rounds_trace: list[dict] = []
        prompt_hashes = []
        prev_sig, same_sig = None, 0   # stuck detector state (per API)
        import sys as _sys
        receiver = _receiver_hint(entry.name, owner_map)
        for attempt in range(1 + max_fix_rounds):
            # A condition's first attempt must be documentation-only. Historical
            # error-log feedback would leak earlier treatments into A1/A2 even
            # with max_fix_rounds=0. Only an actual retry may see failures.
            known = [] if attempt == 0 else log.failures_for(entry.name)
            try:
                delivered_prompt = load_prompt(cfg, "aideal/comprehension_write_exec",
                                 api_body=body_for(entry), api_name=entry.name,
                                 available_inputs=available_inputs,
                                 receiver=receiver or "(receiver type not resolved)",
                                 known_failures=known or "(none yet)",
                                 execution_context=ex.get("execution_context", ""),
                                 exec_hints=ex.get("exec_hints", ""),
                                 io_hints=io_hints_text)
                prompt_hashes.append(_hashlib.sha256(_json.dumps(delivered_prompt).encode()).hexdigest())
                snippet = _strip_fences(invoke_text(
                    writer_spec if attempt == 0 else fixer_spec, *delivered_prompt),
                    strip_imports=strip_snippet_imports)
            except Exception as llm_exc:
                # provider error (quota/network/bad model id) must not kill a
                # 200-API run — record it as this API's failure and move on.
                cat = "llm-error"
                msg = f"{type(llm_exc).__name__}: {llm_exc}"
                last = {"cat": cat, "msg": msg, "locus": "", "code": ""}
                rounds_trace.append({"round": attempt, "status": "fail",
                                     "category": cat, "error": msg[:160]})
                _sys.stderr.write(f"  [{entry.name}] round {attempt}: FAIL [{cat}] {msg[:90]}\n")
                _sys.stderr.flush()
                log.append(run_id=run_id, step="readme-exec-test", language=cfg.language,
                           task=task, status="fail", function=entry.name,
                           error_category=cat, error=msg[:500], round=attempt)
                break
            scala = _fill_scaffold(scaffold.replace("// AIDEAL_DATA_BINDINGS", bindings)
                                   .replace("# AIDEAL_DATA_BINDINGS", bindings),
                                   snippet, region, placeholders)
            scala_file.write_text(scala, encoding="utf-8")
            try:
                # shell=True so the `scalac && jar && spark-submit` pipeline runs
                from .execution import run_command
                proc = run_command(cmd, cwd=work_dir, timeout=timeout, env=dict(os.environ))
                out, err_out, rc = proc.stdout, proc.stderr, proc.returncode
            except subprocess.TimeoutExpired as e:
                # TimeoutExpired carries the captured streams as BYTES even with
                # text=True — concatenating raw killed the 2026-07-01 full run
                # ("can't concat str to bytes" at plotImage, ~120 APIs in).
                def _txt(b):
                    return b.decode("utf-8", "ignore") if isinstance(b, (bytes, bytearray)) else (b or "")
                out, err_out, rc = _txt(e.stdout), _txt(e.stderr) + "\n[timeout]", 124
            last_run = {"stdout": out or "", "stderr": err_out or "", "exit_code": rc}
            merged = (out or "") + "\n" + (err_out or "")
            ran = (rc == 0) and (success_marker in merged if success_marker else True) \
                and not (error_marker and error_marker in merged) \
                and (check_marker in merged if require_correctness else True)
            if ran:
                rounds_trace.append({"round": attempt, "status": "pass"})
                _sys.stderr.write(f"  [{entry.name}] round {attempt}: PASS\n"); _sys.stderr.flush()
                # record the PASSING snippet: a compiled-and-ran example is the
                # strongest grounding -> `aideal augment` folds it into the entry.
                log.append(run_id=run_id, step="readme-exec-test", language=cfg.language,
                           task=task, status="pass", function=entry.name,
                           code=snippet.strip()[:1500], round=attempt)
                # if this took a retry, also log the fix (error -> working code)
                if attempt > 0 and last:
                    log.append(run_id=run_id, step="readme-exec-test", language=cfg.language,
                               task=task, status="fixed", function=entry.name,
                               error_category=last.get("cat", ""), error=last.get("msg", ""),
                               root_cause=last.get("locus", ""), code=last.get("code", ""),
                               suggested_fix_code=snippet.strip()[:1000], round=attempt)
                break
            cat, msg, locus = _classify_error(merged, rc, error_marker,
                                              language=cfg.language)
            # coarse cat (compile/runtime/timeout) drives metrics/report; the shared
            # FIX_GUIDE adds a FINER, actionable hint (e.g. type-mismatch -> "pick the
            # geoTiff[T] that matches the raster"). Stored so failures_for replays it
            # into the next round, the same way the demo agent converges.
            from .fix_guide import classify as _classify_fix
            _, fix_hint = _classify_fix(merged)
            # ran clean but omitted the correctness witness -> tell the model exactly
            # what's missing instead of a vague "unknown" (Phase-A gate).
            if (require_correctness and rc == 0 and check_marker not in merged
                    and not (error_marker and error_marker in merged)):
                cat = "no-correctness-check"
                msg = (f"ran without a correctness check: no '{check_marker}' witness printed. "
                       f"End the snippet with require(<result non-degenerate>, ...) then "
                       f"println(\"{check_marker} {entry.name} \" + <witness>).")
                fix_hint = msg
            frames = _codebase_frames(merged, file_index)
            last = {"cat": cat, "msg": msg, "locus": locus,
                    "code": snippet.strip()[:1000], "frames": frames}
            rounds_trace.append({"round": attempt, "status": "fail", "category": cat,
                                 "error": msg[:160],
                                 **({"codebase_frames": frames} if frames else {})})
            _sys.stderr.write(f"  [{entry.name}] round {attempt}: FAIL [{cat}] {msg[:90]}\n"); _sys.stderr.flush()
            log.append(run_id=run_id, step="readme-exec-test", language=cfg.language,
                       task=task, status="fail", function=entry.name,
                       error_category=cat, error=msg, root_cause=locus,
                       code=snippet.strip()[:1000], suggested_fix_code=fix_hint,
                       round=attempt)
            # infra (missing jar) won't be fixed by rewriting the snippet — stop
            # retrying and don't spam the log with identical dependency failures.
            if cat == "infra":
                break
            sig = (cat, (msg or "")[:120])
            same_sig = same_sig + 1 if sig == prev_sig else 1
            prev_sig = sig
            if stuck_repeats and same_sig >= stuck_repeats:
                rounds_trace.append({"round": attempt, "status": "stuck-stop",
                                     "note": f"same error {same_sig}x consecutively"})
                _sys.stderr.write(f"  [{entry.name}] STUCK: same error {same_sig}x — "
                                  f"stopping fix loop\n"); _sys.stderr.flush()
                break
        if ran:
            passed_n += 1
            status = "pass" if not last else "pass (after fix)"
            per_api[entry.name] = (
                {"status": status, "rounds": rounds_trace, "code": snippet.strip(),
                 "scala_file": str(scala_file), "exit_code": last_run["exit_code"],
                 "stdout_tail": last_run["stdout"][-output_tail_chars:],
                 "stderr_tail": last_run["stderr"][-output_tail_chars:]}
                if show_code else
                ({"status": status, "rounds": rounds_trace} if len(rounds_trace) > 1 else status)
            )
        else:
            status = f"fail [{last.get('cat','?')}]: {last.get('msg','')[:140]}"
            if last.get("cat") == "infra":
                infra_n += 1
            per_api[entry.name] = (
                {"status": "fail", "rounds": rounds_trace, "error_category": last.get("cat", ""),
                 "error": last.get("msg", ""), "code": last.get("code", ""),
                 "scala_file": str(scala_file), "exit_code": last_run["exit_code"],
                 "stdout_tail": last_run["stdout"][-output_tail_chars:],
                 "stderr_tail": last_run["stderr"][-output_tail_chars:]}
                if show_code else
                ({"status": status, "rounds": rounds_trace} if len(rounds_trace) > 1 else status)
            )
        u = usage_delta(api_u0)
        metrics[entry.name] = {
            "status": "pass" if ran else "fail",
            "attempts": len(rounds_trace),
            "rendered_prompt_sha256": prompt_hashes,
            "pass_round": next((r["round"] for r in rounds_trace
                                if r["status"] == "pass"), None),
            "wall_s": round(_time.time() - api_t0, 1),
            "llm_calls": u["calls"],
            "input_tokens": u["input_tokens"],
            "output_tokens": u["output_tokens"],
            "by_model": u["by_model"],
            "error_category": None if ran else last.get("cat", ""),
            "error": None if ran else last.get("msg", ""),
            "locus": None if ran else last.get("locus", ""),
            "doc_chars": len(shared_doc if shared_doc is not None else entry.body),
            "document_sha256": _hashlib.sha256(
                (shared_doc if shared_doc is not None else entry.body).encode("utf-8")
            ).hexdigest(),
            # which RDPro definition this API targets (canonical file:line,
            # same election as `aideal dedup`) …
            "source": site_of.get(entry.name, {}).get("source"),
            "source_other_sites": site_of.get(entry.name, {}).get("other_sites"),
            # … and which codebase lines the run actually REACHED (JVM stack
            # frames from the last failing round; empty for compile failures
            # — those never enter rdpro code; None for passes — no trace).
            "codebase_frames": (last.get("frames") or None) if not ran else None,
        }
        with ckpt.open("a", encoding="utf-8") as _ck:   # flush per API — crash-safe
            _ck.write(_json.dumps({"name": entry.name, "doc_source": doc_source,
                                   "experiment_fingerprint": experiment_fingerprint,
                                   "execution_evidence": per_api[entry.name],
                                   **metrics[entry.name]}, ensure_ascii=False) + "\n")
    n = len(inventory)
    # Doc-quality denominator excludes infra-only failures (missing-dependency runs
    # are environment noise, not documentation failures — see _classify_error). The
    # raw pass/n is kept as `score_with_infra` for transparency.
    scored_n = n - infra_n
    # Report all three denominators explicitly (no ambiguity):
    #   raw_surface       = every visible public def (regex surface)
    #   intended_surface  = surface_filter set (what gets documented)
    #   executed          = the runnable subset actually compiled/run here
    raw = public_api_surface(cfg, override_filter="all")
    intended = public_api_surface(cfg)
    covered = {e.name for e in inventory}
    return {
        "check": "comprehension",
        "mode": "execute",
        "doc_source": doc_source,
        "run": {   # micro-benchmark header: everything a condition needs to be comparable
            "run_id": run_id,
            "api_count": n,
            "manifest_api_count": manifest_inventory_n,
            "models": {"audience": f"{writer_spec.provider}:{writer_spec.model}",
                       "fixer": f"{fixer_spec.provider}:{fixer_spec.model}"},
            "max_fix_rounds": max_fix_rounds,
            "class_context": bool(class_context),
            "timeout_s": timeout,
            "wall_s": round(_time.time() - run_t0, 1),
            "usage": usage_delta(run_u0),
            "checkpoint": str(ckpt),
            "resumed_apis": len([k for k in done_rows if k in metrics]),
            "manifest_sha256": manifest_sha256,
            "document_sha256": doc_sha256,
            "experiment_fingerprint": experiment_fingerprint,
            "fingerprint_components": fingerprint_components,
            "checkpoint_reuse": reuse,
            "doc_scope": doc_scope,
        },
        "passed": bool(scored_n) and passed_n == scored_n,
        "score": round(passed_n / scored_n, 3) if scored_n else 0.0,
        "score_with_infra": round(passed_n / n, 3) if n else 0.0,
        "infra_excluded": infra_n,
        "coverage": {
            "raw_surface": len(raw),
            "intended_surface": len(intended),
            "surface_filter": cfg.surface_filter,
            "executed": n,
            "scored": scored_n,
            "infra_excluded": infra_n,
            "untested_intended": sorted(intended - covered)[:20],
        },
        # surfaced (not fatal): typed inputs whose path is missing or the wrong type.
        # A non-empty list here usually explains a run of runtime I/O failures.
        "sample_data_warnings": sample_data_warnings,
        "metrics": metrics,   # per-API: status, attempts, pass_round, wall_s, tokens, by_model
        "details": per_api,
    }
