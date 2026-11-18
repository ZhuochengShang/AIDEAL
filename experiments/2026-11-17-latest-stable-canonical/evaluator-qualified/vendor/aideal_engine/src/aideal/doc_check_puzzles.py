"""Application-owned puzzle execution with documentation/plan controls and repair memory."""
from __future__ import annotations

import re
import shlex
import subprocess
import sys
from .config import AidealConfig
from .error_log import ErrorLog
from .notes_to_self import NotesToSelf


def puzzle_check(
    cfg: AidealConfig,
    dry_run: bool = False,
    *,
    doc_source: str = "aideal",
    api_doc: str | None = None,
    bank: str | None = None,
    sample_data: str | None = None,
    plan_path: str | None = None,
    plan_out: str | None = None,
    mode: str | None = None,
    case_ids: list[str] | None = None,
    sample: int | None = None,
    seed: int | None = None,
    tag: str | None = None,
    memory: str | None = None,
) -> dict:
    """Run an application-provided puzzle evaluator on a frozen AIDEAL plan.

    The runner remains application-owned, but AIDEAL owns the experimental
    controls: documentation arm, stable case selection, fixture hashes, model,
    and run label.  Legacy projects with only ``puzzle.command`` continue to
    work without a bank or plan.
    """
    import hashlib
    import json as _json
    import os
    from pathlib import Path

    from .puzzle_bank import (
        freeze_puzzle_plan,
        load_structured,
        verify_plan_inputs,
        write_plan,
    )

    def _path(value: str) -> Path:
        p = Path(value)
        return p.resolve() if p.is_absolute() else (cfg.root / p).resolve()

    def _doc_path() -> Path:
        if api_doc:
            result = _path(api_doc)
            if not result.is_file():
                raise FileNotFoundError(f"puzzle documentation not found: {result}")
            return result
        if doc_source == "aideal":
            if not cfg.llm_readme.is_file():
                raise FileNotFoundError(f"generated documentation not found: {cfg.llm_readme}")
            return cfg.llm_readme
        parts: list[str] = []
        if doc_source in ("original", "original+aideal"):
            original = cfg.original_readme_text(limit=None)
            if not original.strip():
                raise FileNotFoundError("no configured original documentation for puzzle arm")
            parts.append(original)
        if doc_source == "original+aideal":
            parts.append("===== GENERATED AIDEAL DOCUMENTATION =====\n"
                         + cfg.llm_readme.read_text(encoding="utf-8", errors="ignore"))
        destination = cfg.root / ".aideal_exec" / "puzzle_docs" / f"{doc_source}.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n\n".join(parts), encoding="utf-8")
        return destination

    def _sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    pz = cfg.puzzle
    cmd_template = pz.get("command", "")
    if not cmd_template:
        return {"check": "puzzle", "passed": False, "score": 0.0,
                "details": {"error": "no puzzle.command configured"}}
    selected_seed = int(seed if seed is not None else pz.get("seed", 42))
    selected_doc = _doc_path()
    frozen_plan: dict | None = None
    selected_plan: Path | None = None
    selected_mode = mode or "composition"
    if plan_path:
        selected_plan = _path(plan_path)
        frozen_plan = load_structured(selected_plan)
        plan_mode = str(frozen_plan.get("mode", "composition"))
        if mode is not None and mode != plan_mode:
            return {"check": "puzzle", "passed": False, "score": 0.0,
                    "details": {"error": f"--mode {mode} disagrees with frozen plan mode {plan_mode}",
                                "plan": str(selected_plan)}}
        selected_mode = plan_mode
        drift = verify_plan_inputs(frozen_plan)
        if drift:
            return {"check": "puzzle", "passed": False, "score": 0.0,
                    "details": {"error": "frozen plan input drift", "issues": drift,
                                "plan": str(selected_plan)}}
    else:
        bank_value = bank or pz.get("test_bank")
        data_value = sample_data or pz.get("sample_data")
        if bank_value or data_value:
            if not bank_value or not data_value:
                return {"check": "puzzle", "passed": False, "score": 0.0,
                        "details": {"error": "both puzzle test bank and sample data are required"}}
            from .readme_agent import parse_readme
            frozen_plan = freeze_puzzle_plan(
                root=cfg.root,
                bank_path=_path(str(bank_value)),
                sample_data_path=_path(str(data_value)),
                mode=selected_mode,
                case_ids=case_ids,
                sample=sample,
                seed=selected_seed,
                documented_apis={entry.name for entry in parse_readme(cfg.llm_readme)},
            )
            selected_plan = (_path(plan_out) if plan_out else
                             cfg.root / ".aideal_exec" / "puzzle_plans" /
                             f"{selected_mode}_seed{selected_seed}.json")
            write_plan(frozen_plan, selected_plan)

    model = cfg.model_for_role("audience")
    run_tag = tag or f"{doc_source}_{selected_mode}"
    work_dir = _path(str(pz.get("work_dir", "results/puzzle_runs")))
    runner_args = pz.get("runner_args") or []
    if isinstance(runner_args, str):
        runner_args = shlex.split(runner_args)
    rendered_runner_args = " ".join(shlex.quote(str(item)) for item in runner_args)
    scaffold = _path(str(pz.get("scaffold", "../../grail-agent/outputs/generated_scala/job_scaffold.scala")))
    guide_value = str(pz.get("guide", "")).strip()
    guide = _path(guide_value) if guide_value else None
    values = {
        "python": shlex.quote(sys.executable),
        "llm_readme": shlex.quote(str(cfg.llm_readme)),
        "api_doc": shlex.quote(str(selected_doc)),
        "test_bank": shlex.quote(str(_path(str(bank or pz.get('test_bank', '.'))))),
        "sample_data": shlex.quote(str(_path(str(sample_data or pz.get('sample_data', '.'))))),
        "plan": shlex.quote(str(selected_plan)) if selected_plan else "",
        "work_dir": shlex.quote(str(work_dir)),
        "mode": shlex.quote(selected_mode),
        "tag": shlex.quote(run_tag),
        "provider": shlex.quote(model.provider),
        "model": shlex.quote(model.model),
        "scaffold": shlex.quote(str(scaffold)),
        "guide": shlex.quote(str(guide)) if guide else "",
        "runner_args": rendered_runner_args,
        "max_retries_per_section": int(pz.get("max_retries_per_section", 2)),
        "dry_run": "--dry-run" if dry_run else "",
        "n": pz.get("num_puzzles", 3),
        "k": pz.get("num_functions", 5),
        "seed": selected_seed,
    }
    cmd = cmd_template.format(**values)
    if dry_run and "{dry_run}" not in cmd_template:
        cmd += " --dry-run"

    notes = NotesToSelf(cfg.notes_to_self)
    log = ErrorLog(cfg.error_log)
    rounds = []
    max_rounds = 1 if dry_run else 1 + int(pz.get("max_fix_rounds", 0))
    memory_enabled = (memory or str(pz.get("memory", "on"))).lower() == "on"
    for rnd in range(max_rounds):
        env = dict(os.environ)
        env.pop("PUZZLE_HINTS", None)
        hints = ("\n\n".join(x for x in (notes.to_prompt(), log.to_prompt()) if x)
                 if memory_enabled else "")
        if hints:
            hint_path = cfg.error_log.parent / "puzzle_hints.txt"
            hint_path.parent.mkdir(parents=True, exist_ok=True)
            hint_path.write_text(hints, encoding="utf-8")
            env["PUZZLE_HINTS"] = str(hint_path)
        run_cwd = (cfg.root / pz.get("cwd", ".")).resolve()
        proc = subprocess.run(shlex.split(cmd), cwd=run_cwd,
                              capture_output=True, text=True, env=env)
        report_summary = None
        report_match = re.search(r"^report:\s*(.+puzzle_report\.json)\s*$", proc.stdout, re.M)
        if report_match:
            report_file = Path(report_match.group(1).strip())
            try:
                report_summary = _json.loads(report_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                report_summary = None
        rounds.append({"round": rnd, "exit_code": proc.returncode,
                       "stdout_tail": proc.stdout[-2000:],
                       "stderr_tail": proc.stderr[-2000:],
                       "report": report_summary})
        if proc.returncode == 0:
            break
        notes.distill(log)  # consolidate before the next fix round
    ok = rounds[-1]["exit_code"] == 0
    scored = [round_["report"].get("readiness_score") for round_ in rounds
              if isinstance(round_.get("report"), dict)
              and round_["report"].get("readiness_score") is not None]
    return {"check": "puzzle", "passed": ok,
            "score": (None if dry_run else
                      (scored[-1] if scored else (1.0 if ok else 0.0))),
            "details": {
                "dry_run": dry_run,
                "command": cmd,
                "rounds": rounds,
                "doc_source": doc_source,
                "api_doc": str(selected_doc),
                "api_doc_sha256": _sha(selected_doc),
                "api_doc_bytes": selected_doc.stat().st_size,
                "plan": str(selected_plan) if selected_plan else None,
                "case_ids": frozen_plan.get("case_ids", []) if frozen_plan else [],
                "mode": selected_mode,
                "tag": run_tag,
                "memory": "on" if memory_enabled else "off",
                "model": {"provider": model.provider, "model": model.model},
            }}
