"""probe.py — Version B: execution-FIRST grounding ("try first").

Version A (`readme_agent.find_or_create`) grounds a doc entry on STATIC evidence —
an existing test, the original README, or a tested sibling method — and only THEN
asks the author model for text. For a function with none of those three, the
fallback is the literal string `"(no existing test found for this API)"`, and the
author writes the entire entry (Goal, Valid Call Patterns, everything) from the
signature alone. Nothing runs before that text is written, so the "guessed" tier
is a blind guess until a later `comprehension --execute` + `augment_from_log`
pass happens to catch up.

Version B closes that gap by RUNNING the function first. Given only its signature,
it picks type-matched sample inputs, synthesizes a call, compiles + runs it through
the SAME scaffold/command the comprehension harness already uses, and returns the
outcome:
  - PASS -> the compiled-and-ran snippet becomes an authoritative call pattern,
            fed into the `readme_entry` prompt exactly like a `test_examples` block.
  - FAIL -> the real compiler/runtime trace becomes negative grounding — still
            evidence, still better than a blind guess.

Prior art this mirrors (see readme_gen_A_vs_B.md):
  * Randoop (feedback-directed random testing) — try a call, keep it if it runs.
  * ChatTester / TestART (LLM test-gen with execution repair) — regenerate from
    the compiler error, up to `max_fix_rounds`.
  * TODO(next): Daikon-style invariant capture over the observed inputs/outputs so
    a PASS records "here is the contract it obeyed", not just "it ran".

Design note: this module is deliberately ISOLATED. It reuses the standalone
helpers in `doc_checks`/`readme_agent` but does NOT touch `_comprehension_execute`,
so enabling Version B cannot regress Version A. The jar/classpath resolution here
mirrors `_comprehension_execute`'s setup; TODO: factor that setup into one shared
`resolve_exec_context` and call it from both.

Enable the hook with `comprehension.execute.probe_on_missing: true` in aideal.yaml.
"""

from __future__ import annotations

import glob as _glob
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .config import AidealConfig
from .error_log import ErrorLog, git_version, new_run_id


@dataclass
class ProbeResult:
    name: str
    status: str                      # "pass" | "fail" | "skipped" | "dry-run"
    snippet: str = ""                # the call body that was tried
    witness: str = ""                # the __CHECK__ line / stdout evidence on pass
    error_category: str = ""
    error: str = ""
    rounds: list[dict] = field(default_factory=list)
    scala_file: str = ""             # the assembled ApiTest.scala (for inspection)
    command: str = ""                # the exact compile+run command
    input_var: str = ""              # the type-matched sample input chosen


# ---------------------------------------------------------------------------
# Type-matched input selection — the seed of the type-compatibility idea.
# Sample-data keys are typed by convention (raster_tif, vector_geojson,
# table_csv, ...); pick the key whose kind matches what the signature reads.
# ---------------------------------------------------------------------------
_TYPE_HINTS = [
    (re.compile(r"raster|tile|pixel|geotiff|\btif\b", re.I), "raster"),
    (re.compile(r"feature|geometry|vector|spatial|point|polygon|linestring", re.I), "vector"),
    (re.compile(r"dataframe|dataset|\brow\b|table|column", re.I), "table"),
]


def _kind_for_signature(signature: str, params, returns: str) -> str | None:
    blob = " ".join([signature or "", returns or "",
                     " ".join((p.get("type", "") or "") for p in (params or []))])
    for rx, kind in _TYPE_HINTS:
        if rx.search(blob):
            return kind
    return None


def _pick_input(sample_data: dict, signature: str, params, returns: str) -> str:
    """Return the sample_data KEY whose kind best matches the signature, else the
    first non-output input. `raster_tif` -> kind `raster`, etc."""
    kind = _kind_for_signature(signature, params, returns)
    if kind:
        for key in sample_data:
            if key == "output_dir":
                continue
            if key.split("_")[0] == kind:
                return key
    for key in sample_data:               # fallback: first real input
        if key != "output_dir":
            return key
    return ""


