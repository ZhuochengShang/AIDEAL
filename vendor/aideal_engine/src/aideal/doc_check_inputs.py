"""Scaffold insertion, fixture discovery, and codebase-derived input/receiver hints."""
from __future__ import annotations

import re
from .config import AidealConfig


_FIXTURE_TYPES = {
    ".tif": "raster_tif", ".tiff": "raster_tif",
    ".geojson": "vector_geojson",
    ".shp": "vector_shapefile",
    ".csv": "table_csv",
    ".tsv": "table_tsv",
    ".parquet": "table_parquet",
    ".wkt": "vector_wkt",
    ".kml": "vector_kml",
    ".gpx": "vector_gpx",
    ".json": "vector_geojson",
}

_SUFFIXES_FOR_TYPE: dict[str, set[str]] = {}

for _suf, _name in _FIXTURE_TYPES.items():
    _SUFFIXES_FOR_TYPE.setdefault(_name, set()).add(_suf)


def _fill_scaffold(scaffold: str, snippet: str, region: list[str], placeholders: dict) -> str:
    """Insert the snippet into the scaffold's API-test region and substitute
    {{KEY}} placeholders (sample-data paths). Generic: region markers and
    placeholder keys all come from config, nothing GRAIL-specific is hardcoded."""
    text = scaffold
    if region and len(region) == 2 and region[0] in text and region[1] in text:
        pre, _, rest = text.partition(region[0])
        _, _, post = rest.partition(region[1])
        # match the marker's indentation (required for Python scaffolds, where the
        # region sits inside a function body; harmless formatting for brace languages)
        indent = pre.rpartition("\n")[2]
        if indent.strip() == "":
            snippet = "\n".join((indent + l) if l.strip() else l
                                for l in snippet.splitlines())
        text = f"{pre}{region[0]}\n{snippet}\n{indent}{region[1]}{post}"
    else:                                  # no region markers: append the snippet
        text = text + "\n" + snippet
    for key, val in (placeholders or {}).items():
        text = text.replace("{{" + key + "}}", str(val))
    return text


def _strip_fences(text: str, *, strip_imports: bool = False) -> str:
    """Remove markdown code fences / language tags the model may emit despite
    instructions, so the snippet is pure code. When the scaffold owns imports,
    callers can also drop model-generated import lines to avoid stale/wrong
    imports shadowing curated scaffold imports."""
    t = text.strip()
    if "```" in t:
        # keep the content of the first fenced block if present, else strip fences
        import re as _re
        m = _re.search(r"```[a-zA-Z]*\n(.*?)```", t, _re.DOTALL)
        t = (m.group(1) if m else
             t.replace("```scala", "").replace("```python", "").replace("```", ""))
    if strip_imports:
        t = "\n".join(
            line for line in t.strip().splitlines()
            if not line.lstrip().startswith("import ")
        )
    return t.strip()


def _kind_of(suffix: str) -> str | None:
    """raster / vector / table for a file extension (the *_dir kind)."""
    name = _FIXTURE_TYPES.get(suffix.lower())
    return name.split("_")[0] if name else None


def _validate_sample_data(sample_data: dict[str, str]) -> list[str]:
    """Sanity-check every typed input path BEFORE it is compiled into the scaffold, so a
    mis-pinned or missing `sample_data` entry fails LOUDLY and specifically here —
    `sample_data.raster_tif expects .tif/.tiff but path has '.shp'` — instead of
    surfacing many steps later as an opaque Scala runtime error the fix-loop can't parse.

    Only bindings whose NAME encodes a type (the `_FIXTURE_TYPES` convention:
    raster_tif, vector_shapefile, table_csv, ...) are type-checked; custom names and
    `output_dir` are exempt (existence-only where sensible). `*_dir` bindings must be
    directories. Returns human-readable warning lines (empty = all inputs look right)."""
    import os
    warns: list[str] = []
    for name, path in sample_data.items():
        if name == "output_dir":                       # an output target, may not exist yet
            continue
        local = str(path).split("://", 1)[-1]          # strip file:// for on-disk checks
        exists = os.path.exists(local)
        if name.endswith("_dir"):                       # folder-of-data binding
            if exists and not os.path.isdir(local):
                warns.append(f"sample_data.{name} should be a directory but is a file: {local}")
            elif not exists:
                warns.append(f"sample_data.{name} directory not found: {local}")
            continue
        expected = _SUFFIXES_FOR_TYPE.get(name)         # None -> custom name, skip type check
        if expected and not os.path.isdir(local):        # a dir dataset (parquet/, tiles/) has no file ext
            suf = os.path.splitext(local)[1].lower()
            if suf not in expected:
                warns.append(
                    f"sample_data.{name} expects {'/'.join(sorted(expected))} "
                    f"but path has '{suf or '(no extension)'}': {local}")
        if not exists:
            warns.append(f"sample_data.{name} file not found: {local}")
    return warns


