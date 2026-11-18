# RDPro strict raster API bank

The revised bank contains **330 targets** from the pinned Beast 0.10.1 source, commit `547f7f912131a8032f6b5d26991415a5faf05cef`. It covers the Raptor module and eight supporting raster tile, metadata, schema and serializer files in `cg/geolite`. It excludes vector-only processing, visualization, web/server operations and general utilities as evaluation targets.

| Language | Methods | Concrete class/constructor entries | Total |
|---|---:|---:|---:|
| Java | 62 | 7 | **69** |
| Scala | 209 | 52 | **261** |
| **Total** | **271** | **59** | **330** |

Java here identifies the source language. Every selected definition belongs to `edu.ucr.cs.bdlab`; none is an imported Java, Spark, Scala or other dependency definition. Custom operations can still call these dependencies when implementing raster behavior.

## How the reduction works

| Selection step | Source declaration sites |
|---|---:|
| Public candidate sites in the raster scope, including overloads | 452 |
| Exclude reviewed forwarding wrappers, adapters and facade entries | −72 |
| Exclude unconditional Scala `???` stubs | −25 |
| Keep three abstract types as context only | −3 |
| Exclude abstract/bodyless method declarations | −15 |
| Keep the maximum-parameter eligible overload within each owner-qualified API | −7 |
| **Selected targets** | **330** |

The earlier 422-target scope had not applied these strict exclusions. The intermediate 406-target bank removed only 16 source-verified forwarding forms. The new review checks all 452 candidate declaration sites, including overloads that were not previously selected.

The 25 stubs include 24 earlier selected methods and one previously omitted overload. `ITile`, `AbstractGeoTiffTile` and `AbstractConvolutionTile` remain valid library types and documentation context. They are excluded only as independent executable constructor targets.

## What was removed and retained

| Example | Decision | Source evidence |
|---|---|---|
| `FilterTile.getPixelValue` | Exclude forwarding method | Calls `tile.getPixelValue(i, j)` unchanged |
| `RasterSchemaHelper.readIn` | Exclude IO adapter | Wraps its input and calls `readExternalObj` |
| `RaptorJoin.raptorJoinFeatureJ` | Exclude Java adapter | Converts between JavaRDD and the existing Scala operation |
| `sc.geoTiff` / `sc.hdfFile` | Exclude convenience facades as separate targets | Set a layer option and construct `RasterFileRDD` |
| `RasterFeature.createEmpty` | Exclude convenience factory | Constructs the existing representation with fixed arguments |
| `MemoryTile.copy` | Exclude unimplemented method | Complete body is `???` |
| `RasterOperationsGlobal.rasterizePixels` | Retain custom operation | Assigns pixels to tiles, groups them and builds tile contents |
| `RasterOperationsLocal.mapPixels` | Retain custom operation | Constructs mapped tiles with a supplied pixel transformation |
| `RasterMetadata.create` | Retain custom construction operation | Builds the affine grid-to-model transform before constructing metadata |

Removing an evaluation target does not remove code from RDPro. The convenient calling forms remain available in the original library and documentation. A facade is not claimed to be behaviorally identical to its target merely because both participate in the same workflow.

Two equal-arity overload groups previously selected wrappers because of source order. Exclusion now happens **before** overload selection, so the bank retains the actual operations:

| API family | Former selected overload | New selected implementation |
|---|---|---|
| `Intersections.compute` | `ArrayList<Long>, Geometry[], RasterMetadata` conversion adapter | `Geometry[], long[], RasterMetadata` intersection algorithm |
| `RaptorJoin.raptorJoinLocal` | `Array[IFeature]` conversion adapter | `Array[Geometry]` raster intersection and pixel retrieval |

## Duplicate and ownership checks

The selected bank has 330 unique API identities and 330 unique source sites. Java and Scala banks are disjoint. No selected API has another eligible overload in the same owner with more parameters.

The exact-body scan retains ten groups with matching body text across distinct owners. These are recorded in [NORMALIZED_BODY_REVIEW.json](NORMALIZED_BODY_REVIEW.json), with the reason for each decision. For example, three iterator `next` bodies call different private `prefetchNext` implementations; they do not perform the same operation. This preserves the approved rule that distinct owners remain separate. Text equality and a shared short name do not prove semantic equivalence.

This review removes the identified wrappers and stubs. It does not establish universal semantic independence among every remaining operation.

## Review files

- [SUMMARY.json](SUMMARY.json) contains the counts and the two replacement overloads.
- [SELECTED_APIS.json](SELECTED_APIS.json) lists every retained target, source location and signature.
- [ALL_CANDIDATE_DECISIONS.json](ALL_CANDIDATE_DECISIONS.json) records every scoped candidate, its exact source declaration, hashes and decision.
- [REMOVED.json](REMOVED.json) lists all 100 explicit source-site exclusions and reasons.
- [selection_exclusions.json](selection_exclusions.json) is the machine-readable source-bound exclusion review.
- [canonical-selection.json](canonical-selection.json) covers the **full** original source ledger after exclusions. Its 2,695 winners preserve unaffected modules for provenance; the two task manifests select only 330 raster targets.
- [Java manifest](api_manifest.java.json) and [Scala manifest](api_manifest.scala.json) define the runnable bank.
- [VALIDATION.json](VALIDATION.json) records the checks and artifact hashes.

The full frozen source ledger and language declaration lists remain unchanged. The run operator must bind the new exclusion review and canonical receipt, relocate their paths, and prepare a fresh output directory. README authoring must use `--scope manifest` to keep this same bank.

To reproduce the selection and static validation on this machine:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python \
  /tmp/aideal-raptor-scope-2026-11-17/strict-no-wrappers/build_strict.py

PYTHONDONTWRITEBYTECODE=1 /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python \
  /tmp/aideal-raptor-scope-2026-11-17/strict-no-wrappers/validate_strict.py
```

These commands make no model calls and do not execute or alter the RDPro library. Runtime and provider checks are separate launch requirements.
