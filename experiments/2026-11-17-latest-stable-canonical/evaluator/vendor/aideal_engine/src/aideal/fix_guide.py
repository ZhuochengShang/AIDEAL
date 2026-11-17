"""Shared error-signature -> fix-hint guide for the repair loops.

Both the per-API comprehension executor (`doc_checks._comprehension_execute`) and
the demo agent replay these hints, so a failing round gets targeted guidance
(what KIND of mistake was made) alongside the actual compiler error (which symbol
on which line). Keeping ONE copy here avoids the two loops drifting apart.

Codebase-agnostic: the categories/patterns are generic; the doc (LLM_readme)
supplies the specifics. The specific hint that steers the raster pixel-type lesson
(`geoTiff[Int]` -> `geoTiff[Float]`) is the `type-mismatch` rule.
"""
from __future__ import annotations

import re

# (regex on the build output, category, human fix hint). First match wins.
FIX_GUIDE: list[tuple[str, str, str]] = [
    (r"not found: value (\w+)", "unknown-name",
     "That name isn't in the API. Use the documented function from the doc's Valid "
     "Call Patterns, or an alias from the alias map below."),
    (r"value (\w+) is not a member", "wrong-receiver",
     "The method isn't on that type. Call it on the receiver/object the doc shows "
     "(e.g. `Object.op(...)` for a static op, or `value.op(...)` for an instance "
     "op), not a bare name or a call on the wrong type."),
    (r"type mismatch|required:.*found:", "type-mismatch",
     "Match the parameter and return TYPES in the doc's Signature block exactly. "
     "Pick the type ARGUMENT that matches the actual input data — for a raster, the "
     "pixel type in geoTiff[T] must match the file (e.g. geoTiff[Float] for float "
     "rasters, not geoTiff[Int]) — and wrap inputs as the RDD/collection type the "
     "API expects."),
    (r"object (\w+) is not a member of package", "bad-import",
     "Import path is wrong. Use only the imports the scaffold already provides."),
    (r"overloaded method|ambiguous reference", "ambiguity",
     "Disambiguate by giving explicit types; pick the overload shown in the doc."),
    # --- Spark / Hadoop / Beast runtime gotchas (specific -> match before the
    #     generic runtime catch-all below; first match wins) ---------------------
    (r"Wrong FS|expected: file:///|IllegalArgumentException:.*Wrong FS", "hadoop-path",
     "Hadoop 'Wrong FS' = the path's scheme doesn't match the FileSystem you asked "
     "for. Prefer the library's high-level reader on the PRE-LOADED typed inputs "
     "(e.g. rasterRDD / featuresRDD, or sc.geoTiff / sc.shapefile) instead of raw "
     "Hadoop FileSystem calls. If you truly need a FileSystem, get it FROM the path: "
     "`path.getFileSystem(sc.hadoopConfiguration)`, NOT `FileSystem.get(conf)`. Never "
     "prepend 'file://' to a path string that already starts with a scheme."),
    (r"output format must be defined|specify the output format|No output format", "output-format",
     "This writer needs an output FORMAT. Use the documented writer that names the "
     "format (e.g. saveAsGeoJSON / saveAsShapefile / saveAsGeoTiff / writeSpatialFile "
     "with a format), or set the format option the doc shows, before writing to "
     "output_dir. A bare .save(...) with no format will fail."),
    (r"NoClassDefFoundError|ClassNotFoundException", "infra",
     "A runtime dependency is MISSING from the harness classpath — an environment "
     "gap, not a code/doc problem. Do NOT rewrite the snippet; it needs the jar added "
     "to comprehension.execute.packages (or the function excluded). This is filtered "
     "out of the doc-quality score."),
    (r"Unable to locate class corresponding to inner class|Scala signature .* has wrong version|"
     r"object (?:\w+) is not a member of package (?:org\.apache\.spark|org\.apache\.hadoop|com\.google)",
     "infra",
     "A class / inner class can't be resolved on the compile classpath — a build or "
     "dependency-version gap, not a doc problem. Add the missing jar to "
     "comprehension.execute.packages rather than editing the snippet."),
    (r"Task not serializable|NotSerializableException", "serialization",
     "Spark ships closures to executors, so everything captured must be Serializable. "
     "Don't reference the SparkContext, a connection, or other non-serializable object "
     "inside a map/filter; hoist the value you need into a local val first, then "
     "capture only that."),
    (r"__RUN_ERR__|Exception", "runtime",
     "Compiles but fails at run. Re-check input types/paths and the doc's Common "
     "Failure Modes for this API."),
]


def classify(stderr: str) -> tuple[str, str]:
    """Return (category, fix_hint) for the first matching fix-guide rule."""
    for pat, cat, hint in FIX_GUIDE:
        if re.search(pat, stderr or ""):
            return cat, hint
    return "unknown", "Re-read the doc entry's Signature and Valid Call Patterns."
