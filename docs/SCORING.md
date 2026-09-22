# Scoring a matched study

A unit is **one condition × one case × one trial**. Report microtasks and composition puzzles separately. Compared conditions share the case bank, trials, model settings and repair allowance; treatment context and implementation vary according to the [condition matrix](VERSIONS.md).

## Pass, failure and unresolved work

A pass requires three verified Boolean flags: execution, independent oracle and required API reachability. The checker must return the requested backend identity and valid evidence for its declared adjudication artifacts.

Let `B = common.max_snippet_fixes`. Candidate rounds are `0` through `B`: at most `B + 1` solutions. Round 0 measures first-attempt success. A verified failure may trigger repair with previous code and public feedback; eligible hints appear only on repairs. A pass stops the unit. Verified failure after the final round is terminal `fail`.

Provider transport attempts have a separate allowance. Transport failure does not consume a semantic repair round. Exhaustion records `provider_pending`; unverified checker evidence records `unverified`. Both are unresolved, not semantic failures. `--retry-provider` explicitly permits another bounded transport batch, retaining prior attempts/cost. It does not increase `B` or reopen a terminal result.

## Fixed denominators

For kind `k`, let `C_k` be selected cases and `T` shared trials. Every condition uses `N_k = |C_k| × |T|`, including during partial execution. Let `I_a,k` count first-attempt passes, `P_a,k` passes within budget, and `F_a,k` terminal verified failures for condition `a`.

| Quantity | Formula |
| --- | --- |
| First-attempt observed lower bound (%) | `100 × I_a,k / N_k` |
| Within-budget observed lower bound (%) | `100 × P_a,k / N_k` |
| Completed units | `P_a,k + F_a,k` |
| Unresolved units | `N_k − P_a,k − F_a,k` |
| Final within-budget accuracy (%) | `100 × P_a,k / N_k`, final only when unresolved is zero |

Missing rows, `not_run`, `provider_pending` and `unverified` stay in the denominator. `--condition` and `--max-units` limit execution, not the selection. Lower bounds are observed proportions with unresolved outcomes contributing no known successes; they are not confidence bounds. With `B = 0`, first-attempt and within-budget success coincide.

## Paired comparisons

Pair conditions `a` and `b` only on the same case/trial. Let `M_ab,k` count pairs with both outcomes terminal, `R_ab,k` fail→pass recoveries, and `G_ab,k` pass→fail regressions.

- Provisional delta: `100 × (R_ab,k − G_ab,k) / M_ab,k` percentage points, undefined when no pair is complete.
- Final paired lift: `100 × (R_ab,k − G_ab,k) / N_k` percentage points, only when every selected pair is complete.

The provisional value describes a completed subset and can be biased by execution order/selective completion. Final lift is a descriptive within-budget accuracy difference. Reports include all pairs but do not infer causal significance, confidence intervals or broad generalization.

## Resources and interpretation

Reports total provider calls, provider/checker wall time and valid provider-reported token usage across attempts. Missing usage stays explicit. Control costs remain in validation evidence, separate from audience generation. Documentation, aliases and hints have separate character caps; these are not token budgets or proof of equal prompt lengths.

An outcome concerns the supplied bank and trusted adapter. It does not establish compatibility beyond tested contracts, direct caller use from transitive reachability, or security against adversarial programs. A small scaffolded bank and one trial cannot establish robust model superiority.

Implementation: [condition_reporting.py](../workflow/condition_reporting.py), [condition_evaluation.py](../workflow/condition_evaluation.py), [condition_setup.py](../workflow/condition_setup.py). [OUTPUTS.md](OUTPUTS.md) locates reports and raw evidence. The three-README evaluator retains its separate protocol; do not relabel its results as treatment-condition evidence.
