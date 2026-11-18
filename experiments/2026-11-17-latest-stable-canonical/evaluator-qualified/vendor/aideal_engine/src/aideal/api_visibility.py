"""Language visibility rules and source-definition scanning."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig


# --- Visibility models -------------------------------------------------------
# No single rule works across languages, so each language picks one of four
# modes. `deny`  = public by default, drop defs carrying a private marker
# (Scala/Java/C++/C#/TS/Kotlin). `allow` = private by default, keep only defs
# carrying an export marker (Rust `pub`, JS `export`). `case` = exported when
# the name starts uppercase (Go). `convention` = no keyword; the universal
# `_`-prefix rule below is the only filter (Python). Override per project with a
# `codebase.visibility` block in aideal.yaml.
_VISIBILITY_DEFAULTS: dict[str, dict] = {
    "scala":      {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b"]},
    "java":       {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b"]},
    "kotlin":     {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b", r"\binternal\b"]},
    "typescript": {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b", r"#"]},
    "c#":         {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b", r"\binternal\b"]},
    "csharp":     {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b", r"\binternal\b"]},
    "c++":        {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b"]},
    "cpp":        {"mode": "deny",  "private": [r"\bprivate\b", r"\bprotected\b"]},
    "rust":       {"mode": "allow", "public":  [r"\bpub\b"]},
    "go":         {"mode": "case"},
    "python":     {"mode": "convention"},
    "javascript": {"mode": "convention"},
}


def visibility_model(cfg: AidealConfig) -> dict:
    """Resolve the visibility model: explicit config overrides the language default."""
    if cfg.visibility:
        return cfg.visibility
    return _VISIBILITY_DEFAULTS.get(cfg.language.lower(), {"mode": "convention"})


def _is_public(name: str, prefix: str, model: dict) -> bool:
    """`prefix` is the text on the def line BEFORE the matched name (the modifiers),
    with any NON-PUBLIC enclosing-container modifiers prepended by `_iter_defs`
    (a def inside `private[pkg] object X` is not callable from outside either)."""
    if name.startswith("_"):          # universal convention rule (Python/JS internals)
        return False
    mode = model.get("mode", "convention")
    if mode == "deny":
        return not any(re.search(p, prefix) for p in model.get("private", []))
    if mode == "allow":
        return any(re.search(p, prefix) for p in model.get("public", []))
    if mode == "case":
        return name[:1].isupper()
    return True                       # convention: only the `_` rule applies


# Container declarations for brace-scoped languages (Scala/Java/Kotlin/C#/...).
# `mods` = everything before the container keyword on that line (modifiers).
_CONTAINER_DECL_RE = re.compile(
    r"^(?P<mods>[^={}]*?)\b(?:case\s+)?(?:class|object|trait|interface|enum|record)\s+\w+")


# Scoped Scala modifiers too: `private[raptor]`, `protected[davinci]`.
_NONPUBLIC_MOD_RE = re.compile(r"\b(?:private|protected)\b(?:\[[^\]]*\])?")


def _container_context(lines: list[str]) -> list[str]:
    """Per-line NON-PUBLIC modifier text of the enclosing containers.

    ctx[i] = space-joined private/protected modifiers of every container
    enclosing line i ('' when the whole chain is public). Members of a
    `private[pkg] object Helper { ... }` are unreachable from user code even
    when the def line itself carries no modifier — the observed leak class
    (docfix not-testable verdicts: compress protected[raptor], createRings
    private[davinci]). Heuristic brace tracking; braces inside string
    literals/comments are not parsed (acceptable for surface estimation)."""
    ctx: list[str] = [""] * len(lines)
    stack: list[tuple[int, str]] = []   # (depth after the container's `{`, mods)
    depth = 0
    pending: tuple[int, str] | None = None   # container decl awaiting its `{`
    for i, line in enumerate(lines):
        ctx[i] = " ".join(m for _, m in stack if m)
        decl = _CONTAINER_DECL_RE.match(line)
        if decl:
            mods = " ".join(_NONPUBLIC_MOD_RE.findall(decl.group("mods")))
            pending = (depth, mods)
        for ch in line:
            if ch == "{":
                if pending is not None and pending[0] == depth:
                    stack.append((depth + 1, pending[1]))
                    pending = None
                else:
                    stack.append((depth + 1, ""))   # def body / match block / ...
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
                while stack and stack[-1][0] > depth:
                    stack.pop()
    return ctx


def _exclude_path_patterns(cfg: AidealConfig) -> list:
    """codebase.exclude_path_patterns — regexes matched against the project-
    relative POSIX path of each source file; matches are dropped from the
    surface entirely. Use for modules that are source-visible but not user
    API (e.g. a `commontest/` test-scaffolding module)."""
    pats = (cfg.raw.get("codebase", {}) or {}).get("exclude_path_patterns", []) or []
    return [re.compile(p) for p in pats]


def _iter_defs(cfg: AidealConfig):
    """Yield (name, prefix, file_path, lineno, line) for every matched def.

    `prefix` is everything on the line BEFORE the matched NAME (so modifier
    regexes see `private`/`protected`/`override` even when the project's
    def-regex is anchored at ^), with any non-public enclosing-container
    modifiers prepended. NOTE: a lookahead like `^\\s*(?!private\\b)` in the
    def regex is NOT a reliable visibility filter — `\\s*` backtracks one
    space and the lookahead passes on any indented def; visibility belongs to
    the visibility model, not the regex."""
    pattern = re.compile(cfg.public_def_regex)
    excl = _exclude_path_patterns(cfg)
    deny_mode = visibility_model(cfg).get("mode") == "deny"
    for g in cfg.source_globs:
        for path in globmod.glob(str(cfg.root / g), recursive=True):
            rel = str(Path(path).relative_to(cfg.root)).replace("\\", "/") \
                if str(path).startswith(str(cfg.root)) else str(path).replace("\\", "/")
            if any(p.search(rel) for p in excl):
                continue
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
            ctx = _container_context(lines) if deny_mode else None
            for i, line in enumerate(lines):
                for m in pattern.finditer(line):
                    name = m.group(1)
                    # text before the NAME (not before the whole match): the
                    # modifiers survive even under a ^-anchored project regex.
                    prefix = line[:m.start(1)]
                    if ctx is not None and ctx[i]:
                        prefix = ctx[i] + " " + prefix
                    yield name, prefix, path, i, line
