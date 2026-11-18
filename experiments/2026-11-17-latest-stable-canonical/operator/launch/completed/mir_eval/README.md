# Completed mir_eval evidence

Collected 2026-11-18T01:19:15.017306+00:00. Model `google:gemini-3.1-flash-lite`; source version `0.8.2`.

| Stage | Completed scope | Result | Input tokens | Output tokens | Recorded time |
|---|---:|---|---:|---:|---:|
| Original micro R0 | 178 API targets, one trial, zero repairs | 128 pass / 50 fail (71.91%) | 400,170 | 31,869 | 774.5 s run wall time |
| README authoring | 178 entries + 2 corpus-distillation calls | authored, not execution validated | 1,128,968 | 171,805 | 774.14 s first-to-last-call span |
| Total recorded tokens | 358 model calls | No missing provider-usage calls | 1,529,138 | 203,674 | Stages overlap; do not add their wall times |

Both outputs contain exactly the same 178 selected API identities as the frozen manifest, with no duplicates, missing IDs or extras. The final README and every author-call request/response hash match the completion receipt.

All 50 R0 failures are recorded as runtime failures, with zero infrastructure exclusions. The stored raw and infrastructure-adjusted scores are both `0.719`. Native R0 success uses executed audience-written assertions and required witnesses; it is not an independently hidden-oracle score. README authoring is not a Generated README evaluation result, and no source-treatment installation is claimed here.

R0 recorded 178 executions. Its summed model-call time is 332.08 s and summed program-execution time is 391.60 s. README authoring recorded 178 entry calls and 2 distillation calls, with 720.66 s summed provider time. The original raw artifacts remain unchanged.

## Files

- [Full result and per-API metrics](r0/result.json)
- [Original R0 report](r0/REPORT.md)
- [Generated README](readme/docs/LLM_readme.md)
- [README completion receipt](readme/completion.json)
- [Authoring result](readme/result.json)
- [Coverage, time, token and evidence-hash summary](SUMMARY.json)

Only these final artifacts were downloaded. Full execution programs and detailed attempt histories remain in the cluster output paths recorded in the summary.
