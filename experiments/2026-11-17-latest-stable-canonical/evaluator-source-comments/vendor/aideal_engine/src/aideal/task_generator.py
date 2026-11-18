"""Generate integration tasks from the project profile + LLM_readme.

Three task provenances coexist in integration_tasks.yaml:
  source: human      hand-written gold tasks (small, trusted)
  source: generated  author-model tasks seeded by profile use_cases (scale)
  (random puzzles are a third tier, handled by the puzzle runner)

The AUTHOR model generates; the AUDIENCE model solves — never the same role,
to avoid same-model bias.
"""

from __future__ import annotations

import re

import yaml

from .config import AidealConfig, load_tasks
from .llm import invoke_text
from .profile import require_profile
from .prompts import load as load_prompt
from .readme_agent import parse_readme


def generate_tasks(cfg: AidealConfig, n: int = 5) -> dict:
    require_profile(cfg)
    inventory = parse_readme(cfg.llm_readme)
    api_list = "\n".join(f"- `{e.name}`: {e.goal}" for e in inventory)

    raw = invoke_text(
        cfg.model_for_role("author"),
        *load_prompt(cfg, "aideal/tasks_generate", api_list=api_list, n=n),
    )
    m = re.search(r"tasks:.*", raw, re.DOTALL)
    if not m:
        return {"generated": 0, "error": "author model returned no tasks YAML", "raw_tail": raw[-300:]}
    parsed = yaml.safe_load(m.group(0)) or {}
    new_tasks = parsed.get("tasks", [])

    valid_names = {re.sub(r"\[.*\]$", "", e.name) for e in inventory}
    accepted, rejected = [], []
    existing_ids = {t.get("id") for t in load_tasks(cfg)}
    for t in new_tasks:
        apis = [re.sub(r"\[.*\]$", "", a) for a in t.get("apis", [])]
        if not t.get("id") or t["id"] in existing_ids:
            rejected.append({"task": t, "reason": "missing or duplicate id"})
        elif not apis or any(a not in valid_names for a in apis):
            rejected.append({"task": t, "reason": "uses APIs not in LLM_readme"})
        else:
            t["source"] = "generated"
            t.setdefault("language", cfg.language)
            accepted.append(t)
            existing_ids.add(t["id"])

    if accepted:
        data = {"tasks": load_tasks(cfg) + accepted}
        cfg.integration_tasks.write_text(
            "# Benchmark tasks. source: human = curated; generated = author-model from profile.\n"
            + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return {
        "generated": len(accepted),
        "rejected": rejected,
        "ids": [t["id"] for t in accepted],
        "tasks_file": str(cfg.integration_tasks),
    }
