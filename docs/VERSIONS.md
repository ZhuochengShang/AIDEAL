# Conditions and version navigation

Attachment pins a clean library baseline and creates isolated worktrees. A checkout, treatment bundle, frozen protocol and result run are different identities. Folder names alone do not prove what was installed or evaluated.

## Condition matrix

| Condition ID | Documentation | Executed library | Extra context |
| --- | --- | --- | --- |
| `original` | Original | Original | Common public task/scaffold and checker feedback |
| `readme_only` | Selected generated/improved README | Original | Common context |
| `alias_only` | Original | Original plus additive forwarding aliases | Minimal alias interface |
| `error_hints_only` | Original | Original | Matching hints after verified failure |
| `combined` | Same README as `readme_only` | Same aliases as `alias_only` | Same interface/hints as individual treatments |
| `refactor_only` | Original | Explicit API-preserving source refactor | Common context |

`five_arm` selects the first five; `refactor_pair` Original and Refactor only; `six_arm` all six. Combined excludes refactoring. This is not a full factorial design. Alias interface text is part of the alias treatment; keep it narrow and identical in Combined.

The separate three-README protocol defaults to `Original README`, `Generated README`, and `Repaired README` on one backend. Explicit `readme_evaluation.design: selective_refresh` instead uses `Unchanged generated README`, `Selected API refresh`, and `Full README refresh`, with the unchanged generated base as baseline. These document identities and frozen records are not interchangeable with the source-treatment matrix. See [audited README sessions](README_SESSIONS.md); prepared candidates are not evaluated results.

## Authoritative records

| Identity | Record |
| --- | --- |
| Baseline and five source paths | `STUDY/attachment.json` |
| Input/configuration snapshot | `STUDY/source.json` and preview manifest/batches |
| Installed treatment version | `STUDY/treatments/<proposal-sha256>/application.json` |
| Current treatment pointer | `STUDY/treatments/current.json` |
| Separate refactor version | `STUDY/refactors/<version>.json`; pointer `refactors/current.json` |
| Frozen protocol | `FREEZE/frozen.json`, including controller/source/artifact identities and controls |
| Audience run | Chosen `RUN/identity.json`, unit records and reports |

Use full stored hashes. Git HEAD alone does not bind uncommitted toolkit changes. Current pointers do not replace immutable version records; an old freeze stays tied to its original bytes.

```sh
python scripts/aideal versions --study /absolute/path/to/study
```

This navigator is read-only. Open returned paths rather than switching branches in the original library repository.

## Source changes

Five initial checkouts—`Original/source/`, `README only/source/`, `Alias only/source/`, `Error hints only/source/`, `Combined/source/`—share a baseline in an isolated `repository.git`. Their `.aideal/` scaffolding is preparation infrastructure.

`bundle-proposals` combines selected batches into a complete treatment version. `install-treatments` writes aliases to declared new source paths and metadata to `.aideal/treatments/` in applicable arms. A bundle replaces the prior owned treatment set; it is not an implicit append of whichever files were regenerated.

`install-refactor` accepts an explicit `source_refactor` manifest: baseline revision, `preserve_public_api: true`, validation plan, and changed paths with baseline hashes plus full replacement bindings (or deletion). It creates `Refactor only/<version>/source/` on a separate versioned branch from the baseline. It does not edit existing arms or the original repository. See [source_refactors.py](../workflow/source_refactors.py).

The API-preservation flag states a requirement, not a proof. Build and test argument/default/result/exception behavior. Duplicate scans require comparable analyzer settings/scope; lower candidate counts alone do not establish equivalent behavior.

## State labels

- **Prepared:** source/context exists; no performance claim.
- **Proposed / installed, unvalidated:** artifacts/commits exist; build, behavior and exposure still need checks.
- **Frozen:** complete declared controls and exact inputs were validated and bound.
- **Pending / unverified:** selected work or infrastructure validation is unresolved.
- **Complete:** all selected units have terminal checked outcomes; report scope and denominators.

Resume only matching identities. Changed implementation, tasks, checker, model or treatment requires a new validated freeze. Retain earlier evidence and review holds. See [outputs](OUTPUTS.md) and [scores](SCORING.md).
