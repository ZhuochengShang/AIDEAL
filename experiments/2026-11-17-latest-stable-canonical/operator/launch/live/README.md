# Running R0 and README generation

Snapshot: 2026-11-18T01:29:57.894433+00:00. Two jobs run at a time; corrected JVM jobs wait for the original queue. [Interactive trace viewer](STATUS.html) · [Full workflow](../../../RUN_FLOW.md) · [Live progress snapshot](LATEST_PROGRESS.json).

| Request | API | Status | Input tokens | Output tokens | Seconds | Exact input and output |
|---|---|---|---:|---:|---:|---|
| r0-pass | python:mir_eval.alignment.absolute_error | pass | 2133 | 78 | 3.419 | [request](20261118T010432Z/r0-pass/attempt/request.json), [response](20261118T010432Z/r0-pass/attempt/response.txt), [usage](20261118T010432Z/r0-pass/attempt/provider.json) |
| r0-failure | python:mir_eval.alignment.evaluate | fail | 2165 | 77 | 1.163 | [request](20261118T010432Z/r0-failure/attempt/request.json), [response](20261118T010432Z/r0-failure/attempt/response.txt), [usage](20261118T010432Z/r0-failure/attempt/provider.json) |
| readme-distill | Whole-corpus chunk | complete | 40006 | 1469 | 8.19210406858474 | [request](20261118T010432Z/readme-distill/request.json), [response](20261118T010432Z/readme-distill/response.txt), [usage](20261118T010432Z/readme-distill/provider.json) |
| readme-entry | python:mir_eval.alignment.absolute_error | complete | 5596 | 765 | 3.3506230683997273 | [request](20261118T010432Z/readme-entry/request.json), [response](20261118T010432Z/readme-entry/response.txt), [usage](20261118T010432Z/readme-entry/provider.json) |

The failed R0 program calls `mir_eval.alignment.evaluate` and then asserts that the returned dictionary contains `Precision`. The assertion fails. Its [program](20261118T010432Z/r0-failure/attempt/api_test.py) and [stderr](20261118T010432Z/r0-failure/attempt/stderr.txt) remain unchanged. R0 has no repair round, so this failure is retained as baseline evidence. It is not a provider outage.

README entries are structurally accepted authoring outputs; their examples have not yet been execution-validated. The two paths use separate output directories and do not share R0 failure feedback.

Run `qualified-description-recovery/launch/progress_all.py` on the cluster for current counts; this saved page does not automatically refresh.

[Completed mir_eval results](../completed/mir_eval/README.md) · [Corrected reader and recovery queue](../../../RUN_RECOVERY.md).