# ---------------------------------------------------------------------------
# Execution context — mirrors _comprehension_execute's setup (jars/classpath/
# scaffold/sample-data/bindings/command). Reused, not re-derived per call.
# ---------------------------------------------------------------------------
def resolve_exec_context(cfg: AidealConfig) -> dict:
    from .doc_checks import _execute_sample_data
    from .readme_agent import generate_scaffold

    ex = (cfg.comprehension or {}).get("execute", {}) if cfg.comprehension else {}
    # scaffold: a configured file if present, else auto-derive from the API surface
    scaffold_path = ex.get("scaffold", "")
    scaffold_file = (cfg.root / scaffold_path).resolve() if scaffold_path else None
    if scaffold_file and scaffold_file.exists():
        scaffold = scaffold_file.read_text(encoding="utf-8", errors="ignore")
    else:
        scaffold = generate_scaffold(cfg)

    # uberjar (built once, if configured) + beast jars + spark jars -> classpath
    build_cwd = (cfg.root / ex.get("build_cwd", ".")).resolve()
    uber_list: list[str] = []
    if ex.get("uberjar"):
        uber_list = sorted(_glob.glob(str(build_cwd / ex["uberjar"])))
    uberjar = uber_list[-1] if uber_list else ""
    beast_jars: list[str] = []
    if ex.get("jars"):
        jg = str(ex["jars"])
        beast_jars = sorted(_glob.glob(jg if jg.startswith("/") else str(cfg.root / jg)))
    spark_jars: list[str] = []
    try:
        import pyspark as _pyspark
        spark_jars = sorted(_glob.glob(os.path.join(os.path.dirname(_pyspark.__file__), "jars", "*.jar")))
    except Exception:
        pass
    classpath = ":".join(beast_jars + spark_jars + uber_list)
    jars = ",".join(beast_jars)

    sample_data, available_inputs, _warn = _execute_sample_data(cfg, ex)
    bindings = "\n    ".join(f'val {k} = "{p}"' for k, p in sample_data.items())

    pkgs = ex.get("packages") or []
    repos = ex.get("repositories") or []
    return {
        "ex": ex,
        "scaffold": scaffold,
        "region": ex.get("region", ["// TODO API_TEST_START", "// TODO API_TEST_END"]),
        "classpath": classpath, "jars": jars, "uberjar": uberjar,
        "packages_flag": ("--packages " + ",".join(pkgs)) if pkgs else "",
        "repositories_flag": ("--repositories " + ",".join(repos)) if repos else "",
        "sample_data": sample_data, "available_inputs": available_inputs, "bindings": bindings,
        "success_marker": ex.get("success_marker", ""),
        "error_marker": ex.get("error_marker", ""),
        "check_marker": ex.get("check_marker", "__CHECK__"),
        "require_correctness": bool(ex.get("require_correctness", False)),
        "timeout": int(ex.get("timeout_seconds", 600) or 600),
        "work_dir": (cfg.root / ex.get("work_dir", ".aideal_exec")).resolve(),
        "command": ex.get("command", ""),
    }


def _template_probe_snippet(name: str, params, returns: str, input_var: str, check_marker: str) -> str:
    """No-LLM best-effort probe body (for offline/dry-run). Heuristic call shape:
    an `sc.<name>` loader vs. an instance method `<input>.<name>`. Clearly marked
    as unverified — the LLM path (probe_write.md) produces the real snippet."""
    ret = (returns or "").lower()
    loaderish = bool(re.search(r"rdd|dataset|dataframe", ret)) and not params
    call = (f"sc.{name}({input_var})" if loaderish
            else f"val __src = {input_var}\n    // best-effort: adjust receiver/args from the real signature\n    __src.{name}()")
    return (f"// [Version B — template probe, UNVERIFIED shape] type-matched input: {input_var}\n"
            f"    val __res = {call}\n"
            f"    val __n = __res.count()\n"
            f"    require(__n >= 0, \"empty result for {name}\")\n"
            f"    println(\"{check_marker} {name} \" + __n)")


