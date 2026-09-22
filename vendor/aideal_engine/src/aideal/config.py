"""AIDEAL configuration: one YAML file controls models, paths, languages,
tasks, and run settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("AIDEAL needs PyYAML: pip install pyyaml") from exc


@dataclass
class ModelSpec:
    provider: str
    model: str
    bridge: dict | None = None


@dataclass
class AidealConfig:
    root: Path
    project_name: str
    language: str
    source_globs: list[str]
    public_def_regex: str
    exclude_names: list[str]
    visibility: dict          # optional override of the per-language visibility model
    test_globs: list[str]     # where existing unit tests live (real usage examples)
    surface_filter: str       # intended-API filter: all|documented|non_override|documented_non_override
    # workspace files
    llm_readme: Path
    original_readme: Path | None            # first baseline doc (back-compat / existence check)
    original_readme_files: list[Path]       # all baseline docs (files/dirs/globs expanded)
    notes_to_self: Path
    integration_tasks: Path
    aliases_file: Path
    error_log: Path
    # models
    registry: dict[str, ModelSpec]
    roles: dict[str, str]            # role -> registry key
    # runtime
    runtime_target: str
    runtime: dict
    # checks
    required_sections: list[str]
    comprehension_apis_sampled: int
    comprehension: dict           # optional execute-mode config (scaffold, command, sample data)
    # puzzle
    puzzle: dict
    raw: dict = field(default_factory=dict)

    def original_readme_text(self, limit: int | None = None) -> str:
        """Concatenate all baseline docs (README + extra docs/dirs) with file
        headers. `limit` caps the total characters."""
        parts: list[str] = []
        for p in self.original_readme_files:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            try:
                label = p.relative_to(self.root)
            except ValueError:
                # External codebases/docs are valid project inputs; retain an
                # auditable absolute label when the file is outside cfg.root.
                label = p
            parts.append(f"===== {label} =====\n{t}")
        text = "\n\n".join(parts)
        return text[:limit] if limit else text

    #: roles that silently inherit another role's model when unmapped.
    #: `fixer` (attempts >0 in the comprehension fix loop) defaults to the
    #: audience model — mapping it separately enables the Gemini-as-fixer
    #: benchmark condition without touching the writer.
    _ROLE_FALLBACKS = {"fixer": "audience"}

    def model_for_role(self, role: str) -> ModelSpec:
        key = self.roles.get(role)
        if key is None and role in self._ROLE_FALLBACKS:
            return self.model_for_role(self._ROLE_FALLBACKS[role])
        if key is None or key not in self.registry:
            raise KeyError(f"role '{role}' is not mapped to a registry model (have: {list(self.registry)})")
        return self.registry[key]

    def override_role(self, role: str, value: str) -> None:
        """Point `role` at a model at runtime (CLI `--role role=value`).
        `value` is a registry key, or `provider:model` (e.g.
        `google:gemini-2.5-pro`, `codex:gpt-5.1-codex-max`) registered on
        the fly — benchmark conditions never need a yaml edit."""
        if ":" in value and value not in self.registry:
            provider, model = value.split(":", 1)
            self.registry[value] = ModelSpec(provider=provider, model=model)
        if value not in self.registry:
            raise KeyError(f"--role {role}={value}: not a registry key and not provider:model "
                           f"(have: {list(self.registry)})")
        self.roles[role] = value

    def model_by_name(self, name: str) -> ModelSpec:
        return self.registry[name]


#: extensions accepted into the ORIGINAL-DOCUMENTATION bundle. The bundle is
#: what the audience model reads whole in full-doc mode — binary imagery
#: (PNG/TIFF/SVG) decoded as errors="ignore" mojibake is NOT documentation.
#: Markdown keeps its image REFERENCES;
#: the bytes stay out.
_TEXT_DOC_EXTS = {
    ".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".html",
    # Documentation galleries commonly store executable source rendered
    # alongside prose (Sphinx-Gallery Python, Java/Scala example galleries).
    ".py", ".java", ".scala",
}


def _resolve_readme_sources(root: Path, sources: list[str]) -> list[Path]:
    """Expand each baseline-doc source (a file, a directory, or a glob) into a
    DETERMINISTIC (per-source sorted), de-duplicated, TEXT-ONLY list of files.
    Directories recursively include every extension in ``_TEXT_DOC_EXTS``;
    globs and explicit files use the same filter."""
    import glob as _glob
    found: list[Path] = []
    seen: set[Path] = set()
    for src in sources:
        base = (root / src)
        if base.is_dir():
            matches = sorted(str(p) for p in base.rglob("*")
                             if p.is_file() and p.suffix.lower() in _TEXT_DOC_EXTS)
        elif any(ch in src for ch in "*?["):
            matches = sorted(_glob.glob(str(base), recursive=True))
        else:
            matches = [str(base)]
        for m in matches:
            p = Path(m).resolve()
            if (p.is_file() and p not in seen
                    and p.suffix.lower() in _TEXT_DOC_EXTS):
                seen.add(p); found.append(p)
    return found


def find_config(start: Path | None = None) -> Path | None:
    """Search cwd and up to 3 parents for configs/aideal.yaml."""
    cur = (start or Path.cwd()).resolve()
    for d in [cur, *cur.parents[:3]]:
        cand = d / "configs" / "aideal.yaml"
        if cand.exists():
            return cand
    return None


# --- Layered config (defaults -> adapters -> project) ---------------------
# A project's configs/aideal.yaml is deep-merged ON TOP of framework defaults
# (this package's defaults.yaml) and any adapters it pulls in via `extends:`.
# This keeps per-project files small: they hold only wiring + codebase-specific
# execution config; generic knobs and ecosystem conventions live in the lower
# layers. A full self-contained aideal.yaml still works unchanged — its keys
# simply override the defaults, producing the same resolved config.

DEFAULTS_PATH = Path(__file__).parent / "defaults.yaml"
ADAPTERS_DIR = Path(__file__).parent / "adapters"


def _deep_merge(base: dict, over: dict) -> dict:
    """Recursively merge `over` onto `base`. Dicts merge key-by-key; lists and
    scalars are replaced by the higher layer."""
    out = dict(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _resolve_adapter(name: str, configs_dir: Path) -> Path | None:
    """An `extends:` entry resolves to a file relative to the project's configs/
    dir, else to a named adapter shipped in this package's adapters/ dir."""
    cand = (configs_dir / name).resolve()
    if cand.exists():
        return cand
    fname = name if name.endswith((".yaml", ".yml")) else f"{name}.yaml"
    pkg = (ADAPTERS_DIR / fname)
    return pkg if pkg.exists() else None


