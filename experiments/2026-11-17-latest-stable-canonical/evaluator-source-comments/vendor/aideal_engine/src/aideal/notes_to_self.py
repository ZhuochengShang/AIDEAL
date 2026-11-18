"""notes_to_self.md — the distilled memory from previous rounds.

Records reusable lessons in a compact format so the next generation round
avoids repeating known mistakes:

    issue {{...}} fix {{...}} pattern {{...}}

`distill()` converts repeated error-log records into notes (the
errors -> memory consolidation step). `to_prompt()` returns the notes block
for injection into generation prompts.
"""

from __future__ import annotations

import re
from pathlib import Path

from .error_log import ErrorLog

NOTE_RE = re.compile(
    r"issue\s*\{\{(?P<issue>.*?)\}\}\s*fix\s*\{\{(?P<fix>.*?)\}\}\s*pattern\s*\{\{(?P<pattern>.*?)\}\}",
    re.DOTALL,
)

# single braces in the example so NOTE_RE never matches the header itself
HEADER = "# notes_to_self\n\nDistilled lessons from previous rounds. One line per lesson:\n`issue {...} fix {...} pattern {...}`\n\n"


class NotesToSelf:
    def __init__(self, path: Path):
        self.path = path

    def _ensure(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(HEADER, encoding="utf-8")

    def notes(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [m.groupdict() for m in NOTE_RE.finditer(self.path.read_text(encoding="utf-8"))]

    def add(self, issue: str, fix: str, pattern: str = "") -> bool:
        """Append a note; returns False if an identical issue already exists."""
        issue, fix, pattern = issue.strip(), fix.strip(), pattern.strip()
        if any(n["issue"].strip() == issue for n in self.notes()):
            return False
        self._ensure()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(f"issue {{{{{issue}}}}} fix {{{{{fix}}}}} pattern {{{{{pattern}}}}}\n")
        return True

    def distill(self, error_log: ErrorLog, min_count: int = 2) -> int:
        """Consolidate repeated errors into notes. Returns number added."""
        counts: dict[tuple, int] = {}
        fix_for: dict[tuple, str] = {}
        for e in error_log.entries():
            key = (e.get("function", ""), e.get("error", ""))
            counts[key] = counts.get(key, 0) + 1
            if e.get("suggested_fix_code"):
                fix_for[key] = e["suggested_fix_code"]
        added = 0
        for (fn, err), n in counts.items():
            if n >= min_count and err:
                if self.add(issue=f"{fn}: {err}",
                            fix=fix_for.get((fn, err), "see error log"),
                            pattern=fn):
                    added += 1
        return added

    def to_prompt(self, max_notes: int = 20) -> str:
        notes = self.notes()[:max_notes]
        if not notes:
            return ""
        lines = ["Lessons from previous rounds (do not repeat these mistakes):"]
        for n in notes:
            lines.append(f"- issue: {n['issue'].strip()} | fix: {n['fix'].strip()}")
        return "\n".join(lines)