def _llm_probe_snippet(cfg: AidealConfig, name: str, signature: str, params, returns: str,
                       available_inputs: str, known_failures: str, ctx: dict) -> str:
    from .llm import invoke_text
    from .prompts import load as load_prompt
    from .doc_checks import _strip_fences
    ex = ctx["ex"]
    pstr = "; ".join(f"{p.get('name','?')}: {p.get('type','?')}" for p in (params or [])) or "(none)"
    system, user = load_prompt(cfg, "aideal/probe_write",
                               api_name=name, signature=signature or name,
                               params=pstr, returns=returns or "(unspecified)",
                               available_inputs=available_inputs,
                               known_failures=known_failures or "(none yet)",
                               execution_context=ex.get("execution_context", ""),
                               exec_hints=ex.get("exec_hints", ""),
                               io_hints="")
    raw = invoke_text(cfg.model_for_role("audience"), system, user)
    return _strip_fences(raw, strip_imports=bool(ex.get("strip_snippet_imports", False)))


def run_probe(cfg: AidealConfig, name: str, *, signature: str = "", params=None, returns: str = "",
              dry_run: bool = False, use_llm: bool = True, max_fix_rounds: int | None = None,
              log: bool = True) -> ProbeResult:
    """Try to invoke ONE function from its signature and report what happened.

    dry_run=True assembles inputs + snippet + scaffold + command and returns them
    WITHOUT compiling (works offline, no jars/Spark/LLM needed)."""
    from .doc_checks import _fill_scaffold, _classify_error
    params = params or []
    ctx = resolve_exec_context(cfg)
    input_var = _pick_input(ctx["sample_data"], signature, params, returns)
    if not input_var:
        return ProbeResult(name=name, status="skipped",
                           error="no sample inputs available (configure comprehension.execute fixtures)")

    if max_fix_rounds is None:
        max_fix_rounds = int(ctx["ex"].get("max_fix_rounds", 3) or 0)

    work_api = ctx["work_dir"] / f"probe_{name}"
    scala_file = work_api / "ApiTest.scala"
    cmd = (ctx["command"].replace("{scala_file}", str(scala_file)).replace("{uberjar}", ctx["uberjar"])
           .replace("{jars}", ctx["jars"]).replace("{classpath}", ctx["classpath"])
           .replace("{work}", str(work_api)).replace("{packages}", ctx["packages_flag"])
           .replace("{repositories}", ctx["repositories_flag"]))

    # first snippet: LLM from signature (real path) or template (offline/dry-run)
    if use_llm and not dry_run:
        try:
            snippet = _llm_probe_snippet(cfg, name, signature, params, returns,
                                         ctx["available_inputs"], "", ctx)
        except Exception:
            snippet = _template_probe_snippet(name, params, returns, input_var, ctx["check_marker"])
    else:
        snippet = _template_probe_snippet(name, params, returns, input_var, ctx["check_marker"])

    scaffold = ctx["scaffold"].replace("// AIDEAL_DATA_BINDINGS", ctx["bindings"])
    scala = _fill_scaffold(scaffold, snippet, ctx["region"], {})

    if dry_run:
        return ProbeResult(name=name, status="dry-run", snippet=snippet, input_var=input_var,
                           scala_file=scala, command=cmd)

    work_api.mkdir(parents=True, exist_ok=True)
    _elog = ErrorLog(cfg.error_log)
    run_id = new_run_id()
    version = git_version(cfg.root)
    rounds: list[dict] = []
    last = {}
    for attempt in range(1 + max_fix_rounds):
        scala_file.write_text(_fill_scaffold(scaffold, snippet, ctx["region"], {}), encoding="utf-8")
        try:
            proc = subprocess.run(cmd, shell=True, cwd=work_api, capture_output=True,
                                  text=True, timeout=ctx["timeout"], env=dict(os.environ))
            out, err_out, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            out, err_out, rc = (e.stdout or ""), (e.stderr or "") + "\n[timeout]", 124
        merged = (out or "") + "\n" + (err_out or "")
        ok = (rc == 0) \
            and (ctx["success_marker"] in merged if ctx["success_marker"] else True) \
            and not (ctx["error_marker"] and ctx["error_marker"] in merged) \
            and (ctx["check_marker"] in merged if ctx["require_correctness"] else True)
        if ok:
            witness = next((ln for ln in merged.splitlines() if ctx["check_marker"] in ln), "")
            rounds.append({"round": attempt, "status": "pass"})
            if log:
                _elog.append(run_id=run_id, step="probe", language=cfg.language,
                             task="probe_try_first", status="pass", function=name,
                             code=snippet.strip()[:1500], library_version=version)
            return ProbeResult(name=name, status="pass", snippet=snippet, witness=witness.strip(),
                               rounds=rounds, scala_file=str(scala_file), command=cmd, input_var=input_var)
        cat, msg, locus = _classify_error(merged, rc, ctx["error_marker"])
        rounds.append({"round": attempt, "status": "fail", "category": cat, "error": msg[:160]})
        last = {"cat": cat, "msg": msg, "locus": locus}
        if log:
            _elog.append(run_id=run_id, step="probe", language=cfg.language, task="probe_try_first",
                         status="fail", function=name, error_category=cat, error=msg,
                         root_cause=locus, code=snippet.strip()[:1000], library_version=version)
        # regenerate from the error (ChatTester-style), if we have the LLM
        if use_llm and attempt < max_fix_rounds:
            try:
                snippet = _llm_probe_snippet(cfg, name, signature, params, returns,
                                             ctx["available_inputs"],
                                             f"Prior attempt failed [{cat}]: {msg[:300]}", ctx)
            except Exception:
                break
        else:
            break
    return ProbeResult(name=name, status="fail", snippet=snippet, rounds=rounds,
                       error_category=last.get("cat", ""), error=last.get("msg", ""),
                       scala_file=str(scala_file), command=cmd, input_var=input_var)


