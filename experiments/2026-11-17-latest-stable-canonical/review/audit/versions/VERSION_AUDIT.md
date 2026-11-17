# AIDEAL six-library version audit — 2026-11-17

The six libraries were not all on the latest stable source releases. MDAnalysis and tslearn need newer stable releases; mir_eval has the stable version label but a later development commit. Beast and Thumbnailator match stable source content. Active SedonaDB is version 0.5.0, but its measured synthetic source tree omitted upstream entries and must be replaced with the full official release tree.

| Library | Observed source/runtime | Latest stable | Required source action |
|---|---|---|---|
| RDPro / Beast | 0.10.1 | 0.10.1 | all 921 regular-file bytes match latest stable |
| MDAnalysis | 2.9.0 | 2.11.0 | upgrade required |
| tslearn | 0.10.0.dev | 0.10.0 | replace development snapshot with stable release |
| mir_eval | 0.8.2 | 0.8.2 | version label matches; source is later development commit, replace for stable-only protocol |
| Thumbnailator | 0.4.21 | 0.4.21 | stable source content matches; measured HEAD is synthetic |
| SedonaDB | 0.5.0 | 0.5.0 | stable version matches; re-materialize full upstream tree |

## Exact stable targets

- **RDPro / Beast**: `beast-0.10.1` → `547f7f912131a8032f6b5d26991415a5faf05cef`. [Official evidence](https://bitbucket.org/bdlabucr/beast/commits/547f7f912131a8032f6b5d26991415a5faf05cef).
- **MDAnalysis**: `package-2.11.0` → `ace84dde1363e32aa94cd3f29a42c2f590bd0575`. [Official evidence](https://github.com/MDAnalysis/mdanalysis/releases/tag/package-2.11.0).
- **tslearn**: `v0.10.0` → `f6072f237313d610413359ecc899cdb9038f4b7e`. [Official evidence](https://github.com/tslearn-team/tslearn/releases/tag/v0.10.0).
- **mir_eval**: `0.8.2` → `8db0b3812e2032544c1fc00d02d4256cab043f3d`. [Official evidence](https://github.com/mir-evaluation/mir_eval/releases/tag/0.8.2).
- **Thumbnailator**: `0.4.21` → `c9d99613878bbbf1f4d9369585b4cb5352c3b474`. [Official evidence](https://github.com/coobird/thumbnailator/commit/c9d99613878bbbf1f4d9369585b4cb5352c3b474).
- **SedonaDB**: `apache-sedona-db-0.5.0` → `751453f04cd6e09842adf3073b2b3dac7d1777bc`. [Official evidence](https://github.com/apache/sedona-db/releases/tag/apache-sedona-db-0.5.0).

## Evidence and interpretation

- Beast official archive matches all 921 tracked snapshot files byte-for-byte. Source snapshot `5ee41a6…` is content-identical to stable `547f7f9…`; do not interpret the synthetic snapshot date as release recency. [Maven metadata](https://repo.maven.apache.org/maven2/edu/ucr/cs/bdlab/beast/maven-metadata.xml).
- Thumbnailator has no GitHub Release object; stable 0.4.21 is verified by its tag and Maven Central release metadata. [Maven metadata](https://repo.maven.apache.org/maven2/net/coobird/thumbnailator/maven-metadata.xml).
- SedonaDB active catalog points to `sources/sedonadb-release-0.5.0`; the old local blocked entry and historical `sources/sedonadb` tree do not describe its active runtime. Its measured HEAD `d1a2b1e…` is a synthetic snapshot, not official commit `751453f…`. The root agent verified 1,423 retained regular files match but four Git submodule entries and `r/sedonadb/src/rust/Cargo.toml` are omitted; the measured tree is not the complete upstream release tree.
- MDAnalysis installed distribution is 2.9.0. tslearn and mir_eval are source imports, absent from installed distribution metadata; preflight imports report 0.10.0.dev and 0.8.2 respectively.
- Default branches are separately recorded in JSON and are not the stable target. Beast master equals its stable tag; all five GitHub default branches differ from the pinned study source identities.
- AIDEAL `f2fc66558adb` (216 files) was independently verified by the root agent; this subaudit does not repeat that verification.

## Runtime and new-study plan

1. Preserve the 2026-11-16 study, source snapshots, environments, results, and manifests. Prepare the authorized new study under `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical`.
2. Pin each source to the exact stable commit above. Re-extract the public API definitions and per-library manifest; do not claim the historical API counts describe the new source releases.
3. Use a fresh environment at `/home/zshan011/apps/aideal/envs/2026-11-17-latest-stable`, Python >=3.11, because MDAnalysis 2.11.0 and MDAnalysisTests 2.11.0 require it. MDAnalysisTests must match MDAnalysis exactly. [Package metadata](https://pypi.org/pypi/MDAnalysis/2.11.0/json).
4. tslearn 0.10.0 requires Python >=3.10, NumPy >=1.24.3, SciPy >=1.10.1, scikit-learn >=1.5, Numba >=0.61, joblib >=1.2, and statsmodels >=0.14. PyTorch is optional for foundation/pytorch features. [Package metadata](https://pypi.org/pypi/tslearn/0.10.0/json).
5. Bind each actual import path and compiled extension/JAR to the chosen source, freeze dependencies, validate matching fixtures and positive/negative execution controls, and run zero model calls during preparation.
6. RDPro cached module JARs are labeled 0.10.1, but all eight differ from official Maven Central bytes/checksums. Its module JARs, overlay and helper require a fresh stable-source production build or proof of official runtime code equivalence before measured work.

## Remaining limits

- The prior RDPro runtime uses library_overlay.jar and public_helpers.jar ahead of official release jars; source equivalence does not certify those overlays as stable-only runtime. New build must bind compiled classes to selected stable sources and preserve helpers separately.
- Future new-study imports and optional dependency coverage require preflight after source selection and manifest regeneration.

Detailed source commits, current default-branch heads, official URLs, dates, package metadata, cluster paths, and receipt references are in `VERSION_AUDIT.json`.

## Post-audit runtime preparation

The user subsequently authorized latest stable releases for all six libraries. Progress and final runtime readiness are recorded separately in [RUNTIME_PREPARATION.json](RUNTIME_PREPARATION.json); this audit retains the original observed study identities. The new RDPro runtime has been freshly compiled from stable source, replacing the historical JAR ambiguity in the new study. The earlier study remains unchanged.
