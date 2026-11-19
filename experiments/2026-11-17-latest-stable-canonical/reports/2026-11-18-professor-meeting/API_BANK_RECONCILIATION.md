# API bank reconciliation

The older table combines catalog counts, bare name inventories, selected evaluation targets and SQL example counts. The current experiment uses explicit qualified target manifests. These numbers answer different questions and must not share a denominator without a source mapping.

The complete current selection contains **2,823 targets across seven banks**. RDPro contributes **261 Scala targets and 69 Java targets**, or 330 in total. A table that focuses on the Scala bank should report 261 and state the separate Java bank in a note. It should not rename the 330 combined count as Scala.

## Current selection and complete bank access

| Bank | Source version | Current targets | Complete readable list | Frozen selection manifest |
|---|---|---:|---|---|
| RDPro Java | 0.10.1 | 69 | [All 69 targets](banks/rdpro_java.tsv) | [Manifest](../../review/raptor-scope/strict-no-wrappers/api_manifest.java.json) |
| RDPro Scala | 0.10.1 | 261 | [All 261 targets](banks/rdpro_scala.tsv) | [Manifest](../../review/raptor-scope/strict-no-wrappers/api_manifest.scala.json) |
| SedonaDB | 0.5.0 | 217 | [All 217 targets](banks/sedonadb.tsv) | [Manifest](../../review/qualified-plan/libraries/sedonadb/inputs/api_manifest.json) |
| MDAnalysis | 2.11.0 | 1,519 | [All 1519 targets](banks/mdanalysis.tsv) | [Manifest](../../evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/selection-correction-final/api_manifest_public_nonwrapper.json) |
| tslearn | 0.10.0 | 354 | [All 354 targets](banks/tslearn.tsv) | [Manifest](../../evaluator-correction-2026-11-18/review/final-scope/tslearn/api_manifest.json) |
| mir_eval | 0.8.2 | 178 | [All 178 targets](banks/mir_eval.tsv) | [Manifest](../../review/qualified-plan/libraries/mir_eval/inputs/api_manifest.json) |
| Thumbnailator | 0.4.21 | 225 | [All 225 targets](banks/thumbnailator.tsv) | [Manifest](../../review/qualified-plan/libraries/thumbnailator/inputs/api_manifest.json) |


The linked TSV files retain every row from the authoritative current selection. Their partition check confirms 2,823 rows, no duplicate bank and API pairs and equality with all seven final manifests. The bank index links the original document mapping, source inventory and exclusions for each library.

## Why the earlier numbers differ

| Library | Earlier number and unit | Current selected target count | Supported explanation |
|---|---|---|---|
| RDPro | 280 owner qualified API families in a September catalog, 341 definition sites and 169 bare names. The separate native study used 161 bare names. | 261 Scala and 69 Java | Different catalog and evaluation scopes, different target identity and explicit wrapper and overload decisions. The 280 catalog was not the 161 target test bank. |
| SedonaDB | 201 documented SQL function pages and 322 SQL example blocks | 217 selected SQL target IDs in version 0.5.0 | A function can have several examples. The earlier sweep executed existing SQL, whereas the current audience generates a program for each retained target. No one to one mapping from 322 examples to 217 targets is established. |
| MDAnalysis | 1,032 public bare names in the 2.9.0 full surface plan. An older generated document cohort contained 661 entries. | 1,519 qualified targets in version 2.11.0 | Owner identity retains distinct class and module operations that bare names merge. The current discovery also covers the newer source and then removes nineteen audited entries from 1,538. |
| tslearn | 235 bare names in the saved full manifest | 354 qualified targets in version 0.10.0 | Distinct owners and callable kinds produce a different count. The final audit removes eight import hooks or forwarding operations from 362 current candidates. |
| mir_eval | 148 bare names in the earlier result | 178 qualified targets in version 0.8.2 | The source and identity rules differ. The earlier source reconciliation found that register_colormap no longer appears as a declared callable in the pinned source. This does not imply that the other 147 names map one to one to the current 178 IDs. |
| Thumbnailator | 149 bare names in the earlier result | 225 qualified targets in version 0.4.21 | The qualified inventory preserves owner identity and supported constructors. An earlier audit also found an if statement mistaken for a declaration and excluded nonpublic operations. Thus neither the increase nor the decrease of one subcount measures library growth alone. |

The current RDPro strict audit starts with 452 candidate sites. It excludes 72 wrappers or adapters, 25 unimplemented bodies, three abstract constructors, fifteen bodyless methods and seven redundant overloads. Its 330 retained sites comprise 271 methods and 59 concrete constructors. The older 171 July count is another separate scope. It contains 161 intent selected Scala names plus ten additional generated README names, across a broader Beast module selection.

