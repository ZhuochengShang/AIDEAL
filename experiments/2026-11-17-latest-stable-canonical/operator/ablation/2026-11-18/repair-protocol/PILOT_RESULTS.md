# Native hint repair pilot

The workflow completed six real Gemini requests without a provider error,
incomplete response, or infrastructure failure. Both conditions still failed the
single task after two repairs. This checks the mechanism and its records; it does
not establish a performance improvement.

Target `python:mir_eval.transcription.validate`, one trial per condition,
`gemini-3.1-flash-lite`, fresh initial programs, maximum two repairs.
The hint was developed from the same API bank. This is development evidence,
not held-out generalization or a complete five-condition comparison.

| Condition | R0 passes | Through R1 | Through R2 | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|
| Original | 0/1 | 0/1 | 0/1 | 8,764 | 841 |
| Error Hints | 0/1 | 0/1 | 0/1 | 8,905 | 866 |
| Total usage | | | | 17,669 | 1,707 |

| Round | Original failure | Error Hints failure | Native hint exposure |
|---|---|---|---|
| R0 | Intervals and pitches have different lengths | Same error with embedded guidance | Library emits the hint after the failed call |
| R1 | At least one non-positive pitch | Same error | Repair prompt includes the preceding emitted hint |
| R2 | Boolean mask has length 5 for an array of length 4 | Same error | Prior length hint is absent; only the latest feedback is supplied |

Both versions corrected the first length mismatch. The next program exposed a
second requirement, positive pitch values, and the final attempted repair used
an incompatible mask. The added length hint reached the model through the
ordinary exception message, but it did not improve final success in this trial.

Total elapsed time was **69.6 seconds**. Recorded provider time was 17.94 seconds
and program execution time was 9.85 seconds; approximately 41.8 seconds covered
preparation, verification, scheduling and reporting. Repeated native preparation
needs a throughput review before applying this controller to all 2,850 targets.
There is no automatic expansion from this pilot.

The two native execution checks with scripted answers separately passed
fail → fail → pass, with **zero model calls**. Those tests are software validation
and are labelled `offline_mock`; they are not included in the live table.

- `PILOT_RESULT_SUMMARY.json` contains actual per-request tokens, time, exit codes,
  hint emission and prompt exposure.
- `evidence/live/original/` and `evidence/live/error_hints/` contain every delivered
  prompt, response, executed program, stdout, stderr and round receipt.
- `LOCAL_EVIDENCE_CHECK.json` verifies the downloaded stable artifacts.
- `PILOT_QUEUE.json`, `PILOT_PREFLIGHT.json`, and `PILOT_STATE.json` record the
  bounded two-job plan and its successful completion.
