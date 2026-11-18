# RDPro counts and the strict raster study

The current RDPro bank contains **330 targets: 271 methods and 59 concrete constructors**, split into **261 Scala and 69 Java targets**. It covers Raptor and supporting raster types. The six-library study now contains **2,850 targets**. Original R0 and README authoring use the same final manifest; R0 uses one trial and zero repairs, and authoring uses `--scope manifest`.

**Final cluster preflight is pending at this documentation checkpoint. The replacement gate has not started, and no new Raptor model requests have started.** The current evaluator release is `2026-11-17-strict-raptor-64fcd34eb17c`.

## Before and after

| Review point | Count | What it counts |
|---|---:|---|
| Historical source selection | 161 | Intent-selected Scala names across Beast; Java supplied type context |
| Historical original-document matches | 88 | Names found by the earlier document heuristic within that selected surface |
| Historical README evaluation | 171 | Filled generated-README API entries: the 161 names plus ten additional entries |
| Superseded full-Beast bank | 2,787 | Selected identities across all Beast modules |
| Initial raster bank | 422 | Earlier selected identities in Raptor and eight supporting raster types |
| Intermediate consolidation | 406 | Earlier raster bank after 16 proven forwarding forms were consolidated |
| **Current strict raster bank** | **330** | **271 methods + 59 concrete constructors; 261 Scala + 69 Java** |

The 171 count was neither a complete source inventory nor the original-document API count. The old selector grouped by short method name, so distinct owners such as `GeoTiffReader.readTile` and `HDF4Reader.readTile` could share one target. It also included vector and visualization operations. Without an explicit manifest, the old evaluator used filled `## API Test:` headings in the generated README. Its ten extra entries existed in broader source; their presence alone does not establish hallucination. [Historical records and selection rules](history-171/README.md).

## Exact strict reduction

The strict pass revisits **452 candidate declaration sites**, including overloads, before selecting one eligible implementation per owner/API. This avoids selecting a large wrapper and losing the smaller implementation it calls.

| Step | Removed | Remaining |
|---|---:|---:|
| Candidate declaration sites in raster scope | — | 452 |
| Reviewed wrappers, configuration facades and thin adapters | 72 | 380 |
| Unimplemented `???` bodies | 25 | 355 |
| Abstract-type constructors | 3 | 352 |
| Methods without implementation bodies | 15 | 337 |
| Additional overloads within the same owner/API | 7 | **330** |

**452 − 72 − 25 − 3 − 15 − 7 = 330.** The earlier 422 and 406 counts were already selected identities, while 452 counts candidate declaration sites before this stricter selection. These are different stages, not contradictory totals. The 25 unimplemented candidate sites include one extra site beyond the 24 stubs found in the earlier 406-target selection.

The final targets comprise 265 Raptor-module identities and 65 supporting raster-type identities. Imported or inherited-only Java/Spark methods do not become independent targets. A library-defined implementation of a framework interface remains eligible when it performs its own operation. Distinct owners remain separate; equal names or short equal bodies do not prove equal behavior.

| Retained | Excluded as an independent target | Reason |
|---|---|---|
| `RasterOperationsLocal.mapPixels` | `RaptorMixinOperations3.mapPixels` | Native facade forwards to the retained implementation |
| `RasterFileRDD` constructor | `sc.geoTiff` and `sc.hdfFile` | Convenience functions configure options and construct the reader |
| `RasterMetadata.create` | `RasterMetadata.retile` | `create` computes an affine transform; `retile` constructs another metadata object |
| `MemoryTile.getPixelValue` | `MemoryTile.get`, `length`, `copy` | The excluded bodies are `???` |
| Concrete tile constructors | `ITile`, `AbstractGeoTiffTile`, `AbstractConvolutionTile` constructors | Abstract types are not independent executable construction targets |
| Implementation overloads of `Intersections.compute` and `RaptorJoin.raptorJoinLocal` | Their earlier selected forwarding overloads | Wrapper exclusion happens before the largest-parameter eligible overload is chosen |

No native public wrapper or dependency was deleted from Beast. Wrappers remain callable and can appear in original documentation; they no longer inflate the count of independent benchmark targets. Source-level review does not prove that every remaining operation is semantically independent or free of runtime bugs.

[Current selection](strict-no-wrappers/SELECTED_APIS.json) · [All candidate decisions](strict-no-wrappers/ALL_CANDIDATE_DECISIONS.json) · [Hash-bound exclusions](strict-no-wrappers/selection_exclusions.json) · [Scala manifest](strict-no-wrappers/api_manifest.scala.json) · [Java manifest](strict-no-wrappers/api_manifest.java.json).

## Original documentation and fairness

The linked GitHub `doc/` folder contains 16 Markdown tutorials. Raster examples are concentrated in `rdpro.md` and `raptor-join.md`. Excluding external Spark/Scala/Java/GeoTools calls, constants, types and repeated examples yields **18 raster operation families exposed through 21 owner-specific callable interfaces**. The two `shapefile` interfaces are supporting vector loaders and are counted separately. All 16 fetched documents are byte-identical to the pinned Beast 0.10.1 versions. [Exact GitHub files and hashes](github-docs/SOURCES.json) · [Version comparison](github-docs/VERSION_COMPARISON.json).

The strict bank maps unchanged original examples to **16 retained implementation identities**; **314 targets have no reviewed API-specific match**. This differs from the 18 documented operation families because `geoTiff` and `hdfFile` expose one retained constructor, and `retile` specializes the already-documented `reshapeNN` operation. The `overlay` facade maps to the retained core operation. The abstract `ITile` type remains in the original corpus without a standalone executable target.

The original qualified-name matcher missed implicit receiver forms such as `raster.mapPixels`. Reviewed receiver and source-call mappings correct retrieval without changing the original prose. Source signatures and mapping proofs stay in audit metadata, not audience prompts. Missing matches do not prove that related documentation is absent. Original example errors remain unchanged; this mapping does not certify execution.

[Current original-text manifest](strict-no-wrappers/original-docs/manifest.json) · [Mapping explanation and actual context examples](strict-no-wrappers/original-docs/README.md) · [Exposure proofs](strict-no-wrappers/ORIGINAL_DOC_EXPOSURES.json) · [Actual-reader validation](strict-no-wrappers/original-docs/VALIDATION.json).

## Verification and launch status

| Check | Outcome | Meaning |
|---|---|---|
| Strict selection/reader regression checks | 98 tests and 36 subtests passed | Software checks; no model calls |
| Actual source reader | All 330 targets resolved | Confirms selected source identities and implementation overloads |
| Actual Original audience-context reader | All 330 resolved; 16 mapped | Exact original excerpts and their hashes verified |
| Earlier constructor-correction suite | 664 tests passed | Separate release/checkpoint, not a rerun of 664 tests on the final strict release |
| **Final strict cluster preflight** | **PENDING** | Must complete before the replacement gate starts |
| **Replacement gate / Raptor requests** | **NOT STARTED** | No new Raptor results claimed at this checkpoint |

[Release receipt](operator/EVALUATOR_RELEASE.json) · [Strict verification](operator/STRICT_SELECTION_VALIDATION.json) · [Constructor suite log](operator/CONSTRUCTOR_FULL_TESTS.log). The full-Beast correction gate was stopped before its tasks began. Existing other-library jobs remain unchanged. The final cluster preflight and gate state will supersede the explicit pending status here when observed.
