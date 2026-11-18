"""Build the configured audience scaffold and resolve its available imports."""
from __future__ import annotations

import glob as globmod
import re
from pathlib import Path
from .config import AidealConfig
from .api_discovery import (
    public_api_details,
)


_SCAFFOLD_FRAME = """// AIDEAL API-test scaffold — AUTO-GENERATED from the API surface.
// Run via: spark-shell --jars <uberjar> -i <thisfile>
// spark-shell provides `sc` (SparkContext) and `spark` (SparkSession).
// The generated snippet is spliced between API_TEST_START / END and may use
// the in-scope bindings: sc, inputA, inputB, output.

{imports}

// Compiled form (scalac + spark-submit --class GeoJobMain). This is the proven
// path: an implicit class like RaptorMixin's sc.geoTiff resolves when compiled
// inside an object, but NOT in the spark-shell -i REPL.
object GeoJob {
  def run(sc: SparkContext): Unit = {
    // Alias: LLM-authored snippets frequently reach for `sparkContext` (the
    // SparkSession accessor name) rather than the harness binding `sc`. Expose
    // both so a correct call doesn't fail on the binding name alone.
    val sparkContext = sc
    // Typed sample inputs (from comprehension.execute.sample_data). Use the
    // one(s) whose type matches the API's parameters.
    // AIDEAL_DATA_BINDINGS

    // TODO API_TEST_START
    // (generated snippet inserted here)
    // TODO API_TEST_END
  }
}

object GeoJobMain {
  def main(args: Array[String]): Unit = {
    val spark = SparkSession.builder().appName("ApiTest").master("local[*]").getOrCreate()
    try {
      GeoJob.run(spark.sparkContext)
      println("__DONE__ object=GeoJob")
    } catch {
      case t: Throwable =>
        Console.err.println("__RUN_ERR__ " + t.getClass.getName + ": " + t.getMessage)
        t.printStackTrace()
    } finally {
      spark.stop()
    }
  }
}
"""


# Always-needed runtime imports the source files may not declare themselves.
_SCAFFOLD_BASE_IMPORTS = [
    "import org.apache.spark.SparkContext",
    "import org.apache.spark.sql.{SparkSession, DataFrame, Row}",
    "import org.apache.spark.rdd.RDD",
]


def _available_packages(cfg: AidealConfig) -> set[str]:
    """Packages actually present in the jars the scaffold compiles against
    (comprehension.execute.jars + uberjar). Used to drop wildcard imports for
    packages not on the classpath (e.g. internal `jhdf`) that break compilation."""
    import zipfile
    ex = (cfg.comprehension or {}).get("execute", {}) if cfg.comprehension else {}
    jar_globs = []
    if ex.get("jars"):
        jar_globs.append(str(ex["jars"]))
    if ex.get("uberjar"):
        bc = cfg.root / ex.get("build_cwd", ".")
        jar_globs.append(str(bc / ex["uberjar"]))
    jars = []
    for jg in jar_globs:
        jars += globmod.glob(jg if jg.startswith("/") else str(cfg.root / jg))
    # also the Spark jars (on the compile classpath) so org.apache.spark.* survives
    try:
        import os as _os
        import pyspark as _pyspark
        jars += globmod.glob(_os.path.join(_os.path.dirname(_pyspark.__file__), "jars", "*.jar"))
    except Exception:
        pass
    pkgs: set[str] = set()
    for jar in jars:
        try:
            for n in zipfile.ZipFile(jar).namelist():
                if n.endswith(".class") and "/" in n:
                    pkgs.add(n.rsplit("/", 1)[0].replace("/", "."))
        except Exception:
            continue
    return pkgs


