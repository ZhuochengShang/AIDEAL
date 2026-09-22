"""Legacy RDPro alias-module rendering from explicit or bundled demo specs.

This module does not discover general library-specific wrappers automatically.
Portable source-grounded proposals and versioned installation are provided by
workflow.improvement_suggestions and workflow.treatment_versions.

A recurring, VERIFIED io/type fix from the repair loop is promoted to a small
wrapper function added to the codebase, so future generations call one
LLM-natural, grounded, type-correct name instead of rediscovering the pattern
(e.g. the correct raster pixel type). All wrappers live in ONE `GrailAliases`
object so:
  * the scaffold's symbol-index auto-imports it (no manual import wiring), and
  * it can get its own LLM_readme entry like any other API.

This module only RENDERS + REGISTERS the wrappers (Python side). Two integration
decisions stay with the project:
  1. WHERE the generated .scala is compiled from (it must sit under a module in
     `source_globs` / on the compile classpath to be importable). By default we
     write it next to the alias registry; copy/symlink it into a beast module's
     src/main/scala to have it compiled + auto-imported.
  2. Pixel type is a COMPILE-TIME parameter, so a reader cannot fully auto-detect
     it at runtime and still return a statically-typed RasterRDD[T]. The seeded
     `readRaster` encodes the common Float convention; add typed variants for
     Int/Short datasets (that's the "reader map to correct pixel type").
"""
from __future__ import annotations

from pathlib import Path

from .alias_registry import AliasRegistry


# Each spec: name, full Scala signature, body expression, the canonical API it
# wraps (for the registry), and a one-line doc. Seeded with the two IO fixes the
# repair loop kept rediscovering (raster pixel type; shapefile vector reader).
DEFAULT_ALIAS_FUNCTIONS: list[dict] = [
    {
        "name": "readRaster",
        "signature": "def readRaster(sc: SparkContext, path: String): RasterRDD[Float]",
        "body": "sc.geoTiff[Float](path)",
        "canonical": "geoTiff",
        "doc": ("Load a GeoTIFF as a FLOAT raster (the common pixel type). "
                "For int/short rasters call sc.geoTiff[Int] / sc.geoTiff[Short]."),
    },
    {
        "name": "readVectorShapefile",
        "signature": "def readVectorShapefile(sc: SparkContext, path: String): SpatialRDD",
        "body": "sc.shapefile(path)",
        "canonical": "shapefile",
        "doc": "Load an ESRI shapefile (.shp + sidecars) as a vector SpatialRDD (RDD[IFeature]).",
    },
]

_PACKAGE = "edu.ucr.cs.bdlab.grail"
_HEADER = f"""// AUTO-MANAGED by aideal alias-function synthesis — do not hand-edit entries;
// add/update via aideal.alias_functions.sync. Each wrapper encodes a verified,
// reusable call pattern so generated code calls one grounded name.
package {_PACKAGE}

import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import edu.ucr.cs.bdlab.beast._
import edu.ucr.cs.bdlab.beast.cg.SpatialDataTypes.{{RasterRDD, SpatialRDD}}
import edu.ucr.cs.bdlab.beast.geolite.{{IFeature, ITile}}

object GrailAliases {{
"""
_FOOTER = "}\n"


def render_module(specs: list[dict]) -> str:
    """Render the full GrailAliases.scala from the alias specs (deterministic,
    so re-running produces a stable diff)."""
    parts = []
    for s in sorted(specs, key=lambda x: x["name"]):
        parts.append(f"  /** {s['doc']} (alias for `{s['canonical']}`) */\n"
                     f"  {s['signature']} = {s['body']}")
    return _HEADER + "\n" + "\n\n".join(parts) + "\n" + _FOOTER


def module_path(cfg) -> Path:
    """Where the generated module is written (next to the alias registry by
    default; override with files.alias_functions in the config)."""
    rel = (cfg.raw.get("files", {}) or {}).get("alias_functions", "aliases/GrailAliases.scala")
    return (cfg.root / rel)


def sync(cfg, specs: list[dict] | None = None, *, mark_added: bool = True) -> dict:
    """Render + write GrailAliases.scala and record each wrapper in the alias
    registry (status `added`). Idempotent: re-running with the same specs rewrites
    the same file and leaves the registry unchanged."""
    specs = specs if specs is not None else DEFAULT_ALIAS_FUNCTIONS
    path = module_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render_module(specs)
    changed = (not path.exists()) or path.read_text(encoding="utf-8") != text
    if changed:
        path.write_text(text, encoding="utf-8")
    added = []
    if mark_added:
        reg = AliasRegistry(cfg.aliases_file)
        for s in specs:
            reg.mark_added(s["name"], s["canonical"])   # proposed -> added
            added.append({"alias": s["name"], "canonical": s["canonical"]})
    return {"path": str(path), "changed": changed, "aliases": added,
            "count": len(specs)}
