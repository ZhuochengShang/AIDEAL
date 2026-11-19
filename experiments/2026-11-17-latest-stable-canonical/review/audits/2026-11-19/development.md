# AIDEAL development workflow audit

Audit date: 2026-11-19T08:26:40.472364+00:00. Cluster snapshot: 2026-11-19T08:19:35.429622+00:00.

Current Original/D1 native R0 workflow is distinct from the not-yet-ready full eight-arm independent micro/puzzle/R2/D2 study. 164 focused tests pass, but known readiness and validity gaps remain.

No API calls or experiment mutations were made. A subsequent authorized future-only scanner fix is recorded separately below. This report covers source discovery, original documentation, README authoring, treatment construction, and the gates for later evaluation.

## What works, and what is ready

| Step | Stage | Current state | Review trail |
|---|---|---|---|
| 1 | Pin source and inventory | implemented; current banks frozen | `api_registry.configured_api_details → api_public_inventory.qualified_inventory_details → api_canonical_selection._select_qualified` |
| 2 | Map original documentation | implemented; current seven mappings readable | `original_documents → original_target_texts` |
| 3 | Generate README D1 | implemented and historical D1 exists; quality gaps remain | `readme_generation.find_or_create` |
| 4 | Run current Original/D1 R0 | active measured cohort; native acceptance only | `run_verified_readme_continuation → comprehension_check → doc_check_execution` |
| 5 | Classify and select development failures | implemented intake; current cohort not automatically a held-out bank | `source_hint_development.build_development_preview → native_r0_evidence.build_native_r0_preview` |
| 6 | Create aliases | proposal/install code exists; current cohort has no alias treatment | `preview_improvements → propose_improvements → bundle_proposals → apply_treatments` |
| 7 | Embed native hints | supported subset implemented/tested; current cohort has no hint treatment | `propose_native_hints → validate_native_hints → install_native_hints` |
| 8 | Freeze independent factorial micro/puzzle evaluation | blocked before paid launch | `read_condition_config → validate_conditions → freeze_conditions → run_conditions` |
| 9 | R1/R2 audience repair | shared controlled runner exists; current native cohort R0 only | `evaluation_runner.run_unit repair loop / evaluation_context.public_context` |
| 10 | D2 README repair and fresh evaluation | development R0 operator exists; full paper R2→D2→held-out study pending | `revise_readme_from_replay.prepare/revise → run_corrected_readme_comparison` |

## Current source and document evidence

The current study selects 2,823 targets. These counts describe the current selected bank, not every source declaration. “Documented” means an exact reviewed excerpt exists; shared README prose can still be present for an undocumented target. Source comments are a separate authoring input.

| Bank | Selected APIs | Exact original excerpts | Nonempty source descriptions supplied by selected ledger |
|---|---:|---:|---:|
| rdpro_java | 69 | 0 | 0 |
| rdpro_scala | 261 | 16 | 0 |
| sedonadb | 217 | 211 | SQL registration path |
| mdanalysis | 1519 | 1061 | 1098 |
| tslearn | 354 | 222 | 276 |
| mir_eval | 178 | 177 | 178 |
| thumbnailator | 225 | 225 | 0 |

RDPro Java, RDPro Scala and Thumbnailator have zero nonempty descriptions in their current selected compiler ledger records. This does **not** mean their source files have no comments. The consumer fills missing descriptions with an empty string and authoring passes that empty value. Qualified authoring also disables repository test mining. Therefore the earlier description “source comments and selected tests are sent for every API” is inaccurate for these current runs.

All seven configured `integration_tasks` files and all seven configured `aliases` files are absent. These are inactive placeholders in the current Original/D1 native run, not missing dependencies of that R0 path. No `D2`, alias or hint condition directory exists in the active `explicit-inputs-r0` cohort; its directories are `continuation`, `operator`, and `preflight`. Older study artifacts are not evidence that current source versions have these treatments.

## Findings and concrete gates

### DEV-01 — Eight-factorial design is not implemented

Supported designs are five_arm, refactor_pair and six_arm. README+alias, README+hint, and alias+hint factorial arms are absent. Config validation rejects an eight-arm design before a model call.

Review: [DESIGNS](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_inputs.py:11), [read_condition_config](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_freeze.py:28).

**Next action.** Extend the shared condition schema, factor routing, context exposure and treatment matching once; add all-eight-arm positive/negative and resume tests before publishing a new freeze.

### DEV-02 — Current API banks are not independent task banks

All seven current configurations point to absent integration_tasks files. The native R0 path does not use those files and can run legitimately without them. Independent condition evaluation requires a bound bank with complete micro coverage, at least one held-out puzzle, per-case oracle/reference/negative controls, and successful controls for every backend.

Review: [read_bank](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_inputs.py:31), [validate_conditions](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_freeze.py:209), [freeze_conditions](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_freeze.py:276).

