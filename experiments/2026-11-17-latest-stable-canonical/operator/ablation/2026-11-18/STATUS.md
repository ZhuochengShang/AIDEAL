# Current ablation status

Observed **2026-11-18T20:01:37.561162+00:00**. This is a saved review snapshot. Cluster jobs continue independently of the local app. [Machine-readable snapshot](PROGRESS.json) · [Completed result evidence](resume-check/EVIDENCE.json).

## Generated README R0

**6/7 language banks are complete.** MDAnalysis continues. All banks use `gemini-3.1-flash-lite`, one trial and zero program repairs, with the frozen per-bank Original evaluation settings.

| Bank | Original R0 passes | Generated README R0 |
|---|---:|---|
| mir_eval | 128/178 | 119/178 (66.9%) |
| thumbnailator | 104/225 | 83/225 (36.9%) |
| sedonadb | 78/217 | 100/217 (46.1%) |
| tslearn | 219/362 | 231/362 (63.8%) |
| rdpro_java | 13/69 | 5/69 (7.2%) |
| rdpro_scala | 24/261 | 19/261 (7.3%) |
| mdanalysis | 612/1538 | Running: 993/1538 processed; 431 passes so far |

No provider-blocked targets were recorded in this snapshot. Program failures remain measured failures. These are native execution and configured-check outcomes, not independently adjudicated puzzle accuracy. RDPro Java's lower result includes documented README errors and program-format errors; the read-only audit found matching runtime settings and all 365 classpath files. The measured documentation remains frozen. [Diagnostic review](generated-results/RDPRO_JAVA_REVIEW.md).

## Fresh mir_eval repair comparison

The following study generates fresh R0 programs, then supplies the previous program and public execution feedback for up to two repairs. Counts are cumulative successes. Running rows are partial, not final rates over 178 targets.

| Condition | State | Targets recorded | R0 pass | By R1 | By R2 |
|---|---|---:|---:|---:|---:|
| original | Complete | 178/178 | 132 | 151 | 154 |
| generated_readme | Complete | 178/178 | 112 | 148 | 158 |
| error_hints | Running | 138/178 | 99 | 112 | 117 |

Do not combine these fresh R0 scores with the earlier R0-only results above. In this completed pair, Generated README starts lower but recovers more failed programs by R2. This supports reporting initial usability and repair separately; one trial does not establish a general advantage or a causal explanation for individual failures. Error Hints effectiveness remains unconfirmed while that condition runs.

The earlier one-target pilot verified native hint delivery at R1, but both conditions failed through R2. It used six calls, 17,669 input tokens and 1,707 output tokens. [Exact pilot traces](repair-protocol/PILOT_RESULTS.md).

## Alias queue resumed

The earlier scheduler stopped a whole bank at its first invalid proposal. The published review controller now records complete rejected proposals and proceeds to the next untouched batch. It never installs rejected code. Provider failures and incomplete responses still pause the affected bank, while other banks can continue.

The resumption reused all 63 earlier exposed batches in the five incomplete banks without new model calls. It started a single-worker queue for the remaining **2,090 API targets in 297 batches**. RDPro Java's separate nine-batch review of 69 targets was already complete. SedonaDB's SQL bank remains unsupported by the current source-alias adapter.

| Bank | Queue state | Review progress |
|---|---|---|
| mir_eval | complete | 178/178 APIs reviewed; 67 schema-valid alias candidates |
| rdpro_scala | running | 0 new batches reviewed |
| thumbnailator | pending | 0 new batches reviewed |
| tslearn | pending | 0 new batches reviewed |
| mdanalysis | pending | 0 new batches reviewed |

“Reviewed” means the model response was accepted as a candidate, proposed no alias, or was rejected with a reason. It does not mean every API needs an alias. Schema-valid candidates still need build and paired behavior tests. **No new aliases are installed in the treatment branches yet.**

The controller passed 11 offline integration tests. Five source/manifest/response continuation checks passed before launch. [Queue and rules](aliases/review-all-batches/README.md) · [Launch receipt](resume-check/alias_recovery/LAUNCH.json) · [Preparation and tests](resume-check/alias_recovery/PREPARATION_AND_TESTS.json).

## What is still pending

| Component | Current evidence | Required next step |
|---|---|---|
| mir_eval embedded hints | One source message installed in Error Hints only and Combined; paired controls and runtime checks passed | Complete the current audience repair comparison |
| MDAnalysis embedded hints | One source message installed in both hint-bearing branches; isolated source and dependent-module checks passed | Prepare and run a matched audience repair study |
| Alias-only / Combined evaluation | Full candidate review underway; Combined currently has README and hints where available | Validate aliases, install identical files in both branches, verify runtime identity, then launch matched evaluation |
| RDPro, tslearn, Thumbnailator hints | No accepted native hint under the current literal-message patcher | Support and validate additional source edit cases; keep missing treatment cells explicit |
| SedonaDB source treatments | No compatible SQL alias/native-hint adapter | Implement and validate the adapter before claiming these conditions |
| Other libraries' R1/R2 | Original and Generated R0 evidence retained | Prepare matched repair settings and runtime checks |
| Deep-dive README repair | Planned after R2 | Diagnose selected remaining failures, freeze revised README, run a fresh evaluation |

All 1,672 Original failures remain evidence, including failures unsuitable for source-message edits. A compiler or dependency failure is not automatically a source-hint candidate. Native hint validation and alias forwarding tests do not prove audience success. [Source commits and runtime checks](native-install/NATIVE_HINT_CONDITIONS.md).

## Review locations and resume commands

```text
operator/ablation/2026-11-18/
  STATUS.md, PLAN.md, PROGRESS.json       timestamped plan and progress
  resume-check/                          completed results and recovery receipts
  repair-protocol/                       checked R0/R1/R2 runner and specs
  aliases/review-all-batches/             active alias review controller and plan
  native-install/                        installed hint source commits and controls
ablation-2026-11-18/
  generated-readme-r0/<bank>/             prompts, programs and native R0 results
  matched-repairs/mir_eval/<condition>/   fresh R0/R1/R2 traces
  development/aliases-reviewed/<bank>/   complete/rejected model responses and candidate index
```

```bash
ssh lab
cd /home/zshan011/apps/aideal/studies/2026-11-17-latest-stable-canonical
/home/zshan011/apps/aideal/venv/bin/python operator/ablation/2026-11-18/progress.py
```

After checking process ownership and the failure reason, the same saved alias queue can be resumed with:

```bash
/home/zshan011/apps/aideal/venv/bin/python \
  operator/ablation/2026-11-18/aliases/review-all-batches/start_review.py --launch
```

Do not launch a second copy while its controller is active. The supervisor verifies exclusive ownership and frozen inputs. Local and GitHub records are synchronized snapshots, not continuous live copies. Complete request, response and execution files remain under each cluster output. [Full experiment guide](../../../EXPERIMENT_GUIDE.md).