def _discover_fixtures(cfg: AidealConfig, ex: dict) -> dict[str, str]:
    """Convention over config: when `sample_data` isn't set, build the typed
    catalog by scanning `fixtures_dir` (default 'fixtures/').

      top-level FILES  -> typed file bindings  (raster_tif, vector_geojson, ...)
      top-level FOLDERS -> typed *_dir bindings (raster_dir, vector_dir,
                           table_dir), keyed by the data they contain — for
                           folder-of-tiles / multi-file datasets.

    First file/folder of each type wins. Lets a user drop sample files OR data
    folders in fixtures/ instead of authoring the catalog by hand."""
    sub = ex.get("fixtures_dir", "fixtures")
    root = (cfg.root / sub)
    found: dict[str, str] = {}
    if not root.is_dir():
        return found
    for p in sorted(root.iterdir()):
        if p.is_file():                                   # single-file inputs
            name = _FIXTURE_TYPES.get(p.suffix.lower())
            if name:
                found.setdefault(name, str(p.resolve()))
        elif p.is_dir():                                  # folder-of-data inputs
            kinds = {k for f in p.rglob("*") if f.is_file()
                     for k in (_kind_of(f.suffix),) if k}
            for kind in sorted(kinds):
                found.setdefault(f"{kind}_dir", str(p.resolve()))
    return found


def _base_type(t: str) -> str:
    """Head type name, generics and package path stripped:
    'RDD[ITile[T]]' -> 'RDD', 'JavaRasterRDD[T]' -> 'JavaRasterRDD',
    'edu.ucr...cg.SpatialRDD' -> 'SpatialRDD', '' -> ''."""
    t = (t or "").strip().split("[")[0].strip()
    m = re.match(r"[A-Za-z_][\w.]*", t)
    return m.group(0).split(".")[-1] if m else ""


def _consumed_type_counts(cfg: AidealConfig) -> dict:
    """How many public defs accept each base type as a PARAMETER — i.e. what the
    library's operations actually need loaded, weighted by demand. A reader whose
    return type has count 0 feeds nothing (a shadow reader, e.g. a Java* wrapper);
    a high count means many ops consume it. Codebase-agnostic: no hardcoded names."""
    from collections import Counter
    from .readme_agent import public_api_details
    c: Counter = Counter()
    for d in public_api_details(cfg):
        if d.get("visibility") == "public":
            for p in (d.get("params") or []):
                b = _base_type(p.get("type", ""))
                if b:
                    c[b] += 1
    return dict(c)


def _useful_readers(names: list, ret_of: dict, counts: dict) -> list:
    """Order reader NAMES by how many documented ops consume each reader's return
    type (desc); drop readers whose return type is consumed by nothing. Returns []
    when there's no type signal, so the caller falls back to the raw candidates —
    this is what makes the Scala mixin reader (return feeds many ops) beat a Java
    wrapper (return feeds none) on a name collision, with no 'Java' rule."""
    scored = [(counts.get(ret_of.get(n, ""), 0), n) for n in names]
    return [n for s, n in sorted(scored, key=lambda sn: -sn[0]) if s > 0]


def _drop_unconsumed_lines(code: str, counts: dict) -> str:
    """Belt-and-suspenders: drop any generated `val x: T = ...` whose type T is
    consumed by no documented op (e.g. the model still reached for a Java wrapper)."""
    if not counts:
        return code
    kept = []
    for ln in code.splitlines():
        m = re.match(r"\s*val\s+\w+\s*:\s*([^=]+?)\s*=", ln)
        if m and _base_type(m.group(1)) and counts.get(_base_type(m.group(1)), 0) == 0:
            continue
        kept.append(ln)
    return "\n".join(kept).strip()


