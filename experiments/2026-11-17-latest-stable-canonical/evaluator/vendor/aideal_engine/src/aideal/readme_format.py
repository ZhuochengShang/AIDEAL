"""README entry parsing, section edits, and source-derived entry skeletons."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


API_HEADER_RE = re.compile(r"^## API Test: `([^`]+)`\s*$", re.MULTILINE)


@dataclass
class ApiEntry:
    name: str
    goal: str
    snippet: str
    body: str


def _section_between(body: str, header: str) -> str:
    m = re.search(rf"^### {re.escape(header)}\s*$(.*?)(?=^###? |\Z)", body, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_readme(path: Path) -> list[ApiEntry]:
    if not path.exists():
        return []  # stage-0 codebases have no LLM readme yet
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = list(API_HEADER_RE.finditer(text))
    entries = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        entries.append(ApiEntry(
            name=m.group(1),
            goal=_section_between(body, "Goal"),
            snippet=_section_between(body, "Prompt Snippet"),
            body=body,
        ))
    return entries


def _replace_section(block: str, header: str, content: str) -> str:
    """Replace the content under `### {header}` (up to the next ### or block end).
    Appends the section if it isn't present."""
    pat = re.compile(rf"(###\s+{re.escape(header)}\s*\n)(.*?)(?=\n###\s|\Z)", re.DOTALL)
    if pat.search(block):
        return pat.sub(lambda m: m.group(1) + content.rstrip() + "\n", block, count=1)
    return block.rstrip() + f"\n\n### {header}\n{content}\n"


def _section_has_code(block: str, header: str) -> bool:
    """True if the `### {header}` section already holds a REAL fenced code example —
    a ``` block whose content isn't just the skeleton `TODO` placeholder. Drives
    augment's `only_missing` gap-fill: backfill ONLY entries lacking example/fix code,
    leaving curated or already-generated code untouched."""
    body = _section_between(block, header)
    if not body:
        return False
    for m in re.finditer(r"```[^\n]*\n(.*?)```", body, re.DOTALL):
        inner = m.group(1).strip()
        if inner and not inner.upper().startswith("TODO"):
            return True
    return False


def _params_block(params: list[dict]) -> str:
    """Pre-fill a Parameters list from the structured signature (names/types/
    defaults are facts; meanings are TODO for the author model)."""
    if not params:
        return "_None._"
    out = []
    for p in params:
        t = f" (`{p['type']}`)" if p.get("type") else ""
        d = f", default `{p['default']}`" if p.get("default") else ""
        out.append(f"- `{p['name']}`{t}{d}: TODO — what this argument means / expected values.")
    return "\n".join(out)


def _entry_skeleton(name: str, lang: str, recs: list[dict]) -> str:
    """Build a doc-entry skeleton with the factual Signature / Parameters /
    Output pre-filled from the surface; Goal / Input / examples left as TODO
    for the author model. `recs` = all definition sites for this name."""
    primary = max(recs, key=lambda r: len(r["params"]))     # richest overload
    sigs = list(dict.fromkeys((r["signature"] or name) for r in recs))
    sig_block = "\n".join(sigs)
    src = f"{primary['file']}:{primary['line']}"
    if len(recs) > 1:
        src += f"  (+{len(recs) - 1} more definition site/overload)"
    doc = primary.get("description") or ""
    doc_line = f"\n_Source doc:_ {doc}\n" if doc else ""
    ret = primary["returns"] or "unspecified"
    return f"""## API Test: `{name}`

### Signature
```{lang}
{sig_block}
```
_Source: {src}_
{doc_line}
### Goal
TODO: one sentence describing what `{name}` does, in the project's domain terms.

### Parameters
{_params_block(primary['params'])}

### Input
TODO: the data, file formats, and preconditions the caller must provide.

### Output
Returns `{ret}` — TODO: what the value represents and its format.

### Valid Call Patterns
```{lang}
TODO
```

### LLM Instruction Prompt
- TODO: rules an LLM must follow when calling `{name}`.

### Prompt Snippet
```text
TODO
```

### Common Failure Modes
- TODO

### Fix Code Hint
```{lang}
TODO
```
"""