def _load_layered(config_path: Path) -> dict:
    """Build the effective raw config: framework defaults, then each adapter in
    `extends:`, then the project file itself (highest precedence)."""
    project_raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    merged: dict = {}
    if DEFAULTS_PATH.exists():
        merged = yaml.safe_load(DEFAULTS_PATH.read_text(encoding="utf-8")) or {}
    for name in project_raw.get("extends", []) or []:
        adapter = _resolve_adapter(name, config_path.parent)
        if adapter is not None:
            merged = _deep_merge(merged, yaml.safe_load(adapter.read_text(encoding="utf-8")) or {})
    return _deep_merge(merged, project_raw)


def load_config(config_path: str | Path | None = None) -> AidealConfig:
    if config_path is None:
        config_path = find_config()
        if config_path is None:
            raise FileNotFoundError(
                "No configs/aideal.yaml found in this directory or its parents. "
                "Run from a project root, pass --config <path>, or run "
                "`python -m aideal.cli init` to scaffold a new project here."
            )
    config_path = Path(config_path).resolve()
    root = config_path.parent.parent  # configs/ -> project root (grail-agent/)
    raw = _load_layered(config_path)

    project = raw.get("project", {})
    cb = raw.get("codebase", {})
    files = raw.get("files", {})
    models = raw.get("models", {})
    runtime = raw.get("runtime", {})
    checks = raw.get("checks", {})

    registry = {
        name: ModelSpec(provider=m["provider"], model=m["model"], bridge=m.get("bridge"))
        for name, m in models.get("registry", {}).items()
    }

    def _file(key: str, default: str) -> Path:
        return (root / files.get(key, default)).resolve()

    # baseline docs: accept a single string or a list of files/dirs/globs
    _orig_raw = files.get("original_readme")
    _orig_sources = ([_orig_raw] if isinstance(_orig_raw, str)
                     else list(_orig_raw) if _orig_raw else [])
    _orig_files = _resolve_readme_sources(root, _orig_sources)

    return AidealConfig(
        root=root,
        project_name=project.get("name", "unknown"),
        language=project.get("language", "Scala"),
        source_globs=cb.get("source_globs", []),
        public_def_regex=cb.get("public_def_regex", r"def\s+([A-Za-z][A-Za-z0-9_]*)"),
        exclude_names=cb.get("exclude_names", []),
        visibility=cb.get("visibility", {}) or {},
        test_globs=cb.get("test_globs", []) or [],
        surface_filter=cb.get("surface_filter", "all") or "all",
        llm_readme=_file("llm_readme", "docs/LLM_readme.md"),
        original_readme=_orig_files[0] if _orig_files else None,
        original_readme_files=_orig_files,
        notes_to_self=_file("notes_to_self", "docs/notes_to_self.md"),
        integration_tasks=_file("integration_tasks", "configs/integration_tasks.yaml"),
        aliases_file=_file("aliases", "aliases/aliases.json"),
        error_log=_file("error_log", "logs/error_log.jsonl"),
        registry=registry,
        roles=models.get("roles", {}),
        runtime_target=runtime.get("target", "local"),
        runtime=runtime,
        required_sections=checks.get("required_sections", ["Goal"]),
        comprehension_apis_sampled=int(checks.get("comprehension_apis_sampled", 5)),
        comprehension=raw.get("comprehension", {}) or {},
        puzzle=raw.get("puzzle", {}),
        raw=raw,
    )


