# AIDEAL current status

Observed November 19, 2026 at 09:24:19 Pacific. All 14 Original/D1 R0 bank runs are complete, covering 5,646 outcomes across 2,823 targets. MDAnalysis D1 is 621/1519 (40.9%). These are native acceptance scores with model-written assertions, not independently checked task accuracy.

[Experiment guide](../experiments/2026-11-17-latest-stable-canonical/EXPERIMENT_GUIDE.md) · [Follow-through and live-check command](../experiments/2026-11-17-latest-stable-canonical/review/followthrough-2026-11-19/README.md) · [Tracker](../experiments/2026-11-17-latest-stable-canonical/reports/2026-11-18-professor-meeting/CHECKLIST.md)

Historical replay recovery completed on the cluster without model calls; all 14 historical arms now have completed results. Only its two-file binary-output fix is deployed in the new recovery release. Future README evidence and eight-condition changes passed development tests; real-library treatment admission, independent banks, R1/R2 and D2 remain pending. Old measured results and frozen inputs are preserved.

## Historical September 2026 pilot

The following is preserved historical evidence and does not describe the current run.

[Next RDPro study: scope, cost and selective README plan](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/2026-09-22-full-pipeline-plan/README.md>) — proposal only; no new paid run.

All seven repositories are now public. [Local folders and branches](LOCAL_REPOSITORIES.md) · [Public six-library index](https://github.com/ZhuochengShang/AIDEAL/blob/setup/2026-09-21-library-five-conditions/studies/README.md). Five new libraries have published baseline branches; their treatments and evaluations remain pending.

[Shared evaluator, prompts, settings and results](https://github.com/ZhuochengShang/AIDEAL/tree/evaluation/2026-09-21-rdpro-gpt-5.3-codex-five-conditions) · [RDPro source: five condition branches](https://github.com/ZhuochengShang/AIDEAL-RDPro) · [Source commit mapping](https://github.com/ZhuochengShang/AIDEAL-RDPro/blob/main/study.json)

AIDEAL and the companion RDPro repository are public. Its Original, README-only, Alias-only, Error-hints-only and Combined branches have source trees identical to the measured versions. Publication uses new commit IDs because inherited source history contains a malformed Git tree; original study commits and results remain intact locally. The published guide explains cloning and five separate worktrees. Full benchmark repetition still requires the private inputs, original documentation, pinned dependencies and a new local freeze.

**Historical study:** RDPro · GPT-5.3-Codex · five-condition pilot · 2026-09-21.

Use `2026-09-21-rdpro-gpt-5.3-codex-five-conditions` to identify this experiment. Historical `_v1` paths remain fixed so recorded evidence still resolves.

## Audited Codex results

**40/40 audience units are resolved, and all 120 trusted controls were independently verified.** Resolved includes both verified passes and verified failures; it does not mean every task passed. The audit and report bind frozen study `ed877ae454bc10bc69e27ed7cdc42b59d398f7919ad10ad94084b3dd08706f95`.

[Dashboard](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/runs/codex_v1/INDEX.html>) · [Controller report](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/runs/codex_v1/REPORT.md>) · [Independent audit](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/runs/codex_v1/audit/audit.json>) · [Result interpretation](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/runs/codex_v1/audit/INTERPRETATION.md>) · [Prompt-to-code worked example](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/treatment_comparison_v1/development/codex_preparation_v1/worked_example/PILOT_WORKED_EXAMPLE.md>)

| Condition | Micro first | Micro within budget | Puzzle first | Puzzle within budget |
|---|---:|---:|---:|---:|
| original | 3/4 (75%) | 3/4 (75%) | 1/4 (25%) | 1/4 (25%) |
| readme_only | 3/4 (75%) | 3/4 (75%) | 2/4 (50%) | 2/4 (50%) |
| alias_only | 3/4 (75%) | 3/4 (75%) | 1/4 (25%) | 1/4 (25%) |
| error_hints_only | 3/4 (75%) | 3/4 (75%) | 1/4 (25%) | 2/4 (50%) |
| combined | 3/4 (75%) | 3/4 (75%) | 1/4 (25%) | 1/4 (25%) |

Each kind has a fixed denominator of four per condition. First-attempt and within-budget results are separate; the difference is the number recovered by the one allowed repair. The paired report compares the same case/trial; complete-kind lift is `(recoveries − regressions) / 4 × 100` percentage points. One changed case is 25 points, so this single-trial, four-API pilot does not support broad or precise effectiveness claims.

### Recorded cost and exposure

Known provider-usage cost: **development $0.06331325 + audience $0.64590680**. The shared ledger commits **$0.70922005 of $5**, with all 60 reservations settled and none uncertain. Usage-based charges are not an invoice. Output tokens already include reasoning and are charged once.

| Hint condition | Eligible repair rounds | Matched rounds | Rounds with hint text | Delivered characters |
|---|---:|---:|---:|---:|
| error_hints_only | 4 | 0 | 0 | 0 |
| combined | 4 | 0 | 0 | 0 |

No hint text was delivered in this run. The hints-only condition recovered one puzzle on repair without receiving a generated hint; that extra pass cannot be credited to hint content. The run measured the matching policy but provides no observation of a delivered hint’s effect.
Alias-name mentions are lexical evidence, not proof of wrapper execution. Canonical JVM target tracing includes transitive calls and is unioned across fixtures. The generated readType hints retain ObjectInputStream framing/`???` limitations; the numTiles hint optionally mentions an alias absent in hints-only. These artifacts were not rewritten after seeing results.

All conditions used GPT-5.3-Codex with low reasoning, one trial, one repair, one provider attempt per round, 2,048 output tokens and 8,000/2,500/1,500-character document/alias/hint caps. Temperature 0 was omitted from the API call. The fixed README and bank remain unchanged; document truncation, missing dedicated readType coverage and actual input-length differences remain study limitations.

## Preserved separate evidence

The separate original/refactor freeze retains 48 controls and 1,104 development regression checks; it has no audience run and is excluded from this five-condition result. The older three-README pilot review hold remains active. Gemini/Pro failed-provider records are historical and are not relabelled as Codex results.

## Software publication

This local study result is separate from software-test counts and publication. Consult [the publication record](</Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/docs/PUBLICATION.md>) for the actual pushed commit and validation scope; this navigation update makes no new push claim.
