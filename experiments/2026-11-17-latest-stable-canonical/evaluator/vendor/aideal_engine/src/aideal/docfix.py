"""Doc-repair fix routing — fix the DOCUMENTATION, not just the snippet.

The classic fix loop rewrites the failing snippet with the error pasted back
(same doc, new guess); measured rescue rates are low and stuck loops common.
This routing treats the failure as evidence about the DOC and repairs it:

  1. take a FAILED function (most-recent fail in the error log),
  2. locate its canonical definition in the codebase and read the REAL source,
  3. senior-engineer LLM pass diagnoses the root cause against that source,
  4. rewrite that API's LLM_readme entry, folding the diagnosis in,
  5. re-run the comprehension test for that API with the repaired entry.

Entry policy: keep a repaired entry after its validation passes; otherwise
revert it when the bounded loop ends. A fresh B2 can still regress. Durable
phase state and orchestration live in repair_journal.py and doc_repair.py.
CLI: `aideal fix-docs`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .config import AidealConfig


def _replace_entry_text(text: str, name: str, new_entry: str) -> str:
    """Replace the `## API Test: `name`` section (up to the next entry or EOF).
    Pure function so it is unit-testable. Raises KeyError if absent."""
    pat = re.compile(rf"(?ms)^## API Test: `{re.escape(name)}`.*?(?=^## API Test: `|\Z)")
    if not pat.search(text):
        raise KeyError(name)
    repl = new_entry.rstrip() + "\n\n"
    return pat.sub(lambda _m: repl, text, count=1)


def _insert_entry_text(text: str, new_entry: str) -> str:
    """Append a brand-new `## API Test:` entry at the end of the catalog.
    Used by create-missing mode (original-readme arm: the doc-repair loop
    WRITES the entry that never existed)."""
    return (text.rstrip() + "\n\n" if text.strip() else "") + new_entry.rstrip() + "\n\n"


def _remove_entry_text(text: str, name: str) -> str:
    """Delete an entry created by this run (all-rounds-fail in create-missing
    mode reverts to ABSENT, keeping the catalog exactly as found)."""
    pat = re.compile(rf"(?ms)^## API Test: `{re.escape(name)}`.*?(?=^## API Test: `|\Z)")
    return pat.sub("", text, count=1)


def _source_window(cfg: AidealConfig, name: str, before: int = 15, after: int = 80) -> tuple[str, str]:
    """(window_text, other_sites_note) for the CANONICAL definition of `name`
    — the same election dedup/readme use (subsumption + deprioritized paths)."""
    from .readme_agent import public_api_details, _subsume_overloads, _dedup_deprioritize
    recs = [d for d in public_api_details(cfg)
            if d["visibility"] == "public" and d["name"] == name]
    if not recs:
        return "(definition not found on the public surface)", "(none)"
    maximals, _ = _subsume_overloads(recs, _dedup_deprioritize(cfg))
    canon = maximals[0]
    path = cfg.root / canon["file"]
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    lo = max(0, canon["line"] - 1 - before)
    hi = min(len(lines), canon["line"] - 1 + after)
    numbered = "\n".join(f"{i+1:5d} | {lines[i]}" for i in range(lo, hi))
    window = f"// {canon['file']}:{canon['line']}\n{numbered}"
    others = [f"{d['file']}:{d['line']}" for d in recs if d is not canon]
    return window, (", ".join(others[:6]) or "(none)")


# Legacy fallback only: category contents come from the YAML
# layers (defaults.yaml / adapters / project file, under
# docfix.member_categories) and the DEFAULT evidence source is the repo's own
# call vocabulary (_repo_called_members). This dict answers only for configs
# that name a category without defining it anywhere in YAML.
_ALLOWED_MEMBER_CATEGORIES = {
    # Language/library calls that are normal in snippets and should not be
    # confused with the target project API surface.
    "language_core": {
        "println", "print", "require", "assert", "format", "mkString", "toString",
        "map", "flatMap", "filter", "foreach", "collect", "count", "take", "first",
        "reduce", "fold", "foldLeft", "sum", "min", "max", "size", "length",
        "nonEmpty", "isEmpty", "head", "headOption", "last", "getOrElse", "get",
        "exists", "forall", "contains", "indexOf", "sortBy", "sorted", "zip",
        "zipWithIndex", "toArray", "toList", "toSeq", "toSet", "toMap", "distinct",
        "sliding", "grouped", "apply", "update", "close", "cache", "persist",
        "coalesce", "repartition", "keys", "values", "trim", "split", "replace",
        "startsWith", "endsWith", "toDouble", "toInt", "toLong", "toFloat", "abs",
        "floor", "ceil", "round", "find", "getPath", "getName", "getClass",
        "asInstanceOf", "isInstanceOf", "mkdirs", "listFiles", "delete",
        "getConstructor", "newInstance", "getFileSystem", "resolve",
        "isNaN", "isInfinite", "isFinite", "toRadians", "toDegrees", "sqrt",
        "pow", "sin", "cos", "tan", "atan2", "fill", "range", "empty", "ofDim",
    },
    "spark": {
        "builder", "appName", "master", "config", "getOrCreate", "sparkContext",
        "createDataFrame", "load", "save", "mode", "option", "options", "select",
        "where", "withColumn", "as", "show", "registerTempTable", "toDF", "toDS",
        "rdd", "schema", "printSchema", "parallelize", "textFile", "wholeTextFiles",
        "broadcast", "longAccumulator", "doubleAccumulator", "setLogLevel",
        "getNumPartitions", "partitions", "partitioner", "saveAsTextFile",
    },
    "geometry_common": {
        "createPoint", "createLineString", "createPolygon", "createMultiPolygon",
        "createGeometryCollection", "createLinearRing", "setSRID", "getSRID",
        "getCoordinate", "getCoordinates", "getEnvelopeInternal", "getArea",
        "getLength", "intersects", "contains", "covers", "within", "touches",
        "buffer", "union", "intersection", "difference", "getX", "getY",
        "decode", "encode",
    },
    "raster_common": {
        "getPixelValueAsFloat", "getPixelValueAsDouble",
        "getPixelValueAsInt", "getPixelValueAsLong",
    },
    # Python/numpy/sklearn ecosystem members that are normal in snippets and
    # must not be mistaken for fabricated project APIs (python adapter).
    "python_core": {
        "fit", "predict", "transform", "fit_transform", "fit_predict",
        "score", "ravel", "reshape", "astype", "tolist", "copy", "mean",
        "sum", "std", "var", "argmin", "argmax", "cumsum", "squeeze",
        "flatten", "array", "asarray", "zeros", "ones", "arange", "linspace",
        "allclose", "isclose", "seed", "rand", "randn", "randint",
        "normal", "shuffle", "append", "extend", "join", "format", "items",
        "keys", "values", "get", "strip", "lower", "upper", "round",
        "set_params", "get_params",
    },
}


_MEMBER_CALL_RE = re.compile(r"\.([a-zA-Z_]\w*)\s*\(")


def _repo_called_members(cfg: AidealConfig, max_files: int = 4000) -> set[str]:
    """Derive an evidence-based member-name allowlist: every
    member name the target codebase ITSELF calls in its sources/tests is
    legitimate vocabulary for this ecosystem — `.map`, `.fit`, `.getOrCreate`,
    `.createPoint` all appear in real repo code, so no hand-curated
    language/ecosystem/domain list is needed per codebase. A rewrite calling a
    member the repo has never called anywhere is exactly the hallucination
    class the guard exists to reject. Existence is name-level (like the guard
    itself); wrong-receiver misuse is still caught by the execution retry."""
    import glob as _glob
    out: set[str] = set()
    seen = 0
    for g in list(cfg.source_globs) + list(cfg.test_globs or []):
        for path in _glob.glob(str(cfg.root / g), recursive=True):
            if seen >= max_files:
                return out
            seen += 1
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            out.update(_MEMBER_CALL_RE.findall(text))
    return out


def _allowed_members_from_config(cfg: AidealConfig | None = None) -> set[str]:
    """Allowed-member vocabulary for the fabricated-member guard, from three
    layers (most general first):

      1. docfix.allow_repo_called_members (default TRUE): members mined from
         the target repo's own sources/tests — codebase-agnostic, no curation.
      2. docfix.member_categories (YAML, deep-merged defaults <- adapter <-
         project): named sets whose CONTENTS live in config layers, e.g.
         language_core in defaults.yaml, spark in the scala-spark adapter,
         geometry/raster sets in the rdpro project file. The Python
         _ALLOWED_MEMBER_CATEGORIES dict remains only as a fallback for
         configs that name a category without defining it.
      3. docfix.allowed_members: plain per-project extra names.
    """
    raw_docfix = ((cfg.raw or {}).get("docfix") if cfg else None) or {}
    categories = raw_docfix.get("allowed_member_categories", ["language_core"])
    yaml_cats = raw_docfix.get("member_categories", {}) or {}
    out: set[str] = set()
    for cat in categories:
        defined = yaml_cats.get(cat)
        out.update(defined if defined is not None
                   else _ALLOWED_MEMBER_CATEGORIES.get(cat, set()))
    out.update(raw_docfix.get("allowed_members", []))
    if cfg is not None and raw_docfix.get("allow_repo_called_members", True):
        out |= _repo_called_members(cfg)
    return out


def _fabricated_members(entry_md: str, surface: set[str], api_name: str,
                        allowed_members: set[str] | None = None) -> list[str]:
    """Member calls `.name(` inside the entry's code blocks that are neither on
    the library's RAW surface, nor configured ecosystem/language methods, nor
    the API itself — i.e. likely hallucinated project members (`.convolve`, …)."""
    code = "\n".join(re.findall(r"```.*?\n(.*?)```", entry_md, re.S))
    called = set(re.findall(r"\.([a-z]\w+)\s*\(", code))
    allowed = allowed_members if allowed_members is not None else _allowed_members_from_config()
    return sorted(called - surface - allowed - {api_name})


def _failed_apis_from_results(path: str | Path, entries: set[str]) -> tuple[list[str], list[str]]:
    """Return failed API names from a comprehension/bench result JSON.

    This freezes docfix to a specific baseline run (e.g. g1) instead of whatever
    the mutable error log currently says after later g4/docfix experiments.
    """
    p = Path(path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    metrics = obj.get("metrics") or {}
    failed = sorted(n for n, m in metrics.items()
                    if isinstance(m, dict) and m.get("status") == "fail")
    return [n for n in failed if n in entries], [n for n in failed if n not in entries]


def _write_report(path: str | Path | None, report: dict) -> None:
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    from .repair_journal import atomic
    atomic(p, report)


def _read_report(path: str | Path | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Corrupt document-repair report; preserve and inspect it") from exc


def _outcomes(results: dict[str, dict]) -> dict[str, int]:
    from collections import Counter
    return dict(Counter(v.get("status", "unknown").split(" ")[0]
                        for v in results.values()))


_TYPE_SKIP = {"String", "Int", "Long", "Float", "Double", "Boolean", "Unit",
              "Array", "Option", "Some", "None", "Seq", "List", "Map", "Set",
              "Class", "Any", "AnyRef", "AnyVal", "T", "K", "V", "ClassTag",
              "Iterator", "Iterable", "Tuple2", "Tuple3", "RDD", "JavaRDD",
              "SparkContext", "SparkSession", "DataFrame", "NoneType", "True", "False"}


def _type_context(cfg: AidealConfig, name: str, max_types: int = 4,
                  lines_per_type: int = 35) -> str:
    """Definitions of receiver/parameter/return types found in configured source.

    This intentionally follows ``source_globs`` rather than assuming a language
    pair.  The declaration pattern covers common class/type constructs; projects
    with unusual syntax still get an explicit "not found" instead of a fabricated
    definition.
    """
    import glob as _glob
    from .readme_agent import public_api_details, _subsume_overloads, _dedup_deprioritize
    recs = [d for d in public_api_details(cfg)
            if d["visibility"] == "public" and d["name"] == name]
    if not recs:
        return "(no public definition found)"
    canon = _subsume_overloads(recs, _dedup_deprioritize(cfg))[0][0]
    sig = " ".join([canon.get("signature") or "", canon.get("returns") or ""] +
                   [p.get("type") or "" for p in canon.get("params", [])])
    types = [t for t in dict.fromkeys(re.findall(r"\b([A-Z][A-Za-z0-9]{2,})\b", sig))
             if t not in _TYPE_SKIP][:max_types]
    if not types:
        return "(signature uses only primitive/collection types)"
    pats = {t: re.compile(rf"\b(?:case\s+class|abstract\s+class|class|trait|object|"
                              rf"interface|enum|struct|record|type)\s+{t}\b")
            for t in types}
    found: dict[str, str] = {}
    extra_globs = (((cfg.raw or {}).get("codebase") or {})
                   .get("type_context_globs") or [])
    for g in dict.fromkeys([*cfg.source_globs, *extra_globs]):
        if len(found) == len(types):
            break
        for p in _glob.glob(str(cfg.root / g), recursive=True):
            if len(found) == len(types):
                break
            try:
                text = Path(p).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for t, pat in pats.items():
                if t in found:
                    continue
                m = pat.search(text)
                if m:
                    lines = text.splitlines()
                    ln = text[:m.start()].count("\n")
                    seg = "\n".join(lines[ln:ln + lines_per_type])
                    rel = str(Path(p).relative_to(cfg.root))
                    suffix = Path(p).suffix.lstrip(".") or cfg.language
                    found[t] = f"// type {t} ({suffix} source) — {rel}:{ln + 1}\n{seg}"
    return "\n\n".join(found.get(t, f"// type {t}: definition NOT found in sources")
                       for t in types)


def _err_sig(category: str, message: str) -> str:
    """Normalized error signature (shared with fixreport) for progress checks."""
    from .fixreport import error_signature
    return error_signature(category or "", message or "")


def _diag_sig(diagnosis: str) -> str:
    """Signature of a diagnosis: the ROOT CAUSE section, whitespace-normalized.
    Used for the per-round 'did understanding improve?' check — an unchanged
    root cause means the deep dive learned nothing new this round."""
    m = re.search(r"ROOT CAUSE:(.*?)(?:\n[A-Z][A-Z ]+:|\Z)", diagnosis, re.S)
    core = (m.group(1) if m else diagnosis)
    return " ".join(core.split()).lower()[:400]


def doc_fix_run(cfg: AidealConfig, apis: list[str] | None = None,
                max_apis: int | None = None, retry_rounds: int = 2,
                timeout_s: int | None = None, dry_run: bool = False,
                from_results: str | Path | None = None,
                report_path: str | Path | None = None,
                deep_dive_first: bool = False,
                deep_dive_out: str = "docs/deepdive",
                doc_rounds: int = 1,
                doc_stuck: int = 2,
                create_missing: bool = False,
                doc_source: str = "aideal",
                full_doc: bool | None = None,
                doc_scope: str | None = None,
                manifest: str | None = None) -> dict:
    """Run the resumable document-repair controller under one document lock."""
    arguments = locals().copy()
    from .repair_journal import document_lock
    from .doc_repair import run
    with document_lock(cfg.llm_readme):
        return run(**arguments)
