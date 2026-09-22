# Shared evaluator and separate library repositories

[AIDEAL](https://github.com/ZhuochengShang/AIDEAL) holds the common evaluator, prompts, settings and study guides. Each library uses one companion source repository with five condition branches. The [library index](../studies/README.md) links all six projects and distinguishes the completed RDPro pilot from the five new preparations. GRAIL is a separate application project.

| Item | Purpose |
| --- | --- |
| AIDEAL repository | Shared controller, prompts, harness contracts, setup records and reviewed reports |
| One companion repository per library | Pinned source, license, original/upgraded documentation, aliases and hints when installed |
| Companion `main` | Navigation only; select a condition branch for source |
| Five condition branches | Original, README only, Alias only, Error hints only, Combined |
| Worktree | Separate working directory for a branch, sharing Git objects |
| Run output | New or resumed evidence under an explicit run ID; does not require another repository |

The five new preparations currently share one baseline commit per library. Their names reserve the intended conditions; no treatment or evaluation result exists yet. The source snapshots retain exact upstream trees, with new snapshot commit IDs and upstream provenance recorded in each guide. Older worktrees, jobs and evidence are preserved separately.

Researchers clone AIDEAL and the relevant companion repository. A fork is optional if they need their own writable remote. Five forks are unnecessary. AIDEAL and all six companion source repositories have public read access. Use [version handling](VERSIONS.md) and each study's guide for named worktrees and local attachment; do not switch a running study's checkout.

The [preparation index](../studies/index.json) records readiness. Runtime validation, independent held-out tasks and controls, tested treatments and a new frozen protocol are required before a matched run. Shared source alone does not supply a library-specific correctness oracle.
