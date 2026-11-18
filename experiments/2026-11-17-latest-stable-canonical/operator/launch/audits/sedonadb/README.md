# SedonaDB R0 failure audit

This is a diagnostic sidecar for the ongoing Original R0 run, not a final experiment result. The snapshot at **2026-11-18 01:22:05 UTC** contains **101 recorded APIs: 22 passes and 79 failures**. Later results may differ. The measured files remain unchanged.

## Findings

| Evidence | Finding | Interpretation |
|---|---|---|
| 58 of the 79 failures | Generated SQL calls an unregistered helper: `rs_fromgeotiff` (56), `st_fromgeoraster` (1), or `read_binary` (1). None is the requested target API. | A repeated generated helper error dominates this snapshot. This is not evidence that the target APIs are absent. |
| Delivered `RS_AsGeoTiff` request | The original excerpt includes `RS_Example()`; the prompt also includes toy SQL guidance and both raster fixture paths. | The toy example reached the audience. Missing example exposure does not explain this case. |
| Passing `RS_AsRaster` attempt | Uses documented `RS_FromPath` and materializes the raster. Both fixture files exist and their hashes were recorded. | The configured raster fixture is usable; a universal missing-file problem does not explain the failures. |
| `ST_ClosestPoint` source and isolated reference check | Geography arguments succeed; geometry arguments produce `No kernel matching arguments`. Geometry distance and buffer controls succeed. | The pinned documentation advertises a geometry signature unsupported by this runtime. This is a documentation/runtime kernel mismatch, not evidence of general GEOS absence. |
| `S2_CoveringCellIds` attempt | Requests at most 16 cells but receives 30; the original documentation describes the argument as a maximum. | A possible documentation/implementation contract discrepancy remains unresolved. Do not classify it automatically as an audience mistake. |

The remaining grouped failures are 15 audience assertion or explicit unverifiable-contract failures, one Python API misuse, and five cases requiring individual review. The five include `ST_ClosestPoint` above, passing a string where `RS_EnsureLoaded` expects a raster, unsupported `RS_MakeEmptyRaster` arguments, a bytes/string check in `ST_Collect_Agg`, and unsupported SQL dot access in `ST_Dump`.

## Reference check, separate from the benchmark

The isolated check at **2026-11-18 01:26:16 UTC** made **zero model calls** and changed **zero measured files**. It used the configured SedonaDB runtime. Full queries and outputs are in [REFERENCE_CHECK.json](REFERENCE_CHECK.json).

| Reference query | Outcome |
|---|---|
| `ST_ClosestPoint(geography, geography)` from the documented example | Pass |
| `ST_ClosestPoint(geometry, geometry)` advertised in the same documentation | Fail: no matching kernel |
| `ST_Distance(geometry, geometry)` control | Pass |
| Geometry `ST_Buffer` followed by `ST_Area` control | Pass |

The pinned source at commit `751453f04cd6e09842adf3073b2b3dac7d1777bc` registers `st_closestpoint` in the geography kernel list. Its documentation lists both argument types. [CLOSESTPOINT_SOURCE.json](CLOSESTPOINT_SOURCE.json) preserves exact source excerpts, line numbers, and file hashes.

## Interpretation limits

The native microbenchmark records execution and the audience program's assertions and completion marker. It does not provide an independent semantic oracle. For example, a passing `SD_Order` sample checks row count and non-null values without checking ordering. Report this metric as native execution/assertion success, not independently verified functional accuracy.

Many SQL planning failures currently retain the recorded category `unknown`. The diagnostic grouping here adds an explanation without rewriting those measured categories or changing the running evaluator. Genuine generated mistakes, documentation mismatches, and unresolved cases must remain distinguishable in subsequent analysis.

## Evidence files

- [SAMPLE.json](SAMPLE.json): first five and latest five samples at the earlier 74-record checkpoint, including generated code and execution diagnostics.
- [DIAGNOSTIC_GROUPS.json](DIAGNOSTIC_GROUPS.json): the 101-record snapshot, diagnostic groups, delivered-context checks, and fixture hashes.
- [OTHER_DIAGNOSTICS.json](OTHER_DIAGNOSTICS.json): the five individually reviewed diagnostics.
- [CLOSESTPOINT_SOURCE.json](CLOSESTPOINT_SOURCE.json): pinned documentation and implementation evidence.
- [REFERENCE_CHECK.json](REFERENCE_CHECK.json): isolated runtime checks; not benchmark results.
- [FILES.json](FILES.json): hashes for the publication evidence above and this note.

Operator note: an initial automated approval review applied an earlier review-only restriction to the proposed reference check. The parent agent resolved this using the user's current explicit launch authorization and completed the check. No approval blocker remains for this diagnostic.