**Next action.** Author and validate independent micro/puzzle tasks; freeze development and held-out partitions. Do not relabel native self-check acceptance as independent task correctness.

### DEV-03 — Qualified README authoring still omits test examples and compiler comments

Qualified generation sets test_index={} even when repository tests exist. It only passes the selected definition description as source_doc. Current selected RDPro Java69/Scala261 and Thumbnailator225 ledger entries all lack description; Python descriptions are retained. This remains live code, not solely a frozen-D1 artifact.

Review: [find_or_create](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/readme_generation.py:331), [find_or_create](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/readme_generation.py:386), [qualified_inventory_details](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/api_public_inventory.py:623).

**Next action.** For a new authoring version, bind exact source-comment spans and reviewed exact-API test snippets. Preserve owner identity, constructor/setup dependencies and provenance; reject ambiguous bare-name matches. Keep frozen D1 untouched.

### DEV-04 — README generation checks structure, not executable truth

find_or_create validates required sections and exact identities but does not execute each generated example. Correct APIs/signatures and a complete README do not establish that constructor, receiver, parameter and semantic advice is correct.

Review: [find_or_create](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/readme_generation.py:133), [validate_entry call](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/readme_generation.py:469).

**Next action.** Add bounded source-consistency checks plus isolated example build/run gates to future README artifacts. Report these as development validation, separate from independent task outcomes.

### DEV-05 — Aliases can be installed without an equivalence receipt

Proposal checks enforce target/name/source boundaries and Python syntax. apply_treatments creates local commits with applied_unvalidated status. Condition freeze verifies added wrapper files, unchanged baseline code and task controls, but does not require per-alias forwarding/default/return/error equivalence tests.

Review: [alias proposal validation](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/improvement_suggestions.py:96), [apply_treatments](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/treatment_versions.py:345), [match_treatments](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_inputs.py:153).

**Next action.** Require a hash-bound alias validation receipt covering representative valid, boundary/default and failing inputs before treating installation as accepted or launching the new alias ablation.

### DEV-06 — Native hint editing is gated but does not cover every failure or library

Native hint path handles existing literal exception messages in Python/Java/Scala. Four distinct programs run on baseline/candidate. Unsupported/compiler/nonliteral/ambiguous failures remain evidence, not patches. Registered SQL lacks a reviewed implementation adapter. install_native_hints leaves an explicit checkout uncommitted; branch/commit/rebuild orchestration is separate.

Review: [_literal_site](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/native_hints.py:51), [propose_native_hints](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/native_hints.py:223), [validate_native_hints](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/native_hints.py:348), [install_native_hints](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/native_hints.py:410), [_qualified_library_definitions](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/improvement_context.py:166).

**Next action.** Publish a per-failure intake disposition and a supported-language matrix; prepare trusted controls/adapters, commit/rebuild the verified edits and bind the actual treatment source before evaluation.

### DEV-07 — Development labels alone do not prove held-out independence

Native evidence intake verifies original R0 provenance and excludes supplied held-out IDs/APIs. Generic alias-log intake rejects explicit evaluation/held-out labels but permits unlabeled logs; condition bank checks disjoint IDs plus a nonempty holdout_review string. These checks do not prove semantic, fixture or answer independence.

Review: [build_native_r0_preview](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/native_r0_evidence.py:225), [_development_errors](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/improvement_context.py:64), [read_bank](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_inputs.py:68), [read_condition_config](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_freeze.py:61).

**Next action.** Freeze explicit development/evaluation manifests before treatment authoring; bind provenance and task/fixture partitions. Require a reviewed overlap audit, not only renamed case IDs.

### DEV-08 — Native retry memory is not scoped by trial identity

R0 supplies no historical failures. At retry the native loop queries failures_for(API), which filters only function and fail/fixed status, not run/task/condition/version. Deterministic FIX_GUIDE advice also enters that log. The independent condition runner instead uses previous attempt feedback and native emitted hints without shared-log lookup.

Review: [native attempt loop](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/doc_check_execution.py:519), [ErrorLog.failures_for](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/error_log.py:113), [FIX_GUIDE feedback logging](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/doc_check_execution.py:689), [public_context](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/workflow/evaluation_context.py:10).

**Next action.** Do not just change max_fix_rounds to2. Use trial-scoped feedback or a declared frozen memory/advice policy, with isolation tests and recorded prompt exposure. This does not contaminate the current R0 loop.

### DEV-09 — Existing D2 operator is same-bank R0 development revision

revise_readme_from_replay requires completed corrected replay, diagnoses failed D1 entries, and accepts examples after corrected native execution. It explicitly is not a D1/R2 deep dive or held-out correctness experiment. The matched comparison operator is Original/D1/D2 native R0 only.

Review: [module scope](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/scripts/revise_readme_from_replay.py:1), [prepare](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/scripts/revise_readme_from_replay.py:120), [example validation](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/scripts/revise_readme_from_replay.py:337), [comparison identity](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/scripts/run_corrected_readme_comparison.py:213).