The earlier paper says that the 280 family catalog comes from a newer source revision than the 161 name study. The saved September study plan records source revision `5ee41a6`, while the source receipt shows that this publication snapshot has the same full source tree as official commit `547f7f9` used in the historical source comparison. Consequently, the available evidence does not support explaining the count change through source growth alone. The report treats source identity, inventory rules and study scope separately.

## What the audit verified

| Evidence | Verification level | Location |
|---|---|---|
| RDPro 280 families, 341 sites and 169 names | recorded plan metadata | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/2026-09-22-gpt-5.3-codex-broad-study/development/study_plan.json) |
| MDAnalysis 1,032 names | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_mdanalysis_full1032_v4_A1/experiments/mdanalysis/docs/full_1032/api_manifest.json) |
| MDAnalysis 661 result entries | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_mdanalysis_setup/experiments/mdanalysis/docs/comprehension_A2_generated661_zero.json) |
| tslearn 235 names | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_tslearn_full235_freeze/experiments/tslearn/docs/eval/api_manifest.json) |
| mir_eval 148 result entries | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_mir_eval_A1/experiments/external/mir_eval/docs/eval/A1/comprehension.json) |
| Thumbnailator 149 result entries | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_thumbnailator_A1/experiments/external/thumbnailator/docs/eval/A1/comprehension.json) |
| SedonaDB 201 function pages and 322 examples | recounted artifact entries | [Source artifact](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_workflow/studies/sedonadb/evidence/sql_reference_inventory.json) |

The 280 value has support in the saved plan metadata. This task did not independently reconstruct every historical family grouping. The historical paper also states 1,397 MDAnalysis sites, 343 tslearn sites, 179 mir_eval sites and 340 Thumbnailator sites. Those site counts describe older extraction records. The current manifests do not validate those totals, and this report does not treat them as current public API counts. The MDAnalysis 2.9.0 plan explicitly records its 1,397 site count.

The existing source reconciliation describes an intermediate discovery stage before final qualification and exclusions. For example, it reports 1,053 current MDAnalysis bare names and 237 tslearn bare names. Those values are not alternatives to 1,519 and 354 qualified targets. A single short name can represent several class or module operations. No count in that intermediate CSV should replace the final bank manifest.

## Native usage bank versus independent test bank

The current bank fixes the API identity, library version, allowed documentation, fixtures, scaffold and execution policy. It asks the audience to write its own usage example and assertions. Therefore, the TSV explicitly records `audience_written_native_usage_example` and `fixed_independent_oracle = not_configured`. A native pass confirms the configured execution and witness checks. It does not independently prove task output correctness.

A fixed microbenchmark bank instead supplies the same task, input and independent expected output across conditions. A puzzle bank supplies a broader task that may require API composition. The historical RDPro study has a separate bank with sixteen micro tasks and sixteen puzzles. It is not the current 330 target usage bank and does not establish complete task coverage of other libraries.

R0 means the initial audience program. R1 and R2 mean additional attempts to repair a failed program under fixed resources. They do not mean different API inventories or Git branches. The current Original and existing D1 cohort uses R0 only. Changing the selected API bank, runtime or shared input contract requires a new recorded protocol rather than silently relabeling previous results.

## Source navigation

- [All seven current banks and their source records](banks/README.md)
- [Current bank partition proof](banks/BANK_PARTITION_VERIFICATION.json)
- [Machine readable reconciliation and hashes](API_BANK_RECONCILIATION.json)
- [RDPro 171 denominator and source identity](../../review/raptor-scope/history-171/AUDIT.json)
- [RDPro final selection decisions](../../review/raptor-scope/strict-no-wrappers/ALL_CANDIDATE_DECISIONS.json)
- [MDAnalysis old source and full surface plan](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/GRAIL_mdanalysis_full1032_v4_A1/experiments/mdanalysis/docs/full_1032/FULL_SURFACE_2X2_PLAN.md)
- [Intermediate source name comparison](../../review/audit/latest-source/SOURCE_SCOPE_RECONCILIATION.json)
- [Intermediate declaration count table](../../review/api-audit/COUNT_RECONCILIATION.csv)
- [Historical independent RDPro task contracts](/Users/clockorangezoe/Documents/phd_projects/code/geoAI/AIDEAL_WORKSPACE/03_Experiments/rdpro/2026-09-22-gpt-5.3-codex-broad-study/bank/bank.json)
