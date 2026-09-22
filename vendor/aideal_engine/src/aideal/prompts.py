"""Prompt loader: prompts live as .md files, not inline strings.

Prompts are experimental variables — swapping `prompts_dir` in aideal.yaml
swaps the whole prompt set for an ablation, the same way `--seed` reproduces
puzzles.

File format: a `SYSTEM:` block then a `USER:` block, with {placeholders}.

    load(cfg, "aideal/comprehension_write", api_body=..., api_name=...)
    -> (system, user)
"""

from __future__ import annotations

from pathlib import Path

from .config import AidealConfig
from .profile import project_context, load_profile


DEFAULT_PROMPTS = Path(__file__).resolve().parent / "default_prompts"


def prompts_dir(cfg: AidealConfig) -> Path:
    sub = cfg.raw.get("files", {}).get("prompts_dir", "prompts")
    return (cfg.root / sub).resolve()


def load(cfg: AidealConfig, name: str, **kwargs) -> tuple[str, str]:
    """Read prompts/<name>.md, fill placeholders, return (system, user).

    Resolution order: the project's prompts dir (so prompt ablations work),
    then the defaults shipped inside the package (so pip-installed users
    work out of the box).

    `{project_context}`, `{project_name}`, `{language}`, and `{constraints}`
    are auto-filled from the project profile; other placeholders come from
    kwargs.
    """
    path = prompts_dir(cfg) / f"{name}.md"
    if not path.exists():
        path = DEFAULT_PROMPTS / f"{name}.md"
    text = path.read_text(encoding="utf-8")

    profile = load_profile(cfg)
    kwargs.setdefault("project_context", project_context(profile))
    kwargs.setdefault("project_name", profile.get("project", {}).get("name", cfg.project_name))
    kwargs.setdefault("language", profile.get("project", {}).get("language", cfg.language))
    kwargs.setdefault("constraints", "\n".join(f"- {c}" for c in profile.get("constraints", [])) or "- none")

    if "USER:" not in text:
        raise ValueError(f"{path} must contain a USER: block")
    system_part, user_part = text.split("USER:", 1)
    system = system_part.replace("SYSTEM:", "", 1).strip()
    user = user_part.strip()
    return system.format(**kwargs), user.format(**kwargs)
