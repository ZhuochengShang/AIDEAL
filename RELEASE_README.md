# AIDEAL canonical API evaluator release

This branch publishes the exact 225-file evaluator allowlist for
`2026-11-17-canonical-api-a6e8bb84fe32`, whose content identity is
`a6e8bb84fe32644837603ee4c73a1100f5f51519dfdecbdc36c4ffc992ba98c1`.
`DEPLOYMENT_MANIFEST.json` binds every deployed file by SHA-256. The publication
adds that manifest, this guide, and the unchanged public
`THIRD_PARTY_NOTICES.md`, for 228 files in total.

The release is a versioned evaluator snapshot parented to the prior published
release commit `fc70c0732730a3d8a33f441895ce3c8c588018aa`. It does not modify
or merge into `main`. Files outside the deployment allowlist remain outside this
snapshot without being classified as obsolete. Credentials, private launchers,
study outputs, library checkouts, and machine-specific launch catalogs are not
part of the release.

## Running the toolkit

Start at this repository root and install the requirements for the desired
runtime. Read [README.md](README.md), [cluster setup](docs/CLUSTER_RUN.md),
[Original R0 evaluation](docs/ORIGINAL_MICRO_RUN.md), and
[README generation](docs/README_GENERATION_RUN.md). These commands only show
launcher options:

```sh
python scripts/run_original_micro.py --help
python scripts/run_readme_generation.py --help
python scripts/preflight_cluster_libraries.py --help
python scripts/install_generated_readme.py --help
```

Supply the frozen catalog, source evidence inventories, selection receipts,
runtimes, and fixtures for the intended study. Canonical selection is opt-in;
old configurations retain their historical selection behavior. The new host API
policy chooses one eligible reviewed definition per name across languages within
a library, prioritizing parameter count. Unreviewed definitions and identified
forwarders, wrappers, facades, and no-body declarations are excluded. A discarded
same-name definition is not thereby proved semantically equivalent to the winner.

Registered SQL uses its own source-attested alias policy. The SedonaDB 0.5.0
study validates the full 226-name registry and retains 217 names after excluding
nine explicit aliases. User-defined and variadic SQL signatures do not receive
an invented finite maximum arity. Remaining distinct names are not claimed to
be semantically disjoint.

Prepared target metadata requests the selected declaration or SQL operation
consistently across conditions. A prompt request alone does not prove that a
host-language call executed that overload. The Sedona adapter separately checks
SQL target use and materialization; audience assertions remain the correctness
check. Original documentation inputs remain available in full, with retrieval
and exposure determined by the frozen experiment configuration.

## Latest stable study source provenance

The following versions were audited on November 17, 2026. The execution source
checkouts retain each official upstream commit. The public condition branches
start from parentless publication snapshots with the exact same Git tree,
including file modes and gitlinks. A publication snapshot commit is distinct
from the official upstream commit and does not preserve its upstream ancestry.
Runtime binaries and distributions have separate frozen identities; matching a
version string alone does not establish a source build identity.

| Library | Version / tag | Official upstream commit | Initial publication commit |
|---|---|---|---|
| rdpro | 0.10.1 / `beast-0.10.1` | [547f7f912131](https://bitbucket.org/bdlabucr/beast/commits/547f7f912131a8032f6b5d26991415a5faf05cef) | [88effa8abe57](https://github.com/ZhuochengShang/AIDEAL-RDPro/commit/88effa8abe57b1c844cdd59581e4cade8d0807dc) |
| mdanalysis | 2.11.0 / `package-2.11.0` | [ace84dde1363](https://github.com/MDAnalysis/mdanalysis/commit/ace84dde1363e32aa94cd3f29a42c2f590bd0575) | [ce6e8ddbfe7f](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/commit/ce6e8ddbfe7fb32244c84be689744e20deda8c43) |
| tslearn | 0.10.0 / `v0.10.0` | [f6072f237313](https://github.com/tslearn-team/tslearn/commit/f6072f237313d610413359ecc899cdb9038f4b7e) | [e32e94a758b2](https://github.com/ZhuochengShang/AIDEAL-tslearn/commit/e32e94a758b274d980c1bd1634684cea0cc641dd) |
| mir_eval | 0.8.2 / `0.8.2` | [8db0b3812e20](https://github.com/mir-evaluation/mir_eval/commit/8db0b3812e2032544c1fc00d02d4256cab043f3d) | [967a2466f1de](https://github.com/ZhuochengShang/AIDEAL-mir_eval/commit/967a2466f1dec09730850b9785a7a972ad0955d7) |
| thumbnailator | 0.4.21 / `0.4.21` | [c9d99613878b](https://github.com/coobird/thumbnailator/commit/c9d99613878bbbf1f4d9369585b4cb5352c3b474) | [62a5fff8f577](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/commit/62a5fff8f57705ab105bdd7a42d81b99ee88e889) |
| sedonadb | 0.5.0 / `apache-sedona-db-0.5.0` | [751453f04cd6](https://github.com/apache/sedona-db/commit/751453f04cd6e09842adf3073b2b3dac7d1777bc) | [64d0e42731f4](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/commit/64d0e42731f4014da53aed40ae7bd9e2964330ab) |

SedonaDB's full official tree retains all four upstream gitlink entries. Their
external contents are left uninitialized and excluded from the configured source
inventory unless separately declared. The SQL runtime is the separately verified
official 0.5.0 Python wheel. This full latest-stable snapshot is distinct from the
older release-derived pilot snapshot.

## Thirty condition branches

Each row links the five reserved condition refs under
`study/2026-11-17-latest-stable-canonical/`. All thirty initially point to their
library's untreated exact-tree publication snapshot. Branch names identify roles;
they do not establish that a treatment has been installed or evaluated. Subsequent
README installation updates only its designated unchecked refs and records the
exact commits. Historical study branches and repository main branches are preserved.

| Library | Original | README only | Aliases only | Error hints only | Combined |
|---|---|---|---|---|---|
| rdpro | [original](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |
| mdanalysis | [original](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |
| tslearn | [original](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |
| mir_eval | [original](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |
| thumbnailator | [original](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |
| sedonadb | [original](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-17-latest-stable-canonical%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-17-latest-stable-canonical%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-17-latest-stable-canonical%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-17-latest-stable-canonical%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-17-latest-stable-canonical%2Fcombined) |

## Publication checks

The release is tested from a standalone export using its own engine and workflow
modules. The publication receipt records 104 passing offline contract tests,
standalone import locations, launcher help checks, the exact Git tree and commit,
and preservation of the source checkout and index. No model calls or benchmark
runs are part of publication validation. A credential-pattern scan covers only
the allowlisted files and publication additions; it does not inspect excluded
private launchers. Branch publication and offline controls are not experiment
results.
