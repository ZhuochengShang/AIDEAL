"""Deep-dive: how deeply can a model understand ONE API of this codebase?

Assembles the richest grounded context the repo can offer for a single API —
large canonical source window, definitions of every signature/receiver type
(Scala AND Java), real CALL SITES from across the repo (tests included), the
current catalog entry, and the full recorded failure history — then asks the
model for a LAYERED expert report whose final section is a self-assessment of
what it could NOT verify. The report is saved to docs/deepdive/<api>.md with
token/time accounting, so "depth of understanding" is inspectable and
comparable across models. CLI: `aideal deep-dive --api X [--role fixer=...]`.
"""

from __future__ import annotations

import glob as _glob
import json
import re
import time
from pathlib import Path

from .config import AidealConfig


def _call_sites(cfg: AidealConfig, name: str, limit: int = 6, ctx: int = 3) -> str:
    """Real usages of `name` across the repo (main + tests), with a few lines
    of context — how the codebase ITSELF calls this API."""
    pat = re.compile(rf"\.{re.escape(name)}\s*\(|\b{re.escape(name)}\s*\(")
    defpat = re.compile(rf"\bdef\s+{re.escape(name)}\b")
    hits: list[str] = []
    globs = (list(cfg.source_globs) + list(cfg.test_globs)
             + [g.replace(".scala", ".java") for g in cfg.source_globs])
    for g in globs:
        for p in _glob.glob(str(cfg.root / g), recursive=True):
            if len(hits) >= limit:
                break
            try:
                lines = Path(p).read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for i, ln in enumerate(lines):
                if pat.search(ln) and not defpat.search(ln):
                    lo, hi = max(0, i - ctx), min(len(lines), i + ctx + 1)
                    rel = str(Path(p).relative_to(cfg.root))
                    seg = "\n".join(f"{j+1:5d} | {lines[j]}" for j in range(lo, hi))
                    hits.append(f"// {rel}:{i+1}\n{seg}")
                    break   # one site per file keeps variety
    return "\n\n".join(hits) or "(no call sites found outside the definition)"


def _failure_history(cfg: AidealConfig, name: str, limit: int = 5) -> str:
    from .error_log import ErrorLog
    rows = [r for r in ErrorLog(cfg.error_log).entries()
            if r.get("function") == name and r.get("status") in ("fail", "fixed")]
    out = []
    for r in rows[-limit:]:
        out.append(f"[{r.get('status')}/{r.get('error_category')}] {(r.get('error') or '')[:200]}\n"
                   f"  attempted code: {(r.get('code') or '')[:300]}")
    return "\n\n".join(out) or "(no recorded attempts)"


def deep_dive_run(cfg: AidealConfig, api: str, out_dir: str = "docs/deepdive",
                  context_only: bool = False, return_text: bool = False) -> dict:
    from .docfix import _source_window, _type_context
    from .readme_agent import parse_readme

    window, others = _source_window(cfg, api, before=30, after=160)
    types = _type_context(cfg, api, max_types=6, lines_per_type=45)
    calls = _call_sites(cfg, api)
    history = _failure_history(cfg, api)
    entry = next((e.body for e in parse_readme(cfg.llm_readme) if e.name == api),
                 "(no catalog entry)")
    if context_only:
        ctx = (f"== SOURCE ==\n{window}\n\n== TYPES ==\n{types}\n\n"
               f"== CALL SITES ==\n{calls}\n\n== HISTORY ==\n{history}")
        return {"api": api, "context_chars": len(ctx), "context_preview": ctx[:1500]}

    from .llm import invoke_text, usage_snapshot, usage_delta
    from .prompts import load as load_prompt
    from .profile import require_profile
    require_profile(cfg)
    spec = cfg.model_for_role("fixer")
    t0, u0 = time.time(), usage_snapshot()
    report = invoke_text(spec, *load_prompt(
        cfg, "aideal/deep_dive",
        api_name=api, source_window=window[:14000], other_sites=others,
        type_context=types[:10000], call_sites=calls[:6000],
        entry_body=entry[:5000], failure_history=history[:4000]))
    u = usage_delta(u0)
    out = Path(cfg.root) / out_dir
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{api}.md"
    header = (f"# Deep-dive: `{api}`\n\nmodel: {spec.provider}:{spec.model} · "
              f"tokens in={u['input_tokens']:,} out={u['output_tokens']:,} · "
              f"wall {time.time()-t0:.0f}s · {time.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n")
    dest.write_text(header + report, encoding="utf-8")
    out = {"api": api, "report": str(dest),
           "model": f"{spec.provider}:{spec.model}",
           "tokens": {"in": u["input_tokens"], "out": u["output_tokens"]},
           "wall_s": round(time.time() - t0, 1)}
    if return_text:
        out["report_text"] = report
    return out
