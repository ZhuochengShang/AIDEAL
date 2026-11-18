# Original R0 and README authoring completed

Verified November 18, 2026 at 08:56 AM Pacific. All 14 current jobs passed completion-artifact checks across six libraries and seven language banks. No interrupted provider jobs remain, and no restart or new model request was needed for this check.

| Library | Original R0 passed / targets | README entries authored |
|---|---:|---:|
| RDPro | 37 / 330 (11.2%) | 330 / 330 |
| MDAnalysis | 612 / 1,538 (39.8%) | 1,538 / 1,538 |
| tslearn | 219 / 362 (60.5%) | 362 / 362 |
| mir_eval | 128 / 178 (71.9%) | 178 / 178 |
| Thumbnailator | 104 / 225 (46.2%) | 225 / 225 |
| SedonaDB | 78 / 217 (35.9%) | 217 / 217 |

There are 2,850 recorded R0 outcomes and 2,850 authored README entries. A completed run includes failed programs. The R0 column reports native executable checks under the selected bank, not proof that every assertion is an independent correctness oracle. README completion means authored and structurally accepted, not execution validated. Generated-README evaluation, repairs, puzzles and the five-condition ablation are later stages.

## Recovery verification

- tslearn completed 362 targets with 219 passes. It reused 223 previous outcomes; its former provider timeout succeeded on a later physical attempt at logical R0. The original timeout record remains available.
- MDAnalysis completed 1,538 entries under validation policy `source-note-todo-v3`. It imported 1,348 recorded responses, including one previously rejected source-note reference, and made 203 new author calls for the remaining work. Replayed calls retain their original usage records and are not counted as newly spent tokens.
- Completion-artifact and README hashes match their supervisor receipts. All 4,044 file references in 1,348 replay receipts were verified against the original evidence. Both recovery controllers exited and their locks are free.

## Interpretation limits

No provider-blocked targets remain. The [completed-run failure review](failure-review.md) identifies 11 MDAnalysis targets affected by missing optional dependencies, 2 by Biopython compatibility, and 2 conditional fallback classes absent at runtime. SedonaDB has 65 SQL errors labeled unknown, including helper-call failures and documentation/implementation signature mismatches. Some execution timeouts and native crashes remain unresolved. These are follow-up findings, not reasons to restart the completed queue unchanged.

Keep the original outcomes and denominators. Correcting dependencies, fixtures or target eligibility requires a separately recorded environment/bank; derived error classification can reuse the saved evidence without new model calls.

The libraries retain the selection policies documented in the [cross-library audit](../../../review/raptor-scope/maintenance/SELECTION_POLICY.md); only RDPro has the completed strict wrapper/stub review. Do not describe these banks as identically filtered.

[All-library progress](PROGRESS.json) · [14 completion receipts](completion-checks.json) · [Independent recovery audit](audit.json) · [Recovery commands and output folders](README.md).