def _resolve_preamble(cfg: AidealConfig, ex: dict, sample_data: dict) -> str:
    """Return the typed-input preamble. `preamble: auto` LLM-generates it ONCE
    (cached to docs/preamble.scala) from the codebase's own documented reader
    APIs — so NO human writes Scala. A literal string is used as-is (still
    supported). Any failure (no key/profile) degrades to '' so the model just
    writes its own I/O guided by io_hints.

    Hardened grounding: readers are ranked by how many documented ops CONSUME their
    return type, shadow readers (return type consumed by nothing — the classic
    JavaRasterRDD/JavaSpatialRDD wrappers) are dropped, the model is told the target
    consumed types explicitly, and any generated line binding to an unconsumed type
    is filtered out. This is the general fix for the reader name-collision that made
    `auto` load Java wrappers and force snippets to invent .toRDD/.toRasterRDD."""
    raw = (ex.get("preamble", "") or "")
    if raw.strip().lower() != "auto":
        return raw.strip()
    cache = cfg.llm_readme.parent / "preamble.scala"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    try:
        from .llm import invoke_text
        from .readme_agent import parse_readme, public_api_details
        from .profile import require_profile
        require_profile(cfg)
        counts = _consumed_type_counts(cfg)
        ret_of = {d["name"]: _base_type(d.get("returns", "")) for d in public_api_details(cfg)}
        cands = [e for e in parse_readme(cfg.llm_readme)
                 if re.search(r"read|geoTiff|geojson|load|shapefile|spatialFile|wkt|import", e.name, re.I)]
        useful_names = _useful_readers([e.name for e in cands], ret_of, counts)
        by_name = {e.name: e for e in cands}
        readers = ([by_name[n] for n in useful_names] or cands)[:8]
        target_set = sorted({ret_of.get(e.name, "") for e in readers if ret_of.get(e.name)})
        targets = ", ".join(target_set) or "the library's core input types"
        kinds = ", ".join(sorted(sample_data))
        system = (f"You write {cfg.language} that loads sample inputs into typed variables, "
                  "using ONLY the reader APIs documented below. Output only code, no fences, "
                  "one `val <name>: <Type> = <reader>(<pathVar>)` per usable input. Load into the "
                  f"types the library's operations CONSUME ({targets}); do NOT use a reader that "
                  "returns a type not in that list (e.g. a Java* wrapper the operations don't accept).")
        user = (f"Path variables in scope: {kinds}\n\nTarget consumed types: {targets}\n\n"
                "Documented reader APIs:\n" + "\n\n".join(e.body for e in readers)
                + "\n\nWrite the load statements.")
        code = invoke_text(cfg.model_for_role("author"), system, user).strip()
        code = re.sub(r"^```\w*\n?|```$", "", code, flags=re.MULTILINE).strip()
        code = _drop_unconsumed_lines(code, counts)
        if code:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(code, encoding="utf-8")
        return code
    except Exception:
        return ""


def _resolve_io_hints(cfg: AidealConfig, ex: dict, sample_data: dict) -> str:
    """Return the I/O cheat-sheet. `io_hints: auto` LLM-generates it ONCE (cached
    to docs/io_hints.txt) from the codebase's own documented reader/writer APIs —
    so NO human writes it. A literal string is used as-is. Degrades to '' on any
    failure (no key/profile)."""
    raw = (ex.get("io_hints", "") or "")
    if raw.strip().lower() != "auto":
        return raw.strip()
    cache = cfg.llm_readme.parent / "io_hints.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    try:
        from .llm import invoke_text
        from .readme_agent import parse_readme, public_api_details
        from .profile import require_profile
        require_profile(cfg)
        # rank reader/writer entries by how many documented ops consume their return
        # type (central readers like `shapefile` float up) BEFORE the cap, so a
        # high-index-but-central reader isn't truncated away — the bug that made
        # io_hints miss `shapefile` (past the first 12) and always suggest geojson.
        counts = _consumed_type_counts(cfg)
        ret_of = {d["name"]: _base_type(d.get("returns", "")) for d in public_api_details(cfg)}
        cand = [e for e in parse_readme(cfg.llm_readme)
                if re.search(r"read|write|save|load|geoTiff|geojson|shapefile|join", e.name, re.I)]
        cand.sort(key=lambda e: -counts.get(ret_of.get(e.name, ""), 0))
        entries = [e.body for e in cand[:12]]
        system = (f"From the documented APIs below, write a SHORT I/O cheat-sheet for a coder using this "
                  f"{cfg.language} library: how to load each input type, how to write output, and any "
                  "static-object-vs-instance-method gotchas. 4-6 concrete lines with real call forms. No fences.")
        user = "Documented APIs:\n\n" + "\n\n".join(entries)
        txt = invoke_text(cfg.model_for_role("author"), system, user).strip()
        if txt:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(txt, encoding="utf-8")
        return txt
    except Exception:
        return ""