def _import_package(imp: str) -> str:
    """The enclosing PACKAGE an import resolves against — i.e. exactly what must be on
    the compile classpath for it to resolve. Relies on the Scala/Java convention that
    package segments are lowercase and type/object segments are Uppercase: the package
    is the leading run of segments before the first Uppercase (type/object) segment.
    This is what makes the classpath check correct for BOTH shapes that look identical
    syntactically:
      import edu...dynoviz.raptorhunt.Rectangle          -> package edu...dynoviz.raptorhunt
      import edu...beast.cg.SpatialDataTypes.RasterRDD    -> package edu...beast.cg
        (`SpatialDataTypes` is an OBJECT, `RasterRDD` a type member — the real package
         stops at `cg`, so a member-of-object import isn't mistaken for a missing pkg)
    Wildcards and brace groups reduce to their package the same way:
      import a.b.c._            -> a.b.c
      import a.b.c.Obj._        -> a.b.c
      import a.b.{X, Y}         -> a.b
    A checker that instead accepted ANY ancestor would wrongly keep
    `org.apache.spark.test.ScalaSparkTest` (ancestor `org.apache.spark` is present) even
    though package `org.apache.spark.test` ships no classes — the bug this replaces."""
    path = imp[len("import "):].strip() if imp.startswith("import ") else imp.strip()
    if "{" in path:                       # import a.b.{X, Y} -> drop the brace group
        path = path[:path.index("{")].rstrip(".")
    elif path.endswith("._"):             # wildcard -> drop the trailing ._
        path = path[:-2]
    pkg: list[str] = []
    for seg in path.split("."):
        if seg[:1].isupper():             # first Uppercase segment = type/object -> stop
            break
        pkg.append(seg)
    return ".".join(pkg)


def _on_classpath(imp: str, avail: set[str]) -> bool:
    """True iff the import's enclosing package is present in the compile jars. `avail`
    is derived from the SAME jars scalac compiles against, so this keeps exactly the
    imports that resolve and drops exactly the ones that raise
    `object X is not a member of package Y` — e.g. source-tree-only modules (`dynoviz`,
    `test`) that are indexed from source but never shipped in the runtime jars. Callers
    skip the filter entirely when `avail` is empty (jars unresolved), so behavior is
    unchanged when the classpath can't be determined."""
    pkg = _import_package(imp)
    return bool(pkg) and pkg in avail


_TEST_FRAMEWORK_IMPORT = re.compile(
    r"scalatest|junit|scalatestplus|ScalaSparkTest|mockito|\.mock|RunWith|"
    r"AnyFunSuite|BeforeAndAfter|TestName", re.IGNORECASE)


def _imports_from_tests(cfg: AidealConfig) -> list[str]:
    """Robust import block: the SPECIFIC imports the test suite already uses to
    exercise the APIs — real, compiling, and made COLLISION-FREE. Braced imports
    are expanded to one-per-name; any simple name that resolves to two different
    paths (e.g. two `ByteArrayOutputStream`s) is DROPPED, since including both
    would make scalac ambiguous. Test-framework imports are filtered out."""
    from collections import defaultdict
    imp_re = re.compile(r"^\s*import\s+(\S.*?)\s*$", re.MULTILINE)
    raw: set[str] = set()
    for g in cfg.test_globs:
        for p in globmod.glob(str(cfg.root / g), recursive=True):
            txt = Path(p).read_text(encoding="utf-8", errors="ignore")
            for m in imp_re.finditer(txt):
                t = m.group(1).strip()
                if t and not _TEST_FRAMEWORK_IMPORT.search(t):
                    raw.add(t)
    wildcards: list[str] = []
    by_name: dict[str, set[str]] = defaultdict(set)   # simple name -> {full import}
    for t in raw:
        if t.endswith("._"):                          # package/object wildcard
            wildcards.append(f"import {t}")
        elif "{" in t and t.endswith("}"):            # expand braces to one-per-name
            pkg = t[:t.index("{")]
            for nm in t[t.index("{") + 1:t.rindex("}")].split(","):
                nm = nm.strip()
                if not nm:
                    continue
                simple = nm.split("=>")[-1].strip()   # renamed import: keep the alias
                by_name[simple].add(f"import {pkg}{nm}")
        else:
            by_name[t.rsplit('.', 1)[-1]].add(f"import {t}")
    out = list(dict.fromkeys(wildcards))
    for simple, imps in by_name.items():
        if len(imps) == 1:                            # unambiguous -> keep
            out.append(next(iter(imps)))
        # else: same simple name from >1 path -> drop (would be ambiguous)
    # drop imports whose package isn't on the compile classpath (a test-only dep
    # would fail scalac). Skipped when jars aren't configured/resolvable.
    avail = _available_packages(cfg)
    if avail:
        out = [i for i in out if _on_classpath(i, avail)]
    return sorted(set(out))


