# Six-library freshness and runtime evidence audit

Checked 2026-11-17T22:19:49.088811+00:00. **All six pins remain the latest official stable versions, and all six stable tags still resolve to the pinned commits.** No upgrades are needed for these subject versions.

| Library | Pinned / latest stable | Fresh official evidence | Recorded runtime |
|---|---|---|---|
| Beast / RDPro | 0.10.1 / 0.10.1 | [Official release metadata](https://repo.maven.apache.org/maven2/edu/ucr/cs/bdlab/beast/maven-metadata.xml) | 0.10.1 |
| MDAnalysis | 2.11.0 / 2.11.0 | [Official release metadata](https://github.com/MDAnalysis/mdanalysis/releases/tag/package-2.11.0) | 2.11.0 |
| tslearn | 0.10.0 / 0.10.0 | [Official release metadata](https://github.com/tslearn-team/tslearn/releases/tag/v0.10.0) | 0.10.0 |
| mir_eval | 0.8.2 / 0.8.2 | [Official release metadata](https://github.com/mir-evaluation/mir_eval/releases/tag/0.8.2) | 0.8.2 |
| Thumbnailator | 0.4.21 / 0.4.21 | [Official release metadata](https://repo.maven.apache.org/maven2/net/coobird/thumbnailator/maven-metadata.xml) | 0.4.21 |
| SedonaDB | 0.5.0 / 0.5.0 | [Official release metadata](https://github.com/apache/sedona-db/releases/tag/apache-sedona-db-0.5.0) | 0.5.0 |

Exact tags, commits, URLs, fetch times, raw-response hashes and receipt hashes are in [upstream.json](upstream.json). Public release metadata was fetched at 22:16–22:17 UTC on November 17. Thumbnailator’s GitHub latest-release endpoint returns 404; its Maven stable-release metadata and source tag both verify 0.4.21. Default/development branches are not treated as stable updates.

Saved runtime evidence records Python 3.12.15 for MDAnalysis/tslearn/mir_eval, matching official package versions and source implementation comparisons. MDAnalysisTests also matches 2.11.0. Beast uses the fresh 0.10.1 production source build; Thumbnailator uses the official 0.4.21 JAR with JDK17 and Java8 compilation compatibility. SedonaDB uses its official 0.5.0 wheel in the retained Python3.10 environment. The copied Sedona identity receipts match the hashes in its control receipt.

**This is receipt verification, not a new runtime test.** Scientific and Thumbnailator native controls ran on `c7a8f0af0504`; saved code equivalence supports `a6e8bb84fe32`. Beast controls span these releases. They do not establish that current `b9f31cd` was executed or that every API and optional format works. The earlier failed Java operator fixture is preserved alongside its corrected controls.

**The project remains on hold for API-surface revision.** The current operator status prohibits generation and evaluation. The archived `review/audit/latest-readiness/REVIEW_STATUS.json` still says `READY_FOR_USER_REVIEW` and 1695; treat that as a historical snapshot. Those counts are not the revised approved API surface.

Three inspected local runtime-receipt mirrors add one final newline relative to their recorded cluster bytes. Their contents are otherwise exact; the report records both hashes instead of claiming byte identity. Optional dependency gaps and the untested network-dependent MDAnalysis fetch are retained in the JSON. No live runtime rehash, subject execution, installation, cleanup, source/config change, or model call was performed.
