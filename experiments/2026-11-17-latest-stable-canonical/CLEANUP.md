# Cleanup and retained history

The current six-library study uses `study/2026-11-17-latest-stable-canonical/` condition branches. All 30 current library refs remain available on GitHub and in the verified local/cluster Git stores.

Removed 26 obsolete setup branch labels after checking their exact commits. The central `setup/2026-09-21-library-five-conditions` commit remains reachable from preserved main. For each of the five other libraries, five September preparation branches pointed to one baseline; one archive tag now preserves that baseline before removal.

| Library | Preserved preparation baseline |
|---|---|
| SedonaDB | [Archive tag](https://github.com/ZhuochengShang/AIDEAL-SedonaDB/tree/archive%2Fpreparation-2026-09-21-five-conditions) |
| MDAnalysis | [Archive tag](https://github.com/ZhuochengShang/AIDEAL-MDAnalysis/tree/archive%2Fpreparation-2026-09-21-five-conditions) |
| tslearn | [Archive tag](https://github.com/ZhuochengShang/AIDEAL-tslearn/tree/archive%2Fpreparation-2026-09-21-five-conditions) |
| mir_eval | [Archive tag](https://github.com/ZhuochengShang/AIDEAL-mir_eval/tree/archive%2Fpreparation-2026-09-21-five-conditions) |
| Thumbnailator | [Archive tag](https://github.com/ZhuochengShang/AIDEAL-Thumbnailator/tree/archive%2Fpreparation-2026-09-21-five-conditions) |

All 87 other branches in the audited seven repositories were preserved, including current study refs, previous evaluator releases, completed experiments and the interrupted 1,348-target RDPro cohort. The later central review-publication branch is an additional branch, not part of that before/after count.

Local cleanup pruned only the matching obsolete remote-tracking refs. Active local branches, HEAD, index and user edits stayed intact. The 12 inspected old/new cluster checkouts had no matching obsolete setup refs to remove; all 30 current condition refs were verified.

- [Exact old branch names and commits](review/audit/github-cleanup/CLEANUP_PROPOSAL.md)
- [Remote deletion/tag verification](review/audit/github-cleanup/REMOTE_CLEANUP_RECEIPT.json)
- [Local reconciliation](review/audit/github-cleanup/LOCAL_TRACKING_CLEANUP_RECEIPT.json)
- [Cluster reconciliation](review/audit/github-cleanup/CLUSTER_CLEANUP_RECEIPT.json)
- [Redundant transfer-cache cleanup](review/audit/CACHE_CLEANUP.json)

The cache cleanup removed only verified redundant transfer artifacts with retained matching copies. Measured requests, responses, outputs, source snapshots, reusable dependencies and historical guides were preserved. No blanket cache reset or history rewrite was performed.
