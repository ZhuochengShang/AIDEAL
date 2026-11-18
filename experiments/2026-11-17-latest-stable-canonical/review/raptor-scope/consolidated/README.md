# RDPro raster-only API scope

The source remains the official Beast 0.10.1 commit `547f7f912131a8032f6b5d26991415a5faf05cef`. Only the selected evaluation targets change.

| Selection step | Targets |
|---|---:|
| Previous full Beast selection | 2,787 |
| Retain `raptor/src/main/` | 347 |
| Add eight explicit raster tile/metadata/schema support files from `cg/geolite` | +75 |
| Raster scope before forwarding consolidation | 422 |
| Collapse source-verified forwarding forms into retained operations | −16 |
| **New selected targets** | **406** |

| Bank | Methods | Class/type entries | Total |
|---|---:|---:|---:|
| Java | 71 | 7 | **78** |
| Scala | 271 | 57 | **328** |
| Total | **342** | **64** | **406** |

The bank contains 331 targets in Raptor and 75 supporting raster-type targets across 67 source files. It has 253 distinct short names but 406 distinct owner-qualified identities. Methods with the same name in different classes remain distinct. The two language banks partition source definitions; they do not count every definition twice.

The support files are `ITile`, `ITileSerializer`, `DefaultReadOnlyTile`, `RasterMetadata`, `RasterMetadataSerializer`, `RasterFeature`, `RasterFeatureSerializer`, and `RasterSchemaHelper`. Vector processing, visualization, web/server applications and generic utility modules are outside the target bank. Their code remains available as build/runtime dependencies when Raptor needs it. TIFF/HDF internals outside these explicitly selected files are likewise dependencies rather than extra evaluation targets.

## Forwarding consolidation

Twelve RaptorMixin methods directly call retained operations. Four SlidingWindowTile coordinate getters directly call retained RasterMetadata boundary methods. The audit verifies the complete forwarding expression, a unique retained callee definition, source-file and declaration hashes, declared argument/receiver mappings, and relevant defaults. These 16 native calling forms remain recorded in [EXPOSURES.json](EXPOSURES.json), although they no longer create separate evaluation denominators.

For example, `raster.mapPixels(f)` forwards to `RasterOperationsLocal.mapPixels(raster, f)`. The scoped bank evaluates the underlying operation once and keeps the convenient calling form discoverable. This is a native interface from the original source, not an LLM-generated alias.

The detailed [consolidation receipt](CONSOLIDATION.json) contains all 16 mappings and the review of every one of the 71 records labelled `wrapper` or `direct_forwarder` by the earlier syntax classifier. Fifty-five stay selected because their labels do not establish duplication. They include actual rasterization algorithms, coordinate conversions, formatting, representation adapters, and calls on dynamic tile receivers. Blindly removing those labels would delete real raster functionality. These are source-level forwarding checks, not a claim that all remaining functions are semantically independent or behaviorally equivalent on every input.

Three Java-facing interfaces outside the Raptor module—`JavaSpatialSparkContext.geoTiff`, `JavaSpatialSparkContext.hdfFile`, and `JavaSpatialRDDHelper.raptorJoin`—are recorded as alternate adapter paths. The documented Scala loader and raster-operation forms are already represented by Raptor's own source and forwarding records.

## Use in the run plan

- R0 and README authoring must use the same [Java manifest](api_manifest.java.json) or [Scala manifest](api_manifest.scala.json).
- Use `--scope manifest` for README authoring; `surface` would select the full inventory again.
- Keep the original full source ledger and canonical-selection receipt intact for provenance. The qualified reader checks those complete bindings before applying a task subset.
- Prepare a new output directory and bind these manifests. Do not change a prepared full-Beast run in place.
- The five other libraries retain 2,520 targets. The revised total is **2,926**, rather than 5,307.

The older 171-target result used a different target construction. Its historical count must be reconciled with its saved manifest before treating the two denominators as comparable. In particular, the new scope counts class/type entries and preserves owning classes. Original-document coverage is a separate measurement; source count is not a count of examples or operations described in the README.