def _execute_sample_data(cfg: AidealConfig, ex: dict) -> tuple[dict[str, str], str, list[str]]:
    """Resolve sample-data bindings for prompts/scaffolds. Uses the configured
    `sample_data` if present; otherwise auto-discovers a `fixtures/` folder.
    Always provides an `output_dir` binding so write APIs have a target.

    Returns (sample_data, available_inputs, warnings). `warnings` flags typed inputs
    whose path is missing or whose extension contradicts the binding's declared type
    (see _validate_sample_data); they're also echoed to stderr so a mis-pinned input is
    obvious on the console, not buried in a downstream compile/runtime failure."""
    def _resolve(v):
        if isinstance(v, dict):
            package = v.get("package")
            resource = v.get("resource")
            if not package or not resource:
                raise ValueError("sample_data mapping requires both 'package' and 'resource'")
            from importlib.resources import files
            target = files(str(package)).joinpath(str(resource))
            if not target.is_file():
                raise FileNotFoundError(
                    f"package resource not found: {package}:{resource}")
            return str(target)
        v = str(v)
        return str((cfg.root / v).resolve()) if (not v.startswith("/") and "/" in v) else v

    use_uri = ex.get("local_uris", True)

    def _as_uri(p):
        p = str(p)
        if "://" in p:
            return p
        return f"file://{p}" if (use_uri and p.startswith("/")) else p

    # fixtures auto-discovery is the base; explicit `sample_data` entries OVERRIDE
    # per binding — so you can pin just raster_tif and let geojson/csv auto-fill.
    configured = dict(_discover_fixtures(cfg, ex))
    configured.update(ex.get("sample_data", {}) or {})
    configured.setdefault("output_dir", ex.get("output_dir", "/tmp/aideal_apitest_out"))
    sample_data = {k: _as_uri(_resolve(v)) for k, v in configured.items()}
    available_inputs = "\n".join(f"- {k} = {p}" for k, p in sample_data.items()) or "(none configured)"
    # type/existence check on the input paths (raster_tif must be a .tif, etc.) so a
    # bad binding is caught here, not as an opaque Scala error deep in the run.
    warnings = _validate_sample_data(sample_data)
    if warnings:
        import sys
        for w in warnings:
            sys.stderr.write(f"  [sample_data] WARNING: {w}\n")
        sys.stderr.flush()
    return sample_data, available_inputs, warnings


def _owner_map(cfg: AidealConfig) -> dict:
    """name -> (owner_type, kind). owner_type is the class/object that DEFINES the
    function (Scala's one-top-level-type-per-file convention: the source file stem).
    kind is 'static' when that type is declared `object <stem>` and NOT also a
    class/trait (call as `Owner.method(...)`), else 'instance' (needs a receiver of
    type Owner: `val r: Owner = ...; r.method(...)`).

    This is the receiver TYPE the flat doc erases into a bare `value.method`, which
    is what sends a snippet calling the method on the wrong type (e.g. `area` on
    IFeature instead of its owner LiteGeometry). Same class grouping `organize`
    already uses — reused here to type the receiver."""
    import os
    from .readme_agent import public_api_details
    file_kind: dict[str, str] = {}
    owners: dict[str, tuple] = {}
    for d in public_api_details(cfg):
        f = d.get("file", "")
        if not f.endswith(".scala"):
            continue
        stem = os.path.basename(f)[:-6]
        if f not in file_kind:
            try:
                txt = (cfg.root / f).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                txt = ""
            has_object = bool(re.search(rf"^\s*(?:final\s+|case\s+)?object\s+{re.escape(stem)}\b", txt, re.M))
            has_type = bool(re.search(
                rf"^\s*(?:final\s+|sealed\s+|abstract\s+|case\s+)?(?:class|trait)\s+{re.escape(stem)}\b", txt, re.M))
            file_kind[f] = "static" if (has_object and not has_type) else "instance"
        owners[d["name"]] = (stem, file_kind[f])
    return owners


def _receiver_hint(entry_name: str, owner_map: dict) -> str:
    """Render the receiver-typing instruction for the snippet-writer, from _owner_map."""
    own = owner_map.get(entry_name)
    if not own:
        return ""
    typ, kind = own
    if kind == "static":
        return f"`{entry_name}` is a STATIC method on object `{typ}` — call it as `{typ}.{entry_name}(...)`."
    return (f"`{entry_name}` is an INSTANCE method on `{typ}` — you need a value of type `{typ}` to "
            f"call it on (obtain one from a preloaded input, or from a sibling method that returns / "
            f"constructs a `{typ}`), then call `.{entry_name}` on it. Do NOT call it on an unrelated type.")
