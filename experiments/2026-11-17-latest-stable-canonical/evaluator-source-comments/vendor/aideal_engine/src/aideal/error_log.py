"""Accumulated error log (JSONL, one structured record per line).

Record schema (agreed format):
  {
    "run_id": "20260420-223000Z",
    "step": "code-test",
    "language": "Scala",
    "task": "ndvi_pipeline",
    "status": "fail",
    "function": "saveAsGeoTiff",
    "error": "unsupported raster datatype Float64",
    "root_cause": "ClassCastException: java.lang.Float cannot be cast to java.lang.Int",
    "suggested_fix_code": "val inRaw: RasterRDD[$actualType] = sc.geoTiff[$actualType](inputPath)"
  }

Storage is JSONL (machine-grade, append-only across runs).
`to_prompt()` renders a compact, token-efficient view for prompt injection —
the LLM never sees the raw JSON.
`suggest_aliases()` mines hallucinated function names -> alias candidates.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from collections import Counter
from pathlib import Path

FIELDS = ("run_id", "step", "language", "task", "status",
          "function", "error_category", "error", "root_cause", "code", "suggested_fix_code",
          # fix-loop provenance: which retry round produced this row (0 = first
          # attempt). Lets `aideal fix-report` reconstruct the round-by-round
          # error evolution per API without guessing from line order.
          "round",
          # staleness tags: a verified example can go stale when the code moves
          # underneath it. `library_version` catches a KNOWN change (commit/tag
          # differs -> invalidate); `timestamp` catches an UNKNOWN one (too old to
          # trust when no version is tracked). Both optional; old logs stay valid.
          "library_version", "timestamp")

HALLUCINATED_NAME_RE = re.compile(
    r"value (\w+) is not a member|not found: value (\w+)|has no attribute '(\w+)'"
)


def new_run_id() -> str:
    return time.strftime("%Y%m%d-%H%M%SZ", time.gmtime())


def git_version(root) -> str:
    """Short git commit of the target codebase, used to tag memory entries so a
    verified example can be invalidated when the code moves underneath it. Returns
    '' when `root` isn't a git repo (staleness then falls back to timestamp)."""
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


class ErrorLog:
    def __init__(self, path: Path):
        self.path = path

    def append(self, **record) -> dict:
        if not record.get("run_id"):
            record["run_id"] = new_run_id()
        if not record.get("status"):
            record["status"] = "fail"
        if not record.get("timestamp"):
            record["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry = {k: record.get(k, "") for k in FIELDS}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def to_prompt(self, max_entries: int = 15, task: str | None = None) -> str:
        """Compact token-efficient render: `function: error -> fix (xN)`."""
        seen: Counter = Counter()
        fixes: dict[tuple, str] = {}
        for e in self.entries():
            if task and e.get("task") != task:
                continue
            key = (e.get("function", ""), e.get("error", ""))
            seen[key] += 1
            if e.get("suggested_fix_code"):
                fixes[key] = e["suggested_fix_code"]
        if not seen:
            return ""
        lines = ["Known failures to avoid (function: error -> fix):"]
        for (fn, err), n in seen.most_common(max_entries):
            fix = fixes.get((fn, err), "")
            lines.append(f"- {fn}: {err}" + (f" -> {fix}" if fix else "") + (f" (x{n})" if n > 1 else ""))
        return "\n".join(lines)

    def failures_for(self, function: str, max_items: int = 4) -> str:
        """Compact render of prior failures for ONE function, to feed back into
        the next generation/repair attempt. Pairs error -> fix when known."""
        rows = [e for e in self.entries()
                if e.get("function") == function and e.get("status") in ("fail", "fixed")]
        if not rows:
            return ""
        lines = [f"Prior failures for `{function}` — avoid repeating these:"]
        for e in rows[-max_items:]:
            cat = e.get("error_category", "") or "error"
            line = f"- [{cat}] {e.get('error','').strip()[:200]}"
            if e.get("root_cause"):
                line += f"  (at: {e['root_cause'].strip()[:120]})"
            if e.get("suggested_fix_code"):
                # `fixed` rows carry real working code; `fail` rows carry a
                # FIX_GUIDE hint (what kind of fix). Label accordingly so the model
                # isn't told a hint is proven code.
                label = "fix that worked" if e.get("status") == "fixed" else "suggested fix"
                line += f"\n  {label}: {e['suggested_fix_code'].strip()[:300]}"
            lines.append(line)
        return "\n".join(lines)

    def suggest_aliases(self) -> list[dict]:
        """Hallucinated names are evidence of what models EXPECT the API to be
        called — i.e., good alias candidates."""
        candidates: Counter = Counter()
        context: dict[str, str] = {}
        for e in self.entries():
            for text in (e.get("error", ""), e.get("root_cause", "")):
                m = HALLUCINATED_NAME_RE.search(text)
                if m:
                    name = next(g for g in m.groups() if g)
                    candidates[name] += 1
                    context[name] = e.get("function", "") or e.get("task", "")
        return [
            {"proposed_alias": name, "for": context[name], "evidence_count": n}
            for name, n in candidates.most_common()
        ]
