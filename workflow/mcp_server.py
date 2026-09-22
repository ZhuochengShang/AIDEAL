"""Optional agent interface over the same portable AIDEAL controller."""
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .preparation import prepared_study_status
from .worktrees import attach

mcp = FastMCP(
    'AIDEAL',
    instructions=(
        'Attach to the user-specified codebase and YAML configuration. '
        'Use the same frozen microtest and puzzle bank for Original, README only, '
        'Alias only, Error hints only and Combined. Attachment creates isolated '
        'branches, not evaluated improvements. Do not claim the adapter or model '
        'evaluation ran from a branch name or a readiness flag. '
        'Keep source-based development diagnosis out of held-out audience prompts.'
    ),
)


@mcp.tool()
def attach_codebase(repository: str, config: str, output: str) -> dict:
    """Create five real branches in a separate local clone; never patch the input checkout."""
    return attach(repository, config, output)


@mcp.tool()
def inspect_study(directory: str) -> dict:
    """Inspect generated preparation records; does not launch evaluation or validate approval."""
    return prepared_study_status(directory)


@mcp.tool()
def operating_instructions() -> str:
    """Read the toolkit's current implementation boundaries and end-to-end instructions."""
    return (Path(__file__).resolve().parents[1] / 'README.md').read_text(encoding='utf-8')


def main():
    mcp.run()


if __name__ == '__main__':
    main()
