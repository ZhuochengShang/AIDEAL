# Current API bank index

These files partition the authoritative current selection without changing its rows, order within each bank or selection policy. The seven banks contain 2,823 distinct qualified target IDs. Original and existing D1 use the same IDs. The rows describe audience written native usage examples, with no fixed independent output oracle.

| Bank | Source version | Current targets | Complete readable list | Frozen selection manifest |
|---|---|---:|---|---|
| RDPro Java | 0.10.1 | 69 | [All 69 targets](rdpro_java.tsv) | [Manifest](../../../review/raptor-scope/strict-no-wrappers/api_manifest.java.json) |
| RDPro Scala | 0.10.1 | 261 | [All 261 targets](rdpro_scala.tsv) | [Manifest](../../../review/raptor-scope/strict-no-wrappers/api_manifest.scala.json) |
| SedonaDB | 0.5.0 | 217 | [All 217 targets](sedonadb.tsv) | [Manifest](../../../review/qualified-plan/libraries/sedonadb/inputs/api_manifest.json) |
| MDAnalysis | 2.11.0 | 1,519 | [All 1519 targets](mdanalysis.tsv) | [Manifest](../../../evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/selection-correction-final/api_manifest_public_nonwrapper.json) |
| tslearn | 0.10.0 | 354 | [All 354 targets](tslearn.tsv) | [Manifest](../../../evaluator-correction-2026-11-18/review/final-scope/tslearn/api_manifest.json) |
| mir_eval | 0.8.2 | 178 | [All 178 targets](mir_eval.tsv) | [Manifest](../../../review/qualified-plan/libraries/mir_eval/inputs/api_manifest.json) |
| Thumbnailator | 0.4.21 | 225 | [All 225 targets](thumbnailator.tsv) | [Manifest](../../../review/qualified-plan/libraries/thumbnailator/inputs/api_manifest.json) |

The authoritative combined list is [SELECTED_API_BANK.tsv](../../../evaluator-correction-2026-11-18/review/final-scope/SELECTED_API_BANK.tsv). [BANK_PARTITION_VERIFICATION.json](BANK_PARTITION_VERIFICATION.json) records hashes and equality checks.

## Source and original document evidence

| Bank | Original corpus map | Full source inventory | Selection and exclusion evidence |
|---|---|---|---|
| RDPro Java | [Coverage manifest](../../../review/raptor-scope/strict-no-wrappers/original-docs/manifest.json) | [Inventory](../../../review/raptor-scope/strict-no-wrappers/api_inventory.java.json) | [Audit](../../../review/raptor-scope/strict-no-wrappers/ALL_CANDIDATE_DECISIONS.json) |
| RDPro Scala | [Coverage manifest](../../../review/raptor-scope/strict-no-wrappers/original-docs/manifest.json) | [Inventory](../../../review/raptor-scope/strict-no-wrappers/api_inventory.scala.json) | [Audit](../../../review/raptor-scope/strict-no-wrappers/ALL_CANDIDATE_DECISIONS.json) |
| SedonaDB | [Coverage manifest](../../../review/qualified-api/sedonadb/original-docs/manifest.json) | [Inventory](../../../review/qualified-api/sedonadb/api_inventory.sql.json) | [Audit](../../../review/qualified-api/sedonadb/canonical-selection.json) |
| MDAnalysis | [Coverage manifest](../../../review/qualified-api/mdanalysis/original-docs/manifest.json) | [Inventory](../../../review/qualified-api/mdanalysis/api_inventory.python.json) | [Audit](../../../evaluator-correction-2026-11-18/fixture-development-v1/mdanalysis/selection-correction-final/exclusion_audit.json) |
| tslearn | [Coverage manifest](../../../review/qualified-api/tslearn/original-docs/manifest.json) | [Inventory](../../../review/qualified-api/tslearn/api_inventory.python.json) | [Audit](../../../evaluator-correction-2026-11-18/review/final-scope/tslearn/audit.json) |
| mir_eval | [Coverage manifest](../../../review/qualified-api/mir_eval/original-docs/manifest.json) | [Inventory](../../../review/qualified-api/mir_eval/api_inventory.python.json) | [Audit](../../../evaluator-correction-2026-11-18/review/final-scope/mir_eval/candidate_review.json) |
| Thumbnailator | [Coverage manifest](../../../review/qualified-api/thumbnailator/original-docs/manifest.json) | [Inventory](../../../review/qualified-api/thumbnailator/api_inventory.java.json) | [Audit](../../../review/qualified-api/thumbnailator/canonical-selection.json) |

The full inventories can contain candidates outside the final selection. Apply the final manifest before computing study denominators. Original corpus matches describe the reviewed retrieval map, not verified completeness of every API description or absence of all other documentation. Source inventories and original document manifests remain in place rather than duplicating large files here.

## Prompt and execution evidence

Each current target has an Original request and a D1 request under the cluster cohort `explicit-inputs-r0/continuation/<bank>/<condition>/execution/run_<qualified-target-key>/attempt_<number>/`. The files include `request.json`, `response.txt`, the complete generated program, `provider.json`, `execution.json`, `stdout.txt` and `stderr.txt`. The exact attempt directory can differ after a provider interruption. Provider retry attempts do not create program repair rounds.

For complete small examples, open the [meeting report](../MEETING_REPORT.md) and its linked trace folders. The historical [prompt index](../../../evaluator-correction-2026-11-18/review/prompt-audit/INDEX.html) covers 2,850 earlier target records and must not replace the current 2,823 target manifest.
