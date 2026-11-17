# AIDEAL deployed evaluator snapshot

This branch contains the exact allowlisted evaluator files deployed as
`2026-11-17-r0-readme-f2fc66558adb`. Their SHA256 hashes are recorded in `DEPLOYMENT_MANIFEST.json`.
The publication additionally includes this entry guide and the existing public
`THIRD_PARTY_NOTICES.md` without changing its content.

This is a versioned deployment snapshot, not the complete main-branch workspace.
Files on main that are outside the deployment allowlist are intentionally absent
here. That does not mark those files as obsolete. This branch preserves main's
history through its parent commit and does not change or merge into main.

Start from this repository root. Install the dependencies appropriate for the
intended runtime using the supplied requirements files. The release does not
contain credentials, the private quick launcher, generated study payloads,
library source checkouts, or environment-specific launch catalogs.

Read `README.md`, `docs/CLUSTER_RUN.md`, `docs/ORIGINAL_MICRO_RUN.md`, and
`docs/README_GENERATION_RUN.md` for setup and experiment semantics. Inspect the
available launcher options without making model calls:

```sh
python scripts/run_original_micro.py --help
python scripts/run_readme_generation.py --help
python scripts/preflight_cluster_libraries.py --help
```

Supply a study catalog and library runtime/configuration paths for the target
machine. This branch does not imply that every named condition has been generated
or evaluated. Library source and treatment branches are versioned separately in
the six AIDEAL library repositories.

Publication validation runs from a standalone export of this branch, with its
own engine and workflow paths, and performs no model calls. The parent task keeps
the exact export checks and publication commit receipt alongside the study audit.

## Source inventory and library branches

The full RDPro source audit identifies 629 public Scala method names and 719 public
Java method names. These are separate language/name counts, not a deduplicated
union, overload-level coverage, runnable guarantees, or completed evaluation
counts. The November 16 pilot remains a separate frozen scope.

The following 35 study branches were published without changing the historical
branches or main in any library repository. Placeholders are intentionally
visible: alias-only and error-hints-only contain no installed treatments yet;
combined contains README changes only where installed. The five full-source
RDPro branches initially point to the measured original snapshot. At publication,
MDAnalysis README generation was still pending.

| Library / study | Original | README only | Aliases only | Error hints only | Combined |
|---|---|---|---|---|---|
| AIDEAL-RDPro / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |
| AIDEAL-RDPro / full source Nov 17 | [original](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-rdpro-entire-source%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-rdpro-entire-source%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-rdpro-entire-source%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-rdpro-entire-source%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-RDPro/tree/study%2F2026-11-17-rdpro-entire-source%2Fcombined) |
| AIDEAL-SedonaDB / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |
| AIDEAL-MDAnalysis / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |
| AIDEAL-tslearn / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |
| AIDEAL-mir_eval / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |
| AIDEAL-Thumbnailator / pilot Nov 16 | [original](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Foriginal) | [readme-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Freadme-only) | [alias-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Falias-only) | [error-hints-only](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Ferror-hints-only) | [combined](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/study%2F2026-11-16-gemini-3.1-flash-lite%2Fcombined) |

Use the matching study catalog to bind each library checkout, native runtime,
fixtures and documentation. Machine-specific checkout locations are recorded in
the study's publication audit, outside this portable evaluator snapshot. The
SedonaDB November study uses the measured 0.5.0 release-derived source snapshot,
not the older historical preparation branch. Its recorded Git tree omits four
upstream gitlinks and `r/sedonadb/src/rust/Cargo.toml`; every recorded leaf matches
the official release leaf hash and mode. The measured runtime is the separately
verified official 0.5.0 wheel.