def _pkgobject_reexported_wildcards(cfg: AidealConfig) -> dict[str, set[str]]:
    """Auto-detect wildcard imports made REDUNDANT (and thus ambiguous) by a Scala
    package object. `package object X extends A with B` means `import <path>.X._`
    already brings A's/B's implicit classes into scope; a SECOND wildcard
    `import <pathA>.A._` re-introduces the same implicit at equal priority, so
    Scala can no longer disambiguate and the conversion silently stops resolving
    (the `sc.shapefile is not a member` class of bug).

    Returns `{package-object wildcard -> {redundant mixin wildcards it re-exports}}`
    so the caller can drop the mixin wildcards ONLY when the package-object
    wildcard is actually present (dropping them otherwise would delete implicits a
    codebase legitimately imports the narrow way). General: works for any codebase
    that fronts its implicits with a package object — no per-conflict config."""
    out: dict[str, set[str]] = {}
    pkg_re = re.compile(r"^\s*package\s+([\w.]+)\s*$", re.MULTILINE)
    obj_re = re.compile(r"package\s+object\s+(\w+)\s+extends\s+(.+?)(?:\{|\n\s*\n|\Z)", re.DOTALL)
    imp_named = re.compile(r"^\s*import\s+([\w.]+)\.(\w+)\s*$", re.MULTILINE)
    for g in cfg.source_globs:
        for path in globmod.glob(str(cfg.root / g), recursive=True):
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            mo = obj_re.search(text)
            if not mo:
                continue
            pm = pkg_re.search(text)
            if not pm:
                continue
            pkg_path = f"{pm.group(1)}.{mo.group(1)}"          # e.g. edu...beast
            # resolve each mixed-in trait's simple name to a full import path using
            # this file's own imports (traits with no import share the package and
            # can't collide via a *different* wildcard, so skipping them is safe).
            named = {simple: f"{owner}.{simple}" for owner, simple in imp_named.findall(text)}
            mixins: set[str] = set()
            for part in re.split(r"\bwith\b", mo.group(2)):
                m = re.match(r"\s*([\w.]+)", part)
                if not m:
                    continue
                full = named.get(m.group(1).split(".")[-1])
                if full and full != pkg_path:
                    mixins.add(f"import {full}._")
            if mixins:
                out.setdefault(f"import {pkg_path}._", set()).update(mixins)
    return out


def _source_symbol_index(cfg: AidealConfig) -> dict[str, str]:
    """Index PUBLIC, top-level type/object declarations across the source tree:
    `{SimpleName -> "import pkg.Name"}`. Top-level = declared at column 0 (Scala
    convention), which also excludes nested and private/protected declarations
    (their line starts with indentation or `private`/`protected`, so the anchored
    pattern won't match). Simple-name collisions across packages are dropped to
    avoid ambiguous imports. This is the lookup table the scaffold uses to resolve
    symbols automatically — no hand-maintained import list."""
    from collections import defaultdict
    pkg_re = re.compile(r"^\s*package\s+([\w.]+)\s*$", re.MULTILINE)
    # anchored at line start, optional benign modifiers, then the keyword + an
    # Uppercase name. `private`/`protected` are NOT in the modifier set, so a
    # `private object X` line fails to match and is skipped.
    decl_re = re.compile(
        r"^(?:(?:final|sealed|abstract|implicit|case)\s+)*(?:class|trait|object)\s+([A-Z]\w*)",
        re.MULTILINE)
    by_name: dict[str, set[str]] = defaultdict(set)
    for g in cfg.source_globs:
        for path in globmod.glob(str(cfg.root / g), recursive=True):
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            pm = pkg_re.search(text)
            if not pm:
                continue
            pkg = pm.group(1)
            for nm in decl_re.findall(text):
                by_name[nm].add(f"import {pkg}.{nm}")
    return {n: next(iter(s)) for n, s in by_name.items() if len(s) == 1}