CONFIG_TEMPLATE = """\
# AIDEAL config - scaffolded by `aideal init`. Fill the TODOs.
project:
  name: TODO
  language: TODO        # e.g. Python, Scala

codebase:
  source_globs:
    - "TODO/**/*.py"    # where the public API lives
  test_globs:
    - "TODO/**/*test*.py"   # tests = real usage examples; powers the "tested" intent signal
  public_def_regex: "def\\\\s+([a-zA-Z][A-Za-z0-9_]*)"
  exclude_names: []
  surface_filter: intent_score   # "all" = keep every public def; "intent_score" = keep intended APIs
  intent:
    threshold: 5                 # min evidence score for an API to count as user-intended
    use_llm: true                # author model also flags commonly-used APIs
    weights:
      llm_common: 4              # weight of the LLM "commonly-used" signal
    # If there is no API key or the profile is unfilled, the LLM signal silently
    # degrades to static scoring (tests + docs), so this default is always safe.

files:
  project_profile: configs/project_profile.yaml
  prompts_dir: prompts            # optional overrides; package defaults used if absent
  original_readme:                # baseline doc(s): a path, or a list of files/dirs/globs
    - README.md
    - docs                        # missing paths are ignored; add wiki/doc dirs here
  llm_readme: docs/LLM_readme.md
  notes_to_self: docs/notes_to_self.md
  integration_tasks: configs/integration_tasks.yaml
  aliases: aliases/aliases.json
  error_log: logs/error_log.jsonl

models:
  registry:
    gpt-4o:      { provider: openai, model: gpt-4o }
    gpt-4o-mini: { provider: openai, model: gpt-4o-mini }
  roles:
    author: gpt-4o-mini
    audience: gpt-4o

runtime:
  target: local
  local: {}

checks:
  required_sections:
    - "Goal"
    - "Valid Call Patterns|Valid Access Patterns"
    - "LLM Instruction Prompt"
    - "Prompt Snippet"
    - "Common Failure Modes"
    - "Fix Code Hint"
  comprehension_apis_sampled: 5

puzzle:
  cwd: .
  command: ""           # application-provided runner, see experiments/testbed/runner
  num_puzzles: 5
  num_functions: 4
  seed: 42
  max_fix_rounds: 2
"""


def init_config(directory: Path | None = None) -> Path:
    """Scaffold configs/aideal.yaml in `directory` (default cwd)."""
    root = (directory or Path.cwd()).resolve()
    path = root / "configs" / "aideal.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    return path


def load_tasks(cfg: AidealConfig) -> list[dict]:
    """Read integration_tasks.yaml -> list of {id, language, goal, apis}."""
    if not cfg.integration_tasks.exists():
        return []
    data = yaml.safe_load(cfg.integration_tasks.read_text(encoding="utf-8")) or {}
    return data.get("tasks", [])
