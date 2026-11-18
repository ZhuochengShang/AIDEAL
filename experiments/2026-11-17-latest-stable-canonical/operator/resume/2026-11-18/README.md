# November 18 recovery

RDPro finished all 330 Original R0 targets (37 passed) and authored all 330 README entries. Compiler/runtime failures are recorded outcomes, not unfinished provider requests.

| Interrupted job | Recovery | Preserved evidence |
|---|---|---|
| tslearn Original R0 | Resume the exact frozen command at R0 |223 completed outcomes; the timed-out API passed on retry |
| MDAnalysis README | Running validation-only replay in a separate output folder |1,334 completed entries and the returned response previously rejected for discussing a source `Todo` note |

Only `readme_validation.py` changes production behavior (+18 lines, no new helper). It allows a source-backed inline reference to a TODO note while still rejecting unfinished placeholders. 26 regression tests pass locally and on the cluster. The existing replay engine checks request identity and records reused responses without adding their tokens again.

The author release is based on the original f3 evaluator; using the newer Raptor API-selection implementation would invalidate replay. A separate current-toolkit release includes both the strict Raptor selector and this validator fix. Earlier frozen releases remain intact.

## Check live progress

```bash
ssh -o ClearAllForwardings=yes lab
/home/zshan011/apps/aideal/venv/bin/python /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical/operator/resume/2026-11-18/progress_resumed.py
```

Add `--json` for exact output paths and replay counts. The operator scripts here reuse the existing frozen supervisor; they are recovery receipts, not new AIDEAL workflow commands.

| Output | Cluster path below the study root |
|---|---|
| Resumed tslearn R0 |`qualified/runs/original/tslearn/tslearn/`|
| New MDAnalysis README |`qualified-readme-source-note/authoring/mdanalysis/mdanalysis/`|
| Original MDAnalysis attempt |`qualified/authoring/mdanalysis/mdanalysis/`|
| tslearn recovery process |`operator/resume/2026-11-18/STATE.json`|
| MDAnalysis recovery process |`qualified-readme-source-note/STATE.json`|

[Validator tests](tests.log) · [Preparation](author-preparation.json) · [Failure diagnosis](failure-audit.md) · [Original recovery checks](recovery-audit.json).

## Verified recovery snapshot

Observed 2026-11-18T08:56:36.479728+00:00. [All-library progress](PROGRESS.json) · [Checkpoint/replay verification](resume-verification.json) · [Previously rejected response now validates](REAL_RESPONSE_VALIDATION.json).

The live monitor supersedes this saved snapshot. Existing calls retain their original provider receipts; replay references them rather than adding their tokens to the new-call total.