def _defining_object_imports(cfg: AidealConfig) -> list[str]:
    """Auto-import the symbols documented APIs need — no per-object/type config:
      (a) the OBJECT that defines each API (file-stem object), so static call forms
          `RasterOperationsLocal.mapPixels(...)` / `RaptorJoin.raptorJoinFeature(...)`
          resolve — these live in the same package as their tests, so `from-tests`
          mining can't discover them; and
      (b) every TYPE a documented signature references (return + params), e.g. the
          `RaptorJoinResult` / `RaptorJoinFeature` case classes used in a raptor
          result annotation, which are also same-package and mining-invisible.
    Both are looked up in the source symbol index; anything not defined in this
    codebase (Spark's `RDD`, generic params `T`/`U`, ...) is simply absent from the
    index and ignored."""
    index = _source_symbol_index(cfg)
    if not index:
        return []
    needed: set[str] = set()
    _ident = re.compile(r"[A-Z]\w*")
    for d in public_api_details(cfg):
        if d.get("visibility") != "public":
            continue
        f = d.get("file", "")
        if f.endswith(".scala"):
            needed.add(Path(f).stem)                       # (a) defining object
        sig = d.get("signature") or ""
        ret = d.get("returns") or ""
        ptypes = " ".join(p.get("type", "") for p in (d.get("params") or []))
        for blob in (sig, ret, ptypes):                    # (b) referenced types
            needed.update(_ident.findall(blob))
    imports = {index[n] for n in needed if n in index}
    # Same compile-classpath gate the from-tests path uses: a documented API can live
    # in a source module that ISN'T on the exec classpath (e.g. `dynoviz`, or the
    # `test` helper modules under src/main/scala). Its defining-object / referenced-type
    # import is real in the source tree but `object dynoviz is not a member ...` at
    # scalac time, and — because these imports are shared by EVERY api-test — one such
    # leak fails the whole suite. Drop them here; skipped when jars are unresolved.
    avail = _available_packages(cfg)
    if avail:
        imports = {i for i in imports if _on_classpath(i, avail)}
    return sorted(imports)


