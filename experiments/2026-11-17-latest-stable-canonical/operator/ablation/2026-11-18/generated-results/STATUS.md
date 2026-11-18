# Generated README R0 snapshot

Observed 2026-11-18T18:05:09.391421+00:00. Actual recorded model is `google:gemini-3.1-flash-lite`. One program per target, zero program repairs. This snapshot does not alter or restart active experiments.

| Bank | State | Recorded / selected | Pass | Fail | Input tokens | Output tokens |
|---|---|---:|---:|---:|---:|---:|
| mir_eval | complete | 178/178 | 119 | 59 | 436,815 | 39,441 |
| thumbnailator | complete | 225/225 | 83 | 142 | 455,856 | 47,313 |
| sedonadb | complete | 217/217 | 100 | 117 | 511,581 | 56,231 |
| tslearn | running | 135/362 | 90 | 45 | 325,850 | 32,982 |
| rdpro_java | complete | 69/69 | 5 | 64 | 133,382 | 14,820 |
| rdpro_scala | running | 21/261 | 1 | 20 | 47,939 | 4,068 |
| mdanalysis | pending | 0/1538 | 0 | 0 | 0 | 0 |

RDPro comprises the Java and Scala banks. Their combined result is unfinished; do not treat the completed Java result as the full RDPro score. MDAnalysis has not started in this queue.

All banks have zero recorded provider-blocked rows and zero partial checkpoint lines. The controller PID 2863977 is live. Actual tslearn and RDPro Scala worker processes were found, matching the running states.

Tokens for running banks cover recorded checkpoint rows only; in-flight calls are excluded. All recorded model usage rows have usage fields and zero missing-usage calls. These totals concern this Generated README evaluation, not README authoring, aliases, hint development or later repair studies.

Completed result hashes match their completion receipts. Each completed bank folder contains its compact `result.summary.json`, `completion.json` and `REPORT.md`; raw prompts/programs/logs stay at the recorded cluster paths.

## Cluster evidence

- `mir_eval`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/mir_eval`
- `thumbnailator`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/thumbnailator`
- `sedonadb`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/sedonadb`
- `tslearn`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/tslearn`
- `rdpro_java`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_java`
- `rdpro_scala`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/rdpro_scala`
- `mdanalysis`: `/home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/ablation-2026-11-18/generated-readme-r0/mdanalysis`

The run changes the selected documentation and its retrieval granularity. It preserves the frozen evaluator and other matched settings. These observations do not establish documentation causality for each failure.


## RDPro Java diagnostic review

The completed Java bank passes 5/69 tasks, versus 13/69 under Original documentation. Its 64 failures comprise 63 compilation failures and one runtime assertion failure. The reviewer checked all execution settings, 13 frozen comparison fields, all 365 classpath files and representative classes inside the configured library jar. No shared missing-classpath or condition source-path mixup was found.

Three saved requests contain demonstrably incorrect generated README guidance: the GeoTiffMetadata constructor, a static call to the instance Intersections.compute method, and Statistics.isValid fresh-state behavior. Separately, 13 compile failures violate the body-only Java response format by inserting imports or other invalid structure. These examples distinguish documentation errors from audience response errors; they do not establish documentation as the cause of every failure. See `RDPRO_JAVA_REVIEW.md` and its JSON evidence. No run, README, or result was edited.