**Next action.** For the paper plan, drive D2 only from development failures after the declared repair policy, freeze D2, and conduct fresh held-out evaluation with matched tasks. Keep this existing operator labelled development.

## Subsequent narrow inventory correction

The source audit confirmed three currently selected MDAnalysis targets are empty classes declared only inside `except ImportError` branches. With the configured real dependencies installed, these attributes do not exist. The affected targets are `MDAnalysis.coordinates.H5MD.MockH5pyFile`, `MDAnalysis.coordinates.IMD.MockIMDClient`, and `MDAnalysis.coordinates.GSD.MockHOOMDTrajectory`. [Source and runtime evidence](fallbacks.json).

A future-only fix now retains the exception type, handler line, try line and imported modules. It excludes empty base-free undecorated import-failure placeholders from default candidates. It keeps ordinary empty classes, real nonempty fallbacks, inherited/decorated/metaclass classes and broad or shadowed exception cases. See [scanner guard](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/api_public_inventory.py:100), [typed handler provenance](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/vendor/aideal_engine/src/aideal/api_public_inventory.py:233), and [new fixtures](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/tests/test_import_failure_stubs.py:22).

After this change, **161 inventory tests and 78 subtests passed in 1.33s**. [Log](evidence/aideal-audit-2026-11-19-inventory-tests.log). These test invocations overlap earlier suites and are not an additional disjoint test count. No frozen inventory, cluster release or current denominator was edited. The current 2,823 selected targets still include these three historical selection errors; any future exclusion requires a new reviewed manifest.

## Safe launch decisions

| Proposed action | Gate today |
|---|---|
| Resume unchanged current Original/D1 R0 | Uses its existing frozen identity, runtime and provider readiness gates; this audit does not authorize an altered protocol. |
| Launch eight factorial arms | Rejected by current design schema. Implement and test factor routing first. |
| Launch independent micro/puzzle study without a bank | Missing file fails before model call. Reference, wrong-output and no-target controls must validate every backend. |
| Launch native-hint conditions without successful paired validation | Rejected by native validation and exact installed-source checks. |
| Install an alias proposal | Allowed as **unvalidated**; installation alone is not scientific acceptance. Current condition gates lack a separate per-alias equivalence receipt. |
| Increase native repair rounds to two | Mechanically possible, but controlled-study readiness is not automatic. Scope memory and FIX_GUIDE advice before interpreting repair gains. |
| Run existing D2 operator | Requires corrected replay and runtime readiness; it is same-bank development and cannot establish held-out D2 improvement. |

## Bounded fix for future README authoring

1. Add a source-bound authoring context manifest for each exact defining API. Preserve the source commit, file hash, comment span, signature, public access path and required owner/constructor context. Extract compiler comments from verified source; do not synthesize missing comments.
2. Add reviewed test-snippet mappings keyed by exact API identity and owner. Bind test file/line/hash and include needed setup. Do not restore ambiguous bare-name or unrelated sibling matches. If no snippet was supplied, say that explicitly rather than claiming no repository test exists.
3. Add tests for two same-name owners, constructor context, absent comments, exact source changes, omitted/ambiguous test mappings and payload hashes. Preserve qualified scope and fail closed on ambiguous context.
4. Generate a new document version in a new output directory. Add source-consistency and isolated example execution checks before accepting entries. Keep structural validation, example execution and independent task correctness as separate statuses.
5. Leave frozen D1 and its measured results unchanged. Compare the revised document under a newly frozen, matched evaluation.

## Validation performed

164 focused offline tests passed. These establish tested mechanisms, not bug-free operation across every library or production treatment.

- **106 passed in 98.74s**. [Log](evidence/aideal-audit-2026-11-19-development-tests.log).

```bash
cd /Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:vendor/aideal_engine/src:. /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python -m unittest test_qualified_readme test_qualified_api_selection test_native_hints test_improvement_suggestions test_condition_evaluation test_treatment_versions test_readme_entry_prompt -q
```

- **58 passed in 14.422s**. [Log](evidence/aideal-audit-2026-11-19-development-gates-tests.log).

```bash
cd /Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:vendor/aideal_engine/src:. /Users/clockorangezoe/miniconda3/envs/geo_llm_spark/bin/python -m unittest test_native_r0_evidence test_source_hint_development test_readme_replay test_corrected_readme_comparison -q
```

A separate synthetic check confirmed that `ErrorLog.failures_for` returns an old-trial suggestion for the same API without taking run, task, condition or version arguments. [Reproduction result](/tmp/aideal-audit-2026-11-19-memory-proof.json). It does not show leakage in the current R0 run, which explicitly suppresses that history.

Machine-readable findings, per-step inputs/outputs, code hashes and exact cluster receipts are in [development.json](development.json). [Cluster snapshot](/tmp/aideal-audit-2026-11-19-development-cluster.json).