def generate_scaffold(cfg: AidealConfig) -> str:
    """Build a runnable scaffold. `comprehension.execute.imports`:
      - a list      -> use that curated block verbatim,
      - "from-tests"/"auto" -> mine the SPECIFIC, compiling imports the test suite
        uses (robust; avoids the ambiguous-RasterRDD wildcard collision),
      - unset       -> auto-derive wildcard imports from source packages (best-effort)."""
    ex = (cfg.comprehension or {}).get("execute", {}) if cfg.comprehension else {}
    # the scaffold FRAME is language-specific -> a codebase adapter can override it
    # (e.g. scala-spark's GeoJobMain harness, or a Python __main__ runner). Core
    # only fills the {imports} slot + the AIDEAL_DATA_BINDINGS / API_TEST markers.
    frame = ex.get("scaffold_frame") or _SCAFFOLD_FRAME
    override = ex.get("imports")
    # project may declare must-have imports the test suite / source never writes
    # explicitly (e.g. an object like `RaptorJoin` used only inside its own
    # package, or a package-object of implicits). Honored in EVERY mode.
    extra = ex.get("extra_imports", []) or []
    # ...plus the defining OBJECT of every documented API, so static-method call
    # forms resolve even when the object lives in the same package as its tests
    # (which `from-tests` mining can't discover). Opt out with defining_object_imports: false.
    defining = _defining_object_imports(cfg) if ex.get("defining_object_imports", True) else []
    # project may drop imports that are REDUNDANT AND AMBIGUOUS: a Scala package
    # object that `extends` several mixin traits (e.g. `edu.ucr.cs.bdlab.beast._`
    # re-exports ReadWriteMixin) makes a second wildcard of the same mixin
    # (`ReadWriteMixin._`) a duplicate implicit at equal priority -> the implicit
    # conversion becomes ambiguous and silently stops resolving (`sc.shapefile`
    # "is not a member"). Listing that redundant wildcard here removes the tie.
    exclude = set(ex.get("exclude_imports", []) or [])
    # package-object re-export map: {pkgobj wildcard -> redundant mixin wildcards}.
    # Auto-drops the ambiguous duplicates so common cases need no manual
    # `exclude_imports`; config stays as an additional override.
    reexports = _pkgobject_reexported_wildcards(cfg)
    # ...and GUARANTEE the package-object umbrella wildcard(s) themselves (e.g.
    # `import edu.ucr.cs.bdlab.beast._`) — the documented entry point for the
    # sc.* implicits (shapefile/geoTiff/mapPixels-instance-form). Adding them here
    # means no manual extra_import is needed, and the reexport-drop above keeps the
    # redundant mixin wildcards from re-introducing the ambiguity.
    extra = list(extra) + defining + sorted(reexports)
    def _drop(lines: list[str]) -> list[str]:
        # remove excluded imports AND de-duplicate (a guaranteed extra_import may
        # also be mined from tests; two identical wildcards are harmless but noisy)
        present = set(lines)
        dyn = set(exclude)
        for pkgobj, mixins in reexports.items():
            if pkgobj in present:          # only redundant when the umbrella is there
                dyn |= mixins
        out: list[str] = []
        seen: set[str] = set()
        for l in lines:
            if l in dyn or l in seen:
                continue
            seen.add(l)
            out.append(l)
        return out
    if isinstance(override, list) and override:
        return frame.replace("{imports}", "\n".join(_drop(list(extra) + override)))
    if isinstance(override, str) and override.strip().lower() in ("from-tests", "auto"):
        mined = _imports_from_tests(cfg)
        return frame.replace("{imports}", "\n".join(_drop(_SCAFFOLD_BASE_IMPORTS + list(extra) + mined)))
    # Collect source packages (wildcarded) + the packages/objects the source
    # imports from. Collapse every import to a WILDCARD of its package/object so
    # the noisy per-class member lists become a short, clean set. Keep only
    # caller-facing roots — a doc-driven snippet needs the library + Spark +
    # geometry, not the library's internal deps (hadoop/geotools/kryo/jhdf).
    caller_roots = ("edu.ucr.cs.bdlab", "org.apache.spark", "org.locationtech")
    pkgs: set[str] = set()
    wilds: set[str] = set()
    pkg_re = re.compile(r"^\s*package\s+([\w.]+)", re.MULTILINE)
    imp_re = re.compile(r"^\s*import\s+(\S.*)$", re.MULTILINE)

    def _wildcard_of(target: str) -> str:
        s = target.strip()
        if s.endswith("._"):
            return s[:-2]
        if s.endswith("}"):
            return s[:s.rfind(".{")]
        return s.rsplit(".", 1)[0]            # drop the single class/member

    for g in cfg.source_globs:
        for path in globmod.glob(str(cfg.root / g), recursive=True):
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            for m in pkg_re.finditer(text):
                pkgs.add(m.group(1))
            for m in imp_re.finditer(text):
                w = _wildcard_of(m.group(1))
                if w.startswith(caller_roots) and w.count(".") >= 2:
                    wilds.add(w)
    wilds |= pkgs
    # drop accidental ancestors of a source package (e.g. edu.ucr.cs.bdlab left
    # over from `import edu.ucr.cs.bdlab.raptor`) — the specific one is kept.
    wilds = {w for w in wilds
             if w in pkgs or not any(p.startswith(w + ".") for p in pkgs)}
    # drop wildcards for packages NOT present in the compile jars (e.g. internal
    # `jhdf`) — those imports would fail to compile. Keep a wildcard if the
    # package itself, or its enclosing package (for object imports like
    # `RaptorMixin._`), has classes in the jars. Skipped if jars not configured.
    avail = _available_packages(cfg)
    if avail:
        wilds = {w for w in wilds
                 if w in avail or w.rsplit(".", 1)[0] in avail}
    # extra_imports + defining-object imports (same `extra` assembled above).
    pkg_imports = sorted(f"import {w}._" for w in wilds)
    imports = "\n".join(_drop(_SCAFFOLD_BASE_IMPORTS + list(extra) + pkg_imports))
    return frame.replace("{imports}", imports)
