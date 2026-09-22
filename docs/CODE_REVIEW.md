# Review the code one boundary at a time

Read the [workflow](SUMMARY.md) and [condition matrix](VERSIONS.md), then follow this route. Start with each main function and expand helpers to answer a specific question. Source inspection alone does not prove runtime behavior.

| Order | Entry points | Review question |
| --- | --- | --- |
| Dispatch | [scripts/aideal](../scripts/aideal), [__main__.py](../workflow/__main__.py), [development_cli.py](../workflow/development_cli.py) | Which command, explicit inputs and output path are selected? |
| Intake | `prepare_study` in [preparation.py](../workflow/preparation.py); `attach` in [worktrees.py](../workflow/worktrees.py) | Are inputs resolved, baseline pinned and worktrees isolated? |
| Development exposure | `preview_library_improvements` / `propose_library_improvements` in [improvement_batches.py](../workflow/improvement_batches.py); [improvement_context.py](../workflow/improvement_context.py) | What reaches the model, and are scope, omissions and exact requests recorded? |
| Proposal meaning | [improvement_suggestions.py](../workflow/improvement_suggestions.py), [refactor_proposals.py](../workflow/refactor_proposals.py), [proposal prompt](../prompts/improvement_suggestions.md) | Are names checked and hints/refactors grounded in supplied evidence? |
| Installation | [treatment_bundles.py](../workflow/treatment_bundles.py), [treatment_versions.py](../workflow/treatment_versions.py), [source_refactors.py](../workflow/source_refactors.py) | Do exact artifacts land in intended arms with recoverable version records? |
| Contract/freeze | [condition_inputs.py](../workflow/condition_inputs.py), `freeze_conditions` in [condition_setup.py](../workflow/condition_setup.py) | Are arms matched, controls complete and runtime dependencies explicitly bound? |
| Audience context | `public_context` in [condition_context.py](../workflow/condition_context.py) | Are private answers excluded and hints delivered only after matching failures? |
| Execution/resume | `run_conditions` in [condition_evaluation.py](../workflow/condition_evaluation.py), [execution.py](../workflow/execution.py) | Are retries distinct from repairs and all reused evidence verified? |
| Optional Codex provider | [openai_codex_adapter.py](../workflow/openai_codex_adapter.py), [provider_budget.py](../workflow/provider_budget.py), [pilot guide](OPENAI_CODEX_PILOT.md) | Are final-answer phases selected, request settings recorded, and the shared reservation made before HTTP? |
| Scores | `report_conditions` in [condition_reporting.py](../workflow/condition_reporting.py) | Are denominators, matched pairs, unresolved units and costs retained? |

## Audited authoring and refresh

Follow [readme_authoring.py](../workflow/readme_authoring.py) for exact input/role bindings, [scala_owners.py](../workflow/scala_owners.py) for conservative lexical receivers, and [readme_spans.py](../workflow/readme_spans.py) for byte preservation. [readme_session.py](../workflow/readme_session.py) invokes the explicit [native bridge](../workflow/native_provider_bridge.py); [readme_receipts.py](../workflow/readme_receipts.py) checks saved provider/ledger evidence before a completed phase is reused. [Session tests](../tests/test_readme_authoring.py) exercise alteration, uncertain dispatch and preservation without a provider call.

For `selective_refresh`, start at `conditions_for` in [evaluation_setup.py](../workflow/evaluation_setup.py), then follow the frozen names into [evaluation.py](../workflow/evaluation.py) and [reporting.py](../workflow/reporting.py). [Design tests](../tests/test_evaluation_designs.py) retain legacy defaults and reject mixed names. See [configuration and output contracts](README_SESSIONS.md).

## Native documentation development

The native engine has a separate [CLI](../vendor/aideal_engine/src/aideal/cli.py). `readme_agent.py` and `doc_checks.py` are explicit compatibility facades; implementation lives in smaller modules.

- Discovery/evidence: [api_discovery.py](../vendor/aideal_engine/src/aideal/api_discovery.py), [api_visibility.py](../vendor/aideal_engine/src/aideal/api_visibility.py), [api_examples.py](../vendor/aideal_engine/src/aideal/api_examples.py).
- Authoring: [readme_generation.py](../vendor/aideal_engine/src/aideal/readme_generation.py), [readme_catalogue.py](../vendor/aideal_engine/src/aideal/readme_catalogue.py), [prompts.py](../vendor/aideal_engine/src/aideal/prompts.py).
- Checks: [doc_check_comprehension.py](../vendor/aideal_engine/src/aideal/doc_check_comprehension.py) routes grading/execution; [doc_check_execution.py](../vendor/aideal_engine/src/aideal/doc_check_execution.py) generates/runs API snippets. Model grading is not independent executable ground truth.
- Diagnosis/repair: [deepdive.py](../vendor/aideal_engine/src/aideal/deepdive.py), [docfix.py](../vendor/aideal_engine/src/aideal/docfix.py), [doc_repair.py](../vendor/aideal_engine/src/aideal/doc_repair.py).

Native development can use source/error history to improve docs. Held-out audience evaluation is separate; do not assume the development repair loop or score is the frozen procedure.

## Inspect evidence with the code

Follow one unit's exact public request → response code → checker request → raw verdict → terminal result. Then confirm matching case/trial and budgets across arms. [OUTPUTS.md](OUTPUTS.md) locates records; [SCORING.md](SCORING.md) explains them.

Relevant tests: [batch proposals](../tests/test_improvement_batches.py), [treatment versions](../tests/test_treatment_versions.py), [refactor recovery](../tests/test_refactor_recovery.py), [condition evaluation](../tests/test_condition_evaluation.py), [evidence integrity](../tests/test_condition_evidence.py). Controlled fixtures test meaningful boundaries/failures; they do not replace a real library build or oracle validation.

The [function index](FUNCTION_INDEX.md) and [interactive map](CODE_MAP.html) link definitions, calls, prompts and harness metadata. Open the HTML locally. Static names/imports are resolved where possible; callbacks, dynamic dispatch and external tools remain partial. Missing inbound edges are not unused-code proof. [pipeline_reference.json](pipeline_reference.json) defines the reading paths.
