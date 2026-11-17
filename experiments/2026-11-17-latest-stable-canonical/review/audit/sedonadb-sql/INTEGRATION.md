# SedonaDB stable SQL alias policy

The pinned SedonaDB 0.5.0 source supports removing **nine explicit SQL aliases** from the prior **226-name** configured registry. The proposed surface contains **217 names: 210 scalar and seven aggregate operations**. All 226 prior definition evidence-file hashes match the new stable checkout. No Rust helper or registration factory is counted as an additional SQL API.

| Omitted alias | Retained canonical operation |
|---|---|
| st_aswkb | st_asbinary |
| st_aswkt | st_astext |
| st_force3dz | st_force3d |
| st_geogfromtext | st_geogfromwkt |
| st_geometryfromtext | st_geomfromwkt |
| st_geomfromtext | st_geomfromwkt |
| st_linefromwkb | st_linestringfromwkb |
| st_linestringfromtext | st_linefromtext |
| st_numpoints | st_npoints |

Each edge is bound to an exact `with_aliases` registration-function source span and file SHA256. `SedonaScalarUDF::with_aliases` preserves the same UDF and replaces its alias-name list. The receipt also binds the implementation of that mechanism and the stable Git commit/tree.

`st_numinteriorring` and `st_numinteriorrings` share one GEOS kernel registration, but the plural name has additional backend registration context. Both remain selected, with an explicit review candidate. No claim is made that the other 217 operations have been proven semantically distinct.

SQL registered operation identity uses `registered_sql_explicit_aliases_v1`, separate from host-language maximum-parameter definition selection. Sedona scalar registration uses a user-defined runtime signature. Official SQL-page kernel lists are retained as documented call patterns; their largest listed argument count is not called a runtime maximum. `RS_Stack` explicitly accepts an unbounded number of rasters in source. Its maximum parameter count remains unknown/unbounded, and it stays selected as a unique registered operation.

The adjacent historical `expected_registry.json` lists only 198 Sedona scalar names. The active prior inventory has 219 scalar names; the exact difference is recorded in `SQL_CANONICAL_ALIAS_AUDIT.json`. The input registry was not freshly queried from a running library during this audit.

## Install only the guarded changes

- Add `aideal/api_sql_canonical.py` to the engine package.
- Apply `registry_sql_dispatch.patch`: existing complete SQL definition validation runs before optional alias filtering.
- Apply `sql_prompt_identity.patch`: canonical SQL requests expose public SQL names and documented signatures, with `parameter_count=null` and honest arity status; no source bodies or implementation ledger is included.
- Apply `fingerprint.patch` to bind the new reader code in native run identity.
- Add `tests/test_sql_canonical_aliases.py` to repository tests.

Staged full module copies exist only for isolated testing; use the patches to preserve concurrent canonical changes. Legacy SQL configurations without canonical fields return all original definitions with their original field shape.

## Ready isolated binding package

Cluster root: `/tmp/aideal-sedonadb-canonical-bindings-2026-11-17/`.

It contains `sql_api_inventory.json` (all 226 source-bound definitions plus the optional selection binding), `canonical-selection.json`, `api_manifest.json` (217 reader-returned display names), `canonical-details.json`, `requested-targets.json`, `config-binding.json`, `VALIDATION.json`, and a `source` symlink to the new stable checkout.

Relocate the package intact or symlink its frozen files into a library config root. Preserve the full original-document configuration (`README.md` plus every SQL reference page), native runtime, fixtures, and scaffold. Use `api_manifest.json` rather than constructing a manifest from lower-case receipt names: it preserves the existing public display spelling that the native manifest loader expects.

Manifest opt-in fields are `canonical_selection`, `canonical_selection_sha256`, `canonical_selection_policy_version`, and `canonical_registered_names`. The reader requires selected names to equal the complete registry minus the proven direct alias edges. It verifies the stable source identity, all receipt evidence hashes/spans, and exact name-set accounting. The existing SQL reader independently validates every original definition file, including omitted aliases.

## Verification

Five new synthetic tests and all seven existing Sedona adapter tests passed. Actual cluster validation also passed: all 226 definition files validated, 217 selected facts and request identities returned, nine aliases removed, and every SQL request represented arity without inventing a finite maximum. Evidence is in `CLUSTER_VALIDATION.json`. No SQL execution, audited library imports, model calls, or canonical-file changes occurred.
