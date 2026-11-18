# RDPro overlap and structural target-selection audit

`overlap_audit.json` records the complete source-scope comparison: 629 Scala names / 1,310 public production method sites and 719 Java names / 1,663 sites. The 80 equal cross-language names are equal spellings, not proven equivalent operations. All 171 historical names remain within Scala 629; the additional 458 arise from full-source scope. The historical 171 was 88 shared-document names plus 83 generated-complement names; 161 was a separately validated subset.

`module_distribution.csv`, `language_name_groups.csv`, `cross_language_name_overlap.csv`, `historical171_membership.csv` and `forwarding_examples.csv` provide inspectable detail. Within-module name counts overlap and must not be summed as global unique names.

`prior_design_review.json` explains why the previous dedup report did not enforce global maximum-parameter-first selection or wrapper exclusion. The full compiler inventory stays unchanged.

## Latest stable source and stricter policy

Beast 0.10.1 uses the same pinned source tree as this audit. The final reviewed input is `reviewed_structural_site_ledger.json`, with hashes in `structural_provenance.json`. This is a reviewed **structural policy**, not a proof of general semantic equivalence.

The v2 policy excludes facade paths, no-body declarations, all root-call bodies and thin blocks containing only local bindings followed by a call. It quarantines unresolved accessors, constructor factories and unclassified bodies. Remaining eligibility requires recognized assignment, loop or operator work, or a literal-return leaf. There are 1,354 eligible declaration sites spanning 708 global bare names; the canonical-selection helper must elect the greatest parameter count among eligible sites and resolve exact-arity ties deterministically. Earlier candidate scenarios in `candidate_rule_counts.json` are diagnostic alternatives, not the final selected denominator.

`residual_unknown: true` marks all 714 unresolved records. Do not reclassify them merely to raise coverage. Additional semantic overlaps or multi-statement adapters can still require further review. The output therefore supports “no identified wrapper under the stated structural rules,” not an unrestricted guarantee of semantic independence.

## Reuse the parser on a new source snapshot

Keep `extract_structural_methods.py`, `ScalaOverlapInventory.scala` and `JavaOverlapInventory.java` together. Supply a complete compiler inventory containing source SHA-256 values, scopes and declaration positions:

```sh
python3 extract_structural_methods.py \
  --source-root /absolute/source/root \
  --inventory /absolute/source_declarations.json \
  --compiler-config /absolute/compiler_paths.json \
  --output /absolute/structural-audit
```

The compiler configuration supplies only `java` and the Scala compiler `classpath`; it cannot override the requested source root. The helper verifies source hashes, parses syntax only, and joins every selected method exactly by source position, signature and owner. It never executes the library or sends model requests.

Apply the explicit policy using:

```sh
python3 normalize_structural_policy.py \
  --input /absolute/structural-audit/public_method_candidate_ledger.json \
  --output /absolute/structural-audit/reviewed_structural_site_ledger.json
```

The current normalization policy's stable-version metadata must be updated when the source identity changes. `structural_parser_contract_receipt.json` records 20 parser-only fixture checks covering direct and nested calls, casts, curried/implicit arity, thin adapters, mutation, ambiguous references, literals, abstract methods and unresolved blocks. Fixture code was never executed.
