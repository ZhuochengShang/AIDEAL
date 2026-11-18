"""Project profile: the user-entered fields the agent needs BEFORE reading
the code — what the project is, who the target users are, and the domain /
use cases. Injected into every author/audience prompt.

Created by `python -m aideal.cli init`; the agent refuses LLM-based steps
while required fields are missing or still TODO.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .config import AidealConfig

REQUIRED_FIELDS = ("project.description", "target_users", "use_cases", "domain")

TEMPLATE = """\
# Project profile — fill this in BEFORE running AIDEAL's LLM steps.
# `role`: the expertise persona the agent should adopt (injected first into
# every prompt), e.g. "an expert in geospatial raster pipelines on Spark".
role: "TODO: the expert role the agent should assume for this codebase"
project:
  name: TODO
  language: TODO
  description: >
    TODO: one paragraph - what this codebase does.

target_users:
  - "TODO: who consumes the LLM-generated code (e.g., scientists who know Python but not Scala)"

use_cases:
  - "TODO: concrete domain tasks the docs must support"

domain: "TODO: the problem domain (e.g., geospatial raster analytics)"

constraints:
  - "TODO: hard rules generated code must respect"
"""


def profile_path(cfg: AidealConfig) -> Path:
    sub = cfg.raw.get("files", {}).get("project_profile", "configs/project_profile.yaml")
    return (cfg.root / sub).resolve()


def load_profile(cfg: AidealConfig) -> dict:
    path = profile_path(cfg)
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def missing_fields(profile: dict) -> list[str]:
    missing = []
    for dotted in REQUIRED_FIELDS:
        node: object = profile
        for part in dotted.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        text = " ".join(map(str, node)) if isinstance(node, list) else str(node or "")
        if not node or "TODO" in text:
            missing.append(dotted)
    return missing


def require_profile(cfg: AidealConfig) -> dict:
    """Gate for LLM-based steps: raise with guidance if the profile is incomplete."""
    profile = load_profile(cfg)
    missing = missing_fields(profile)
    if missing:
        raise SystemExit(
            f"project profile incomplete ({profile_path(cfg)}): fill {missing}. "
            "Run `python -m aideal.cli init` to create the template."
        )
    return profile


AGENTS_SNIPPET = """\
## AIDEAL (LLM-readiness tooling)

This repo uses AIDEAL. Conventions for coding agents:

- **Before generating code against this codebase**, run `aideal log-prompt`
  and `aideal notes-prompt` (or the `known_mistakes` MCP tool) and respect the
  listed failures/lessons.
- **After a code-generation failure** (compile error, wrong API, hallucinated
  function), record it:
  `aideal log-add --step code-test --function <api> --error "<message>" --root-cause "<exception>" --suggested-fix-code "<fix>"`
- **After editing documentation**, verify structure: `aideal form` and
  `aideal completeness`. Doc entries live in the file configured as
  `files.llm_readme` and follow the `## API Test: \\`name\\`` template.
- **Do not invent API names.** If an intuitive name is missing, check
  `aideal alias-suggest` — it may already be a proposed alias.
- Project context (target users, domain, constraints) is in
  `configs/project_profile.yaml`; honor its constraints in all generated code.
- All commands read `configs/aideal.yaml`; output is JSON on stdout.
  MCP alternative: `aideal-mcp` exposes the same operations as tools.
"""


def init_agents_md(cfg: AidealConfig) -> dict:
    """Write AGENTS.md with the AIDEAL section if absent (never clobbers)."""
    path = cfg.root / "AGENTS.md"
    if path.exists():
        if "AIDEAL" in path.read_text(encoding="utf-8"):
            return {"agents_md": "already present"}
        with path.open("a", encoding="utf-8") as f:
            f.write("\n" + AGENTS_SNIPPET)
        return {"agents_md": "appended AIDEAL section"}
    path.write_text("# Agent instructions\n\n" + AGENTS_SNIPPET, encoding="utf-8")
    return {"agents_md": f"created {path}"}


def init_profile(cfg: AidealConfig) -> dict:
    path = profile_path(cfg)
    if path.exists():
        return {"action": "exists", "path": str(path), "missing_fields": missing_fields(load_profile(cfg))}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE, encoding="utf-8")
    return {"action": "created", "path": str(path),
            "note": "fill the TODOs - the agent will not run LLM steps until done"}


def project_context(profile: dict) -> str:
    """Render the profile as a compact prompt block."""
    if not profile:
        return ""
    proj = profile.get("project", {})
    lines = []
    if profile.get("role"):
        lines.append(f"Role: {profile['role'].strip()}")
    lines.append(f"Project: {proj.get('name', '?')} ({proj.get('language', '?')}) - {proj.get('description', '').strip()}")
    if profile.get("domain"):
        lines.append(f"Domain: {profile['domain']}")
    if profile.get("target_users"):
        lines.append("Target users: " + "; ".join(profile["target_users"]))
    if profile.get("use_cases"):
        lines.append("Use cases: " + "; ".join(profile["use_cases"]))
    if profile.get("constraints"):
        lines.append("Constraints: " + "; ".join(profile["constraints"]))
    return "\n".join(lines)
