# SedonaDB completed Original R0

Observed at 2026-11-18T01:29:29.296212+00:00. The frozen manifest, result keys, and recorded attempt requests contain the same **217 unique API IDs**, with no missing, extra, or duplicate IDs. Downloaded result and report hashes match the cluster.

| Item | Recorded result |
|---|---:|
| Condition | Original documentation |
| Model | `google:gemini-3.1-flash-lite` |
| Trials per API / repair rounds | 1 / 0 |
| Passed | **78/217 (35.94%)** |
| Failed | 139 |
| Recorded exclusions | 0 |
| Model calls / executions | 217 / 217 |
| Input / output tokens | 1,230,325 / 56,067 |
| Missing usage records | 0 |
| Run wall time | 748.4 seconds |
| Summed provider / execution time | 494.7 / 184.6 seconds |

This is native execution and audience-written assertion/witness success, not accuracy against an independent hidden oracle. The saved failure categories are 74 `runtime` and 65 `unknown`. The recorded exclusion count of zero does not establish that every failure is an audience error.

The [separate diagnostic audit](../../audits/sedonadb/README.md) identifies repeated generated helper-name failures and a confirmed documentation/runtime mismatch for `ST_ClosestPoint(geometry, geometry)`. Its partial diagnostic counts are not the final totals above. Its isolated reference checks did not modify benchmark results.

README authoring had no completion receipt at this observation. This packet makes **no README completion, execution validation, or treatment installation claim**.

- [Final result](r0/result.json)
- [Final evaluator report](r0/REPORT.md)
- [Exact-ID, token, time, and source-hash summary](SUMMARY.json)
- [Downloaded artifact hashes](FILES.json)
