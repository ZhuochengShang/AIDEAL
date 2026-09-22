"""AIDEAL MCP server — exposes the doc-test pipeline as agent-discoverable tools.

Thin wrapper over the same functions the CLI calls; one wrapper covers every
MCP-speaking client (Claude Code, Cursor, Windsurf, ...).

Run:  aideal-mcp                      (stdio transport)
Config resolution: AIDEAL_CONFIG env var, else configs/aideal.yaml found
upward from the server's working directory.

Claude Code registration example:
  claude mcp add aideal -- aideal-mcp
"""

from __future__ import annotations

import os

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise ImportError("MCP support needs the `mcp` package: pip install 'grail-agent[mcp]'") from exc

from .config import load_config

mcp = FastMCP(
    "aideal",
    instructions=(
        "AIDEAL tests and improves how LLM-ready a codebase is. Typical flow: "
        "check_profile -> form_check / completeness_check (static) -> "
        "comprehension_check (LLM) -> puzzle_check (execution). Before "
        "generating code against this codebase, call known_mistakes to avoid "
        "repeating logged failures."
    ),
)


def _cfg():
    return load_config(os.environ.get("AIDEAL_CONFIG") or None)


@mcp.tool()
def check_profile() -> dict:
    """Project intake status: which required profile fields are still missing."""
    from .profile import load_profile, missing_fields, profile_path
    cfg = _cfg()
    prof = load_profile(cfg)
    return {"path": str(profile_path(cfg)), "missing_fields": missing_fields(prof),
            "ready": not missing_fields(prof)}


@mcp.tool()
def form_check() -> dict:
    """Structural check: does every API entry in LLM_readme.md have the required sections?"""
    from .doc_checks import form_check as run
    return run(_cfg())


@mcp.tool()
def completeness_check() -> dict:
    """Coverage check: which public functions of the codebase have no doc entry?"""
    from .doc_checks import completeness_check as run
    return run(_cfg())


@mcp.tool()
def comprehension_check(sample: int = 5, doc: str = "aideal",
                        class_context: bool | None = None) -> dict:
    """Readme unit test: audience model writes code from the docs alone; author model grades.
    doc='original' uses the project's pre-existing README as the only context.
    class_context=True uses the INDEX-FIRST read path (prefix each API with its catalogue
    class header: receiver + a verified sibling's call pattern); None -> config default."""
    from .doc_checks import comprehension_check as run
    return run(_cfg(), sample=sample, doc_source=doc, class_context=class_context)


@mcp.tool()
def puzzle_check(dry_run: bool = True) -> dict:
    """Integration check: compose sampled APIs into tasks, generate, execute, score.
    dry_run=True previews puzzles without LLM/execution cost."""
    from .doc_checks import puzzle_check as run
    return run(_cfg(), dry_run=dry_run)


@mcp.tool()
def readme_status(generate: bool = False) -> dict:
    """Find the LLM readme, or create a skeleton (generate=True fills entries via the author model)."""
    from .readme_agent import find_or_create
    return find_or_create(_cfg(), generate=generate)


@mcp.tool()
def known_mistakes() -> str:
    """Compact list of previously logged failures + distilled lessons.
    CALL THIS BEFORE GENERATING CODE against the codebase, and include it in your reasoning."""
    from .error_log import ErrorLog
    from .notes_to_self import NotesToSelf
    cfg = _cfg()
    parts = [NotesToSelf(cfg.notes_to_self).to_prompt(), ErrorLog(cfg.error_log).to_prompt()]
    return "\n\n".join(p for p in parts if p) or "No logged mistakes yet."


@mcp.tool()
def log_failure(function: str, error: str, task: str = "", root_cause: str = "",
                suggested_fix_code: str = "", step: str = "code-test") -> dict:
    """Record a code-generation failure you encountered, so future runs avoid it."""
    from .error_log import ErrorLog
    cfg = _cfg()
    return ErrorLog(cfg.error_log).append(
        step=step, language=cfg.language, task=task, status="fail",
        function=function, error=error, root_cause=root_cause,
        suggested_fix_code=suggested_fix_code)


@mcp.tool()
def alias_suggestions() -> list:
    """Alias candidates mined from logged hallucinated names (what models EXPECT APIs to be called)."""
    from .error_log import ErrorLog
    return ErrorLog(_cfg().error_log).suggest_aliases()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