def probe_grounding_block(result: ProbeResult, name: str) -> str:
    """Render a probe result as a `tests_text` grounding block for the readme_entry
    prompt — the same slot a real test example fills."""
    if result.status == "pass":
        w = f"\n// observed result: {result.witness}" if result.witness else ""
        return ("(no existing test; a VERIFIED signature-probe compiled AND ran — this is a "
                f"real, executable call pattern, reproduce its shape){w}\n" + result.snippet.strip())
    if result.status == "fail":
        return (f"(no existing test; a signature-probe was attempted and FAILED "
                f"[{result.error_category}] — avoid this shape)\n"
                f"// error: {result.error.strip()[:300]}\n// tried:\n{result.snippet.strip()}")
    return "(no existing test found for this API)"


def main(argv=None):
    import argparse
    import json
    from .config import load_config
    from .readme_agent import public_api_details
    p = argparse.ArgumentParser(description="Version B: execution-first probe for one API.")
    p.add_argument("--config", default="aideal.yaml")
    p.add_argument("--api", required=True, help="function name to probe")
    p.add_argument("--dry-run", action="store_true", help="assemble inputs+snippet+command, run nothing")
    p.add_argument("--no-llm", action="store_true", help="use the template snippet, skip the LLM")
    args = p.parse_args(argv)
    cfg = load_config(Path(args.config))
    recs = [d for d in public_api_details(cfg) if d["name"] == args.api]
    if not recs:
        print(f"API '{args.api}' not found in the surface."); return 1
    primary = max(recs, key=lambda r: len(r.get("params") or []))
    res = run_probe(cfg, args.api, signature=primary.get("signature", ""),
                    params=primary.get("params"), returns=primary.get("returns", ""),
                    dry_run=args.dry_run, use_llm=not args.no_llm, log=not args.dry_run)
    print(f"== probe: {res.name} -> {res.status}  (input: {res.input_var}) ==")
    if res.command:
        print(f"\n-- command --\n{res.command}")
    if res.scala_file and args.dry_run:
        print(f"\n-- assembled ApiTest.scala --\n{res.scala_file}")
    else:
        print(json.dumps({"status": res.status, "witness": res.witness,
                          "error": res.error, "rounds": res.rounds}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
