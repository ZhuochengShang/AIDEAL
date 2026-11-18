"""Mine existing Scala, Python, and Java test blocks for API usage examples."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig
from .api_discovery import (
    public_api_surface,
)


_TEST_BLOCK_RE = re.compile(r'\btest\s*\(\s*"([^"]*)"\s*\)\s*\{')


_PY_TEST_DEF_RE = re.compile(r"^([ \t]*)def\s+(test_\w+)\s*\(", re.M)


def _iter_test_blocks_py(text: str):
    """pytest style: yield (test_name, body) for each `def test_*(...)`, the body
    being every following line indented deeper than the def (indentation-scoped —
    Python has no braces). Before this, test-example mining fired 0x on Python
    codebases (_TEST_BLOCK_RE is ScalaTest-only; Sedona audit 2026-07-06)."""
    import bisect
    lines = text.splitlines()
    starts, off = [], 0
    for ln in lines:
        starts.append(off)
        off += len(ln) + 1
    for m in _PY_TEST_DEF_RE.finditer(text):
        indent = len(m.group(1).expandtabs())
        i = bisect.bisect_right(starts, m.start()) - 1
        body = [lines[i]]
        for j in range(i + 1, len(lines)):
            ln = lines[j]
            if ln.strip() and (len(ln) - len(ln.lstrip(" \t"))) <= indent:
                break
            body.append(ln)
        yield m.group(2), "\n".join(body)


_JAVA_TEST_RE = re.compile(
    r"@(?:Test|ParameterizedTest)\b[\s\S]*?\b(?:void|public\s+void)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w., ]+)?\{")


def _iter_test_blocks_java(text: str):
    """JUnit style: yield (method_name, body) for each @Test/@ParameterizedTest
    method (brace-balanced from its opening `{`)."""
    for m in _JAVA_TEST_RE.finditer(text):
        open_brace = text.index("{", m.end() - 1)
        depth = 0
        for k in range(open_brace, len(text)):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    yield m.group(1), text[open_brace:k + 1]
                    break


#: per-language test-block miners; default = ScalaTest-style `test("..."){}`.
#: Extend for new languages (the `tested` intent signal + example mining
#: both flow through this table).
_TEST_MINERS = {
    "python": _iter_test_blocks_py,
    "java": _iter_test_blocks_java,
}


def _test_blocks_for(cfg: AidealConfig, text: str):
    """Language-aware test-block iterator (see _TEST_MINERS)."""
    miner = _TEST_MINERS.get(cfg.language.lower(), _iter_test_blocks)
    blocks = list(miner(text))
    # graceful fallback: a Scala repo with JUnit-style tests (or vice versa)
    # still yields examples rather than silently zero.
    if not blocks and miner is not _iter_test_blocks:
        blocks = list(_iter_test_blocks(text))
    if not blocks and miner is not _iter_test_blocks_java:
        blocks = list(_iter_test_blocks_java(text))
    return blocks


def _iter_test_blocks(text: str):
    """Yield (test_name, block_text) for each `test("...") { ... }` (brace-balanced).
    Generic for *Spec/FunSuite-style tests; falls back to nothing if none match."""
    for m in _TEST_BLOCK_RE.finditer(text):
        open_brace = text.index("{", m.end() - 1)
        depth = 0
        for k in range(open_brace, len(text)):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    yield m.group(1), text[open_brace:k + 1]
                    break


def api_test_examples(cfg: AidealConfig, max_per_api: int = 2, max_chars: int = 1400) -> dict[str, list[dict]]:
    """Search the configured test files and index real usage examples by API name.
    Returns {api_name: [{file, test, code}]}. These are compiling, ground-truth
    call patterns the generator/audience can learn from."""
    if not cfg.test_globs:
        return {}
    surface = public_api_surface(cfg)
    index: dict[str, list[dict]] = {}
    for g in cfg.test_globs:
        for path in sorted(globmod.glob(str(cfg.root / g), recursive=True)):
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            rel = str(Path(path).relative_to(cfg.root))
            for tname, block in _test_blocks_for(cfg, text):
                for name in surface:
                    if len(index.get(name, [])) >= max_per_api:
                        continue
                    # match a call/use of the name: `name(` `name[` or `.name`
                    if re.search(rf"\b{re.escape(name)}\s*[\(\[]|\.{re.escape(name)}\b", block):
                        index.setdefault(name, []).append(
                            {"file": rel, "test": tname, "code": block.strip()[:max_chars]})
    return index
